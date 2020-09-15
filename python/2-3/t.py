#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Python 2 or 3 should work.

import datetime, fnmatch, io, os, re, sys, time

# Use colored text if available:
try:
	from termcolor import colored, cprint
	import colorama

	colorama.init()

except ImportError:
	def colored(*list_args, **keyword_args): return list_args[0]
	def cprint(*list_args, **keyword_args): print(list_args[0])

print_encoding = sys.getfilesystemencoding() or 'utf-8'
argc = len(sys.argv)

flags = sys.argv[1] if argc > 1 else ''

if argc < 2 or not flags or not len(flags) or 'h' in flags:
	self_name = os.path.basename(__file__)

	help_text_lines = [
		''
	,	'* Description:'
	,	'	For each file or folder find the latest timestamp inside and apply it on container.'
	,	''
	,	'* Usage:'
	,	'	%s <flags> [<mask>] [<mask>] ...'
	,	''
	,	'<flags>: string of letters in any order.'
	,	'	a: Apply changes. Otherwise just show expected values.'
	,	'	r: Recursively go into subfolders.'
	,	'	q: Quiet, print only final sum.'
	,	'	s: Silent, print nothing.'
	,	'	d: For each folder set its mod-time to latest file inside, before own.'
	,	'	f: For each text file set its mod-time to latest timestamp inside.'
	,	'	u: Set each file modtime to 1st found Unix-time stamp (first 10 digits) in filename.'
	,	'	y: Set each file modtime to 1st found date-time stamp (yyyy*mm*dd*HH*MM*SS) in filename.'
#	,	'TODO ->	z: For each zip file set its mod-time to latest file inside.'
	,	'<mask>: filename or wildcard to ignore for last time, if anything else exists.'
	,	''
	,	'* Example:'
	,	'	%s adr'
	]

	print('\n'.join(help_text_lines).replace('%s', self_name))

	sys.exit(0)

masks = sys.argv[2:]

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

count_dirs_checked = count_dirs_changed = count_dirs_errors = 0
count_files_checked = count_files_changed = count_files_errors = count_files_read = 0

t_min_valid = 60
t_now = str(datetime.datetime.now())	# <- '2011-05-03 17:45:35.177000', from http://stackoverflow.com/a/5877368

def print_exception(title, exception=None, path=None):
	cprint(title, 'red')

	if path is not None:
		print('"%s"' % path.encode(print_encoding))

	if exception is not None:
		print(exception)

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
			print_exception('Error reading contents of file:', exception, path)

	if file:
		file.close()

	return file_content

def process_folder(path):
	global count_dirs_checked, count_dirs_changed, count_dirs_errors
	global count_files_checked, count_files_changed, count_files_errors, count_files_read

	last_file_time_of_included = last_file_time = 0

	try:
		names = os.listdir(path)
	except:
		count_dirs_errors += 1

		return

	for name in names:
		path_name = path+'/'+name

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
						print_exception('Error reading time text from file:', exception, path_name)

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
						print_exception('Error printing path info for:', exception, path_name)

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
					print_exception('Error printing path info for:', exception, path)

			if arg_apply:
				count_dirs_changed += 1

				os.utime(path, (timestamp_value, timestamp_value))

	return timestamp_value or modtime_value

process_folder(u'.')

if not arg_silent:
	print('')
	cprint('- Done:', 'green')

	if count_dirs_checked:	print('%d %s' % (count_dirs_checked,	colored('folders checked.',		'cyan')))
	if count_files_checked:	print('%d %s' % (count_files_checked,	colored('files checked.',		'cyan')))
	if count_files_read:	print('%d %s' % (count_files_read,	colored('files contain timestamps.',	'cyan')))

	if count_dirs_errors:	print('%d %s' % (count_dirs_errors,	colored('folders skipped with error.',	'red')))
	if count_files_errors:	print('%d %s' % (count_files_errors,	colored('files skipped with error.',	'red')))

	if count_dirs_changed:	print('%d %s' % (count_dirs_changed,	colored('folders changed.',		'green')))
	if count_files_changed:	print('%d %s' % (count_files_changed,	colored('files changed.',		'green')))
