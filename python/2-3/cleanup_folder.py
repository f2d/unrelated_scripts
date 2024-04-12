#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Python 2 or 3 should work.

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
	,	'	At least one age/size criteria is required.'
	,	''
	,	colored('* Usage:', 'yellow')
	,	'	{0}'
		+	colored(' [--age-above=<Number>]', 'cyan')
		+	colored(' [--age-below=<Number>]', 'cyan')
		+	colored(' [--size-above=<Number>]', 'cyan')
		+	colored(' [--size-below=<Number>]', 'cyan')
		+	colored(' [<dir/path>] [<dir/path2>] ...', 'magenta')
	,	''
	,	colored('	-o=<N> --older=<N>   --age-above=<Number>', 'cyan') + ':  pick files older than Number of seconds.'
	,	colored('	-n=<N> --newer=<N>   --age-below=<Number>', 'cyan') + ':  pick files newer than Number of seconds.'
	,	colored('	-l=<N> --larger=<N>  --size-above=<Number>', 'cyan') + ': pick files larger than Number of bytes.'
	,	colored('	-s=<N> --smaller=<N> --size-below=<Number>', 'cyan') + ': pick files smaller than Number of bytes.'
	,	''
	,	colored('	-t --test --read-only', 'magenta') + ': show picked files, do not delete anything.'
	,	colored('	-h, --help, /?       ', 'magenta') + ': show this help text, do nothing else.'
	,	''
	,	colored('* Examples:', 'yellow')
	,	'	{0} --newer=3600'
	,	'	{0} --age-above=60 --size-below=1024 . .. some/other/path'
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

	READ_ONLY = False
	arg_age_above = 0
	arg_age_below = 0
	arg_size_above = 0
	arg_size_below = 0
	src_dirs = []

	for each_arg in argv:

		if '-' == each_arg[0] and not (
			'.' in each_arg
		or	'/' in each_arg
		or	'\\' in each_arg
		):
			if '=' in each_arg:
				arg_name, arg_value = each_arg.split('=', 1)
			else:
				arg_name = each_arg
				arg_value = None

			arg_words = list(filter(bool, arg_name.split('-')))
			arg_what = arg_words[0]
			arg_how = arg_words[1] if len(arg_words) > 1 else None

			if (
				arg_what == 't'
			or	arg_what == 'test'
			or (	arg_what == 'read' and arg_how == 'only')
			):
				READ_ONLY = True

				continue
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

		src_dirs.append(each_arg)

	if not (
		arg_age_above
	or	arg_age_below
	or	arg_size_above
	or	arg_size_below
	):
		print_help()

		return 2

	if not len(src_dirs):
		src_dirs.append(default_src_dir)

	now_time = time.time()

	if READ_ONLY:
		print('')
		print_with_colored_prefix('READ_ONLY:', READ_ONLY)
		print_with_colored_prefix('now_time:', now_time)
		print_with_colored_prefix('arg_age_above:', arg_age_above)
		print_with_colored_prefix('arg_age_below:', arg_age_below)
		print_with_colored_prefix('arg_size_above:', arg_size_above)
		print_with_colored_prefix('arg_size_below:', arg_size_below)
		print_with_colored_prefix('src_dirs:', src_dirs)

	count_found_files = 0
	count_total_size = 0

	for each_dir in src_dirs:

		print('')
		print_with_colored_prefix('Search path:', each_dir.encode(print_encoding))

		if os.path.isdir(each_dir):
			src_names = list_dir_except_dots(each_dir)

			for each_name in src_names:
				file_path = normalize_slashes(each_dir + '/' + each_name)

				if os.path.isfile(file_path):
					file_size = os.path.getsize(file_path)
					file_mod_time = os.path.getmtime(file_path)
					file_age = now_time - file_mod_time

					if arg_age_above and file_age < arg_age_above: continue
					if arg_age_below and file_age > arg_age_below: continue
					if arg_size_above and file_size < arg_size_above: continue
					if arg_size_below and file_size > arg_size_below: continue

					count_found_files += 1
					count_total_size += file_size

					if READ_ONLY:
						print_with_colored_prefix(
							'Found:'
						,	'"{file}" {date}, {age} sec. old, {size} bytes'.format(
								file=each_name.encode(print_encoding)
							,	size=file_size
							,	age=file_age
							,	date=get_formatted_modtime(file_mod_time)
							)
						)
					else:
						print_with_colored_prefix(
							'Deleting:'
						,	'"{file}" {date}, {size} bytes'.format(
								file=each_name.encode(print_encoding)
							,	size=file_size
							,	date=get_formatted_modtime(file_mod_time)
							)
						)

						os.remove(file_path)
	print('')

	if count_found_files > 0:

		print_with_colored_prefix(
			'Files to delete:' if READ_ONLY else 'Deleted files:'
		,	'{number}, {size} bytes total'.format(
				number=count_found_files
			,	size=count_total_size
			)
		,	'cyan' if READ_ONLY else 'green'
		)

		return 0
	else:
		cprint('Found no files to delete.', 'red')

		return 10

# - Run from commandline, when not imported as module -------------------------

if __name__ == '__main__':
	sys.exit(run_cleanup_folder(sys.argv[1 : ]))

# - End -----------------------------------------------------------------------
