#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Python 2 or 3 should work.

import datetime, os, sys

print_encoding = sys.getfilesystemencoding() or 'utf-8'
argc = len(sys.argv)

if argc < 2:
	self_name = os.path.basename(__file__)

	help_text_lines = [
		''
	,	'Description:'
	,	'	For each file get its timestamp of creation on the disk volume,'
	,	'	and if far enough, set file modification time to that.'
	,	''
	,	'Usage:'
	,	'	%s <flags> [<threshold>]'
	,	''
	,	'<flags>: string of letters in any order.'
	,	'	a: Apply changes. Otherwise just show expected values.'
	,	'	r: Recursively go into subfolders.'
	,	'	t: Test output only, opposite of "a".'
	,	''
	,	'<threshold>: Number in seconds, default = 30*24*3600 seconds = ~1 month.'
	,	'	threshold > 0: Changes apply if ctime > mtime + threshold.'
	,	'	threshold < 0: Changes apply if ctime < mtime - threshold.'
	]

	print('\n'.join(help_text_lines).replace('%s', self_name))

	sys.exit(0)

count_changed = count_checked = count_dirs_checked = count_files_checked = 0

flags = sys.argv[1]
arg_recurse = 'r' in flags
arg_apply = ('a' in flags) and not ('t' in flags)
arg_test = not arg_apply

threshold = (int(sys.argv[2]) if argc > 2 else 0) or 30*24*3600

def process_folder(path):
	global count_changed, count_checked, count_dirs_checked, count_files_checked

	for name in os.listdir(path):
		count_checked += 1

		filepath = path+'/'+name

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
			print('%d	t_diff = %.2f	%s' % (count_checked, time_difference, filepath.encode('utf-8')))

			if arg_apply:
				os.utime(filepath, (c_time, c_time))

		if arg_test and count_changed > 9:
			break

print('')
process_folder(u'.')

print('')
print('%d dirs, %d files, %d changes %s.' % (count_dirs_checked, count_files_checked, count_changed, 'done' if arg_apply else 'pending'))
