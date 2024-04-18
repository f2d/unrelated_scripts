#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import os, sys

argc = len(sys.argv)

if (
	argc < 2
or	'--help' in sys.argv
or	'-help' in sys.argv
or	'-h' in sys.argv
or	'/?' in sys.argv
):
	self_name = os.path.basename(__file__)

	print('''
- Recursively generate embedded class files for AS3 project.
- Package names are relative, so run at source root and give your subfolders.
- Wildcard path names (*.*, ?) are not supported.
- Order of parameters is not important.

- Usage: "{0}" [<path=.>] [<path2> ...] [-h|--help|/?] [-t|--test] [i=<MyImageClass>] [a=<MyAudioClass>] [v=<MyVideoClass>] [t=<MyTextClass>]

- Example 1: "{0}" --test
- Example 2: "{0}" assets i=MyBitmap
- Example 3: "{0}" ../a/b/ "long name/sub/sub folder"'''.format(self_name))

	sys.exit(1)

class_names = {
	'i': {'myclass': 'BitMap','ext': ['bmp','gif','jpg','png']}
,	'a': {'myclass': 'Sound', 'ext': ['mp3','ogg','wav']}
,	'v': {'myclass': 'Video', 'ext': ['mp4','flv']}
,	't': {'myclass': 'Text',  'ext': ['txt','xml']}
}

TEST = 0
path = []

for arg in sys.argv[1:]:
	if arg == '-t' or arg == '--test':
		TEST = 1
		continue

	elif arg.find('=') > 0:
		k, val = arg.split('=', 1)
		if k in class_names:
			class_names[k]['myclass'] = val
			continue

	k = arg.replace('\\', '/').rstrip('/')
	if len(k.strip()):
		path.append(k)

if not len(path):
	path = [u'.']

def get_ext(path):
	if path.find('/') >= 0:
		path = path.rsplit('/', 1)[1]
	if path.find('.') >= 0:
		path = path.rsplit('.', 1)[1]
	return path.lower()

def process_dir(path):
	if not os.path.isdir(path):
		return

	count_found = count_write = 0
	names = os.listdir(path)

	for name in names:
		src = path+'/'+name

		if os.path.isdir(src):
			process_dir(src)
			continue

		ext = get_ext(name)

		for k in class_names:
			if ext in class_names[k]['ext']:
				count_found += 1

				dest = src[:-len(ext)]+'as'
				my_class = class_names[k]['myclass']

				content = path.strip('/.').replace('/', '.')
				content = 'package'+(' '+content if content else '')+'''
{
	[Embed(source="'''+name+'''")]
	public class '''+name[:-len(ext)-1].replace('.', '_')+' extends '+my_class+''' {}
}'''
				if TEST:
					print content
				else:
					old = ''
					if os.path.exists(dest):
						f = open(dest, 'r+b')
						old = f.read()
						f.close()

					if content != old:
						f = open(dest, 'w+b')
						f.write(content)
						f.close()

						count_write += 1
						print my_class, ext, name, '->', dest
				break

	print count_found, 'files found,', count_write, 'modified in', path

for i in path:
	process_dir(i)