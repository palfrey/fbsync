#!/usr/bin/python
from facebook import Facebook, FacebookError
from cPickle import load, dump, PickleError
from os.path import exists,abspath
from os import walk,sep
from os.path import join
from sys import argv,exit

try:
	from urlgrab.GetURL import GetURL
except ImportError:
	print "You need to install urlgrab. Get it using 'git clone git://github.com/palfrey/urlgrab.git urlgrab'"
	exit(1)

from re import search,findall
from time import sleep
from PIL import Image

auth = "auth"

if not exists(auth):
	# Get api_key and secret_key from a file
	fbs = open("settings").readlines()
	facebook = Facebook(fbs[0].strip(), fbs[1].strip())

	facebook.auth_createToken()
	# Show login window
	facebook.login()

	# Login to the window, then press enter
	print 'After logging in, press enter...'
	raw_input()

	facebook.auth_getSession()
	dump(facebook,file(auth,"wb"))
	info = facebook.users_getInfo([facebook.uid], ['name'])[0]
	print 'Name: ', info['name']
else:
	facebook = load(file(auth))

if len(argv)==1:
	print "need a dir!"
	exit(1)

trueroot = abspath(argv[1])+sep
print "trueroot",trueroot


def regenfolders():
	global folders
	_folders = facebook.photos_getAlbums(facebook.uid)
	sleep(1)
	folders = {}
	for f in _folders:
		folders[f['name']] = f

regenfolders()

print "folders",folders.keys()

def createfolder(folder):
	global folders
	if folder not in folders.keys():
		print "creating",folder
		facebook.photos_createAlbum(folder)
		print "created",folder
		#folders[folder] = {}
		#raise Exception
		regenfolders()

try:
	done = load(file("done","rb"))
except (PickleError,IOError):
	done = []
	
for root, dirs, files in walk(trueroot):
	if root[-len("tn"):] == "tn":
		continue
	folder = root[len(trueroot):].replace(sep," - ")
	truefolder = folder
	findex = 1
	if folder.find("200")!=0:
		continue
	if folder in done:
		continue
	#if folder!="2004 - 1127-30 dallas":
	#	continue
	existing = None	
	added = 0
	for x in files:
		if x.lower().find(".jpg")!=-1:
			createfolder(folder)
			if existing == None:
				existing = []
				counts = {}
				for f in folders:
					if f.find(folder)!=0:
						continue
					if f!=folder:
						print f,folder,f[len(folder):]
						try:
							i = int(f[len(folder):])
						except ValueError:
							continue
						#raise Exception
					print "aid",folders[f]['aid'],f
					orig = facebook.photos_get(aid=folders[f]['aid'])
					sleep(1)
					counts[f] = len(orig)
					for z in orig:
						existing.append(z['caption'])
					if len(orig)>0:
						print orig[0]
				print "existing",existing
				for k in sorted(counts.keys()):
					if k<60: # folder limit
						break
				folder = k # pick a folder that's got some space
				#raise Exception
			
			fullpath = join(root,x)
			print fullpath
			if x in existing:
				continue
			
			im = Image.open(fullpath)
			ratio = (1.0*im.size[0])/im.size[1]
			#print "im.size",im.size,ratio
			if ratio<1.0:
				ratio = 1.0/ratio
			#print "ratio",ratio
			if ratio>3.0:
				print "file '%s' has ratio %.2f, which exceeds 3.0, so facebook won't like it..."%(x,ratio)
				continue
			#raise Exception

			added +=1
			#raise Exception

			data = file(fullpath,"r").read()
			try:
				facebook.photos_upload(data,caption=x,aid=folders[folder]['aid'])
				sleep(1)
			except FacebookError,e:
				if e.code() == 321: #album full
					findex +=1
					folder = "%s %d"%(truefolder,findex)
					createfolder(folder)
				else:
					raise
				
	done.append(truefolder)
	dump(done,file("done","wb"))
			
