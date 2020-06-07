#include "utils/crypto.hpp"
#include "wcx/PCD.hpp"
#include "wcx/PGF.hpp"
#include "wcx/PGT.hpp"
#include "wcx/WB7.hpp"
#include "wcx/WC4.hpp"
#include "wcx/WC6.hpp"
#include "wcx/WC7.hpp"
#include "wcx/WC8.hpp"
#include <algorithm>
#include <bzlib.h>
#include <filesystem>
#include <limits>
#include <nlohmann/json.hpp>
#include <stdio.h>
#include <string>
#include <vector>

static const std::string langs[]      = {"CHS", "CHT", "ENG", "FRE", "GER", "ITA", "JPN", "KOR", "SPA"};
static const std::string extensions[] = {"wc7", "wc6", "wc7full", "wc6full", "pgf", "wc4", "pgt", "pcd"};

void scanDir(std::vector<u8>& outData, nlohmann::json& outSheet, const std::filesystem::path& root, bool released)
{
    for (auto& file : std::filesystem::recursive_directory_iterator{root})
    {
        bool goodExtension = false;
        for (const auto& extension : extensions)
        {
            // +1 removes the period
            if (extension == file.path().extension().generic_string().c_str() + 1)
            {
                goodExtension = true;
                break;
            }
        }
        if (file.is_regular_file() && goodExtension)
        {
            nlohmann::json entry = nlohmann::json::object();
            std::string name     = file.path().stem().generic_string();
            std::string game     = name.substr(name.find(' ') + 1);
            std::string type     = file.path().extension().generic_string().c_str() + 1;
            std::string lang;
            auto fileSize = std::filesystem::file_size(file);
            for (const auto& l : langs)
            {
                if (name.find("(" + l + ")") != std::string::npos)
                {
                    lang = l;
                }
            }
            entry["game"]   = game.substr(0, game.find(' '));
            entry["size"]   = fileSize;
            entry["type"]   = type;
            entry["offset"] = outData.size();
            if (type == "pgt" && file.path().parent_path().filename() == "Pokemon Ranger Manaphy Egg")
            {
                name = "Pokemon Ranger Manaphy Egg";
                game = "DPPtHGSS";
            }
            if (name.find("Item ") != std::string::npos)
            {
                name.replace(name.find("Item "), name.find("Item ") + 5, "");
            }
            if (name.find(" " + game) != std::string::npos)
            {
                name.replace(name.find(" " + game), name.find(" " + game) + game.size() + 1, "");
            }
            if (name.find(" (" + lang + ")") != std::string::npos)
            {
                name.replace(name.find(" (" + lang + ")"), name.find(" (" + lang + ")") + lang.size() + 3, "");
            }

#ifdef _WIN32
            FILE* in = _wfopen(file.path().generic_wstring().c_str(), L"rb");
#else
            FILE* in = fopen(file.path().generic_string().c_str(), "rb");
#endif
            if (!in)
            {
#ifdef _WIN32
                wprintf(L"Could not open %s\n", file.path().generic_wstring().c_str());
#else
                printf("Could not open %s\n", file.path().generic_string().c_str());
#endif
            }
            u8* data    = new u8[fileSize];
            size_t read = fread(data, 1, fileSize, in);
            fclose(in);
            // Probably unnecessary, but let's do this to silence the warning
            if (read != fileSize)
            {
                printf("Bad: %lu read of %lu", read, fileSize);
                continue;
            }
            std::unique_ptr<pksm::WCX> wc;
            if (type == "wc7" || type == "wc7full")
            {
                wc = std::make_unique<pksm::WC7>((u8*)data, type == "wc7full");
            }
            else if (type == "wc6" || type == "wc6full")
            {
                wc = std::make_unique<pksm::WC6>((u8*)data, type == "wc6full");
            }
            else if (type == "pgf")
            {
                wc = std::make_unique<pksm::PGF>((u8*)data);
            }
            else if (type == "pgt")
            {
                wc = std::make_unique<pksm::PGT>((u8*)data);
            }
            else if (type == "pcd")
            {
                wc = std::make_unique<pksm::PCD>((u8*)data);
            }
            else if (type == "wc4")
            {
                wc = std::make_unique<pksm::WC4>((u8*)data);
            }

            if (lang.empty())
            {
                switch (wc->language())
                {
                    case pksm::Language::CHS:
                        lang = "CHS";
                        break;
                    case pksm::Language::CHT:
                        lang = "CHT";
                        break;
                    case pksm::Language::ENG:
                        lang = "ENG";
                        break;
                    case pksm::Language::FRE:
                        lang = "FRE";
                        break;
                    case pksm::Language::GER:
                        lang = "GER";
                        break;
                    case pksm::Language::ITA:
                        lang = "ITA";
                        break;
                    case pksm::Language::JPN:
                        lang = "JPN";
                        break;
                    case pksm::Language::KOR:
                        lang = "KOR";
                        break;
                    case pksm::Language::SPA:
                        lang = "SPA";
                        break;
                    default:
                        lang = "ENG";
                        break;
                }
            }

            // There's a dumb WC6 that requires this special case. Whee
            if (wc->pokemon() && wc->species() == pksm::Species::None)
            {
                continue;
            }

            outData.insert(outData.end(), data, data + fileSize);

            delete[] data;

            if (wc->pokemon())
            {
                entry["species"] = int(wc->species());
                entry["gender"]  = int(wc->gender());
                if (wc->species() == pksm::Species::Manaphy && wc->egg())
                {
                    entry["form"] = -1;
                }
                else
                {
                    entry["form"] = wc->alternativeForm();
                }
                entry["moves"] = nlohmann::json::array();
                for (size_t i = 0; i < 4; i++)
                {
                    entry["moves"].emplace_back(wc->move(i));
                }
                entry["TID"] = wc->TID();
                entry["SID"] = wc->SID();
            }
            else
            {
                entry["species"] = -1;
                entry["form"]    = -1;
                entry["gender"]  = -1;
                entry["moves"]   = nlohmann::json::array();
                for (size_t i = 0; i < 4; i++)
                {
                    entry["moves"].emplace_back(0);
                }
                entry["TID"] = 0;
                entry["SID"] = 0;
            }

            entry["item"] = wc->object();
            entry["id"]   = wc->ID();
            if (type != "pgt")
            {
                name        = wc->title();
                char id[10] = {'\0'}; // One extra character for safety (u16 can only be up to 5 characters)
                sprintf(id, "%04u - ", wc->ID());
                name = id + name;
            }

            entry["name"]     = name;
            entry["released"] = released;

            outSheet["wondercards"].emplace_back(entry);

            bool inMatches = false;
            for (auto& match : outSheet["matches"])
            {
                if (match["species"] == entry["species"] && match["form"] == entry["form"] && match["gender"] == entry["gender"] &&
                    match["item"] == entry["item"] && match["id"] == entry["id"] && match["TID"] == entry["TID"] && match["SID"] == entry["SID"] &&
                    match["moves"][0] == entry["moves"][0] && match["moves"][1] == entry["moves"][1] && match["moves"][2] == entry["moves"][2] &&
                    match["moves"][3] == entry["moves"][3])
                {
                    match["indices"][lang] = outSheet["wondercards"].size() - 1;
                    inMatches              = true;
                    break;
                }
            }

            if (!inMatches)
            {
                nlohmann::json match   = nlohmann::json::object();
                match["species"]       = entry["species"];
                match["form"]          = entry["form"];
                match["gender"]        = entry["gender"];
                match["item"]          = entry["item"];
                match["id"]            = entry["id"];
                match["TID"]           = entry["TID"];
                match["SID"]           = entry["SID"];
                match["moves"]         = entry["moves"];
                match["indices"]       = nlohmann::json::object();
                match["indices"][lang] = outSheet["wondercards"].size() - 1;
                outSheet["matches"].emplace_back(match);
            }
        }
    }
}

int main(int argc, char** argv)
{
    if (argc != 2)
    {
        printf("Usage: %s <EventsGallery directory>\n", argv[0]);
        return 1;
    }

    std::filesystem::create_directory("out");

    std::filesystem::path gallery(argv[1]);
    if (!std::filesystem::exists(gallery))
    {
        printf("Gallery directory does not exist\n");
        return 2;
    }

    for (const int& gen : {4, 5, 6, 7})
    {
        std::filesystem::path dir = gallery / "Released" / ("Gen " + std::to_string(gen)) / "Wondercards";
        if (!std::filesystem::exists(dir))
        {
            printf("\'%s\' does not exist\n", dir.c_str());
            return 3;
        }

        nlohmann::json sheet = nlohmann::json::object();
        sheet["gen"]         = std::to_string(gen);
        sheet["wondercards"] = nlohmann::json::array();
        sheet["matches"]     = nlohmann::json::array();

        std::vector<u8> data;
        scanDir(data, sheet, dir, true);
        if (gen == 4)
        {
            scanDir(data, sheet, gallery / "Released" / "Gen 4" / "Pokemon Ranger Manaphy Egg", true);
        }

        dir = gallery / "Unreleased" / ("Gen " + std::to_string(gen));
        if (std::filesystem::exists(dir))
        {
            scanDir(data, sheet, dir, false);
        }

        std::sort(sheet["matches"].begin(), sheet["matches"].end(),
            [](const nlohmann::json& j1, const nlohmann::json& j2) { return j1["id"].get<int>() < j2["id"].get<int>(); });

        // remove unnecessary data
        for (auto& match : sheet["matches"])
        {
            match = match["indices"];
        }

        unsigned int compressedSize = (unsigned int)(1.11 * data.size() + 600);
        u8* compData                = new u8[compressedSize];

        int error = BZ2_bzBuffToBuffCompress((char*)compData, &compressedSize, (char*)data.data(), data.size(), 5, 0, 0);

        std::string outPath = "out/data" + std::to_string(gen) + ".bin.bz2";
        FILE* outFile       = fopen(outPath.c_str(), "wb");
        auto written        = fwrite(compData, 1, compressedSize, outFile);
        fclose(outFile);

        auto hash = pksm::crypto::sha256(compData, compressedSize);

        outPath += ".sha";
        outFile = fopen(outPath.c_str(), "wb");
        fwrite(hash.data(), 1, hash.size(), outFile);
        fclose(outFile);

        delete[] compData;
        std::string jsonData = sheet.dump(2);
        compressedSize       = (unsigned int)(1.11 * jsonData.size() + 600);
        compData             = new u8[compressedSize];

        BZ2_bzBuffToBuffCompress((char*)compData, &compressedSize, (char*)jsonData.data(), jsonData.size(), 5, 0, 0);

        outPath = "out/sheet" + std::to_string(gen) + ".json.bz2";
        outFile = fopen(outPath.c_str(), "wb");
        fwrite(compData, 1, compressedSize, outFile);
        fclose(outFile);

        hash = pksm::crypto::sha256(compData, compressedSize);

        outPath += ".sha";
        outFile = fopen(outPath.c_str(), "wb");
        fwrite(hash.data(), 1, hash.size(), outFile);
        fclose(outFile);
    }

    return 0;
}
