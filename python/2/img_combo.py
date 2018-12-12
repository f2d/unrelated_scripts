#!/usr/bin/env python2
import Image
import sys

padding_x = 16
padding_y = 8
width = 800

if len(sys.argv) < 3:
	print 'Usage: {0} <images> <output>'.format(sys.argv[0])
	sys.exit(-1)

if len(sys.argv) == 3:
	flist = []
	import os
	for filename in os.listdir(sys.argv[1]):
		flist.append(sys.argv[1]+'/'+filename)
else:
	flist = sys.argv[1:-1]

class Row(object):
	pass
rows = []
row = None

for filename in flist:
	img = Image.open(filename)
	if row is None or row.width + img.size[0] + padding_x > width:
		row = Row()
		rows.append(row)
		row.images = []
		row.width = padding_x
		row.height = 0
	row.images.append(img)
	row.width += img.size[0] + padding_x
	row.height = max(row.height, img.size[1])

height = padding_y
for row in rows:
	height += row.height + padding_y

collage = Image.new('RGB', (width, height), (255, 255, 255))
pos_y = padding_y
for row in rows:
	pos_x = (width - row.width) / 2 + padding_x
	for img in row.images:
		collage.paste(img, (pos_x, pos_y + (row.height - img.size[1])/2))
		pos_x += img.size[0] + padding_x
	pos_y += row.height + padding_y

collage.save(sys.argv[-1])