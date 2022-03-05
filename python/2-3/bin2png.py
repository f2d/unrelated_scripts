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

pat_part_extra_start = br'^'
pat_part_extra_end   = br'(?P<Extra>\d+)?$'

# GIF magic bytes:
# start	GIF87a
# or	GIF89a
# end	;

pat_part_gif = (br'''
	(?P<Content>
		(?P<Start>
			\x47\x49\x46\x38
			[\x37\x39]
			\x61
		)(?P<Vary>.*?
		)(?P<End>
			\x00\x3B
		)
	)
''')

# JPEG magic bytes:
# start	яШяа
# end	яЩ

pat_part_jpg = (br'''
	(?P<Content>
		(?P<Start>
			\xFF\xD8\xFF
			[\xE0\xE1\xEE\xDB]
		)(?P<Vary>.*?
		)(?P<End>
			\xFF\xD9
		)
	)
''')

# PNG magic bytes:
# start	‰PNG
#	CR LF SUB LF
# end	IEND
#	®B`‚

pat_part_png = (br'''
	(?P<Content>
		(?P<Start>
			\x89\x50\x4E\x47
			\x0D\x0A\x1A\x0A
		)(?P<Vary>.*?
		)(?P<End>
			\x49\x45\x4E\x44
			\xAE\x42\x60\x82
		)
	)
''')

pat_part_by_ext = {
	'png': pat_part_png
,	'gif': pat_part_gif
,	'jpg': pat_part_jpg
# ,	'jpeg': pat_part_jpg
}

pat_file_content = {}
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
	,	'	Find and extract files of known formats stored as is inside other files.'
	,	'	Or truncate extraneous digits at the end of files of known formats (for deduplication).'
	,	''
	,	colored('* Known file formats:', 'yellow')
	,	'	' + ', '.join(sorted(set(pat_part_by_ext.keys())))
	,	''
	,	colored('* Usage:', 'yellow')
	,	'	{0}'
		+	colored(' <source> <dest>', 'cyan')
		+	colored(' <optional args> <...>', 'magenta')
	,	''
	,	colored('<source>', 'cyan') + ': path to binary data file or folder with files to read.'
	,	colored('<dest>', 'cyan') + ': path to folder to save extracted files. If "TEST", do not save.'
	,	''
	,	colored('-t --test', 'magenta') + ': do not save or change any files.'
	,	colored('-r --recurse', 'magenta') + ': go into subfolders, if given source path is a folder.'
	,	colored('-e --truncate', 'magenta') + ': cut extra digits from content (added to bypass duplicate file checks), and add them to saved file name.'
	,	colored('-d --remove-old', 'magenta') + ': delete original file after cutting extraneous data.'
	,	colored('-i --in-place', 'magenta') + ': save to original file after cutting extraneous data.'
	,	colored('-f --in-folder', 'magenta') + ': save extracted files to original folder.'
	,	''
	,	'Ending slashes in paths are optional.'
	,	'Dash signs in args are optional.'
	,	''
	,	colored('* Examples:', 'yellow')
	,	'	{0} "/read/from/folder/" "/save/to/folder/"'
	,	'	{0} "/read/from/folder/" --in-folder --recurse --test'
	,	'	{0} "/read/from/file.dat" . --truncate --remove-old'
	,	'	{0} "/read/from/file.dat" . d e f r t'
	,	'	{0} "/read/from/file.dat" TEST'
	]

	print('\n'.join(help_text_lines).format(self_name))

def fix_slashes(path):
	return re.sub(pat_conseq_slashes, '/', u'' + path)

# - Main job function ---------------------------------------------------------

def run_batch_extract(argv):

	def get_file_content(src_file_path):

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

		return content

	def extract_from_file(src_path, dest_path):

		src_file_path = fix_slashes(src_path)
		src_file_ext = src_file_path.rsplit('.', 1)[1].replace('jpeg', 'jpg')
		found_count_total = 0
		content = None

		for ext, pat in pat_file_content.items():

			if arg_truncate and ext != src_file_ext:
				continue

			if not content:
				content = get_file_content(src_file_path)

			if not content:
				return found_count_total

			found_count = 0

			for found in pat.finditer(content):

				found_content_part = found.group('Content')
				found_extra_data = found.group('Extra')

				if arg_truncate and not found_extra_data:
					continue

				found_count_total += 1
				found_count += 1

				dest_file_path = (
					src_file_path
					if arg_in_place
					else
					fix_slashes(
						'{}(d{}).{}'.format(dest_path, int(found_extra_data), ext)
						if arg_truncate and found_extra_data
						else
						'{}/{}.{}'.format(dest_path, found_count, ext)
					)
				)

				print_with_colored_prefix_line('Save file:', dest_file_path)

				print_with_colored_prefix('Size:', '{} bytes'.format(len(found_content_part)))

				if (
					not arg_readonly_test
				and	found_content_part
				and	len(found_content_part) > 0
				):
					dest_dir = dest_file_path.rsplit('/', 1)[0]

					if dest_dir and not os.path.isdir(dest_dir):
						os.makedirs(dest_dir)

					dest_file = open(dest_file_path, 'wb')
					dest_file.write(found_content_part)
					dest_file.close()

					cprint('Saved.', 'green')

			if found_count > 0:
				print('')
				print_with_colored_prefix('Found', '{} {} files.'.format(found_count, ext), 'cyan')

		if not content:
			return found_count_total

		if (
			found_count_total
		and	arg_truncate
		and	arg_remove_old
		and	not arg_in_place
		and	os.path.isfile(src_file_path)
		):
			print_with_colored_prefix_line('Delete file:', src_file_path)

			if not arg_readonly_test:
				os.remove(src_file_path)

				cprint('Deleted.', 'red')

		print('')
		print('	--------' * 4)

		return found_count_total

# - Show help and exit --------------------------------------------------------

	argc = len(argv)

	if argc < 2:
		print_help()

		return 1

# - Check arguments -----------------------------------------------------------

	src_path = fix_slashes(argv[0] if argc > 0 else '') or '.'
	dest_path = fix_slashes(argv[1] if argc > 1 else '') or '.'

	optional_args = [
		arg
		.replace('-', '')
		.replace('/', '')
		.lower()
		for arg in argv[1:]
	] if argc > 1 else []

	arg_in_folder  = ('infolder'  in optional_args or 'f' in optional_args)

	if not arg_in_folder and len(optional_args) > 0:
		optional_args = optional_args[1:]

	arg_in_place   = ('inplace'   in optional_args or 'i' in optional_args)
	arg_recurse    = ('recurse'   in optional_args or 'r' in optional_args)
	arg_remove_old = ('removeold' in optional_args or 'd' in optional_args)
	arg_truncate   = ('truncate'  in optional_args or 'e' in optional_args)

	arg_readonly_test = (
		'TEST' == dest_path
	or	'test' in optional_args
	or	't' in optional_args
	)

	if arg_in_folder:
		dest_path = src_path

	for ext, pat_part_real_file_content in pat_part_by_ext.items():
		pat_file_content[ext] = re.compile(
			(
				pat_part_extra_start
			+	pat_part_real_file_content
			+	pat_part_extra_end
			) if arg_truncate else pat_part_real_file_content
		,	re.X | re.DOTALL
		)

# - Do the job ----------------------------------------------------------------

	found_count_total = 0

	if os.path.isdir(src_path):

		def extract_from_folder(src_path):

			found_count = 0

			for name in os.listdir(src_path):
				each_src_path = fix_slashes(src_path + '/' + name)
				each_dest_path = fix_slashes(
					(
						src_path if arg_in_folder else dest_path
					) + '/' + (
						name.rsplit('.', 1)[0]
						if arg_truncate
						else
						name + '_parts'
					)
				)

				if os.path.isdir(each_src_path):
					found_count += extract_from_folder(each_src_path)
				else:
					found_count += extract_from_file(
						each_src_path
					,	each_dest_path
					)

			return found_count

		found_count_total += extract_from_folder(src_path)
	else:
		found_count_total += extract_from_file(src_path, dest_path)

	if found_count_total > 0:
		if arg_readonly_test:
			print_with_colored_prefix_line('Files to save:', found_count_total, 'cyan')
		else:
			print_with_colored_prefix_line('Files saved:', found_count_total, 'green')
	else:
		print('')
		cprint('Known files not found.', 'cyan')

	return 0

# - Run from commandline, when not imported as module -------------------------

if __name__ == '__main__':
	sys.exit(run_batch_extract(sys.argv[1 : ]))

# - End -----------------------------------------------------------------------
