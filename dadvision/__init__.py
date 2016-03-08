# -*- coding: UTF-8 -*-
'''

Purpose:
	Initialization Routine for DadVision

	Setup of standard Logging and Command Line Options

'''

from common.cmdoptions import CmdOptions
from common.settings import Settings

__pgmname__     = 'dadvision'

__author__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"

__maintainer__ = __author__

__copyright__ = "Copyright 2016, AJ Reynolds"
__license__ = "GPL"


class DadVision(object):

	from common import logger
	settings = Settings()
	cmdoptions = CmdOptions()
	args = {}


	def __init__(self):
		super(DadVision, self).__init__()


if __name__ == '__main__':

	from sys import argv
	from dadvision import DadVision
	from logging import INFO, DEBUG, ERROR; TRACE = 5; VERBOSE = 15
	from common import logger
	logger.initialize(level=DEBUG)
	DadVision.args = DadVision.cmdoptions.ParseArgs(argv[1:])

	log = logger.logging.getLogger(__pgmname__)
	logger.start(DadVision.args.logfile, DadVision.args.loglevel, timed=DadVision.args.timed)

	log.verbose("*** LOGGING STARTED ***")

	_lib_paths = DadVision.args.pathname

	pass