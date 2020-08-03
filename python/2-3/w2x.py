#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Python 2 or 3 should work.

import os, re, sys, subprocess
from PIL import Image

work_dir = u'd:/programs/!_media/waifu2x-converter_x64_0813/'
base_cmd = [work_dir+'waifu2x-converter_x64.exe', '-j', '7']
mode = 'scale'
suffix = ',waifu2x_0813_'
must_quote = ' ,;>='

pat_res = re.compile(r'^[\'"]*(?P<Width>\d+)?(?:x(?P<Height>\d+))?[\'"]*$', re.I)
pat_help = re.compile(r'^(-+h[elp]*|/\?)$', re.I)
#pat_trim_float = re.compile(r'((\d+\.(0))\3{9,}|(\d+\.\d*?)0{9,}|(\d+\.\d*?(\d))\6{9,})\d+|(\d+\.\d{6})\d*') # -> r'\2\4\5\7~'
pats_trim_float = [
	re.compile(r'(?P<Short>\d+\.0)0{6,}\d*')
,	re.compile(r'(?P<Short>\d+\.\d*?)0{6,}\d*')
,	re.compile(r'(?P<Short>\d+\.\d*?(\d))\2{6,}\d*')
,	re.compile(r'(?P<Short>\d+\.\d{6})\d*')
] # -> r'\g<Short>'

print_encoding = sys.getfilesystemencoding() or 'utf-8'

def show_help_and_exit(exit_code=0):
	self_name = os.path.basename(__file__)

	help_text_lines = [
		''
	,	'* Description:'
	,	'  Make resized copies of all images in current folder'
	,	'  using external waifu2xprogram.'
	,	''
	,	'* Usage:'
	,	'  %s [<width>][x<height>] [<flags>] [<destination folder>]'
	,	''
	,	'<flags>: string of letters in any order.'
	,	'	t: show possible test info, don\'t apply changes'
	,	'	r: recursion - go into subfolders'
	,	'	f: keep source subfolder structure at destination, implies "r"'
	,	'	i: resize - touch given frame inside (default)'
	,	'	o: resize - touch given frame outside, no effect without both dimensions'
	,	'	l: keep larger files as is (scale factor <= 1.0)'
	,	'	s: keep smaller files as is (scale factor >= 1.0)'
	,	'	0 or 1 or 2: noise reduction level (default = none)'
	,	''
	,	'<width> or x<height>: number, stick to one, calculate the other'
	,	'<width>x<height>: numbers, resize to touch given frame'
	,	''
	,	'* Note:'
	,	'	After excluding the first found argument matching width/height,'
	,	'	first remaining is flags, second is destination folder.'
	,	''
	,	'* Examples:'
	,	'	%s t ./dest 1920'
	,	'	%s x1080 o ..'
	,	'	%s x3840 l1 e:/4k/png/wide'
	,	'	%s 3840x2160 r1 e:/dest/'
	]

	print('\n'.join(help_text_lines).replace('%s', self_name))

	sys.exit(exit_code)

def is_any_char_of_a_in_b(a, b):
	for c in a:
		if b.find(c) >= 0:
			return True

	return False

def quoted_if_must(text):
	return ('"%s"' % text) if is_any_char_of_a_in_b(must_quote, text) else text

def quoted_list(a):
	return map(quoted_if_must, a)

def get_cmd_text(cmd_args):
	return ' '.join(quoted_list(cmd_args))

arg_w = arg_h = res = None
args = []

for v in sys.argv:
	if len(v) > 0:
	#	help = re.search(pat_help, v)
	#	if help:
	#		show_help_and_exit()

		if not (arg_w or arg_h):
			res = re.search(pat_res, v)
			if res:
				arg_w = res.group('Width')
				arg_h = res.group('Height')
				if arg_w or arg_h:
					continue
		args.append(v)

if not (arg_w or arg_h):
	show_help_and_exit(-1)

argc = len(args)

flags = args[1] if argc > 1 and len(args[1]) > 0 else ''
arg_dest_subfolders = 'f' in flags
arg_recurse = 'r' in flags or arg_dest_subfolders
arg_keep_larger = 'l' in flags
arg_touch_outside = 'o' in flags and not 'i' in flags
arg_keep_smaller = 's' in flags
arg_test = 't' in flags

base_dest = args[2].replace('\\', '/').rstrip('/')+'/' if argc > 2 and len(args[2]) > 0 else './'

for i in range(0, 2):
	n = str(i)
	if n in flags:
		mode = 'noise_scale'
		suffix += 'n'+n+'_'
		base_cmd += ['--noise_level', n]
		break

base_cmd += ['-m', mode]

# print('base_cmd: %s' % get_cmd_text(base_cmd))
# print('args: %s' % get_cmd_text(args))
print('flags: %s' % flags)
print('base_dest: %s' % base_dest)
print('width x height: %sx%s' % (arg_w, arg_h))

count_checked = 0

def get_image_sizes(src):
	try:
		img = Image.open(src)
		if img:
			return img.size

		if arg_test:
			print('')
			print('Error: %r is not image - "%s"' % (img, src.encode(print_encoding)))

		return None

	except Exception as exception:
		if arg_test:
			print('')
			print('Error: %r - "%s"' % (exception, src.encode(print_encoding)))

		return None

def process_folder(path):
	global count_checked

	names = os.listdir(path)

	for name in names:
		src = path+'/'+name

		if os.path.isdir(src):
			if arg_recurse:
				process_folder(src)
			continue

		if os.path.isfile(src):
			sz = get_image_sizes(src)
			if sz:
				orig_w, orig_h = sz
			else:
				continue

			count_checked += 1
			print('')
			print('%d - "%s"' % (count_checked, src.encode(print_encoding)))

			w, h = arg_w, arg_h
			if w and h:
				w_ratio = float(w)/orig_w
				h_ratio = float(h)/orig_h
				if w_ratio < h_ratio:
					scale = h_ratio if arg_touch_outside else w_ratio
				else:
					scale = w_ratio if arg_touch_outside else h_ratio
				w = int(scale*orig_w)
				h = int(scale*orig_h)
			elif w:
				scale = float(w)/orig_w
				h = int(scale*orig_h)
			elif h:
				scale = float(h)/orig_h
				w = int(scale*orig_w)
			else:
				print('Error: scale factor is undetermined.')
				break

			orig_res = '%dx%d' % (orig_w, orig_h)
			dest_res = '%dx%d' % (w, h)

			if arg_keep_smaller and scale >= 1:
				print('%d - skipped, %.5f > 1, %s > %s' % (count_checked, scale, dest_res, orig_res))
				continue

			if arg_keep_larger and scale <= 1:
				print('%d - skipped, %.5f < 1, %s > %s' % (count_checked, scale, dest_res, orig_res))
				continue

			if arg_dest_subfolders and arg_recurse:
				name = path.split(':', 2)[-1].strip('/')+'/'+name

		#	scale = str(scale)	# <- max 10 digits after dot
			scale = "%.50f" % scale	# <- max precision for python 2 x64 under Win7
		#	scale = "%.32f" % scale	# <- same as of Win7 calculator

			scale_short = scale

			print(scale)

			for p in pats_trim_float:
				res = re.search(p, scale)
				if res:
					scale_short = re.sub(p, r'\g<Short>~', scale)

					print(scale_short)

					break

			src = os.path.abspath(src)
			dest = os.path.abspath(base_dest+'/'+name)+suffix+orig_res+'x'+scale_short+'.png'

			file_cmd = base_cmd + [
				'--scale_ratio'	, scale
			,	'--input_file'	, src
			,	'--output_file'	, dest
			]

			if arg_test:
				print('Test resize: %s x %s -> %s' % (orig_res, scale, dest_res))
				print('Test command: %s' % get_cmd_text(file_cmd))
			else:
				if not os.path.exists(base_dest):
					os.makedirs(base_dest)

				print('Processing: %s x %s -> %s ...' % (orig_res, scale, dest_res))

				with open(dest+'.log', 'w') as log_file:
					e = subprocess.call(file_cmd, stdout=log_file, cwd=work_dir)

				print('')
				print('%d - done, %s' % (count_checked, ('error code: %d' % e) if e else 'OK'))

				if os.path.isfile(dest):
					sz = get_image_sizes(dest)
					if sz:
						w, h = sz
					else:
						continue

					result_res = str(w)+'x'+str(h)
					if result_res != dest_res:
						print('Estimated / result image size: %s / %s' % (dest_res, result_res))

					r = ('='+result_res+'.').join(dest.rsplit('.', 1))

					while os.path.exists(r):
						r = '(2).'.join(r.rsplit('.', 1))

					os.rename(dest, r)

process_folder(u'.')
