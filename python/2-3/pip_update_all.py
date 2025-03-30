#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Python 2 or 3 should work.

# - Dependencies --------------------------------------------------------------

import subprocess, sys

# Use colored text if available:
try:
	from termcolor import colored, cprint
	import colorama

	colorama.init()

except ImportError:
	def colored(*list_args, **keyword_args): return list_args[0]
	def cprint (*list_args, **keyword_args): print (list_args[0])

# Check versions of python and pip: -------------------------------------------
# https://stackoverflow.com/a/9079062

python_version_string = str(sys.version_info.major)

# pip_exe_filename = 'pip' + python_version_string
pip_exe_filename = 'python' + python_version_string + ' -m pip'

print(
	colored('Got python version: ', 'yellow')
+	python_version_string
+	colored(', full text:\n', 'yellow')
+	sys.version
+	'\n'
)

cmd_string = pip_exe_filename + ' --version'

print(
	colored('Running: ', 'magenta')
+	cmd_string
+	'\n'
)

pip_version_output = subprocess.check_output(cmd_string, shell=True)
pip_version_output = pip_version_output.decode().strip()
pip_version_string = pip_version_output.split(' ')[1]
pip_version_numbers = list(map(int, pip_version_string.split('.')))

print(
	colored('Got pip version: ', 'yellow')
+	pip_version_string
+	colored(', full text:\n', 'yellow')
+	pip_version_output
+	'\n'
)

# Get list of packages to update: ---------------------------------------------
# https://stackoverflow.com/a/24736563

try:
	from importlib.metadata import distributions
	packages = [dist.metadata['Name'] for dist in distributions()]

	cprint('Got packages from importlib.metadata.\n', 'yellow')

except ImportError:

# https://stackoverflow.com/a/5839291

	try:
		import pkg_resources
		packages = [dist.project_name for dist in pkg_resources.working_set]

		cprint('Got packages from pkg_resources.\n', 'yellow')

	except ImportError:

		import pip
		packages = [dist.project_name for dist in pip.get_installed_distributions()]

		cprint('Got packages from pip version <= 10.0.0.\n', 'yellow')

# Alternative to internal methods:
# python3 -m pip list --outdated --format=columns

cmd_string = pip_exe_filename + ' install --upgrade ' + ' '.join(packages)

print(
	colored('Command to run: ', 'magenta')
+	cmd_string
+	'\n'
)

cprint('Press Enter to continue.', 'cyan')

# Update packages: ------------------------------------------------------------

if sys.version_info.major == 2:
	raw_input()
else:
	input()

subprocess.call(cmd_string, shell=True)

cprint('\nDone.', 'green')

# - End -----------------------------------------------------------------------
