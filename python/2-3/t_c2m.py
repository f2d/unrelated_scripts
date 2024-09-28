#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Python 2 or 3 should work.

# - Help screen shown on demand or without arguments --------------------------

def print_help():
	self_name = os.path.basename(__file__)

	help_text_lines = [
		''
	,	colored('* Description:', 'yellow')
	,	'	For each file get its timestamp of creation on the disk volume,'
	,	'	and if far enough, set file modification time to that.'
	,	''
	,	colored('* Usage:', 'yellow')
	,	'	{0}'
		+	colored(' <flags>', 'cyan')
		+	colored(' [<threshold>]', 'magenta')
	,	''
	,	colored('<flags>', 'cyan') + ': string of letters in any order.'
	,	'	a: Apply changes. Otherwise just show expected values.'
	,	'	r: Recursively go into subfolders.'
	,	'	t: Test output only, opposite of "a".'
	,	''
	,	colored('<threshold>', 'cyan') + ': Number in seconds, default = {} seconds = ~1 month.'.format(default_time_threshold)
	,	'	threshold > 0: Changes apply if ctime > mtime + threshold.'
	,	'	threshold < 0: Changes apply if ctime < mtime - threshold.'
	,	''
	,	colored('* Examples:', 'yellow')
	,	'	{0} tr'
	,	'	{0} ar 123'
	]

	print('\n'.join(help_text_lines).format(self_name))

# - Dependencies --------------------------------------------------------------

import datetime, os, sys

# Use colored text if available:
try:
	from termcolor import colored, cprint
	import colorama

	colorama.init()

except ImportError:
	def colored(*list_args, **keyword_args): return list_args[0]
	def cprint (*list_args, **keyword_args): print (list_args[0])

# - Configuration and defaults ------------------------------------------------

# print_encoding = 'unicode_escape'
print_encoding = sys.getfilesystemencoding() or 'utf-8'

default_time_threshold = 30*24*3600

# - Utility functions ---------------------------------------------------------

def get_text_encoded_for_print(text):
	return text.encode(print_encoding) if sys.version_info.major == 2 else text

def print_with_colored_prefix(comment, value, color=None):
	print('{} {}'.format(colored(comment, color or 'yellow'), value))

def print_with_colored_suffix(value, comment, color=None):
	print('{} {}'.format(value, colored(comment, color or 'yellow')))

# - Main job function ---------------------------------------------------------

def run_batch_retime(argv):

	global count_changed, count_checked, count_dirs_checked, count_files_checked

	def process_folder(path):

		global count_changed, count_checked, count_dirs_checked, count_files_checked

		for name in os.listdir(path):
			count_checked += 1

			filepath = path + '/' + name

			if os.path.isdir(filepath):
				if arg_recurse:
					count_dirs_checked += 1

					process_folder(filepath)
				continue

			count_files_checked += 1

		#	a_time = os.path.getatime(filepath)
			c_time = os.path.getctime(filepath)
			m_time = os.path.getmtime(filepath)

			time_difference = c_time - m_time

			if (
				time_difference > threshold if (threshold > 0) else
				time_difference < threshold
			):
				count_changed += 1

				print(' '.join([
					colored(count_checked, 'yellow')
				,	colored('c/m time diff =', 'cyan')
				,	'{:.2f}'.format(time_difference)
				,	colored('for file', 'cyan')
				,	get_text_encoded_for_print(filepath)
				]))

				if arg_apply:
					os.utime(filepath, (c_time, c_time))
			else:
				print(' '.join([
					colored(count_checked, 'yellow')
				,	colored('c/m time diff =', 'red')
				,	'{:.2f}'.format(time_difference)
				,	colored('for file', 'red')
				,	get_text_encoded_for_print(filepath)
				]))

			if arg_test and count_changed > 9:
				break

# - Show help and exit --------------------------------------------------------

	argc = len(argv)

	if argc < 1:
		print_help()

		return 1

# - Check arguments -----------------------------------------------------------

	flags = argv[0]
	arg_recurse = ('r' in flags)
	arg_verbose = ('t' in flags)
	arg_apply = ('a' in flags) and not arg_verbose
	arg_test = not arg_apply

	threshold = (int(argv[1]) if argc > 1 else 0) or default_time_threshold

	count_changed = count_checked = count_dirs_checked = count_files_checked = 0

# - Do the job ----------------------------------------------------------------

	print('')
	process_folder(u'.')

# - Result summary ------------------------------------------------------------

	print('')
	cprint('- Done:', 'green')

	if count_dirs_checked > 0:
		print_with_colored_suffix(count_dirs_checked, 'folders checked.')

	if count_files_checked > 0:
		print_with_colored_suffix(count_files_checked, 'files checked.')

	if count_changed > 0:
		if arg_apply:
			print_with_colored_suffix(count_changed, 'changed.', 'green')
		else:
			print_with_colored_suffix(count_changed, 'to change.', 'cyan')

	return 0

# - Run from commandline, when not imported as module -------------------------

if __name__ == '__main__':
	sys.exit(run_batch_retime(sys.argv[1 : ]))

# - End -----------------------------------------------------------------------
