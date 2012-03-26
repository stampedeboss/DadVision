#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Purpose:
     Scan Movie Library and report any possible issues discovered    

'''
from daddyvision.common import logger
from daddyvision.common.options import OptionParser
from daddyvision.common.settings import Settings
from daddyvision.common.countfiles import countFiles
from daddyvision.movies.fileparser import FileParser
from logging import INFO, WARNING, ERROR, DEBUG
import fnmatch
import logging
import os
import sys

__pgmname__ = 'daddyvision.movies.movies'
__version__ = '$Rev$'

__author__ = "AJ Reynolds"
__copyright__ = "Copyright 2011, AJ Reynolds"
__credits__ = []
__license__ = "GPL"

__maintainer__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"
__status__ = "Development"

TRACE = 5
VERBOSE = 15

log = logging.getLogger(__pgmname__)
logger.initialize()
config = Settings()

TRACE = 5
VERBOSE = 15

class MovieLibrary(object):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        pass
    
    def check(self, pathname):
        _files_checked = 0
        _total_files = countFiles(pathname, exclude_list=(config.ExcludeList + config.ExcludeScanList), types=config.MediaExt)

        log.info("==== Begin Scan: {} ====".format(pathname))

        for _root, _dirs, _files in os.walk(os.path.abspath(pathname),followlinks=True):
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
                if _ext in config.MediaExt:
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
        exclude = config.ExcludeList + config.ExcludeScanList
        return any(fnmatch.fnmatch(name.lower(), pattern) for pattern in (config.ExcludeList + config.ExcludeScanList) + config.IgnoreGlob)

class GetOutOfLoop(Exception):
    pass


if __name__ == '__main__':
    parser = OptionParser()
    options, args = parser.parse_args()

    log_level = logging.getLevelName(options.loglevel.upper())

    if options.logfile == 'daddyvision.log':
        log_file = '{}.log'.format(__pgmname__)
    else:
        log_file = os.path.expanduser(options.logfile)

    # If an absolute path is not specified, use the default directory.
    if not os.path.isabs(log_file):
        log_file = os.path.join(logger.LogDir, log_file)

    logger.start(log_file, log_level, timed=True)

    log.debug("Parsed command line options: {!s}".format(options))
    log.debug("Parsed arguments: %r" % args)

    movies = MovieLibrary()
    movies.check('/mnt/DadVision/Movies')