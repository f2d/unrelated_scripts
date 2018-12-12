#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import os, sys

l = sys.argv[1] if len(sys.argv) > 1 else 987

for name in os.listdir(u'.'):
	f = open(name, 'r+b')
	f.truncate(l)
	f.close()
