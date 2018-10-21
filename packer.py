#!/usr/bin/python3
import git
import os
import json
import struct

def getWC4(data):
	return bytearray(data[0x8:0x8 + 136])

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

	# initialize data
	data = b''

	# parse files
	for path, subdirs, files in os.walk(root):
		for fullname in files:
			name = fullname[:fullname.rindex(".")]
			type = fullname[fullname.rindex(".")+1:]
			size = os.stat(os.path.join(path, fullname)).st_size
			game = name[name.index(" ")+1:name[name.index(" ")+1:].index(" ") + name.index(" ")+1]

			name = name[0:4] + name[4:].replace("-","")
			name = name.replace(" &", ",")
			# get rid of language
			name = name.replace("(" + path[path.rindex(os.sep)+1:] + ")", "")
			# get rid of game (already saved into the 'game' field in the JSON)
			name = name.replace(game, "")
			# sanitize spaces
			name = ' '.join(name.split())
			
			entry = {}
			entry['name'] = name
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
				elif type == 'wc7full' or type == 'wc6full':
					entry['species'] = -1 if tempdata[0x51 + 0x208] != 0 else struct.unpack('<H', tempdata[0x28A:0x28C])[0]
					entry['form'] = -1 if tempdata[0x51 + 0x208] != 0 else tempdata[0x28C]
				elif type == 'pgf':
					entry['species'] = -1 if tempdata[0xB3] != 1 else struct.unpack('<H', tempdata[0x1A:0x1C])[0]
					entry['form'] = -1 if tempdata[0xB3] != 1 else tempdata[0x1C]
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
				
				if entry['species'] == -1:
					entry['name'] = name.replace("Item ", "")
				data += tempdata
		
	# export sheet	
	sheet_data = json.dumps(sheet)
	with open("./out/sheet{}.json".format(gen), 'w') as f:
		f.write(sheet_data)

	# export data
	with open("./out/data{}.bin".format(gen), 'wb') as f:
		f.write(data)	
