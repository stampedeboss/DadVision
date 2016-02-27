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
from common.matching import matching
from dadvision.library import Library

__pgmname__ = 'gettmdb'

__author__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"

__maintainer__ = __author__

__copyright__ = "Copyright 2011, AJ Reynolds"
__license__ = "GPL"

log = logging.getLogger(__pgmname__)


def uselibrarylogging(func):
	def wrapper(self, *args, **kw):
		"""
		Set the library name in the logger

		:param self:
		:param args:
		:param kw:
		:return:
		"""
		logger.set_library('movie')
		try:
			return func(self, *args, **kw)
		finally:
			logger.set_library('')

	return wrapper


class TMDBInfo(Library):
	"""

	:return:
	"""

	def __init__(self):

		super(TMDBInfo, self).__init__()

		TMDB_group = TMDBInfo.cmdoptions.parser.add_argument_group("Get TMDB Information Options",
																		   description=None)
		TMDB_group.add_argument("--movie", type=str, dest='MovieName', nargs='?')
		TMDB_group.add_argument("--year", type=int, dest='Year', nargs='?')

		tmdb3.set_key('587c13e576f991c0a653f783b290a065')
		tmdb3.set_cache(filename='tmdb3.cache')

		return

	def retrieve_tmdb_info(self, request):
		"""

		:param request:
		:return:
		:raise MovieNotFound:
		"""

		if Library.args.MovieName:
			request['title'] = Library.args.MovieName
		if TMDBInfo.args.Year:
			request['year'] = int(Library.args.Year)

		try:
			if 'year' in request:
				_movie = '{title} ({year})'.format(**request)
				tmdb_details = list(tmdb3.searchMovieWithYear(_movie))
				try:
					tmdb_details = self.review_entries(tmdb_details, request)
					if not tmdb_details:
						raise MovieNotFound("Movie Not Found in TMDb: {}".format(request['title']))
				except MovieNotFound:
					tmdb_details = list(tmdb3.searchMovie(request['title']))
					if not tmdb_details:
						raise MovieNotFound("Movie Not Found in TMDb: {}".format(request['title']))
					try:
						request = self.review_entries(tmdb_details, request)
					except MovieNotFound:
						raise
			else:
				tmdb_details = list(tmdb3.searchMovie(request['title']))
				request = self.review_entries(tmdb_details, request)
		except MovieNotFound:
			raise

		return request

	def review_entries(self, tmdbDetails, request):

		"""

		:param tmdbDetails:
		:param request:
		:param chkyear:
		:return: :raise MovieNotFound:
		"""

		try:
			for _movie in tmdbDetails:
				_title = self.decode(_movie.title)

				if 'year' in request:
					if matching(" ".join([_title.lower(), str(_movie.releasedate.year)]),
								" ".join([request['title'].lower(), str(request['year'])])):
						request['title'] = _title
						raise GetOutOfLoop
				else:
					if matching(_title.lower(), request['title'].lower()):
						request['title'] = _title
						raise GetOutOfLoop
				# Check Alternate Titles: list(AlternateTitle) alternate_titles
				for _alternate_title in _movie.alternate_titles:
					log.trace('Check Alternate Titles: {}'.format(_alternate_title))
					_alternate_title = self.decode(_alternate_title)
					if _alternate_title and matching(_alternate_title, request['title']):
						request['title'] = _alternate_title
						request['alternate_title'] = _title
						raise GetOutOfLoop
			log.warn("Movie Not Found in TMDb: {}".format(request['title']))
			raise MovieNotFound("Movie Not Found in TMDb: {}".format(request['title']))
		except GetOutOfLoop:
			if _movie.releasedate:
				request['releasedate'] = _movie.releasedate
				if 'year' in request:
					if (-2 < (request['year'] - _movie.releasedate.year) < 2):
						request['year'] = _movie.releasedate.year
					else:
						msg = "Movie name found, Years too far apart: {} - {}/{}".format(request['title'],
																						 request['year'],
																						 _movie.releasedate.year)
						log.warning(msg)
						raise MovieNotFound(msg)
				else:
					request['year'] = _movie.releasedate.year

		request['tmdb_id'] = _movie.id
		request['imdb_id'] = _movie.imdb
		request['cast'] = _movie.cast

		log.trace("Movie Located in TMDB")
		return request

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
					if self._ignored(_dir):
						_dirs.remove(_dir)

				_files.sort()
				for _file in _files:
					# _path_name = os.path.join(_root, _file)
					log.trace("Movie Filename: %s" % _file)
					if self._ignored(_file):
						continue
					self.check_file(_root, _file)
		return None

	def check_file(self, directory, filename):
		pathname = os.path.join(directory, filename)
		try:
			# Get Directory Details
			_dir_details = parser.getFileDetails(os.path.join(directory, directory + ".mkv"))
			_dir_answer = library.retrieve_tmdb_info(_dir_details)

			# Get File Details
			_file_details = parser.getFileDetails(filename)
			_file_answer = library.retrieve_tmdb_info(_file_details)
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

	tmdbinfo = TMDBInfo()

	Library.args = Library.cmdoptions.ParseArgs(sys.argv[1:])
	Library.settings.IgnoreGlob.extend(['*.ifo', '*.bup', '*.vob'])

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
