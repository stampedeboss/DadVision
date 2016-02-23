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

__copyright__ = "Copyright 2011, AJ Reynolds"
__license__ = "GPL"


class DadVision(object):

	from common import logger

	settings = Settings()
	cmdoptions = CmdOptions()
	args = {}

	logger.initialize()

	def __init__(self):
		super(DadVision, self).__init__()


if __name__ == '__main__':

	import sys
	log = DadVision.logger.logging.getLogger(__pgmname__)
	DadVision.logger.initialize()

	DadVision.args = DadVision.cmdoptions.ParseArgs(sys.argv[1:])

	log.verbose("*** LOGGING STARTED ***")

	_lib_paths = DadVision.args.filespec

	pass