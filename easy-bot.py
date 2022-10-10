#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import os
import sys

# Globals
g_version = Path('VERSION').read_text()
g_required_files = [
    'jasper.py',
    'creds.py',
    'chromedriver',
]

def checkfile(filename):
    if not os.path.isfile(filename):
        print(f":: File '{ filename }' couldn't be found, aborting.")
        sys.exit(1)

    print(f":: File '{ filename }' was found, proceeding...")

print(f'Welcome to Jasper Worker ({ g_version })')
print("Starting checks")

for rf in g_required_files:
    checkfile(rf)

print('All OK.')