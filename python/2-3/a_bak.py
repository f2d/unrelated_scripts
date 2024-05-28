#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Python 2 or 3 should work.

# [v]	TODO: 1) run mod.date updater script first.
# [v]	TODO: 2) per each src name, only make new archive if src mod.date is later than newest old bak.
# [v]	TODO: 3) per each src name, keep N (or none) last old bak archives aside from newly created by this run.
#	TODO: 4) delete latest obsolete old bak archives only after successful creation (to still have some working backup in case of problems).

# - Help screen shown on demand or without arguments --------------------------

def print_help():

	def get_found_mark_for_help(check_value):
		return colored('[v]', 'green') if check_value else colored('[not found]', 'red')

	self_name = os.path.basename(__file__)

	help_text_lines = [
		''
	,	colored('* Description:', 'yellow')
	,	'	Create backup archives for each title - direct subfolder or file in each given source folder.'
	,	'	Optionally keep N old archives per each title.'
	,	'	New archives are created only if source mod.date is later than newest existing archive.'
	,	'	Default source path is current working folder.'
	,	''
	,	colored('* Usage:', 'yellow')
	,	'	{0}'
		+	colored(' [--dest-path=<dir/path>]', 'cyan')
		+	colored(' [--keep-path=<dir/path>]', 'cyan')
		+	colored(' [--keep-num=<Number>]', 'cyan')
		+	colored(' [--src-path=<dir/path>] [<src/dir/path2>] ...', 'magenta')
	,	''
	,	colored('	--dest-path=<dir/path>', 'cyan') + ': Destination path to create new archives. Default: ' + default_new_bak_path
	,	colored('	--keep-path=<dir/path>', 'cyan') + ': Destination path to move old archives. Do not move if omitted.'
	,	''
	,	colored('	-k=<N> --keep=<N> --keep-num=<Number>', 'cyan')
		+	': Number of old archives per each title to keep aside from newly created.'
	,	'		Default: {}'.format(default_number_to_keep)
	,	'		Minimum: 1' # TODO: remove minimum and delete last old only after new creation success
	,	'		Excess archives per each title are deleted before creating new.'
# TODO:	,	'		The latest previous archive is moved or deleted (if set to keep zero) after successfuly creating new.'
	,	''
	,	colored('	-a=<flags> --archive-type=<flags>', 'magenta')
		+	': archive type flags for "a.py", case insensitive.'
	,	'		Default: ' + cmd_arch + ' (fast ZSTD, solid by ext)'
	,	'		These flags are ignored, as caution for accidental input: "d" (delete sources) and all after extra "=".'
	,	'		These flags are always appended: ' + cmd_glue + ' (no GUI, no wait, keep one and named by subfolder + timestamp)'
	,	''
	,	colored('	-r --read-only', 'magenta') + ': show expected updates, do not change anything.'
	,	colored('	-t --test   ', 'magenta') + ': updates folder mod.times and list pending archives, but do not create.'
	,	colored('	-h --help /?', 'magenta') + ': show this help text, do nothing else.'
	,	''
	,	colored('* Examples:', 'yellow')
	,	'	{0} "--dest-path=/dest/path" "--keep-path=/dest/path/keep" --keep-num=1 . "--src-path=../src/path"'
	,	''
	,	colored('* Dependencies:', 'yellow')
	,	'	"t.py" {} is used to update modification dates in the root.'.format(get_found_mark_for_help(run_batch_retime))
	,	'	"a.py" {} is used to call archiver program(s).'             .format(get_found_mark_for_help(run_batch_archiving))
	]

	print('\n'.join(help_text_lines).format(self_name))

# - Dependencies --------------------------------------------------------------

import os, re, sys, json, traceback

# Custom scripts from this folder:
try:  from a import run_batch_archiving
except ImportError: run_batch_archiving = None

try:  from t import run_batch_retime
except ImportError: run_batch_retime = None

# Use colored text if available:
try:
	from termcolor import colored, cprint
	import colorama

	colorama.init()

except ImportError:
	def colored(*list_args, **keyword_args): return list_args[0]
	def cprint (*list_args, **keyword_args): print (list_args[0])

# - Configuration and defaults ------------------------------------------------

default_src_root_path = u'.'
default_new_bak_path = u'..'
default_number_to_keep = 1

cmd_arch = '790e'
cmd_glue = '_kkom;>='

# - Declare functions ---------------------------------------------------------

def print_with_colored_prefix(prefix, value, color=None):

	print('{} {}'.format(colored(prefix, color or 'yellow'), value))

# https://stackoverflow.com/a/3314411
def get_obj_pretty_print(obj):

	try:
		return json.dumps(
			obj.__dict__ if '__dict__' in obj else obj
		,	sort_keys=True
		,	indent=4
		,	default=repr
		).replace(' '*4, '\t')

	except Exception as exception:
		traceback.print_exc()

		return '{}'.format(obj)

def add_to_set_in_dict(dict, key, item):

	if not key in dict:
		dict[key] = set()

	dict[key].add(item)

def is_not_dots(path):

	return len(
		path
		.replace('\\', '')
		.replace('/', '')
		.replace('.', '')
	) > 0

def list_dir_except_dots(path):

	return filter(is_not_dots, os.listdir(path))

# https://stackoverflow.com/a/57968977
def is_dir_empty(path):

	return not next(os.scandir(path), None)

def normalize_slashes(path):

	return path.replace('\\', '/')

def get_file_name(path):

	return normalize_slashes(path).rsplit('/', 1)[-1 : ][0]

def get_bak_src_name(path):

	return (
		get_file_name(path)
		.rsplit('.', 1)[0]
		.rsplit(';_', 1)[0]
	)

# - Main job function ---------------------------------------------------------

def run_backup_batch_archiving(argv):

	argc = len(argv)

# - Show help and exit --------------------------------------------------------

	if (
		argc < 1
	or	'/?' in argv
	or	'-h' in argv
	or	'--help' in argv
	):
		print_help()

		return 1

	if not (
		run_batch_archiving
	and	run_batch_retime
	):
		print_help()

		return 2

# - Check arguments -----------------------------------------------------------

	arg_test = arg_read_only = False
	arg_new_path = arg_old_path = None
	arg_cmd_arch = cmd_arch
	arg_number_to_keep = default_number_to_keep

	src_dirs = []

	for each_arg in argv:

		if '-' == each_arg[0]:
			if '=' in each_arg:
				arg_name, arg_value = each_arg.split('=', 1)
			else:
				arg_name = each_arg
				arg_value = None

			arg_words = list(filter(bool, arg_name.split('-')))
			arg_what = arg_words[0]
			arg_how = arg_words[1] if len(arg_words) > 1 else None

			if (
				arg_what == 't'
			or	arg_what == 'test'
			):
				arg_test = True

				continue

			if (
				arg_what == 'r'
			or (	arg_what == 'read' and arg_how == 'only')
			):
				arg_read_only = True

				continue

			if arg_value and len(arg_value.strip()) > 0:
				if (
					arg_what == 'a'
				or	arg_what == 'archive'
				):
					arg_cmd_arch = arg_value.split('=', 1)[0].lower().replace('d', '')

					continue
				if (
					arg_what == 'k'
				or (	arg_what == 'keep' and (not arg_how or arg_how == 'num'))
				):
					arg_number_to_keep = int(arg_value)

					continue

				if arg_what == 'keep' and arg_how == 'path':
					arg_old_path = arg_value

					continue

				if arg_what == 'dest' and (not arg_how or arg_how == 'path'):
					arg_new_path = arg_value

					continue

				if arg_what == 'src' and (not arg_how or arg_how == 'path'):
					src_dirs.append(arg_value)

					continue

		src_dirs.append(each_arg)

	if not len(src_dirs): src_dirs.append(default_src_root_path)
	if not arg_new_path: arg_new_path = default_new_bak_path
	if not arg_old_path: arg_old_path = arg_new_path

	if arg_read_only or arg_test:
		print('')
		print_with_colored_prefix('arg_test:', arg_test)
		print_with_colored_prefix('arg_read_only:', arg_read_only)
		print_with_colored_prefix('arg_number_to_keep:', arg_number_to_keep)
		print_with_colored_prefix('arg_cmd_arch:', arg_cmd_arch)
		print_with_colored_prefix('arg_new_path:', arg_new_path)
		print_with_colored_prefix('arg_old_path:', arg_old_path)
		print_with_colored_prefix('src_dirs:', src_dirs)
		print('')

# - Do the job ----------------------------------------------------------------

# Update mod.times:

	if arg_read_only:
		arg_test = True
	else:
		run_batch_retime(['abdir'])

	old_files_to_move = set()
	old_files_by_src = {}
	new_archives_count = 0

# Delete oldest extra archives in old keep folder, per source, over specified keep limit:

	def get_file_path_by_name(name):
		return normalize_slashes((
			arg_new_path if name in old_files_to_move else
			arg_old_path
		) + '/' + name)

	def cleanup_old_files(number_to_keep):
		for each_src_name, each_file_set in old_files_by_src.items():

			if len(each_file_set) > number_to_keep:

				for each_name in (
					sorted(each_file_set)[ : -number_to_keep]
					if number_to_keep > 0
					else
					each_file_set
				):
					old_file_path = get_file_path_by_name(each_name)

					if arg_test:
						print_with_colored_prefix('Delete old file:', old_file_path)
					else:
						print_with_colored_prefix('Deleting old file:', old_file_path)

						os.remove(old_file_path)

	if arg_old_path:

		for each_name in list_dir_except_dots(arg_old_path):

		# Skip names without timestamp or extension:

			src_name = get_bak_src_name(each_name)

			if src_name == each_name:
				if arg_test:
					print_with_colored_prefix('Skip in folder for kept:', each_name)

				continue

			add_to_set_in_dict(old_files_by_src, src_name, each_name)

	if arg_new_path and arg_new_path != arg_old_path:

		for each_name in list_dir_except_dots(arg_new_path):

		# Skip names without timestamp or extension:

			src_name = get_bak_src_name(each_name)

			if src_name == each_name:
				if arg_test:
					print_with_colored_prefix('Skip in folder for latest:', each_name)

				continue

			add_to_set_in_dict(old_files_by_src, src_name, each_name)
			old_files_to_move.add(each_name)

	if arg_test:
		print_with_colored_prefix('Old archives:', get_obj_pretty_print(old_files_by_src), 'cyan')
		print_with_colored_prefix('Old archives to move if updated:', get_obj_pretty_print(old_files_to_move), 'cyan')

	cleanup_old_files(arg_number_to_keep if arg_number_to_keep > 1 else 1)

	for each_src_path in src_dirs:

		for each_name in list_dir_except_dots(each_src_path):

			src_path = normalize_slashes(each_src_path + '/' + each_name)
			old_file_path = old_file_name = None

			if os.path.isdir(src_path) and is_dir_empty(src_path):
				continue

			try:
				if each_name in old_files_by_src:
					old_file_name = sorted(old_files_by_src[each_name])[-1 : ][0]
					old_file_path = get_file_path_by_name(old_file_name)
					old_file_time = os.path.getmtime(old_file_path)
					latest_src_time = os.path.getmtime(src_path)

					if arg_test:
						print('{} {} {} {} {} {}'.format(
							colored('Old bak.time', 'yellow')
						,	old_file_time
						,	colored((
								'<' if latest_src_time < old_file_time else
								'>' if latest_src_time > old_file_time else
								'='
							), 'yellow')
						,	latest_src_time
						,	colored('src:', 'yellow')
						,	each_name
						))

					if latest_src_time <= old_file_time:
						continue
			except:
				traceback.print_exc()

				continue

# Move previous latest archive to old keep folder:

			if old_file_path and (
				old_file_name in old_files_to_move
			or	old_file_path in old_files_to_move
			):
				if arg_test:
					print_with_colored_prefix('Move old file:', old_file_path)

				elif os.path.isfile(old_file_path):
					print_with_colored_prefix('Moving old file:', old_file_path)

					old_dest_path = normalize_slashes(arg_old_path + '/' + old_file_name)

					if os.path.exists(old_dest_path):
						try_count = 1
						path_parts = old_dest_path.rsplit('.', 1)

						while os.path.exists(old_dest_path):
							try_count += 1
							old_dest_path = '({}).'.format(try_count).join(path_parts)

					os.rename(old_file_path, old_dest_path)

# Create new archive for this source:

			new_archives_count += 1
			cmd_args = [arg_cmd_arch + cmd_glue + each_name, src_path, arg_new_path]

			print_with_colored_prefix('Source to archive {}:'.format(new_archives_count), each_name)

			if not arg_test:
				run_batch_archiving(cmd_args)

# - Result summary ------------------------------------------------------------

	if not new_archives_count:
		print('')
		cprint('Nothing to archive.', 'red')

		return 11

	return 0

# - Run from commandline, when not imported as module -------------------------

if __name__ == '__main__':
	sys.exit(run_backup_batch_archiving(sys.argv[1 : ]))

# - End -----------------------------------------------------------------------
