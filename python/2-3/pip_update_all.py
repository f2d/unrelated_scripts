#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Python 2 or 3 should work.

# Check versions of python and pip:
# https://stackoverflow.com/a/9079062

import subprocess, sys

python_version_string = str(sys.version_info.major)

# pip_exe_filename = 'pip' + python_version_string
pip_exe_filename = 'python' + python_version_string + ' -m pip'

print('Got python version: ' + python_version_string + ', full text:\n' + sys.version + '\n')

cmd_string = pip_exe_filename + ' --version'
print('Running: ' + cmd_string + '\n')

pip_version_output = subprocess.check_output(cmd_string, shell=True)
pip_version_output = pip_version_output.decode().strip()
pip_version_string = pip_version_output.split(' ')[1]
pip_version_numbers = list(map(int, pip_version_string.split('.')))

print('Got pip version: ' + pip_version_string + ', full text:\n' + pip_version_output + '\n')

# Update packages:
# https://stackoverflow.com/a/5839291

# if pip_version < 10.0.1:
if (
	(len(pip_version_numbers) < 1 or pip_version_numbers[0] < 10)
or	(
		(len(pip_version_numbers) < 1 or pip_version_numbers[0] == 10)
	and	(len(pip_version_numbers) < 2 or pip_version_numbers[1] <= 0)
	and	(len(pip_version_numbers) < 3 or pip_version_numbers[2] < 1)
	)
):
	print('Get packages for pip version <= 10.0.0:\n')

	import pip
	packages = [dist.project_name for dist in pip.get_installed_distributions()]
else:
	print('Get packages for pip version >= 10.0.1:\n')

	import pkg_resources
	packages = [dist.project_name for dist in pkg_resources.working_set]

cmd_string = pip_exe_filename + ' install --upgrade ' + ' '.join(packages)
print('Running: ' + cmd_string + '\n')

subprocess.call(cmd_string, shell=True)
