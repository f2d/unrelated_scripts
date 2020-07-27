#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Python 2 or 3 should work.

import os, sys, re

print_encoding = sys.getfilesystemencoding() or 'utf-8'
argc = len(sys.argv)

if argc < 2:
	self_name = os.path.basename(__file__)

	help_text_lines = [
		''
	,	'* Description:'
	,	'	Find and extract known files (PNGs) stored as is inside other files.'
	,	''
	,	'* Usage:'
	,	'	%s <source> <dest>'
	,	''
	,	'<source>: path to binary data file or folder with files to read.'
	,	'<dest>: path to folder to save extracted files. If "TEST", do not save.'
	,	''
	,	'* Examples:'
	,	'	%s "/read/from/folder/" "/save/to/folder/"'
	,	'	%s "/read/from/data.bin" TEST'
	]

	print('\n'.join(help_text_lines).replace('%s', self_name))

	sys.exit()

# png magic bytes:
# ‰PNG
# IEND
# ®B`‚

pat_file_content = {
	'png': re.compile(br'''
		\x89\x50\x4E\x47
		.*?
		\x49\x45\x4E\x44
		\xAE\x42\x60\x82
	''', re.X | re.DOTALL)
}

pat_conseq_slashes = re.compile(r'[\\/]+')

def fix_slashes(path):
	return re.sub(pat_conseq_slashes, '/', u'' + path)

def extract_from_file(src_path, dest_path):
	src_file_path = fix_slashes(src_path)

	if not os.path.isfile(src_file_path):
		return False

	src_file = open(src_file_path, 'rb')

	if not src_file:
		print('Error: Could not open source file.')
		return False

	print('')
	print('Read file: "%s"' % src_file_path.encode(print_encoding))

	content = src_file.read()
	src_file.close()

	print('Size: %d bytes' % len(content))

	for ext, pat in pat_file_content.items():
		i = 0

		for found in pat.finditer(content):
			i += 1

			found_content_part = found.group(0)
			dest_file_path = fix_slashes('%s/%d.%s' % (dest_path, i, ext))

			print('')
			print('Save file: "%s"' % dest_file_path.encode(print_encoding))
			print('Size: %d bytes' % len(found_content_part))

			if not TEST:
				if not os.path.isdir(dest_path):
					os.makedirs(dest_path)

				dest_file = open(dest_file_path, 'wb')
				dest_file.write(found_content_part)
				dest_file.close()

				print('Saved.')

		print('Found %d %s files.' % (i, ext))

	print('	--------' * 4)
	return True

src_path = fix_slashes(sys.argv[1] if argc > 1 else '') or '.'
dest_path = fix_slashes(sys.argv[2] if argc > 2 else '') or '.'

TEST = (dest_path == 'TEST')

if os.path.isdir(src_path):
	for name in os.listdir(src_path):
		extract_from_file(src_path+'/'+name, dest_path+'/'+name+'_parts')
else:
	extract_from_file(src_path, dest_path)
