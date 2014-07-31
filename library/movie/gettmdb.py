#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Purpose:
Program to rename files associated with Movie Content

"""
from library import Library
from common import logger
from common.exceptions import MovieNotFound, DictKeyError, InvalidArgumentType
from fuzzywuzzy import fuzz
import logging
import os
import re
import sys
import tmdb3
import unicodedata

__pgmname__ = 'gettmdb'
__version__ = '$Rev: 341 $'

__author__ = "@author: AJ Reynolds"
__copyright__ = "@copyright: Copyright 2014, AJ Reynolds"
__license__ = "@license: GPL"
__email__ = "@contact: stampedeboss@gmail.com"

__maintainer__ = "@organization: AJ Reynolds"
__status__ = "@status: Development"
__credits__ = []

log = logging.getLogger(__pgmname__)


def uselibrarylogging(func):
	"""

	:param func:
	:return:
	"""

	def wrapper(self, *args, **kw):
		# Set the library name in the logger
		# from daddyvision.common import logger
		"""

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
		log.trace("INIT: =================================================")
		log.trace('TMDBInfo.__init__ method: Started')

		super(TMDBInfo, self).__init__()

		TMDB_group = self.options.parser.add_argument_group("Get TMDB Information Options", description=None)
		TMDB_group.add_argument("--movie", type=str, dest='MovieName', nargs='?')
		TMDB_group.add_argument("--year", type=int, dest='Year', nargs='?')

		tmdb3.set_key('587c13e576f991c0a653f783b290a065')
		tmdb3.set_cache(filename='tmdb3.cache')

		self._check_suffix = re.compile('^(?P<MovieName>.+?)[ \._\-\(]*?(?P<Year>[1|2][0|9]\d\d)(:P.*)?', re.VERBOSE)

		return

	@uselibrarylogging
	def retrieve_info(self, request):
		"""

		:param request:
		:return: :raise MovieNotFound:
		"""
		log.trace("=================================================")
		log.trace("retrieve_info method: request:{}".format(request))

		moviedetails = request
		if type(moviedetails) == dict:
			if 'MovieName' in moviedetails and moviedetails['MovieName'] is None:
				error_msg = 'LocaateMovie: Request Missing "MovieName" Value: {!s}'.format(moviedetails)
				log.trace(error_msg)
				raise DictKeyError(error_msg)
		else:
			error_msg = 'retrieve_info: Invalid object type passed, must be DICT, received: {}'.format(
				type(moviedetails))
			log.trace(error_msg)
			raise InvalidArgumentType(error_msg)

		if self.args.MovieName:
			moviedetails['MovieName'] = self.args.MovieName
		if self.args.Year:
			moviedetails['Year'] = self.args.Year

		_suffix = self._check_suffix.match(moviedetails['MovieName'])
		if _suffix:
			moviedetails['MovieName'] = '{} '.format(_suffix.group('MovieName')).rstrip()
			if 'Year' not in moviedetails:
				moviedetails['Year'] = '{}'.format(_suffix.group('Year').upper())
			log.debug('retrieve_info: Request: Modified {}'.format(moviedetails))

		try:
			moviedetails = self._get_details(moviedetails)
		except MovieNotFound:
			raise MovieNotFound("Movie Not Found in TMDb: {}".format(moviedetails['MovieName']))

		return moviedetails

	@uselibrarylogging
	def _get_details(self, moviedetails):
		log.trace("=================================================")
		log.trace("_get_details: Movie Details:{!s}".format(moviedetails))

		if 'Year' in moviedetails:
			_movie = '{MovieName} ({Year})'.format(**moviedetails)
			tmdb_details = list(tmdb3.searchMovieWithYear(_movie))
			try:
				moviedetails = self.review_entries(tmdb_details, moviedetails, False)
			except MovieNotFound:
				tmdb_details = list(tmdb3.searchMovie(moviedetails['MovieName']))
				if not tmdb_details:
					raise MovieNotFound("Movie Not Found in TMDb: {}".format(moviedetails['MovieName']))
				moviedetails = self.review_entries(tmdb_details, moviedetails, True)
		else:
			tmdb_details = list(tmdb3.searchMovie(moviedetails['MovieName']))
			moviedetails = self.review_entries(tmdb_details, moviedetails, False)

		return moviedetails

	@staticmethod
	def review_entries(tmdbDetails, moviedetails, chkyear):

		"""

		:param tmdbDetails:
		:param moviedetails:
		:param chkyear:
		:return: :raise MovieNotFound:
		"""
		log.trace("=================================================")
		log.trace('Reviewing TMDB Details: {}'.format(tmdbDetails))

		if not tmdbDetails:
			raise MovieNotFound("Movie Not Found in TMDb: {}".format(moviedetails['MovieName']))

		_title = ''
		try:
			for _movie in tmdbDetails:
				_title = unicodedata.normalize('NFKD', _movie.title).encode("ascii", 'ignore')
				_title = _title.replace("&amp;", "&").replace("/", "_")

				if 'Year' in moviedetails:
					if _matching(_title + ' ' + str(_movie.releasedate.year),
								 moviedetails['MovieName'] + ' ' + str(moviedetails['Year'])):
						raise GetOutOfLoop
				else:
					if _matching(_title, moviedetails['MovieName']):
						raise GetOutOfLoop
		except GetOutOfLoop:
			if not _matching(_title, moviedetails['MovieName']):
				# Check Alternate Titles: list(AlternateTitle) alternate_titles
				try:
					_alt_title = _movie.alternate_titles
					for _alt_title in _movie.alternate_titles:
						log.trace('Check Alternate Titles: {}'.format(_alt_title.title))
						_alt_title = unicodedata.normalize('NFKD', _alt_title.title).encode("ascii", 'ignore')
						_alt_title = _alt_title.replace("&amp;", "&").replace("/", "_")
						if _matching(_alt_title, moviedetails['MovieName']):
							raise GetOutOfLoop
					log.warn("Movie Not Found in TMDb: {}".format(moviedetails['MovieName']))
					raise MovieNotFound("Movie Not Found in TMDb: {}".format(moviedetails['MovieName']))
				except GetOutOfLoop:
					moviedetails['AltMovieName'] = _alt_title

		moviedetails['MovieName'] = _title
		if _movie.releasedate:
			if chkyear and not -2 < (int(moviedetails['Year']) - _movie.releasedate.year) < 2:
				raise MovieNotFound("Movie Not Found in TMDb: {}".format(moviedetails['MovieName']))
			moviedetails['Year'] = str(_movie.releasedate.year)

			log.trace("Movie Located in TMDB")
			return moviedetails
		raise MovieNotFound("Movie Not Found in TMDb: {}".format(moviedetails['MovieName']))


@uselibrarylogging
def _matching(value1, value2):
	log.trace("=================================================")
	log.trace("_matching: Compare: {} --> {}".format(value1, value2))

	fuzzy = [fuzz.ratio(value1, value2), fuzz.token_set_ratio(value1, value2), fuzz.token_sort_ratio(value1, value2),
			 fuzz.token_set_ratio(value1, value2)]

	log.debug('fuzzy Ratio" {} for {} - {}'.format(fuzzy[0], value1, value2))
	log.debug('fuzzy Partial Ratio" {} for {} - {}'.format(fuzzy[1], value1, value2))
	log.debug('fuzzy Token Sort Ratio" {} for {} - {}'.format(fuzzy[2], value1, value2))
	log.debug('fuzzy Token Set Ratio" {} for {} - {}'.format(fuzzy[3], value1, value2))

	return any([fr > 85 for fr in fuzzy])

class GetOutOfLoop(Exception):
	pass


if __name__ == "__main__":

	logger.initialize()
	log.trace("MAIN: -------------------------------------------------")
	from library.movie.fileparser import FileParser
	from library.movie.rename import RenameMovie

	library = TMDBInfo()
	parser = FileParser()
	rename = RenameMovie()
	__main__group = library.options.parser.add_argument_group("Get TMDB Information Options", description=None)
	__main__group.add_argument("--pickle", dest="pickleIt",
							   action="store_true", default=False,
							   help="Force Renames for Files That Already Exist")

	Library.args = library.options.parser.parse_args(sys.argv[1:])
	log.debug("Parsed command line: {!s}".format(library.args))

	log_level = logging.getLevelName(library.args.loglevel.upper())

	if library.args.logfile == 'daddyvision.log':
		log_file = '{}.log'.format(__pgmname__)
	else:
		log_file = os.path.expanduser(library.args.logfile)

	# If an absolute path is not specified, use the default directory.
	if not os.path.isabs(log_file):
		log_file = os.path.join(logger.LogDir, log_file)

	logger.start(log_file, log_level, timed=True)

	_MovieDetails = {}
	_answer = ''
	if library.args.Year:
		_MovieDetails['Year'] = library.args.Year
	if library.args.MovieName:
		_MovieDetails['MovieName'] = library.args.MovieName
		_answer = library.retrieve_info(_MovieDetails)
		log.info(_answer)
		sys.exit(0)
	elif len(library.args.library) > 0 and 'MovieName' not in _MovieDetails:
		for pathname in library.args.library:
			if os.path.isfile(pathname):
				_file_details = parser.getFileDetails(pathname)
				_answer = library.retrieve_info(_MovieDetails)
				log.info(_answer)
				sys.exit(0)
			else:
				for _path in os.listdir(os.path.abspath(pathname)):
					try:
						_file_details = parser.getFileDetails(os.path.join(pathname, _path, _path+'.mkv'))
						_answer = library.retrieve_info(_file_details)
						if int(_file_details['Year'])-int(_answer['Year']) != 0:
							log.warning('Rename Required: {} (Current)'.format(_path))
							log.warning('                 {MovieName} ({Year})'.format(**_answer))
#						    rename.renameMovie(os.path.joing(pathname, _path))
						if _path != '{MovieName} ({Year})'.format(**_answer):
							log.warning('Rename Required: {} (Current)'.format(_path))
							log.warning('                 {MovieName} ({Year})'.format(**_answer))

						# 	s = str(_path.decode('ascii', 'ignore'))
						# 	if s != _path:
						# 		log.error('INVALID NAME: {} - {}'.format(_path-s, _path))

#							log.info(_answer)
					except Exception:
						log.warning('MovieNotFound {}'.format(_path))
						sys.exc_clear()
				sys.exit(0)

