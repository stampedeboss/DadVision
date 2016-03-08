#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from stat import S_ISREG, ST_MTIME, ST_MODE
import os
import sys


# path to the directory (relative or absolute)
dirpath = sys.argv[1] if len(sys.argv) == 2 else r'.'

# get all entries in the directory w/ stats
entries2 = [(os.path.join(dirpath, fn) for fn in os.listdir(dirpath))]
entries = (os.path.join(dirpath, fn) for fn in os.listdir(dirpath))
entries = ((os.stat(path), path) for path in entries)

# leave only regular files, insert creation date
entries = ((stat[ST_MTIME], path)
           for stat, path in entries if S_ISREG(stat[ST_MODE]))
#NOTE: on Windows `ST_CTIME` is a creation date
#  but on Unix it could be something else
#NOTE: use `ST_MTIME` to sort by a modification date

_episode = 0
for cdate, path in sorted(entries):
    _episode += 1
    _new_name = 'E{0:02d} {1:s}'.format(_episode, os.path.basename(path).split(' ', 1)[1])
    _fq_name = os.path.join(dirpath, _new_name)
#    _mod_time = time.ctime(os.path.getmtime(path))
#    os.rename(path, _fq_name)
#    print time.ctime(cdate), os.path.basename(path), _new_name, _mod_time
