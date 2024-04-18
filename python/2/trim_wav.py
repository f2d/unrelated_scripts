#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

# - Help screen shown on demand or without arguments --------------------------

def print_help():
	self_name = os.path.basename(__file__)

	help_text_lines = [
		''
	,	colored('* Description:', 'yellow')
	,	'	Write copies of wav files with start/end silence removed, into given folder.'
	,	''
	,	colored('* Usage:', 'yellow')
	,	'	{0}'
		+	colored(' [<flags>]', 'cyan')
		+	colored(' [<src_folder/file>|.]',		'magenta')
		+	colored(' [<put_folder>|.]',			'magenta')
		+	colored(' [<silence_threshold(Db)>|-50.0]',	'magenta')
		+	colored(' [<chunk_size(ms)>|10]',		'magenta')
	,	''
	,	colored('<flags>', 'cyan') + ': string of letters in any order.'
	,	'	c: Use timestamp format ;_YYYY-MM-DD,HH-MM-SS, default is _YYYY-MM-DD_HH-MM-SS.'
	,	'	r: Recurse into subfolders.'
	,	'	i: Recurse including <put_folder>.'
	,	'	Anything else to go flat.'
	,	'	Nothing to show this help.'
	]

	print('\n'.join(help_text_lines).format(self_name))

# - Dependencies --------------------------------------------------------------

import datetime, os, sys, time
from pydub import AudioSegment

# Use colored text if available:
try:
	from termcolor import colored, cprint
	import colorama

	colorama.init()

except ImportError:
	def colored(*list_args, **keyword_args): return list_args[0]
	def cprint (*list_args, **keyword_args): print (list_args[0])

# - Utility functions ---------------------------------------------------------

# Source: http://stackoverflow.com/questions/29547218/remove-silence-at-the-beginning-and-at-the-end-of-wave-files-with-pydub
def get_trimmed_sound(path):

	def get_leading_silence(sound):
		'''
		sound is a pydub.AudioSegment
		silence_threshold in dB
		chunk_size in ms

		iterate over chunks until you find the first one with sound
		'''

		ms = 0
		while sound[ms : ms + chunk_size].dBFS < silence_threshold:
			ms += chunk_size
		return ms

	sound = AudioSegment.from_file(path, format="wav")

	start_pos = get_leading_silence(sound)
	end_pos = get_leading_silence(sound.reverse())

	return sound[start_pos : len(sound) - end_pos]

def get_norm_path(path):
	return os.path.normpath(path).replace('\\', '/')

def get_path_name(path):
	return path if path.find('/') < 0 else path.rsplit('/', 1)[1]

def get_path_ext(path):
	if path.find('/') >= 0:
		path = path.rsplit('/', 1)[1]
	if path.find('.') >= 0:
		path = path.rsplit('.', 1)[1]
	return path.lower()

# - Main job function ---------------------------------------------------------

def run_batch_trim_wav(argv):

	def get_path_dest_uniq(src, d):
		i = 0
		if os.path.exists(d):
			d = s0.join(d.rsplit('.', 1))
			i += 1
		if os.path.exists(d):
			d = t0.join(d.rsplit('.', 1))
			i += 1
		if os.path.exists(d) and os.path.exists(src):
			d = datetime.datetime.fromtimestamp(os.path.getmtime(src)).strftime(time_format).join(d.rsplit('.', 1))
			i += 1
		while os.path.exists(d):
			d = '(2).'.join(d.rsplit('.', 1))
			i += 1
	#	if i: print '+', i, 'duplicate(s)'
		return d

	def run_file(src):
		global n_done
		d = get_path_name(src)
		if get_path_ext(d) == 'wav':
			n_done += 1
			d = get_path_dest_uniq(src, put_folder+u'/'+d)

			try:
				print colored(n_done, 'yellow'), src, colored('->', 'yellow'), d
			except Exception as e:
				try:
					print colored(n_done, 'yellow'), src.encode('utf-8'), colored('->', 'yellow'), d.encode('utf-8')
				except Exception as e:
					print n_done, colored('<Error: unprintable path>', 'red'), e

			if not os.path.exists(put_folder):
				os.mkdir(put_folder)
			get_trimmed_sound(src).export(d, format="wav")

	def run_path(path):
		if os.path.isdir(path):
			names = os.listdir(path)
			for name in names:
				src = path.rstrip('/')+u'/'+name
				if not arg_i and get_norm_path(src) == put_folder:
					continue
				if os.path.isdir(src):
					if arg_r:
						run_path(src)
					continue
				run_file(src)
		else:
			run_file(path)

	argc = len(argv)
	flags = argv[0].lower() if argc > 0 else ''

# - Show help and exit --------------------------------------------------------

	if (
		argc < 1
	or	not flags
	or	'-' in flags
	or	'/' in flags
	or	'?' in flags
	or	'h' in flags
	):
		print_help()

		return 1

# - Check arguments -----------------------------------------------------------

	get_folder = get_norm_path(argv[1]) if argc > 1 else '.'
	put_folder = get_norm_path(argv[2]) if argc > 2 else '.'
	silence_threshold =  float(argv[3]) if argc > 3 else -50.0
	chunk_size =           int(argv[4]) if argc > 4 else 10

	errors = 0

	print('')

	if not os.path.exists(get_folder):
		cprint('Error: source file or folder not found.', 'red')
		errors += 1
		
	if os.path.exists(put_folder) and not os.path.isdir(put_folder):
		cprint('Error: destination exists but is not a folder.', 'red')
		errors += 1
		
	if not errors:

# - Do the job ----------------------------------------------------------------

		arg_i = 'i' in flags
		arg_r = arg_i or ('r' in flags)	# <- recursion

		time_format = ';_%Y-%m-%d,%H-%M-%S.' if 'c' in flags else '_%Y-%m-%d_%H-%M-%S.'
		t0 = time.strftime(time_format)
		s0 = '.'+str(silence_threshold)+'dB.'
		n_done = 0

		print colored('Source:', 'yellow'), get_folder.encode('utf-8')
		print colored('Destination:', 'yellow'), put_folder.encode('utf-8')
		print colored('Silence threshold:', 'yellow'), silence_threshold
		print colored('Chunk size:', 'yellow'), chunk_size
		print colored('Run:', 'yellow'), (
			'all subfolders.' if arg_i else
			'all subfolders except destination.' if arg_r else
			'only current path.'
		)

		run_path(get_folder)

# - Result summary ------------------------------------------------------------

		print n_done, colored('files done.', 'green')

	return 0

# - Run from commandline, when not imported as module -------------------------

if __name__ == '__main__':
	sys.exit(run_batch_trim_wav(sys.argv[1 : ]))

# - End -----------------------------------------------------------------------
