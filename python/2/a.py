#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import datetime, glob, os, re, subprocess, sys, time

exe_7zip = 'd:/programs/7-Zip_x64/7zG.exe'
exe_winrar = 'd:/programs/WinRAR_x64/WinRAR.exe'

d = '12.'
flags_all_solid_types = '7res'
flags_all_types = 'anwz'
must_quote = ' ,;>='

def_name = '='
def_suffix = '>'
def_subj = '.'
def_dest = '..'

argc = len(sys.argv)

# - help ----------------------------------------------------------------------

if argc < 2 or sys.argv[1][0] == '-' or sys.argv[1][0] == '/':
	print 'This script makes a set of archives with same content,'
	print 'to see results, compare and hand-pick best suitable ones.'
	print
	print 'Usage: a.py', ' '.join([
		'"['
		+']['.join([
			''.join(sorted(flags_all_solid_types+'1234_069.,;>fzwdatmnc'))
		,	def_name+'<arc.filename>'
		,	def_suffix+'<suffix>'
		])
		+']"'
	,	'["<subj>"|'+def_subj+']'
	,	'["<dest>"|'+def_dest+']'
	,	'[<optional args> ...]'
	])
	print
	print 'Warning: add "quotes" around arguments, that contain any of the symbols:'
	print '"'+must_quote+'"'
	print 'Or quote/escape anything beyond latin letters and digits just in case.'
	print
	print 'Switch letters (concatenate in any order):'
	print '	c: check resulting command lines without running them'
	print
	print '---- speed/size/priority:'
	print '	_: start all subprocesses minimized'
	print '	0: no compression settings (store file content as is)'
	print '	6: big data compression settings (256 MB dictionary, 256 B word size)'
#	print '	9: maximum compression settings (not always best result though)'
	print
	print '---- group source files:'
	print '	1: make separate archives for each group of files'
	print '		by first found numeric ID in filename (name1part2 -> name1*)'
	print '	2: same as 1 but create filelist files (in destination folder)'
	print '		to separate ambiguous cases, like when "name1*" mask'
	print '		would undesirably capture "name1a" and "name12" files'
	print '	12: same as 2 but files without ID go to one list, not separate'
	print '	. and/or ,: same as numbers but ID may also contain dots and/or commas'
	print '		("1" is implied until any other is given)'
	print '	3: equivalent to "'+d+'"'
	print '	4 and/or f: make separate archives for each file/dir of subject mask'
#	print 'TODO ->		4: only dirs'
#	print 'TODO ->		f: only files'
#	print 'TODO ->	5 and/or g: make separate archives for each group of subjects'
#	print 'TODO ->		group by longest common filename parts'
#	print 'TODO ->		5: name part break can include alphanumerics, etc'
#	print 'TODO ->		g: name part break only by punctuation or spaces'
#	print 'TODO ->		g5: start comparing from longest filenames'
#	print 'TODO ->		5g: start comparing from shortest filenames'
#	print 'TODO ->		if "4f" aren\'t set, skip singletons'
#	print 'TODO ->		("45fg" are cross-compatible, but disabled with any ID-grouping)'
	print
	print '---- archive types:'
	print '	7: make a .7z file with 7-Zip'
	print '	z: make a .zip file with 7-Zip'
	print '	w: make a .zip file with WinRAR'
	print '	r: make a .rar file with WinRAR'
	print '	s: make solid archives'
	print '	e: make solid by extension'
	print '	n: make non-solid archives, also assumed when no "s" or "e"'
	print '	a: make a set of solid variants, equivalent to "'+flags_all_solid_types+'"'
	print '	8: make all types currently supported, equivalent to "'+flags_all_types+'"'
	print
	print '---- archive filenames:'
	print '	t: add "_YYYY-mm-dd_HH-MM-SS" script start time to all filenames'
	print '	m: add each archive\'s last-modified time to its filename'
	print '	;: timestamp fotmat = ";_YYYY-mm-dd,HH-MM-SS"'
	print '	>: put timestamp before archive type suffix'
	print '	=filename>suffix: add given suffix between timestamp and archive type'
	print
	print '---- change source files:'
	print '	d: delete done source files (only by WinRAR, or 7-Zip since v17)'
	print
	print 'Example 1: a.py a  	(subj = current folder, destination = 1 folder up)'
	print 'Example 2: a.py a "*some*thing*"    (destination = 1 up so wildcard won\'t see archives)'
	print 'Example 3: a.py a "subfolder/file"  (destination = here, no wildcard, safe)'
	print 'Example 4: a.py ";3dat" "c:/subfolder/*.txt" "d:/dest/folder" "-x!readme.txt"'
	print 'Example 5: a.py "7r'+def_name+'dest_filename" "@path/to/subj_listfile" "../../dest/folder"'
	sys.exit()

# - functions -----------------------------------------------------------------

def uniq(n, e):
	r = n+e
	if os.path.exists(r):
		r = n+t0+e
	while os.path.exists(r):
		r = '(2).'.join(r.rsplit('.', 1))
	return r.replace('/', os.sep)

def is_any_char_of_a_in_b(a, b):
	for c in a:
		if b.find(c) >= 0:
			return True
	return False

def pad_list(a, minimum_len=2, pad_value=''):
	diff = minimum_len - len(a)
	return (a + [pad_value] * diff) if diff > 0 else a

def quoted_list(a):
	return map(lambda x: '"'+x+'"' if is_any_char_of_a_in_b(must_quote, x) else x, a)

def append_cmd(paths, suffix, opt_args=None):
	global cmd

	subj, dest = paths
	rar = suffix.find('rar') > suffix.find('7z')
	a = (cmd_winrar if rar else cmd_7zip) + (opt_args or [])
	if suffix.find('.zip') >= 0:
		a = filter(bool, map(
			lambda x: (
				None if x[0:4] == '-mqs'
			else	None if x[0:4] == '-md='
			else	(None if '0' in flag else '-mfb=256') if x[0:5] == '-mfb='
			else	x
			), a
		))

	dest = uniq(dest, suffix)
	path_args = (
		[('-n' if rar else '-i')+subj, '--', dest] if ('@' in subj) else
		['--', dest, subj]
	)

	cmd.append([
		1 if rar else 0
	,	dest
	,	a + path_args
	,	',' in suffix
	])
	return 1

def queue(subj):
	global cmd, dest, del_warn
	name = def_name or subj
	mask = ('*' in subj) or ('?' in subj)
	if len(name.replace('.', '')) > 0:
		if '/' in name:
			name = name.rsplit('/', 1)[1]

		# re-guess dest arg when not given:
		if (
			(
				argc < 4 or
				not len(sys.argv[3])
			) and not (
				mask or
				subj == def_subj
			)
		):
			dest = '.'

		for i in ['"\'', '?', ':;', '/,', '\\,', '|,', '<', '>', '*']:
			name = name.replace(i[0], i[1] if len(i) > 1 else '_')
	else:
		name = 'default'
	print 'name:	', name

	name = dest+'/'+name+(t0 if 't' in flag else '')
	mass = mask or ('@' in subj) or os.path.isdir(subj)
	uncm = ',store' if '0' in flag else ''
	dcsz = ',d=256m' if '6' in flag else ''
	subj = subj.replace('/', os.sep)

	paths = [subj, name]

	if '7' in flag:
		ext = (uncm or dcsz)+'.7z'
		solid = 0
		if mass and not uncm:
			if 'e' in flag: solid += append_cmd(paths, ',se'+ext, ['-ms=e'])
			if 's' in flag: solid += append_cmd(paths, ',s'+ext, ['-ms'])
		if not solid or 'n' in flag: append_cmd(paths, ext, ['-ms=off'])

	ext = uncm+'.zip'

	if 'z' in flag: append_cmd(paths, ',7z'+ext)
	if 'w' in flag: append_cmd(paths, ',winrar'+ext)

	if 'r' in flag:
		ext = uncm+'.rar'
		solid = 0
		if mass and not uncm:
			if 'e' in flag: solid += append_cmd(paths, ',se'+ext, ['-se'])
			if 's' in flag: solid += append_cmd(paths, ',s'+ext, ['-s'])
		if not solid or 'n' in flag: append_cmd(paths, ext, ['-s-'])

	# delete subj files, only for last queued cmd per subj:
	if 'd' in flag:
		da = (
			['-df', '-y'] if ('w' in flag) or ('r' in flag) else
			['-sdel', '-y'] if ('7' in flag) or ('z' in flag) else
			[]
		)
		if da:
			j = len(cmd) - 1
			a = cmd[j][2]
			i = (a.index('--') - len(a)) if '--' in a else -2
			a = a[:i] + da + a[i:]
			cmd[j][2] = a
		else:
			del_warn = 1

# - calculate params ----------------------------------------------------------

flag, def_name = pad_list((sys.argv[1].strip('"') or '').split(def_name, 1))

flag = (
	flag
	.replace('8', flags_all_types)
	.replace('a', flags_all_solid_types)
	.replace('3', d)
#+'9'
)

if def_suffix in def_name and not def_suffix in flag:
	flag += def_suffix

def_name, def_suffix = pad_list((def_name or '').split(def_suffix, 1))

subj = sys.argv[2].replace('\\', '/') if argc > 2 and len(sys.argv[2]) > 0 else def_subj
dest = sys.argv[3].replace('\\', '/') if argc > 3 and len(sys.argv[3]) > 0 else def_dest
rest = sys.argv[4:] if argc > 4 else []

print 'argc:	', argc
print 'flags:	', flag
print 'suffix:	', def_suffix
print 'subj:	', subj
print 'dest:	', dest
print 'etc:	', ' '.join(rest)

if '_' in flag:
	SW_MINIMIZE = 6
	minimized = subprocess.STARTUPINFO()
	minimized.dwFlags = subprocess.STARTF_USESHOWWINDOW
	minimized.wShowWindow = SW_MINIMIZE
else:
	minimized = None

foreach = (subj[0] != '@') and (('4' in flag) or ('f' in flag))
for_ID = ''.join(map(lambda i: i if i in flag else '', d+','))

cmd_7zip = (
	[exe_7zip, 'a', '-stl', '-ssw', '-mqs']
+	(
		['-mx0', '-mmt=off'] if '0' in flag else
		['-mx9', '-mmt=2'] #if '9' in flag else []
	)
+	(
		[] if '0' in flag else
		['-md=256m', '-mfb=256'] if '6' in flag else
		['-md=64m', '-mfb=273'] #if '9' in flag else []

	#	['-m0=LZMA2:d=256m:fb=256'] if '6' in flag else
	#	['-m0=LZMA:d=64m:fb=273']
	)
+	rest
)

cmd_winrar = (
	[exe_winrar, 'a', '-tl', '-dh']
+	(
		['-m0', '-mt1'] if '0' in flag else
		['-m5', '-mt4']
	)
+	(
		['-ibck'] if minimized else
		[]
	)
+	(
		[] if (
			foreach
			or '-r' in rest
			or '-r-' in rest
			or '-r0' in rest
		) else
		['-r0']
	)
+	map(lambda x: '-x'+x[3:] if x[0:3] == '-x!' else x, rest)
)

cmd = []
del_warn = 0
time_format = ';_%Y-%m-%d,%H-%M-%S' if ';' in flag else '_%Y-%m-%d_%H-%M-%S'
t0 = time.strftime(time_format)

# - fill batch queue ----------------------------------------------------------

if foreach or for_ID:
	names = (
		glob.glob(subj) if ('*' in subj or '?' in subj) else
		os.listdir(subj) if os.path.isdir(subj) else
		[subj]
	)
	if for_ID:
		dots = ''
		d = '.,'
		for i in d:
			if i in for_ID:
				dots += i
		d = '\d'+dots
		pat_ID = re.compile(r'^(\D*\d['+d+']*)([^'+d+']|$)' if dots else r'^(\D*\d+)(\D|$)')

		if '2' in for_ID:
			no_group = def_name or 'default'
			other_to_1 = '1' in for_ID
			d = {}
			for subj in names:
				s = re.search(pat_ID, subj)
				n = s.group(1) if s else no_group if other_to_1 else subj
				if not n in d:
					d[n] = []
				d[n].append(subj)
			names = []
			for i in d.keys():
				name = dest+'/'+i+'_list.txt'
				names.append('@'+name)
				if not 'c' in flag:
					f = open(name, 'wb')
					r = f.write('\n'.join(d[i]))
					f.close()
		else:
			d = []
			for subj in names:
				s = re.search(pat_ID, subj)
				if s:
					n = s.group(1)+'*'
					if not (n in d):
						d.append(n)
				else:
					d.append(subj)
			names = d
	for subj in names:
		queue(subj)
else:
	queue(subj)

if not (len(cmd) > 0):
	print '----	----	Nothing to run, command queue is empty.'
	sys.exit()

if del_warn:
	print '----	----	WARNING, only WinRAR or 7-zip v17+ can delete files!'

# - run batch queue -----------------------------------------------------------

codes = [
# 7-Zip exit codes: http://sevenzip.sourceforge.jp/chm/cmdline/exit_codes.htm
	{
		0: 'No error'
	,	1: 'Warning (Non fatal error(s)). For example, one or more files were locked by some other application, so they were not compressed.'
	,	2: 'Fatal error'
	,	7: 'Command line error'
	,	8: 'Not enough memory for operation'
	,	255: 'User stopped the process'
	}
# WinRAR exit codes: http://en.helpdoc-online.com/winrar_4/source/html/helpexitcodes.htm
,	{
		0: 'Successful operation.'
	,	1: 'Warning. Non fatal error(s) occurred.'
	,	2: 'A fatal error occurred.'
	,	3: 'Invalid CRC32 control sum. Data is damaged.'
	,	4: 'Attempt to modify a locked archive.'
	,	5: 'Write error.'
	,	6: 'File open error.'
	,	7: 'Wrong command line option.'
	,	8: 'Not enough memory.'
	,	9: 'File create error.'
	,	10: 'No files matching the specified mask and options were found.'
	,	255: 'User break.'
	}
]

# - run batch queue -----------------------------------------------------------

check = 0

for i in cmd:
	print ' '.join(quoted_list(i[2]))
	if not 'c' in flag:
		e = subprocess.call(i[2], startupinfo=minimized)
		if os.path.exists(i[1]):
			c = ',' if ('>' in flag and len(i) > 3 and i[3]) else '.'
# TODO: remember [name][;_date][,any,suffixes][.ext] as parts, do not rely on split+join
			d = i[1]
			j = (
				datetime.datetime.fromtimestamp(os.path.getmtime(d)).strftime(time_format)
				if 'm' in flag
				else ''
			) + def_suffix + c
			if j != c:
				d = j.join(d.rsplit(c, 1))
				while os.path.exists(d):
					d = '(2).'.join(d.rsplit('.', 1))
				print i[1]
				print d
				os.rename(i[1], d)
		print e, ':', codes[i[0]][e] if e in codes[i[0]] else 'Unknown code', '\n'
		check += e
if check:
	raw_input('----	----	Done. See error messages above, press Enter to continue.')

# unexpected EOF my ass
