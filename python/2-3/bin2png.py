#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Python 2 or 3 should work.

import os, sys, re

# Use colored text if available:
try:
	from termcolor import colored, cprint
	import colorama

	colorama.init()

except ImportError:
	def colored(*list_args, **keyword_args): return list_args[0]
	def cprint(*list_args, **keyword_args): print(list_args[0])

# - Configuration and defaults ------------------------------------------------

# PNG magic bytes:
#	‰PNG
#	IEND
#	®B`‚

pat_file_content = {
	'png': re.compile(br'''
		\x89\x50\x4E\x47
		.*?
		\x49\x45\x4E\x44
		\xAE\x42\x60\x82
	''', re.X | re.DOTALL)
}

pat_conseq_slashes = re.compile(r'[\\/]+')

# - Declare functions ---------------------------------------------------------

def print_with_colored_prefix_line(comment, value, color=None):
	print('')
	cprint(comment, color or 'yellow')
	print(value)

def print_with_colored_prefix(prefix, value, color=None):
	print('{} {}'.format(colored(prefix, color or 'yellow'), value))

def print_help():
	self_name = os.path.basename(__file__)

	help_text_lines = [
		''
	,	colored('* Description:', 'yellow')
	,	'	Find and extract known files stored as is inside other files.'
	,	''
	,	colored('* Known file formats:', 'yellow')
	,	'	' + ', '.join(sorted(set(pat_file_content.keys())))
	,	''
	,	colored('* Usage:', 'yellow')
	,	'	{0}'
		+	colored(' <source> <dest>', 'cyan')
	,	''
	,	colored('<source>', 'cyan') + ': path to binary data file or folder with files to read.'
	,	colored('<dest>', 'cyan') + ': path to folder to save extracted files. If "TEST", do not save.'
	,	''
	,	colored('* Examples:', 'yellow')
	,	'	{0} "/read/from/folder/" "/save/to/folder/"'
	,	'	{0} "/read/from/data.bin" TEST'
	]

	print('\n'.join(help_text_lines).format(self_name))

def fix_slashes(path):
	return re.sub(pat_conseq_slashes, '/', u'' + path)

# - Main job function ---------------------------------------------------------

def run_batch_extract(argv):

	def extract_from_file(src_path, dest_path):
		src_file_path = fix_slashes(src_path)

		if not os.path.isfile(src_file_path):
			return False

		src_file = open(src_file_path, 'rb')

		if not src_file:
			print_with_colored_prefix_line('Error: Could not open source file:', src_file_path, 'red')

			return False

		print_with_colored_prefix_line('Read file:', src_file_path)

		content = src_file.read()
		src_file.close()

		print_with_colored_prefix('Size:', '{} bytes'.format(len(content)))

		for ext, pat in pat_file_content.items():
			i = 0

			for found in pat.finditer(content):
				i += 1

				found_content_part = found.group(0)
				dest_file_path = fix_slashes('{}/{}.{}'.format(dest_path, i, ext))

				print_with_colored_prefix_line('Save file:', dest_file_path)

				print_with_colored_prefix('Size:', '{} bytes'.format(len(found_content_part)))

				if not TEST:
					if not os.path.isdir(dest_path):
						os.makedirs(dest_path)

					dest_file = open(dest_file_path, 'wb')
					dest_file.write(found_content_part)
					dest_file.close()

					cprint('Saved.', 'green')

			if i > 0:
				print('')
				print_with_colored_prefix('Found', '{} {} files.'.format(i, ext), 'cyan')

		print('')
		print('	--------' * 4)

		return True

# - Show help and exit --------------------------------------------------------

	argc = len(argv)

	if argc < 2:
		print_help()

		return 1

# - Check arguments -----------------------------------------------------------

	src_path = fix_slashes(argv[0] if argc > 0 else '') or '.'
	dest_path = fix_slashes(argv[1] if argc > 1 else '') or '.'

	TEST = (dest_path == 'TEST')

# - Do the job ----------------------------------------------------------------

	if os.path.isdir(src_path):
		for name in os.listdir(src_path):
			extract_from_file(
				src_path + '/' + name
			,	dest_path + '/' + name + '_parts'
			)
	else:
		extract_from_file(src_path, dest_path)

	return 0

# - Run from commandline, when not imported as module -------------------------

if __name__ == '__main__':
	sys.exit(run_batch_extract(sys.argv[1 : ]))

# - End -----------------------------------------------------------------------
