#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Purpose:
        Program to Sync Remote Hosts

'''
from library import Library
from common import logger
from subprocess import Popen, call as Call, check_call, CalledProcessError
import logging
import os
import psutil
import re
import sys
import time

__pgmname__ = 'startdeluged'
__version__ = '@version: $Rev: 306 $'

__author__ = "@author: AJ Reynolds"
__copyright__ = "@copyright: Copyright 2014, AJ Reynolds"
__status__ = "@status: Development"
__license__ = "@license: GPL"

__maintainer__ = "@organization: AJ Reynolds"
__credits__ = []

log = logging.getLogger(__pgmname__)


class StartDeluged(Library):

    def __init__(self):
        super(StartDeluged, self).__init__()

        start = self.options.parser.add_argument_group("Deluged Already Running",
                                                       description=None
                                                       )
        start.add_argument("-r", "--restart", dest="runaction", default='ignore',
                           action="store_const", const='restart',
                           help="Stop existing and Restart")

        return

    def _chk_deluged(self):
        devnull = open(os.devnull, 'wb') # use this in python < 3.3
        pidList = psutil.process_iter()
        for p in pidList:
            if p.name == 'deluged':
                if self.args.runaction == 'ignore':
                    log.info('Deluged is Running')
                    sys.exit(0)
                else:
                    p.kill()
                    log.warn('Previous Session Killed: %s' % p.pid)
                    time.sleep(0.2)
                    break
        log.warn('Deluged Not Running')
        Popen(['nohup', 'deluged'], stdout=devnull, stderr=devnull)
        log.warn('Deluged Restarted')
        return



if __name__ == '__main__':	

    logger.initialize()
    library = StartDeluged()

    Library.args = library.options.parser.parse_args(sys.argv[1:])
    log.debug("Parsed command line: {!s}".format(library.args))

    log_level = logging.getLevelName(library.args.loglevel.upper())

    if library.args.logfile == 'daddyvision.log':
        log_file = 'startdeluged.log'
    else:
        log_file = os.path.expanduser(library.args.logfile)

    # If an absolute path is not specified, use the default directory.
    if not os.path.isabs(log_file):
        log_file = os.path.join(logger.LogDir, log_file)

    logger.start(log_file, log_level, timed=True)

    library._chk_deluged()
