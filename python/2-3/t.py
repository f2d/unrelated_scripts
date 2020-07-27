#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Python 2 or 3 should work.

import datetime, fnmatch, io, os, re, sys, time

flags = sys.argv[1] if len(sys.argv) > 1 else ''

if len(sys.argv) < 2 or not flags or not len(flags) or 'h' in flags:
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
	,	'	q: Quiet, do not ,	each working file or folder, only sum.'
	,	'	r: Recursively go into subfolders.'
	,	'	f: For each text file set its mod-time to latest timestamp inside.'
	,	'	u: Set each file modtime to 1st found Unix-time stamp (first 10 digits) in filename.'
	,	'	y: Set each file modtime to 1st found date-time stamp (yyyy*mm*dd*HH*MM*SS) in filename.'
#	,	'TODO ->	z: For each zip file set its mod-time to latest file inside.'
	,	'	d: For each folder set its mod-time to latest file inside, before own.'
	,	'<mask>: filename or wildcard to ignore for last time, if anything else exists.'
	,	''
	,	'* Example:'
	,	'	%s adr'
	]

	print('\n'.join(help_text_lines).replace('%s', self_name))

	sys.exit(0)

masks = sys.argv[2:]

arg_apply = 'a' in flags			# <- apply changes
arg_recurse = 'r' in flags			# <- subfolder recursion
arg_folders_by_files = 'd' in flags		# <- set folder by files
arg_files_by_content = 'f' in flags		# <- set file by text content
arg_files_by_name_ymdhms = 'y' in flags		# <- set file by name (Y-m-d?H-M-S)
arg_files_by_name_unixtime = 'u' in flags	# <- set file by name (unix time = first 10 digits)
# arg_zip_by_files_inside = 'z' in flags	# <- set zip by files
arg_verbose = not 'q' in flags			# <- verbose

read_encodings = 'utf_8|utf_16_le|utf_16_be|cp1251'.split('|')

pat_time = re.compile(r'(?:^|[^a-z\d])(\d{10})', re.I)
pat_date = re.compile(r'''
	(?:^|[^a-z\d])
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
	(?:\D|$)
''', re.I | re.X)

pat_date_full_compact = re.compile(r'''
	(?:^|\D)
	(\d{4})\D?
	(\d{2})\D?
	(\d{2})\D?
	(\d{2})\D?
	(\d{2})\D?
	(\d{2})
	(?:\D|$)
''', re.I | re.X)

exp_date = [
	r'\1-\2-\3 \4:\5:\6'
,	r'\1-\2-\3 \4:\5:00'
,	r'\1-\2-\3 00:00:00'
]

fmt_date = r'%Y-%m-%d %H:%M:%S'

count_dirs_checked = count_dirs_changed = count_dirs_errors = 0
count_files_checked = count_files_changed = count_files_errors = count_files_read = 0

t0 = str(datetime.datetime.now())	# <- '2011-05-03 17:45:35.177000', from http://stackoverflow.com/a/5877368

def get_timestamp_text(value):
	return time.strftime(fmt_date, time.localtime(value))

def get_timestamp_value(text):
	return time.mktime(datetime.datetime.strptime(text.replace('::', '0:0:0').replace(' :', '0:0'), fmt_date).timetuple())

def read_file(path, mode='r'):
	if not os.path.isfile(path):
		return ''

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

	if file:
		file.close()

	return file_content

def process_folder(path):
	global count_dirs_checked, count_dirs_changed, count_dirs_errors
	global count_files_checked, count_files_changed, count_files_errors, count_files_read

	last_file_time_ex = last_file_time = 0

	try:
		names = os.listdir(path)
	except Exception:
		count_dirs_errors += 1

		return

	for name in names:
		full_path = path+'/'+name

		if not os.path.exists(full_path):
			continue

		if os.path.isdir(full_path):
			count_dirs_checked += 1

			if arg_recurse:
				process_folder(full_path)
		else:
			count_files_checked += 1

			def check_time_in(last_time, text, pat=None):
				result = last_time

				for match in re.finditer(pat or pat_date, text):
					timestamp_text = ''

					for partial_format in exp_date:
						try:
							timestamp_text = match.expand(partial_format)
							break

						except Exception:
							continue

					if not timestamp_text:
						timestamp_text = get_timestamp_text(int(match.group(1)))

					if result < timestamp_text and timestamp_text < t0:
						result = timestamp_text
				return result

			timestamp_value = 0
			timestamp_text = ''

			if arg_files_by_name_unixtime:	timestamp_text = check_time_in(timestamp_text, name, pat_time)
			if arg_files_by_name_ymdhms:	timestamp_text = check_time_in(timestamp_text, name, pat_date)
			if arg_files_by_name_ymdhms:	timestamp_text = check_time_in(timestamp_text, name, pat_date_full_compact)
			if arg_files_by_content:	timestamp_text = check_time_in(timestamp_text, read_file(full_path))

			if timestamp_text:
				try:
					timestamp_value = get_timestamp_value(timestamp_text)
				except Exception as e:
					if arg_verbose:
						print(e)

					count_files_errors += 1

			if timestamp_value:
				count_files_read += 1

				if arg_verbose:
					try:
						print('%d %s %d %s' % (
							count_files_read,
							timestamp_text,
							timestamp_value,
							full_path
						))
					except Exception as e:
						print(full_path.encode('utf-8'))
						print(e)

				if arg_apply:
					count_files_changed += 1

					os.utime(full_path, (timestamp_value, timestamp_value))

		if arg_folders_by_files:
			modtime_value = os.path.getmtime(full_path)
			if last_file_time < modtime_value:
				last_file_time = modtime_value

			included = True

			for mask in masks:
				if fnmatch.fnmatch(name, mask):
					included = False
					break

			if included and last_file_time_ex < modtime_value:
				last_file_time_ex = modtime_value

	if arg_folders_by_files:
		modtime_value = os.path.getmtime(path)
		timestamp_value = last_file_time_ex or last_file_time

		if arg_verbose:
			try:
				comparison_sign = (
					'<' if timestamp_value < modtime_value else
					'>' if timestamp_value > modtime_value else
					'='
				)

				print('%s in %s %s of %s' % (
					get_timestamp_text(timestamp_value),
					comparison_sign,
					get_timestamp_text(modtime_value),
					path
				))
			except Exception:
				print(path.encode('utf-8'))
				print(e)

		if arg_apply and timestamp_value and (timestamp_value < modtime_value or modtime_value < 9000):
			count_dirs_changed += 1

			os.utime(path, (timestamp_value, timestamp_value))

process_folder(u'.')

if arg_verbose:
	print('')
	print('- Done:')

	if count_files_checked:	print('%d files checked.'		% count_files_checked)
	if count_files_read:	print('%d files contain timestamps.'	% count_files_read)
	if count_files_changed:	print('%d files changed.'		% count_files_changed)
	if count_files_errors:	print('%d files skipped with error.'	% count_files_errors)
	if count_dirs_checked:	print('%d folders checked.'		% count_dirs_checked)
	if count_dirs_changed:	print('%d folders changed.'		% count_dirs_changed)
	if count_dirs_errors:	print('%d folders skipped with error.'	% count_dirs_errors)
