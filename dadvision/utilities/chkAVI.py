#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''

Purpose:
    Scan Video Libraries to check for errors with the video
    structure or conent
'''
from __future__ import division

import logging
import os

from common.options import OptionParser
from common.settings import Settings

import logger
from chkvideo import chkAVId

__pgmname__ = 'chkAVI'

__author__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"

__maintainer__ = __author__

__copyright__ = "Copyright 2011, AJ Reynolds"
__license__ = "GPL"

log = logging.getLogger(__pgmname__)
logger.initialize()

TRACE = 5
VERBOSE = 15

FilehIssues = []

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

rc, FileIssues = chkAVId(pathname)

print 'Return Code: {}'.format(rc)
if FileIssues <> []:
    print
    print
    for _entry in FileIssues:
        print _entry
    print 'Number Issues Identified: %s' % len(FileIssues)
else:
    print 'No errors found'

