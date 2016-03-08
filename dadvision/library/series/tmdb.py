#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Purpose:
Program to retrieve movie information from TMDB

"""
import logging
import traceback
from common.exceptions import SeriesNotFound, SeasonNotFound, EpisodeNotFound, GetOutOfLoop
from library import decode, matching

from dadvision import DadVision
from library.series import Series

__pgmname__ = 'TMDB'

__author__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"

__maintainer__ = __author__

__copyright__ = "Copyright 2011, AJ Reynolds"
__license__ = "GPL"

log = logging.getLogger(__pgmname__)


class TMDB(Series):

	def __init__(self, **kwargs):

		super(TMDB, self).__init__(**kwargs)

		return

	def tmdb(self):


if __name__ == "__main__":

	from sys import argv
	from common import logger
	from logging import DEBUG; TRACE = 5; VERBOSE = 15
	logger.initialize(level=DEBUG)
	DadVision.args = DadVision.cmdoptions.ParseArgs(argv[1:])

	logger.start(DadVision.args.logfile, DEBUG, timed=DadVision.args.timed)

	movie = TMDB()

	if len(DadVision.args.pathname) > 0:
		for pathname in DadVision.args.pathname:
			movie.media_details(pathname)
			movie = movie.tmdb()
