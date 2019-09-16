#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import datetime, glob, os, re, subprocess, sys, time

flags_group_by_num_any_sep = '12.,'
flags_group_by_num_dot = '12.'
flags_all_solid_types = '7res'
flags_all_types = 'anwz'
must_quote = ' ,;>='

def_name_fallback = 'default'
def_name_separator = '='
def_suffix_separator = '>'
def_subj = '.'
def_dest = '..'

# - find executables ----------------------------------------------------------

# https://stackoverflow.com/a/189664/8352410
class GetOutOfLoop( Exception ):
	pass

def get_exe_paths():
	exe_paths_found = {}
	exe_try_root_dirs = ['%ProgramW6432%', '%ProgramFiles%', '%ProgramFiles(x86)%', '%CommonProgramFiles%', 'C:/Program Files', '']
	exe_try_subdir_suffixes = ['_x64', 'x64', '(x64)', '_(x64)', ' (x64)', '']
	exe_try_filename_suffixes = ['.exe', '']
	exe_try_types = {
		'7z': {
			'subdirs': ['7-Zip', '7zip']
		,	'filenames': ['7zG']
		}
	,	'rar': {
			'subdirs': ['WinRAR']
		,	'filenames': ['WinRAR']
		}
	}

	for type_name, type_part in exe_try_types.items():
		try:
			for root_dir in exe_try_root_dirs:
				env_dir = root_dir.strip('%')

				if env_dir != root_dir:
					env_dir = os.environ.get(env_dir)

					if env_dir:
						root_dir = env_dir

				for subdir in type_part['subdirs']:
					for filename in type_part['filenames']:
						for subdir_suffix in exe_try_subdir_suffixes:
							for filename_suffix in exe_try_filename_suffixes:
								path = (
									root_dir
								+'/'+	subdir + subdir_suffix
								+'/'+	filename + filename_suffix
								).replace('\\', '/')

								if os.path.isfile(path):
									exe_paths_found[type_name] = path

									raise GetOutOfLoop

			exe_paths_found[type_name] = type_part['filenames'][0]

		except GetOutOfLoop:
			pass

	return exe_paths_found

exe_paths = get_exe_paths()

# - display help --------------------------------------------------------------

def print_help():
	print
	print 'Description:'
	print
	print '	This script calls several preinstalled programs in a batch'
	print '	to make a set of archives with same content with intention'
	print '	to compare and hand-pick the best or most suitable results.'
	print
	print 'Usage:'
	print
	print '	a.py', ' '.join([
		'"['
		+']['.join([
			''.join(sorted(set(
				'1234_069.,;fzwdatmnckl'
			+	flags_all_solid_types
			+	def_suffix_separator
			)))
		,	def_name_separator+'<name>'
		,	def_suffix_separator+'<suffix>'
		])
		+']"'
	,	'["<subj>"|'+def_subj+']'
	,	'["<dest>"|'+def_dest+']'
	,	'[<optional args> ...]'
	])
	print
	print 'Warning:'
	print
	print '	In shell, add "quotes" around arguments, that contain any of the'
	print '	following symbols: "'+must_quote+'"'
	print '	Or quote/escape anything beyond latin letters and digits just in case.'
	print
	print 'Current executable paths to be used (found or fallback):'
	print

	for k, v in exe_paths.items():
		print k + ':	' + v

	print
	print 'Switch letters (concatenate in any order, any case):'
	print
	print '	c: check resulting command lines without running them.'
	print '	k: don\'t wait for key press after errors.'
	print
	print '	---- speed/size/priority:'
	print '	_: start all subprocesses minimized.'
	print '	L: store identical files as references to one copy of content.'
	print '		(only by WinRAR since v5)'
	print '		(limits storage redundancy and archive editing)'
	print '	0: no compression (store file content as is, overrides "6").'
	print '	6: big data compression settings (256 MB dictionary, 256 B word size).'
	print
	print '	---- group subjects into separate archives:'
	print '	(each name is appended with comma to "=filename" from arguments)'
	print '	1: make separate archives for each group of subjects'
	print '		by first found numeric ID in subject name.'
	print '		(name1part2 -> name1*)'
	print '	2: same as "1" but create filelist files (in destination folder)'
	print '		to separate ambiguous cases, like when "name1*" mask'
	print '		would undesirably capture "name1a" and "name12" files.'
	print '	12: same as "2" but files without ID go to one list, not separate.'
	print '	. and/or ,: same as "1" or "2" but ID may contain dots and/or commas.'
	print '		("1" is implied unless "2" is given)'
	print '	3: shortcut, equivalent to "'+flags_group_by_num_dot+'".'
	print '	4: make separate archives for each dir of subject mask.'
	print '	f: make separate archives for each file of subject mask.'
	print '		(use one of "4" or "f" with any of "'+flags_group_by_num_any_sep+'" to add only dirs or'
	print '		files to the groups)'
#	print 'TODO ->	5 and/or g: make separate archives for each group of subjects'
#	print 'TODO ->		by longest common subject name parts.'
#	print 'TODO ->		5: name part break can include alphanumerics, etc.'
#	print 'TODO ->		g: name part break only by punctuation or spaces.'
#	print 'TODO ->		g5: start comparing from longest filenames.'
#	print 'TODO ->		5g: start comparing from shortest filenames.'
#	print 'TODO ->		if "4" or "f" is not set, skip singletons.'
#	print 'TODO ->		("45fg" are cross-compatible, but disabled with any of "'+flags_group_by_num_any_sep+'").'
	print
	print '	---- archive types:'
	print '	7: make a .7z  file with 7-Zip.'
	print '	z: make a .zip file with 7-Zip.'
	print '	w: make a .zip file with WinRAR.'
	print '	r: make a .rar file with WinRAR.'
	print '	s: make solid archives.'
	print '	e: make archives with solid blocks grouped by filename extension.'
	print '	n: make non-solid archives (implied unless "s" or "e" is given).'
	print '	a: make a set of solid variants, equivalent to "'+flags_all_solid_types+'".'
	print '	8: make all types currently supported, equivalent to "'+flags_all_types+'".'
	print
	print '	---- archive filenames:'
	print '	t: add "_YYYY-mm-dd_HH-MM-SS" script start time to all filenames.'
	print '	m: add each archive\'s last-modified time to its filename.'
	print '	;: timestamp fotmat = ";_YYYY-mm-dd,HH-MM-SS".'
	print '	'+def_suffix_separator+': put timestamp before archive type suffix.'
	print '	'+def_name_separator+'filename'+def_suffix_separator+'suffix: add given suffix between timestamp and archive type.'
	print
	print '	---- clean up:'
	print '	d: delete subjects (source files) when done.'
	print '		(only by WinRAR, or 7-Zip since v17)'
	print '		(if by WinRAR, last archive is tested before deleting subjects)'
	print
	print 'Example 1: a.py a'
	print '	(default subj = current folder, destination = 1 folder up)'
	print
	print 'Example 2: a.py a "*some*thing*"'
	print '	(default destination = 1 up, so wildcard won\'t grab result archives)'
	print
	print 'Example 3: a.py a "subfolder/file"'
	print '	(default destination = here, safe because no wildcard)'
	print
	print 'Example 4: a.py ";3dat" "c:/subfolder/*.txt" "d:/dest/folder" "-x!readme.txt"'
	print 'Example 5: a.py "7r_e'+def_name_separator+'dest_filename" "@path/to/subj_listfile" "../../dest/folder"'

argc = len(sys.argv)

if argc < 2 or sys.argv[1][0] == '-' or sys.argv[1][0] == '/':
	print_help()
	sys.exit()

# - aux functions -------------------------------------------------------------

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

def quoted_list(a):
	return map(lambda x: '"'+x+'"' if is_any_char_of_a_in_b(must_quote, x) else x, a)

def pad_list(a, minimum_len=2, pad_value=''):
	diff = minimum_len - len(a)

	return (a + [pad_value] * diff) if diff > 0 else a

def append_cmd(paths, suffix, opt_args=None):
	global cmd_queue

	subj, dest = paths
	rar = suffix.find('rar') > suffix.find('7z')
	exe_type = 'rar' if rar else '7z'
	cmd_args = cmd_template[exe_type] + (opt_args or [])

	if suffix.find('.zip') >= 0:
		cmd_args = filter(bool, map(
			lambda x: (
				None if x[0:4] == '-mqs'
			else	None if x[0:4] == '-md='
			else	(None if '0' in flag else '-mfb=256') if x[0:5] == '-mfb='
			else	x
			), cmd_args
		))

	dest = uniq(dest, suffix)
	path_args = (
		[('-n' if rar else '-i')+subj, '--', dest] if ('@' in subj) else
		['--', dest, subj]
	)

	cmd_queue.append({
		'exe_type': exe_type
	,	'dest': dest
	,	'args': cmd_args + path_args
	,	'suffix': (suffix.rsplit('.', 1)[0] + '.') if ',' in suffix else '.'
	})

	return 1

def queue(subj, foreach=False):
	global cmd_queue, dest, del_warn

	name = (def_name + ',' + subj) if (foreach and def_name and subj) else (def_name or subj)
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
	else:
		name = def_name_fallback

	for i in ['"\'', '?', ':;', '/,', '\\,', '|,', '<', '>', '*']:
		name = name.replace(i[0], i[1] if len(i) > 1 else '_')

	print 'name:	', name

	name = dest+'/'+name+(t0 if 't' in flag else '')
	mass = mask or ('@' in subj) or os.path.isdir(subj)
	ddup = ',dedup' if 'l' in flag else ''
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
		ext = (uncm or dcsz)+ddup+'.rar'
		solid = 0
		if mass and not uncm:
			if 'e' in flag: solid += append_cmd(paths, ',se'+ext, ['-se'])
			if 's' in flag: solid += append_cmd(paths, ',s'+ext, ['-s'])
		if not solid or 'n' in flag: append_cmd(paths, ext, ['-s-'])

	# delete subj files, only for last queued cmd per subj:
	if 'd' in flag:
		da = (
			['-df', '-y', '-t'] if ('w' in flag) or ('r' in flag) else
			['-sdel', '-y'] if ('7' in flag) or ('z' in flag) else
			[]
		)
		if da:
			j = len(cmd_queue) - 1
			a = cmd_queue[j]['args']
			i = (a.index('--') - len(a)) if '--' in a else -2
			a = a[:i] + da + a[i:]
			cmd_queue[j]['args'] = a
		else:
			del_warn = 1

# - calculate params ----------------------------------------------------------

flag, def_name = pad_list((sys.argv[1].strip('"') or '').split(def_name_separator, 1))

flag = (
	flag
	.lower()
	.replace('8', flags_all_types)
	.replace('a', flags_all_solid_types)
	.replace('3', flags_group_by_num_dot)
#+'9'
)

if (def_suffix_separator in def_name) and not (def_suffix_separator in flag):
	flag += def_suffix_separator

def_name, def_suffix = pad_list((def_name or '').split(def_suffix_separator, 1))

subj = sys.argv[2].replace('\\', '/') if argc > 2 and len(sys.argv[2]) > 0 else def_subj
dest = sys.argv[3].replace('\\', '/') if argc > 3 and len(sys.argv[3]) > 0 else def_dest
rest = sys.argv[4:] if argc > 4 else []

print
print 'argc:	', argc
print 'flags:	', flag
print 'suffix:	', def_suffix
print 'subj:	', subj
print 'dest:	', dest
print 'etc:	', ' '.join(rest)
print

if '_' in flag:
	SW_MINIMIZE = 6
	minimized = subprocess.STARTUPINFO()
	minimized.dwFlags = subprocess.STARTF_USESHOWWINDOW
	minimized.wShowWindow = SW_MINIMIZE
else:
	minimized = None

foreach_dir  = '4' in flag
foreach_file = 'f' in flag
foreach = (subj[0] != '@') and (foreach_dir or foreach_file)
foreach_ID = ''.join(map(lambda i: i if i in flag else '', flags_group_by_num_any_sep))

cmd_template = {}
cmd_template['7z'] = (
	[exe_paths['7z'], 'a', '-stl', '-ssw', '-mqs']
+	(
		['-mx0', '-mmt=off'] if '0' in flag else
		['-mx9', '-mmt=2'] + (
			['-md=256m', '-mfb=256'] if '6' in flag else
			['-md=64m', '-mfb=273']
		)
	)
+	rest
)

pat_inex = re.compile(r'^(?P<InEx>-[ix])(?P<Recurse>r[0-]*)?(?P<Value>[!@].*)$', re.I)
rest_winrar = []

for arg in rest:
	res = re.search(pat_inex, arg)
	if res:
		rest_winrar.append(res.group('InEx') + res.group('Value'))
		r = res.group('Recurse')
		if r:
			rest_winrar.append('-' + r)
	else:
		rest_winrar.append(arg)

if not (
	foreach
or	'-r' in rest_winrar
or	'-r-' in rest_winrar
or	'-r0' in rest_winrar
):
	rest_winrar.append('-r0')

cmd_template['rar'] = (
	[exe_paths['rar'], 'a', '-tl', '-dh']
+	(
		['-m0', '-mt1'] if '0' in flag else
		['-m5', '-mt4'] + (
			['-ma5', '-md256m'] if '6' in flag else
			[]
		)
	)
+	(
		['-ma5', '-oi:0'] if 'l' in flag else
		[]
	)
+	(
		['-ibck'] if minimized else
		[]
	)
+	rest_winrar
)

cmd_queue = []
del_warn = 0
time_format = ';_%Y-%m-%d,%H-%M-%S' if ';' in flag else '_%Y-%m-%d_%H-%M-%S'
t0 = time.strftime(time_format)

# - fill batch queue ----------------------------------------------------------

if foreach or foreach_ID:
	names = (
		glob.glob(subj) if ('*' in subj or '?' in subj) else
		os.listdir(subj) if os.path.isdir(subj) else
		[subj]
	)

	if foreach_ID:
		dots = ''
		d = '.,'
		for i in d:
			if i in foreach_ID:
				dots += i
		d = '\d'+dots
		pat_ID = re.compile(r'^(\D*\d['+d+']*)([^'+d+']|$)' if dots else r'^(\D*\d+)(\D|$)')

		if '2' in foreach_ID:
			no_group = def_name or def_name_fallback
			other_to_1 = '1' in foreach_ID
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
		if foreach_dir != foreach_file and foreach_dir != os.path.isdir(subj):
			continue

		queue(subj, foreach=True)
else:
	queue(subj)

if len(cmd_queue) > 0:
	print
else:
	print '----	----	Nothing to do, command queue is empty.'
	sys.exit()

if del_warn:
	print '----	----	WARNING, only WinRAR or 7-zip v17+ can delete files!'
	print

exit_codes = {
# http://sevenzip.sourceforge.jp/chm/cmdline/exit_codes.htm
	'7z': {
		0: 'No error'
	,	1: 'Warning (Non fatal error(s)). For example, one or more files were locked by some other application, so they were not compressed.'
	,	2: 'Fatal error'
	,	7: 'Command line error'
	,	8: 'Not enough memory for operation'
	,	255: 'User stopped the process'
	}
# http://en.helpdoc-online.com/winrar_4/source/html/helpexitcodes.htm
,	'rar': {
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
}

error_count = 0

# - run batch queue -----------------------------------------------------------

for cmd in cmd_queue:
	cmd_args = cmd['args']
	cmd_dest = cmd['dest']
	cmd_type = cmd['exe_type']
	cmd_suffix = cmd['suffix']

	print ' '.join(quoted_list(cmd_args))

	if not 'c' in flag:
		e = subprocess.call(cmd_args, startupinfo=minimized)

		if e:
			error_count += 1

		if os.path.exists(cmd_dest):
			c = cmd_suffix if ((def_suffix_separator in flag) and cmd_suffix) else '.'
			d = cmd_dest
			j = (
				datetime.datetime.fromtimestamp(os.path.getmtime(d)).strftime(time_format)
				if 'm' in flag
				else ''
			) + def_suffix + c

			if j != c:
				d = j.join(d.rsplit(c, 1))
				while os.path.exists(d):
					d = '(2).'.join(d.rsplit('.', 1))

				print cmd_dest
				print d

				os.rename(cmd_dest, d)

		c = exit_codes[cmd_type]

		print e, ':', c[e] if e in c else 'Unknown code'
		print

# - finished ------------------------------------------------------------------

if 'c' in flag:
	print

if error_count > 0:
	if 'k' in flag:
		print '----	----	Done', len(cmd_queue), 'archives,', error_count, 'errors. See messages above.'
	else:
		raw_input('----	----	Done', len(cmd_queue), 'archives,', error_count, 'errors. Press Enter to continue.')
elif 'c' in flag:
	print '----	----	Total', len(cmd_queue), 'commands.'
else:
	print '----	----	Done', len(cmd_queue), 'archives.'
