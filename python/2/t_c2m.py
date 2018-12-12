#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import datetime, os, sys

if len(sys.argv) < 2:
	print 'For each file get its timestamp of creation on the disk volume, and'
	print 'if far enough, set file modification time to that.'
	print
	print 'Usage: t_c2m.py [art] [threshold]'
	print '	a: Apply changes. Otherwise just show expected values.'
	print '	r: Recursively go into subfolders.'
	print '	t: opposite of "a".'
	print '	threshold: Number in seconds, default = 30*24*3600 seconds = ~1 month.'
	print '	threshold > 0: Changes apply if ctime > mtime + threshold.'
	print '	threshold < 0: Changes apply if ctime < mtime - threshold.'
	sys.exit(0)

n_c = n_d = n_f = n_i = 0	# <- count iterations, changes, etc

flag = sys.argv[1]
a_r = 'r' in flag
a_c = ('a' in flag) and not ('t' in flag)
a_t = not a_c

threshold = int(sys.argv[2]) if len(sys.argv) > 2 and int(sys.argv[2]) else 30*24*3600

def r(path):
	global n_c, n_d, n_f, n_i
	for name in os.listdir(path):
		n_i += 1
		f = path+'/'+name
		if os.path.isdir(f):
			if a_r:
				n_d += 1
				r(f)
			continue
		n_f += 1
	#	a = os.path.getatime(f)
		c = os.path.getctime(f)
		m = os.path.getmtime(f)
		t = c-m

		if (t > threshold if (threshold > 0) else t < threshold):
			n_c += 1
			print "%d	%.2f	%s" % (n_i, t, f.encode('utf-8'))
			if a_c:
				os.utime(f, (c, c))

		if a_t and n_c > 9:
			break

r(u'.')
print '\n', n_d, 'dirs,', n_f, 'files,', n_c, 'changes', 'done' if a_c else 'pending'
