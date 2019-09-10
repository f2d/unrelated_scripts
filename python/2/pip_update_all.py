#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# https://stackoverflow.com/a/5839291

# ------------------ For pip < 10.0.1 ------------------

# import pip
# from subprocess import call

# packages = [dist.project_name for dist in pip.get_installed_distributions()]
# call("pip install --upgrade " + ' '.join(packages), shell=True)

# ------------------ For pip >= 10.0.1 ------------------

import pkg_resources
from subprocess import call

packages = [dist.project_name for dist in pkg_resources.working_set]
call("pip2 install --upgrade " + ' '.join(packages), shell=True)
