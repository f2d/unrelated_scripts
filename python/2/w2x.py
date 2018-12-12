#!/usr/bin/env python2

import Image, os, re, sys, subprocess

work_dir = u'd:/programs/!_media/waifu2x-converter_x64_0813/'
base_cmd = [work_dir+'waifu2x-converter_x64.exe', '-j', '7']
mode = 'scale'
suffix = ',waifu2x_0813_'

pat_res = re.compile(r'^[\'"]*(?P<Width>\d+)?(?:x(?P<Height>\d+))?[\'"]*$', re.I)
pat_help = re.compile(r'^(-+h[elp]*|/\?)$', re.I)
#pat_trim_float = re.compile(r'((\d+\.(0))\3{9,}|(\d+\.\d*?)0{9,}|(\d+\.\d*?(\d))\6{9,})\d+|(\d+\.\d{6})\d*') # -> r'\2\4\5\7~'
pats_trim_float = [
	re.compile(r'(?P<Short>\d+\.0)0{6,}\d*')
,	re.compile(r'(?P<Short>\d+\.\d*?)0{6,}\d*')
,	re.compile(r'(?P<Short>\d+\.\d*?(\d))\2{6,}\d*')
,	re.compile(r'(?P<Short>\d+\.\d{6})\d*')
] # -> r'\g<Short>'

def show_help_and_exit(exit_code=0):
	print '* Description:'
	print '  Make resized copies of all images in current folder using external waifu2x'
	print '  program.'
	print
	print '* Usage: w2x.py [<width>][x<height>] [<flags>] [<destination folder>]'
	print
	print '* Flags (add in any order without spaces as first argument):'
	print '	t: show possible test info, don\'t apply changes'
	print '	r: recursion - go into subfolders'
	print '	f: keep source subfolder structure at destination, implies "r"'
	print '	i: resize - touch given frame inside (default)'
	print '	o: resize - touch given frame outside, no effect without both dimensions'
	print '	l: keep larger files as is (scale factor <= 1.0)'
	print '	s: keep smaller files as is (scale factor >= 1.0)'
	print '	0 or 1 or 2: noise reduction level (default = none)'
	print
	print '* Other options:'
	print ' <width> or x<height>: number, stick to one, calculate the other'
	print ' <width>x<height>: numbers, resize to touch given frame'
	print
	print '* Notice: excluding the first found argument matching width/height,'
	print '  #1 is flags, #2 is destination folder.'
	print
	print '* Example 1: w2x.py t ./dest 1920'
	print '* Example 2: w2x.py x1080 o ..'
	print '* Example 3: w2x.py x3840 l1 e:/4k/png/wide'
	print '* Example 4: w2x.py 3840x2160 r1 e:/dest/'
	sys.exit(exit_code)

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
arg_f = 'f' in flags
arg_r = 'r' in flags or arg_f
arg_l = 'l' in flags
arg_o = 'o' in flags and not 'i' in flags
arg_s = 's' in flags
arg_t = 't' in flags

base_dest = args[2].replace('\\', '/').rstrip('/')+'/' if argc > 2 and len(args[2]) > 0 else './'

for i in range(0, 2):
	n = str(i)
	if n in flags:
		mode = 'noise_scale'
		suffix += 'n'+n+'_'
		base_cmd += ['--noise_level', n]
		break

base_cmd += ['-m', mode]

#print 'args:', args
print 'flags:', flags
print 'base_dest:', base_dest
#print 'base_cmd:', base_cmd
print 'width x height:', arg_w, 'x', arg_h

n_i = 0

def get_image_sizes(src):
	try:
		img = Image.open(src)
		if img:
			return img.size

		if arg_t:
			print
			print 'Error:', img, '- file is not image -', src.encode('utf-8')
		return None

	except Exception as e:
		if arg_t:
			print
			print 'Error:', e, '-', src.encode('utf-8')
		return None

def process_folder(path):
	global n_i
	names = os.listdir(path)
	for name in names:
		src = path+'/'+name

		if os.path.isdir(src):
			if arg_r:
				process_folder(src)
			continue

		if os.path.isfile(src):
			sz = get_image_sizes(src)
			if sz:
				orig_w, orig_h = sz
			else:
				continue

			n_i += 1
			print
			print n_i, '-', src.encode('utf-8')

			w, h = arg_w, arg_h
			if w and h:
				w_ratio = float(w)/orig_w
				h_ratio = float(h)/orig_h
				if w_ratio < h_ratio:
					scale = h_ratio if arg_o else w_ratio
				else:
					scale = w_ratio if arg_o else h_ratio
				w = int(scale*orig_w)
				h = int(scale*orig_h)
			elif w:
				scale = float(w)/orig_w
				h = int(scale*orig_h)
			elif h:
				scale = float(h)/orig_h
				w = int(scale*orig_w)
			else:
				print 'Error: scale factor is undetermined.'
				break

			orig_res = str(orig_w)+'x'+str(orig_h)
			dest_res = str(w)+'x'+str(h)

			if arg_s and scale >= 1:
				print n_i, '- skipped,', scale, '> 1,', dest_res, '>', orig_res
				continue

			if arg_l and scale <= 1:
				print n_i, '- skipped,', scale, '< 1,', dest_res, '<', orig_res
				continue

			if arg_f and arg_r:
				name = path.split(':', 2)[-1].strip('/')+'/'+name

		#	scale = str(scale)	# <- max 10 digits after dot
			scale = "%.50f" % scale	# <- max precision for python 2 x64 under Win7
		#	scale = "%.32f" % scale	# <- same as of Win7 calculator

			scale_short = scale

			print scale

			for p in pats_trim_float:
				res = re.search(p, scale)
				if res:
					scale_short = re.sub(p, r'\g<Short>~', scale)

					print scale_short

					break

			src = os.path.abspath(src)
			dest = os.path.abspath(base_dest+'/'+name)+suffix+orig_res+'x'+scale_short+'.png'

			file_cmd = base_cmd + [
				'--scale_ratio'	, scale
			,	'--input_file'	, src
			,	'--output_file'	, dest
			]

			if arg_t:
				print 'Test resize:', orig_res, 'x', scale, '->', dest_res
				print 'Test command:', file_cmd
			else:
				if not os.path.exists(base_dest):
					os.makedirs(base_dest)

				print 'Processing:', orig_res, 'x', scale, '->', dest_res, '...'

				with open(dest+'.log', 'w') as log_file:
					e = subprocess.call(file_cmd, stdout=log_file, cwd=work_dir)

				print
				print n_i, '- done,', ('error code:', e) if e else 'OK'

				if os.path.isfile(dest):
					sz = get_image_sizes(dest)
					if sz:
						w, h = sz
					else:
						continue

					result_res = str(w)+'x'+str(h)
					if result_res != dest_res:
						print 'Estimated / result image size:', dest_res, '/', result_res

					r = ('='+result_res+'.').join(dest.rsplit('.', 1))

					while os.path.exists(r):
						r = '(2).'.join(r.rsplit('.', 1))

					os.rename(dest, r)

process_folder(u'.')
