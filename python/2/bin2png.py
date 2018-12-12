#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import os, sys, re

fse = sys.getfilesystemencoding() or 'utf-8'

argc = len(sys.argv)

if argc < 2:
	print '* Usage: bin2png.py <Source> <Dest>'
	print
	print '* Source: path to binary data file or folder with files to read.'
	print '* Dest: path to folder to save extracted files. If "TEST", do not save.'
	print
	print '* Example 1: bin2png.py "/read/from/folder/" "/save/to/folder/"'
	print '* Example 2: bin2png.py "/read/from/data.bin" TEST'
	sys.exit()

pat_conseq_slashes = re.compile(r'[\\/]+')

pat_file_content = {
	'png': re.compile(r'''
		\x89\x50\x4E\x47 # ‰PNG
		.*?
		\x49\x45\x4E\x44 # IEND
		\xAE\x42\x60\x82 # ®B`‚
	''', re.X | re.DOTALL)
}

def fix_slashes(path):
	return re.sub(pat_conseq_slashes, '/', unicode(path))

def extract_from_file(src, dest):
	src_file_path = fix_slashes(src)

	if not os.path.isfile(src_file_path):
		return False

	src_file = open(src_file_path, 'rb')

	if not src_file:
		print 'Error: Could not open source file.'
		return False

	print
	print 'Read file:', src_file_path.encode(fse)

	content = src_file.read()
	src_file.close()

	print 'Size:', len(content), 'bytes'

	for ext, pat in pat_file_content.items():
		i = 0

		for found in pat.finditer(content):
			i += 1

			found_content_part = found.group(0)
			dest_file_path = fix_slashes(dest+'/'+str(i)+'.'+ext)

			print
			print 'Save file:', dest_file_path.encode(fse)
			print 'Size:', len(found_content_part), 'bytes'

			if not TEST:
				if not os.path.isdir(dest):
					os.makedirs(dest)

				dest_file = open(dest_file_path, 'wb')
				dest_file.write(found_content_part)
				dest_file.close()

				print 'Saved.'


		print 'Found', i, ext, 'files.'

	print '	--------	--------	--------	--------'
	return True

src = fix_slashes(sys.argv[1] if argc > 1 else '') or '.'
dest = fix_slashes(sys.argv[2] if argc > 2 else '') or '.'

TEST = (dest == 'TEST')

if os.path.isdir(src):
	for name in os.listdir(src):
		extract_from_file(src+'/'+name, dest+'/'+name+'_parts')
else:
	extract_from_file(src, dest)
