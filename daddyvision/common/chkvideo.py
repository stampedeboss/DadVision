#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''

Purpose:
    Scan Video Libraries to check for errors with the video
    structure or conent
'''
from __future__ import division
from daddyvision.common import logger
from subprocess import Popen, check_call as Call, PIPE
from daddyvision.common.countfiles import countFiles
from daddyvision.common.options import OptionParser, OptionGroup

import logging
import os
import tempfile
import re

__pgmname__ = 'chkvideo'
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

FilesWithIssues = {}

def chkVideoDir(pathname, deep=False):
    log.trace('Checking Directory: %s' % pathname)
    global FilesWithIssues

    _files_checked = 0

    _file_count = countFiles(pathname)
    log.info('Number of Files in Tree: %s' % _file_count)

    if os.path.isdir(pathname):
        for root, dirs, files in os.walk(os.path.abspath(pathname),followlinks=False):
            dirs = sorted(dirs)
            files = sorted(files)
            for fname in files:
                fq_fname = os.path.join(root, fname)
                rc = chkVideoFile(fq_fname, deep)
                if deep and rc[0] > 0:
                    FilesWithIssues[fq_fname] = rc[1]
                elif rc > 0:
                    FilesWithIssues[fq_fname] = 'Errors Found'
                    log.verbose('File has issues: %s' % fq_fname)
                _files_checked += 1
                quotient, remainder = divmod(_files_checked, 250)
                if remainder == 0:
                    log.info('Files Checked: %2.2f%% - %5s of %5s   Number of Errors: %s' % (_files_checked/_file_count, _files_checked, _file_count, len(FilesWithIssues)))
        log.info('Files Checked: %2.2f%% - %5s of %5s   Number of Errors: %s' % (_files_checked/_file_count, _files_checked, _file_count, len(FilesWithIssues)))

    return FilesWithIssues

def chkVideoFile(pathname, deep=False):
    log.trace('Checking File: %s' % pathname)

    ext = os.path.splitext(pathname)[1][1:]
    if ext == 'avi':
        if deep:
            rc = chkAVId(pathname)
            return rc
        rc = chkAVI(pathname)
        if rc == 1:
            rc = chkAVId(pathname)[0]
    elif ext == 'mkv':
        rc = chkMKV(pathname)
    else:
        rc = 0
    return rc

def chkAVId(pathname):
    regex_bracket = re.compile('.*\].*$', re.IGNORECASE)
    regex_text = re.compile('((frame)|(Press)|(PAR))', re.IGNORECASE)
    error_msgs = []
    rc = 0
    _ffmpeg_out =  tempfile.NamedTemporaryFile()
    cmd = ['ffmpeg', '-v', '5', '-i', pathname, '-f', 'null', '-']
    process = Popen(cmd, shell=False, stdin=None, stdout=None, stderr=PIPE, cwd=None)
    output = process.stderr.readlines()
    for line in output:
        if not regex_bracket.match(line):
            continue
        else:
            if not regex_text.search(line):
                error_msgs.append(line.strip('\n'))
                print line.strip('\n')
                rc = 1
    return rc, error_msgs

def chkAVI(pathname):
    cmd = ['avinfo', '-q', pathname, '--list']
    process = Popen(cmd, shell=False, stdin=None, stdout=PIPE, stderr=PIPE, cwd=None)
    output = process.stdout.read()
    log.debug('AVINFO: %s' % output)
    if output == '':
        rc = 1
    else:
        rc = 0
    return rc

def chkMKV(pathname):
    NULLF = open('/dev/null', 'w')
    cmd = ['mkvinfo', pathname]
    process = Popen(cmd, shell=False, stdin=None, stdout=NULLF, stderr=NULLF, cwd=None)
    rc = process.returncode
    return rc

class localOptions(OptionParser):

    def __init__(self, unit_test=False, **kwargs):
        OptionParser.__init__(self, **kwargs)

        group = OptionGroup(self, "Modifers")
        group.add_option("-d", "--deep", dest="deep",
            action="store_true", default=False,
            help="Perform Detailed Check of AVI Files")
        self.add_option_group(group)


if __name__ == '__main__':
    from daddyvision.common.settings import Settings

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

    config = Settings()
    if len(args) == 0:
        pathname = config.SeriesDir
    elif len(args) > 0:
        pathname = args[0]

    FilesWithIssues = chkVideoDir(pathname, options.deep)
    if len(FilesWithIssues) > 0:
        for _entry in sorted(FilesWithIssues):
            print _entry
        print 'Number Files Identified: %s' % len(FilesWithIssues)
    else:
        print 'No errors found'
