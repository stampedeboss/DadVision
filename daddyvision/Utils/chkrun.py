#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Author: AJ Reynolds
Date: 01-24-2011
Purpose:
    Program to Sync Remote Hosts

"""

from daddyvision.common import logger
from daddyvision.common.exceptions import ConfigValueError
from daddyvision.common.options import OptionParser, CoreOptionParser
from daddyvision.common.settings import Settings
import logging
import os
import psutil
import subprocess
import sys
import time

__pgmname__ = 'chkrun'
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

class chkStatus(object):
    def __init__(self):
        time.sleep(0.2)
        pidList = psutil.process_iter()
        for p in pidList:
            cmdline = p.cmdline
            if len(cmdline) > 0:
                nameList = ['rsync', 'python2.7', 'python']
                if p.name in nameList:
                    if p.name == "python2.7" and len(cmdline) > 2:
                        log.debug('%s %s' % (p.name,cmdline))
                    elif p.name == 'python':
                        if os.path.basename(cmdline[1]) == 'chkrun':
                            continue
                        if len(cmdline) == 2:
                            log.info('{:>6d} {:<8s} {}'.format(p.pid, p.terminal, os.path.basename(cmdline[1])))
                        elif len(cmdline) == 3:
                            log.info('{:>6d} {:<8s} {} {}'.format(p.pid, p.terminal, os.path.basename(cmdline[1]), cmdline[2]))
                    elif p.name == 'rsync':
                        log.info('{:>6d} {:<8s} {} {}'.format(p.pid, p.terminal, p.name, cmdline[-1]))
        return

if __name__ == '__main__':

    parser = CoreOptionParser()
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

    chkStatus()
    sys.exit(0)