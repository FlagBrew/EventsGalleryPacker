#!/usr/bin/python3
import git
import os
import json

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
				data += f.read()
		
	# export sheet	
	sheet_data = json.dumps(sheet, indent=2)
	with open("./out/sheet{}.json".format(gen), 'w') as f:
		f.write(sheet_data)

	# export data
	with open("./out/data{}.bin".format(gen), 'wb') as f:
		f.write(data)	
