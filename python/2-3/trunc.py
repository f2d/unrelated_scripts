#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import os, sys

# Use colored text if available:
try:
	from termcolor import colored, cprint
	import colorama

	colorama.init()

except ImportError:
	def colored(*list_args, **keyword_args): return list_args[0]
	def cprint (*list_args, **keyword_args): print (list_args[0])

# - Configuration and defaults ------------------------------------------------

default_file_size = 1000
default_root_path = u'.'

# - Declare functions ---------------------------------------------------------

def print_with_colored_prefix(comment, value, color=None):
	print('{} {}'.format(colored(comment, color or 'yellow'), value))

def print_with_colored_suffix(value, comment, color=None):
	print('{} {}'.format(value, colored(comment, color or 'yellow')))

def print_help():
	self_name = os.path.basename(__file__)

	help_text_lines = [
		''
	,	colored('* Description:', 'yellow')
	,	'	Truncate all files to given size.'
	,	''
	,	colored('* Usage:', 'yellow')
	,	'	{0}'
		+	colored(' <size>', 'cyan')
		+	colored(' [<filepath>] [<filepath>] ...', 'magenta')
	,	''
	,	colored('<size>', 'cyan') + ': desired file size in bytes.'
	,	'	If not a number, use {}.'.format(default_file_size)
	,	''
	,	colored('<filepath>', 'cyan') + ': path to file.'
	,	'	If no file paths given, truncate all files in current folder.'
	,	''
	,	colored('* Examples:', 'yellow')
	,	'	{0} default_size'
	,	'	{0} 1234 example_name.txt ../example_path.txt'
	]

	print('\n'.join(help_text_lines).format(self_name))

# - Main job function ---------------------------------------------------------

def run_batch_truncate(argv):

# - Show help and exit --------------------------------------------------------

	argc = len(argv)

	if argc < 1:
		print_help()

		return 1

# - Check arguments -----------------------------------------------------------

	try:
		target_file_size = int(argv[0])
	except:
		target_file_size = default_file_size

	path_list = argv[1 : ] if argc > 1 else os.listdir(default_root_path)

	print('')
	print_with_colored_prefix('Truncating files to:', '{} bytes.'.format(target_file_size))
	print('')

	count_done = count_errors = 0

# - Do the job ----------------------------------------------------------------

	for file_path in path_list:
		if os.path.isfile(file_path):
			print(file_path)

			f = open(file_path, 'r+b')
			f.truncate(target_file_size)
			f.close()

			count_done += 1
		else:
			print_with_colored_prefix('Not a file:', file_path, 'red')

			count_errors += 1

# - Result summary ------------------------------------------------------------

	if count_done > 0 or count_errors > 0:
		print('')

		if count_done > 0:
			print_with_colored_suffix(count_done, 'files truncated to {} bytes.'.format(target_file_size), 'green')

		if count_errors > 0:
			print_with_colored_suffix(count_errors, 'errors.', 'red')

			return -2
	else:
		print('No result.')

		return -1

	return 0

# - Run from commandline, when not imported as module -------------------------

if __name__ == '__main__':
	sys.exit(run_batch_truncate(sys.argv[1 : ]))

# - End -----------------------------------------------------------------------
