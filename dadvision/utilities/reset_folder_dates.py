#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Purpose:
     The purpose of this routine is to reset the folder dates to be equal
     to the latest video file date in the folder.

'''
from __future__ import division

import fnmatch
import logging
import os
import sys

from common.countfiles import countFiles
from common.exceptions import InvalidPath

import logger
from dadvision.library import Library

__pgmname__ = 'reset_folder_dates'

__author__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"

__maintainer__ = __author__

__copyright__ = "Copyright 2011, AJ Reynolds"
__license__ = "GPL"

log = logging.getLogger(__pgmname__)

class ResetFolders(Library):
    '''
    Scan pathname passed and reset folder dates and timestamps
    '''
    def reset_folders(self, pathname):
        log.trace('reset_folders: Pathname Requested: {}'.format(pathname))

        _files_checked = 0
        _total_files = countFiles(pathname, self.settings.MediaExt, self.settings.ExcludeList)

        if _total_files == 0:
            log.warn('Path contains no video content, Stopping scan. Path: {}'.format(pathname))
            return(4)

        log.info("==== Begin Scan: {} ====".format(pathname))

        dir_count = 0
        dir_skipped = 0
        for _root, _dirs, _files in os.walk(os.path.abspath(pathname), followlinks=False):
            dir_count += 1
            _last_date = None
            if _dirs != []:
                _dirs.sort()
                _dirs_temp = sorted(_dirs)
                for _dir in _dirs_temp:
                    if self.ignored(_dir):
                        dir_skipped += 1
                        _dirs.remove(_dir)
                        log.trace('Removing Dir: %s' % _dir)

            for _file in _files:
                _ext = os.path.splitext(_file)[1][1:]
                if _ext.lower() not in self.settings.MediaExt:
                    continue
                _files_checked += 1
                _fq_name = os.path.join(_root, _file)
                _mod_date = os.path.getmtime(_fq_name)
                if _last_date < _mod_date or _last_date == None:
                    _last_date = _mod_date
            if _last_date:
                os.utime(_root, (_last_date, _last_date))
            elif _dirs == []:
                os.utime(_root, None)

        message = 'Files Checked: %2.2f%%   %5d of %5d' % (((_files_checked) / _total_files) * 100, (_files_checked), _total_files)
        log.info(message)

    def ignored(self, name):
        """ Check for ignored pathnames.
        """
        return any(fnmatch.fnmatch(name.lower(), pattern) for pattern in self.settings.ExcludeList)

if __name__ == '__main__':

    logger.initialize()
    library = ResetFolders()

#    parser = OptionParser()
    Library.args = library.options.parser.parse_args(sys.argv[1:])
    log.debug("Parsed command line: {!s}".format(library.args))

    log_level = logging.getLevelName(library.args.loglevel.upper())

    if library.args.logfile == 'daddyvision.log':
        log_file = '{}.log'.format(__pgmname__)
    else:
        log_file = os.path.expanduser(library.args.logfile)

    # If an absolute path is not specified, use the default directory.
    if not os.path.isabs(log_file):
        log_file = os.path.join(logger.LogDir, log_file)

    logger.start(log_file, log_level, timed=True)

    if len(library.args.library) < 1:
        log.warn('No pathname supplied for rename: Using default: {}'.format(library.settings.MoviesDir))
        Library.args.library = [library.settings.MoviesDir]

    _lib_paths = library.args.library

    for _lib_path in _lib_paths:
        if os.path.exists(_lib_path):
            library.reset_folders(_lib_path)
        else:
            log.error('Invalid arguments file or path name not found: %s' % _lib_path)
            raise InvalidPath('Invalid arguments file or path name not found: %s' % _lib_path)
