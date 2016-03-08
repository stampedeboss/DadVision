#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Purpose:
Program to rename files associated with Movie Content

"""
import logging
import os
import sys

import tmdb3

from common.exceptions import MovieNotFound, GetOutOfLoop
from library import matching
from dadvision.library.movie import Movie

__pgmname__ = 'tmdbinfo'

__author__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"

__maintainer__ = __author__

__copyright__ = "Copyright 2016, AJ Reynolds"
__license__ = "GPL"

log = logging.getLogger(__pgmname__)

class TMDBInfo(Movie):
	"""

	:return:
	"""

	def __init__(self):

		super(TMDBInfo, self).__init__()

		return

	def check_movie_names(self, pathname):
		log.trace("=================================================")
		log.trace("check_movie_names method: pathname:{}".format(pathname))

		pathname = os.path.abspath(pathname)

		if os.path.isfile(pathname):
			log.debug("-----------------------------------------------")
			log.debug("Movie Directory: %s" % os.path.split(pathname)[0])
			log.debug("Movie Filename:  %s" % os.path.split(pathname)[1])
			self.check_file(pathname)
		elif os.path.isdir(pathname):
			log.debug("-----------------------------------------------")
			log.debug("Movie Directory: %s" % pathname)
			for _root, _dirs, _files in os.walk(os.path.abspath(pathname)):
				_dirs.sort()
				for _dir in _dirs[:]:
					# Process Enbedded Directories
					if self.Library._ignored(_dir):
						_dirs.remove(_dir)

				_files.sort()
				for _file in _files:
					# _path_name = os.path.join(_root, _file)
					log.trace("Movie Filename: %s" % _file)
					if self.Library._ignored(_file):
						continue
					self.check_file(_root, _file)
		return None

	def check_file(self, directory, filename):
		pathname = os.path.join(directory, filename)
		try:
			# Get Directory Details
			_dir_details = parser.getFileDetails(os.path.join(directory, directory + ".mkv"))
			_dir_answer = library.tmdb(_dir_details)

			# Get File Details
			_file_details = parser.getFileDetails(filename)
			_file_answer = library.tmdb(_file_details)
		except Exception:
			log.error('MovieNotFound {}'.format(os.path.join(directory, filename)))
			# an_error = traceback.format_exc(1)
			#			log.error(traceback.format_exception_only(type(an_error), an_error)[-1])
			#			print 'Exception in user code:'
			#			print '-'*60
			#			traceback.print_exc(file=sys.stdout)
			#			print '-'*60
			sys.exc_clear()
			return

		if _dir_details['Year'] != _dir_answer['Year']:
			log.info('Rename Required: {} (Year) (Current) - Directory'.format(os.path.basename(directory)))
			log.info('                 {MovieName} ({Year})'.format(**_dir_answer))

		if os.path.basename(directory) != '{MovieName} ({Year})'.format(**_dir_answer):
			log.info('Rename Required: {} (Current) - Directory'.format(os.path.basename(directory)))
			log.info('                 {MovieName} ({Year})'.format(**_dir_answer))

		if _file_details['Year'] != _file_answer['Year']:
			log.info('Rename Required: {} (Year) (Current)'.format(filename))
			log.info('                 {MovieName} ({Year})'.format(**_file_answer))

		test1 = os.path.splitext(filename)[0]
		test2 = '{MovieName} ({Year})'.format(**_file_answer)
		_part = self._check_part.match(test1)
		if _part:
			test1 = _part.group('MovieName').rstrip()
		if test1 != test2:
			log.info('Rename Required: {} (Current)'.format(filename))
			log.info('                 {MovieName} ({Year})'.format(**_file_answer))

		s = pathname.decode('ascii', 'ignore')
		if s != pathname:
			log.warning('INVALID CHARs: {} vs {}'.format(pathname - s, pathname))


if __name__ == "__main__":

	from sys import argv
	from dadvision import DadVision
	from logging import DEBUG; TRACE = 5; VERBOSE = 15
	from common import logger
	logger.initialize(level=DEBUG)
	DadVision.args = DadVision.cmdoptions.ParseArgs(argv[1:])

	logger.start(DadVision.args.logfile, DEBUG, timed=DadVision.args.timed)

	tmdbinfo = TMDBInfo()

	DadVision.settings.IgnoreGlob.extend(['*.ifo', '*.bup', '*.vob'])

	_MovieDetails = {}
	_answer = ''

	if Library.args.Year:
		_MovieDetails['Year'] = Library.args.Year
	if Library.args.MovieName:
		_MovieDetails['MovieName'] = Library.args.MovieName
		_answer = tmdbinfo.retrieve_tmdb_info(_MovieDetails)
		log.info(_answer)
		sys.exit(0)
	elif len(Library.args.filespec) > 0 and 'MovieName' not in _MovieDetails:
		for pathname in Library.args.filespec:
			_MovieDetails = fileinfo.get_movie_details(pathname)
			_MovieDetails = tmdbinfo.retrieve_tmdb_info(_MovieDetails)
