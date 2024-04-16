#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Python 2 or 3 should work.

# Use case - cleanup old Firefox cache2 folder before creating backup archive.
# This script imitates command like the following, which is slow, as it must spawn new cmd process for each file:
# FORFILES /M ?* /D -1 /C "cmd /c if @fsize leq 4234 echo @file @fdate @ftime @fsize && del /F /Q @file"

import datetime, os, sys, time

# Use colored text if available:
try:
	from termcolor import colored, cprint
	import colorama

	colorama.init()

except ImportError:
	def colored(*list_args, **keyword_args): return list_args[0]
	def cprint (*list_args, **keyword_args): print (list_args[0])

# - Configuration and defaults ------------------------------------------------

print_encoding = sys.stdout.encoding or sys.getfilesystemencoding() or 'utf-8'

timestamp_format = r'%Y-%m-%d %H:%M:%S'
default_src_dir = u'.'

# - Declare functions ---------------------------------------------------------

def print_help():
	self_name = os.path.basename(__file__)

	help_text_lines = [
		''
	,	colored('* Description:', 'yellow')
	,	'	In each given folder, find and delete all files which meet given age/size criteria.'
	,	'	At least one age/size criteria number > 0 is required.'
	,	'	Files of age/size equal to given criteria are included.'
	,	''
	,	colored('* Usage:', 'yellow')
	,	'	{0}'
		+	colored(' [--age-above=<N>]', 'cyan')
		+	colored(' [--age-below=<N>]', 'cyan')
		+	colored(' [--size-above=<N>]', 'cyan')
		+	colored(' [--size-below=<N>]', 'cyan')
		+	colored(' [--include=<Text>]', 'cyan')
		+	colored(' [--exclude=<Text>]', 'cyan')
		+	colored(' [<dir/path>] [<dir/path2>] ...', 'magenta')
	,	''
	,	colored('	-o=<N> --older=<N>   --age-above=<Number> ', 'cyan') + ': pick files older than Number of seconds.'
	,	colored('	-n=<N> --newer=<N>   --age-below=<Number> ', 'cyan') + ': pick files newer than Number of seconds.'
	,	colored('	-l=<N> --larger=<N>  --size-above=<Number>', 'cyan') + ': pick files larger than Number of bytes.'
	,	colored('	-s=<N> --smaller=<N> --size-below=<Number>', 'cyan') + ': pick files smaller than Number of bytes.'
	,	''
	,	colored('	-i=<T> --include=<T> --contains=<Text>   ', 'cyan') + ': pick files containing given text.'
	,	colored('	-x=<T> --exclude=<T> --contains-no=<Text>', 'cyan') + ': skip files containing given text.'
	,		'		Multiple arguments are supported, any match counts.'
	,		'		Exclude arguments have precedence before include.'
	,		'		Search is performed for each line, case sensitive.'
	,		'		Line breaks are not supported.'
	,	''
	,	colored('	-r --recurse         ', 'magenta') + ': process subfolders in each given path.'
	,	colored('	-m --name-last       ', 'magenta') + ': show each file name last, after dates and sizes.'
	,	colored('	-t --test --read-only', 'magenta') + ': show picked files, do not delete anything.'
	,	colored('	-h --help /?         ', 'magenta') + ': show this help text, do nothing else.'
	,	''
	,	colored('* Examples:', 'yellow')
	,	'	{0} --newer=3600 -r -m -t'
	,	'	{0} --older=60 --smaller=8000 "--contains=304 Not Modified"'
	,	'	{0} --age-above=60 --size-below=1024 . .. some/other/path "--contains-no=skip this"'
	,	'	{0} "--contains=Argument with spaces must be in quotes" "--contains=possibly other text"'
	]

	print('\n'.join(help_text_lines).format(self_name))

def print_with_colored_prefix(prefix, value, color=None):
	try:
		print('{} {}'.format(colored(prefix, color or 'yellow'), value))

	except UnicodeEncodeError:
		print('{} {} {}'.format(
			colored(prefix, color or 'yellow')
		,	colored('<not showing unprintable unicode>', 'red')
		,	value.encode('utf_8').decode('ascii', 'ignore')	# https://stackoverflow.com/a/62658901
		))

def is_not_dots(path):

	return len(
		path
		.replace('\\', '')
		.replace('/', '')
		.replace('.', '')
	) > 0

def list_dir_except_dots(path):

	return filter(is_not_dots, os.listdir(path))

def normalize_slashes(path):

	return path.replace('\\', '/')

def get_formatted_modtime(mtime, format=timestamp_format):
	return datetime.datetime.fromtimestamp(mtime).strftime(format)

# - Main job function ---------------------------------------------------------

def run_cleanup_folder(argv):

	argc = len(argv)

	if (
		argc < 1
	or	'/?' in argv
	or	'-h' in argv
	or	'--help' in argv
	):
		print_help()

		return 1

	arg_exclude_by_content = False
	arg_include_by_content = False
	arg_name_last = False
	arg_read_only = False
	arg_recurse = False

	arg_age_above = 0
	arg_age_below = 0
	arg_size_above = 0
	arg_size_below = 0

	exclude_content_parts = []
	include_content_parts = []
	src_dirs = []

	for each_arg in argv:

		if '-' == each_arg[0]:
			if '=' in each_arg:
				arg_name, arg_value = each_arg.split('=', 1)
			else:
				arg_name = each_arg
				arg_value = None

			arg_words = list(filter(bool, arg_name.split('-')))
			arg_what = arg_words[0]
			arg_how = arg_words[1] if len(arg_words) > 1 else None

			if (
				arg_value
			and	len(arg_value) > 0
			):
				if (
					arg_what == 'x'
				or	arg_what == 'exclude'
				or (	arg_what == 'contains' and arg_how == 'no')
				):
					arg_exclude_by_content = True
					exclude_content_parts.append(arg_value.encode(print_encoding))

					continue
				if (
					arg_what == 'i'
				or	arg_what == 'include'
				or (	arg_what == 'contains' and not arg_how)
				):
					arg_include_by_content = True
					include_content_parts.append(arg_value.encode(print_encoding))

					continue

			if not (
				'.' in each_arg
			or	'/' in each_arg
			or	'\\' in each_arg
			):
				if (
					arg_value
				and	len(arg_value.strip()) > 0
				):
					if (
						arg_what == 'o'
					or	arg_what == 'older'
					or (	arg_what == 'age' and arg_how == 'above')
					):
						arg_age_above = int(arg_value)

						continue
					if (
						arg_what == 'n'
					or	arg_what == 'newer'
					or (	arg_what == 'age' and arg_how == 'below')
					):
						arg_age_below = int(arg_value)

						continue
					if (
						arg_what == 'l'
					or	arg_what == 'larger'
					or (	arg_what == 'size' and arg_how == 'above')
					):
						arg_size_above = int(arg_value)

						continue
					if (
						arg_what == 's'
					or	arg_what == 'smaller'
					or (	arg_what == 'size' and arg_how == 'below')
					):
						arg_size_below = int(arg_value)

						continue
				if (
					arg_what == 'm'
				or (	arg_what == 'name' and arg_how == 'last')
				):
					arg_name_last = True

					continue
				if (
					arg_what == 'r'
				or	arg_what == 'recurse'
				):
					arg_recurse = True

					continue
				if (
					arg_what == 't'
				or	arg_what == 'test'
				or (	arg_what == 'read' and arg_how == 'only')
				):
					arg_read_only = True

					continue

		src_dirs.append(each_arg)

	if not (
		arg_age_above > 0
	or	arg_age_below > 0
	or	arg_size_above > 0
	or	arg_size_below > 0
	):
		print_help()

		return 2

	if not len(src_dirs):
		src_dirs.append(default_src_dir)

	arg_contains = arg_exclude_by_content or arg_include_by_content
	now_time = time.time()

	if arg_read_only:
		print('')
		print_with_colored_prefix('now_time:', now_time)
		print_with_colored_prefix('arg_age_above:', arg_age_above)
		print_with_colored_prefix('arg_age_below:', arg_age_below)
		print_with_colored_prefix('arg_size_above:', arg_size_above)
		print_with_colored_prefix('arg_size_below:', arg_size_below)
		print_with_colored_prefix('arg_read_only:', arg_read_only)
		print_with_colored_prefix('arg_contains:', arg_contains)
		print_with_colored_prefix('arg_exclude_by_content:', arg_exclude_by_content)
		print_with_colored_prefix('arg_include_by_content:', arg_include_by_content)
		print_with_colored_prefix('exclude_content_parts:', exclude_content_parts)
		print_with_colored_prefix('include_content_parts:', include_content_parts)
		print_with_colored_prefix('src_dirs:', src_dirs)

	count_found_files = 0
	count_total_size = 0
	min_found_size = 0
	max_found_size = 0

	each_file_print_format = (
		('' if arg_name_last else '"{file}" ')
	+	'{date}'
	+	(', {age} sec. old' if arg_read_only else '')
	+	', {size} bytes'
	+	(' "{file}"' if arg_name_last else '')
	)

	def is_file_content_included(full_path):

		file_matched = (arg_exclude_by_content and not arg_include_by_content)

		with open(full_path, 'rb') as src_file:
			for each_line in src_file:

			# Exclude arguments have priority, completely skip file after first matched line:

				if arg_exclude_by_content:
					for each_part in exclude_content_parts:
						if each_part in each_line:
							return False

				if arg_include_by_content and not file_matched:
					for each_part in include_content_parts:
						if each_part in each_line:

			# If given both exclude and include, stop iterating arguments and continue reading file:

							if arg_exclude_by_content:
								file_matched = True

								break

			# If include arguments only, pick file and stop reading after first matched line:

							else:
								return True
		return file_matched

	for each_dir in src_dirs:

		print('')
		print_with_colored_prefix('Search path:', each_dir.encode(print_encoding))

		if os.path.isdir(each_dir):
			src_names = list_dir_except_dots(each_dir)

			for each_name in src_names:
				full_path = normalize_slashes(each_dir + '/' + each_name)

				if os.path.isfile(full_path):
					file_size = os.path.getsize(full_path)

					if arg_size_above and file_size < arg_size_above: continue
					if arg_size_below and file_size > arg_size_below: continue

					file_mod_time = os.path.getmtime(full_path)
					file_age = now_time - file_mod_time

					if arg_age_above and file_age < arg_age_above: continue
					if arg_age_below and file_age > arg_age_below: continue
					if arg_contains and not is_file_content_included(full_path): continue

					count_found_files += 1
					count_total_size += file_size

					if not min_found_size or min_found_size > file_size: min_found_size = file_size
					if not max_found_size or max_found_size < file_size: max_found_size = file_size

					if arg_read_only:
						print_with_colored_prefix(
							'Found:'
						,	each_file_print_format.format(
								file=each_name.encode(print_encoding)
							,	size=file_size
							,	age=file_age
							,	date=get_formatted_modtime(file_mod_time)
							)
						)
					else:
						print_with_colored_prefix(
							'Deleting:'
						,	each_file_print_format.format(
								file=each_name.encode(print_encoding)
							,	size=file_size
							,	date=get_formatted_modtime(file_mod_time)
							)
						)

						os.remove(full_path)

				elif arg_recurse and os.path.isdir(full_path):

					src_dirs.append(full_path)
	print('')

	if count_found_files > 0:

		print_with_colored_prefix(
			'Files to delete:' if arg_read_only else 'Deleted files:'
		,	'{number}, total {size} bytes, min {min}, max {max} bytes.'.format(
				number=count_found_files
			,	size=count_total_size
			,	min=min_found_size
			,	max=max_found_size
			)
		,	'cyan' if arg_read_only else 'green'
		)

		return 0
	else:
		cprint('Found no files to delete.', 'red')

		return 10

# - Run from commandline, when not imported as module -------------------------

if __name__ == '__main__':
	sys.exit(run_cleanup_folder(sys.argv[1 : ]))

# - End -----------------------------------------------------------------------
