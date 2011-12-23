#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''

Purpose:
    Scan Video Libraries to check for errors with the video
    structure or conent
'''
from __future__ import division
from daddyvision.common import logger
from daddyvision.common.options import OptionParser
from daddyvision.common.settings import Settings
from subprocess import Popen, check_call as Call, PIPE
import logging
import os
import tempfile

__pgmname__ = 'ScanVideo'
__version__ = '$Rev$'

__author__ = "AJ Reynolds"
__copyright__ = "Copyright 2011, AJ Reynolds"
__credits__ = []
__license__ = "GPL"

__maintainer__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"
__status__ = "Development"

log = logging.getLogger(__pgmname__)
logger.initialize()

TRACE = 5
VERBOSE = 15

config = Settings()

class ScanVideo(object):
    def __init__(self):
        pass

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
                    log.debug('Checking File: %s' % fq_name)
                    ext = os.path.splitext(fname)[1]
                    if ext == '.avi':
                        cmd = ['avinfo', '-q', fq_name, '--list']
                        process = Popen(cmd, shell=False, stdin=None, stdout=PIPE, stderr=PIPE, cwd=None)
                        output = process.stdout.read()
                        log.trace('AVINFO: %s' % output)
                        if output == '':
                            rc = 1
                        else:
                            rc = 0
                    elif ext == '.mkv':
                        cmd = ['mkvinfo', fq_name]
                        process = Popen(cmd, shell=False, stdin=None, stdout=PIPE, stderr=PIPE, cwd=None)
                        output = process.stdout.read()
                        log.trace('MKVINFO: %s' % output)
                        rc = process.returncode
                    else:
                        continue
                    if rc > 0:
                        self.FilesWithIssues.append(fq_name)
                        log.verbose('File has issues: %s' % fq_name)

                    _files_checked += 1
                    quotient, remainder = divmod(_files_checked, 250)
                    if remainder == 0:
                        log.info('Files Checked: %2.2f%% - %5s of %5s   Number of Errors: %s' % (_files_checked/_file_count, _files_checked, _file_count, len(self.FilesWithIssues)))
            log.info('Files Checked: %2.2f%% - %5s of %5s   Number of Errors: %s' % (_files_checked/_file_count, _files_checked, _file_count, len(self.FilesWithIssues)))

        return len(self.FilesWithIssues)

    def getFileNames(self, report=False):
        _files_with_errors = tempfile.NamedTemporaryFile(mode='w')

        if self.FilesWithIssues <> []:
            _files_with_errors.write('File Names With Issues: ')
            for _entry in sorted(self.FilesWithIssues):
                _files_with_errors.write('%s' % _entry)
                if report:
                    print _entry
            print 'Files Identified: %s' % len(self.FilesWithIssues)
        else:
            log.info('No errors found')
            return []

        return self.FilesWithIssues

    def _count_total_files(self, valid_path):
        _file_count = 0
        for _root, _dirs, _files in os.walk(valid_path):
            for _f in _files:
                _file_count += 1
        return _file_count


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

    if len(args) == 0:
        args = [config.SeriesDir]

    _dir_scan = ScanVideo()
    _file_count = _dir_scan.scanDir(args[0])
    _file_name_list = _dir_scan.getFileNames(report=True)
