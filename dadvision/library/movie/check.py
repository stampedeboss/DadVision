#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Purpose:
     Scan Movie Library and report any possible issues discovered
'''

from library import Library
from common import logger
from common.countfiles import countFiles
import fnmatch
import logging
import os
import sys

__pgmname__ = 'library.movie.check'
__version__ = '@version: $Rev$'

__author__ = "@author: AJ Reynolds"
__email__ = "@contact: stampedeboss@gmail.com"
__copyright__ = "@copyright: Copyright 2011, AJ Reynolds"
__license__ = "@license: GPL"

__maintainer__ = "@organization: AJ Reynolds"
__status__ = "@status: Development"
__credits__ = []

log = logging.getLogger(__pgmname__)

class Check(Library):
    '''
    classdocs
    '''

    def check(self, pathname):
        _files_checked = 0
        _total_files = countFiles(pathname, exclude_list=(self.settings.ExcludeList + self.settings.ExcludeScanList), types=self.settings.MediaExt)

        log.info("==== Begin Scan: {} ====".format(pathname))

        for _root, _dirs, _files in os.walk(os.path.abspath(pathname), followlinks=True):
            _formats_found = {}
            _file_names = []
            _number_of_formats = 0
            if _dirs != None:
                _dirs.sort()
                _dirs_temp = sorted(_dirs)
                for _dir in _dirs_temp:
                    if self.ignored(_dir):
                        _dirs.remove(_dir)
                        log.trace('Removing Dir: %s' % _dir)
                        continue
            _files.sort()
            for _file in _files:
                _ext = os.path.splitext(_file)[1][1:].lower()
                if _ext in ['ifo', 'bup']:
                    _files_checked += 1
                    continue
                if _ext in self.settings.MediaExt:
                    _files_checked += 1
                    if _ext == 'vob':
                        _formats_found['dvd'] = True
                        if 'DVD' not in _file_names:
                            _file_names.append('DVD')
                    else:
                        _formats_found[_ext] = True
                        _file_names.append(_file)

            for _entry in _formats_found:
                if _entry == 'ifo' or _entry == 'bup':
                    continue
                _number_of_formats += 1

            if _number_of_formats > 1:
                log.info('Possible DUps Found: {}'.format(_root))
                for _file in _file_names:
                    log.info('    FileName: {}'.format(_file))

    def ignored(self, name):
        """ Check for ignored pathnames.
        """
        return any(fnmatch.fnmatch(name.lower(), pattern) for pattern in (self.settings.ExcludeList + self.settings.ExcludeScanList) + self.settings.IgnoreGlob)

class GetOutOfLoop(Exception):
    pass

if __name__ == '__main__':

    logger.initialize()

    library = Check()
    Library.args = library.options.parser.parse_args(sys.argv[1:])
    log.debug("Parsed command line: {!s}".format(Library.args))

    log_level = logging.getLevelName(Library.args.loglevel.upper())

    if Library.args.logfile == 'daddyvision.log':
        log_file = '{}.log'.format(__pgmname__)
    else:
        log_file = os.path.expanduser(Library.args.logfile)

    # If an absolute path is not specified, use the default directory.
    if not os.path.isabs(log_file):
        log_file = os.path.join(logger.LogDir, log_file)

    logger.start(log_file, log_level, timed=True)

    _lib_paths = Library.args.library

    for _lib_path in _lib_paths:
        if os.path.exists(_lib_path):
            library.check(_lib_path)
        else:
            log.error('Library Not Found: {}'.format(_lib_path))
