#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Python 2 or 3 should work.

import fnmatch, io, re, os, sys, tarfile, traceback

# Use colored text if available:
try:
	from termcolor import colored, cprint
	import colorama

	colorama.init()

except ImportError:
	def colored(*list_args, **keyword_args): return list_args[0]
	def cprint(*list_args, **keyword_args): print(list_args[0])

# - Configuration and defaults ------------------------------------------------

argc = len(sys.argv)

compression_modes = ['gz', 'bz2', 'xz']
path_enc = 'utf-8'
regex_delim = '/'
regex_mod_args = 'iLmsux'
regex_mod_flags = [
	re.I # ignore case
,	re.L # locale dependent)
,	re.M # multi-line
,	re.S # dot matches all
,	re.U # Unicode dependent
,	re.X # verbose
]

if argc < 4:
	self_name = os.path.basename(__file__)

	help_text_lines = [
		''
	,	colored('* Description:', 'yellow')
	,	'	Save some files from a tar file into a new tar file.'
	,	''
	,	colored('* Usage:', 'yellow')
	,	'	%s'
		+		colored(' <source> <dest> <mask>', 'cyan')
		+		colored(' [<mask>] [<!mask>] ...', 'magenta')
	,	''
	,	colored('<source>', 'cyan') + ': path to file to read.'
	,	colored('<dest>', 'cyan') + ': path to file to write. If equals "TEST", do not write.'
	,	colored('<mask>', 'cyan') + ': wildcard to include files, whose names matches any of these.'
	,	colored('<!mask>', 'cyan') + ': wildcard to exclude files, whose names matches any of these.'
	,	''
	,	'	Source, dest and at least one mask are required.'
	,	'	All masks are checked and the last met hit (include/exclude) wins.'
	,	''
	,	'	Mask can be a:'
	,	'	- full pathname (never starts with a slash)'
	,	'	- glob pattern: '
		+		colored('*path/name?.*', 'cyan')
	,	'	- regular expression: '
		+		colored(regex_delim + '<pattern>' + regex_delim, 'cyan')
		+		'[modifiers:'
		+			colored(regex_mod_args, 'cyan')
		+		']'
	,	''
	,	'	Regular expressions may need escape for Windows cmd like this:'
	,	colored('		"!/^^/*(lib^|opt^|root^|usr^|var^|srv)(/^|$)/i"', 'cyan')
	,	''
	,	'	Which is interpreted as this:'
	,	colored('		"!/^/*(lib|opt|root|usr|var|srv)(/|$)/i"', 'cyan')
	,	''
	,	colored('* Examples:', 'yellow')
	,	'	%s old.tar TEST *.txt'
	,	'	%s old.tar.gz new.tar.bz2 !*.txt "root/sub/*.txt"'
	,	'	%s ./old.tar.xz /tmp/new.tar "!/^var/run.*$/i"'
	]

	print('\n'.join(help_text_lines).replace('%s', self_name))

	sys.exit()

reg_type = type(re.compile('.'))
str_type = type('')
uni_type = type(u'')

# - Declare functions ---------------------------------------------------------

def is_type_reg(v): return isinstance(v, reg_type)
def is_type_str(v): return isinstance(v, str_type) or isinstance(v, uni_type)

def print_with_colored_prefix(prefix, value, color=None):
	print('{} {}'.format(colored(prefix, color or 'yellow'), value))

def get_open_tarfile(path, mode):

	for compression_mode in compression_modes:
		if path[-len(compression_mode)-1 : ] == '.' + compression_mode:
			mode += ':' + compression_mode
			break

	try:
		opened_file = tarfile.open(path, mode)
		opened_file.dereference = False

		return opened_file
	except:
		traceback.print_exc()

	return None

# - Check command line arguments ----------------------------------------------

old_path = sys.argv[1]
new_path = sys.argv[2]

# https://stackoverflow.com/questions/28583565/str-object-has-no-attribute-decode-python-3-error#comment85846909_28583969
try:
	old_path = old_path.decode(path_enc)
	new_path = new_path.decode(path_enc)
except AttributeError:
	pass

old_path = old_path.replace('\\', '/')
new_path = new_path.replace('\\', '/')

TEST = True if new_path == 'TEST' else False

include_by_default = True

criteria = []

for arg in sys.argv[3:]:
	if len(arg.strip('./*?!"')) > 0:
		x = arg.replace('\\', '/')

		inclusive = (x[0] != '!')

		if inclusive:
			include_by_default = False
		else:
			x = x[1 : ]

		if x[0] == regex_delim:
			regex_delim_pos = x.rfind(regex_delim)
			regex_pat = x[1 : regex_delim_pos]

			if len(regex_pat) == 0:
				continue

			regex_mod = x[regex_delim_pos + 1 : ]

			n = len(regex_mod)
			regex_flags = 0

			if n > 0:
				for i in range(n):
					j = regex_mod_args.find(regex_mod[i])

					if j >= 0:
						regex_flags |= regex_mod_flags[i]

			try:
				x = re.compile(regex_pat, regex_flags)

			except re.error:
				traceback.print_exc()
				print('')
				print_with_colored_prefix('Error in mask expression:', x, 'red')

				sys.exit(4)

		criteria.append({
			'include_if': inclusive
		,	'pattern': x
		,	'arg': arg
		})

if not len(criteria):
	print('')
	cprint('Error: No parts to match.', 'red')

	sys.exit(1)

# - Open archive files --------------------------------------------------------

old_file = get_open_tarfile(old_path, 'r')

if not old_file:
	print('')
	print_with_colored_prefix('Error: Could not open source file to read:', old_path, 'red')

	sys.exit(2)

if not TEST:
	new_file = get_open_tarfile(new_path, 'w')

	if not new_file:
		print('')
		print_with_colored_prefix('Error: Could not open destination file to write:', new_path, 'red')

		sys.exit(3)

print_with_colored_prefix('From:    ', old_path.encode(path_enc))
print_with_colored_prefix('To:      ', new_path.encode(path_enc))
print_with_colored_prefix('Matching:', ', '.join(map(lambda x: x['arg'], criteria)).encode(path_enc))

count_members = 0
count_members_added = 0
count_members_matching = 0
count_skipped_by_error = 0
skip_log = None

# - Iterate archived files ----------------------------------------------------

while True:
	member = old_file.next()

	if member is None:
		break

# for member in old_file.getmembers():
	count_members += 1
	included = include_by_default

	for x in criteria:
		matched = False
		pattern = x['pattern']

		if is_type_str(pattern):
			matched = fnmatch.fnmatch(member.name, pattern)

		elif is_type_reg(pattern):
			matched = re.search(pattern, member.name)

		if matched:
			included = x['include_if']

	if included:
		count_members_matching += 1

		try:
			print(member.name)

		except (UnicodeEncodeError, UnicodeDecodeError):
			try:
				print(member.name.decode(path_enc))

			except (UnicodeEncodeError, UnicodeDecodeError):
				try:
					print(member.name.encode(path_enc))

				except (UnicodeEncodeError, UnicodeDecodeError):

					cprint('<# Unprintable file path - {} #>'.format(count_members), 'red')

		if not TEST:
			try:
				if (
					member.type == tarfile.LNKTYPE
				or	member.type == tarfile.SYMTYPE
				):
					extracted_file = member
				else:
					extracted_file = old_file.extractfile(member)

				if extracted_file:
					new_file.addfile(member, extracted_file)
					count_members_added += 1

			except (KeyError, UnicodeEncodeError, UnicodeDecodeError):
				traceback.print_exc()

				count_skipped_by_error += 1

				if not skip_log:
					skip_log = io.open(new_path + '_skip.log', 'a', encoding=path_enc)

				try:
					skip_log.write(member.name + u'\n')

				except (UnicodeEncodeError, UnicodeDecodeError):
					try:
						skip_log.write(member.name.decode(path_enc) + u'\n')

					except (UnicodeEncodeError, UnicodeDecodeError):
						try:
							skip_log.write(member.name.encode(path_enc) + u'\n')

						except (UnicodeEncodeError, UnicodeDecodeError):

							skip_log.write(u'<# Unwritable file path - {} #>\n'.format(count_members))

# - Result summary ------------------------------------------------------------

old_file.close()

print('')
print_with_colored_prefix('Found', '{} files in old archive, with {} matching.'.format(count_members, count_members_matching), 'yellow')

if count_members_added > 0:
	print_with_colored_prefix('Added', '{} files to new archive.'.format(count_members_added), 'green')

if not TEST:
	new_file.close()

	if skip_log:
		skip_log.close()

	if count_skipped_by_error > 0:
		print_with_colored_prefix('Skipped', '{} files due to errors, see log.'.format(count_skipped_by_error), 'cyan')

# - End -----------------------------------------------------------------------
