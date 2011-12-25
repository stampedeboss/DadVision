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
from daddyvision.common.chkvideo import chkAVId as chkAVI
import logging
import os
import tempfile
import re

__pgmname__ = 'chkAVI'
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

FilehIssues = []

from daddyvision.common.options import OptionParser
from daddyvision.common.settings import Settings

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

config = Settings()
if len(args) == 0:
    parser.error('Missing filename')
elif len(args) > 0:
    pathname = args[0]

rc, FileIssues = chkAVI(pathname)
if FileIssues <> []:
    print
    print
    for _entry in FileIssues:
        print _entry
    print 'Number Issues Identified: %s' % len(FileIssues)
else:
    print 'No errors found'

