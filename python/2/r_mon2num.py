#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
import os, sys

a_test = 't' in sys.argv	# <- add 't' for test output only
a_subst = 's' in sys.argv	# <- substitute, contrary to insert

mon = [
	['01','January']
,	['02','February']
,	['03','March']
,	['04','April']
,	['05','May']
,	['06','June']
,	['07','July']
,	['08','August']
,	['09','September']
,	['10','October']
,	['11','November']
,	['12','December']
]
src_list = os.listdir(u'.')
i = 0

for src in src_list:
	dest = src
	for m in mon:
		dest = dest.replace(m[1], m[0] if a_subst else m[0]+'_'+m[1])

	if dest != src:
		while os.path.exists(dest):
			dest = '(2).'.join(dest.rsplit('.', 1))

		print '\n', dest.encode('utf-8'), '\n', src.encode('utf-8')

		if os.path.exists(src):
			i += 1
			if not a_test:
				os.rename(src, dest)
			print '- OK #', i
		else:
			print '- File not found'
