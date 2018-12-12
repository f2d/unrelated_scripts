#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import os, sys

from PIL import Image, ImageChops

# https://gist.github.com/mattjmorrison/932345
def get_trimmed_image(im, border=None):

	def get_trimmed_image_bbox(border):
		bg = Image.new(im.mode, im.size, border)
		diff = ImageChops.difference(im, bg)
		return diff.getbbox()

	bbox = None

	if border:
		bbox = get_trimmed_image_bbox(im, border)
	else:
		sz = im.size
		x = sz[0] - 1
		y = sz[1] - 1

		bboxes = filter(None, map(lambda x: get_trimmed_image_bbox(im.getpixel(x)), [
			(0, 0)
		,	(x, 0)
		,	(0, y)
		,	(x, y)
		]))

		for i in bboxes:
			if bbox == None:
				bbox = i
			else:
				if bbox[0] < i[0]: bbox[0] = i[0]
				if bbox[1] < i[1]: bbox[1] = i[1]
				if bbox[2] > i[2]: bbox[2] = i[2]
				if bbox[3] > i[3]: bbox[3] = i[3]

# http://pillow.readthedocs.io/en/3.1.x/reference/Image.html#PIL.Image.Image.getbbox
# The bounding box is returned as a 4-tuple defining the left, upper, right, and lower pixel coordinate.

	if bbox:
		return im.crop(bbox)

	return im

for img_path in sys.argv[1 : ]:
	if os.path.isfile(img_path):
		print 'Image:', img_path

		img = Image.open(img_path)
		size = 'x'.join(map(str, img.size))

		print 'Full size:', size

		img = get_trimmed_image(img)
		size = 'x'.join(map(str, img.size))

		print 'Trimmed size:', size

		new_path = '%s_%s.%s' % (img_path, size, img_path.rsplit('.', 1)[-1 : ][0])

		print 'Saving to:', new_path

		img.save(new_path)
		img.close()
