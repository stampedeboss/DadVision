#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Purpose:
	 Obtain movie information from filename
"""
from __future__ import division

import logging
import os

from guessit import guessit
from titlecase import titlecase

from common.exceptions import MovieNotFound
from library.movie import Movie
from common import logger

__pgmname__ = 'fileinfo'

__author__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"

__maintainer__ = __author__

__copyright__ = "Copyright 2016, AJ Reynolds"
__license__ = "GPL"

log = logging.getLogger(__pgmname__)

def uselibrarylogging(func):
	def wrapper(self, *args, **kw):
		logger.set_library('movie')
		try:
			return func(self, *args, **kw)
		finally:
			logger.set_library('')
	return wrapper


class FileInfo(Movie):
	"""
	"""

	def __init__(self, **kwargs):

		super(FileInfo, self).__init__(**kwargs)

	@classmethod
	#@uselibrarylogging
	def get_movie_details(self, fq_name):

		_path, _file_name = os.path.split(fq_name)
		_movie_details = guessit(_file_name, '-t movie')

		if 'alternative_title' in _movie_details:
			_save_title = _movie_details['title']
			_movie_details['title'] = _movie_details['alternative_title']
			_movie_details['alternative_title'] = _save_title
		if 'title' in _movie_details:
			_movie_details['title'] = titlecase(_movie_details['title'])
		else:
			raise MovieNotFound('Guessit unable to determine title')

		_movie_details["filename"] = fq_name

		_rtn = FileInfo(_movie_details)

		return _rtn


if __name__ == '__main__':

	import sys
	from library import Library

	Library.args = Library.cmdoptions.ParseArgs(sys.argv[1:])

	movies = FileInfo()

	if Library.args.filespec:
		_answer = movies.get_movie_details(Library.args.filespec[0])
		print
		print _answer
