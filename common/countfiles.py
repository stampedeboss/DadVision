#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''

Purpose:
    Routine to return the number of video files in tree

'''
from common.exceptions import InvalidPath
import os
import sys
import fnmatch


__pgmname__ = 'countfiles'
__version__ = '$Rev$'

__author__ = "AJ Reynolds"
__copyright__ = "Copyright 2011, AJ Reynolds"
__credits__ = []
__license__ = "GPL"

__maintainer__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"
__status__ = "Development"

ExcludeList = []

def countFiles(pathname, types=[], exclude_list=[]):

    if not os.path.exists(pathname) or not os.path.isdir(pathname):
        raise InvalidPath("Requested pathname does not exist or isn't a directory : {}".format(pathname))

    _file_count = 0
    dir_count = 0
    dir_skipped = 0

    for _root, _dirs, _files in os.walk(pathname, followlinks=True):

        dir_count += 1
        _dirs.sort()
        _dirs_temp = sorted(_dirs)
        if exclude_list != []:
            for _dir in _dirs_temp:
                if ignored(_dir, exclude_list=exclude_list):
                    dir_skipped += 1
                    _dirs.remove(_dir)

        for _file in _files:
            ext = os.path.splitext(_file)[1][1:]
            if types != []:
                if ext.lower() in types:
                    _file_count += 1
            else:
                _file_count += 1

    return _file_count

def ignored(name, exclude_list):
    """ Check for ignored pathnames.
    """
    return any(fnmatch.fnmatch(name.lower(), pattern) for pattern in exclude_list)



if __name__ == '__main__':

    if len(sys.argv) > 1:
        pathname = sys.argv[1]
    else:
        pathname = os.getcwd()

    count = countFiles(pathname, types=[], exclude_list=[])
    print count