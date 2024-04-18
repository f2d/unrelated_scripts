#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Python 2 or 3 should work.

# - Help screen shown on demand or without arguments --------------------------

def print_help():
	self_name = os.path.basename(__file__)

	help_text_lines = [
		''
	,	colored('* Description:', 'yellow')
	,	'	Save some files from a tar file into a new tar file, optionaly compressed.'
	,	''
	,	colored('* Usage:', 'yellow')
	,	'	{0}'
		+	colored(' <source> <dest> <mask>', 'cyan')
		+	colored(' [<mask>] [!<mask>] [...]', 'magenta')
# TODO:	,	'\n\t\t'.join([
# TODO:			'	{0}'
# TODO:			+	colored(' --save-file=<dest1> --include-if-name=<mask1>', 'cyan')
# TODO:			+	colored(' --read-file=<source1>', 'cyan')
# TODO:		,		colored(' [--read-file=<source2>]', 'magenta')
# TODO:			+	colored(' [--save-file=<dest2> [--include-if-name=<mask2>]', 'magenta')
# TODO:		,		colored(' [...]', 'magenta')
# TODO:		])
	,	''
	,	colored('<source>', 'cyan') + ': path to file to read.'
	,	colored('<dest>', 'cyan') + ':   path to file to write. If equals "TEST", do not write.'
	,	colored('<mask>', 'cyan') + ':   include files with name matching any of these masks.'
	,	colored('!', 'magenta') + colored('<mask>', 'cyan') + ':  exclude files matching any of these masks.'
# TODO:	,	colored('--include-if-name=',       'magenta') + colored('<mask>', 'cyan') + ' ' +
# TODO:		colored('--include-if-content=',    'magenta') + colored('<mask>', 'cyan') + ' ' +
# TODO:		colored('--include-content-lines=', 'magenta') + colored('<mask>', 'cyan')
# TODO:	,	colored('--exclude-if-name=',       'magenta') + colored('<mask>', 'cyan') + ' ' +
# TODO:		colored('--exclude-if-content=',    'magenta') + colored('<mask>', 'cyan') + ' ' +
# TODO:		colored('--exclude-content-lines=', 'magenta') + colored('<mask>', 'cyan')
# TODO:	,	colored('--list-file=', 'magenta') + colored('<path>', 'cyan') + ': text file with additional list of prefixed one-line arguments.'
# TODO:	,	colored('--read-file=', 'magenta') + colored('<path>', 'cyan') + ': archive file to read, in given order.'
# TODO:	,	colored('--save-file=', 'magenta') + colored('<path>', 'cyan') + ': archive file to write, associated with all masks after it until the next save file.'
	,	''
	,	'	At least one source and destination are required.'
# TODO:	,	'	There may be any number of source, destination, list file and/or mask arguments.'
# TODO:	,	'	Unprefixed arguments on fixed positions are only allowed in the command line, for simple cases and backward compatibility.'
# TODO:	,	'	Unprefixed lines in list files are ignored and may be used as comments.'
# TODO:	,	'	Lines in list files have the same format as arguments, but only one per line, with no quotes or escaping, and dashed prefixes are required.'
# TODO:	,	''
	,	'	All masks are checked in given order, include or exclude is decided by the last matched mask.'
# TODO:	,	'	First all masks are checked to decide on inclusion of an archived file itself.'
# TODO:	,	'	Then separately decide on each file content line.'
# TODO:	,	'	If file is included and content is filtered, but no lines in result, then file is not added.'
# TODO:	,	'	If only inclusion masks are defined, then exclude all else, and vice versa.'
# TODO:	,	'	All source files are read in given order, defining order of included archived files in result.'
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
	,	'	Regular expressions may be used to match any special characters like dash, = or !.'
	,	'	Regular expressions may need escape for Windows cmd like this:'
	,	colored('		"!/^^/*(lib^|opt^|root^|usr^|var^|srv)(/^|$)/i"', 'cyan')
	,	''
	,	'	Which is interpreted as this:'
	,	colored('		"!/^/*(lib|opt|root|usr|var|srv)(/|$)/i"', 'cyan')
	,	''
	,	'	Supported source/destination compression modes: ' + ', '.join(sorted(compression_modes)) + '.'
	,	''
	,	colored('* Examples:', 'yellow')
	,	'	{0} old.tar TEST "*.txt"'
	,	'	{0} old.tar.gz new.tar.bz2 "!*.txt" "root/sub/*.txt"'
	,	'	{0} ./old.tar.xz /tmp/new.tar "!/^var/run.*$/i"'
# TODO:	,	'	{0} --read-file=old.tar --save-file=1.tar "--include-if-name=1.*" --save-file=2.tar "--include-if-name=2.*"'
# TODO:	,	'	{0} --list-file=arg_list.txt'
	]

	print('\n'.join(help_text_lines).format(self_name))

# - Dependencies --------------------------------------------------------------

import fnmatch, io, re, os, sys, tarfile, traceback

# Use colored text if available:
try:
	from termcolor import colored, cprint
	import colorama

	colorama.init()

except ImportError:
	def colored(*list_args, **keyword_args): return list_args[0]
	def cprint (*list_args, **keyword_args): print (list_args[0])

# - Configuration and defaults ------------------------------------------------

print_encoding = sys.getfilesystemencoding() or 'utf-8'
path_encoding = 'utf-8'

compression_modes = ['gz', 'bz2', 'xz']
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

reg_type = type(re.compile('.'))
str_type = type('')
uni_type = type(u'')

# - Utility functions ---------------------------------------------------------

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

# - Main job function ---------------------------------------------------------

def run_batch_repack(argv):

# - Show help and exit --------------------------------------------------------

	argc = len(argv)

	if argc < 2:
		print_help()

		return 1

# - Check arguments -----------------------------------------------------------

	old_path = argv[0]
	new_path = argv[1]

	# https://stackoverflow.com/questions/28583565/str-object-has-no-attribute-decode-python-3-error#comment85846909_28583969
	try:
		old_path = old_path.decode(path_encoding)
		new_path = new_path.decode(path_encoding)

	except AttributeError:
		pass

	old_path = old_path.replace('\\', '/')
	new_path = new_path.replace('\\', '/')

	if old_path == new_path:
		print('')
		cprint('Error: Source path equals destination.', 'red')

		return 11

	TEST = True if new_path == 'TEST' else False

	include_by_default = True

	criteria = []

	for arg in argv[2 : ]:
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

					return 12

			criteria.append({
				'include_if': inclusive
			,	'pattern': x
			,	'arg': arg
			})

	if not len(criteria):
		print('')
		cprint('Warning: No criteria to match. All files will be copied.', 'yellow')

		criteria = None

# - Open archive files --------------------------------------------------------

	old_file = get_open_tarfile(old_path, 'r')

	if not old_file:
		print('')
		print_with_colored_prefix('Error: Could not open source file to read:', old_path, 'red')

		return 21

	if not TEST:
		new_file = get_open_tarfile(new_path, 'w')

		if not new_file:
			print('')
			print_with_colored_prefix('Error: Could not open destination file to write:', new_path, 'red')

			return 22

	print_with_colored_prefix('From:    ', old_path.encode(print_encoding))
	print_with_colored_prefix('To:      ', new_path.encode(print_encoding))
	print_with_colored_prefix('Matching:', ', '.join([x['arg'] for x in criteria]).encode(print_encoding) if criteria else '*')

	count_old_folders = 0
	count_old_files = 0
	count_old_links = 0
	count_old_members = 0

	count_added_folders = 0
	count_added_files = 0
	count_added_links = 0
	count_added_members = 0

	count_matching_names = 0
	count_skipped_by_error = 0

	skip_log = None

# - Iterate archived files ----------------------------------------------------

	while True:
		member = old_file.next()

		if member is None:
			break

		count_old_members += 1

		if not isinstance(member, tarfile.TarInfo):
			print_with_colored_prefix('Skipped not TarInfo:', member, 'yellow')

			continue

		included = include_by_default
		is_folder = member.isdir()
		is_file = member.isfile()
		is_link = member.islnk() or member.issym()

		if is_folder: count_old_folders += 1
		elif is_file: count_old_files += 1
		elif is_link: count_old_links += 1

		if criteria:
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
			count_matching_names += 1

			try:
				print(member.name)

			except (UnicodeEncodeError, UnicodeDecodeError):
				try:
					print(member.name.decode(print_encoding))

				except (UnicodeEncodeError, UnicodeDecodeError):
					try:
						print(member.name.encode(print_encoding))

					except (UnicodeEncodeError, UnicodeDecodeError):

						cprint('<# Unprintable file path - {} #>'.format(count_old_members), 'red')

			if not TEST:
				try:
					if is_link or is_folder:
						extracted_file = member
					else:
						extracted_file = old_file.extractfile(member)

					if extracted_file:
						new_file.addfile(member, extracted_file)
						count_added_members += 1

						if is_folder: count_added_folders += 1
						elif is_file: count_added_files += 1
						elif is_link: count_added_links += 1

				except (KeyError, UnicodeEncodeError, UnicodeDecodeError):
					traceback.print_exc()

					count_skipped_by_error += 1

					if not skip_log:
						skip_log = io.open(new_path + '_skip.log', 'a', encoding=path_encoding)

					try:
						skip_log.write(member.name + u'\n')

					except (UnicodeEncodeError, UnicodeDecodeError):
						try:
							skip_log.write(member.name.decode(path_encoding) + u'\n')

						except (UnicodeEncodeError, UnicodeDecodeError):
							try:
								skip_log.write(member.name.encode(path_encoding) + u'\n')

							except (UnicodeEncodeError, UnicodeDecodeError):

								skip_log.write(u'<# Unwritable file path - {} #>\n'.format(count_old_members))

# - Result summary ------------------------------------------------------------

	old_file.close()

	count_old_other = (
		count_old_members
	-	count_old_folders
	-	count_old_files
	-	count_old_links
	)

	count_added_other = (
		count_added_members
	-	count_added_folders
	-	count_added_files
	-	count_added_links
	)

	print('')
	print_with_colored_prefix('Found in old archive:', (', '.join(filter(None, [
		'{} folders'.format(count_old_folders) if count_old_folders else None
	,	'{} files'.format(count_old_files) if count_old_files else None
	,	'{} links'.format(count_old_links) if count_old_links else None
	,	'{} other'.format(count_old_other) if count_old_other else None
	,	'{} matching names'.format(count_matching_names) if count_matching_names else None
	])) or 'nothing') + '.', 'yellow')

	if count_added_members > 0:
		print_with_colored_prefix('Added to new archive:', (', '.join(filter(None, [
			'{} folders'.format(count_added_folders) if count_added_folders else None
		,	'{} files'.format(count_added_files) if count_added_files else None
		,	'{} links'.format(count_added_links) if count_added_links else None
		,	'{} other'.format(count_added_other) if count_added_other else None
		])) or 'nothing') + '.', 'green')

	if not TEST:
		new_file.close()

		if skip_log:
			skip_log.close()

		if count_skipped_by_error > 0:
			print_with_colored_prefix('Skipped', '{} files due to errors, see log.'.format(count_skipped_by_error), 'cyan')

	return 0 if count_added_members > 0 else -1

# - Run from commandline, when not imported as module -------------------------

if __name__ == '__main__':
	sys.exit(run_batch_repack(sys.argv[1 : ]))

# - End -----------------------------------------------------------------------
