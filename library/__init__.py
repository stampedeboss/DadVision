# -*- coding: UTF-8 -*-
'''
	Initialization Routine for library

	Routine is call on any import of a module in the library

'''

from common import logger
from common.cmdoptions import CmdOptions
from common.settings import Settings

__pgmname__     = 'library.__init__'
__version__     = '@version: $Rev$'

__author__      = "@author: AJ Reynolds"
__copyright__   = "@copyright: Copyright 2011, AJ Reynolds"
__license__     = "@license: GPL"

__maintainer__  = "@organization: AJ Reynolds"
__status__      = "@status: Development"
__credits__     = []


class Library(object):

	def __init__(self):
		self.settings = Settings()
		self.cmdoptions = CmdOptions()
		self.args = {}
		pass


if __name__ == '__main__':

	import os
	import sys
	logger.initialize()
	log = logger.logging.getLogger(__pgmname__)

	library = Library()

	library.args = library.cmdoptions.parser.parse_args(sys.argv[1:])
	log.debug("Parsed command line: {!s}".format(library.args))

	log_level = logger.logging.getLevelName(library.args.loglevel.upper())

	if library.args.logfile == 'daddyvision.log':
		log_file = '{}.log'.format('check_movie')
	else:
		log_file = os.path.expanduser(library.args.logfile)

	# If an absolute path is not specified, use the default directory.
	if not os.path.isabs(log_file):
		log_file = os.path.join(logger.LogDir, log_file)

	logger.start(log_file, log_level, timed=False)

	_lib_paths = library.args.library

	pass