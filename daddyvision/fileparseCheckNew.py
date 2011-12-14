#!/usr/bin/env python
'''
Routine to check out linking the common routines together

'''
from __future__ import division
from daddyvision.common.exceptions import EpisodeNotFound, SeriesNotFound
from daddyvision.common.options import OptionParser, CoreOptionParser
from daddyvision.common.fileparser import FileParser
from daddyvision.common.settings import Settings
from daddyvision.common import logger
from daddyvision.series.episodeinfo import EpisodeDetails
from subprocess import Popen, call as Call, PIPE
from logging import INFO, WARNING, ERROR, DEBUG
import logging
import os
import sys
import subprocess
import tempfile
import time

__pgmname__ = 'fileparseCheckNew'
__version__ = '$Rev$'

__author__ = "@author: AJ Reynolds"
__copyright__ = "Copyright 2011, AJ Reynolds"
__credits__ = []
__license__ = "GPL"

__maintainer__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"
__status__ = "Development"

log = logging.getLogger(__pgmname__)

def useLibraryLogging(func):

    def wrapper(self, *args, **kw):
        # Set the library name in the logger
        from daddyvision.common import logger
        logger.set_library('Series')
        try:
            return func(self, *args, **kw)
        finally:
            logger.set_library('')

    return wrapper

class ScanDownload(object):
    def __init__(self):
        self.myparser = FileParser()
        self.episodeinfo = EpisodeDetails()

    @useLibraryLogging
    def scanDir(self, pathname):
        _file_count = self._count_total_files(pathname)
        log.info('Number of File to be Checked: %s' % _file_count)
        self.FilesWithIssues = []
        _files_checked = 0
        if os.path.isdir(pathname):
            for root, dirs, files in os.walk(os.path.abspath(pathname),followlinks=False):
                dirs = sorted(dirs)
                files = sorted(files)
                for fname in files:
                    fq_name = os.path.join(root, fname)
                    log.trace('Checking File: %s' % fq_name)

                    try:
                        _file_details = self.myparser.getFileDetails(fq_name)
                        _file_details = self.episodeinfo.getDetails(_file_details)
                        log.info('Series: {SeriesName} Season: {SeasonNum} EPNO: {EpisodeNums}:'.format(_file_details))
                    except:
                        log.error('{} -  Unable to parse: {}'.format(sys.exc_info()[1], fq_name))
                    _files_checked += 1
                    quotient, remainder = divmod(_files_checked, 250)
                    if remainder == 0:
                        log.info('Files Checked: %2.2f%% - %5s of %5s   Number of Errors: %s' % (_files_checked/_file_count, _files_checked, _file_count, len(self.FilesWithIssues)))
            log.info('Files Checked: %2.2f%% - %5s of %5s   Number of Errors: %s' % (_files_checked/_file_count, _files_checked, _file_count, len(self.FilesWithIssues)))

        return len(self.FilesWithIssues)

    def _count_total_files(self, valid_path):
        _file_count = 0
        for _root, _dirs, _files in os.walk(valid_path):
            for _f in _files:
                _file_count += 1
        return _file_count


if __name__ == '__main__':

    logger.initialize()

    parser = CoreOptionParser()
    options, args = parser.parse_args()

    log_level = logging.getLevelName(options.loglevel.upper())
    log_file = os.path.expanduser(options.logfile)

    # If an absolute path is not specified, use the default directory.
    if not os.path.isabs(log_file):
        log_file = os.path.join(logger.LogDir, log_file)

    logger.start(log_file, log_level)

    log.debug("Parsed command line options: {!s}".format(options))
    log.debug("Parsed arguments: %r" % args)

    parms = Settings()

    if len(args) == 0:
        args = [os.path.join(os.path.split(parms.SeriesDir)[0], parms.NewDir)]

    log.info('Scaning Directory: {}'.format(args))

    _dir_scan = ScanDownload()
    _file_count = _dir_scan.scanDir(args[0])
