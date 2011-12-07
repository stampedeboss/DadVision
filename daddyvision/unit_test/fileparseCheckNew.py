#!/usr/bin/env python 
'''
Created on Dec 1, 2011

@author: aj
'''
from __future__ import division
from optparse import OptionParser, OptionGroup
from subprocess import Popen, call as Call, PIPE
from logging import INFO, WARNING, ERROR, DEBUG
from daddyvision.fileparser import FileParser 
import logging
import logging.handlers
import os
import subprocess
import tempfile
import time

__version__ = '$Rev$'
__pgmname__ = 'ScanVideo'

PgmDir = os.path.dirname(__file__)
HomeDir = os.path.expanduser('~')
ConfigDirB = os.path.join(HomeDir, '.config')
ConfigDir = os.path.join(ConfigDirB, 'xbmcsupt')
LogDir = os.path.join(HomeDir, 'log')
TEMP_LOC = os.path.join(HomeDir, __pgmname__)

#Level     Numeric value
#CRITICAL    50
#ERROR       40
#WARNING     30
#INFO        20
#DEBUG       10
#NOTSET       0

logging.addLevelName(5, 'TRACE')
logging.addLevelName(15, 'VERBOSE')
log = logging.getLogger()
setattr(log, 'TRACE', lambda *args: log.log(5, *args))
setattr(log, 'VERBOSE', lambda *args: log.log(15, *args))

class ScanDownload(object):
    def __init__(self):
        self.myparser = FileParser()

    def ScanDir(self, pathname):
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
                    log.TRACE('Checking File: %s' % fq_name)

                    try:
                        _file_details = self.myparser.GetFileDetails(fq_name)
                        log.info(_file_details)
                    except:
                        log.error('Unable to parse: {}'.format(fq_name))
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

    log.setLevel('TRACE')
    _formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)-6s - %(message)s")
    _formatter2 = logging.Formatter("%(message)s")

    #_mem_log = logging.handlers.MemoryHandler(1000 * 1000, 100)
    #_mem_log.setLevel(DEBUG)
    #_mem_log.setFormatter(_formatter)
    #log.addHandler(_mem_log)

    _console = logging.StreamHandler()
    _console.setLevel(INFO)
    _console.setFormatter(_formatter)

    _main_log = logging.handlers.RotatingFileHandler(os.path.join(LogDir, '%s.log' % __pgmname__), maxBytes=0, backupCount=7)
    _main_log.setLevel(DEBUG)
    _main_log.setFormatter(_formatter)

    _error_log = logging.handlers.RotatingFileHandler(os.path.join(LogDir, '%s_error.log' % __pgmname__), maxBytes=0, backupCount=7)
    _error_log.setLevel(ERROR)
    _error_log.setFormatter(_formatter2)

    log.addHandler(_console)
    log.addHandler(_main_log)
    log.addHandler(_error_log)

    _main_log.doRollover()
    _error_log.doRollover()

    parser = OptionParser(
        "%prog [options] [<pathname>]",
        version="%prog " + __version__)

    group = OptionGroup(parser, "Logging Levels:")
    group.add_option("--loglevel", dest="loglevel",
        action="store", type="choice", default="INFO",
        choices=['CRITICAL' ,'ERROR', 'WARNING', 'INFO', 'VERBOSE', 'DEBUG', 'TRACE'],
        help="Specify by name the Level of logging desired, [CRITICAL|ERROR|WARNING|INFO|VERBOSE|DEBUG|TRACE]")
    group.add_option("-e", "--errors", dest="loglevel",
        action="store_const", const="ERROR",
        help="Limit logging to only include Errors and Critical information")
    group.add_option("-q", "--quiet", dest="loglevel",
        action="store_const", const="WARNING",
        help="Limit logging to only include Warning, Errors, and Critical information")
    group.add_option("-v", "--verbose", dest="loglevel",
        action="store_const", const="VERBOSE",
        help="increase logging to include informational information")
    group.add_option("--debug", dest="loglevel",
        action="store_const", const="DEBUG",
        help="increase logging to include debug information")
    group.add_option("--trace", dest="loglevel",
        action="store_const", const="TRACE",
        help="increase logging to include program trace information")
    parser.add_option_group(group)

    options, args = parser.parse_args()
    _console.setLevel(options.loglevel)

    log.debug("Parsed command line options: %r" % options)
    log.debug("Parsed arguments: %r" % args)

    if len(args) == 0:
        args = ['/mnt/TV/New']

    _dir_scan = ScanDownload()
    _file_count = _dir_scan.ScanDir(args[0])
