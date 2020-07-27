#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import fnmatch, io, re, os, sys, tarfile, traceback

argc = len(sys.argv)

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
	,	'* Description:'
	,	'	Save some files from a tar file into a new tar file.'
	,	''
	,	'* Usage:'
	,	'	%s <source> <dest> <mask> [<mask>] [<!mask>] [TEST] ...'
	,	''
	,	'<source>: path to file to read.'
	,	'<dest>: path to file to write. If "TEST", do not write.'
	,	'<mask>: wildcard to include files, whose names matches any of these.'
	,	'<!mask>: wildcard to exclude files, whose names matches any of these.'
	,	''
	,	'	All masks are checked and the last met hit (include/exclude) wins.'
	,	''
	,	'	Mask can be a:'
	,	'	- full pathname (never starts with a slash)'
	,	'	- glob pattern: *path/name?.*'
	,	'	- regular expression: ' + regex_delim + '<pattern>' + regex_delim + '[modifiers:' + regex_mod_args + ']'
	,	''
	,	'* Examples:'
	,	'	%s old.tar TEST *.txt'
	,	'	%s old.tar new.tar !*.txt "root/sub/*.txt"'
	,	'	%s ./old.tar /tmp/new.tar "!/^var/run.*$/i"'
	]

	print('\n'.join(help_text_lines).replace('%s', self_name))

	sys.exit()

reg_type = None
str_type = type('')
uni_type = type(u'')

def is_type_reg(v): return isinstance(v, reg_type)
def is_type_str(v): return isinstance(v, str_type) or isinstance(v, uni_type)

path_enc = 'utf-8'

old_path = sys.argv[1].decode(path_enc).replace('\\', '/')
new_path = sys.argv[2].decode(path_enc).replace('\\', '/')

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

				if not reg_type:
					reg_type = type(x)
			except:
				continue

		criteria.append({
			'include_if': inclusive
		,	'pattern': x
		,	'arg': arg
		})

if not len(criteria):
	print 'Error: No parts to match.'
	sys.exit(1)

try: old_file = tarfile.open(old_path, 'r')
except: old_file = None

if not old_file:
	print 'Error: Could not open source file.'
	sys.exit(2)

if not TEST:
	try: new_file = tarfile.open(new_path, 'w')
	except: new_file = None

	if not new_file:
		print 'Error: Could not open destination file.'
		sys.exit(3)

print 'From:    ', old_path.encode(path_enc)
print 'To:      ', new_path.encode(path_enc)
print 'Matching:', ', '.join(map(lambda x: x['arg'], criteria)).encode(path_enc)

count_members = 0
count_skipped_by_error = 0
skip_log = None

for member in old_file.getmembers():
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
		try:
			print member.name
		except:
			try:
				print member.name.decode(path_enc)
			except:
				try:
					print member.name.encode(path_enc)
				except:
					print '<# Unprintable file path - %d #>' % count_members

		if not TEST:
			try:
				new_file.addfile(member, old_file.extractfile(member.name))
			except:
				traceback.print_exc()

				count_skipped_by_error += 1

				if not skip_log:
					skip_log = io.open(new_path + '_skip.log', 'a', encoding=path_enc)

				try:
					skip_log.write(member.name + u'\n')
				except:
					try:
						skip_log.write(member.name.decode(path_enc) + u'\n')
					except:
						try:
							skip_log.write(member.name.encode(path_enc) + u'\n')
						except:
							skip_log.write(u'<# Unwritable file path - %d #>\n' % count_skipped_by_error)

				# print >>skip_log, member.name

	#if TEST:
	#	if not included: print TEST, 'Skipped:', member.name.encode(path_enc)
	#	TEST += 1
	#	if TEST > 1234: break

old_file.close()

if not TEST:
	new_file.close()

	if skip_log:
		skip_log.close()

	if count_skipped_by_error > 0:
		print 'Skipped', count_skipped_by_error, 'files due to errors, see log.'
