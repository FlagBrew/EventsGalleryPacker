#!/usr/bin/python3
import git
import os
import json
import struct

def getWC4(data):
	return bytearray(data[0x8:0x8 + 136])

def sortById(thing):
	return thing['id']

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
	sheet['gen'] = gen
	sheet['wondercards'] = []
	sheet['matches'] = []

	# initialize data
	data = b''

	# parse files
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

			entry = {}
			if gen == 4:
				entry['name'] = name.replace("Item ", "").replace(" " + game, "").replace(" (" + lang + ")","")
			entry['type'] = type
			entry['size'] = size
			entry['game'] = game
			entry['offset'] = len(data)
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
					cardId = entry['name'][:3]
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
				data += tempdata
	
	# sort, then get rid of data not needed in final product
	sheet['matches'] = sorted(sheet['matches'], key=sortById)
	for i in range(len(sheet['matches'])):
		temp = sheet['matches'][i]['indices']
		sheet['matches'][i] = temp
		
	# export sheet
	sheet_data = json.dumps(sheet)
	with open("./out/sheet{}.json".format(gen), 'w') as f:
		f.write(sheet_data)

	# export data
	with open("./out/data{}.bin".format(gen), 'wb') as f:
		f.write(data)	
