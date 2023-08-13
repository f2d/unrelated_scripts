#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Python 2 or 3 should work.

# [v] TODO: better keeping of unique filenames and parts - prefix, suffix, params, dates, etc.
# [v] 1. Start creation with unique filename to avoid race conditions with simultaneous script runs writing to a same archive file.
# [v] -- Use script process ID = os.getpid() + script starting timestamp + each archive creation timestamp.
# [v] 2. Rename after finishing to a more clean and sensible unique name.
# [ ] -- Sort name parts by type in predefined order.

# TODO: more robust preparation of command line.
# 1. Append args to lists separated by type (compression, sources, destination, etc).
# 2. Arrange args sorted as needed by each archiving program, to avoid failures (e.g. 7-Zip cannot find filelist after -- with @..\name_list.txt).

# TODO: keep archives by subject AND result file sum/list, instead of only subject, to avoid lost files if different program choose differently.
# Or abort the queue before deleting new/old archive, when some subject gives different archived result by different program.

import datetime, glob, io, os, re, subprocess, sys, time

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
	wait_user_input = input
else:
	wait_user_input = raw_input

# - Configuration and defaults ------------------------------------------------

process_id_text = str(os.getpid())
print_encoding = sys.stdout.encoding or sys.getfilesystemencoding() or 'utf-8'
listfile_encoding = 'utf-8'

sort_queue_by_subj = True

empty_archive_max_size = 99	# <- sanity check to delete if any less

esplit_glue_method = 'LZMA:x9:d1m:lc8:lp0:pb0'

zstd_levels = [3, 17, 18, 19, 20, 21, 22]
zstd_levels_max_index = len(zstd_levels) - 1
zstd_flag = '9'

group_flag = '1'
group_listfile_flag = '2'
group_flags_shortcut = '3'
group_sep_dot_flag = '.'
group_sep_comma_flag = ','

group_by_num_dot_flags = (
	group_flag
+	group_listfile_flag
+	group_sep_dot_flag
)

group_by_num_any_sep_flags = (
	group_by_num_dot_flags
+	group_sep_comma_flag
)

for_each_dir_flag = '4'
for_each_file_flag = 'F'

make_7z_flag = '7'
make_rar_flag = 'R'
make_zip_by_7z_flag = 'Z'
make_zip_by_rar_flag = 'W'

make_non_solid_flag = 'N'
make_solid_by_ext_flag = 'E'
make_solid_flag = 'S'
uncompressed_flag = '0'

mega_size_flag = '6'
giga_size_flag = 'G'
esplit_flag = 'P'
dedup_flag = 'L'

add_mod_time_flag = 'M'
add_start_time_flag = 'T'
alt_time_format_flag = ';'

delete_sources_flag = 'D'
keep_smallest_archive_flag = 'O'
no_waiting_keypress_flag = 'K'
only_list_commands_flag = 'C'
minimized_flag = '_'

make_all_solid_flags = (
	make_7z_flag
+	make_rar_flag
+	make_solid_by_ext_flag
+	make_solid_flag
)

make_all_types_flags = (
	make_all_solid_flags
+	make_non_solid_flag
+	make_zip_by_rar_flag
+	make_zip_by_7z_flag
)

make_all_solid_flags_shortcut = 'A'
make_all_types_flags_shortcut = '8'

def_name_fallback = 'default'
def_name_separator = '='
def_suffix_separator = '>'
def_subj = '.'
def_dest = '..'

dest_name_replacements = ['"\'', '?', ':;', '/,', '\\,', '|,', '<', '>', '*']

split_flag_combo = '|'
must_quote_chars = ' ,;<>=&|'

pat_inex = re.compile(r'^(?P<InEx>-[ix])(?P<Recurse>r[0-]*)?(?P<Value>[!@].*)$', re.I)
pat_line_break = re.compile(r'(\r\n|\r|\n)+')
pat_suffix_solid = re.compile(r',s(e|=\w+)?\b')
pat_temp = re.compile(r'([^\w.-]|_)+', re.S)
pat_whitespace = re.compile(r'\s+', re.S)

exit_codes = {

# Source: http://sevenzip.sourceforge.jp/chm/cmdline/exit_codes.htm

	'7z': {
		0: 'No error'
	,	1: 'Warning (Non fatal error(s)). For example, one or more files were locked by some other application, so they were not compressed.'
	,	2: 'Fatal error'
	,	7: 'Command line error'
	,	8: 'Not enough memory for operation'
	,	255: 'User stopped the process'
	}

# Source: http://en.helpdoc-online.com/winrar_4/source/html/helpexitcodes.htm

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

# - Utility functions ---------------------------------------------------------

# Nested loop breaker:
# Source: https://stackoverflow.com/a/189664
class GetOutOfLoop( Exception ):
	pass

def trim_text(content):
	try:	return content.strip(' \t\r\n')
	except:	return content

def bytes_to_text(content, encoding=print_encoding, trim=False):

	try:	content = content.decode(encoding or print_encoding)
	except:	pass

	# https://stackoverflow.com/a/37557962
	try:	content = unicode(content, encoding='ascii', errors='ignore')
	except:	pass

	return trim_text(content) if trim else content

def normalize_line_breaks(text):
	return re.sub(pat_line_break, '\n', text)

def normalize_slashes(path):
	return path.replace('\\', '/')

def fix_slashes(path):
	if os.sep != '/':
		path = path.replace('/', os.sep)

	if os.sep != '\\':
		path = path.replace('\\', os.sep)

	return path

def get_exe_paths():

	exe_try_root_dirs = [
		'%ProgramW6432%'
	,	'%ProgramFiles%'
	,	'%ProgramFiles(x86)%'
	,	'%CommonProgramFiles%'
	,	'C:/Program Files'
	,	'C:/Programs'
	,	'D:/Program Files'
	,	'D:/Programs'
	,	''
	]

	exe_try_subdir_suffixes = [
		'-x64'
	,	'_x64'
	,	' x64'
	,	'x64'
	,	'_(x64)'
	,	' (x64)'
	,	'(x64)'
	,	''
	]

	subdirs_rar = ['WinRAR']
	subdirs_7z = [
		'7-Zip-ZS'
	,	'7-Zip_ZS'
	,	'7-Zip ZS'
	,	'7_Zip_ZS'
	,	'7zip-ZS'
	,	'7zip_ZS'
	,	'7zip ZS'
	,	'7zipZS'
	,	'7-Zip'
	,	'7zip'
	]

	exe_try_types = {
		'7z'      : { 'subdirs': subdirs_7z, 'filenames': ['7zG'] }
	,	'7z_cmd'  : { 'subdirs': subdirs_7z, 'filenames': ['7z'] }
	,	'rar'     : { 'subdirs': subdirs_rar, 'filenames': ['WinRAR'] }
	,	'rar_cmd' : { 'subdirs': subdirs_rar, 'filenames': ['Rar'] }
	}

	exe_try_filename_suffixes = ['.exe', '']
	exe_paths_found = {}

	for type_name, type_part in exe_try_types.items():
		try:
			for root_dir in exe_try_root_dirs:
				env_dir = root_dir.strip('%')

				if env_dir != root_dir:
					env_dir = os.environ.get(env_dir)

					if env_dir:
						root_dir = env_dir

				for subdir in type_part['subdirs']:
					for subdir_suffix in exe_try_subdir_suffixes:
						for filename in type_part['filenames']:
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

def get_text_without_chars(text, chars):
	for c in chars:
		text = text.replace(c, '')

	return text

# Format string with spaces as thousand separator:
# Source: https://stackoverflow.com/a/18891054
def get_bytes_text(bytes_num, add_text=True):
	return ('{:,} bytes' if add_text else '{:,}').format(bytes_num).replace(',', ' ')

def get_text_encoded_for_print(text):
	return text.encode(print_encoding) if sys.version_info.major == 2 else text

def print_with_colored_prefix(prefix, value, color=None):
	print('{} {}'.format(colored(prefix, color or 'yellow'), value))

def print_help():
	self_name = os.path.basename(__file__)
	exe_paths = get_exe_paths()

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
	,	'	In shell, add "quotes" around arguments,'
	,	'	that contain any of the following symbols: "' + must_quote_chars + '",'
	,	'	or quote/escape anything beyond latin letters and digits just in case.'
	,	''
	,	colored('* Current executable paths to be used (found or fallback):', 'yellow')
	] + sorted([
		'	{}	: {}'.format(k, v) for k, v in exe_paths.items()
	]) + [
		''
	,	colored('* Flags (switch letters, concatenate in any order, any letter case):', 'yellow')
	,	''
	,	'	---- Archive types:'
	,	''
	,	'	{make_7z}: make a .7z  file with 7-Zip.'
	,	'	{make_zip_by_7z}: make a .zip file with 7-Zip.'
	,	'	{make_zip_by_rar}: make a .zip file with WinRAR.'
	,	'	{make_rar}: make a .rar file with WinRAR.'
	,	'	{solid}: make solid archives.'
	,	'	{by_ext}: make archives with solid blocks grouped by filename extension.'
	,	'	{non_solid}: make non-solid archives (implied unless "{solid}" or "{by_ext}" is given).'
	,	'	{solid_shortcut}: make a set of solid variants (shortcut, equivalent to "' + make_all_solid_flags + '").'
	,	'	{all_shortcut}: make all types currently supported (shortcut, equivalent to "' + make_all_types_flags + '").'
	,	''
	,	'	---- Archive filenames:'
	,	''
	,	'	{start_time}: add "_YYYY-mm-dd_HH-MM-SS" script start time to all filenames.'
	,	'	{mod_time}: add each archive\'s last-modified time to its filename.'
	,	'	{time_format}: timestamp fotmat = ";_YYYY-mm-dd,HH-MM-SS".'
	,	'	{suffix_sep}: put timestamp before any suffix, after base filename.'
	,	''
	,	'	{name_sep}filename{suffix_sep}suffix:'
	,	'		Add given suffix between timestamp and archive type.'
	,	'		",=suffix" is autoreplaced to ",[suffix]", for usage with arch_sub.bat'
	,	''
	,	'	---- Compression parameters:'
	,	''
	,	'	{store}: no compression (store file content as is).'
	,	'	{mega}: big data compression settings (256 MB dictionary, 256 B word size).'
	,	'	{giga}: very big compression settings (1 GB dictionary, 273 B word size).'
	,	''
	,	'	{zstd_min}, up to {zstd_max}:'
	,	'		Use Zstandard compression method.'
	,	'		Only supported by 7-Zip custom builds or plugins.'
	,	'		Repeat the flag for slower and higher levels ({zstd_min}={zstd_min_level}, {zstd_max}={zstd_max_level}).'
	,	'		Much faster than LZMA/LZMA2 at both compression and decompression, at least up to level 20.'
	,	'		In some rare cases Zstd level 17 archive is smaller than level 20, and 2+ times faster in all cases.'
	,	'		In some rare cases Zstd level 20 archive is smaller than LZMA2 level 9.'
	,	'		"{mega}" and "{giga}" flags without "{by_ext}" set solid block size for Zstd, instead of dictionary size.'
	,	''
	,	'	{zstd_min}{store}:'
		+	'	Use Zstandard level {zstd_store_level}.'
	,	'		Fast alternative to uncompressed 7z format.'
	,	''
	,	'	{esplit}:'
		+	'	Use eSplitter for MHTML files.'
	,	'		Compress base64-decoded binary data separately from text.'
	,	'		Only supported by 7-Zip, in 7z format, and requires eSplitter plugin.'
	,	'		Repeat the flag to use different methods:'
	,	'			Default (single "{esplit}") = use the same main method for all data.'
	,	'			Even count ("'
		+ (esplit_flag * 2) + '", "'
		+ (esplit_flag * 4) + '", etc) = use "'
		+ esplit_glue_method + '" for glue data, faster, sometimes smaller.'
	,	'			Every 3-4 of 4 ("'
		+ (esplit_flag * 3) + '", '
		+ (esplit_flag * 4) + '", x7, x8, etc) = use PPMD for text files data, slower, "{mega}" and "{giga}" flags set mem size.'
	,	'		More info: https://www.tc4shell.com/en/7zip/edecoder/'
	,	'		Discussion: https://sourceforge.net/p/sevenzip/discussion/45797/thread/8df7e14e/'
	,	''
	,	'	{dedup}:'
		+	'	Store identical files as links to one copy of archived content.'
	,	'		Limits storage redundancy and archive editing.'
	,	'		Only supported by WinRAR since v5.'
	,	'		7-Zip may show file errors when testing or unpacking such archives.'
	,	''
	,	'	---- Group subjects into separate archives:'
	,	''
	,	'		Each name is appended with comma to "{name_sep}filename" from arguments.'
	,	''
	,	'	{group_by_name}:'
		+	'	Make separate archives for each group of subjects'
	,	'		by first found numeric ID in subject name.'
	,	'		(name1part2 -> name1*, "{name_sep}filename,name1")'
	,	''
	,	'	{group_lists}:'
		+	'	Same as "{group_by_name}" but create filelist files (in destination folder)'
	,	'		to separate ambiguous cases, like when "name1*" mask'
	,	'		would undesirably capture "name1a" and "name12" files.'
	,	''
	,	'	{group_by_name}{group_lists}:'
		+	'	Same as "{group_lists}" but files without ID go to one list, not separate.'
	,	''
	,	'	{group_dot} and/or {group_comma}:'
	,	'		Same as "{group_by_name}" or "{group_lists}" but ID may contain dots and/or commas.'
	,	'		"{group_by_name}" is implied unless "{group_lists}" is given.'
	,	''
	,	'	{group_shortcut}: shortcut, equivalent to "' + group_by_num_dot_flags + '".'
	,	'	{foreach_dir}: make separate archives for each dir of subject mask.'
	,	'	{foreach_file}: make separate archives for each file of subject mask.'
	,	'		Use one of "{foreach_dir}" or "{foreach_file}" with any of "' + group_by_num_any_sep_flags + '"'
	,	'		to add only dirs or files to the groups.'
#	,	'TODO ->	5 and/or g: make separate archives for each group of subjects'
#	,	'TODO ->		by longest common subject name parts.'
#	,	'TODO ->		5: name part break can include alphanumerics, etc.'
#	,	'TODO ->		g: name part break only by punctuation or spaces.'
#	,	'TODO ->		g5: start comparing from longest filenames.'
#	,	'TODO ->		5g: start comparing from shortest filenames.'
#	,	'TODO ->		if "4" or "f" is not set, skip singletons.'
#	,	'TODO ->		("45fg" are cross-compatible, but disabled with any of "'+group_by_num_any_sep_flags+'").'
#	,	'TODO ->	9, 99, 999, etc.: keep each group population below this number.'
#	,	'TODO ->		(split first by mod.dates - years, then months, days, hours,'
#	,	'TODO ->		minutes, seconds, at last batch subjects with same-second'
#	,	'TODO ->		timestamps alphabetically in simple N+1 groups - 10, 100, etc.)'
	,	''
	,	'	---- Clean up:'
	,	''
	,	'	{keep_1}: keep only the smallest archive for each subject, delete other archives on the go.'
	,	'	{delete_src}: delete subjects (source files and dirs) when done.'
	,	'		Only supported by WinRAR, or 7-Zip since v17.'
	,	'		WinRAR will test its archives before deleting subjects.'
	,	''
	,	'		Warning: using "{delete_src}" with "{keep_1}" is NOT safe, because'
	,	'		in complicated cases with masks, list files or additional include/exclude arguments,'
	,	'		different programs may choose different subject files, which'
	,	'		may not coincide between the archive made by the last program to do subject clean up'
	,	'		and the archive selected as the smallest to be kept,'
	,	'		possibly resulting in some files lost completely.'
	,	''
	,	'	---- Other:'
	,	''
	,	'	{list_cmd}: check resulting command lines without running them.'
	,	'	{no_key_press}: don\'t wait for key press after errors.'
	,	'	{minimized}: start all processes minimized.'
	,	''
	,	'	{split}:'
		+	'	Split flags before filename suffix, make combinations with common last part.'
	,	'		("part_1{split}part_2{split}_last" -> "part_1_last" + "part_2_last")'
	,	'		Any flags unrelated to archive types and compression methods apply to all combinations.'
	,	'		Flag "{delete_src}" (delete files) in any part is automatically moved to the last combination.'
	,	'		Using WinRAR in the last part is recommended, because it will test the archive before deleting anything.'
	,	''
	,	colored('* Examples:', 'yellow')
	,	'	{0}'
		+	colored(' {solid_shortcut}', 'cyan')
	,	'	(default subj = current folder, destination = 1 folder up)'
	,	''
	,	'	{0}'
		+	colored(' {solid_shortcut}', 'cyan')
		+	colored(' "*some*thing*"', 'magenta')
	,	'	(default destination = 1 up, so wildcard won\'t grab result archives)'
	,	''
	,	'	{0}'
		+	colored(' {solid_shortcut}', 'cyan')
		+	colored(' "subfolder/file"', 'magenta')
	,	'	(default destination = here, safe because no wildcard)'
	,	''
	,	'	{0}'
		+	colored(' "{list_cmd}{time_format}{group_shortcut}{delete_src}{solid_shortcut}{start_time}{keep_1}"', 'cyan')
		+	colored(' "c:/subfolder/*.txt" "d:/dest/folder" "-x!readme.txt"', 'magenta')
	,	''
	,	'	{0}'
		+	colored(' "{list_cmd}' + '{split}'.join([
				'{zstd_min}{make_7z}'
			,	'{store}{zstd_min}{all_shortcut}'
			,	'{solid_shortcut}'
			,	'{minimized}{mod_time}{keep_1}{delete_src}'
			]) + '{name_sep}dest_filename"', 'cyan')
		+	colored(' "@path/to/subj_listfile" "../../dest/folder"', 'magenta')
	]

	print('\n'.join(help_text_lines).format(

		self_name

	,	make_7z = make_7z_flag
	,	make_rar = make_rar_flag
	,	make_zip_by_7z = make_zip_by_7z_flag
	,	make_zip_by_rar = make_zip_by_rar_flag
	,	solid_shortcut = make_all_solid_flags_shortcut
	,	all_shortcut = make_all_types_flags_shortcut

	,	zstd_min = zstd_flag
	,	zstd_max = zstd_flag * zstd_levels_max_index
	,	zstd_store_level = zstd_levels[0]
	,	zstd_min_level = zstd_levels[1]
	,	zstd_max_level = zstd_levels[zstd_levels_max_index]

	,	by_ext = make_solid_by_ext_flag
	,	non_solid = make_non_solid_flag
	,	solid = make_solid_flag
	,	store = uncompressed_flag

	,	dedup = dedup_flag
	,	esplit = esplit_flag
	,	giga = giga_size_flag
	,	mega = mega_size_flag

	,	foreach_dir = for_each_dir_flag
	,	foreach_file = for_each_file_flag

	,	group_by_name = group_flag
	,	group_comma = group_sep_comma_flag
	,	group_dot = group_sep_dot_flag
	,	group_lists = group_listfile_flag
	,	group_shortcut = group_flags_shortcut

	,	delete_src = delete_sources_flag
	,	keep_1 = keep_smallest_archive_flag
	,	list_cmd = only_list_commands_flag
	,	minimized = minimized_flag
	,	no_key_press = no_waiting_keypress_flag

	,	mod_time = add_mod_time_flag
	,	start_time = add_start_time_flag
	,	time_format = alt_time_format_flag

	,	name_sep = def_name_separator
	,	suffix_sep = def_suffix_separator

	,	split = split_flag_combo

	))

def remove_trailing_dots_in_path_parts(path):
	return '/'.join(
		part if part == '.' or part == '..'
		else part.rstrip('.')
		for part in normalize_slashes(path).split('/')
	)

def get_unique_clean_path(path_part_before, path_part_after='', timestamp=None):
	full_path = remove_trailing_dots_in_path_parts(path_part_before + path_part_after)

	if timestamp and os.path.exists(full_path):
		full_path = remove_trailing_dots_in_path_parts(path_part_before + timestamp + path_part_after)

	if os.path.exists(full_path):
		try_count = 1
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

def split_text_in_two(text, separator):
	return pad_list((text or '').split(separator, 1))

def get_7z_method_args(flags):

	if esplit_flag in flags:

		flag_count = flags.count(esplit_flag) - 1

# https://www.tc4shell.com/en/7zip/edecoder/
# Example: 0=eSplitter 1=PPMD:x9:mem1g:o32 2=LZMA2:x9:d128m:mt1 3=LZMA:x9:d1m:lc8:lp0:pb0 b0s0:1 b0s1:2 b0s2:3

		main_compression_method = (
			'ZSTD:x{}:mt4'.format(pick_zstd_level_from_flags(flags)) if zstd_flag in flags else
			'Copy' if uncompressed_flag in flags else
			'LZMA{version}:x9:mt{threads}:d{dict}:fb{word}'.format(
				version=pick_lzma_version_from_flags(flags)
			,	threads=pick_lzma_threads_from_flags(flags)
			,	dict=pick_lzma_dict_size_from_flags(flags)
			,	word=pick_lzma_word_size_from_flags(flags)
			)
		)

		text_compression_method = (
			'PPMD:x9:mem{}:o32'.format(pick_lzma_dict_size_from_flags(flags)) if flag_count & 2 else
			main_compression_method
		)

		glue_compression_method = (
			esplit_glue_method if flag_count & 1 else
			main_compression_method
		)

		return [
			'-m0=eSplitter'
		,	'-m1={}'.format(text_compression_method)
		,	'-m2={}'.format(main_compression_method)
		,	'-m3={}'.format(glue_compression_method)
		,	'-mb0s0:1'
		,	'-mb0s1:2'
		,	'-mb0s2:3'
		,	'-mmt=on'
		]
	else:
		return [
			'-m0=zstd'
		,	'-mx={}'.format(pick_zstd_level_from_flags(flags))
		,	'-mmt=on'
		] if zstd_flag in flags else [
			'-m0=lzma2'
		,	'-mx=9'
		,	'-mmt=2'
		,	'-md={}'.format(pick_lzma_dict_size_from_flags(flags))
		,	'-mfb={}'.format(pick_lzma_word_size_from_flags(flags))
		]

def pick_lzma_version_from_flags(flags):
	return (
		# 1 if giga_size_flag in flags else	# <- result was larger in practice.
		2
	)

def pick_lzma_threads_from_flags(flags):
	return (
		1 if giga_size_flag in flags else
		2
	)

def pick_lzma_word_size_from_flags(flags):
	return (
		'256' if mega_size_flag in flags else
		'273'
	)

def pick_lzma_dict_size_from_flags(flags):
	return (
		'1g'   if giga_size_flag in flags else
		'256m' if mega_size_flag in flags else
		'64m'
	)

def pick_zstd_solid_block_size_from_flags(flags):
	return (
		'1g'   if giga_size_flag in flags else
		'256m' if mega_size_flag in flags else
		'99m'
	)

def pick_zstd_level_from_flags(flags):

	flag_count = flags.count(zstd_flag)

	return zstd_levels[
		0 if uncompressed_flag in flags else
		zstd_levels_max_index if zstd_levels_max_index < flag_count else
		flag_count
	]

# - Main job function ---------------------------------------------------------

def run_batch_archiving(argv):

	def queue_batch_part(argv_flag):

		def queue(dest, subj, foreach_dir_or_file=False):

			def append_cmd(paths, suffix, opt_args=None):
				subj, dest = paths
				rar = suffix.find('rar') > suffix.find('7z')
				exe_type = 'rar' if rar else '7z'
				cmd_args = cmd_template[exe_type] + (opt_args or [])

				if suffix.find('.zip') >= 0:

					skip_args = [
						'-mqs'
					,	'-md='
					,	'-ms='
					,	'-m0='
					,	'-m1='
					,	'-m2='
					,	'-m3='
					,	'-mb0'
					]

					cmd_args = [
						(
							None if arg[0 : 4] in skip_args
						else	('-mx=0' if uncompressed_flag in flags else '-mx=9') if arg[0 : 4] == '-mx='
						else	(None if uncompressed_flag in flags else '-mfb=256') if arg[0 : 5] == '-mfb='
						else	arg
						)
						for arg in cmd_args
					]

				elif suffix.find('.7z') and '-ms=e' in cmd_args:
					cmd_args = [
						(
							None if arg[0 : 4] == '-mqs'
						else	arg
						)
						for arg in cmd_args
					] + ['-mqs']

				# dest = get_unique_clean_path(dest, suffix, t0)
				dest = remove_trailing_dots_in_path_parts(dest + suffix)
				dest_dir, dest_name = dest.rsplit('/', 1)
				dest_temp = dest_dir + '/' + re.sub(pat_temp, '_', '_'.join([
					t0
				,	process_id_text
				,	'tmp'
				# ,	dest_name
				# ,	str(len(dest_name))
				,	suffix.replace('=', '')
				])).strip('_')

				path_args = (
					[
						(
							'-n' if rar else
							'-ir' if '-r' in cmd_args else
							'-i'
						) + subj
					,	'--'
					,	dest_temp
					]
					if is_subj_list else
					['--', dest_temp, subj]
				)

				cmd = {
					'args': cmd_args + path_args
				,	'exe_type': exe_type
				,	'flags': flags

				,	'def_suffix': def_suffix
				,	'suffix': (suffix.rsplit('.', 1)[0] + '.') if ',' in suffix else '.'

				,	'dest': dest
				,	'dest_dir': dest_dir
				,	'dest_name': dest_name
				,	'dest_temp': dest_temp
				,	'subj': subj
				}

				if sort_queue_by_subj:
					if not cmd_queue_by_subj.get(subj):
						cmd_queue_by_subj[subj] = []

					cmd_queue_by_subj[subj].append(cmd)

				cmd_queue.append(cmd)

				return 1

			name = (def_name + ',' + subj) if (foreach_dir_or_file and def_name and subj) else (def_name or subj)

			is_subj_mask = ('*' in subj) or ('?' in subj)
			is_subj_mass = is_subj_mask or is_subj_list or os.path.isdir(subj)

			if len(get_text_without_chars(name, '.')) > 0:
				if '/' in name:
					name = name.rsplit('/', 1)[1]

				# re-guess dest arg when not given:
				if (
					(
						not argv_dest
					or	not len(argv_dest) > 0
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

			dest_name = dest + '/' + name + (t0 if add_start_time else '')
			paths = list(map(fix_slashes, [subj, dest_name]))

			dest_name_part_dedup		= ',dedup' if dedup_flag in flags else ''
			dest_name_part_esplit		= ',eSplit' if esplit_flag in flags else ''
			dest_name_part_uncompressed	= ',store' if uncompressed_flag in flags else ''
			dest_name_part_dict_size	= ',d=1g' if giga_size_flag in flags else ',d=256m' if mega_size_flag in flags else ''
			dest_name_part_zstd		= ',zstd={}'.format(pick_zstd_level_from_flags(flags)) if zstd_flag in flags else ''

			if make_7z_flag in flags:
				ext = dest_name_part_esplit + (
					dest_name_part_zstd
				or	dest_name_part_uncompressed
				or	dest_name_part_dict_size
				) + '.7z'

				solid = 0
				solid_block_size = '={}'.format(pick_zstd_solid_block_size_from_flags(flags)) if zstd_flag in flags else ''

				if is_subj_mass and (dest_name_part_zstd or not dest_name_part_uncompressed):
					if make_solid_by_ext_flag in flags: solid += append_cmd(paths, ',se' + ext, ['-ms=e'])
					if make_solid_flag        in flags: solid += append_cmd(paths
					,	',s' + solid_block_size + ext
					,	['-ms' + solid_block_size]
					)

				if not solid or (make_non_solid_flag in flags): append_cmd(paths, ext, ['-ms=off'])

			ext = dest_name_part_uncompressed + '.zip'

			if make_zip_by_7z_flag  in flags: append_cmd(paths, ',7z' + ext)
			if make_zip_by_rar_flag in flags: append_cmd(paths, ',winrar' + ext)

			if make_rar_flag in flags:
				ext = (
					dest_name_part_uncompressed
				or	dest_name_part_dict_size
				) + dest_name_part_dedup + '.rar'

				solid = 0

				if is_subj_mass and not dest_name_part_uncompressed:
					if make_solid_by_ext_flag in flags: solid += append_cmd(paths, ',se' + ext, ['-se'])
					if make_solid_flag        in flags: solid += append_cmd(paths, ',s' + ext, ['-s'])

				if not solid or (make_non_solid_flag in flags): append_cmd(paths, ext, ['-s-'])

			del_warn = 0

			# delete subj files, only for last queued cmd per subj:
			if delete_sources_flag in flags:
				da = (
					['-df', '-y', '-t'] if (make_rar_flag in flags) or (make_zip_by_rar_flag in flags) else
					['-sdel', '-y'    ] if (make_7z_flag  in flags) or (make_zip_by_7z_flag  in flags) else
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

# - Calculate params ----------------------------------------------------------

		flags, def_name = split_text_in_two(argv_flag.strip('"'), def_name_separator)

		flags = (
			flags
			.upper()
			.replace(make_all_types_flags_shortcut, make_all_types_flags)
			.replace(make_all_solid_flags_shortcut, make_all_solid_flags)
			.replace(group_flags_shortcut, group_by_num_dot_flags)
		)

		if (def_suffix_separator in def_name) and not (def_suffix_separator in flags):
			flags += def_suffix_separator

		def_name, def_suffix = split_text_in_two(def_name, def_suffix_separator)

		if def_suffix[0 : 2] == ',=':
			def_suffix = ',[' + def_suffix.strip(',=_[]') + ']'

		print_with_colored_prefix('flags:', get_text_encoded_for_print(flags.lower()))
		print_with_colored_prefix('suffix:', get_text_encoded_for_print(def_suffix))

		cmd_template = {}
		cmd_template['7z'] = (
			[
				exe_paths['7z']
			,	'a'
			# ,	'-bt'	# <- Show execution time statistics, only for 'b' command.
			# ,	'-slt'	# <- Show technical information, only for 'l' command.
			# ,	'-sns'	# <- Currently 7-Zip can store NTFS alternate streams only to WIM archives.
			,	'-ssw'	# <- Compress files open for writing.
			,	'-stl'	# <- Set archive timestamp from the most recently modified file.
			,	(
					'-mqs-' if esplit_flag in flags else	# <- Sort files by full name, all supposed to be MHT type.
					'-mqs'				# <- Sort files by type (name extension) in solid archives.
				)
			]
		+	(		# Compression method, number of threads, dictionary size:
				['-mx=0', '-mmt=off'] if uncompressed_flag in flags and not (zstd_flag in flags or esplit_flag in flags) else
				get_7z_method_args(flags)
			)
		+	rest
		)

		rest_winrar = []

		for arg in rest:
			res = re.search(pat_inex, arg)
			if res:
				inex = res.group('InEx')
				rest_winrar.append(
					(inex if inex == '-x' else '-n')
				+	res.group('Value')
				)

				r = res.group('Recurse')
				if r:
					rest_winrar.append('-' + r)
			else:
				rest_winrar.append(arg)

		if not (
			foreach_dir_or_file
		or	'-r' in rest_winrar
		or	'-r-' in rest_winrar
		or	'-r0' in rest_winrar
		):
			rest_winrar.append('-r0')

		cmd_template['rar'] = (
			[
				exe_paths['rar']
			,	'a'
			,	'-dh'	# <- Open shared files.
			,	'-ma5'	# <- Version of archiving format.
			,	'-qo+'	# <- Add quick open information.
			,	'-tl'	# <- Set archive time to newest file.
			,	(
					'-ibck' if minimized else	# <- Run WinRAR in background.
					None
				), (
					'-oi:0' if dedup_flag in flags else	# <- Save identical files as references.
					'-oi-'
				)
			]
		+	(		# Compression method, number of threads, dictionary size:
				['-m0', '-mt1'] if uncompressed_flag in flags else
				['-m5', '-mt4',
					(
						'-md1g' if giga_size_flag in flags else
						'-md256m' if mega_size_flag in flags else
						None
					)
				]
			)
		+	rest_winrar
		)

# - Fill batch queue ----------------------------------------------------------

		del_warn = 0

		if foreach_subj_names:
			for each_subj in foreach_subj_names:
				del_warn += queue(dest, each_subj, foreach_dir_or_file=True)
		else:
			del_warn += queue(dest, subj)

		return del_warn

	def get_archive_file_summary(file_path, archive_params_dict=None):

		test_result_code = subprocess.call(
			[
				exe_paths[
					'rar_cmd' if (
						archive_params_dict
					and	dedup_flag in archive_params_dict['flags']
					and	file_path.rsplit('.', 1)[1] == 'rar'
					) else '7z_cmd'
				]
			,	't'
			,	file_path
			]
		,	startupinfo=minimized
		)

		if test_result_code:
			return ''

		listing_output = subprocess.check_output(
			[
				exe_paths['7z_cmd']
			,	'l'
			,	file_path
			]
		,	startupinfo=minimized
		)

		output_text = bytes_to_text(listing_output, trim=True)
		output_lines = normalize_line_breaks(output_text).split('\n')
		output_lines = list(filter(bool, map(trim_text, output_lines)))

		if archive_params_dict:
			old_suffix = archive_params_dict.get('suffix')

			if old_suffix:
				old_match = re.search(pat_suffix_solid, old_suffix)

				if old_match:
					suffix_solid_params = old_match.group(1)
					archive_params_found = is_archive_solid = is_single_solid_block = False

					for line in output_lines:
						if archive_params_found:
							if line[0] == '-':
								break

							elif line == 'Solid = +':
								is_archive_solid = True

							elif line == 'Blocks = 1':
								is_single_solid_block = True

						elif line == '--':
							archive_params_found = True

					if is_single_solid_block and not (
						is_archive_solid
					and	(
							not suffix_solid_params
						# or	suffix_solid_params == 'e'
						)
					):
						archive_params_dict['suffix'] = re.sub(
							pat_suffix_solid
						,	',s' if is_archive_solid else ''
						,	old_suffix
						)

		return output_lines[-1 : ][0]

	def run_cmd(cmd):

		print('')

		cmd_subj = cmd['subj']

		if no_files_by_subj.get(cmd_subj):
			print_with_colored_prefix('No files to archive for this subject, skip:', cmd_subj, 'red')

			return 0

		cmd_args = list(filter(bool, cmd['args']))
		cmd_type = cmd['exe_type']
		real_dest = cmd['dest']
		temp_dest = cmd['dest_temp']

		flags = cmd['flags']
		archive_suffix = cmd['suffix']
		def_suffix = cmd['def_suffix']

		print(cmd_args_to_text(cmd_args))

		if is_only_check:
		
			return 0
		else:
			time_before_start = datetime.datetime.now()
			result_code = subprocess.call(cmd_args, startupinfo=minimized)

			time_after_finish = datetime.datetime.now()
			error_count = 1 if result_code else 0

			if (
				cmd_type == 'rar'
			and	result_code == 10
			):
				no_files_by_subj[cmd_subj] = True

			codes_of_type = exit_codes[cmd_type]
			result_text = codes_of_type[result_code] if result_code in codes_of_type else 'Unknown code'

			cprint(
				'{}: {}'.format(result_code, result_text)
			,	'red' if result_code != 0 else 'cyan'
			)

			if os.path.exists(temp_dest):
				archive_file_size = os.path.getsize(temp_dest)
				archive_file_summary = re.sub(pat_whitespace, ' ', get_archive_file_summary(temp_dest, cmd))

				print('')

				if not archive_file_summary:
					error_count += 1

					cprint('Error: Archive is broken or has unknown format, deleting it.', 'red')

					os.remove(temp_dest)
				elif (
					cmd_type == '7z'
				and	archive_file_size < empty_archive_max_size
				and	'0 0 0 files' in archive_file_summary
				):
					no_files_by_subj[cmd_subj] = True

					cprint('Warning: No files to archive, deleting empty archive.', 'red')

					os.remove(temp_dest)
				else:
					add_suffix = cmd['suffix'].rstrip('.') if archive_suffix else ''
					add_timestamp = (
						datetime.datetime.fromtimestamp(os.path.getmtime(temp_dest)).strftime(time_format)
						if add_mod_time
						else ''
					)
					add_timestamp_first = add_timestamp and (def_suffix_separator in flags)

					if add_timestamp or add_suffix or def_suffix:
						path_part_before, path_part_after = real_dest.rsplit(archive_suffix or '.', 1)
						path_part_before += (
							(add_timestamp if add_timestamp_first else '')
						+	(def_suffix or '')
						+	(add_suffix or '')
						+	(add_timestamp if not add_timestamp_first else '')
						)

						final_dest = get_unique_clean_path(path_part_before, '.' + path_part_after)
					else:
						final_dest = get_unique_clean_path(real_dest)

					if final_dest and final_dest != temp_dest:
						print(normalize_slashes(temp_dest))
						print(normalize_slashes(final_dest))
						print('')

						os.rename(temp_dest, final_dest)

					summary_parts = archive_file_summary.split(' ', 4)
					content_sum_size = int(summary_parts[2])
					content_counts_text = summary_parts[4]
					compression_ratio = 100.0 * archive_file_size / content_sum_size

					archive_size_text = get_bytes_text(archive_file_size)
					content_size_text = get_bytes_text(content_sum_size)

					print_with_colored_prefix('Source total size:', '{}, {}'.format(content_size_text, content_counts_text))
					print_with_colored_prefix('Archive file size:', '{}, {:.2f}%'.format(archive_size_text, compression_ratio))
					print_with_colored_prefix('Took time:', time_after_finish - time_before_start)

					if is_keep_only_1:
						obsolete_file_path = None
						smallest_for_this_subj = smallest_archives_by_subj.get(cmd_subj)

						if not smallest_for_this_subj:

							smallest_archives_by_subj[cmd_subj] = {
								'path' : final_dest
							,	'size' : archive_file_size
							}

						elif smallest_for_this_subj['size'] > archive_file_size:

							obsolete_file_path = smallest_for_this_subj['path']

							print('')
							cprint('New archive is smaller: {} < {}, deleting bigger old.'.format(
								get_bytes_text(archive_file_size, add_text=False)
							,	get_bytes_text(smallest_for_this_subj['size'])
							), 'cyan')

							smallest_for_this_subj['path'] = final_dest
							smallest_for_this_subj['size'] = archive_file_size
						else:
							obsolete_file_path = final_dest

							print('')
							cprint('Old archive is smaller or same: {} <= {}, deleting new.'.format(
								get_bytes_text(smallest_for_this_subj['size'], add_text=False)
							,	get_bytes_text(archive_file_size)
							), 'magenta')

						if obsolete_file_path:
							try:
								os.remove(obsolete_file_path)

							except FileNotFoundError:
								print('')
								cprint('Warning: No file to delete.', 'red')

			return error_count
			
# - Check arguments -----------------------------------------------------------

	argv = list(argv)
	argc = len(argv)

	argv_flag = argv.pop(0) if len(argv) > 0 else ''
	argv_subj = argv.pop(0) if len(argv) > 0 else None
	argv_dest = argv.pop(0) if len(argv) > 0 else None
	argv_rest = argv if len(argv) > 0 else None

# - Show help and exit --------------------------------------------------------

	flag_parts_left = list(filter(bool, argv_flag.split(split_flag_combo)))

	if (
		not len(argv_flag) > 0
	or	not len(flag_parts_left) > 0
	or	argv_flag[0] == '-'
	or	argv_flag[0] == '/'
	):
		print_help()

		return 1

# - Fill batch queue and run --------------------------------------------------

	subj = normalize_slashes(argv_subj if argv_subj and len(argv_subj) > 0 else def_subj)
	dest = normalize_slashes(argv_dest if argv_dest and len(argv_dest) > 0 else def_dest)
	rest = argv_rest or []

	print('')
	print_with_colored_prefix('print encoding:', print_encoding)
	print_with_colored_prefix('argc:', argc)
	print_with_colored_prefix('subj:', get_text_encoded_for_print(subj))
	print_with_colored_prefix('dest:', get_text_encoded_for_print(dest))
	print_with_colored_prefix('etc:', get_text_encoded_for_print(' '.join(rest)))

	is_delete_enabled = False
	common_part_with_name = flag_parts_left.pop()

	if len(flag_parts_left) > 0:

		common_flag_part, name = split_text_in_two(common_part_with_name, def_name_separator)
		combos = [
			(combo_flag_part + common_flag_part).upper()
			for combo_flag_part in flag_parts_left
		]

		flags = ''.join(sorted(set(''.join(combos))))
	else:
		flags, name = split_text_in_two(common_part_with_name, def_name_separator)
		flags = flags.upper()

	if minimized_flag in flags:
		SW_MINIMIZE = 6
		minimized = subprocess.STARTUPINFO()
		minimized.dwFlags = subprocess.STARTF_USESHOWWINDOW
		minimized.wShowWindow = SW_MINIMIZE
	else:
		minimized = None

	is_delete_enabled = delete_sources_flag in flags
	is_keep_only_1 = keep_smallest_archive_flag in flags
	is_no_waiting  = no_waiting_keypress_flag in flags
	is_only_check  = only_list_commands_flag in flags
	is_subj_list   = (subj[0].strip('"') == '@')

	foreach_subj_names = None
	foreach_dir  = for_each_dir_flag in flags
	foreach_file = for_each_file_flag in flags
	foreach_dir_or_file = (foreach_dir or foreach_file) and not is_subj_list
	foreach_ID_flags = ''.join([
		x
		for x in group_by_num_any_sep_flags
		if x in flags
	])

	if foreach_dir_or_file or foreach_ID_flags:

		names = list(map(
			normalize_slashes
		,	glob.glob(subj) if ('*' in subj or '?' in subj) else
			os.listdir(subj) if os.path.isdir(subj) else
			[subj]
		))

		if foreach_ID_flags:
			dots = ''.join([
				x
				for x in (group_sep_dot_flag + group_sep_comma_flag)
				if x in foreach_ID_flags
			])

			pat_ID = re.compile(
				r'^(\D*\d[\d' + dots + ']*)(?=[^\d' + dots + ']|$)' if dots else
				r'^(\D*\d+)(?=\D|$)'
			)

			if group_listfile_flag in foreach_ID_flags:
				no_group = def_name or def_name_fallback
				other_to_1 = group_flag in foreach_ID_flags
				d = {}

				for each_subj in names:
					s = re.search(pat_ID, each_subj)
					n = s.group(1) if s else no_group if other_to_1 else each_subj

					if not n in d:
						d[n] = []
					d[n].append(each_subj)

				names = []

				for i in d.keys():
					listfile_path = dest + '/' + i + '_list.txt'
					names.append('@' + listfile_path)

					if not is_only_check:
						grouped_filenames = d[i]

						try:
							f = open(listfile_path, 'wb')
							f.write(u'\n'.join(grouped_filenames))
							f.close()

						except TypeError:
							if f: f.close()

							f = io.open(listfile_path, 'w', encoding=listfile_encoding)
							f.write(u'\n'.join(grouped_filenames))
							f.close()

						except (UnicodeEncodeError, UnicodeDecodeError):
							if f: f.close()
			else:
				d = []
				for each_subj in names:
					s = re.search(pat_ID, each_subj)
					if s:
						n = s.group(1) + '*'
						if not (n in d):
							d.append(n)
					else:
						d.append(each_subj)
				names = d

		foreach_subj_names = names if foreach_dir == foreach_file else [
			each_subj
			for each_subj in names
			if foreach_dir == os.path.isdir(each_subj)
		]

	add_mod_time   = add_mod_time_flag in flags
	add_start_time = add_start_time_flag in flags

	time_format = (
		';_%Y-%m-%d,%H-%M-%S' if alt_time_format_flag in flags else
		r'_%Y-%m-%d_%H-%M-%S'
	)

	t0 = time.strftime(time_format)

	exe_paths = get_exe_paths()
	cmd_queue = []
	cmd_count = error_count = del_warn = 0
	cmd_queue_by_subj = {}
	no_files_by_subj = {}
	smallest_archives_by_subj = {}

	if len(flag_parts_left) > 0:

		def cleanup_combo(combo):
			return (
				(only_list_commands_flag if is_only_check else '')
			+	get_text_without_chars(combo, only_list_commands_flag + delete_sources_flag)
			+	(def_name_separator + name if len(name) > 0 else '')
			)

		combos = list(map(cleanup_combo, combos))

		if is_delete_enabled:
			i = len(combos) - 1
			combos[i] = delete_sources_flag + combos[i]

		print_with_colored_prefix('all flags:', get_text_encoded_for_print(flags.lower()))
		print_with_colored_prefix('flag combos:', len(combos))

		for combo in combos:
			print('')

			del_warn += queue_batch_part(combo)
	else:
		del_warn += queue_batch_part(common_part_with_name)

	cmd_count = len(cmd_queue)

	if cmd_count == 0:
		print('')
		cprint('----	----	Nothing to do, command queue is empty.', 'cyan')

		return 11

	if is_delete_enabled or del_warn:
		print('')
		cprint('----	----	Warning: subject files will be deleted after archiving.', 'yellow')
		print('Only WinRAR or 7-Zip v17+ can delete them.')
		print('Only WinRAR can test archives before deleting anything.')
		print('Please make sure your subject arguments work as intended in all used programs before enabling deletion.')

		if not (is_only_check or is_no_waiting):
			print('Press Enter to continue.')

			wait_user_input()

# - Do all queued jobs --------------------------------------------------------

	if sort_queue_by_subj:
		for each_subj, each_queue in cmd_queue_by_subj.items():
			print('')
			print_with_colored_prefix('subj:', each_subj)

			for cmd in each_queue:
				error_count += run_cmd(cmd)
	else:
		for cmd in cmd_queue:
			error_count += run_cmd(cmd)

# - Result summary ------------------------------------------------------------

	print('')

	if error_count > 0:
		if is_no_waiting:

			print(' '.join([
				colored('----	----	Done {} archive(s),'.format(cmd_count), 'green')
			,	colored('{} errors.'.format(error_count), 'red')
			,	'See messages above.'
			]))
		else:
			print(' '.join([
				colored('----	----	Done {} archive(s),'.format(cmd_count), 'green')
			,	colored('{} errors.'.format(error_count), 'red')
			,	'Press Enter to continue.'
			]))

			wait_user_input()

	elif is_only_check:

		cprint('----	----	Total {} command(s).'.format(cmd_count), 'green')
	else:
		cprint('----	----	Done {} archive(s).'.format(cmd_count), 'green')

	return 0 if error_count == 0 and cmd_count > 0 else -1

# - Run from commandline, when not imported as module -------------------------

if __name__ == '__main__':
	sys.exit(run_batch_archiving(sys.argv[1 : ]))

# - End -----------------------------------------------------------------------
