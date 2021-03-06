#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Python 2 or 3 should work.

import datetime, fnmatch, io, os, re, sys, time, traceback

# Use colored text if available:
try:
	from termcolor import colored, cprint
	import colorama

	colorama.init()

except ImportError:
	def colored(*list_args, **keyword_args): return list_args[0]
	def cprint(*list_args, **keyword_args): print(list_args[0])

# - Configuration and defaults ------------------------------------------------

read_encodings = 'utf_8|utf_16_le|utf_16_be|cp1251'.split('|')

pat_time = re.compile(r'(?:^|[^a-z\d])(\d{10})', re.I)
pat_date = re.compile(r'''
	(?:^|\D)
	(\d{4})\D
	(\d\d)\D
	(\d\d)
	(?:\D
		(\d\d)\D
		(\d\d)
		(?:\D
			(\d\d)
		)?
	)?
	(?:$|\D)
''', re.I | re.X)

pat_date_full_compact = re.compile(r'''
	(?:^|\D)
	(\d{4})\D?
	(\d{2})\D?
	(\d{2})\D?
	(\d{2})\D?
	(\d{2})\D?
	(\d{2})
	(?:$|\D)
''', re.I | re.X)

exp_date = [
	r'\1-\2-\3 \4:\5:\6'
,	r'\1-\2-\3 \4:\5:00'
,	r'\1-\2-\3 00:00:00'
]

fmt_date = r'%Y-%m-%d %H:%M:%S'

t_min_valid = 60

# - Declare functions ---------------------------------------------------------

def print_with_colored_prefix(prefix, value, color=None):
	print('{} {}'.format(colored(prefix, color or 'yellow'), value))

def print_with_colored_suffix(value, suffix, color=None):
	print('{} {}'.format(value, colored(suffix, color or 'yellow')))

def print_help():
	self_name = os.path.basename(__file__)

	help_text_lines = [
		''
	,	colored('* Description:', 'yellow')
	,	'	For each file or folder find the latest timestamp inside and apply it on container.'
	,	''
	,	colored('* Usage:', 'yellow')
	,	'	{0}'
		+	colored(' <flags>', 'cyan')
		+	colored(' [<mask>] [<mask>] ...', 'magenta')
	,	''
	,	colored('<flags>', 'cyan') + ': string of letters in any order.'
	,	'	a: Apply changes. Otherwise just show expected values.'
	,	'	r: Recursively go into subfolders.'
	,	'	q: Quiet, print only final sum.'
	,	'	s: Silent, print nothing.'
	,	'	d: For each folder set its mod-time to latest file inside, before own.'
	,	'	f: For each text file set its mod-time to latest timestamp inside.'
	,	'	u: Set each file modtime to 1st found Unix-time stamp (first 10 digits) in filename.'
	,	'	y: Set each file modtime to 1st found date-time stamp (yyyy*mm*dd*HH*MM*SS) in filename.'
	# ,	'TODO ->	z: For each zip file set its mod-time to latest file inside.'
	,	''
	,	colored('<mask>', 'cyan') + ': filename or wildcard to ignore for last time, if anything else exists.'
	,	''
	,	colored('* Examples:', 'yellow')
	,	'	{0} drf'
	,	'	{0} adry'
	,	'	{0} adr "*.txt"'
	]

	print('\n'.join(help_text_lines).format(self_name))

def print_exception(title, path):
	print('')
	traceback.print_exc()

	print('')
	print_with_colored_prefix(title, path, 'red')

	print('')

def get_timestamp_text(value):
	return time.strftime(fmt_date, time.localtime(value))

def fix_timestamp_text(text):
	text = text.split(' ')
	text[0] = '-'.join([(x or '00') for x in text[0].split('-')])
	text[1] = ':'.join([(x or '00') for x in text[1].split(':')])
	text = ' '.join(text)

	return text

def get_timestamp_value(text):
	return time.mktime(datetime.datetime.strptime(fix_timestamp_text(text), fmt_date).timetuple())

def read_file(path, mode='r'):
	global arg_verbose

	if not os.path.isfile(path):
		return ''

	try:
		if 'b' in mode:
			file = open(path, mode)
			file_content = file.read()
		else:
			file = None
			file_content = ''

			for enc in read_encodings:
				if file:
					file.close()

				try:
					file = io.open(path, mode, encoding=enc)
					file_content = file.read()

					break

				except UnicodeDecodeError:
					continue

	# except PermissionError:
	# There was no PermissionError in Python 2.7, it was introduced in the Python 3.3 stream with PEP 3151.
	# https://stackoverflow.com/a/18199529

	except (IOError, OSError) as exception:
		if arg_verbose:
			print_exception('Error reading contents of file:', path)

	if file:
		file.close()

	return file_content

# - Main job function ---------------------------------------------------------

def run_batch_retime(argv):

	global arg_verbose
	global count_dirs_checked, count_dirs_changed, count_dirs_errors
	global count_files_checked, count_files_changed, count_files_errors, count_files_read

	def process_folder(path):

		global arg_verbose
		global count_dirs_checked, count_dirs_changed, count_dirs_errors
		global count_files_checked, count_files_changed, count_files_errors, count_files_read

		last_file_time_of_included = last_file_time = 0

		try:
			names = os.listdir(path)
		except:
			count_dirs_errors += 1

			return

		for name in names:
			path_name = path + '/' + name

			if os.path.isdir(path_name):
				count_dirs_checked += 1

				if arg_recurse:
					modtime_value = process_folder(path_name)

					if last_file_time < modtime_value:
						last_file_time = modtime_value

			elif os.path.isfile(path_name):
				count_files_checked += 1

				def check_time_in(last_time, text, pat=None):
					result = last_time

					for match in re.finditer(pat or pat_date, text):
						timestamp_text = ''

						for partial_format in exp_date:
							try:
								timestamp_text = match.expand(partial_format)

								break

							except:
								continue

						if not timestamp_text:
							timestamp_text = get_timestamp_text(int(match.group(1)))

						if result < timestamp_text and timestamp_text < t_now:
							result = timestamp_text
					return result

				timestamp_value = 0
				timestamp_text = ''

				if arg_files_modtime_by_name_unixtime:	timestamp_text = check_time_in(timestamp_text, name, pat_time)
				if arg_files_modtime_by_name_ymdhms:	timestamp_text = check_time_in(timestamp_text, name, pat_date)
				if arg_files_modtime_by_name_ymdhms:	timestamp_text = check_time_in(timestamp_text, name, pat_date_full_compact)
				if arg_files_modtime_by_content:	timestamp_text = check_time_in(timestamp_text, read_file(path_name))

				if timestamp_text:
					try:
						timestamp_value = get_timestamp_value(timestamp_text)
					except Exception as exception:
						if arg_verbose:
							print_exception('Error reading time text from file:', path_name)

						count_files_errors += 1

				if timestamp_value > t_min_valid:
					count_files_read += 1

					if arg_verbose:
						try:
							print(' '.join([
								colored(count_files_read, 'yellow')
							,	timestamp_text
							,	colored(timestamp_value, 'yellow')
							,	path_name
							]))
						except Exception as exception:
							print_exception('Error printing path info for:', path_name)

					if arg_apply:
						count_files_changed += 1

						os.utime(path_name, (timestamp_value, timestamp_value))

				if arg_folders_modtime_by_files:
					modtime_value = os.path.getmtime(path_name)

					if last_file_time < modtime_value:
						last_file_time = modtime_value

					included = True

					for mask in masks:
						if fnmatch.fnmatch(name, mask):
							included = False

							break

					if included and last_file_time_of_included < modtime_value:
						last_file_time_of_included = modtime_value

		timestamp_value = last_file_time_of_included or last_file_time
		modtime_value = 0

		if arg_folders_modtime_by_files:
			modtime_value = os.path.getmtime(path)

			if (
				timestamp_value > t_min_valid
			and	(
					timestamp_value < modtime_value
				or	modtime_value < t_min_valid
				)
			):
				if arg_verbose:
					try:
						comparison_sign = (
							'<' if timestamp_value < modtime_value else
							'>' if timestamp_value > modtime_value else
							'='
						)

						print(' '.join([
							get_timestamp_text(timestamp_value)
						,	colored('inside', 'yellow')
						,	comparison_sign
						,	colored('own', 'yellow')
						,	get_timestamp_text(modtime_value)
						,	colored('of', 'yellow')
						,	path
						]))
					except Exception as exception:
						print_exception('Error printing path info for:', path)

				if arg_apply:
					count_dirs_changed += 1

					os.utime(path, (timestamp_value, timestamp_value))

		return timestamp_value or modtime_value

# - Check arguments -----------------------------------------------------------

	argc = len(argv)

	flags = argv[0] if argc > 0 else ''

# - Show help and exit --------------------------------------------------------

	if argc < 1 or not flags or not len(flags) or 'h' in flags:
		print_help()

		return 1

# - Calculate params ----------------------------------------------------------

	masks = argv[1 : ]

	arg_apply = 'a' in flags
	arg_recurse = 'r' in flags
	arg_silent = 's' in flags
	arg_quiet = 'q' in flags
	arg_verbose = not (arg_silent or arg_quiet)
	arg_folders_modtime_by_files = 'd' in flags
	arg_files_modtime_by_content = 'f' in flags
	arg_files_modtime_by_name_ymdhms = 'y' in flags
	arg_files_modtime_by_name_unixtime = 'u' in flags
	# arg_zip_by_files_inside = 'z' in flags

	count_dirs_checked = count_dirs_changed = count_dirs_errors = 0
	count_files_checked = count_files_changed = count_files_errors = count_files_read = 0

	t_now = str(datetime.datetime.now())	# <- '2011-05-03 17:45:35.177000', from http://stackoverflow.com/a/5877368

# - Do the job ----------------------------------------------------------------

	result_value = process_folder(u'.')

# - Result summary ------------------------------------------------------------

	if not arg_silent:
		print('')
		cprint('- Done:', 'green')

		if count_dirs_checked:	print_with_colored_suffix(count_dirs_checked,	'folders checked.',		'cyan')
		if count_files_checked:	print_with_colored_suffix(count_files_checked,	'files checked.',		'cyan')
		if count_files_read:	print_with_colored_suffix(count_files_read,	'files contain timestamps.',	'cyan')

		if count_dirs_errors:	print_with_colored_suffix(count_dirs_errors,	'folders skipped with error.',	'red')
		if count_files_errors:	print_with_colored_suffix(count_files_errors,	'files skipped with error.',	'red')

		if count_dirs_changed:	print_with_colored_suffix(count_dirs_changed,	'folders changed.',		'green')
		if count_files_changed:	print_with_colored_suffix(count_files_changed,	'files changed.',		'green')

	return 0 if result_value else -1

# - Run from commandline, when not imported as module -------------------------

if __name__ == '__main__':
	sys.exit(run_batch_retime(sys.argv[1 : ]))

# - End -----------------------------------------------------------------------
