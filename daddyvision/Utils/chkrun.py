#!/usr/bin/env python
"""
Author: AJ Reynolds
Date: 01-24-2011
Purpose:
    Program to Sync Remote Hosts

"""

import os
import re
import sys
import time
import psutil
import logging
import datetime
import subprocess
import logging.handlers
from configobj import ConfigObj
from seriesExceptions import ConfigValueError
from optparse import OptionParser, OptionGroup

__version__ = '$Rev$'
__pgmname__ = 'ChkDaemons'

PgmDir      = os.path.dirname(__file__)
HomeDir     = os.path.expanduser('~')
ConfigDirB  = os.path.join(HomeDir, '.config')
ConfigDir   = os.path.join(ConfigDirB, 'xbmcsupt')
LogDir      = os.path.join(HomeDir, 'log')

if not os.path.exists(LogDir):
    try:
        os.makedirs(LogDir)
    except:
        raise ConfigValueError("Cannot Create Log Directory: %s" % LogDir)

# Set up a specific logger with our desired output level
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
ml = logging.handlers.TimedRotatingFileHandler(os.path.join(LogDir, '%s.log' % __pgmname__), when='midnight', backupCount=7)
dl = logging.handlers.TimedRotatingFileHandler(os.path.join(LogDir, '%s_debug.log' % __pgmname__), when='midnight', backupCount=7)
ch = logging.StreamHandler()
ml.setLevel(logging.INFO)
dl.setLevel(logging.DEBUG)
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s - %(message)s")
ml.setFormatter(formatter)
dl.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(ml)
logger.addHandler(dl)
logger.addHandler(ch)

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
                        logger.debug('%s %s' % (p.name,cmdline))
                        logger.info('%s %s' % (cmdline[1], cmdline[2]))
                    elif p.name == 'rsync':
                        logger.info('%s %s' % (p.name,cmdline[-1]))
#                    logger ('Running: %s  Directory: %s  Host: %s')
#                    logger.info()
#                    if os.path.split(cmdline[-2].rstrip(os.sep))[0] == directory.rstrip(os.sep):
        return

if __name__ == '__main__':

    parser = OptionParser(
        "%prog [options]",
        version="%prog " + __version__)

    group = OptionGroup(parser, "Logging Levels")
    group.add_option("-e", "--errors", dest="error",
        action="store_true", default=False,
        help="omit all but error logging")
    group.add_option("-q", "--quiet", dest="quiet",
        action="store_true", default=False,
        help="omit informational logging")
    group.add_option("-v", "--verbose", dest="verbose",
        action="store_true", default=False,
        help="increase informational logging")
    group.add_option("-d", "--debug", dest="debug",
        action="store_true", default=False,
        help="increase informational logging to include debug")
    parser.add_option_group(group)

    options, args = parser.parse_args()

    opt_sel = 0
    if options.debug:
        logger.setLevel(logging.DEBUG)
        ml.setLevel(logging.DEBUG)
        ch.setLevel(logging.DEBUG)
        opt_sel = opt_sel + 1
    if options.error:
        logger.setLevel(logging.ERROR)
        ml.setLevel(logging.ERROR)
        ch.setLevel(logging.ERROR)
        opt_sel = opt_sel + 1
    if options.quiet:
        logger.setLevel(logging.WARNING)
        ml.setLevel(logging.WARNING)
        ch.setLevel(logging.WARNING)
        opt_sel = opt_sel + 1
    if options.verbose:
        logger.setLevel(logging.DEBUG)
        ml.setLevel(logging.DEBUG)
        ch.setLevel(logging.DEBUG)
        opt_sel = opt_sel + 1

    logger.debug("Parsed command line options: %r" % options)
    logger.debug("Parsed arguments: %r" % args)

    if opt_sel > 1:
        logger.error('Conflicting options selected, Reconsider Parameters.')
        sys.exit(1)

    chkStatus()
    sys.exit(0)