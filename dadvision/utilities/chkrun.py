#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Author: AJ Reynolds
Date: 01-24-2011
Purpose:

"""

import os
import sys
import time

import psutil

import logger
from dadvision.library import Library

__pgmname__     = 'chkrun'

__author__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"

__maintainer__ = __author__

__copyright__ = "Copyright 2011, AJ Reynolds"
__license__ = "GPL"

log = logger.logging.getLogger(__pgmname__)

class chkStatus(Library):
	def __init__(self):
		super(chkStatus, self).__init__()

	def check(self):
		nameList = ['python2.7', 'python', 'flexget', 'deluge', 'rsync']

		time.sleep(0.2)

		pidList = psutil.process_iter()
		for p in pidList:
			try:
				if p.name() in nameList:
					cmdline = p.cmdline()[1]
					if os.path.basename(p.cmdline()[1]) == 'chkrun':
						continue
					if os.path.basename(cmdline) == 'pydevd.py':
						continue
					if p.name() == "python2.7" and len(cmdline) > 2:
						log.debug('%s %s' % (p.name, cmdline))
					elif p.name() == 'python':
						if os.path.basename(p.cmdline()[1]) == 'syncrmt':
							continue
						log.info('{:>6d} {:<8s} {} {}'.format(p.pid,
						                                      p.terminal(),
						                                      os.path.basename(cmdline),
						                                      cmdline))
					elif p.name == 'rsync':
						log.info('{:>6d} {:<8s} {} {}'.format(p.pid,
						                                      p.terminal(),
						                                      p.name(),
						                                      cmdline))
			except:
				pass


if __name__ == '__main__':

	logger.initialize()
	common = chkStatus()

	Common.args = Common.options.parser.parse_args(sys.argv[1:])
	log.debug("Parsed command line: {!s}".format(common.args))

	log_level = logging.getLevelName(common.args.loglevel.upper())

	if common.args.logfile == 'daddyvision.log':
		log_file = '{}.log'.format(__pgmname__)
	else:
		log_file = os.path.expanduser(common.args.logfile)

	# If an absolute path is not specified, use the default directory.
	if not os.path.isabs(log_file):
		log_file = os.path.join(logger.LogDir, log_file)

	logger.start(log_file, log_level, timed=True)

	common.check()
	sys.exit(0)
