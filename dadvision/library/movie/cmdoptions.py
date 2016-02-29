#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Purpose:

"""

from dadvision import DadVision

__pgmname__ = 'cmdoptions'

__author__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"

__maintainer__ = __author__

__copyright__ = "Copyright 2016, AJ Reynolds"
__license__ = "GPL"


class CmdOptions(DadVision):
	def __init__(self, id=None, **kwargs):
		super(CmdOptions, self).__init__()

		movie_group = DadVision.cmdoptions.parser.add_argument_group("Movie Overrides", description=None)
		movie_group.add_argument("--movie", type=str, dest='MovieName', nargs='?')
		movie_group.add_argument("--year", type=int, dest='Year', nargs='?')


if __name__ == '__main__':
	from sys import argv
	from logging import DEBUG; TRACE = 5; VERBOSE = 15
	DadVision.logger.initialize(level=DEBUG)

	from common.cmdoptions_rn import CmdOptionsRn
	movieOpts = CmdOptions()
	renameOpts = CmdOptionsRn()

	DadVision.args = DadVision.cmdoptions.ParseArgs(argv[1:])
	DadVision.logger.start(DadVision.args.logfile, DEBUG, timed=DadVision.args.timed)

	if len(DadVision.args.pathname) > 0:
		for pathname in DadVision.args.pathname:
			pass
