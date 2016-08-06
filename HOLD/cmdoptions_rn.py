#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Purpose:

"""

from dadvision import DadVision

__pgmname__ = 'rename_cmdoptions'

__author__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"

__maintainer__ = __author__

__copyright__ = "Copyright 2016, AJ Reynolds"
__license__ = "GPL"


class CmdOptionsRn(DadVision):
	def __init__(self, id=None, **kwargs):
		super(CmdOptionsRn, self).__init__()

		rename_group = DadVision.cmdoptions.parser.add_argument_group("Rename Options", description=None)
		rename_group.add_argument("--force-rename", dest="force_rename",
									action="store_true", default=False,
									help="Force Renames for Files That Already Exist")
		rename_group.add_argument("--force-delete", "--fd", dest="force_delete",
									action="store_true", default=False,
									help="Force Deletes for Files That Already Exist")
		rename_group.add_argument("--ignore_excludes", dest="ignore_excludes",
									action="store_true", default=False,
									help="Process all Files Regardless of Excludes")
		rename_group.add_argument("--no-check_video", dest="check_video",
									action="store_false", default=True,
									help="Bypass Video Checks")
		rename_group.add_argument("--no-move", "--nm", dest="move",
									action="store_false", default=True,
									help="Do not change directories, rename in place")
		rename_group.add_argument("--dir", type=str, dest='dir',
									nargs='?', default=None,
									help="Rename and place in this directory")


if __name__ == '__main__':
	from sys import argv
	from logging import DEBUG; TRACE = 5; VERBOSE = 15
	DadVision.logger.initialize(level=DEBUG)

	movieOpts = CmdOptions()

	DadVision.args = DadVision.cmdoptions.ParseArgs(argv[1:])
	DadVision.logger.start(DadVision.args.logfile, DEBUG, timed=DadVision.args.timed)

	if len(DadVision.args.pathname) > 0:
		for pathname in DadVision.args.pathname:
			pass
