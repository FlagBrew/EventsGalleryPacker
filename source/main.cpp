#include "utils/sha256.h"
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
#include <vector>

static const std::string langs[]      = {"CHS", "CHT", "ENG", "FRE", "GER", "ITA", "JPN", "KOR", "SPA"};
static const std::string extensions[] = {"wc7", "wc6", "wc7full", "wc6full", "pgf", "wc4", "pgt", "pcd"};

void scanDir(std::vector<u8>& outData, nlohmann::json& outSheet, std::filesystem::path root)
{
    for (std::filesystem::recursive_directory_iterator it{root}; it != std::filesystem::recursive_directory_iterator{}; it++)
    {
        bool goodExtension = false;
        for (const auto& extension : extensions)
        {
            // +1 removes the period
            if (extension == it->path().extension().c_str() + 1)
            {
                goodExtension = true;
                break;
            }
        }
        if (it->is_regular_file() && goodExtension)
        {
            nlohmann::json entry = nlohmann::json::object();
            std::string name     = it->path().stem();
            std::string game     = name.substr(name.find(' ') + 1);
            std::string type     = it->path().extension().c_str() + 1;
            std::string lang;
            for (const auto& l : langs)
            {
                if (name.find("(" + l + ")") != std::string::npos)
                {
                    lang = l;
                }
            }
            if (lang.empty())
            {
                lang = "ENG";
            }
            entry["game"]   = game.substr(0, game.find(' '));
            entry["size"]   = std::filesystem::file_size(*it);
            entry["type"]   = type;
            entry["offset"] = outData.size();
            if (type == "pgt" && it->path().parent_path().filename() == "Pokemon Ranger Manaphy Egg")
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

            FILE* in    = fopen(it->path().c_str(), "rb");
            u8* data    = new u8[std::filesystem::file_size(*it)];
            size_t read = fread(data, 1, std::filesystem::file_size(*it), in);
            fclose(in);
            // Probably unnecessary, but let's do this to silence the warning
            if (read != std::filesystem::file_size(*it))
            {
                printf("Bad");
                continue;
            }
            outData.insert(outData.end(), data, data + std::filesystem::file_size(*it));
            std::unique_ptr<WCX> wc;
            if (type == "wc7" || type == "wc7full")
            {
                wc = std::make_unique<WC7>((u8*)data, type == "wc7full");
            }
            else if (type == "wc6" || type == "wc6full")
            {
                wc = std::make_unique<WC6>((u8*)data, type == "wc6full");
            }
            else if (type == "pgf")
            {
                wc = std::make_unique<PGF>((u8*)data);
            }
            else if (type == "pgt")
            {
                wc = std::make_unique<PGT>((u8*)data);
            }
            else if (type == "pcd")
            {
                wc = std::make_unique<PCD>((u8*)data);
            }
            else if (type == "wc4")
            {
                wc = std::make_unique<WC4>((u8*)data);
            }

            delete[] data;

            if (wc->pokemon())
            {
                entry["species"] = wc->species();
                entry["gender"]  = wc->gender();
                if (wc->species() == 490 && wc->egg())
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
                entry["form"]    = -1;
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
                name       = wc->title();
                char id[9] = {'\0'};
                sprintf(id, "%04i - ", wc->ID());
                name = id + name;
            }

            entry["name"] = name;

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
        scanDir(data, sheet, dir);
        if (gen == 4)
        {
            scanDir(data, sheet, gallery / "Released" / "Gen 4" / "Pokemon Ranger Manaphy Egg");
        }

        printf("%i\n", data.size());

        std::sort(sheet["matches"].begin(), sheet["matches"].end(),
            [](const nlohmann::json& j1, const nlohmann::json& j2) { return j1["id"].get<int>() < j2["id"].get<int>(); });

        // remove unnecessary data
        for (auto& match : sheet["matches"])
        {
            match = match["indices"];
        }

        u8* compData = new u8[data.size()];
        u8 hash[SHA256_BLOCK_SIZE];
        unsigned int compressedSize;

        int error = BZ2_bzBuffToBuffCompress((char*)compData, &compressedSize, (char*)data.data(), data.size(), 5, 0, 0);

        std::string outPath = "out/data" + std::to_string(gen) + ".bin.bz2";
        FILE* outFile       = fopen(outPath.c_str(), "wb");
        fwrite(compData, 1, compressedSize, outFile);
        fclose(outFile);

        sha256(hash, compData, compressedSize);

        outPath += ".sha";
        outFile = fopen(outPath.c_str(), "wb");
        fwrite(hash, 1, sizeof(hash), outFile);
        fclose(outFile);

        delete[] compData;
        std::string jsonData = sheet.dump(2);
        compData             = new u8[jsonData.size()];

        BZ2_bzBuffToBuffCompress((char*)compData, &compressedSize, (char*)jsonData.data(), jsonData.size(), 5, 0, 0);

        outPath = "out/sheet" + std::to_string(gen) + ".json.bz2";
        outFile = fopen(outPath.c_str(), "wb");
        fwrite(compData, 1, compressedSize, outFile);
        fclose(outFile);

        sha256(hash, compData, compressedSize);

        outPath += ".sha";
        outFile = fopen(outPath.c_str(), "wb");
        fwrite(hash, 1, sizeof(hash), outFile);
        fclose(outFile);
    }

    return 0;
}
