#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Python 2 or 3 should work.

# TODO: 1. skip readonly/hidden/system files, to avoid modifying files used for torrents, etc.
# TODO: 2. trim repeatedly, because some files may have multiple repeating patterns each ending with format-specific EOF mark.
# TODO: 3. collapse repeating digit runs: br'(?P<Digits>\d{1,64}?)(?P=Digits)*', including already present suffixes in filename?
# TODO: 4. collapse separately parts of long runs, like "111111111111111111111234", to shorten filename suffix?
# TODO: 5. for trim - try checking only start and end of file, may be faster for very big files (over 1 GB).

import os, re, sys, time

try:
	from collections.abc import Iterable

except:
	from collections import Iterable

# Use colored text if available:
try:
	from termcolor import colored, cprint
	import colorama

	colorama.init()

except ImportError:
	def colored(*list_args, **keyword_args): return list_args[0]
	def cprint (*list_args, **keyword_args): print (list_args[0])

# https://stackoverflow.com/a/47625614
if sys.version_info[0] >= 3:
	unicode = str

# - Configuration and defaults ------------------------------------------------

print_encoding = sys.stdout.encoding or sys.getfilesystemencoding() or 'utf-8'

optional_arg_prefixes = ['-', '/']

pat_part_content = br'(?P<Content>'
pat_part_start   = br'(?P<Start>'
pat_part_end     = br'(?P<End>'
pat_part_close   = br')'
pat_part_multifile_vary_start = br'(?P<Vary>.(?!'
pat_part_multifile_vary_end   = br'))*'
pat_part_singlefile_start = br'^'
pat_part_singlefile_vary  = br'(?P<Vary>.*?)'
pat_part_singlefile_extra_start  = br'(?P<Extra>'
pat_part_singlefile_extra_bytes  = br'(?P<Repeated>.{1,32}?)(?P=Repeated)*'	# <- trim unlimited repeats of limited length, save with count
pat_part_singlefile_extra_nulls  = br'\x00+'	# <- trim any count of null bytes, save as count
pat_part_singlefile_extra_digits = br'\d{1,99}'
pat_part_singlefile_extra_guess  = br'\d{6,99}'	# <- not really sure, user should be careful
pat_part_singlefile_extra_end    = br')?$'

pat_parts_by_ext = {

# GIF magic bytes:
# start	GIF87a
# or	GIF89a
# end	NUL ;

	'gif' : {
		'start' : br'''
			\x47\x49\x46\x38
			[\x37\x39]
			\x61
		'''
	,	'end' : br'''
			\x00\x3B
		'''
	}

# JPEG magic bytes:
# start	яШяа
# end	яЩ

,	'jpg' : {
		'start' : br'''
			\xFF\xD8\xFF
			[\xE0\xE1\xEE\xDB]
		'''
	,	'end' : br'''
			\xFF\xD9
		'''
	}

# PNG magic bytes:
# start	‰PNG
#	CR LF SUB LF
# end	IEND
#	®B`‚

,	'png' : {
		'start' : br'''
			\x89\x50\x4E\x47
			\x0D\x0A\x1A\x0A
		'''
	,	'end' : br'''
			\x49\x45\x4E\x44
			\xAE\x42\x60\x82
		'''
	}

# WEBP magic bytes:
# start	RIFF (3 bytes vary) NUL WEBPVP8

,	'webp' : {
		'start' : br'''
			\x89\x50\x4E\x47
			.   .   .   \x00
			\x57\x45\x42\x50
			\x56\x50\x38
		'''
	}

# MOV magic bytes:
# start	NUL NUL NUL 0x14 ftypqt SPACE SPACE

,	'mov' : {
		'start' : br'''
			\x00\x00\x00\x14
			\x66\x74\x79\x70
			\x71\x74\x20\x20
		'''
	}

# MP4 magic bytes:
# start	NUL NUL NUL 0x18 ftypmp42

,	'mp4' : {
		'start' : br'''
			\x00\x00\x00\x18
			\x66\x74\x79\x70
			\x6D\x70\x34\x32
		'''
	}

# M4V magic bytes:
# start	NUL NUL NUL 0x20 ftypM4V SPACE

,	'm4v' : {
		'start' : br'''
			\x00\x00\x00\x20
			\x66\x74\x79\x70
			\x4D\x34\x56\x20
		'''
	}

# MKV magic bytes:
# start	SUB EЯЈ
# end	м† (only in webm?)

,	'mkv' : {
		'start' : br'''
			\x1A\x45\xDF\xA3
		'''
	,	'end' : br'''
			\xEC\x86
		'''
	}

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

pat_non_digit = re.compile(br'\D')
pat_non_null = re.compile(br'[^\x00]')
pat_conseq_slashes = re.compile(r'[\\/]+')
pat_local_prefix = re.compile(r'(?P<Prefix>^[\\/]+[?][\\/]+)(?P<Path>.*?)$')

# local_path_prefix = u'//?/'
local_path_prefix = u''
timestamp_format = r'%Y-%m-%d %H:%M:%S'
tz_timestamp_format = r'%Y-%m-%d %H:%M:%S{f} %z %Z'
gm_timestamp_format = r'%Y-%m-%d %H:%M:%S{f} GMT'

a_type = type([])
d_type = type({})
s_type = type('')
u_type = type(u'')
b_type = type(b'')

# - Declare functions ---------------------------------------------------------

def is_iterable(v): return isinstance(v, Iterable)
def is_type_int(v): return isinstance(v, int)
def is_type_arr(v): return isinstance(v, a_type)
def is_type_bin(v): return isinstance(v, b_type)
def is_type_dic(v): return isinstance(v, d_type)
def is_type_str(v): return isinstance(v, s_type) or isinstance(v, u_type)

def get_hex_text_from_bytes(byte_string):
	try:
		# Since Python 3.5:
		# https://stackoverflow.com/a/36149089

		text = byte_string.hex()

	except AttributeError:

		# Equivalent in Python 2.x:
		# https://stackoverflow.com/a/54747809

		text = byte_string.encode('hex')

	return text.upper()

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

def get_bytes_length_text(value):
	return '{} bytes'.format(len(value) if is_iterable(value) else value)

def get_sorted_text_from_items(items, separator=', '):
	return separator.join(sorted(set(items)))

def get_dir_from_path(path):
	path = normalize_slashes(path)

	if path.find('/') >= 0:
		return path.rsplit('/', 1)[0]

	return ''

def get_file_name_from_path(path):
	path = normalize_slashes(path)

	if path.find('/') >= 0: path = path.rsplit('/', 1)[1]

	return path

def get_file_ext_from_path(path):
	path = normalize_slashes(path)

	if path.find('/') >= 0: path = path.rsplit('/', 1)[1]
	if path.find('.') >= 0: path = path.rsplit('.', 1)[1]

	return path.lower()

def get_file_path_without_ext(path):
	return (
		path[ : -len(get_file_ext_from_path(path)) - 1]
		# .rstrip('.')
		or path
	)

def normalize_slashes(path):
	return path.replace('\\', '/')

def fix_slashes(path):
	if os.sep != '/':
		path = path.replace('/', os.sep)

	if os.sep != '\\':
		path = path.replace('\\', os.sep)

	return path

def conflate_slashes(path):

	match = re.search(pat_local_prefix, path)

	return (
		local_path_prefix + re.sub(pat_conseq_slashes, '/', match.group('Path'))
		if match
		else
		re.sub(pat_conseq_slashes, '/', path)
	)

def get_path_with_local_prefix(path):

	match = re.search(pat_local_prefix, path)
	path = re.sub(pat_conseq_slashes, '/', match.group('Path') if match else path)

	return local_path_prefix + path.lstrip('/')

def remove_trailing_dots_in_path_parts(path):
	return '/'.join(
		part if part == '.' or part == '..'
		else part.rstrip('.')
		for part in normalize_slashes(path).split('/')
	)

def get_long_abs_path(path):
	if local_path_prefix:
		path = remove_trailing_dots_in_path_parts(path)

		if path.find(normalize_slashes(local_path_prefix)) == 0:
			return path
		else:
			return local_path_prefix + os.path.abspath(path)

	return fix_slashes(remove_trailing_dots_in_path_parts(path))

def print_with_colored_prefix_line(comment, value, color=None):
	print('')
	cprint(comment, color or 'yellow')
	print(value)

def print_with_colored_prefix(prefix, value, color=None):
	print('{prefix} {value}'.format(prefix=colored(prefix, color or 'yellow'), value=value))

def print_help():
	self_name = os.path.basename(__file__)
	max_file_type_length = 0

	for media_type in file_exts_by_type.keys():
		type_length = len(media_type)

		if max_file_type_length < type_length:
			max_file_type_length = type_length

	help_text_lines = [
		''
	,	colored('* Description:', 'yellow')
	,	'	Find and extract files of known formats stored as is inside other files.'
	,	'	Or truncate extraneous data at the end of files of known formats (for deduplication).'
	,	''
	,	colored('* Known file formats:', 'yellow')
	,	'	' + get_sorted_text_from_items(pat_parts_by_ext.keys())
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
	,	colored(' -s --silent', 'magenta') + '   : print nothing, usable for calling from another script.'
	,	colored(' -b --verbose', 'magenta') + '  : print more internal info, for testing and debug.'
	,	colored(' -r --recurse', 'magenta') + '  : go into subfolders, if given source path is a folder.'
	,	colored(' -l --long-time', 'magenta') + '  : print long detailed timestamps with fractional seconds and timezone.'
	,	colored(' -m --keep-time', 'magenta') + '  : set modification time of saved file to be same as original file.'
	,	colored(' -d --remove-old', 'magenta') + ' : delete original file after cutting extraneous data.'
	,	colored(' -i --in-place', 'magenta') + '   : save to original file after cutting extraneous data.'
	,	colored(' -f --in-folder', 'magenta') + '  : save extracted files to original folder. '
		+	colored('<dest>', 'cyan')
		+	' argument is not needed.'

	,	colored(' -e --truncate', 'magenta') + '     : cut extraneous bytes from content,'
		+	' added there to bypass duplicate file checks, and discard them.'

	,	colored(' -x --truncate-hex', 'magenta') + ' : cut extraneous bytes from content,'
		+	' and add them to saved file name as hex, like "(xFF...)".'

	,	colored(' -n --truncate-num', 'magenta') + ' : cut extraneous digits from content,'
		+	' and add them to saved file name as is, like "(dNN...)".'

	,	colored(' -c --content-in-arg', 'magenta') + ' : read content directly from '
		+	colored('<source>', 'cyan')
		+	' argument, not as path, and return a list of dictionaries, each with new file name and extracted content.'
	,	'	This is usable for calling from another script.'
	,	'	Otherwise, read files from path on disk, return success status (zero).'
	]+[
		(
			colored(
				' -' + media_type[0 : 1]
			+	' --' + media_type + (' ' * (max_file_type_length - len(media_type)))
			,	'magenta'
			)
			+	' : process only ' + media_type + ' files ('
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
		) for media_type, exts in file_exts_by_type.items()
	]+[
		colored(' .<ext>', 'magenta') + (' ' * (max_file_type_length - 1))
		+	' : process only files of given extensions, including all aliases.'
# TODO:	,	colored(' -a=<date> --after=<time>', 'magenta') + '  : process only files modified after given date or time.'
# TODO:	,	colored(' -b=<date> --before=<time>', 'magenta') + ' : process only files modified before given date or time.'
	,	''
	,	'Ending slashes in paths are optional.'
	,	'Dash or slash signs in other args are optional.'
	,	'Single-letter optional arguments can be concatenated, starting from single dash or slash.'
	,	'If file type restrictions are not given, all known types will be processed.'
	,	''
	,	colored('* Examples:', 'yellow')
	,	'	{0} "/read/from/folder/" "/save/to/folder/"'
	,	'	{0} "/read/from/folder/" --in-folder --recurse --test --video'
	,	'	{0} "/read/from/folder/" . --truncate --remove-old --picture'
	,	'	{0} "/read/from/folder/" -r t -def --quiet ".jpeg" ".mkv"'
	,	'	{0} "/read/from/file.dat" TEST --verbose'
	]

	print(u'\n'.join(help_text_lines).format(self_name))

def get_extracted_files(argv):
	return run_batch_extract(argv, '--content-in-arg') if len(argv) > 1 else []

# - Main job function ---------------------------------------------------------

def run_batch_extract(argv, *list_args, **keyword_args):

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

	def get_text_suffix_from_data(byte_string, found=None):

		if arg_truncate_n:

			if not re.search(pat_non_digit, byte_string):
				return '(d{})'.format(int(byte_string))

		if arg_truncate_x:

			if len(byte_string) > 1 and not re.search(pat_non_null, byte_string):
				return '(x00x{})'.format(len(byte_string))

			try:
				unrepeated_data = found.group('Repeated')

			except IndexError:
				unrepeated_data = None

			if unrepeated_data:
				unrepeated_byte_count = len(unrepeated_data)
				total_byte_count = len(byte_string)
				repeats_count = int(total_byte_count // unrepeated_byte_count)

				unrepeated_text_with_count = '{}x{}'.format(get_hex_text_from_bytes(unrepeated_data), repeats_count)

				if len(unrepeated_text_with_count) <= total_byte_count * 2:
					return '(x{})'.format(unrepeated_text_with_count)

			return '(x{})'.format(get_hex_text_from_bytes(byte_string))

		return ''

	def extract_from_file(source, dest_path):

		if arg_content:
			content = source
			src_file_path = fix_slashes(dest_path)
		else:
			content = None
			src_file_path = fix_slashes(source)

		if arg_content or arg_in_folder:
			dest_path = get_file_path_without_ext(src_file_path)

		file_type = src_file_ext = get_file_ext_from_path(src_file_path)

		for ext, aliases in file_ext_aliases_by_ext.items():
			if file_type in aliases:
				file_type = ext

				break

		if process_only_exts and not file_type in process_only_exts:
			return 0

		found_count_in_src_file = dest_file_size = 0

		for each_ext, each_pat in pat_file_content.items():

			if arg_truncate and each_ext != file_type:
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

			for found in each_pat.finditer(content):

				if arg_truncate:
					found_extra_data = found.group('Extra')

					if not found_extra_data:
						continue

				file_counts['found'] += 1
				found_count_in_src_file += 1
				found_count_of_one_type += 1

				dest_file_path = (
					src_file_path
					if arg_in_place
					else
					fix_slashes(
						u'{prefix}{suffix}.{ext}'
						.format(
							prefix=dest_path
						,	suffix=get_text_suffix_from_data(found_extra_data, found)
						,	ext=(src_file_ext or file_type or each_ext)
						)
						if arg_truncate and found_extra_data
						else
						u'{dir}/{index}.{ext}'
						.format(
							dir=dest_path
						,	index=found_count_of_one_type
						,	ext=each_ext
						)
					)
				)

				dest_file_exists = not arg_content and os.path.exists(dest_file_path)

				found_content_part = found.group('Content')
				found_file_size = len(found_content_part)

				found_files_to_save.append(
					{
						'name' : get_file_name_from_path(dest_file_path)
					,	'path' : dest_file_path
					,	'size' : found_file_size
					,	'content' : found_content_part
					}
					if arg_content
					else
					dest_file_path
				)

				if not arg_quiet or (not arg_silent and not arg_readonly_test):
					print_with_colored_prefix_line(
						'{what} file, {size}:'.format(
							what=('Result' if arg_content else 'Save')
						,	size=get_bytes_length_text(found_file_size)
						)
					,	dest_file_path
					)

				if not arg_quiet and dest_file_exists:
					cprint('Warning: file already exists at destination path.', 'yellow')

				if (
					not arg_readonly_test
				and	not arg_content
				and	found_content_part
				and	found_file_size > 0
				):
					dest_dir = get_dir_from_path(dest_file_path)

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
						if not arg_silent:
							print_with_colored_prefix_line('Cannot create folder:', dest_dir, 'red')
					else:
						file_counts['saved'] += 1

						dest_file = open(dest_file_path, 'wb')
						dest_file.write(found_content_part)
						dest_file.close()

						dest_file_size = os.path.getsize(dest_file_path)

						if arg_keep_time:
							os.utime(dest_file_path, (src_file_time, src_file_time))

						if not arg_silent:
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
										,	'{in_src} in source'
										,	'{of_type} of type {file_type}'
										]).format(
											total=file_counts['saved']
										,	in_src=found_count_in_src_file
										,	of_type=found_count_of_one_type
										,	file_type=file_type
										)
										if not arg_truncate and arg_verbose
										else file_counts['saved']
									)
								)
							,	get_bytes_length_text(dest_file_size)
								+ (
									', time set to '
								+	get_mod_time_text(src_file_time)
									if arg_keep_time
									else ''
								)
							,	'green'
							)

			if (
				not arg_silent
			and	not arg_truncate
			and	found_count_of_one_type > 0
			):
				print('')
				print_with_colored_prefix(
					'Found', u'{count} {file_type} files.'
					.format(
						count=found_count_of_one_type
					,	file_type=each_ext
					)
				,	'cyan'
				)

		if not content:
			return found_count_in_src_file

		if (
			found_count_in_src_file > 0
		and	arg_truncate
		and	arg_remove_old
		and	not arg_content
		and	not arg_in_place
		and	os.path.isfile(src_file_path)
		):
			if arg_readonly_test or dest_file_size > 0:
				if not arg_silent:
					print_with_colored_prefix_line('Delete file:', src_file_path)

				if not arg_readonly_test:
					os.remove(src_file_path)

					if not arg_silent:
						cprint('Deleted.', 'red')
			elif not arg_quiet:
				cprint('Skip deleting file, because nothing was saved.')

		if not arg_quiet:
			print('')
			print('	--------' * 4)

		return found_count_in_src_file

# - Collect arguments into one flat list --------------------------------------

	if not is_type_arr(argv):
		if (
			not is_iterable(argv)
		or	is_type_bin(argv)
		or	is_type_str(argv)
		):
			argv = [argv]
		else:
			argv = list(argv)

	if list_args and len(list_args) > 0:
		argv += list(list_args)

	if keyword_args:
		for k, v in keyword_args.items():
			argv.append(v)

	argc = len(argv)

# - Show help and exit --------------------------------------------------------

	if argc < 2:
		print_help()

		return 1

# - Check arguments -----------------------------------------------------------

	process_only_exts = []

	def get_path_arg_from(index, fix_path=True):
		arg = argv[index] if argc > index else ''

		if fix_path and (not arg_content or (arg and re.search(pat_conseq_slashes, arg))):
			return get_long_abs_path(arg or '.')

		return arg

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

	arg_content    = ('contentinarg' in optional_args or 'c' in optional_args)
	arg_in_place   = ('inplace'      in optional_args or 'i' in optional_args)
	arg_keep_time  = ('keeptime'     in optional_args or 'm' in optional_args)
	arg_long_time  = ('longtime'     in optional_args or 'l' in optional_args)
	arg_quiet      = ('quiet'        in optional_args or 'q' in optional_args)
	arg_recurse    = ('recurse'      in optional_args or 'r' in optional_args)
	arg_remove_old = ('removeold'    in optional_args or 'd' in optional_args)
	arg_silent     = ('silent'       in optional_args or 's' in optional_args)
	arg_truncate   = ('truncate'     in optional_args or 'e' in optional_args)
	arg_truncate_x = ('truncatehex'  in optional_args or 'x' in optional_args)
	arg_truncate_n = ('truncatenum'  in optional_args or 'n' in optional_args)
	arg_verbose    = ('verbose'      in optional_args or 'b' in optional_args)

	arg_quiet = arg_quiet or arg_silent
	arg_verbose = arg_verbose and not arg_quiet
	arg_truncate = arg_truncate or arg_truncate_x or arg_truncate_n

	src_content = get_path_arg_from(0, fix_path=False) if arg_content else None
	src_path    = get_path_arg_from(0) if not arg_content else None
	dest_path   = get_path_arg_from(1)

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
		if arg_content:
			src_path = dest_path
		else:
			dest_path = src_path

	if not arg_quiet:
		print_with_colored_prefix('Read only:', arg_readonly_test or arg_content)
		print_with_colored_prefix('Read path:',
			'<content in argument>' if arg_content else
			src_path
		)
		print_with_colored_prefix('Save path:',
			# '<return value>' if arg_content else
			'<same as source file>' if arg_in_folder else
			dest_path
		)
		print_with_colored_prefix('Optional args:', optional_args)

	for arg in optional_args:
		if arg[0 : 1] == '.':
			process_only_exts.append(arg.strip('.'))

	for media_type, exts in file_exts_by_type.items():
		if (
			media_type in optional_args
		or	media_type[0 : 1] in optional_args
		):
			process_only_exts += exts

	if len(process_only_exts) > 0:
		process_only_exts = sorted(set(process_only_exts))

		if not arg_quiet:
			print_with_colored_prefix('Processing only files of types:', process_only_exts)
	else:
		process_only_exts = None

	if arg_truncate:
		pat_part_singlefile_extra_data = br'|'.join(
			filter(
				bool
			,	[
					pat_part_singlefile_extra_digits if arg_truncate_n else None
				,	pat_part_singlefile_extra_nulls  if arg_truncate_x else None
				,	pat_part_singlefile_extra_bytes  if arg_truncate_x else None
				]
			)
		)

	for each_ext, each_pat_parts in pat_parts_by_ext.items():

		if process_only_exts and not each_ext in process_only_exts:
			continue

		start_mark_magic_bytes = (
			each_pat_parts.get('start') if is_type_dic(each_pat_parts) else
			each_pat_parts[0] if is_type_arr(each_pat_parts) else
			each_pat_parts
		)

		end_mark_magic_bytes = (
			each_pat_parts.get('end') if is_type_dic(each_pat_parts) else
			each_pat_parts[1] if is_type_arr(each_pat_parts) else
			None
		)

		pat_part_start_with_mark = (
			pat_part_start
		+	start_mark_magic_bytes
		+	pat_part_close
		)

		pat_part_end_with_mark = (
			pat_part_end
		+	end_mark_magic_bytes
		+	pat_part_close
		) if end_mark_magic_bytes else None

		pattern = (
			pat_part_singlefile_start
		+	pat_part_content
		+	pat_part_start_with_mark
		+	pat_part_singlefile_vary
		+	(
				(
					pat_part_end_with_mark
				+	pat_part_close		# <- end of actual content
				+	(
						pat_part_singlefile_extra_start
					+	pat_part_singlefile_extra_data
					+	pat_part_singlefile_extra_end
					)
				) if end_mark_magic_bytes
				else (
					pat_part_close
				+	pat_part_singlefile_extra_start
				+	pat_part_singlefile_extra_guess
				+	pat_part_singlefile_extra_end
				)
			)

		) if arg_truncate else (

			pat_part_content
		+	pat_part_start_with_mark
		+	pat_part_multifile_vary_start
		+	start_mark_magic_bytes		# <- avoid till the end of each sub-file
		+	pat_part_multifile_vary_end
		+	(
				pat_part_end_with_mark
				if end_mark_magic_bytes
				else b''
			)
		+	pat_part_close			# <- end of actual content
		)

		pat_file_content[each_ext] = regex = re.compile(pattern, re.X | re.DOTALL)

		if arg_verbose:
			print('')
			print_with_colored_prefix('File type:', each_ext)
			print_with_colored_prefix('Pattern:', pattern.decode(print_encoding))	# <- decode bytes to string
			print_with_colored_prefix('Regex:', regex)

# - Do the job ----------------------------------------------------------------

	found_files_to_save = []
	file_counts = {
		'found' : 0
	,	'saved' : 0
	}

	if not arg_content and os.path.isdir(src_path):

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
			src_content or src_path
		,	dest_path
		)

	if not arg_silent:
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

	return found_files_to_save if arg_content else 0

# - Run from commandline, when not imported as module -------------------------

if __name__ == '__main__':
	sys.exit(run_batch_extract(sys.argv[1 : ]))

# - End -----------------------------------------------------------------------
