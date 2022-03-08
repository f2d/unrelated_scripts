#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Python 2 or 3 should work.

import os, re, sys, time

# Use colored text if available:
try:
	from termcolor import colored, cprint
	import colorama

	colorama.init()

except ImportError:
	def colored(*list_args, **keyword_args): return list_args[0]
	def cprint(*list_args, **keyword_args): print(list_args[0])

# - Configuration and defaults ------------------------------------------------

print_encoding = sys.stdout.encoding or sys.getfilesystemencoding() or 'utf-8'

optional_arg_prefixes = ['-', '/']

pat_part_start       = br'(?P<Start>'
pat_part_vary_start  = br'(?P<Vary>.(?!'
pat_part_vary_end    = br')*'
pat_part_extra_vary  = br'(?P<Vary>.*?)'
pat_part_extra_start = br'^'
pat_part_extra_end   = br'(?P<Extra>\d{4,})?$'

# GIF magic bytes:
# start	GIF87a
# or	GIF89a
# end	NUL ;

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

# WEBP magic bytes:
# start	RIFF (3 bytes vary) NUL WEBPVP8

pat_part_webp = (br'''
	(?P<Content>
		(?P<Start>
			\x89\x50\x4E\x47
			...\x00
			\x57\x45\x42\x50
			\x56\x50\x38
		)(?P<Vary>.*?)
	)
''')

# MOV magic bytes:
# start	NUL NUL NUL 0x14 ftypqt SPACE SPACE

pat_part_mov = (br'''
	(?P<Content>
		(?P<Start>
			\x00\x00\x00\x14
			\x66\x74\x79\x70
			\x71\x74\x20\x20
		)(?P<Vary>.*?)
	)
''')

# MP4 magic bytes:
# start	NUL NUL NUL 0x18 ftypmp42

pat_part_mp4 = (br'''
	(?P<Content>
		(?P<Start>
			\x00\x00\x00\x18
			\x66\x74\x79\x70
			\x6D\x70\x34\x32
		)(?P<Vary>.*?)
	)
''')

# M4V magic bytes:
# start	NUL NUL NUL 0x20 ftypM4V SPACE

pat_part_m4v = (br'''
	(?P<Content>
		(?P<Start>
			\x00\x00\x00\x20
			\x66\x74\x79\x70
			\x4D\x34\x56\x20
		)(?P<Vary>.*?)
	)
''')

# MKV magic bytes:
# start	SUB EЯЈ
# end	м† (only in webm?)

pat_part_mkv = (br'''
	(?P<Content>
		(?P<Start>
			\x1A\x45\xDF\xA3
		)(?P<Vary>.*?
		)(?P<End>
			\xEC\x86
		)
	)
''')

pat_part_by_ext = {
	'gif' : pat_part_gif
,	'jpg' : pat_part_jpg
,	'png' : pat_part_png
,	'webp' : pat_part_webp

,	'm4v' : pat_part_m4v
,	'mkv' : pat_part_mkv
,	'mov' : pat_part_mov
,	'mp4' : pat_part_mp4
}

file_ext_aliases_by_ext = {
	'jpg' : ['jpe', 'jpeg']
,	'mkv' : ['mka', 'mks', 'webm']
}

file_exts_by_type = {
	'picture' : ['gif', 'jpg', 'png', 'webp']
,	'video'   : ['m4v', 'mkv', 'mov', 'mp4']
}

pat_file_content = {}
pat_conseq_slashes = re.compile(r'[\\/]+')

timestamp_format = r'%Y-%m-%d %H:%M:%S'
tz_timestamp_format = r'%Y-%m-%d %H:%M:%S{f} %z %Z'
gm_timestamp_format = r'%Y-%m-%d %H:%M:%S{f} GMT'

# - Declare functions ---------------------------------------------------------

def get_timestamp_text(time_value):
	return time.strftime(timestamp_format, time.localtime(time_value))

def get_tz_timestamp_text(time_value):
	return time.strftime(
		tz_timestamp_format.format(f=get_trimmed_fraction_text(time_value))
	,	time.localtime(time_value)
	)

def get_gm_timestamp_text(time_value):
	return time.strftime(
		gm_timestamp_format.format(f=get_trimmed_fraction_text(time_value))
	,	time.gmtime(time_value)
	)

def get_long_timestamp_text(time_value):
	return '{tz_time} ({gm_time})'.format(
		tz_time=get_tz_timestamp_text(time_value)
	,	gm_time=get_gm_timestamp_text(time_value)
	)

def get_trimmed_fraction_text(time_value, max_digits=6):
	text = str(time_value % 1.0).strip('0')

	return '' if text == '.' else text [ : max_digits + 1]

def get_bytes_length_text(content):
	return '{} bytes'.format(len(content))

def get_sorted_text_from_items(items, separator=', '):
	return separator.join(sorted(set(items)))

def get_file_ext_from_path(path):
	return  (
		path
		.rsplit('/', 1)[-1 : ][0]
		.rsplit('.', 1)[-1 : ][0]
		.lower()
	)

def print_with_colored_prefix_line(comment, value, color=None):
	print('')
	cprint(comment, color or 'yellow')
	print(value)

def print_with_colored_prefix(prefix, value, color=None):
	print('{prefix} {value}'.format(prefix=colored(prefix, color or 'yellow'), value=value))

def print_help():
	self_name = os.path.basename(__file__)
	max_file_type_length = 0

	for type in file_exts_by_type.keys():
		type_length = len(type)

		if max_file_type_length < type_length:
			max_file_type_length = type_length

	help_text_lines = [
		''
	,	colored('* Description:', 'yellow')
	,	'	Find and extract files of known formats stored as is inside other files.'
	,	'	Or truncate extraneous digits at the end of files of known formats (for deduplication).'
	,	''
	,	colored('* Known file formats:', 'yellow')
	,	'	' + get_sorted_text_from_items(pat_part_by_ext.keys())
	,	''
	,	colored('* Usage:', 'yellow')
	,	'	{0}'
		+	colored(' <source> <dest>', 'cyan')
		+	colored(' <optional args> <...>', 'magenta')
	,	''
	,	colored('<source>', 'cyan') + ' : path to binary data file or folder with files to read.'
	,	colored('<dest>', 'cyan') + '   : path to folder to save extracted files. If "TEST", do not save.'
	,	''
	,	colored(' -t --test', 'magenta') + '     : do not save or change any files.'
	,	colored(' -q --quiet', 'magenta') + '    : print only changes and final summary.'
	,	colored(' -b --verbose', 'magenta') + '  : print more internal info, for testing and debug.'
	,	colored(' -r --recurse', 'magenta') + '  : go into subfolders, if given source path is a folder.'
	,	colored(' -e --truncate', 'magenta') + ' : cut extra digits from content (added to bypass duplicate file checks), and add them to saved file name.'
	,	colored(' -l --long-time', 'magenta') + '  : print long detailed timestamps with fractional seconds and timezone.'
	,	colored(' -m --keep-time', 'magenta') + '  : set modification time of saved file to be same as original file.'
	,	colored(' -d --remove-old', 'magenta') + ' : delete original file after cutting extraneous data.'
	,	colored(' -i --in-place', 'magenta') + '   : save to original file after cutting extraneous data.'
	,	colored(' -f --in-folder', 'magenta') + '  : save extracted files to original folder. '
		+	colored('<dest>', 'cyan')
		+	' argument is not needed.'
	]+[
		(
			colored(
				' -' + type[0 : 1]
			+	' --' + type + (' ' * (max_file_type_length - len(type)))
			,	'magenta'
			)
			+	' : process only ' + type + ' files ('
			+	get_sorted_text_from_items(
					(
						colored(ext, 'yellow')
					+	' ['
					+	get_sorted_text_from_items(
							colored(alias, 'green')
							for alias in file_ext_aliases_by_ext[ext]
						)
					+	']'
						if file_ext_aliases_by_ext.get(ext)
						else
						colored(ext, 'yellow')
					) for ext in exts
				)
			+	').'
		) for type, exts in file_exts_by_type.items()
	]+[
		colored(' .<ext>', 'magenta') + (' ' * (max_file_type_length - 1))
		+	' : process only files of given extensions, including all aliases.'
# TODO:	,	colored(' -a=<date> --after=<time>', 'magenta') + '  : process only files modified after given date or time.'
# TODO:	,	colored(' -b=<date> --before=<time>', 'magenta') + ' : process only files modified before given date or time.'
	,	''
	,	'Ending slashes in paths are optional.'
	,	'Dash or slash signs in other args are optional.'
	,	'Single-letter optional arguments can be concatenated, starting from single dash or slash.'
	,	''
	,	colored('* Examples:', 'yellow')
	,	'	{0} "/read/from/folder/" "/save/to/folder/"'
	,	'	{0} "/read/from/folder/" --in-folder --recurse --test --video'
	,	'	{0} "/read/from/folder/" . --truncate --remove-old --picture'
	,	'	{0} "/read/from/folder/" -r t -def --quiet ".jpeg" ".mkv"'
	,	'	{0} "/read/from/file.dat" TEST --verbose'
	]

	print(u'\n'.join(help_text_lines).format(self_name))

def fix_slashes(path):
	return re.sub(pat_conseq_slashes, '/', u'' + path)

# - Main job function ---------------------------------------------------------

def run_batch_extract(argv):

	def get_file_content(src_file_path):

		if not os.path.isfile(src_file_path):
			return False

		src_file = open(src_file_path, 'rb')

		if not src_file:
			if not arg_quiet:
				print_with_colored_prefix_line('Error: Could not open source file:', src_file_path, 'red')

			return False

		if not arg_quiet:
			print_with_colored_prefix_line('Read file:', src_file_path)

		content = src_file.read()
		src_file.close()

		if not arg_quiet:
			print_with_colored_prefix('Size:', get_bytes_length_text(content))

		return content

	def extract_from_file(src_path, dest_path):

		src_file_path = fix_slashes(src_path)
		src_file_ext = file_type = get_file_ext_from_path(src_file_path)

		for ext, aliases in file_ext_aliases_by_ext.items():
			if file_type in aliases:
				file_type = ext

				break

		if process_only_exts and not file_type in process_only_exts:
			return 0

		found_count_in_src_file = dest_file_size = 0
		content = None

		for ext, pat in pat_file_content.items():

			if arg_truncate and ext != file_type:
				continue

			if not content:
				content = get_file_content(src_file_path)

				if arg_keep_time:
					src_file_time = os.path.getmtime(src_file_path)

					if not arg_quiet:
						print_with_colored_prefix('Last modified at:', get_mod_time_text(src_file_time))

			if not content:
				return found_count_in_src_file

			found_count_of_one_type = 0

			for found in pat.finditer(content):

				found_content_part = found.group('Content')
				found_extra_data = found.group('Extra') if arg_truncate else None

				if arg_truncate and not found_extra_data:
					continue

				file_counts['found'] += 1
				found_count_in_src_file += 1
				found_count_of_one_type += 1

				dest_file_path = (
					src_file_path
					if arg_in_place
					else
					fix_slashes(
						u'{prefix}(d{suffix}).{ext}'
						.format(
							prefix=dest_path
						,	suffix=int(found_extra_data)
						,	ext=src_file_ext
						)
						if arg_truncate and found_extra_data
						else
						u'{dir}/{index}.{ext}'
						.format(
							dir=dest_path
						,	index=found_count_of_one_type
						,	ext=ext
						)
					)
				)

				dest_file_exists = os.path.exists(dest_file_path)
				found_files_to_save.append(dest_file_path)

				if not arg_quiet or not arg_readonly_test:
					print_with_colored_prefix_line('Save file:', dest_file_path)
					print_with_colored_prefix('Size:', get_bytes_length_text(found_content_part))

				if not arg_quiet and dest_file_exists:
					cprint('Warning: file already exists at destination path.', 'yellow')

				if (
					not arg_readonly_test
				and	found_content_part
				and	len(found_content_part) > 0
				):
					dest_dir = dest_file_path.rsplit('/', 1)[0]

					if (
						dest_dir
					and	not os.path.isdir(dest_dir)
					and	not os.path.exists(dest_dir)
					):
						try:
							os.makedirs(dest_dir)
						except FileExistsError:
							pass

					if not os.path.isdir(dest_dir):
						print_with_colored_prefix_line('Cannot create folder:', dest_dir, 'red')
					else:
						file_counts['saved'] += 1

						dest_file = open(dest_file_path, 'wb')
						dest_file.write(found_content_part)
						dest_file.close()

						dest_file_size = os.path.getsize(dest_file_path)

						if arg_keep_time:
							os.utime(dest_file_path, (src_file_time, src_file_time))

						print_with_colored_prefix(
							'Saved file # {index}{existed}:'
							.format(
								existed=(
									', overwritten'
									if dest_file_exists
									else ''
								)
							,	index=(
									', '.join([
										'{total} total'
									,	'{in_src} in src'
									,	'{of_type} of type {type}'
									]).format(
										total=file_counts['saved']
									,	in_src=found_count_in_src_file
									,	of_type=found_count_of_one_type
									,	type=file_type
									)
									if not arg_truncate and arg_verbose
									else file_counts['saved']
								)
							)
						,	'{bytes} bytes{modtime}'
							.format(
								bytes=dest_file_size
							,	modtime=(
									', time set to ' + get_mod_time_text(src_file_time)
									if arg_keep_time
									else ''
								)
							)
						,	'green'
						)

			if not arg_truncate and found_count_of_one_type > 0:
				print('')
				print_with_colored_prefix(
					'Found', u'{count} {type} files.'
					.format(
						count=found_count_of_one_type
					,	type=ext
					)
				,	'cyan'
				)

		if not content:
			return found_count_in_src_file

		if (
			found_count_in_src_file > 0
		and	arg_truncate
		and	arg_remove_old
		and	not arg_in_place
		and	os.path.isfile(src_file_path)
		):
			if arg_readonly_test or dest_file_size > 0:
				print_with_colored_prefix_line('Delete file:', src_file_path)

				if not arg_readonly_test:
					os.remove(src_file_path)

					cprint('Deleted.', 'red')
			elif not arg_quiet:
				cprint('Skip deleting file, because nothing was saved.')

		if not arg_quiet:
			print('')
			print('	--------' * 4)

		return found_count_in_src_file

# - Show help and exit --------------------------------------------------------

	argc = len(argv)

	if argc < 2:
		print_help()

		return 1

# - Check arguments -----------------------------------------------------------

	process_only_exts = []

	def get_path_arg_from(index):
		return fix_slashes(argv[index] if argc > index else '') or '.'

	def get_optional_args_starting_from(start_index):

		args = []

		if argc <= start_index:
			return args

		for arg in argv[start_index : ]:
			if (
				len(arg) > 1
			and	arg[0] != arg[1]
			and	arg[0] in optional_arg_prefixes
			):
				args += arg[1 : ].lower()
			else:
				normalized_arg = arg.lower()

				for prefix in optional_arg_prefixes:
					normalized_arg = normalized_arg.replace(prefix, '')

				args.append(normalized_arg)

		return sorted(set(args))

	optional_args = get_optional_args_starting_from(1)
	arg_in_folder = ('infolder' in optional_args or 'f' in optional_args)

	if not arg_in_folder:
		optional_args = get_optional_args_starting_from(2)

	arg_in_place   = ('inplace'   in optional_args or 'i' in optional_args)
	arg_keep_time  = ('keeptime'  in optional_args or 'm' in optional_args)
	arg_long_time  = ('longtime'  in optional_args or 'l' in optional_args)
	arg_quiet      = ('quiet'     in optional_args or 'q' in optional_args)
	arg_recurse    = ('recurse'   in optional_args or 'r' in optional_args)
	arg_remove_old = ('removeold' in optional_args or 'd' in optional_args)
	arg_truncate   = ('truncate'  in optional_args or 'e' in optional_args)
	arg_verbose    = ('verbose'   in optional_args or 'b' in optional_args)

	src_path  = get_path_arg_from(0)
	dest_path = get_path_arg_from(1)

	arg_readonly_test = (
		'TEST' == dest_path
	or	'test' in optional_args
	or	't' in optional_args
	)

	get_mod_time_text = (
		get_long_timestamp_text
		if arg_long_time
		else get_timestamp_text
	)

	if arg_in_folder:
		dest_path = src_path

	if not arg_quiet:
		print_with_colored_prefix('Read only:', arg_readonly_test)
		print_with_colored_prefix('Read path:', src_path)
		print_with_colored_prefix('Save path:', '<same as source file>' if arg_in_folder else dest_path)
		print_with_colored_prefix('Optional args:', optional_args)

	for arg in optional_args:
		if arg[0 : 1] == '.':
			process_only_exts.append(arg.strip('.'))

	for type, exts in file_exts_by_type.items():
		if (
			type in optional_args
		or	type[0 : 1] in optional_args
		):
			process_only_exts += exts

	if len(process_only_exts) > 0:
		process_only_exts = sorted(set(process_only_exts))

		if not arg_quiet:
			print_with_colored_prefix('Processing only files of types:', process_only_exts)
	else:
		process_only_exts = None

	for ext, pat_part_real_file_content in pat_part_by_ext.items():
		pattern = pat_part_real_file_content

		if arg_truncate:
			pattern = (
				pat_part_extra_start
			+	pattern
			+	pat_part_extra_end
			)

		elif pat_part_extra_vary in pattern:
			pattern_parts = pattern.split(pat_part_extra_vary)
			pattern_magic_bytes = pattern_parts[0].split(pat_part_start, 1)[1]
			pattern = (
				pattern_parts[0]
			+	pat_part_vary_start
			+	pattern_magic_bytes
			+	pat_part_vary_end
			+	pattern_parts[1]
			)

		pat_file_content[ext] = regex = re.compile(pattern, re.X | re.DOTALL)

		if not arg_quiet and arg_verbose:
			print('')
			print_with_colored_prefix('File type:', ext)
			print_with_colored_prefix('Pattern:', pattern.decode(print_encoding))	# <- decode bytes to string
			print_with_colored_prefix('Regex:', regex)

# - Do the job ----------------------------------------------------------------

	found_files_to_save = []
	file_counts = {
		'found' : 0
	,	'saved' : 0
	}

	if os.path.isdir(src_path):

		def extract_from_folder(src_path):

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

				if arg_recurse and os.path.isdir(each_src_path):
					extract_from_folder(each_src_path)
				else:
					extract_from_file(
						each_src_path
					,	each_dest_path
					)

		extract_from_folder(src_path)
	else:
		extract_from_file(
			src_path
		,	(
				dest_path[ : -len(get_file_ext_from_path(dest_path)) - 1]
				# .rstrip('.')
				or dest_path
			)
			if arg_in_folder
			else dest_path
		)

	if file_counts['found'] > 0:
		print('')
		print_with_colored_prefix('Files found:', file_counts['found'], 'cyan')

		if arg_readonly_test:
			print('')
			print(u'\n'.join(found_files_to_save))

		elif file_counts['saved'] > 0:
			print_with_colored_prefix('Files saved:', file_counts['saved'], 'green')
	else:
		print('')
		cprint('Known files not found.', 'cyan')

	return 0

# - Run from commandline, when not imported as module -------------------------

if __name__ == '__main__':
	sys.exit(run_batch_extract(sys.argv[1 : ]))

# - End -----------------------------------------------------------------------
