#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import datetime, fnmatch, os, re, subprocess, sys

fse = sys.getfilesystemencoding()

TEST = 't' in sys.argv			# <- add 't' for test output only
CYS = 'c' in sys.argv

# test samples:
#	d:\_dl\Youtube,v=Ws6AAhTw7RA,1280x720.mp4
#	d:\_dl\YouTube - ASTCvideos - 2011-10-16 - Quantum Levitation.mht
#	Content-Location: http://www.youtube.com/watch?v=Ws6AAhTw7RA&feature=player_embedded
#
#	YouTube - K6nkymk - 2013-08-10 - NINE TAIL-Trial Ver.C84- PV - watch.mht
#	NINE TAIL-Trial Ver.C84- PV (HD).mp4
#	ИСТОРИЯ ПОЯВЛЕНИЯ - ЗЕМЛИ-ТЯН И СОЛНЕЧНОЙ СИСТЕМЫ - ХУМАНИЗАЦИЯ - YouTube (HD).mp4

src_list = os.listdir(u'.')
#dest_dir = u'd:/_bak/v/_yt'
dest_dir = u'd:/1_Video/other/_xz/_yt'
separated_dir = '_audio-video_separated'

page_prfx = 'Youtube'
page_sufx = ' - watch'
page_ext_arr = ['mht', 'mhtml']
page_fnmatch_by_ext_arr = map(lambda x: page_prfx+'*.'+x, page_ext_arr)

len_p = len(page_prfx)
len_s = len(page_sufx)

pat_url = re.compile(r'''
	(?:^|[\r\n])
	(?P<Header>Content-Location:)\s*
	(?P<URL>
		(?P<URL_Start>[htps]+[^\r\n]+?[?&])
		(?P<ID>v=[^&#\r\n]+)
		(?P<URL_End>[&#][^\r\n]+?)?
	)
	(?:[\r\n]|$)
''', re.I | re.X | re.DOTALL)

pat_page_title = re.compile(r'^' + page_prfx + r'''
	(?P<NameDateTitle>
		\s+-\s+(?P<UserName>.*?)
		\s+-\s+(?P<Date>\d{4}-\d\d-\d\d)
		\s+-\s+(?P<Title>.*)
	)
$''', re.I | re.X | re.DOTALL)

pat_video_title = re.compile(r'''^
	(?P<NameDateTitle>
		(?:
			(?P<UserName>.*?)\s+-\s+
			(?P<Date>\d{4}-\d\d-\d\d)\s+-\s+
		)?
		(?P<Title>.+?\S)
	)
	(?P<Site>\s*-\s*YouTube)?
	\s*\(
		(?P<Res>\w+)
	\)
	(?P<Ext>\.[^.()]+)?
$''', re.I | re.X | re.DOTALL)

titles_to_compare = ['NameDateTitle', 'Title', None]

space_placeholder = '_'

pat_normalize_title = [
	[re.compile(r'(\S)&+', re.U), r'\1']
,	[re.compile(r'[\s`~!@#$%^?*;\'"«—»,._=+-]+', re.U), space_placeholder]
]

pat_fix = [
	[re.compile(r'\.+(\.[^.]+)$'	, re.I), r'\1']				# <- autoreplace after inserting title
,	[re.compile(r',FHD\w*(\.[^.]+)$', re.I), r',1920x1080\1']
,	[re.compile(r',(\w*BA\.[^.]+)$'	, re.I), r',1920x1080.\1_audio.wav']	# <- bogus filetype for autoload in players
]

res_list = {
	'LD': '640x360'
,	'SD': '640x360'
,	'HD': '1280x720'
,	'FHD': '1920x1080'
,	'UHD': '3840x2160'
}

sub_ext_to_rename = ['mp3', 'mp4', 'm4a', 'mkv', 'ogg', 'ogm', 'wav', 'webm']
m_type = type(re.search('.', '.'))

def encode_cmd(cmd_array):
	return [(arg.encode(fse) if isinstance(arg,unicode) else arg) for arg in cmd_array]

def get_ext(path):
	if path.find('/') >= 0: path = path.rsplit('/', 1)[1]
	if path.find('.') >= 0: path = path.rsplit('.', 1)[1]
	return path.lower()

def normalize_title(n):
	n = unicode(n)
	for pat in pat_normalize_title:
		n = re.sub(pat[0], pat[1], n)
	return n.strip(space_placeholder).replace('&', 'and')

def get_normalized_title(i, t):
	return normalize_title(t.group(i or 0) if type(t) == m_type else t)

def is_title_equivalent(a, b):
	a_a = [get_normalized_title(i, a) for i in titles_to_compare]
	a_b = [get_normalized_title(i, b) for i in titles_to_compare]

	for a in a_a:
		if TEST: print '\na:', a.encode(fse)

		for b in a_b:
			if TEST: print 'b:', b.encode(fse)

			if a and b and a == b:
				if TEST: print 'matched!'

				return True
	return False

def get_uniq_path(src, d):
	i = 0
	if os.path.exists(d) and os.path.exists(src):
		d = datetime.datetime.fromtimestamp(os.path.getmtime(src)).strftime(';_%Y-%m-%d,%H-%M-%S.').join(d.rsplit('.', 1))
		i += 1
	while os.path.exists(d):
		d = '(2).'.join(d.rsplit('.', 1))
		i += 1
	if i: print '+', i, 'duplicate(s)'
	return d

def move_to_unique_path(src, dest):
	os.rename(src, get_uniq_path(src, dest))

def check_src_page(src_page, page_fnmatch):
	global i

	page_ext = '.' + get_ext(src_page)
	len_e = len(page_ext)

	if fnmatch.fnmatch(src_page, page_fnmatch):
		f = open(src_page)
		src_match = re.search(pat_url, f.read(123456))
		f.close()
		if src_match:
			v = src_match.group('ID')

			page_title = src_page[ : -len_e]

			if page_title[-len_s : ] == page_sufx:
				page_title = page_title[ : -len_s]

			page_title = page_title.strip()

			for video_filename in src_list:
				f = page_title
				if (
					fnmatch.fnmatch(video_filename, v+'.*')
				):
					f += ',' + ',360p.'.join(video_filename.rsplit('.'))
				elif (
					fnmatch.fnmatch(video_filename, page_prfx+','+v+'.*')
				or	fnmatch.fnmatch(video_filename, page_prfx+','+v+',*')
				):
					f += video_filename[len_p : ]
					for pat in pat_fix:
						f = re.sub(pat[0], pat[1], f)
				elif (
					fnmatch.fnmatch(video_filename, '*.'+v)
				or	fnmatch.fnmatch(video_filename, '*.'+v+'.*')
				):
					r, vid, ext = video_filename.split('.')
					if r in res_list:
						f += ','+v+','+res_list[r]+'.'+(ext or 'mp4')
					else:
						f = separated_dir+'/'+f+','+v+',1920x1080.'+(
							'mp4' if r == 'v' else
							''.join(video_filename.split(v)[1 : ]).strip('._')+'_audio.wav'
						)
				else:
					p = re.search(pat_page_title, f)
					t = re.search(pat_video_title, video_filename)
					if p and t:
						r = t.group('Res')
						if r in res_list and is_title_equivalent(p, t):
							e = t.group('Ext')
							f += ','+v+','+res_list[r]+(e or '.mp4')
						else:
							continue
					else:
						continue

				i += 1

				if TEST:
					print i, video_filename.encode('utf-8'), f.encode('utf-8')
				else:
					if os.path.exists(video_filename):
						print i, video_filename.encode('utf-8')
						dest = dest_dir+'/'+f
						d = dest.rsplit('/', 1)[0]
						if not os.path.exists(d):
							print '- Path not found, make dirs: '+d.encode('utf-8')
							os.makedirs(d)
						if os.path.exists(d):
							move_to_unique_path(video_filename, dest)
						else:
							print '- Fail: could not make dirs.'
			#		else:
			#			print i, video_filename.encode('utf-8'), '- File not found'
#				break	# <- break for speed, no break to rename same-named files of different type
#	if i > 15:
#		break			# <- leftover shortcut for testing

# CYS (Complete YouTube Saver) complete pages in subfolders:
# from "title,v=ID/v=ID.ext" + other files inside
# to "title,v=ID.ext" + "title,v=ID.other_files_archive_ext":
	elif CYS and os.path.isdir(src_page):
		v = src_page.rsplit('v=', 1)[-1 : ][0].encode('utf-8')
		for sub_name in os.listdir(src_page):
			path = src_page+'/'+sub_name
			if not os.path.isdir(path):
				ext = get_ext(sub_name)
				if ext in sub_ext_to_rename:
					dest = src_page+'.'+ext
					if TEST:
						print '- from:', path.encode('utf-8')
						print '- to:', dest.encode('utf-8')
					else:
						print '- Moving up media file:', sub_name.rsplit('v=', 1)[-1 : ][0].encode('utf-8')
						move_to_unique_path(path, dest)
			#	elif TEST: print ext
		if len(os.listdir(src_page)):
			print '- Archiving leftover page files:', v
			if not TEST:
				subprocess.call(encode_cmd(['pynp.bat', 'a', '7re_d', src_page, '.']))
		if os.path.isdir(src_page) and not len(os.listdir(src_page)):
			print -' Deleting empty folder:', v
			if not TEST:
				os.remove(src_page)
		print

i = 0

for src_page in src_list:
	for page_fnmatch in page_fnmatch_by_ext_arr:
		check_src_page(src_page, page_fnmatch)
