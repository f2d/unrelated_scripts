#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import datetime, fnmatch, os, re, sys, time

if len(sys.argv) < 2:
	print 'For each file or folder find the latest timestamp inside and apply it on container.'
	print '\nUsage: touch.py [adfqrz] [<mask>] [<mask>] ...'
	print '\nExample: t.py adr'
	print '	a: Apply changes. Otherwise just show expected values.'
	print '	q: Quiet, do not print each working file or folder, only sum.'
	print '	r: Recursively go into subfolders.'
	print '	f: For each text file set its mod-time to latest timestamp inside.'
	print '	u: Set each file modtime to 1st found Unix-time stamp (first 10 digits) in filename.'
	print '	y: Set each file modtime to 1st found date-time stamp (yyyy*mm*dd*HH*MM*SS) in filename.'
#	print 'TODO ->	z: For each zip file set its mod-time to latest file inside.'
	print '	d: For each folder set its mod-time to latest file inside, before own.'
	print '<mask>: filename or wildcard to ignore for last time, if anything else exists.'
	sys.exit(0)

flag  = sys.argv[1]
masks = sys.argv[2:]

arg_a = 'a' in flag	# <- apply changes
arg_r = 'r' in flag	# <- subfolder recursion
arg_d = 'd' in flag	# <- set folder by files
arg_f = 'f' in flag	# <- set file by text content
arg_y = 'y' in flag	# <- set file by name (Y-m-d?H-M-S)
arg_u = 'u' in flag	# <- set file by name (unix time = first 10 digits)
#arg_z = 'z' in flag	# <- set zip by files
arg_v = not 'q' in flag	# <- verbose

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
count_changes = count_errors = count_found = count_read = 0

t0 = str(datetime.datetime.now())	# <- '2011-05-03 17:45:35.177000', from http://stackoverflow.com/a/5877368

def get_stamp_text(value):
	return time.strftime(fmt_date, time.localtime(value))

def get_stamp_value(text):
	return time.mktime(datetime.datetime.strptime(text, fmt_date).timetuple())

def read_file(path, mode='rb'):
	if not os.path.isfile(path):
		return ''
	f = open(path, mode)
	r = f.read()
	f.close()
	return r

def r(path):
	global count_changes, count_errors, count_found, count_read
	last_file_time_ex = last_file_time = 0

	try:
		names = os.listdir(path)
	except Exception:
		count_errors += 1
		return

	for name in names:
		count_found += 1
		full_path = path+'/'+name

		if not os.path.exists(full_path):
			continue

		if os.path.isdir(full_path):
			if arg_r:
				r(full_path)
		else:
			def check_time_in(last_time, text, pat=None):
				r = last_time
				for m in re.finditer(pat or pat_date, text):
					i = ''
					for e in exp_date:
						try:
							i = m.expand(e)
							break

						except Exception:
							continue

					if not i: i = get_stamp_text(int(m.group(1)))
					if r < i and i < t0: r = i
				return r

			d = 0
			t = ''
			if arg_u: t = check_time_in(t, name, pat_time)
			if arg_y: t = check_time_in(t, name, pat_date)
			if arg_y: t = check_time_in(t, name, pat_date_full_compact)
			if arg_f: t = check_time_in(t, read_file(full_path))

			if t:
				try:
					d = get_stamp_value(t)
				except Exception as e:
					print e
			if d:
				count_read += 1
				if arg_v:
					try:
						print count_read, t, d, full_path
					except Exception as e:
						print full_path.encode('utf-8')
				if arg_a:
					count_changes += 1
					os.utime(full_path, (d, d))
		if arg_d:
			m = os.path.getmtime(full_path)
			if last_file_time < m:
				last_file_time = m

			included = True

			for mask in masks:
				if fnmatch.fnmatch(name, mask):
					included = False
					break

			if included and last_file_time_ex < m:
				last_file_time_ex = m

	if arg_d:
		m = os.path.getmtime(path)
		d = last_file_time_ex or last_file_time
		if arg_v:
			try:
				print get_stamp_text(d), 'in', ('<' if d < m else '>' if d > m else '='), get_stamp_text(m), 'of', path
			except Exception:
				print path.encode('utf-8')
		if arg_a and d and (d < m or m < 9000):
			count_changes += 1
			os.utime(path, (d, d))

r(u'.')
print '- Done:'
if count_found:
	print count_found, 'found'
if count_changes:
	print count_changes, 'changed'
if count_errors:
	print count_errors, 'errors skipped'