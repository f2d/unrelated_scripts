#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Python 2 or 3 should work.

import os, re, sys, subprocess, traceback
from PIL import Image

# Use colored text if available:
try:
	from termcolor import colored, cprint
	import colorama

	colorama.init()

except ImportError:
	def colored(*list_args, **keyword_args): return list_args[0]
	def cprint (*list_args, **keyword_args): print (list_args[0])

# https://stackoverflow.com/a/47625614
if sys.version_info[0] >= 3:
	unicode = str

# - Configuration and defaults ------------------------------------------------

print_encoding = sys.getfilesystemencoding() or 'utf-8'

arg_test = False

work_dir = u'd:/programs/!_media/waifu2x-converter_x64_0813/'
base_cmd = [work_dir + 'waifu2x-converter_x64.exe', '-j', '7']
default_mode = 'scale'
default_suffix = ',waifu2x_0813_'
must_quote_chars = ' ,;>='

pat_res = re.compile(r'^[\'"]*(?P<Width>\d+)?(?:x(?P<Height>\d+))?[\'"]*$', re.I)
pat_help = re.compile(r'^(-+h[elp]*|/\?)$', re.I)
#pat_trim_float = re.compile(r'((\d+\.(0))\3{9,}|(\d+\.\d*?)0{9,}|(\d+\.\d*?(\d))\6{9,})\d+|(\d+\.\d{6})\d*') # -> r'\2\4\5\7~'

pats_trim_float = [
	re.compile(r'(?P<Short>\d+\.0)0{6,}\d*')
,	re.compile(r'(?P<Short>\d+\.\d*?)0{6,}\d*')
,	re.compile(r'(?P<Short>\d+\.\d*?(\d))\2{6,}\d*')
,	re.compile(r'(?P<Short>\d+\.\d{6})\d*')
] # -> r'\g<Short>'

# - Declare functions ---------------------------------------------------------

def get_text_encoded_for_print(text):
	text = unicode(text)

	return text.encode(print_encoding) if sys.version_info.major == 2 else text

def print_with_colored_prefix_line(comment, value, color=None):
	print('')
	cprint(comment, color or 'yellow')
	print(value)

def print_with_colored_prefix(comment, value, color=None):
	print('{} {}'.format(colored(comment, color or 'yellow'), value))

def print_with_colored_suffix(value, comment, color=None):
	print('{} {}'.format(value, colored(comment, color or 'yellow')))

def print_help():
	self_name = os.path.basename(__file__)

	help_text_lines = [
		''
	,	colored('* Description:', 'yellow')
	,	'	Make resized copies of all images in current folder'
	,	'	using external waifu2xprogram.'
	,	''
	,	colored('* Usage:', 'yellow')
	,	'	{0}'
		+	colored(' [<width>][x<height>]', 'cyan')
		+	colored(' [<flags>] [<destination folder>]', 'magenta')
	,	''
	,	colored('<flags>', 'cyan') + ': string of letters in any order.'
	,	'	t: show possible test info, don\'t apply changes'
	,	'	r: recursion - go into subfolders'
	,	'	f: keep source subfolder structure at destination, implies "r"'
	,	'	i: resize - touch given frame inside (default)'
	,	'	o: resize - touch given frame outside, no effect without both dimensions'
	,	'	l: keep larger files as is (scale factor <= 1.0)'
	,	'	s: keep smaller files as is (scale factor >= 1.0)'
	,	'	0 or 1 or 2: noise reduction level (default = none)'
	,	''
	,	colored('<width>', 'cyan') + ' or ' + colored('x<height>', 'cyan') + ': use one number, calculate the other.'
	,	colored('<width>x<height>', 'cyan') + ': use two numbers, resize to touch given frame.'
	,	''
	,	colored('* Note:', 'yellow')
	,	'	After excluding the first found argument matching width/height,'
	,	'	first remaining is flags, second is destination folder.'
	,	''
	,	colored('* Examples:', 'yellow')
	,	'	{0} t ./dest 1920'
	,	'	{0} x1080 o ..'
	,	'	{0} x3840 l1 e:/4k/png/wide'
	,	'	{0} 3840x2160 r1 e:/dest/'
	]

	print('\n'.join(help_text_lines).format(self_name))

def is_any_char_of_a_in_b(chars, text):
	for char in chars:
		if text.find(char) >= 0:
			return True

	return False

def is_any_char_code_out_of_normal_range(text):
	for char in text:
		if ord(char) > 127:
			return True

	return False

def is_quoted(text):
	for char in '\'"':
		if text[0] == char and text[-1 : ][0] == char:
			return True

	return False

def quoted_if_must(text):
	text = get_text_encoded_for_print(text)

	return (
		'"{}"'.format(text)
		if not is_quoted(text) and (
			is_any_char_of_a_in_b(must_quote_chars, text)
		or	is_any_char_code_out_of_normal_range(text)
		)
		else text
	)

def quoted_list(args):
	return list(map(quoted_if_must, args))

def cmd_args_to_text(args):
	return ' '.join(quoted_list(args))

def get_image_sizes(file_path):
	global arg_test

	try:
		img = Image.open(file_path)

		if img:
			return img.size

		if arg_test:
			print_with_colored_prefix_line('Error: not image:', file_path, 'red')

		return None

	except Exception as exception:

		if arg_test:
			print('')
			traceback.print_exc()

			print_with_colored_prefix_line('Error with file:', file_path, 'red')

		return None

# - Main job function ---------------------------------------------------------

def run_batch_resize(argv):
	global arg_test

	def process_folder(path):
		count_checked = count_skipped = count_done = count_errors = 0

		names = os.listdir(path)

		for name in names:
			src_file_path = path + '/' + name

			if os.path.isdir(src_file_path):
				if arg_recurse:
					process_folder(src_file_path)
				continue

			if os.path.isfile(src_file_path):
				src_image_sizes = get_image_sizes(src_file_path)

				if src_image_sizes:
					orig_w, orig_h = src_image_sizes
				else:
					continue

				count_checked += 1

				print_with_colored_prefix_line('File:', src_file_path)

				w, h = arg_w, arg_h

				if w and h:
					w_ratio = float(w) / orig_w
					h_ratio = float(h) / orig_h

					if w_ratio < h_ratio:
						scale = h_ratio if arg_touch_outside else w_ratio
					else:
						scale = w_ratio if arg_touch_outside else h_ratio

					w = int(scale * orig_w)
					h = int(scale * orig_h)
				elif w:
					scale = float(w) / orig_w
					h = int(scale * orig_h)
				elif h:
					scale = float(h) / orig_h
					w = int(scale * orig_w)
				else:
					print('')
					cprint('Error: scale factor is undetermined.', 'red')

					break

				orig_res = '{}x{}'.format(orig_w, orig_h)
				dest_res = '{}x{}'.format(w, h)

				if arg_keep_smaller and scale >= 1:
					count_skipped += 1

					print_with_colored_prefix_line('Skipped:', '{:.5f} >= 1\n{} >= {}'.format(scale, dest_res, orig_res), 'cyan')

					continue

				if arg_keep_larger and scale <= 1:
					count_skipped += 1

					print_with_colored_prefix_line('Skipped:', '{:.5f} <= 1\n{} <= {}'.format(scale, dest_res, orig_res), 'cyan')

					continue

				if arg_dest_subfolders and arg_recurse:
					name = path.split(':', 2)[-1].strip('/')+'/'+name

			#	scale = str(scale)		# <- max 10 digits after dot
				scale = '{:.50f}'.format(scale)	# <- max precision for python 2 x64 under Win7
			#	scale = '{:.32f}'.format(scale)	# <- same as of Win7 calculator

				scale_short = scale

				print_with_colored_prefix_line('Scale:', scale, 'cyan')

				for p in pats_trim_float:
					res = re.search(p, scale)

					if res:
						scale_short = re.sub(p, r'\g<Short>~', scale)

						print_with_colored_prefix_line('Short:', scale_short, 'cyan')

						break

				src_file_path = os.path.abspath(src_file_path)
				dest_file_path = os.path.abspath(base_dest + '/' + name) + dest_suffix + orig_res + 'x' + scale_short + '.png'

				file_cmd = base_cmd + [
					'--scale_ratio'	, scale
				,	'--input_file'	, src_file_path
				,	'--output_file'	, dest_file_path
				]

				if arg_test:
					print_with_colored_prefix_line('To resize:', '{} x {} -> {}'.format(orig_res, scale, dest_res), 'cyan')
					print_with_colored_prefix_line('Command to run:', cmd_args_to_text(file_cmd), 'cyan')
				else:
					if not os.path.exists(base_dest):
						os.makedirs(base_dest)

					print_with_colored_prefix_line('Resizing:', '{} x {} -> {}'.format(orig_res, scale, dest_res), 'cyan')
					print_with_colored_prefix_line('Running command:', cmd_args_to_text(file_cmd), 'magenta')

					with open(dest_file_path + '.log', 'w') as log_file:
						result_code = subprocess.call(file_cmd, stdout=log_file, cwd=work_dir)

					if result_code:
						count_errors += 1

						print_with_colored_prefix_line('Error {}:'.format(result_code), dest_file_path, 'red')
					else:
						count_done += 1

						print_with_colored_prefix_line('Done:', dest_file_path, 'green')

					if os.path.isfile(dest_file_path):
						dest_image_sizes = get_image_sizes(dest_file_path)

						if dest_image_sizes:
							w, h = dest_image_sizes
						else:
							continue

						result_res = '{}x{}'.format(w, h)

						if result_res != dest_res:
							print_with_colored_prefix_line(
								'Estimated / result image size:'
							,	'{} / {}'.format(dest_res, result_res)
							)

						new_file_path = ('={}.').format(result_res).join(dest_file_path.rsplit('.', 1))

						while os.path.exists(new_file_path):
							new_file_path = '(2).'.join(new_file_path.rsplit('.', 1))

						os.rename(dest_file_path, new_file_path)

# - Result summary ------------------------------------------------------------

		print('')
		cprint('- Done:', 'green')

		if count_checked > 0:
			print_with_colored_suffix(count_checked, 'files checked.')

		if count_skipped > 0:
			print_with_colored_suffix(count_skipped, 'files skipped.', 'cyan')

		if count_done > 0:
			print_with_colored_suffix(count_done, 'files saved.', 'green')

		if count_errors > 0:
			print_with_colored_suffix(count_errors, 'errors.', 'red')

		return count_done

# - Check arguments -----------------------------------------------------------

	arg_w = arg_h = res = None
	args = []

	for v in argv:
		if len(v) > 0:
			if not (arg_w or arg_h):
				res = re.search(pat_res, v)

				if res:
					arg_w = res.group('Width')
					arg_h = res.group('Height')

					if arg_w or arg_h:
						continue
			args.append(v)

# - Show help and exit --------------------------------------------------------

	if not (arg_w or arg_h):
		print_help()

		return 1

# - Calculate params ----------------------------------------------------------

	argc = len(args)

	flags = args[0] if (argc > 0) and (len(args[0]) > 0) else ''
	arg_dest_subfolders = ('f' in flags)
	arg_recurse = ('r' in flags) or arg_dest_subfolders
	arg_keep_larger = ('l' in flags)
	arg_touch_outside = ('o' in flags) and not ('i' in flags)
	arg_keep_smaller = ('s' in flags)
	arg_test = ('t' in flags)

	base_dest = (
		args[1].replace('\\', '/').rstrip('/')
		if (argc > 1) and (len(args[1]) > 0)
		else '.'
	) + '/'

	cmd_args = list(base_cmd)
	cmd_mode = default_mode
	dest_suffix = default_suffix

	for i in range(0, 2):
		n = str(i)

		if n in flags:
			cmd_mode = 'noise_scale'
			cmd_args += ['--noise_level', n]
			dest_suffix += 'n{}_'.format(n)

			break

	cmd_args += ['-m', cmd_mode]

	print('')
	print_with_colored_prefix('cmd:', cmd_args_to_text(cmd_args))
	print_with_colored_prefix('dest:', base_dest)
	print_with_colored_prefix('flags:', flags)
	print_with_colored_prefix('width:', arg_w)
	print_with_colored_prefix('height:', arg_h)

# - Do the job ----------------------------------------------------------------

	return 0 if process_folder(u'.') > 0 else -1

# - Run from commandline, when not imported as module -------------------------

if __name__ == '__main__':
	sys.exit(run_batch_resize(sys.argv[1 : ]))

# - End -----------------------------------------------------------------------
