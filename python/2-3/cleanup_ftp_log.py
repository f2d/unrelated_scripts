#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Python 2 or 3 should work.

# TODO: 1. [v] dedup lines from trash IPs.
# TODO: 2. [v] skip trash commands (non-word/binary prefix, followed by "500 Syntax error, command unrecognized" line).

import os, re, sys

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

bad_content_placeholder = br'<...>'
pat_part_response_500 = br'500 Syntax error, command unrecognized.'

pat_log_line_normal_content = re.compile(br'''^(?:
	(?:\d{3}|[A-Z]{3}[A-Z0-9]?)(?:$|[\s-]+["'\w])
|	[A-Z]?[a-z]{5,}[\s/.,;:!?-]
)''', re.X)

pat_log_line = re.compile(br'[ \t]+'.join([
	br'(?P<LineMetaData>\((?P<ClientIDNumber>\d+)\)'
,	br'(?P<Date>\d+(?:[^\d\s]\d+){2})'
,	br'(?P<Time>\d+(?:[^\d\s]\d+){1,2})'
,	br'(?P<AMPM>[AP]M'
,	br')?-'
,	br'(?P<ClientLogin>\(not logged in\)|[^\r\n\(\)]+)'
,	br'\((?P<ClientIPAddress>\d+\.\d+\.\d+\.\d+)\)\>'
,	br')(?P<LineContent>[^\r\n]*)(?P<LineBreak>[\r\n]*)$'
]))

# - Declare functions ---------------------------------------------------------

def normalize_slashes(path):
	return path.replace('\\', '/')

def fix_slashes(path):
	if os.sep != '/':
		path = path.replace('/', os.sep)

	if os.sep != '\\':
		path = path.replace('\\', os.sep)

	return path

def get_file_name_from_path(path):
	path = normalize_slashes(path)

	if path.find('/') >= 0: path = path.rsplit('/', 1)[1]

	return path

def print_with_colored_prefix_line(comment, value, color=None):
	print('')
	cprint(comment, color or 'yellow')
	print(value)

def print_with_colored_prefix(prefix, value, color=None):
	print('{prefix} {value}'.format(prefix=colored(prefix, color or 'yellow'), value=value))

def print_help():
	self_name = os.path.basename(__file__)

	help_text_lines = [
		''
	,	colored('* Description:', 'yellow')
	,	'	Cleanup FileZilla FTP Server log files after DDoS.'
	,	''
	,	colored('* Usage:', 'yellow')
	,	'	{0}'
		+	colored(' <source> <dest>', 'cyan')
	#	+	colored(' <optional args> [1234567890] [R|recurse] <...>', 'magenta')	# for debug
	,	''
	,	colored('<source>', 'cyan') + ' : path to log file or folder with files to read.'
	,	colored('<dest>', 'cyan') + '   : path to file or folder to save filtered log lines.'
	,	'	If "TEST", do not save.'
	,	'	If file, append all lines into it from all source(s).'
	,	'	If folder, overwrite each file in it with same name as source file(s).'
	]

	print(u'\n'.join(help_text_lines).format(self_name))

# - Main job function ---------------------------------------------------------

def run_file_cleanup(argv, *list_args, **keyword_args):

	argc = len(argv)

# - Show help and exit --------------------------------------------------------

	if argc < 2:
		print_help()

		return 1

# - Check arguments -----------------------------------------------------------

	src_path = argv[0]
	dest_path = argv[1]

	arg_dest_isdir = os.path.isdir(dest_path)
	arg_max_line_count = int(argv[2]) if argc > 2 else 0
	arg_recurse = bool(argv[3][0].lower() == 'r') if argc > 3 else False

	arg_readonly_show = (
		r'TESTEST' == dest_path
	or	b'TESTEST' == dest_path
	)

	arg_readonly_test = (
		arg_readonly_show
	or	r'TEST' == dest_path
	or	b'TEST' == dest_path
	)

# - Do the job ----------------------------------------------------------------

	file_counts = {
		'found' : 0
	,	'saved' : 0
	}

	def process_file(src_path, dest_path):

		def write_line(content, skip_same=False):
			if skip_same and (
				line_contens['last_saved'] == content
			or	content in saved_lines
			):
				line_counts['skip_same'] += 1

				return

			line_counts['save'] += 1
			line_counts['save_bytes'] += len(content)
			line_contens['last_saved'] = content
			saved_lines.add(content)

			if dest_file:
				return dest_file.write(content)

		if (
			src_path == dest_path
		or	not os.path.isfile(src_path)
		):
			return 0

		file_counts['found'] += 1

		line_counts = {
			'read' : 0
		,	'save' : 0
		,	'save_bytes' : 0
		,	'skip_same' : 0
		,	'log_format' : 0
		,	'bad_format' : 0
		,	'bad_protocol' : 0
		}

		line_contens = {
			'last_saved' : ''
		}

		print('')
		print_with_colored_prefix(
			'File {}:'.format(file_counts['found'])
		,	src_path.encode(print_encoding)
		)

		print_with_colored_prefix(
			('Overwrite to:' if arg_readonly_test else 'Overwriting to:') if arg_dest_isdir else
			('Append to:'    if arg_readonly_test else 'Appending to:')
		,	dest_path.encode(print_encoding)
		)

		dest_file = None
		bad_last_line_match = None
		bad_last_line_by_user = {}
		bad_ips = set()
		saved_lines = set()

		with open(src_path, 'rb') as src_file:

			if arg_readonly_test:
				dest_file = None
			else:
				dest_file = open(dest_path, ('wb' if arg_dest_isdir else 'ab'))

			for each_line in src_file:
				line_counts['read'] += 1
				log_line_match = re.search(pat_log_line, each_line)

				if log_line_match:
					line_counts['log_format'] += 1

					line_content = log_line_match.group('LineContent')
					user_ip = log_line_match.group('ClientIPAddress')
					user_id = log_line_match.group('ClientIDNumber')

	# If unrecognized line was followed by 500 response, purify it and skip any following garbage from the same client:

					if line_content == pat_part_response_500:

						bad_last_line_match = bad_last_line_by_user.get(user_id)

						if not user_ip in bad_ips:
							if bad_last_line_match:
								command_len = len(bad_last_line_match.group('LineContent'))

								write_line(
									bad_last_line_match.group('LineMetaData')
								+	bad_content_placeholder
								+	' {} bytes'.format(command_len).encode(print_encoding)
								+	bad_last_line_match.group('LineBreak')
								)

							write_line(each_line)

						if bad_last_line_match:
							bad_ips.add(user_ip)

							if arg_readonly_show:
								# print(each_line)

								print_with_colored_prefix(
									bad_last_line_match.group('LineMetaData')
								,	bad_last_line_match.group('LineContent')
								)

						bad_last_line_by_user[user_id] = None

	# If unrecognized line format, keep it for checking server response line:

					elif not re.search(pat_log_line_normal_content, line_content):

						line_counts['bad_protocol'] += 1

						bad_last_line_by_user[user_id] = log_line_match

	# If unrecognized line was NOT followed by 500 response, save it:

					else:
						skip_same = (user_ip in bad_ips)
						bad_last_line_match = bad_last_line_by_user.get(user_id)

						if bad_last_line_match:
							write_line(bad_last_line_match.group(0), skip_same=skip_same)

							bad_last_line_by_user[user_id] = None

						write_line(each_line, skip_same=skip_same)
				else:
					line_counts['bad_format'] += 1

				if (
					arg_readonly_test
				and	arg_max_line_count > 0
				and	arg_max_line_count <= line_counts['read']
				):
					break

			if dest_file:
				dest_file.close()

		if line_counts['read'] > 0:
			print('{} lines total.'.format(line_counts['read']))

		if line_counts['log_format'] > 0:
			print('{} lines in log format.'.format(line_counts['log_format']))

		if line_counts['bad_format'] > 0:
			print('{} lines not matching log format.'.format(line_counts['bad_format']))

		if line_counts['bad_protocol'] > 0:
			print('{} log lines containing bad commands.'.format(line_counts['bad_protocol']))

		if line_counts['skip_same'] > 0:
			print('{} log lines with same content skipped.'.format(line_counts['skip_same']))

		if line_counts['save'] > 0:
			print(
				'{} log lines in {} bytes {}.'.format(
					line_counts['save']
				,	line_counts['save_bytes']
				,	('to overwrite' if arg_readonly_test else 'overwritten') if arg_dest_isdir else
					('to append'    if arg_readonly_test else 'appended')
				)
			)

		return 1

	if os.path.isdir(src_path):

		def process_folder(src_path):

			for name in os.listdir(src_path):
				each_src_path = fix_slashes(src_path + '/' + name)

				if os.path.isdir(each_src_path):
					if arg_recurse:
						process_folder(each_src_path)
				else:
					process_file(
						each_src_path
					,	fix_slashes(dest_path + '/' + name) if arg_dest_isdir else dest_path
					)

		process_folder(src_path)
	else:
		process_file(
			src_path
		,	fix_slashes(dest_path + '/' + get_file_name_from_path(src_path)) if arg_dest_isdir else dest_path
		)

	if file_counts['found'] > 0:
		print('')
		print_with_colored_prefix('Files found:', file_counts['found'], 'cyan')

		if file_counts['saved'] > 0:
			print_with_colored_prefix('Files saved:', file_counts['saved'], 'green')
	else:
		print('')
		cprint('Files not found.', 'cyan')

	return 1 if file_counts['saved'] > 0 else 0

# - Run from commandline, when not imported as module -------------------------

if __name__ == '__main__':
	sys.exit(run_file_cleanup(sys.argv[1 : ]))

# - End -----------------------------------------------------------------------
