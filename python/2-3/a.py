#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Python 2 or 3 should work.

import datetime, glob, os, re, subprocess, sys, time

# Use colored text if available:
try:
	from termcolor import colored, cprint
	import colorama

	colorama.init()

except ImportError:
	def colored(*list_args, **keyword_args): return list_args[0]
	def cprint(*list_args, **keyword_args): print(list_args[0])

# - Configuration and defaults ------------------------------------------------

print_encoding = sys.getfilesystemencoding() or 'utf-8'

flags_group_by_num_any_sep = '12.,'
flags_group_by_num_dot = '12.'
flags_all_solid_types = '7res'
flags_all_types = 'anwz'
must_quote_chars = ' ,;>='

def_name_fallback = 'default'
def_name_separator = '='
def_suffix_separator = '>'
def_subj = '.'
def_dest = '..'

dest_name_replacements = ['"\'', '?', ':;', '/,', '\\,', '|,', '<', '>', '*']

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

# - Declare functions ---------------------------------------------------------

# https://stackoverflow.com/a/189664/8352410
class GetOutOfLoop( Exception ):
	pass

def normalize_slashes(path):
	return path.replace('\\', '/')

def fix_slashes(path):
	if os.sep != '/':
		path = path.replace('/', os.sep)

	if os.sep != '\\':
		path = path.replace('\\', os.sep)

	return path

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
								path = fix_slashes(
									root_dir + '/' +
									subdir + subdir_suffix + '/' +
									filename + filename_suffix
								)

								if os.path.isfile(path):
									exe_paths_found[type_name] = path

									raise GetOutOfLoop

			exe_paths_found[type_name] = type_part['filenames'][0]

		except GetOutOfLoop:
			pass

	return exe_paths_found

def get_text_encoded_for_print(text):
	return text.encode(print_encoding) if sys.version_info.major == 2 else text

def print_with_colored_prefix(prefix, value, color=None):
	print('{} {}'.format(colored(prefix, color or 'yellow'), value))

def print_help():
	self_name = os.path.basename(__file__)
	exe_paths = get_exe_paths()

	all_flags = ''.join(sorted(set(
		'1234_069.,;fzwdatmnckl'
	+	flags_all_solid_types
	+	def_suffix_separator
	)))

	help_text_lines = [
		''
	,	colored('* Description:', 'yellow')
	,	'	This script calls several preinstalled programs in a batch'
	,	'	to make a set of archives with same content with intention'
	,	'	to compare and hand-pick the best or most suitable results.'
	,	''
	,	colored('* Usage:', 'yellow')
	,	'	{0}'
		+	colored(
				' "['
				+ ']['.join([
					'<flags>'
				,	def_name_separator + '<name>'
				,	def_suffix_separator + '<suffix>'
				])
				+ ']"'
			,	'cyan'
			)
		+	'\n		'
		+	colored(' ["<subj>"|' + def_subj + ']', 'magenta')
		+	colored(' ["<dest>"|' + def_dest + ']', 'magenta')
		+	colored(' [<optional args> ...]', 'magenta')
	,	''
	,	colored('* Warning:', 'yellow')
	,	'	In shell, add "quotes" around arguments, that contain any of the'
	,	'	following symbols: "' + must_quote_chars + '"'
	,	'	Or quote/escape anything beyond latin letters and digits just in case.'
	,	''
	,	colored('* Current executable paths to be used (found or fallback):', 'yellow')
	] + [
		'	{}:	{}'.format(k, v) for k, v in exe_paths.items()
	] + [
		''
	,	colored('* Flags (switch letters, concatenate in any order, any case):', 'yellow')
	,	'	c: check resulting command lines without running them.'
	,	'	k: don\'t wait for key press after errors.'
	,	''
	,	'	---- speed/size/priority:'
	,	'	_: start all subprocesses minimized.'
	,	'	L: store identical files as references to one copy of content.'
	,	'		(only by WinRAR since v5)'
	,	'		(limits storage redundancy and archive editing)'
	,	'	0: no compression (store file content as is, overrides "6").'
	,	'	6: big data compression settings (256 MB dictionary, 256 B word size).'
	,	''
	,	'	---- group subjects into separate archives:'
	,	'	(each name is appended with comma to "=filename" from arguments)'
	,	'	1: make separate archives for each group of subjects'
	,	'		by first found numeric ID in subject name.'
	,	'		(name1part2 -> name1*)'
	,	'	2: same as "1" but create filelist files (in destination folder)'
	,	'		to separate ambiguous cases, like when "name1*" mask'
	,	'		would undesirably capture "name1a" and "name12" files.'
	,	'	12: same as "2" but files without ID go to one list, not separate.'
	,	'	. and/or ,: same as "1" or "2" but ID may contain dots and/or commas.'
	,	'		("1" is implied unless "2" is given)'
	,	'	3: shortcut, equivalent to "' + flags_group_by_num_dot + '".'
	,	'	4: make separate archives for each dir of subject mask.'
	,	'	f: make separate archives for each file of subject mask.'
	,	'		(use one of "4" or "f" with any of "' + flags_group_by_num_any_sep + '" to add only dirs or'
	,	'		files to the groups)'
#	,	'TODO ->	5 and/or g: make separate archives for each group of subjects'
#	,	'TODO ->		by longest common subject name parts.'
#	,	'TODO ->		5: name part break can include alphanumerics, etc.'
#	,	'TODO ->		g: name part break only by punctuation or spaces.'
#	,	'TODO ->		g5: start comparing from longest filenames.'
#	,	'TODO ->		5g: start comparing from shortest filenames.'
#	,	'TODO ->		if "4" or "f" is not set, skip singletons.'
#	,	'TODO ->		("45fg" are cross-compatible, but disabled with any of "'+flags_group_by_num_any_sep+'").'
#	,	'TODO ->	9, 99, 999, etc.: keep each group population below this number.'
#	,	'TODO ->		(split first by mod.dates - years, then months, days, hours,'
#	,	'TODO ->		minutes, seconds, at last batch subjects with same-second'
#	,	'TODO ->		timestamps alphabetically in simple N+1 groups - 10, 100, etc.)'
	,	''
	,	'	---- archive types:'
	,	'	7: make a .7z  file with 7-Zip.'
	,	'	z: make a .zip file with 7-Zip.'
	,	'	w: make a .zip file with WinRAR.'
	,	'	r: make a .rar file with WinRAR.'
	,	'	s: make solid archives.'
	,	'	e: make archives with solid blocks grouped by filename extension.'
	,	'	n: make non-solid archives (implied unless "s" or "e" is given).'
	,	'	a: make a set of solid variants, equivalent to "' + flags_all_solid_types + '".'
	,	'	8: make all types currently supported, equivalent to "' + flags_all_types + '".'
	,	''
	,	'	---- archive filenames:'
	,	'	t: add "_YYYY-mm-dd_HH-MM-SS" script start time to all filenames.'
	,	'	m: add each archive\'s last-modified time to its filename.'
	,	'	;: timestamp fotmat = ";_YYYY-mm-dd,HH-MM-SS".'
	,	'	' + def_suffix_separator + ': put timestamp before archive type suffix.'
	,	'	' + def_name_separator + 'filename' + def_suffix_separator + 'suffix: add given suffix between timestamp and archive type.'
	,	''
	,	'	---- clean up:'
	,	'	d: delete subjects (source files) when done.'
	,	'		(only by WinRAR, or 7-Zip since v17)'
	,	'		(if by WinRAR, last archive is tested before deleting subjects)'
	,	''
	,	colored('* Examples:', 'yellow')
	,	'	{0} a'
	,	'	(default subj = current folder, destination = 1 folder up)'
	,	''
	,	'	{0} a "*some*thing*"'
	,	'	(default destination = 1 up, so wildcard won\'t grab result archives)'
	,	''
	,	'	{0} a "subfolder/file"'
	,	'	(default destination = here, safe because no wildcard)'
	,	''
	,	'	{0} ";3dat" "c:/subfolder/*.txt" "d:/dest/folder" "-x!readme.txt"'
	,	''
	,	'	{0} "7r_e' + def_name_separator + 'dest_filename" "@path/to/subj_listfile" "../../dest/folder"'
	]

	print('\n'.join(help_text_lines).format(self_name))

def remove_trailing_dots_in_path_parts(path):
	return '/'.join(
		part if part == '.' or part == '..'
		else part.rstrip('.')
		for part in normalize_slashes(path).split('/')
	)

def get_unique_clean_path(path_part_before, path_part_after, timestamp):
	try_count = 0
	full_path = remove_trailing_dots_in_path_parts(path_part_before + path_part_after)

	if os.path.exists(full_path):
		try_count += 1
		full_path = remove_trailing_dots_in_path_parts(path_part_before + timestamp + path_part_after)

	if os.path.exists(full_path):
		full_path_parts = full_path.rsplit('.', 1)

		while os.path.exists(full_path):
			try_count += 1
			full_path = '({}).'.format(try_count).join(full_path_parts)

	return fix_slashes(full_path)

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

def pad_list(a, minimum_len=2, pad_value=''):
	diff = minimum_len - len(a)

	return (a + [pad_value] * diff) if diff > 0 else a

# - Main job function ---------------------------------------------------------

def run_batch_archiving(argv):

	def queue(cmd_queue, dest, subj, foreach=False):

		def append_cmd(cmd_queue, paths, suffix, opt_args=None):
			subj, dest = paths
			rar = suffix.find('rar') > suffix.find('7z')
			exe_type = 'rar' if rar else '7z'
			cmd_args = cmd_template[exe_type] + (opt_args or [])

			if suffix.find('.zip') >= 0:
				cmd_args = list(map(
					lambda x: (
						None if x[0 : 4] == '-mqs'
					else	None if x[0 : 4] == '-md='
					else	(None if '0' in flags else '-mfb=256') if x[0 : 5] == '-mfb='
					else	x
					), cmd_args
				))

			dest = get_unique_clean_path(dest, suffix, t0)
			path_args = (
				[('-n' if rar else '-i') + subj, '--', dest] if is_subj_list else
				['--', dest, subj]
			)

			cmd_queue.append({
				'exe_type': exe_type
			,	'dest': dest
			,	'args': cmd_args + path_args
			,	'suffix': (suffix.rsplit('.', 1)[0] + '.') if ',' in suffix else '.'
			})

			return 1

		name = (def_name + ',' + subj) if (foreach and def_name and subj) else (def_name or subj)

		is_subj_mask = ('*' in subj) or ('?' in subj)
		is_subj_mass = is_subj_mask or is_subj_list or os.path.isdir(subj)

		if len(name.replace('.', '')) > 0:
			if '/' in name:
				name = name.rsplit('/', 1)[1]

			# re-guess dest arg when not given:
			if (
				(
					not argv_dest
				or	not len(argv_dest)
				) and not (
					is_subj_mask
				or	subj == def_subj
				)
			):
				dest = '.'
		else:
			name = def_name_fallback

		for i in dest_name_replacements:
			name = name.replace(i[0], i[1] if len(i) > 1 else '_')

		print_with_colored_prefix('name:', get_text_encoded_for_print(name))

		dest_name = dest + '/' + name + (t0 if 't' in flags else '')
		paths = list(map(fix_slashes, [subj, dest_name]))

		dest_name_part_dedup		= ',dedup' if 'l' in flags else ''
		dest_name_part_uncompressed	= ',store' if '0' in flags else ''
		dest_name_part_dict_size	= ',d=256m' if '6' in flags else ''

		if '7' in flags:
			ext = (dest_name_part_uncompressed or dest_name_part_dict_size) + '.7z'
			solid = 0

			if is_subj_mass and not dest_name_part_uncompressed:
				if 'e' in flags: solid += append_cmd(cmd_queue, paths, ',se' + ext, ['-ms=e'])
				if 's' in flags: solid += append_cmd(cmd_queue, paths, ',s' + ext, ['-ms'])

			if not solid or ('n' in flags): append_cmd(cmd_queue, paths, ext, ['-ms=off'])

		ext = dest_name_part_uncompressed + '.zip'

		if 'z' in flags: append_cmd(cmd_queue, paths, ',7z' + ext)
		if 'w' in flags: append_cmd(cmd_queue, paths, ',winrar' + ext)

		if 'r' in flags:
			ext = (dest_name_part_uncompressed or dest_name_part_dict_size) + dest_name_part_dedup + '.rar'
			solid = 0

			if is_subj_mass and not dest_name_part_uncompressed:
				if 'e' in flags: solid += append_cmd(cmd_queue, paths, ',se' + ext, ['-se'])
				if 's' in flags: solid += append_cmd(cmd_queue, paths, ',s' + ext, ['-s'])

			if not solid or ('n' in flags): append_cmd(cmd_queue, paths, ext, ['-s-'])

		del_warn = 0

		# delete subj files, only for last queued cmd per subj:
		if 'd' in flags:
			da = (
				['-df', '-y', '-t'] if ('w' in flags) or ('r' in flags) else
				['-sdel', '-y'] if ('7' in flags) or ('z' in flags) else
				[]
			)

			if da:
				j = len(cmd_queue) - 1
				a = cmd_queue[j]['args']
				i = (a.index('--') - len(a)) if ('--' in a) else -2
				a = a[ : i] + da + a[i : ]
				cmd_queue[j]['args'] = a
			else:
				del_warn = 1

		return del_warn

# - Check arguments -----------------------------------------------------------

	argv = list(argv)
	argc = len(argv)

	argv_flag = argv.pop(0) if len(argv) else None
	argv_subj = argv.pop(0) if len(argv) else None
	argv_dest = argv.pop(0) if len(argv) else None
	argv_rest = argv if len(argv) else None

# - Show help and exit --------------------------------------------------------

	if (
		not argv_flag
	or	argv_flag[0] == '-'
	or	argv_flag[0] == '/'
	):
		print_help()

		return 1

# - Calculate params ----------------------------------------------------------

	flags, def_name = pad_list((argv_flag.strip('"') or '').split(def_name_separator, 1))

	flags = (
		flags
		.lower()
		.replace('8', flags_all_types)
		.replace('a', flags_all_solid_types)
		.replace('3', flags_group_by_num_dot)
	# + '9'
	)

	if (def_suffix_separator in def_name) and not (def_suffix_separator in flags):
		flags += def_suffix_separator

	def_name, def_suffix = pad_list((def_name or '').split(def_suffix_separator, 1))

	subj = normalize_slashes(argv_subj if argv_subj and len(argv_subj) > 0 else def_subj)
	dest = normalize_slashes(argv_dest if argv_dest and len(argv_dest) > 0 else def_dest)
	rest = argv_rest or []

	print('')
	print_with_colored_prefix('argc:', argc)
	print_with_colored_prefix('flags:', get_text_encoded_for_print(flags))
	print_with_colored_prefix('suffix:', get_text_encoded_for_print(def_suffix))
	print_with_colored_prefix('subj:', get_text_encoded_for_print(subj))
	print_with_colored_prefix('dest:', get_text_encoded_for_print(dest))
	print_with_colored_prefix('etc:', get_text_encoded_for_print(' '.join(rest)))
	print('')

	if '_' in flags:
		SW_MINIMIZE = 6
		minimized = subprocess.STARTUPINFO()
		minimized.dwFlags = subprocess.STARTF_USESHOWWINDOW
		minimized.wShowWindow = SW_MINIMIZE
	else:
		minimized = None

	is_subj_list = (subj[0] == '@')
	foreach_date = flags.count('9')
	foreach_dir  = '4' in flags
	foreach_file = 'f' in flags
	foreach = (foreach_dir or foreach_file) and not is_subj_list
	foreach_ID = ''.join(map(lambda x: x if x in flags else '', flags_group_by_num_any_sep))

	exe_paths = get_exe_paths()

	cmd_template = {}
	cmd_template['7z'] = (
		[exe_paths['7z'], 'a', '-stl', '-ssw', '-mqs']
	+	(
			['-mx0', '-mmt=off'] if '0' in flags else
			['-mx9', '-mmt=2'] + (
				['-md=256m', '-mfb=256'] if '6' in flags else
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
		[exe_paths['rar'], 'a', '-tl', '-dh', '-ma5', '-qo+']
	+	(
			['-m0', '-mt1'] if '0' in flags else
			['-m5', '-mt4'] + (
				['-md256m'] if '6' in flags else
				[]
			)
		)
	+	(
			['-oi:0'] if 'l' in flags else
			['-oi-']
		)
	+	(
			['-ibck'] if minimized else
			[]
		)
	+	rest_winrar
	)

	cmd_queue = []
	del_warn = 0
	time_format = ';_%Y-%m-%d,%H-%M-%S' if ';' in flags else '_%Y-%m-%d_%H-%M-%S'
	t0 = time.strftime(time_format)

# - Fill batch queue ----------------------------------------------------------

	if foreach or foreach_ID:
		names = list(map(
			normalize_slashes
		,	glob.glob(subj) if ('*' in subj or '?' in subj) else
			os.listdir(subj) if os.path.isdir(subj) else
			[subj]
		))

		if foreach_ID:
			dots = ''
			d = '.,'
			for i in d:
				if i in foreach_ID:
					dots += i
			d = '\d' + dots
			pat_ID = re.compile(r'^(\D*\d[' + d + ']*)([^' + d + ']|$)' if dots else r'^(\D*\d+)(\D|$)')

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
					name = dest + '/' + i + '_list.txt'
					names.append('@' + name)
					if not 'c' in flags:
						f = open(name, 'wb')
						r = f.write('\n'.join(d[i]))
						f.close()
			else:
				d = []
				for subj in names:
					s = re.search(pat_ID, subj)
					if s:
						n = s.group(1) + '*'
						if not (n in d):
							d.append(n)
					else:
						d.append(subj)
				names = d

		for subj in names:
			if foreach_dir != foreach_file and foreach_dir != os.path.isdir(subj):
				continue

			del_warn += queue(cmd_queue, dest, subj, foreach=True)
	else:
		del_warn += queue(cmd_queue, dest, subj)

	cmd_count = len(cmd_queue)

	if cmd_count > 0:
		print('')
	else:
		cprint('----	----	Nothing to do, command queue is empty.', 'cyan')

		return 11

	if del_warn:
		cprint('----	----	WARNING, only WinRAR or 7-zip v17+ can delete files!', 'yellow')
		print('')

	error_count = 0

# - Do the job ----------------------------------------------------------------

	for cmd in cmd_queue:
		cmd_args = list(filter(bool, cmd['args']))
		cmd_dest = cmd['dest']
		cmd_type = cmd['exe_type']
		cmd_suffix = cmd['suffix']

		print(cmd_args_to_text(cmd_args))

		if not 'c' in flags:
			result_code = subprocess.call(cmd_args, startupinfo=minimized)

			if result_code:
				error_count += 1

			if os.path.exists(cmd_dest):
				c = cmd_suffix if ((def_suffix_separator in flags) and cmd_suffix) else '.'
				d = cmd_dest
				j = (
					datetime.datetime.fromtimestamp(os.path.getmtime(d)).strftime(time_format)
					if 'm' in flags
					else ''
				) + def_suffix + c

				if j != c:
					d = j.join(d.rsplit(c, 1))
					while os.path.exists(d):
						d = '(2).'.join(d.rsplit('.', 1))

					print(cmd_dest)
					print(d)

					os.rename(cmd_dest, d)

			codes_of_type = exit_codes[cmd_type]
			result_text = codes_of_type[result_code] if result_code in codes_of_type else 'Unknown code'

			cprint(
				'{}: {}'.format(result_code, result_text)
			,	'red' if result_code != 0 else 'cyan'
			)

			print('')

# - Result summary ------------------------------------------------------------

	if 'c' in flags:
		print('')

	if error_count > 0:
		if 'k' in flags:
			print(' '.join([
				colored('----	----	Done {} archives,'.format(cmd_count), 'green')
			,	colored('{} errors.'.format(error_count), 'red')
			,	'See messages above.'
			]))
		else:
			print(' '.join([
				colored('----	----	Done {} archives,'.format(cmd_count), 'green')
			,	colored('{} errors.'.format(error_count), 'red')
			,	'Press Enter to continue.'
			]))

			if sys.version_info.major == 2:
				raw_input()
			else:
				input()
	elif 'c' in flags:
		cprint('----	----	Total {} commands.'.format(cmd_count), 'green')
	else:
		cprint('----	----	Done {} archives.'.format(cmd_count), 'green')

	return 0 if error_count == 0 and cmd_count > 0 else -1

# - Run from commandline, when not imported as module -------------------------

if __name__ == '__main__':
	sys.exit(run_batch_archiving(sys.argv[1 : ]))

# - End -----------------------------------------------------------------------
