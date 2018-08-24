#!/usr/bin/python3
import git
import os
import json
import struct

def decryptWC4(wc4):
	pk4 = bytearray(wc4[0x8:0x8 + 136])
	checksum = struct.unpack('<H', pk4[0x6:0x8])[0]
	for i in range(0x8, 4 * 32 + 8, 2):
		checksum = ((checksum * 0x41C64E6D + 0x6073) & 0xFFFFFFFF);
		pk4[i] ^= ((checksum >> 16) & 0xFF)
		pk4[i + 1] ^= (checksum >> 24)
	
	seed = (((struct.unpack('<I', pk4[:0x4])[0] >> 0xD) & 0x1F) % 24)
	aloc = [ 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 2, 3, 1, 1, 2, 3, 2, 3, 1, 1, 2, 3, 2, 3 ]
	bloc = [ 1, 1, 2, 3, 2, 3, 0, 0, 0, 0, 0, 0, 2, 3, 1, 1, 3, 2, 2, 3, 1, 1, 3, 2 ]
	cloc = [ 2, 3, 1, 1, 3, 2, 2, 3, 1, 1, 3, 2, 0, 0, 0, 0, 0, 0, 3, 2, 3, 2, 1, 1 ]
	dloc = [ 3, 2, 3, 2, 1, 1, 3, 2, 3, 2, 1, 1, 3, 2, 3, 2, 1, 1, 0, 0, 0, 0, 0, 0 ]
	ord = [ aloc[seed], bloc[seed], cloc[seed], dloc[seed] ]
	
	cpk4 = bytearray(pk4)
	for i in range(4):
		pk4[8 + 32 * i : 40 + 32 * i] = cpk4[32 * ord[i] + 8 : 32 * ord[i] + 40]
	
	return pk4

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
			
			entry = {}
			entry['name'] = name
			entry['type'] = type
			entry['size'] = size
			entry['offset'] = len(data)
			sheet['wondercards'].append(entry)
			
			with open(os.path.join(path, fullname), 'rb') as f:
				tempdata = f.read()
				if type == 'wc7' or type == 'wc6':
					entry['species'] = -1 if tempdata[0x51] != 0 else struct.unpack('<H', tempdata[0x82:0x84])[0]
					entry['form'] = -1 if tempdata[0x51] != 0 else tempdata[0x84]
				elif type == 'wc7full' or type == 'wc6full':
					entry['species'] = -1 if tempdata[0x51 + 0x208] != 0 else struct.unpack('<H', tempdata[0x82:0x84])[0]
					entry['form'] = -1 if tempdata[0x51 + 0x208] != 0 else tempdata[0x84]
				elif type == 'pgf':
					entry['species'] = -1 if tempdata[0xB3] != 1 else struct.unpack('<H', tempdata[0x1A:0x1C])[0]
					entry['form'] = -1 if tempdata[0xB3] != 1 else tempdata[0x1C]
				elif type == 'wc4':
					if tempdata[0] == 1 or tempdata[0] == 2:
						pk4 = decryptWC4(tempdata)
						entry['species'] = struct.unpack('<H', pk4[0x8:0x0A])[0]
						entry['form'] = pk4[0x40] >> 3
					elif tempdata[0] == 7:
						entry['species'] = 470
						entry['form'] = 0
					else:
						entry['species'] = -1
						entry['form'] = -1
				
				data += tempdata
		
	# export sheet	
	sheet_data = json.dumps(sheet, indent=2)
	with open("./out/sheet{}.json".format(gen), 'w') as f:
		f.write(sheet_data)

	# export data
	with open("./out/data{}.bin".format(gen), 'wb') as f:
		f.write(data)	
