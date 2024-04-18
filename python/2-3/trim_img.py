#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Python 2 or 3 should work.

# - Help screen shown on demand or without arguments --------------------------

def print_help():
	self_name = os.path.basename(__file__)

	help_text_lines = [
		''
	,	colored('* Description:', 'yellow')
	,	'	Save a trimmed image copy for each file path in arguments.'
	,	'	Non-existing or non-file paths are ignored.'
	,	'	Unsupported or non-image files are skipped.'
	,	''
	,	colored('* Usage:', 'yellow')
	,	'	{0}'
		+	colored(' "<source file path>"', 'cyan')
		+	colored(' "<more>" "<files>" <...>', 'magenta')
	]

	print('\n'.join(help_text_lines).format(self_name))

# - Dependencies --------------------------------------------------------------

import os, sys

from PIL import Image, ImageChops

# Use colored text if available:
try:
	from termcolor import colored, cprint
	import colorama

	colorama.init()

except ImportError:
	def colored(*list_args, **keyword_args): return list_args[0]
	def cprint (*list_args, **keyword_args): print (list_args[0])

# - Utility functions ---------------------------------------------------------

def print_with_colored_prefix(prefix, value, color=None):
	print('{} {}'.format(colored(prefix, color or 'yellow'), value))

# https://gist.github.com/mattjmorrison/932345
def get_trimmed_image(img, border=None):

	def get_trimmed_image_bbox(border):
		bg = Image.new(img.mode, img.size, border)
		diff = ImageChops.difference(img, bg)
		return diff.getbbox()

	bbox = None

	if border:
		bbox = get_trimmed_image_bbox(img, border)
	else:
		x = img.size[0] - 1
		y = img.size[1] - 1

		bboxes = filter(
			None
		,	[
				get_trimmed_image_bbox(img.getpixel(xy)) for xy in [
					(0, 0)
				,	(x, 0)
				,	(0, y)
				,	(x, y)
				]
			]
		)

		for each_box in bboxes:
			if bbox == None:
				bbox = list(each_box)
			else:
				if bbox[0] < each_box[0]: bbox[0] = each_box[0]
				if bbox[1] < each_box[1]: bbox[1] = each_box[1]
				if bbox[2] > each_box[2]: bbox[2] = each_box[2]
				if bbox[3] > each_box[3]: bbox[3] = each_box[3]

# http://pillow.readthedocs.io/en/3.1.x/reference/Image.html#PIL.Image.Image.getbbox
# The bounding box is returned as a 4-tuple defining the left, upper, right, and lower pixel coordinate.

	if bbox:
		return img.crop(bbox)

	return img

def get_dimensions_text(dimensions):
	return 'x'.join(map(str, dimensions))

# - Main job function ---------------------------------------------------------

def run_batch_trim_image(argv):

	argc = len(argv)

# - Show help and exit --------------------------------------------------------

	if argc < 1:
		print_help()

		return 1

# - Do the job for each argument ----------------------------------------------

	count_done = 0

	for img_path in argv:
		if os.path.isfile(img_path):
			try:
				img = Image.open(img_path)
				print_with_colored_prefix('Image:', img_path)

				size_text = get_dimensions_text(img.size)
				print_with_colored_prefix('Full size:', size_text)

				img = get_trimmed_image(img)
				size_text = get_dimensions_text(img.size)
				print_with_colored_prefix('Trimmed size:', size_text)

				new_path = '{name}_{size}.{ext}'.format(
					name=img_path
				,	size=size_text
				,	ext=img_path.rsplit('.', 1)[-1 : ][0]
				)
				print_with_colored_prefix('Saving to:', new_path)

				img.save(new_path)
				img.close()

				count_done += 1

				print_with_colored_prefix('Done:', count_done, 'green')

			except IOError:
				print_with_colored_prefix('Not image:', img_path, 'red')

				continue
	return 0

# - Run from commandline, when not imported as module -------------------------

if __name__ == '__main__':
	sys.exit(run_batch_trim_image(sys.argv[1 : ]))

# - End -----------------------------------------------------------------------
