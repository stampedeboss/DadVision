#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Purpose:
     The purpose of this routine is to reset the folder dates to be equal
     to the latest video file date in the folder.

'''
from __future__ import division
from daddyvision.common.exceptions import (InvalidPath, InvalidFilename, ConfigNotFound, ConfigValueError)
from daddyvision.common import logger
from daddyvision.common.options import OptionParser, OptionGroup
from daddyvision.common.settings import Settings
from daddyvision.common.countfiles import countFiles
from datetime import datetime, date, timedelta
from logging import INFO, WARNING, ERROR, DEBUG
import fnmatch
import logging
import os
import sys

__pgmname__ = 'reset_folder_dates'
__version__ = '$Rev$'

__author__ = "AJ Reynolds"
__copyright__ = "Copyright 2012, AJ Reynolds"
__credits__ = []
__license__ = "GPL"

__maintainer__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"
__status__ = "Development"

TRACE = 5
VERBOSE = 15

log = logging.getLogger(__pgmname__)

logger.initialize()

TRACE = 5
VERBOSE = 15

class MovieLibrary(object):
    '''
    Scan pathname passed and reset folder dates and timestamps
    '''

    def __init__(self, config, options):
        '''
        Return MovieLibray object
        '''
        log.trace('MovieLibrary - __init__')

        self.config = config
        self.options = options

    def check(self, pathname):
        log.trace('check: Pathname Requested: {}'.format(pathname))

        _files_checked = 0
        _total_files = countFiles(pathname, exclude_list=(self.config.ExcludeList + self.config.ExcludeScanList), types=self.config.MediaExt)

        log.info("==== Begin Scan: {} ====".format(pathname))

        for _root, _dirs, _files in os.walk(os.path.abspath(pathname),followlinks=False):
            _last_date = None
            if _dirs != []:
                _dirs.sort()
                _dirs_temp = sorted(_dirs)
                for _dir in _dirs_temp:
                    if self.ignored(_dir):
                        _dirs.remove(_dir)
                        log.trace('Removing Dir: %s' % _dir)
            for _file in _files:
                _ext = os.path.splitext(_file)[1][1:]
                if _ext not in self.config.MediaExt and _ext.lower() not in ['vob', 'iso']:
                    continue
                if _ext.lower() != 'vob':
                    _files_checked += 1
                _fq_name = os.path.join(_root, _file)
                _mod_date = os.path.getmtime(_fq_name)
                if _last_date < _mod_date or _last_date == None:
                    _last_date = _mod_date
            if _last_date:
                os.utime(_root, (_last_date, _last_date))
            elif _dirs == []:
                os.utime(_root, None)

        message = 'Files Checked: %2.2f%%   %5d of %5d' % ((_files_checked)/_total_files, (_files_checked), _total_files)
        log.info(message)

    def ignored(self, name):
        """ Check for ignored pathnames.
        """
        return any(fnmatch.fnmatch(name.lower(), pattern) for pattern in (self.config.ExcludeList + self.config.ExcludeScanList))

class localOptions(OptionParser):

    def __init__(self, unit_test=False, **kwargs):
        OptionParser.__init__(self, **kwargs)

        group = OptionGroup(self, "Reset Folder Dates Unique Options:")
        group.add_option("-i", "--input-directory",
            dest="requested_dir",
            default="None",
            help="directory to be scanned")
        self.add_option_group(group)


if __name__ == '__main__':
    config = Settings()
    logger.initialize()

#    parser = OptionParser()
    parser = localOptions()
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

    _path_name = ''
    for i in range(len(args)):
        _path_name = '%s %s'% (_path_name, args[i])

    if options.requested_dir == "None":
        if len(args) > 1:
            options.requested_dir = _path_name
        else:
            log.info('Missing Scan Starting Point (Input Directory), Using Default: %r' % config.MoviesDir)
            options.requested_dir = config.MoviesDir

    if not os.path.exists(options.requested_dir):
        log.error('Invalid arguments file or path name not found: %s' % options.requested_dir)
        sys.exit(1)

    MovieLib = MovieLibrary(config, options)
    MovieLib.check(options.requested_dir)
