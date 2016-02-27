#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Purpose:
Program to rename files associated with Movie Content

"""
import sys
import logging
import tmdb3
from common.exceptions import MovieNotFound, GetOutOfLoop
from common.matching import matching

from library.movie import Movie

__pgmname__ = 'tmdbinfo'

__author__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"

__maintainer__ = __author__

__copyright__ = "Copyright 2011, AJ Reynolds"
__license__ = "GPL"

log = logging.getLogger(__pgmname__)


class TMDBInfo(Movie):

	def __init__(self):

		super(TMDBInfo, self).__init__()

		tmdb3.set_key('587c13e576f991c0a653f783b290a065')
		tmdb3.set_cache(filename='tmdb3.cache')

		return

	def retrieve_tmdb_info(self):

		try:
			if self.year:
				_movie = '{title} ({year})'.format(self.title, self.year)
				tmdb_details = list(tmdb3.searchMovieWithYear(_movie))
				try:
					+++++++++++++++++++++++++++++++630+
		*0*+-			-


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


if __name__ == "__main__":

	from movie.fileinfo import FileInfo
	logger.initialize()

	TMDB_group = TMDBInfo.cmdoptions.parser.add_argument_group("Get TMDB Information Options",
																	   description=None)
	TMDB_group.add_argument("--movie", type=str, dest='MovieName', nargs='?')
	TMDB_group.add_argument("--year", type=int, dest='Year', nargs='?')

	fileinfo = FileInfo()
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
			log.info(tmdbinfo.retrieve_tmdb_info(_MovieDetails))
