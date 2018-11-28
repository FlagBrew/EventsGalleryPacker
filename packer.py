#!/usr/bin/python3
import git
import os
import json
import struct
import gen4string

def getWC4(data):
	return bytearray(data[0x8:0x8 + 136])

def sortById(thing):
	return thing['id']

def scanDir(root, sheet, origOffset):
	retdata = b''
	for path, subdirs, files in os.walk(root):
		for fullname in files:
			name = fullname[:fullname.rindex(".")]
			type = fullname[fullname.rindex(".")+1:]
			size = os.stat(os.path.join(path, fullname)).st_size
			game = name[name.index(" ")+1:name[name.index(" ")+1:].index(" ") + name.index(" ")+1]

			lang = path[path.rindex("/")+1:]
			if len(lang) != 3:
				# in a subdirectory (there are currently only single subdirectories)
				lang = path[:path.rindex("/")]
				lang = lang[lang.rindex("/")+1:]
			
			if len(lang) != 3:
				# Pokemon Link card; see Gen 6 folder structure
				if "(" in name:
					lang = name[name.index("(")+1:name.index("(")+1 + 3]
				else:
					lang = "ENG"

			entry = {}
			if type == 'pgt':
				if path[path.rindex("/")+1:] == "Pokemon Ranger Manaphy Egg":
					game = "DPPtHGSS"
					entry['name'] = "Pokemon Ranger Manaphy Egg"
				else:
					entry['name'] = name.replace("Item ", "").replace(" " + game, "").replace(" (" + lang + ")","")
			entry['type'] = type
			entry['size'] = size
			entry['game'] = game
			entry['offset'] = origOffset + len(retdata)
			sheet['wondercards'].append(entry)
			
			with open(os.path.join(path, fullname), 'rb') as f:
				tempdata = f.read()
				if type == 'wc7' or type == 'wc6':
					entry['species'] = -1 if tempdata[0x51] != 0 else struct.unpack('<H', tempdata[0x82:0x84])[0]
					entry['form'] = -1 if tempdata[0x51] != 0 else tempdata[0x84]
					cardId = struct.unpack('<H', tempdata[:0x2])[0]
					# get event title
					name = tempdata[0x2:0x4C]
					for i in range(0, len(name), 2):
						if name[i] == 0x00:
							if name[i+1] == 0x00:
								name = name[:i]
								break
					if len(name) == 0:
						if "(" in fullname:
							name = fullname[:fullname.index("(")].replace("Pokemon Link ","")
						else:
							name = fullname[:fullname.rindex(".")].replace("Pokemon Link ","")
					else:
						name = name.decode('utf-16le')
					entry['name'] = "%04i - " % cardId + name
					inMatches = False
					for i in range(len(sheet['matches'])):
						if sheet['matches'][i]['id'] == cardId and sheet['matches'][i]['species'] == entry['species']:
							sheet['matches'][i]['indices'][lang] = len(sheet['wondercards']) - 1
							inMatches = True
					if not inMatches:
						match = {}
						match['id'] = cardId
						match['species'] = entry['species']
						match['indices'] = {}
						match['indices'][lang] = len(sheet['wondercards']) - 1
						sheet['matches'].append(match)
				elif type == 'wc7full' or type == 'wc6full':
					entry['species'] = -1 if tempdata[0x51 + 0x208] != 0 else struct.unpack('<H', tempdata[0x28A:0x28C])[0]
					entry['form'] = -1 if tempdata[0x51 + 0x208] != 0 else tempdata[0x28C]
					cardId = struct.unpack('<H', tempdata[0x208:0x20A])[0]
					# get event title
					name = tempdata[0x20A:0x254]
					for i in range(0, len(name), 2):
						if name[i] == 0x00:
							if name[i+1] == 0x00:
								name = name[:i]
								break
					name = name.decode('utf-16le')
					entry['name'] = "%04i - " % cardId + name
					inMatches = False
					for i in range(len(sheet['matches'])):
						if sheet['matches'][i]['id'] == cardId and sheet['matches'][i]['species'] == entry['species']:
							sheet['matches'][i]['indices'][lang] = len(sheet['wondercards']) - 1
							inMatches = True
					if not inMatches:
						match = {}
						match['id'] = cardId
						match['species'] = entry['species']
						match['indices'] = {}
						match['indices'][lang] = len(sheet['wondercards']) - 1
						sheet['matches'].append(match)
				elif type == 'pgf':
					entry['species'] = -1 if tempdata[0xB3] != 1 else struct.unpack('<H', tempdata[0x1A:0x1C])[0]
					entry['form'] = -1 if tempdata[0xB3] != 1 else tempdata[0x1C]
					cardId = struct.unpack('<H', tempdata[0xB0:0xB2])[0]
					# get event title
					name = tempdata[0x60:0xAA]
					for i in range(0, len(name), 2):
						if name[i] == 0xFF:
							if name[i+1] == 0xFF:
								name = name[:i]
								break
					name = name.decode('utf-16le')
					entry['name'] = "%04i - " % cardId + name
					inMatches = False
					for i in range(len(sheet['matches'])):
						if sheet['matches'][i]['id'] == cardId and sheet['matches'][i]['species'] == entry['species'] and sheet['matches'][i]['form'] == entry['form']:
							sheet['matches'][i]['indices'][lang] = len(sheet['wondercards']) - 1
							inMatches = True
					if not inMatches:
						match = {}
						match['id'] = cardId
						match['species'] = entry['species']
						match['form'] = entry['form']
						match['indices'] = {}
						match['indices'][lang] = len(sheet['wondercards']) - 1
						sheet['matches'].append(match)
				elif type == 'wc4':
					if tempdata[0] == 1 or tempdata[0] == 2:
						pk4 = getWC4(tempdata)
						entry['species'] = struct.unpack('<H', pk4[0x8:0x0A])[0]
						entry['form'] = pk4[0x40] >> 3
					elif tempdata[0] == 7:
						entry['species'] = 470
						entry['form'] = 0
					else:
						entry['species'] = -1
						entry['form'] = -1
					cardId = struct.unpack('<H', tempdata[0x150:0x152])[0]
					entry['name'] = "%03i - " % cardId + gen4string.translateG4String(tempdata[0x104:0x104+0x48]).replace("Mystery Gift ","")
					if entry['name'] == "%03i - " % cardId:
						entry['name'] = name.replace("Item ", "").replace(" " + game, "").replace(" (" + lang + ")","")
					inMatches = False
					for i in range(len(sheet['matches'])):
						if sheet['matches'][i]['id'] == cardId and sheet['matches'][i]['species'] == entry['species'] and sheet['matches'][i]['form'] == entry['form']:
							sheet['matches'][i]['indices'][lang] = len(sheet['wondercards']) - 1
							inMatches = True
					if not inMatches:
						match = {}
						match['id'] = cardId
						match['species'] = entry['species']
						match['form'] = entry['form']
						match['indices'] = {}
						match['indices'][lang] = len(sheet['wondercards']) - 1
						sheet['matches'].append(match)
				elif type == 'pgt':
					if tempdata[0] == 1 or tempdata[0] == 2:
						pk4 = getWC4(tempdata)
						entry['species'] = struct.unpack('<H', pk4[0x8:0x0A])[0]
						entry['form'] = pk4[0x40] >> 3
					elif tempdata[0] == 7:
						entry['species'] = 490
						entry['form'] = -1 # special meaning for Manaphy: egg
					else:
						entry['species'] = -1
						entry['form'] = -1
					cardId = entry['name'][:3]
					if not any(elem in "1234567890" for elem in cardId):
						cardId = 999
					inMatches = False
					for i in range(len(sheet['matches'])):
						if sheet['matches'][i]['id'] == cardId and sheet['matches'][i]['species'] == entry['species'] and sheet['matches'][i]['form'] == entry['form']:
							sheet['matches'][i]['indices'][lang] = len(sheet['wondercards']) - 1
							inMatches = True
					if not inMatches:
						match = {}
						match['id'] = cardId
						match['species'] = entry['species']
						match['form'] = entry['form']
						match['indices'] = {}
						match['indices'][lang] = len(sheet['wondercards']) - 1
						sheet['matches'].append(match)

				retdata += tempdata
	return retdata

# create out directory
try:
    os.stat("./out")
except:
    os.mkdir("./out")

# import a/o update the EventsGallery
if os.path.exists("./EventsGallery"):
	print("Pulling from EventsGallery...")
	repo = git.Repo("./EventsGallery")
	repo.remotes.origin.pull()
else:
	print("Cloning EventsGallery...")
	git.Git(".").clone("https://github.com/projectpokemon/EventsGallery.git")

# loop generations
print("Creating data...")
for gen in range (4, 7+1):
	# set root path
	root = "./EventsGallery/Released/Gen {}/Wondercards".format(gen)

	# initialize sheet
	sheet = {}
	sheet['gen'] = str(gen)
	sheet['wondercards'] = []
	sheet['matches'] = []

	# initialize data
	data = b''

	# parse files
	data += scanDir(root, sheet, 0)
	if (gen == 4):
		data += scanDir("./EventsGallery/Released/Gen 4/Pokemon Ranger Manaphy Egg", sheet, len(data))
	
	# sort, then get rid of data not needed in final product
	sheet['matches'] = sorted(sheet['matches'], key=sortById)
	for i in range(len(sheet['matches'])):
		temp = sheet['matches'][i]['indices']
		sheet['matches'][i] = temp
		sheet['matches'][i]
		
	# export sheet
	sheet_data = json.dumps(sheet)
	with open("./out/sheet{}.json".format(gen), 'w') as f:
		f.write(sheet_data)

	# export data
	with open("./out/data{}.bin".format(gen), 'wb') as f:
		f.write(data)	
