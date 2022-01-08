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
	def cprint(*list_args, **keyword_args): print(list_args[0])

from r_config import get_rei, re_ix, re_iux
from r_config import default_print_encoding, default_name_cut_length, default_read_bytes
from r_config import dest_root, dest_root_by_ext, dest_root_yt
from r_config import ext_web, ext_web_remap, ext_web_read_bytes, ext_web_index_file, sites

arg_name_cut = 'cut'

args = sys.argv
argc = len(args)

arg_flags = args[1] if argc > 1 else ''
other_args = args[2:] if argc > 2 else []

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
	,	'	t: for test output only (don\'t apply changes)'
	,	'	e: turn warnings (just printed) into exceptions (stop the script if uncatched) for debug'
	,	'	f: when cutting, check length of full path instead of only name'
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
	,	'	y:   move any leftover files into subdir named by mod-time year'
	,	'	m:   subdir by month'
	,	'	d:   subdir by day'
	,	'	ym:  subdir by year-month'
	,	'	ymd: subdir by year-month-day'
	,	'		Notes: may be combined,'
	,	'		interpreted as switches (on/off),'
	,	'		resulting always in this order: y/ym/m/ymd/d'
	,	'	dir: move dirs into subdir by mod-time too'
	,	''
	,	'* Examples:'
	,	'	%s rwb'
	,	'	%s tfo '+arg_name_cut+'234'
	,	'	%s o y ym ymd dir'
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

j = len(arg_name_cut)
if arg_name_cut in other_args:
	arg_len = default_name_cut_length			# <- pass 'cut' or 'cut123' for longname cutting tool; excludes move to folders
else:
	arg_len = 0
	for a in other_args:
		if a[0:j] == arg_name_cut:
			arg_len = int(a[j:])
			break

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
	|	<!--\s+Page\s+saved\s+with\s+SingleFileZ?\s+url:\s+
	|	<a\s+id="savepage-pageinfo-bar-link"\s+href=[^<>\w\r\n]*
	|	<base\s+href=[^<>\w\r\n]*
	)
)
(?P<URL>
	(?P<Protocol>[\w-]+)
	:+/*
	(?P<Proxy>
		u
	#	(?P<ProxyPort>:[^:/?#\r\n]+)?
		(?:[:](?P<ProxyPort>\d+))?
		/+[?]*
		(?P<ProxyProtocol>ftps?|https?)
		:*/+
	)?
	(?P<DomainPath>
		(?P<DomainPort>
			(?P<Domain>[^"':/?&=\#\s\r\n]+)?
		#	(?P<Port>:\d+)?
			(?:[:](?P<Port>\d+))?
		)
		(?P<Path>
			/+
		#	(?:
		#		(?P<PathBeforeQuery>[^"?\#\s\r\n]*)
		#		[?]
		#	)?
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

info_prfx = '\t'
msg_prfx = '\n-\t'

def is_type_str(s):
	return isinstance(s, s_type) or isinstance(s, u_type)

def dumpclean(obj):
	if type(obj) == dict:
		for k, v in obj.items():
			if hasattr(v, '__iter__'):
				print k
				dumpclean(v)
			else: print k, ':', v
	elif type(obj) == list:
		for v in obj:
			if hasattr(v, '__iter__'):
				dumpclean(v)
			else: print v
	else: print obj

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

def get_file_name(path):
	if path.find('/') >= 0: path = path.rsplit('/', 1)[1]
	return path

def get_file_ext(path):
	if path.find('/') >= 0: path = path.rsplit('/', 1)[1]
	if path.find('.') >= 0: path = path.rsplit('.', 1)[1]
	return path.lower()

def read_zip_file(name, return_source_html=False):
	file_ext = get_file_ext(name)

	for ext, index_file_name in ext_web_index_file.items():
		if ext != file_ext:
			continue

		try:
			zip_file = zipfile.ZipFile(name, 'r')

			for path in zip_file.namelist():
				name = path.rsplit('/', 1)[-1:][0]
				if name == index_file_name:
					if TEST:
						print info_prfx, colored('MAFF/ZIP test, meta file:', 'yellow'), path, '\n'

					result = zip_file.read(path)			# <- return source URL

					if return_source_html:
						s = re.search(pat_idx, result)
						if s and s.group(1):
							path = path[:-len(name)] + s.group(1)
							if TEST:
								print info_prfx, colored('MAFF/ZIP test, content file:', 'yellow'), path, '\n'

							result = zip_file.read(path)	# <- return source HTML
					return result

		except zipfile.BadZipfile as exception:
			if TEST:
				print msg_prfx, colored('MAFF/ZIP test, cannot read file as ZIP:', 'yellow'), name
				print exception


def read_file_or_part(name, size=0):
	global n_fail

	result = ''

	try:
		result = read_zip_file(name, return_source_html=(not size))

		if result is None:
			f = open(name)
			result = f.read(size) if size else f.read()
			f.close()

	except Exception as exception:
		n_fail += 1
		print msg_prfx, colored('Path length:', 'yellow'), len(name)
		print exception

	return result

def get_formatted_modtime(src_path, format):
	return datetime.datetime.fromtimestamp(os.path.getmtime(src_path)).strftime(format)

def remove_trailing_dots_in_path_parts(path):
	return '/'.join(
		part if part == '.' or part == '..'
		else part.rstrip('.')
		for part in normalize_slashes(path).split('/')
	)

def get_unique_clean_path(src_path, dest_path, print_duplicate_count=True):
	global unprinted_duplicate_count

	try_count = 0
	dest_path = remove_trailing_dots_in_path_parts(dest_path)

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
	return os.rename(src_path, get_unique_clean_path(src_path, dest_path))

def meet(obj, criteria):
	try:
		return True if (
			(obj is criteria) or
			(obj == criteria) or (
				(is_type_str(obj	) or obj	) and
				(is_type_str(criteria	) or criteria	) and (
					criteria.match(obj)		if isinstance(criteria, r_type) else
					(obj in criteria)		if isinstance(criteria, a_type) else
					(obj.find(criteria) >= 0)	if is_type_str(criteria) else
					None
				)
			)
		) else False

	except UnicodeWarning as exception:
		print msg_prfx, colored('Exception:', 'red'), exception
		print msg_prfx, colored('While comparing:', 'yellow'), obj
		print msg_prfx, colored('To criteria:', 'yellow'), criteria

	return False

def get_sub(subj, rules):
	if not rules:
		return None

	if is_type_str(rules):
		return [rules, '']

	name, meeting, board = subj

	for r in rules:
		if not r:
			continue

		if is_type_str(r):
			return [r, '']

		if isinstance(r, a_type):
			if len(r) > 1:
				r0 = isinstance(r[0], r_type)
				pattern = r[0 if r0 else 1]
				met = None
				for me in meeting:
					if meet(me, pattern):
						met = me
						break
				if met is not None:
					if r[0] is None:
						return None

					dsub = rename = ''

				# grab subfolder from URL parts:
					if r0:
						r1 = r[1]
						r1a = r1 if isinstance(r1, a_type) else [r1]
						for r1 in r1a:
							try:
								if r1 and isinstance(r1, s_type):
									dsub = (
										re
										.search(r[0], met)
										.expand(r1)
									)
									break
							except:
								continue
					else:
				# specific rules:
						dsub = r[0]
				# full filename replacement:
						if len(r) > 3 and isinstance(r[2], r_type):
							rename = re.sub(r[2], r[3], name)
				# only append item ID to filename, if not yet:
						elif len(r) > 2 and isinstance(r[1], r_type):
							suffix = (
								re
								.search(r[1], met)
								.expand(r[2])
							)
							if name.find(suffix) < 0:
								rename = (suffix+'.').join(name.rsplit('.', 1))
						if TEST and rename:
							print rename

					return [dsub, rename]

			elif board:
				return [r[0], '']

	return None

def print_name(name, prefix='', extra_line=True):
	if extra_line:
		print

	if prefix:
		prefix = '%s ' % prefix
	else:
		prefix = ''

	for enc in ['utf-8', 'unicode-escape']:
		cprint('{0}name in {1}:'.format(prefix, enc), 'yellow')
		print name.encode(enc)

def move_processed_target(src, path, name, dest_dir=None):
	global n_fail, n_moved

	if not dest_dir and arg_subdir_modtime_format:
		dest_dir = path.rstrip('/') + '/' + get_formatted_modtime(src, arg_subdir_modtime_format).strip('/')

	if dest_dir:
		print dest_dir.encode(default_print_encoding), colored('<-', 'yellow'), name.encode(default_print_encoding)

		if DO:
			dest = get_unique_clean_path(src, dest_dir+'/'+name)

			try:
				if not os.path.exists(dest_dir):
					print colored('Path not found, make dirs:', 'yellow'), dest_dir.encode(default_print_encoding)
					os.makedirs(dest_dir)

				os.rename(src, dest)
				n_moved += 1

			except Exception as exception:
				n_fail += 1
				print msg_prfx, colored('Path length:', 'yellow'), len(src), colored('to', 'yellow'), len(dest)
				print exception

def process_dir(path, later=0):
	global n_i, n_fail, n_matched, n_moved, n_back, n_later, n_max_len
	global not_existed, dup_lists_by_ID
	global print_duplicate_count

	names = os.listdir(path)

	for name in names:
		n_i += 1
		src = path+'/'+name
		if os.path.isdir(src):
			if arg_recurse_into_subdirs:
				if TEST and arg_print_full_path:
					print_name(name, 'Dir')
				process_dir(src, later)

			if arg_move_dirs_to_subdir_by_modtime:
				move_processed_target(src, path, name)

			continue

		if TEST and arg_print_full_path:
			print_name(name, 'File')

		# optionally cut long names before anything else:

		if arg_len:
			src_path = os.path.abspath(src) if arg_cut_full_path else name
			src_len = len(src_path)

			if src_len > arg_len:
				n_matched += 1
				if n_max_len < src_len:
					n_max_len = src_len

				ext = '(...).' + get_file_ext(name)
				dest_path = src_path[:arg_len - len(ext)].rstrip() + ext
				dest_path = get_unique_clean_path(src_path, dest_path)
				dest_show = (dest_path if arg_print_full_path else get_file_name(dest_path))

				print
				print colored('Cut from', 'yellow'), src_len, (src_path if arg_print_full_path else name).encode(default_print_encoding)
				print colored('Cut to', 'yellow'), len(dest_show), dest_show.encode(default_print_encoding)

				if DO:
					os.rename(src, dest_path)

					name = get_file_name(dest_path)
					src = path+'/'+name

					n_moved += 1

		ext = old_ext = get_file_ext(name)
		ext = ext_web_remap.get(ext, ext)
		d = ''

		if arg_move_types_by_ext and ext in dest_root_by_ext:
			if later:
				n_later += 1
			else:
				d = dest_root_by_ext[ext]

				if isinstance(d, a_type):
					for d_i in d:
						if isinstance(d_i, d_type):
							test = d_i.get('match_name')
							if test and not meet(name, test):
								continue

							d = d_i.get('dest_path') or dest_root
							break
						else:
							d = d_i
							break

				if not is_type_str(d):
					continue

				print d.encode(default_print_encoding), colored('<-', 'yellow'), name.encode(default_print_encoding)

				if DO and os.path.exists(src) and os.path.isdir(d):
					rename_to_unique_clean_path(src, d+'/'+name)
					n_moved += 1

		elif ext in ext_path_inside:
			n_matched += 1
			read_bytes = ext_web_read_bytes.get(ext, default_read_bytes)

			if ext == 'html':
				url = None
				max_found_url_length = 0

				for each_found_url in re.finditer(pat_url, read_file_or_part(src, read_bytes)):
					url_length = len(each_found_url.group('URL'))

					if max_found_url_length < url_length:
						max_found_url_length = url_length

						url = each_found_url
			else:
				url = re.search(pat_url, read_file_or_part(src, read_bytes))

			if url:
				if TEST:
					print_url_groups(url, 'yellow')
			else:
				if TEST:
					print info_prfx, colored('No URL in file:', 'yellow'), src.encode(default_print_encoding)

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

				d = url.group('Protocol')
				domain = ''
				test = s[0]

				if meet(d, test):
					domain = d
				else:
					d = url.group('Domain')
					if not d:
						continue

					dp = url.group('DomainPort')
					if meet(dp+'.', test):	# <- "name." or "name:port." to match exact full name
						domain = d
					else:
						words = reversed(dp.split('.'))
						d = ''
						for i in words:
							d = (i+'.'+d) if d else i
							if meet(d, test):
								domain = d
								break
				if not domain:
					continue

				dest = (s[1] if (len(s) > 1) else domain)		# <- site bak root
				dest += (
					test[0]
					if (isinstance(test, a_type) and dest[-2:] == '//')
					else
					domain
					if (dest[-1:] == '/')
					else ''
				).strip('/:.')+'/'

				if len(s) > 2:
					x = [name, meeting, True if board else False]
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
						print info_prfx, src.encode(default_print_encoding)
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
						page_content = re.sub(pat_ren_mht_linebreak, '', read_file_or_part(src))

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
						child_ext = get_file_ext(child_name)
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
								f = re.sub(pat_ren_src_name, '', child_name[:-f])
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

						dq = get_unique_clean_path(src, d, print_duplicate_count=print_duplicate_count)
						os.rename(src, dq)

						if os.path.exists(d):		# <- check that new-moved and possible duplicate both exist
							n_moved += 1
							if arg_print_full_path:
								print info_prfx, src.encode(default_print_encoding)
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

				elif not d in not_existed and not os.path.exists(d):
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

				pat_match     = p.get('match')
				pat_match_dir = p.get('match_dir')

				s = sd = subdir = None

				if pat_match_dir:
					sd = re.search(pat_match_dir, path)

					if not sd:
						continue

				if pat_match:
					s = re.search(pat_match, name)

					if not s:
						continue

				pat_subdir = p.get('subdir')
				pat_dup_ID = p.get('group_by')
				pat_date   = p.get('date')
				pat_next   = p.get('next')

				if s:
					if pat_next and not (s.expand(pat_next) in names):
						continue

					if pat_dup_ID:
						dup_ID = s.expand(pat_dup_ID)

						try:
							dup_stamp = s.expand(pat_date)
						except:
							dup_stamp = 'last'

						d = dup_lists_by_ID[dup_ID] if dup_ID in dup_lists_by_ID else None
						if later:
							n_later += 1
							if dup_stamp:
								if d:
									if isinstance(d, a_type) and not dup_stamp in d:
										d.append(dup_stamp)
								else:
									d = dup_lists_by_ID[dup_ID] = {}
								if isinstance(d, d_type):
									d[name] = dup_stamp or name
							else:
								if d:
									d += '1'	# <- to simply check len() the same way
								else:
									d = dup_lists_by_ID[dup_ID] = '1'
							if TEST:
								lend = len(d.keys() if isinstance(d, d_type) else d)
								print dup_ID.encode(default_print_encoding), colored('- dup #', 'yellow'), lend, dup_stamp.encode(default_print_encoding)
							continue
						elif not (
							d
						and	len(d.keys() if isinstance(d, d_type) else d)
						and	(
								(isinstance(d, a_type) and dup_stamp in d)
							or	(isinstance(d, d_type) and name in d)
							)
						):
							continue

					subdir = '/' + (s.expand(pat_subdir) if pat_subdir else s.group(1)).strip('/')
				elif sd:
					subdir = '/' + (sd.expand(pat_subdir) if pat_subdir else sd.group(1)).strip('/')

				if not subdir:
					continue

				i = len(subdir)
				d = path.rstrip('/')

				while d[-i:] == subdir:
					d = d[0:-i]

				d += subdir
				if d == path:
					continue

				break

			move_processed_target(src, path, name, d)

def run(later=0):
	global n_later, dup_lists_by_ID

	process_dir(u'.', later)

	if later:
		for i in dup_lists_by_ID:
			d = dup_lists_by_ID[i]

			if isinstance(d, a_type):
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

			elif isinstance(d, d_type):
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

if run(1):
	run()
