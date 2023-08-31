#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import datetime, json, os, re, sys, zipfile

# Use colored text if available:
try:
	from termcolor import colored, cprint
	import colorama

	colorama.init()

except ImportError:
	def colored(*list_args, **keyword_args): return list_args[0]
	def cprint (*list_args, **keyword_args): print (list_args[0])

from r_config import get_rei, re_ix, re_iux
from r_config import default_print_encoding, default_name_cut_length, default_read_bytes
from r_config import dest_root, dest_root_by_ext, dest_root_yt
from r_config import ext_web, ext_web_remap, ext_web_read_bytes, ext_web_index_file, sites

arg_name_cut = 'cut'
arg_name_sub = 'sub'

args = sys.argv
argc = len(args)

arg_flags = args[1] if argc > 1 else ''
other_args = args[2 : ] if argc > 2 else []

if argc < 2 or arg_flags[0] == '-' or arg_flags[0] == '/':
	self_name = os.path.basename(__file__)

	help_text_lines = [
		''
	,	'* Description:'
	,	'	Move files from unsorted pile, e.g. download folder,'
	,	'	into predesignated places depending on file names and/or contents.'
	,	''
	,	'* Usage:'
	,	'	%s <flags> [<other options>] ...'
	,	''
	,	'<flags>: string of letters in any order as first argument.'
	,	'	t: for test, output only (don\'t apply changes)'
	,	'	e: for debug, turn warnings (just printed) into exceptions (stop the script if uncatched)'
	,	'	f: for name cutting, check length of full path instead of only name'
	,	'	o: print full path instead of only name'
	,	'	r: recurse into subfolders (default = stay in working folder)'
	,	''
	,	'	b: move aib-grabbed files into subdir by thread ID in filename'
	,	'	d: move booru-grabbed duplicates into subdir by md5 in filename, keep oldest'
	,	'	p: move pixiv-grabbed files into subdir by work ID in filename'
	,	'	s: move files with specific ext to configured paths'
	,	'	u: move files up from subdir by type (flash, gif, video, etc, may start from underscore)'
	,	'	w: move web page archive files ('+'/'.join(ext_web)+') by URL in file content'
	,	'	x: move non-image files into subdir by type in ext (flash, gif, video, etc)'
	,	'	y: rename Complete YouTube Saver downloads in sub/same-folder by ID in URL and filenames'
	,	''
	,	'<other options>: separate each with a space.'
	,	'	'+arg_name_cut+': cut long names to '+str(default_name_cut_length)
	,	'	'+arg_name_cut+'<number>: cut long names to specified length'
	,	''
	,	'	'+arg_name_sub+': move each leftover file into a subdir named by first character of its name'
	,	'	'+arg_name_sub+'<number>: name subdir by specified number of first characters of subject name'
	,	''
	,	'	y:   move leftover files into subdir named by mod-time year'
	,	'	m:   subdir by month'
	,	'	d:   subdir by day'
	,	'	ym:  subdir by year-month'
	,	'	ymd: subdir by year-month-day'
	,	'		Notes: may be combined,'
	,	'		interpreted as switches (on/off),'
	,	'		resulting always in this order: y/ym/m/ymd/d/'+arg_name_sub
	,	''
	,	'	dir: move dirs into subdir by name and/or mod-time too'
	,	''
	,	'* Examples:'
	,	'	%s rwb'
	,	'	%s tfo '+arg_name_cut+'234'
	,	'	%s o dir '+arg_name_sub
	,	'	%s o dir y ym ymd'
	]

	print('\n'.join(help_text_lines).replace('%s', self_name))

	sys.exit()

TEST = 't' in arg_flags
DO = not TEST

arg_cut_full_path        = 'f' in arg_flags
arg_print_full_path      = 'o' in arg_flags
arg_recurse_into_subdirs = 'r' in arg_flags
arg_warning_to_error     = 'e' in arg_flags

arg_move_aib_by_threads = 'b' in arg_flags
arg_move_cys_by_id      = 'y' in arg_flags
arg_move_dups_by_md5    = 'd' in arg_flags
arg_move_pxv_by_id      = 'p' in arg_flags
arg_move_types_by_ext   = 's' in arg_flags
arg_move_subtypes       = 'x' in arg_flags
arg_move_subtypes_up    = 'u' in arg_flags
arg_move_web_pages      = 'w' in arg_flags
arg_move_dirs_to_subdir_by_modtime = 'dir' in other_args

arg_subdir_modtime_format = ''

if 'y'   in other_args: arg_subdir_modtime_format += '/%Y'
if 'ym'  in other_args: arg_subdir_modtime_format += '/%Y-%m'
if 'm'   in other_args: arg_subdir_modtime_format += '/%m'
if 'ymd' in other_args: arg_subdir_modtime_format += '/%Y-%m-%d'
if 'd'   in other_args: arg_subdir_modtime_format += '/%d'

if arg_warning_to_error:
	# https://stackoverflow.com/a/17211698
	import warnings
	warnings.filterwarnings('error')

def get_number_from_args(arg_name, default_value=1):

	arg_name_len = len(arg_name)
	result_value = default_value if arg_name in other_args else 0

	for each_arg in other_args:
		if (
			len(each_arg) > arg_name_len
		and	arg_name == each_arg[0 : arg_name_len]
		):
			result_value = max(result_value, int(each_arg[arg_name_len : ]))

	return result_value

arg_cut_name_to_subdir_len = get_number_from_args(arg_name_sub)
arg_cut_name_to_rename_len = get_number_from_args(arg_name_cut, default_name_cut_length)
# ^- pass 'cut' or 'cut123' for longname cutting tool; excludes move to folders

print_duplicate_count=True
unprinted_duplicate_count=0

pat_url = get_rei(r'''
(?:^|[>\r\n]\s*)
(?P<Meta>
	(?:
	# MHT:
		(?:Snapshot-)?Content-Location:[^\w\r\n]*	# <- [skip quotes, whitespace, any garbage, etc]
	# MAFF:
	|	<MAF:originalurl\s+[^<>\s=\r\n]+=[^<>\w\r\n]*
	# HTML:
	|	<!--\s+saved\s+from\s+url=(?:\(\d+\))?
	|	<!--\s+Page\s+saved\s+with\s+SingleFileZ?\s+url:\s+
	|	<a\s+id="savepage-pageinfo-bar-link"\s+href=[^<>\w\r\n]*
	|	<base\s+href=[^<>\w\r\n]*
	)
)
(?P<URL>
	(?P<Scheme>
		(?P<Protocol>[\w-]+)
		:+
	)
	/*
	(?P<Proxy>
		u
		(?:[:](?P<ProxyPort>\d+))?
		/+[?]*
		(?P<ProxyScheme>
			(?P<ProxyProtocol>ftps?|https?)
			:*
		)
		/+
	)?
	(?P<DomainPath>
		(?P<DomainPort>
			(?P<Domain>[^"':/?&=\#\s\r\n]+)?
			(?:[:](?P<Port>\d+))?
		)
		(?P<Path>
			/+
			(?P<Query>
				[?]?
				(?P<QueryPath>
					(?P<QuerySelector>
						(?P<QueryKey>[^"/?&=\#\s\r\n]+)?
						(?:
							[=]
							(?P<QueryValue>[^"/?&\#\s\r\n]+)
						)?
					)
					(
						[/?&]+
						(?P<IsArchived>arch[ive]*/+)?
						(?P<ItemSelector>
							(?P<ItemContainer>prev|res|thread)/+
						|	\w+\.pl[/?]*
						)?
					)?
					(?P<ItemID>[^"\#\s\r\n]*)
				)
			)
		)?
		(?P<Fragment>\#[^"\r\n]*)?
	)
)
''')

pat_ren = [
	{
		'type': 'booru'
	,	'page': get_rei(r'''^
			(?P<Domain>\{[^{}\s]+\})?		# <- added by SavePageWE
			(?P<Prefix>
				(/dan|gel|r34|san|sfb)\s+
				([0-9]+)
			)
			(\s+.*)?
			(?P<Ext>\.[^.]+)
		$''', re_iux)
	,	'child': get_rei(r'''^	# image/video files:
			(?P<Prefix>\S+)?
			(?P<ID>[0-9a-f]{32})
			(?P<Suffix>\S+)?
			(?P<Ext>\.[^.]+)
		$''', re_iux)
#	,	'child': get_rei(r'^([^_]\S*)?[0-9a-f]{32}\S*\.\w+$')
	}
,	{
		'type': 'filehosting'
	,	'page': get_rei(r'''^			# <- ur'' gives "SyntaxError: invalid syntax" in python3
			(?P<Domain>\{[^{}\s]+\})?		# <- added by SavePageWE
			(?P<Prefix>
				(?P<SiteName>[^{}\s]+)\s+
				(?P<FileID>\S+)
				\s+-\s+
				(?P<Date>\d{4}(?:\D\d\d){5})
				(?P<TimeZone>\s+[+-]\d+)?
				\s+-\s+
			)
			(?P<FileName>\S.*?)\s+[-\u2014\S]+\s+
			(?P<Suffix>
			''' + '|'.join([
				'RGhost(?:\s+\S\s+[^.]+)?'
			,	'Yandex[.\S]Dis[ck]'
			,	u'Яндекс[.\S]Диск		# <- "yandex.disk"'
			,	'\S+\s+Mail\.Ru			# <- "cloud mail.ru"'
			]) + r'''
			)
			(?P<PageName>\s+-\s+\S+?)?		# <- added by UnMHT
			(?P<SaveDate>\{\d{4}(?:\D\d\d){5}\})?	# <- added by SavePageWE
			(?P<OpenDate>;?_\d{4}(?:\D\d\d){5})?	# <- added by UserJS
			(?P<Ext>\.[^.]+)
		$''', re_iux)
	}
,	{
		'type': 'youtube'
	,	'page': get_rei(r'''^	# page files:
			(?P<Domain>\{[^{}\s]+\})?		# <- added by SavePageWE
			(?P<Prefix>
				YouTube
				(?:\s+-\s+(?P<Author>.+?))
				(?:\s+-\s+(?P<Date>\d{4}(-\d\d){2}))
				(?:\s+-\s+(?P<Title>.+?))
			)
			(?P<PageName>\s+-\s+watch)?		# <- added by UnMHT
			(?P<SaveDate>\{\d{4}(?:\D\d\d){5}\})?	# <- added by SavePageWE
			(?P<OpenDate>;?_\d{4}(?:\D\d\d){5})?
			(?P<Ext>\.[^.]+)
		$''', re_iux)
	,	'child': get_rei(r'''^	# video files/folders:
			(?:Youtube(?:,|\s+-\s+))?
			(?P<ID>v=[\w-]+)(?:,|\s+-\s+)
			(?P<Res>\d+p|\d+x\d+)?
			(?P<FPS>\d+fps)?
			(?P<TimeStamp>;?_\d{4}(?:\D\d\d){5})?
			(?P<Ext>\.[^.]+)?
		$''', re_iux)
	,	'dest': dest_root_yt
	} if arg_move_cys_by_id else None
#,	['pixiv', get_rei(r',illust_id=(\d+).*\.\w+$')]
]

pat_sub = [
# item format:
# [
#	match
#	optional subdirname (default = 1st capture group)
#	optional match if 2nd file existed (for series)
#	optional match for duplicate ID
#	optional match for the smallest value to leave one duplicate at old place (to delete others manually, etc)
# ]
	{
		'match': get_rei(r'^.*?\b(\w+#\d+),\d+(,\s+\d+\s+*\w+,\s+\d+x\d+([.,].*)?)?\.\w+$')
	,	'subdir': r'\1'
	} if arg_move_aib_by_threads else None
,	{
		'match': get_rei(r'^(pxv\D+(\d+)\D*?_)p\d+(\D.*)$')
	,	'next': r'\1p1\3'
	,	'subdir': r'\2'
	} if arg_move_pxv_by_id else None
,	{
		'match': get_rei(r'''^
			(?:(?P<Site>\S+)\s-\s)
			(?:(?P<ID>\S+)\s-\s)
			(?P<Hash>\S+)
			(?:\s-\s
				(?P<TimeStamp>\d{4}(?:\D\d\d){2,5})
			)?
			(?:\s-\s
				(?P<Etc>.*?)
			)?
			(?P<Ext>\.[^.]+)
		$''')
	,	'group_by': r'\g<Hash>'
	,	'date': r'\g<TimeStamp>'
	,	'subdir': '1'
	} if arg_move_dups_by_md5 else None
,	{
		'match_dir': get_rei(r'(^|[\\/])(_not|_animation|_frames|_gif|_flash|_video|_img)+([\\/]|$)')
	,	'subdir': r'..'
	} if arg_move_subtypes_up else None
] + ([
	{'subdir': r'_animation_frames','match': get_rei(r'\.zip$')}
,	{'subdir': r'_gif',		'match': get_rei(r'\.gif$')}
,	{'subdir': r'_flash',		'match': get_rei(r'\.(swf|fws)$')}
,	{'subdir': r'_video',		'match': get_rei(r'\.(mov|mp4|mkv|webm)$')}
,	{'subdir': r'_not_img',		'match': get_rei(r'\.(?!(bmp|png|jp[eg]+|webp|gif|swf|fws|mov|mp4|mkv|webm|zip)$)\w+$')}
] if arg_move_subtypes else [])

pat_idx = get_rei(r'<MAF:indexfilename\s+[^=>\s]+="([^">]+)')
pat_ren_mht_linebreak = get_rei(r'=\s+')
pat_ren_src_name = get_rei(r'([a-z0-9]*[^a-z0-9.]+)+')
pat_ren_yt_URL_ID = get_rei(r'[?&](?P<ID>v=[\w-]+)(?:[?&#]|$)')

dup_lists_by_ID = {}
not_existed = []
n_i = n_matched = n_moved = n_fail = n_back = n_later = n_max_len = 0	# <- count iterations, etc
ext_path_inside = ext_web if arg_move_web_pages else []			# <- understandable file format extensions

a_type = type(pat_ren)
d_type = type(dup_lists_by_ID)
r_type = type(pat_url)
s_type = type('')
u_type = type(u'')

local_path_prefix = u'//?/'
info_prfx = '\t'
msg_prfx = '\n-\t'

def is_type_int(v): return isinstance(v, int)
def is_type_arr(v): return isinstance(v, a_type)
def is_type_dic(v): return isinstance(v, d_type)
def is_type_reg(v): return isinstance(v, r_type)
def is_type_str(v): return isinstance(v, s_type) or isinstance(v, u_type)

def dumpclean(obj):
	if type(obj) == dict:
		for k, v in obj.items():
			if hasattr(v, '__iter__'):
				print k
				dumpclean(v)
			else:
				print k, ':', v
	elif type(obj) == list:
		for v in obj:
			if hasattr(v, '__iter__'):
				dumpclean(v)
			else:
				print v
	else:
		print obj

def print_url_groups(match, prefix_color='red'):
	# print colored('URL:', prefix_color), url.group('URL')
	print colored('Match groups:', prefix_color), match.groups()
	print colored('Named groups:', prefix_color), json.dumps(match.groupdict(), indent=4, sort_keys=True)

def normalize_slashes(path):
	return path.replace('\\', '/')

def fix_slashes(path):
	if os.sep != '/':
		path = path.replace('/', os.sep)

	if os.sep != '\\':
		path = path.replace('\\', os.sep)

	return path

def conflate_slashes(path):

	match = re.search(pat_local_prefix, path)

	return (
		local_path_prefix + re.sub(pat_conseq_slashes, '/', match.group('Path'))
		if match
		else
		re.sub(pat_conseq_slashes, '/', path)
	)

def get_path_with_local_prefix(path):

	match = re.search(pat_local_prefix, path)
	path = re.sub(pat_conseq_slashes, '/', match.group('Path') if match else path)

	return local_path_prefix + path.lstrip('/')

def remove_trailing_dots_in_path_parts(path):
	return '/'.join(
		part if part == '.' or part == '..'
		else part.rstrip('.')
		for part in normalize_slashes(path).split('/')
	)

def get_long_abs_path(path):
	if local_path_prefix:
		path = remove_trailing_dots_in_path_parts(path)

		if path.find(normalize_slashes(local_path_prefix)) == 0:
			return path
		else:
			return local_path_prefix + os.path.abspath(path)

	return fix_slashes(remove_trailing_dots_in_path_parts(path))

def get_file_name_from_path(path):
	path = normalize_slashes(path)

	if path.find('/') >= 0: path = path.rsplit('/', 1)[1]

	return path

def get_file_ext_from_path(path):
	path = normalize_slashes(path)

	if path.find('/') >= 0: path = path.rsplit('/', 1)[1]
	if path.find('.') >= 0: path = path.rsplit('.', 1)[1]

	return path.lower()

def read_zip_file(src_path, return_source_html=False):
	file_ext = get_file_ext_from_path(src_path)

	for ext, index_file_name in ext_web_index_file.items():
		if ext != file_ext:
			continue

		try:
			zip_file = zipfile.ZipFile(src_path, 'r')

			for path in zip_file.namelist():
				name = path.rsplit('/', 1)[-1 : ][0]

				if name == index_file_name:
					if TEST:
						print info_prfx, colored('MAFF/ZIP test, meta file:', 'yellow'), path, '\n'

					result = zip_file.read(path)			# <- return source URL

					if return_source_html:
						s = re.search(pat_idx, result)

						if s and s.group(1):
							path = path[ : -len(name)] + s.group(1)
							if TEST:
								print info_prfx, colored('MAFF/ZIP test, content file:', 'yellow'), path, '\n'

							result = zip_file.read(path)	# <- return source HTML

					elif '<?xml' in result and '<RDF:RDF' in result:
						result = result.replace('&amp;', '&')

					return result

		except zipfile.BadZipfile as exception:
			if TEST:
				print msg_prfx, colored('MAFF/ZIP test, cannot read file as ZIP:', 'yellow'), src_path
				print exception


def read_file_or_part(src_path, size=0):
	global n_fail

	result = ''

	try:
		result = read_zip_file(src_path, return_source_html=(not size))

		if result is None:
			f = open(src_path)
			result = f.read(size) if size else f.read()
			f.close()

	except Exception as exception:
		n_fail += 1
		print msg_prfx, colored('Path length:', 'yellow'), len(src_path)
		print exception

	return result

def get_formatted_modtime(src_path, format):
	return datetime.datetime.fromtimestamp(os.path.getmtime(src_path)).strftime(format)

def get_unique_clean_path(src_path, dest_path, print_duplicate_count=True):
	global unprinted_duplicate_count

	try_count = 0
	dest_path = get_long_abs_path(dest_path)

	if os.path.exists(dest_path) and os.path.exists(src_path):
		try_count += 1
		dest_path = get_formatted_modtime(src_path, ';_%Y-%m-%d,%H-%M-%S.').join(dest_path.rsplit('.', 1))

	if os.path.exists(dest_path):
		dest_path_parts = dest_path.rsplit('.', 1)

		while os.path.exists(dest_path):
			try_count += 1
			dest_path = '({}).'.format(try_count).join(dest_path_parts)

	if try_count:
		if print_duplicate_count:
			try_count += unprinted_duplicate_count
			cprint('+ %d %s' % (try_count, 'duplicate' if try_count == 1 else 'duplicates'), 'yellow')
			unprinted_duplicate_count = 0
		else:
			unprinted_duplicate_count += 1

	return dest_path

def rename_to_unique_clean_path(src_path, dest_path):
	src_path = get_long_abs_path(src_path)

	return os.rename(src_path, get_unique_clean_path(src_path, dest_path))

def meet(obj, criteria, file_path_or_name=None):
	try:
		return True if (
			(obj is criteria) or
			(obj == criteria) or (
				(is_type_str(obj     ) or obj     ) and
				(is_type_str(criteria) or criteria) and (
					criteria.match(obj)       if is_type_reg(criteria) else
					(obj in criteria)         if is_type_arr(criteria) else
					(obj.find(criteria) >= 0) if is_type_str(criteria) else
					None
				)
			)
		) else False

	except UnicodeWarning as exception:
		print msg_prfx, colored('Exception:', 'red'), exception
		print info_prfx, colored('While comparing:', 'yellow'), obj
		print info_prfx, colored('To criteria:', 'yellow'), criteria

		if file_path_or_name:
			print info_prfx, colored('In file:', 'yellow'), file_path_or_name.encode(default_print_encoding)

	return False

def get_sub(subj, rules):
	if not rules:
		return None

	if is_type_str(rules):
		return [rules, '']

	name, meeting, board, file_path_or_name = subj

	for rule in rules:
		if not rule:
			continue

		if is_type_str(rule):
			return [rule, '']

		if is_type_arr(rule):
			if len(rule) > 1:
				r0 = is_type_reg(rule[0])
				pattern = rule[0 if r0 else 1]
				met = None

				for me in meeting:
					if meet(me, pattern, file_path_or_name):
						met = me

						break

				if met is not None:
					if rule[0] is None:
						return None

					dsub = rename = ''

				# grab subfolder from URL parts:

					if r0:
						r1 = rule[1]
						r1a = r1 if is_type_arr(r1) else [r1]
						for r1 in r1a:
							try:
								if r1 and is_type_str(r1):
									dsub = (
										re
										.search(rule[0], met)
										.expand(r1)
									)

									break
							except:
								continue
					else:

				# specific rules:

						dsub = rule[0]
						rename = name

				# full filename replacement:

						if len(rule) > 3:
							if is_type_reg(rule[2]) and is_type_str(rule[3]):
								rename = re.sub(rule[2], rule[3], rename)

							for replacement in rule[2 : ]:
								if (
									is_type_arr(replacement)
								and	len(replacement) > 1
								and	is_type_reg(replacement[0])
								and	is_type_str(replacement[1])
								):
									rename = re.sub(replacement[0], replacement[1], rename)

				# only append item ID to filename, if not yet:

						if len(rule) > 2:
							if is_type_reg(rule[1]) and is_type_str(rule[2]):
								suffix = (
									re
									.search(rule[1], met)
									.expand(rule[2])
								)

								if rename.find(suffix) < 0:
									rename = (suffix+'.').join(rename.rsplit('.', 1))

						if rename == name:
							rename = ''

						if TEST and rename:
							try:
								print 'Rename:', rename

							except UnicodeEncodeError:
								cprint('<not showing unprintable unicode>', 'red')

								# https://stackoverflow.com/a/62658901
								print 'Rename:', rename.encode('utf-8').decode('ascii', 'ignore')

					return [dsub, rename]

			elif board:
				return [rule[0], '']

	return None

def print_name(name, prefix='', extra_line=True):
	if extra_line:
		print

	mid_text = 'name in'
	pre_text = '{0} {1}'.format(prefix, mid_text) if prefix else mid_text

	for enc in ['utf-8', 'unicode-escape']:
		cprint('{0} {1}:'.format(pre_text, enc), 'yellow')
		print name.encode(enc)

def move_processed_target(src_path, path, name, dest_dir=None):
	global n_fail, n_moved

	if not dest_dir and (
		arg_subdir_modtime_format
	or	arg_cut_name_to_subdir_len
	):
		dest_dir = '/'.join(filter(None, [
			path.rstrip('/')
		,	get_formatted_modtime(src_path, arg_subdir_modtime_format).strip('/') if arg_subdir_modtime_format else None
		,	name[ : arg_cut_name_to_subdir_len] if arg_cut_name_to_subdir_len else None
		]))

	if dest_dir:
		print dest_dir.encode(default_print_encoding), colored('<-', 'yellow'), name.encode(default_print_encoding)

		if DO:
			dest = get_unique_clean_path(src_path, dest_dir+'/'+name)

			try:
				if not os.path.exists(dest_dir):
					print colored('Path not found, make dirs:', 'yellow'), dest_dir.encode(default_print_encoding)
					os.makedirs(dest_dir)

				os.rename(src_path, dest)
				n_moved += 1

			except Exception as exception:
				n_fail += 1
				print msg_prfx, colored('Path length:', 'yellow'), len(src_path), colored('to', 'yellow'), len(dest)
				print exception

def process_dir(path, later=0):
	names = os.listdir(path)
	names_todo_later = process_names(path, names, later)

	if names_todo_later:
		process_names(path, names_todo_later)

def process_names(path, names, later=0):

	global n_i, n_fail, n_matched, n_moved, n_back, n_later, n_max_len
	global not_existed, dup_lists_by_ID
	global print_duplicate_count

	if later:
		files_to_check_later = []

	for name in names:
		if not later:
			n_i += 1

		src_path = get_long_abs_path(path+'/'+name)
		src_path_or_name = (src_path if arg_print_full_path else name)

		if os.path.isdir(src_path):
			if arg_recurse_into_subdirs:
				if later:
					n_later += 1
					files_to_check_later.append(name)
				else:
					if TEST and arg_print_full_path:
						print_name(name, 'Dir')

					process_dir(src_path, later)

			if arg_move_dirs_to_subdir_by_modtime:
				move_processed_target(src_path, path, name)

			continue

		if TEST and arg_print_full_path:
			print_name(name, 'File')

		# optionally cut long names before anything else:

		if arg_cut_name_to_rename_len:
			src_path = os.path.abspath(src_path) if arg_cut_full_path else name
			src_len = len(src_path)

			if src_len > arg_cut_name_to_rename_len:
				n_matched += 1

				if n_max_len < src_len:
					n_max_len = src_len

				ext = '(...).' + get_file_ext_from_path(name)
				dest_path = src_path[ : arg_cut_name_to_rename_len - len(ext)].rstrip() + ext
				dest_path = get_unique_clean_path(src_path, dest_path)
				dest_show = (dest_path if arg_print_full_path else get_file_name_from_path(dest_path))
				src_show = (src_path if arg_print_full_path else name)

				print
				print colored('Cut from', 'yellow'), src_len, src_show.encode(default_print_encoding)
				print colored('Cut to', 'yellow'), len(dest_show), dest_show.encode(default_print_encoding)

				if DO:
					os.rename(src_path, dest_path)

					name = get_file_name_from_path(dest_path)
					src_path = get_long_abs_path(path+'/'+name)

					n_moved += 1

		ext = old_ext = get_file_ext_from_path(name)
		ext = ext_web_remap.get(ext, ext)
		d = ''

		if arg_move_types_by_ext and ext in dest_root_by_ext:
			if later:
				n_later += 1
				files_to_check_later.append(name)
			else:
				d = dest_root_by_ext[ext]

				if is_type_arr(d):
					for d_i in d:
						if is_type_dic(d_i):
							test = d_i.get('match_name')

							if test and not meet(name, test, src_path_or_name):
								continue

							d = d_i.get('dest_path') or dest_root
						else:
							d = d_i

						break

				if not is_type_str(d):
					continue

				print d.encode(default_print_encoding), colored('<-', 'yellow'), name.encode(default_print_encoding)

				if DO and os.path.exists(src_path) and os.path.isdir(d):
					rename_to_unique_clean_path(src_path, d+'/'+name)
					n_moved += 1

		elif ext in ext_path_inside:
			n_matched += 1

			url = None
			size_of_part_to_read = ext_web_read_bytes.get(ext, default_read_bytes)
			file_content_part = read_file_or_part(src_path, size_of_part_to_read)

			if file_content_part:
				if ext == 'html':
					max_found_url_length = 0

					for each_found_url in re.finditer(pat_url, file_content_part):
						url_length = len(each_found_url.group('URL'))

						if max_found_url_length < url_length:
							max_found_url_length = url_length

							url = each_found_url
				else:
					url = re.search(pat_url, file_content_part)

			if url:
				if TEST:
					print_url_groups(url, 'yellow')
			else:
				if TEST:
					print info_prfx, colored('No URL in file:', 'yellow'), src_path.encode(default_print_encoding)

				continue

			ufull = url.group('URL')
			board = url.group('QuerySelector')
			thread = (url.group('ItemSelector') or url.group('IsArchived')) and url.group('ItemID')

			# define rule trying order:
			meeting = [
				ufull
			,	url.group('DomainPath')
			,	url.group('Path')
			,	url.group('QueryKey')
			,	url.group('Query')
			,	url.group('Fragment')
			,	board
			]

			for s in sites:
				if not s or not len(s):
					break

				d = url.group('Scheme') or url.group('Protocol')
				domain = ''
				test = s[0]

				if meet(d, test, src_path_or_name):
					domain = d
				else:
					d = url.group('Domain')

					if not d:
						continue

					dp = url.group('DomainPort')

					if meet(dp+'.', test, src_path_or_name):	# <- "name." or "name:port." to match exact full name
						domain = d
					else:
						words = reversed(dp.split('.'))
						d = ''
						for i in words:
							d = (i+'.'+d) if d else i

							if meet(d, test, src_path_or_name):
								domain = d

								break

				if not domain:
					continue

				dest = (s[1] if (len(s) > 1) else domain)		# <- site bak root
				dest += (
					test[0]
					if (is_type_arr(test) and dest[-2 : ] == '//')
					else
					domain
					if (dest[-1 : ] == '/')
					else ''
				).strip('/:.')+'/'

				if len(s) > 2:
					x = [name, meeting, True if board else False, src_path_or_name]
					z = s[2]
					dsub, rename = (
				# board threads (to scrape by other scripts):
						(
							get_sub(x, z.get('sub_threads'))
							if board and thread
							else None
						)
				# board roots, text boards, other specifics (not to scrape):
					or	get_sub(x, z.get('sub'))
					or	['', '']
					)
					if dsub:
						dest += dsub+'/'
					if rename:
						name = rename

				if TEST:
					if arg_print_full_path:
						print info_prfx, src_path.encode(default_print_encoding)
					print dest, colored('<-', 'yellow'), ufull

				# rename target files downloaded from RGHost/booru/yt/etc:
				for p in pat_ren:
					if not p:
						continue

					pat_page_name = p.get('page')

					if not pat_page_name:
						continue

					page_match = re.search(pat_page_name, name)

					if not page_match:
						continue

					site_type = p.get('type')
					site_dest = p.get('dest', '').rstrip('/')
					pat_child_name = p.get('child')

					if site_type == 'booru':
						page_content = re.sub(pat_ren_mht_linebreak, '', read_file_or_part(src_path))

					if site_type == 'youtube':
						page_ID = re.search(pat_ren_yt_URL_ID, url.group('Query'))
						if page_ID:
							page_ID = page_ID.group('ID')

					for child_name in names:
						if pat_child_name:
							child_match = re.search(pat_child_name, child_name)

							if not child_match:
								continue

						child_path = path+'/'+child_name
						child_ext = get_file_ext_from_path(child_name)

						if (child_ext in ext_path_inside) or (not os.path.exists(child_path)):
							continue

						prfx = ''

						if site_type == 'youtube':
							if pat_child_name:
								if page_ID != child_match.group('ID'):
									continue

							prfx = page_match.group('Prefix')+','

							if os.path.isdir(child_path):
								sub_names = os.listdir(child_path)

								for sub_name in sub_names:
									if pat_child_name:
										sub_match = re.search(pat_child_name, sub_name)

										if (not sub_match) or (page_ID != sub_match.group('ID')):
											continue

									sub_path = child_path+'/'+sub_name
									sub_dest = (site_dest or path)+'/'+prfx+sub_name

									print info_prfx, sub_name.encode(default_print_encoding)

									if DO:
										rename_to_unique_clean_path(sub_path, sub_dest)
										n_moved += 1
						elif os.path.isdir(child_path):
							continue

						if site_type == 'filehosting':
							page_child_name = page_match.group('FileName')

							if (
								page_child_name == child_name
							# or	page_child_name == child_name.rsplit('.', 1)[0]
							# or	page_child_name+'.'+child_ext == child_name
							):
								prfx = page_match.group('Prefix')

						if site_type == 'booru':
							f = ''
							if pat_child_name:
								f = child_match.group('ID')
							if not f:
								f = len(child_ext)+1
								f = re.sub(pat_ren_src_name, '', child_name[ : -f])
							if f:
								f = re.search(get_rei(
									r'(?:^|[\r\n\t])'
								+	r'(?:'
								+	r'Content-Location:\s+'
								+	r'|<meta\s+name="twitter:image:src"\s+content="'
								+	r')'
								+	r'\w+:/+[^\r\n\t]+[^w]/'
								+	r'(preview|sample[_-]*)?'
								+	f + '|/'
								+	f + '.'
								+	child_ext
								+	'(\?[^">]*)?">Save'
								), page_content)	# <- [^w] to workaround /preview/ child post list
								if f:
									prfx = page_match.group('Prefix')+(' full,' if f.group(1) else ',')

						if prfx:
							child_dest = (
								path
								if site_type == 'youtube' and os.path.isdir(child_path)
								else
								(site_dest or path)
							)+'/'+prfx+child_name

							print info_prfx, child_dest.encode(default_print_encoding)

							if DO:
								rename_to_unique_clean_path(child_path, child_dest)
								n_moved += 1
					break

				d = ''

				try:
					d = (dest_root+dest).rstrip('/.')
				except Exception as exception:
					print colored('Destination path error:', 'red'), exception

				if len(d) < 1:
					d = u'.'

				dq = d = remove_trailing_dots_in_path_parts(d)

				if DO:
					try:
						if not os.path.exists(d):
							print msg_prfx, colored('Path not found, make dirs:', 'yellow'), d.encode(default_print_encoding)
							os.makedirs(d)

						d += '/'+(
							name
							if ext == old_ext
							else name[ : -len(old_ext)] + ext
						)

						dq = get_unique_clean_path(src_path, d, print_duplicate_count=print_duplicate_count)
						os.rename(src_path, dq)

						if os.path.exists(d):		# <- check that new-moved and possible duplicate both exist
							n_moved += 1
							if arg_print_full_path:
								print info_prfx, src_path.encode(default_print_encoding)
							print dest, colored('<-', 'yellow'), ufull

							print_duplicate_count=True
						else:
							n_back += 1		# <- if renamed "path/name" to the same "path/name(2)", revert
							os.rename(dq, d)	# <- this is simpler than checking equality, symlinks and stuff

							print_duplicate_count=False

					except Exception as exception:
						print msg_prfx, colored('Error renaming:', 'red'), exception
						print_url_groups(url, 'red')

						n_fail += 1
						d_len = len(d)
						dq_len = len(dq)

						print colored('Destination path length:', 'red'), d_len

						try:
							print colored('Destination path:', 'red'), d
						except Exception as exception:
							print colored('Error printing:', 'red'), exception

						if d_len != dq_len:
							print colored('Destination unique path length:', 'red'), dq_len

							try:
								print colored('Destination unique path:', 'red'), dq
							except Exception as exception:
								print colored('Error printing:', 'red'), exception

				elif (
					not d in not_existed
				and	not os.path.exists(d)
				):
					print msg_prfx, colored('Path not found:', 'red'), d.encode(default_print_encoding)
					not_existed.append(d)
				break

		# unknown filetypes, group into subfolders by ID, for pixiv multipages and such:

		else:
			d = None

			for p in pat_sub:
				d = None

				if not p:
					continue

				path_match = name_match = subdir = None
				pat_match_path = p.get('match_dir')

				if pat_match_path:
					path_match = re.search(pat_match_path, path)

					if not path_match:
						continue

				pat_match_name = p.get('match')

				if pat_match_name:
					name_match = re.search(pat_match_name, name)

					if not name_match:
						continue

				pat_subdir = p.get('subdir')
				pat_dup_ID = p.get('group_by')
				pat_date   = p.get('date')
				pat_next   = p.get('next')

				if name_match:
					if pat_next and not (name_match.expand(pat_next) in names):
						continue

					if pat_dup_ID:
						dup_ID = name_match.expand(pat_dup_ID)

						try:
							dup_stamp = name_match.expand(pat_date)
						except:
							dup_stamp = 'last'

						d = dup_lists_by_ID[dup_ID] if dup_ID in dup_lists_by_ID else None

						if later:
							n_later += 1
							files_to_check_later.append(name)

							if dup_stamp:
								if d:
									if is_type_arr(d) and not dup_stamp in d:
										d.append(dup_stamp)
								else:
									d = dup_lists_by_ID[dup_ID] = {}

								if is_type_dic(d):
									d[name] = dup_stamp or name
							else:
								if d:
									d += '1'	# <- to simply check len() the same way
								else:
									d = dup_lists_by_ID[dup_ID] = '1'

							if TEST:
								lend = len(d.keys() if is_type_dic(d) else d)
								print dup_ID.encode(default_print_encoding), colored('- dup #', 'yellow'), lend, dup_stamp.encode(default_print_encoding)

							continue

						elif not (
							d
						and	len(d.keys() if is_type_dic(d) else d)
						and	(
								(is_type_arr(d) and dup_stamp in d)
							or	(is_type_dic(d) and name      in d)
							)
						):
							continue

					subdir = '/' + (name_match.expand(pat_subdir) if pat_subdir else name_match.group(1)).strip('/')
				elif path_match:
					subdir = '/' + (path_match.expand(pat_subdir) if pat_subdir else path_match.group(1)).strip('/')

				if not subdir:
					continue

				i = len(subdir)
				d = path.rstrip('/')

				while d[-i : ] == subdir:
					d = d[0 : -i]

				d += subdir

				if d == path:
					continue

				break

			move_processed_target(src_path, path, name, d)

	return files_to_check_later if later else None

def run(later=0):
	global n_later, dup_lists_by_ID

	process_dir(get_long_abs_path(u'.'), later)

	if later:
		for i in dup_lists_by_ID:
			d = dup_lists_by_ID[i]

			if is_type_arr(d):
				len_d = len(d)

				if len_d > 1:
					if TEST:
						print colored('ID:', 'yellow'), i
						print len_d, colored('before sort:', 'yellow'), d
				d.sort()
				d.pop(0)		# <- leave alone the earliest at old place
				len_d = len(d)

				if len_d:
					if TEST:
						print len_d, colored('after sort:', 'green'), d
						print
				n_later -= 1

			elif is_type_dic(d):
				len_d = len(d.keys())

				if len_d > 1:
					if TEST:
						print colored('ID:', 'yellow'), i
						print len_d, colored('before sort:', 'yellow'), str(d).replace('u\'', '\nu\'')
						print
				name_0 = stamp_0 = None

				for name in d:
					stamp = d[name]

					if (
						not name_0
					or	not stamp_0
					or	stamp_0 > stamp
					or	(stamp_0 == stamp and name_0 > name)
					):
						name_0 = name
						stamp_0 = stamp
				d.pop(name_0)		# <- leave alone the first by name of the earliest ones
				len_d = len(d.keys())

				if len_d:
					if TEST:
						print len_d, colored('after sort:', 'green'), str(d).replace('u\'', '\nu\'')
						print
				n_later -= 1

			elif TEST:
				print colored('%d:' % len(d), 'yellow'), d

	a = []
	n = [
		[n_i	,	'checks']
	,	[n_matched,	'matches']
	,	[n_moved,	colored('moved', 'green')]
	,	[n_later,	colored('later', 'cyan')]
	,	[n_fail,	colored('failed', 'red')]
	,	[n_back,	colored('back', 'yellow')]
	,	[n_max_len,	'max name length']
	]
	for i in n:
		if i[0] > 0:
			a.append(str(i[0])+' '+i[1])

	print msg_prfx, colored('Result:', 'green'), (', '.join(a) if len(a) > 0 else 'no files matched.')

	return n_later if DO else 0

run(1) #and run(0)
