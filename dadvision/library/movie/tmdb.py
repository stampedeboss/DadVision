#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Purpose:
Program to retrieve movie information from TMDB

"""
import logging
import tmdb3

from common.exceptions import MovieNotFound, GetOutOfLoop
from library import decode, matching

from dadvision import DadVision
from library.movie import Movie

__pgmname__ = 'TMDB'

__author__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"

__maintainer__ = __author__

__copyright__ = "Copyright 2011, AJ Reynolds"
__license__ = "GPL"

log = logging.getLogger(__pgmname__)


class TMDB(Movie):

	tmdb3.set_key('587c13e576f991c0a653f783b290a065')
	tmdb3.set_cache(filename='tmdb3.cache')

	def __init__(self, **kwargs):

		super(TMDB, self).__init__(**kwargs)

		return

	def tmdb(self):

		if self.year:
			_movie = '{} ({})'.format(self.title, self.year)
			try:
				self.review_entries(list(tmdb3.searchMovieWithYear(_movie)))
				return
			except MovieNotFound:
				pass
		self.review_entries(list(tmdb3.searchMovie(self.title)))
		return self

	def review_entries(self, tmdb_results):

		"""
		:param tmdb_results:
		:param chkyear:
		:return: :raise MovieNotFound:
		"""

		try:
			for _movie in tmdb_results:
				_title = decode(_movie.title)
				if self.year:
					if matching(" ".join([_title.lower(), str(_movie.releasedate.year)]),
								" ".join([self.title.lower(), str(self.year)])):
						self.title = _title
						raise GetOutOfLoop(_movie)
				if matching(_title.lower(), self.title.lower()):
					self.title = _title
					raise GetOutOfLoop(_movie)
				else:
				# Check Alternate Titles: list(AlternateTitle) alternate_titles
					for _alternate_title in _movie.alternate_titles:
						log.trace('Check Alternate Titles: {}'.format(_alternate_title))
						_alternate_title = decode(_alternate_title)
						if matching(_alternate_title, self.title):
							_movie.alternate_titles.append(_title)
							self.title = _alternate_title
							self.alternate_title = _movie.alternate_titles
							raise GetOutOfLoop(_movie)
			log.warn("Movie Not Found in TMDb: {}".format(self.title))
			raise MovieNotFound("Movie Not Found in TMDb: {}".format(self.title))
		except GetOutOfLoop, e:
			_movie = e.message
			if _movie.releasedate:
				if self.year:
					if (-2 < (self.year - _movie.releasedate.year) < 2):
						self.year = _movie.releasedate.year
					else:
						msg = "Movie name found, Years too far apart: {} - {}/{}".format(self.title,
																						 self.year,
																						 _movie.releasedate.year)
						log.warning(msg)
						raise MovieNotFound(msg)
				else:
					self.year = _movie.releasedate.year

			log.trace("Movie Located in TMDB")
			self.tmdb_id = _movie.id
			self.imdb_id = _movie.imdb
			self.slug = self.title
			self.cast = _movie.cast
			if hasattr(_movie, "alternate_titles"):
				self.alternate_title = _movie.alternate_titles

		return


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
