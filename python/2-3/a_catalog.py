#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Python 2 or 3 should work.

# Use case - for a bunch of catalog HTML files in per board:
# 1) Add timestamp to each HTML file name without one.
# 2) Make 1 archive (7z or Rar) named like this: "_catalog_htm;_Y-m-d,H-M-S,[subdir1,subdir2,<...>],solid.ext"
# 3) Delete source files and subfolders.

# - Dependencies --------------------------------------------------------------

import datetime, os, re, subprocess, sys, time

# Custom script from this folder:
from a import run_batch_archiving

# - Configuration and defaults ------------------------------------------------

default_root_path = u'.'
time_format = ';_%Y-%m-%d,%H-%M-%S'

pat_normalize_title = [
	[re.compile(r'[;_]*\d{4}(\D\d\d){5}'), '']
]

# - Utility functions ---------------------------------------------------------

def pad_list(a, minimum_len=2, pad_value=''):
	diff = minimum_len - len(a)

	return (a + [pad_value] * diff) if diff > 0 else a

def add_before_ext(path, add):
	if path.find('/') < 0:
		folder = None
		name = path
	else:
		folder, name = pad_list(path.rsplit('/', 1))

	name, ext = pad_list(name.rsplit('.', 1))

	return (folder + '/' if folder else '') + (name + add + '.' + ext).rstrip('.')

def get_path_with_timestamp(src_path):
	if not os.path.exists(src_path):
		return ''

	dest_path = datetime.datetime.fromtimestamp(os.path.getmtime(src_path)).strftime(time_format)
	dest_path = temp_path = add_before_ext(src_path, dest_path)
	try_count = 1

	while os.path.exists(dest_path):
		try_count += 1
		dest_path = add_before_ext(temp_path, '({})'.format(try_count))

	if try_count > 1:
		print('+ {} name duplicate(s)'.format(try_count))

	return dest_path

def get_label(root_path, fix_timestamps=True):
	src_list = os.listdir(root_path)
	names = []

	for name in src_list:
		src_path = root_path + '/' + name

		if os.path.isdir(src_path):
			new_name = name

			for pat in pat_normalize_title:
				new_name = re.sub(pat[0], pat[1], new_name)

			if len(new_name) > 0 and not new_name in names:
				names.append(new_name)

			if fix_timestamps:
				dest_path = get_path_with_timestamp(root_path + '/' + new_name)

				if dest_path and dest_path != src_path:
					print(src_path)
					print(dest_path)

					os.rename(src_path, dest_path)

	if len(names) > 0:
		return ',[' + ','.join(sorted(names)) + ']'

	return ''

# - Main job function ---------------------------------------------------------

def run_catalog_batch_archiving(argv):
	root_path     = argv[0]    if len(argv) > 0 else default_root_path
	archive_types = argv[1]    if len(argv) > 1 else '7rs'
	archive_args  = argv[2 : ] if len(argv) > 2 else []
	archive_label = get_label(root_path)

	if archive_label:
		return run_batch_archiving([archive_types + '_dom;=_catalog_htm>' + archive_label, '.', '..'] + archive_args)
	else:
		print('')
		print('Nothing to archive.')

		return 1

# - Run from commandline, when not imported as module -------------------------

if __name__ == '__main__':
	sys.exit(run_catalog_batch_archiving(sys.argv[1 : ]))

# - End -----------------------------------------------------------------------
