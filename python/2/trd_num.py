#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import fnmatch, os, re, sys

#	Content-Location: http://www.0chan.ru/d/res/12952.html
pat = re.compile('''(?:
Content-Location: |<!-- saved from url=\(\d+\))http[^
]+?/([^/]+)/res/(\d+)''', re.IGNORECASE & re.MULTILINE)
ext = 'mht'
sup = re.compile('^[^,]+,\s*(.*?)(;_[0-9-_,]{19}.*)?\.[^.]+$', re.IGNORECASE)
src = os.listdir(u'.')
i = 0
for mht in src:
	if fnmatch.fnmatch(mht, '*,*.'+ext):
		f = open(mht)
		r = re.search(pat, f.read(987))
		f.close()
		if r:
			i += 1
			tnum = ' '+r.group(1)+'#'+r.group(2)
			os.rename(mht, mht[0:-4]+tnum+'.'+ext)

			j = 0
			if 'r' in sys.argv:
				r = re.search(sup, mht)
				if r:
					sub = r.group(1)
					for pic in src:
						if fnmatch.fnmatch(pic, sub+',*.*'):
							j += 1
							os.rename(pic, pic.replace(sub, sub+tnum))
					if os.path.exists(sub):
						for pic in os.listdir(sub):
							j += 1
							os.rename(sub+'/'+pic, sub+'/'+pic.replace(sub, sub+tnum))
						os.rename(sub, sub+tnum)
			if j:
				print i, tnum, '=', j, 'pics in /', sub
			else:
				print i, tnum #, mht
