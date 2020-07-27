#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import datetime, os, sys, time

# Ref.source: http://stackoverflow.com/questions/29547218/remove-silence-at-the-beginning-and-at-the-end-of-wave-files-with-pydub

from pydub import AudioSegment

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

# Functions -------------------------------------------------------------------

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
			print n_done, src, '->', d
		except Exception as e:
			try:
				print n_done, src.encode('utf-8'), '->', d.encode('utf-8')
			except Exception as e:
				print n_done, '<Error: unprintable path>', e

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

# Run -------------------------------------------------------------------------

print

if len(sys.argv) > 1:
	flags = sys.argv[1].lower()
	get_folder = get_norm_path(sys.argv[2]) if len(sys.argv) > 2 else '.'
	put_folder = get_norm_path(sys.argv[3]) if len(sys.argv) > 3 else '.'
	silence_threshold = float(sys.argv[4]) if len(sys.argv) > 4 else -50.0
	chunk_size = int(sys.argv[5]) if len(sys.argv) > 5 else 10

	errors = 0
	if not os.path.exists(get_folder):
		print 'Error: source file or folder not found.'
		errors += 1
	if os.path.exists(put_folder) and not os.path.isdir(put_folder):
		print 'Error: destination exists but is not a folder.'
		errors += 1
	if not errors:
		arg_i = 'i' in flags
		arg_r = arg_i or ('r' in flags)	# <- recursion

		time_format = ';_%Y-%m-%d,%H-%M-%S.' if 'c' in flags else '_%Y-%m-%d_%H-%M-%S.'
		t0 = time.strftime(time_format)
		s0 = '.'+str(silence_threshold)+'dB.'
		n_done = 0

		print 'Source:', get_folder.encode('utf-8')
		print 'Destination:', put_folder.encode('utf-8')
		print 'Silence threshold:', silence_threshold
		print 'Chunk size:', chunk_size
		print 'Run:', 'all subfolders.' if arg_i else 'all subfolders except destination.' if arg_r else 'only current path.'

		run_path(get_folder)

		print n_done, 'files done.'
else:

# Display help ----------------------------------------------------------------

	self_name = os.path.basename(__file__)

	print '* Description:'
	print '	Write copies of wav files with start/end silence removed, into given folder.'
	print
	print '* Usage:'
	print '	%s [<flags>]' % self_name
	print '		[<src_folder/file>|.] [<put_folder>|.]'
	print '		[<silence_threshold(Db)>|-50.0] [<chunk_size(ms)>|10]'
	print
	print '<flags>: string of letters in any order.'
	print '	c to use timestamp format ;_YYYY-MM-DD,HH-MM-SS, default is _YYYY-MM-DD_HH-MM-SS'
	print '	r to recurse'
	print '	i to recurse including put_folder'
	print '	anything else to go flat'
	print '	or nothing to show this help.'
