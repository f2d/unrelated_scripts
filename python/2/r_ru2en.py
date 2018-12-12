#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import os

arr = [
	[u'А', 'A']
,	[u'Б', 'B']
,	[u'В', 'V']
,	[u'Г', 'G']
,	[u'Д', 'D']
,	[u'Е', 'E']
,	[u'Ё', 'YO']
,	[u'Ж', 'J']
,	[u'З', 'Z']
,	[u'И', 'I']
,	[u'Й', 'Y']
,	[u'К', 'K']
,	[u'Л', 'L']
,	[u'М', 'M']
,	[u'Н', 'N']
,	[u'О', 'O']
,	[u'П', 'P']
,	[u'Р', 'R']
,	[u'С', 'S']
,	[u'Т', 'T']
,	[u'У', 'U']
,	[u'Ф', 'F']
,	[u'Х', 'H']
,	[u'Ц', 'TS']
,	[u'Ч', 'CH']
,	[u'Ш', 'SH']
,	[u'Щ', 'SCH']
,	[u'Ъ', "'"]
,	[u'Ы', 'Y']
,	[u'Ь', "'"]
,	[u'Э', 'E']
,	[u'Ю', 'YU']
,	[u'Я', 'YA']

,	[u'а', 'a']
,	[u'б', 'b']
,	[u'в', 'v']
,	[u'г', 'g']
,	[u'д', 'd']
,	[u'е', 'e']
,	[u'ё', 'yo']
,	[u'ж', 'j']
,	[u'з', 'z']
,	[u'и', 'i']
,	[u'й', 'y']
,	[u'к', 'k']
,	[u'л', 'l']
,	[u'м', 'm']
,	[u'н', 'n']
,	[u'о', 'o']
,	[u'п', 'p']
,	[u'р', 'r']
,	[u'с', 's']
,	[u'т', 't']
,	[u'у', 'u']
,	[u'ф', 'f']
,	[u'х', 'h']
,	[u'ц', 'ts']
,	[u'ч', 'ch']
,	[u'ш', 'sh']
,	[u'щ', 'sch']
,	[u'ъ', "'"]
,	[u'ы', 'y']
,	[u'ь', "'"]
,	[u'э', 'e']
,	[u'ю', 'yu']
,	[u'я', 'ya']
]
i = 0

for src in os.listdir(u'.'):
	dest = src
	for a in arr:
		dest = dest.replace(a[0], a[1])
	if src == dest:
		continue
	i += 1
	print i, src.encode('utf-8'), '->', dest.encode('utf-8')
	os.rename(src, dest)
