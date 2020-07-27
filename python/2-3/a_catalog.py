#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Python 2 or 3 should work.

import datetime, os, re, subprocess, sys, time

# - config: -------------------------------------------------------------------

root_path = u'.'
time_format = ';_%Y-%m-%d,%H-%M-%S'

pat_normalize_title = [
	[re.compile(r'[;_]*\d{4}(\D\d\d){5}'), '']
]

# - functions: ----------------------------------------------------------------

def encode_cmd(cmd_array):
	fse = sys.getfilesystemencoding()
	return [(arg.encode(fse) if isinstance(arg,unicode) else arg) for arg in cmd_array]

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
	return (folder+'/' if folder else '') + (name+add+'.'+ext).rstrip('.')

def get_dest_name(src):
	if not os.path.exists(src):
		return ''

	d = datetime.datetime.fromtimestamp(os.path.getmtime(src)).strftime(time_format)
	d = t = add_before_ext(src, d)
	i = 1
	while os.path.exists(d):
		i += 1
		d = add_before_ext(t, '('+i+')')
	if i > 1:
		print('+', i, 'duplicate(s)')
	return d

# - run names colection: ------------------------------------------------------

src_list = os.listdir(root_path)
names = []

for name in src_list:
	path = root_path+'/'+name
	if os.path.isdir(path):
		n = name
		for pat in pat_normalize_title:
			n = re.sub(pat[0], pat[1], n)
		if len(n) > 0 and not n in names:
			names.append(n)
		n = get_dest_name(root_path+'/'+n)
		if n and n != path:
			print(path)
			print(n)
			os.rename(path, n)

if len(names) > 0:
	names.sort()
	suffix = ',[' + ','.join(names) + ']'
else:
	suffix = ''

# - run batch archiving: ------------------------------------------------------

import a

a.run_batch_archiving(['7r_sdm;=_catalog_htm>'+suffix, '.', '..'])
