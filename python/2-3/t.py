#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Python 2 or 3 should work.

# - Help screen shown on demand or without arguments --------------------------

def print_help():
	self_name = os.path.basename(__file__)

	help_text_lines = [
		''
	,	colored('* Description:', 'yellow')
	,	'	For each file and/or folder, find the latest timestamp inside and set it as modification time of the container.'
	,	''
	,	colored('* Usage:', 'yellow')
	,	'	{0}'
		+	colored(' <flags>', 'cyan')
		+	colored(' [<mask>] [<mask>] ...', 'magenta')
	,	''
	,	colored('<flags>', 'cyan') + ': string of letters in any order.'
	,	'	s: Silent, print nothing.'
	,	'	q: Quiet, print only final sum.'
	,	'	v: Verbose, print more intermediate information for debug.'
	,	'	w: Show all collected warnings and errors at the end.'
	,	''
	,	'	a: Apply changes if mod-time is after (later than) found.'
	,	'	b: Apply changes if mod-time is before (earlier than) found.'
	,	'		Otherwise just show expected values.'
	,	''
	,	'	r: Recursively go into subfolders.'
	,	'	e: Delete empty folders.'
	,	''
	,	'	d: Set each folder mod-time to latest file inside.'
	,	'	i: Set each folder mod-time to latest folder inside.'
	# ,	'TODO ->	z: Set each zip file mod-time to latest file inside.'
	,	''
	,	'	f: Set each file mod-time to 1st found date-time stamp (yyyy?mm?dd(?HH?MM(?SS))) in its content.'
	,	'	y: Set each file mod-time to 1st found date-time stamp (yyyy?mm?dd(?HH?MM(?SS))) in its name.'
	,	'	u: Set each file mod-time to 1st found Unix-time stamp (first 10 consecutive digits) in its name.'
	,	'		Note: timestamps in names may be compact (yyyymmdd),'
	,	'		while timestamps in content must have delimiters (yyyy-mm-dd).'
	,	''
	,	'	1: Set each file mod-time to 1st found time on the last line in file name/content.'
	,	'	l: Set each file mod-time to last found time in file name/content.'
	,	'	m: Set each file mod-time to latest found time in file name/content.'
	,	'	n: Set each file mod-time to earliest found time in file name/content.'
	,	'		Note: last in the whole file, not 1st on the last line,'
	,	'		may be found after any log-formatted timestamps,'
	,	'		including partial timestamps (e.g. dates, y-m-d only) in log content.'
	,	''
	,	colored('<mask>', 'cyan') + ': filename or wildcard to ignore for time checking, if anything else exists.'
	,	''
	,	colored('* Examples:', 'yellow')
	,	'	{0} dirf'
	,	'	{0} adry'
	,	'	{0} abdir "*.txt"'
	]

	print('\n'.join(help_text_lines).format(self_name))

# - Dependencies --------------------------------------------------------------

from email.utils import parsedate
import datetime, fnmatch, io, os, re, sys, time, traceback

# Use colored text if available:
try:
	from termcolor import colored, cprint
	import colorama

	colorama.init()

except ImportError:
	def colored(*list_args, **keyword_args): return list_args[0]
	def cprint (*list_args, **keyword_args): print (list_args[0])

# - Configuration and defaults ------------------------------------------------

read_encodings = 'utf_8|utf_16_le|utf_16_be|cp1251'.split('|')

exp_date = [
	r'\g<Year>-\g<Month>-\g<Day> \g<Hours>:\g<Minutes>:\g<Seconds>'
,	r'\g<Year>-\g<Month>-\g<Day> \g<Hours>:\g<Minutes>:00'
,	r'\g<Year>-\g<Month>-\g<Day> 00:00:00'
# ,	r'\1-\2-\3 \4:\5:\6'
# ,	r'\1-\2-\3 \4:\5:00'
# ,	r'\1-\2-\3 00:00:00'
]

fmt_date = r'%Y-%m-%d %H:%M:%S'

t_min_valid = 60

# - Utility functions ---------------------------------------------------------

def print_with_colored_prefix(prefix, value, color=None):
	try:
		print('{} {}'.format(colored(prefix, color or 'yellow'), value))

	except UnicodeEncodeError:
		print('{} {} {}'.format(
			colored(prefix, color or 'yellow')
		,	colored('<not showing unprintable unicode>', 'red')
		,	value.encode('utf_8').decode('ascii', 'ignore')	# https://stackoverflow.com/a/62658901
		))

def print_with_colored_suffix(value, suffix, color=None):
	try:
		print('{} {}'.format(value, colored(suffix, color or 'yellow')))

	except UnicodeEncodeError:
		print('{} {} {}'.format(
			value.encode('utf_8').decode('ascii', 'ignore')	# https://stackoverflow.com/a/62658901
		,	colored('<not showing unprintable unicode>', 'red')
		,	colored(suffix, color or 'yellow')
		))

def print_exception(title, path):
	print('')
	traceback.print_exc()

	print('')
	print_with_colored_prefix(title, path, 'red')

	print('')

def get_match_group_or_none(match, index=0):
	try:
		return match.group(index)

	except IndexError:
		return None

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

def get_timestamp_value_from_parsedate(text):
	return time.mktime(datetime.datetime(*parsedate(text)[ : 6]).timetuple())

# - Main job function ---------------------------------------------------------

def run_batch_retime(argv):

	def print_and_collect_exception(title, path):
		print_exception(title, path)

		if arg_collect_error_messages:
			if len(error_messages) > 0:
				last_error_message = error_messages[-1 : ][0]

				if last_error_message[0] == title and last_error_message[1] == path:
					return

			error_messages.append([title, path])

	def read_file(path, mode='r'):

		if not os.path.isfile(path):
			return ''

		file = file_content = None

		try:
			if 'b' in mode:
				file = open(path, mode)
				file_content = file.read()
			else:
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
			print_and_collect_exception('Error reading contents of file:', path)

			counts['files_errors'].add(path)

		if file:
			file.close()

		return file_content

	def process_folder(path):

		def check_time_in(last_time, text, pat=None, read_mode=None):

			if read_mode and text and len(text) > 0:
				text = read_file(text, read_mode)

			if not text or not len(text):
				return last_time

			result = last_time

			if arg_verbose_testing:
				print_with_colored_prefix('File size:', len(text), 'yellow')

			for match in re.finditer(pat or pat_date, text):
				timestamp_text = ''

				if arg_verbose_testing:
					print_with_colored_prefix('Match text:', match.group(0), 'magenta')
					print_with_colored_prefix('Match parts:', match.groups(), 'magenta')

				for partial_format in exp_date:
					try:
						timestamp_text = match.expand(partial_format)

					except TypeError:
						timestamp_text = match.expand(bytes(partial_format, 'utf_8')).decode('utf_8')

					except (KeyError, IndexError, re.error):
						continue

					except re.error:
						if arg_verbose_testing:
							print_and_collect_exception(
								'Text "{match}" does not match pattern "{pattern}" in file:'
								.format(
									match=match.group(0)
								,	pattern=partial_format
								)
							,	path_name
							)

						continue

					except Exception as exception:
						if arg_verbose:
							print_and_collect_exception('Error matching time text from file:', path_name)

						continue

					if arg_verbose_testing:
						print_with_colored_prefix('Timestamp text:', (timestamp_text or None), 'cyan')

					if timestamp_text:
						break

				if not timestamp_text:
					timestamp_value = None

					dmy_or_mdy = (
						get_match_group_or_none(match, 'Date')
					or	get_match_group_or_none(match, 'DMY')
					or	get_match_group_or_none(match, 'MDY')
					)

					if dmy_or_mdy:
						hms_or_zero = (
							get_match_group_or_none(match, 'HMS')
						or	'00:00'
						)

						tz_or_gmt = (
							get_match_group_or_none(match, 'TimeZone')
						or	'GMT'
						)

						timestamp_to_parse = '{} {} {}'.format(
							dmy_or_mdy.strip()
						,	hms_or_zero.strip()
						,	tz_or_gmt.strip()
						)

						if arg_verbose_testing:
							print_with_colored_prefix('Text to parse:', timestamp_to_parse, 'magenta')

						try:
							timestamp_value = get_timestamp_value_from_parsedate(timestamp_to_parse)

						except Exception as exception:
							if arg_verbose_testing:
								print_and_collect_exception(
									'Error parsing time from "{text}" in file:'
									.format(text=timestamp_to_parse)
								,	path_name
								)
					else:
						epoch_or_anything = (
							get_match_group_or_none(match, 'Epoch')
						or	get_match_group_or_none(match, 1)
						or	get_match_group_or_none(match, 0)
						)

						if epoch_or_anything:
							timestamp_value = int(epoch_or_anything)

					if arg_verbose_testing:
						print_with_colored_prefix('Timestamp value:', (timestamp_value or None), 'magenta')

					if timestamp_value:
						timestamp_text = get_timestamp_text(timestamp_value)

						if arg_verbose_testing:
							print_with_colored_prefix('Timestamp text:', (timestamp_text or None), 'cyan')

				if (
					timestamp_text
				and	timestamp_text < t_now
				and	(
						not result
					or	arg_files_modtime_last
					or	arg_files_modtime_1st_in_last_line
					or	(arg_files_modtime_max and result < timestamp_text)
					or	(arg_files_modtime_min and result > timestamp_text)
					)
				):
					result = timestamp_text
			return result

		modtime_value = empty_folders_inside_to_delete = 0
		last_file_time = last_file_time_of_included = 0

		try:
			names = os.listdir(path)
		except:
			counts['dirs_errors'].add(path)

			return 0

		excluded_names = []

		for name in names:
			path_name = path + '/' + name

			if os.path.isdir(path_name):
				counts['dirs_checked'] += 1

				if arg_recurse:
					modtime_value = process_folder(path_name)

					if arg_delete_empty_folders:
						if (
							modtime_value
						and	modtime_value < 0
						):
							empty_folders_inside_to_delete += 1

					elif arg_dirs_modtime_by_dirs:
						if (
							modtime_value
						or	modtime_value < 0
						):
							modtime_value = os.path.getmtime(path_name)

					if (
						modtime_value
					and	modtime_value > 0
					and	modtime_value > last_file_time
					):
						last_file_time = modtime_value

						if arg_dirs_modtime_by_dirs and last_file_time_of_included < modtime_value:
							last_file_time_of_included = modtime_value

			elif os.path.isfile(path_name):

				included = True

				for mask in masks:
					if fnmatch.fnmatch(name, mask):
						included = False

						excluded_names.append(name)

						break

				if not included:
					continue

				counts['files_checked'] += 1

				timestamp_value = 0
				timestamp_text = ''

				if arg_files_modtime_by_name_unixtime:
					timestamp_text = check_time_in(timestamp_text, name, pat_time)

				if arg_files_modtime_by_name_ymdhms:
					timestamp_text = check_time_in(timestamp_text, name, pat_date)
					timestamp_text = check_time_in(timestamp_text, name, pat_date_full_compact)

				if arg_files_modtime_by_content:
					timestamp_text = check_time_in(timestamp_text, path_name, pat_date, 'r')
					timestamp_text = check_time_in(timestamp_text, path_name, pat_date_binary, 'rb')

				if timestamp_text:
					try:
						timestamp_value = get_timestamp_value(timestamp_text)

					except Exception as exception:
						if arg_verbose:
							print_and_collect_exception('Error reading time text from file:', path_name)

						counts['files_errors'].add(path)

				if timestamp_value > t_min_valid:
					counts['files_read'] += 1

					if arg_verbose:
						try:
							print_with_colored_prefix(
								' '.join([
									colored(counts['files_read'], 'yellow')
								,	timestamp_text
								,	colored(timestamp_value, 'yellow')
								])
							,	path_name
							,	'white'
							)

						except Exception as exception:
							print_and_collect_exception('Error printing path info for:', path_name)

					if arg_apply:
						modtime_value = os.path.getmtime(path_name)

						if modtime_value and (
							(arg_apply_to_after  and modtime_value > timestamp_value)
						or	(arg_apply_to_before and modtime_value < timestamp_value)
						):
							counts['files_changed'] += 1

							os.utime(path_name, (timestamp_value, timestamp_value))

				if arg_dirs_modtime_by_files:
					modtime_value = os.path.getmtime(path_name)

					if (
						modtime_value
					and	modtime_value > 0
					and	modtime_value > last_file_time
					):
						last_file_time = modtime_value

						if included and last_file_time_of_included < modtime_value:
							last_file_time_of_included = modtime_value

		if arg_delete_empty_folders and	(
			not names
		or	len(names) == empty_folders_inside_to_delete
		):
			if arg_verbose_testing:
				path = os.path.abspath(path)

			try:
				if arg_apply:
					os.rmdir(path)

				counts['dirs_deleted'] += 1

				if arg_verbose:
					print_with_colored_prefix(
						' '.join([
							str(counts['dirs_deleted'])
						,	colored(
								'empty folder deleted:' if arg_apply else
								'empty folder found:'
							,	'yellow'
							)
						])
					,	path
					,	'white'
					)
			except:
				if arg_verbose:
					print_and_collect_exception('Error deleting empty folder:', path)

				counts['dirs_errors'].add(path)

			return -1

		if arg_dirs_modtime_by_dirs or arg_dirs_modtime_by_files:

			timestamp_value = last_file_time_of_included or last_file_time
			modtime_value = os.path.getmtime(path)

			if (
				modtime_value
			and	timestamp_value
			and	timestamp_value > t_min_valid
			and	(
					modtime_value < t_min_valid
				or	(arg_apply_to_after  and modtime_value > timestamp_value)
				or	(arg_apply_to_before and modtime_value < timestamp_value)
				)
			):
				if arg_verbose:
					try:
						comparison_sign = (
							'<' if timestamp_value < modtime_value else
							'>' if timestamp_value > modtime_value else
							'='
						)

						print_with_colored_prefix(
							' '.join([
								get_timestamp_text(timestamp_value)
							,	colored('inside', 'yellow')
							,	comparison_sign
							,	colored('own', 'yellow')
							,	get_timestamp_text(modtime_value)
							,	colored('of', 'yellow')
							])
						,	path
						,	'white'
						)

					except Exception as exception:
						print_and_collect_exception('Error printing path info for:', path)

				if arg_apply and (
					(arg_apply_to_after  and modtime_value > timestamp_value)
				or	(arg_apply_to_before and modtime_value < timestamp_value)
				):
					counts['dirs_changed'] += 1

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

	arg_apply_to_after = 'a' in flags
	arg_apply_to_before = 'b' in flags
	arg_apply = arg_apply_to_after or arg_apply_to_before

	arg_recurse = 'r' in flags
	arg_silent = 's' in flags
	arg_quiet = 'q' in flags
	arg_verbose_testing = 'v' in flags
	arg_verbose = arg_verbose_testing or not (arg_silent or arg_quiet)
	arg_collect_error_messages = 'w' in flags

	arg_delete_empty_folders = 'e' in flags
	arg_dirs_modtime_by_dirs = 'i' in flags
	arg_dirs_modtime_by_files = 'd' in flags
	arg_files_modtime_by_content = 'f' in flags
	arg_files_modtime_by_name_ymdhms = 'y' in flags
	arg_files_modtime_by_name_unixtime = 'u' in flags
	arg_files_modtime_1st_in_last_line = '1' in flags
	arg_files_modtime_last = 'l' in flags
	arg_files_modtime_max = 'm' in flags
	arg_files_modtime_min = 'n' in flags
	# arg_zip_by_files_inside = 'z' in flags

	pat_part_end_of_line_or_timestamp = (
		r'(?:$|[^\d\r\n][^\r\n]*)' if arg_files_modtime_1st_in_last_line else
		r'(?:$|\D)'
	)

	pat_text_date = r'''
		(?P<Date>
			(?P<YMD>
				# 2001-02-03 04:05:06.789
				# mpc20010203040506
				# vlcsnap-2001-02-03-04h05m06s789

				(?:^|(?<=\D))
				(?P<Year>\d{4})				[^a-z:\d]
				(?P<Month>\d\d)				[^a-z:\d]
				(?P<Day>\d\d)
			)
		|	(?:
				# Sat, 03 Feb 2001 04:05:06 -0000
				# 03 Feb 2001 04:05:06
				# Feb 03 2001, 04:05:06

				(?:^|(?<=[^a-z0-9]))
				(?:
					(?P<WeekDay>[a-z]{3})		[,\s]+
				)?
				(?:
					(?P<DMY>
						(?P<DMYDay>\d\d?)	\s+
						(?P<DMYMonth>[a-z]{3})	[,\s]+
						(?P<DMYYear>\d{4})
					)
				|	(?P<MDY>
						(?P<MDYMonth>[a-z]{3})	\s+
						(?P<MDYDay>\d\d?)	[,\s]+
						(?P<MDYYear>\d{4})
					)
				)
			)
		)
		(?P<Time>
								(?:\D|[,\s]+(?:at\s+)?)
			(?P<HMS>
				(?P<Hours>\d\d?)		(?:h|[^a-z\d])
				(?P<Minutes>\d\d)
				(?:
								(?:m|[^a-z\d])
					(?P<Seconds>\d\d)
								s?
				)?
			)
			(?:
								[,\s]+
				(?P<TimeZone>
					(?:(?:GMT|UTC)?[+-])?
					\d\d\:?\d\d
				)
			)?
		)?
	''' + pat_part_end_of_line_or_timestamp

	pat_text_date_full_compact = r'''
		(?:^|\D)
		(?P<Year>\d{4})		[^a-z\d]?
		(?P<Month>\d{2})	[^a-z\d]?
		(?P<Day>\d{2})		\D?
		(?P<Hours>\d{2})	(?:h|[^a-z\d])?
		(?P<Minutes>\d{2})	(?:m|[^a-z\d])?
		(?P<Seconds>\d{2})	s?
	''' + pat_part_end_of_line_or_timestamp

	pat_text_time_epoch = r'''
	#	(?:^|\D)
		(?:^|[^a-z\d])
		(?P<Epoch>\d{10})
	#	(?P<Milliseconds>\d{3})?
		(?P<Etc>\d{1,6})?
		(?:$|[^a-z\d])
	# ''' + pat_part_end_of_line_or_timestamp

	pat_time = re.compile(pat_text_time_epoch, re.I | re.X)
	pat_date = re.compile(pat_text_date, re.I | re.X)
	pat_date_full_compact = re.compile(pat_text_date_full_compact, re.I | re.X)

	try:
		pat_date_binary = re.compile(bytes(pat_text_date, 'utf_8'), re.I | re.X)
	except TypeError:
		pat_date_binary = pat_date

	if arg_collect_error_messages:
		error_messages = []

	counts = {
		'dirs_changed' : 0
	,	'dirs_checked' : 0
	,	'dirs_deleted' : 0
	,	'dirs_errors' : set()
	,	'files_changed' : 0
	,	'files_checked' : 0
	,	'files_errors' : set()
	,	'files_read' : 0
	}

	t_now = str(datetime.datetime.now())	# <- '2011-05-03 17:45:35.177000', from http://stackoverflow.com/a/5877368

# - Do the job ----------------------------------------------------------------

	result_value = process_folder(u'.')

# - Result summary ------------------------------------------------------------

	if not arg_silent:
		print('')

		if arg_collect_error_messages and len(error_messages) > 0:
			cprint('- Done, errors:', 'green')

			for (title, path) in error_messages:
				print_with_colored_prefix(title, path, 'red')
		else:
			cprint('- Done:', 'green')

		if counts['dirs_checked']:	print_with_colored_suffix(counts['dirs_checked'],	'folders checked.',		'cyan')
		if counts['files_checked']:	print_with_colored_suffix(counts['files_checked'],	'files checked.',		'cyan')
		if counts['files_read']:	print_with_colored_suffix(counts['files_read'],		'files contain timestamps.',	'cyan')

		if counts['dirs_errors']:	print_with_colored_suffix(len(counts['dirs_errors']),	'folders skipped with error.',	'red')
		if counts['files_errors']:	print_with_colored_suffix(len(counts['files_errors']),	'files skipped with error.',	'red')

		if counts['dirs_changed']:	print_with_colored_suffix(counts['dirs_changed'],	'folders changed.',		'green')
		if counts['files_changed']:	print_with_colored_suffix(counts['files_changed'],	'files changed.',		'green')

		if counts['dirs_deleted']:	print_with_colored_suffix(
			counts['dirs_deleted']
		,	'empty folders deleted.' if arg_apply else
			'empty folders to delete.'
		,	'magenta'
		)

	return 0 if result_value else -1

# - Run from commandline, when not imported as module -------------------------

if __name__ == '__main__':
	sys.exit(run_batch_retime(sys.argv[1 : ]))

# - End -----------------------------------------------------------------------
