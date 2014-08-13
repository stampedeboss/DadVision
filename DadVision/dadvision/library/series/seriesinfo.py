#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Purpose:
		Configuration and Run-time settings for the XBMC Support Programs
"""
from library import Library
from pytvdbapi.error import TVDBAttributeError, TVDBIndexError, TVDBValueError
from common.exceptions import InvalidArgumentType, DictKeyError, DataRetrievalError
from common.exceptions import SeriesNotFound, EpisodeNotFound, EpisodeNameNotFound
from common import logger
from fuzzywuzzy import fuzz
import datetime
import difflib
import errno
import logging
import os.path
import re
import sys
import fnmatch
import unicodedata

import trakt
from trakt.users import User, UserList
from trakt.tv import TVShow, TVSeason, TVEpisode, trending_shows, TraktRating, TraktStats, rate_shows, rate_episodes, genres, get_recommended_shows, dismiss_recommendation

from pytvdbapi import api
from TVRage import TVRage, Show, ShowInfo, Season, EpisodeList, Episode, EpisodeInfo
#from tvrage import feeds
#from xml.etree.ElementTree import tostring

__pgmname__ = 'seriesinfo'
__version__ = '@version: $Rev$'

__author__ = "@author: AJ Reynolds"
__email__ = "@contact: stampedeboss@gmail.com"
__copyright__ = "@copyright: Copyright 2014, AJ Reynolds"
__license__ = "@license: GPL"

__maintainer__ = "@organization: AJ Reynolds"
__status__ = "@status: Development"
__credits__ = []

FlexGetConfig = os.path.join(os.path.expanduser('~'), '.flexget', 'config.series')
log = logging.getLogger(__pgmname__)


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


def _ignored(name):
	""" Check for ignored pathnames.
	"""
	rc = []
	if name == 'New': rc.append(True)
	rc.append(any(fnmatch.fnmatch(name.lower(), pattern) for pattern in library.settings.ExcludeList))
	rc.append(any(fnmatch.fnmatch(name.lower(), pattern) for pattern in library.settings.IgnoreGlob))
	return any(rc)


class SeriesInfo(Library):

	def __init__(self):
		log.trace('SeriesInfo.__init__')

		super(SeriesInfo, self).__init__()

		seriesinfo_group = self.options.parser.add_argument_group("Episode Detail Options", description=None)
		seriesinfo_group.add_argument("--series-name", type=str, dest='series_name')
		seriesinfo_group.add_argument("--season", type=int, dest='season')
		seriesinfo_group.add_argument("--epno", type=int, action='append', dest='epno')
		seriesinfo_group.add_argument("--tvrage", dest="tvrage",
				action="store_true", default=False,
				help="Force information to come from TVRage")
		seriesinfo_group.add_argument("--tvdb", dest="tvdb",
				action="store_true", default=False,
				help="Force information to come from TVDB")

		trakt.api_key = self.settings.TraktAPIKey
		trakt.authenticate(self.settings.TraktUserID, self.settings.TraktPassWord)
		self.db = api.TVDB("959D8E76B796A1FB")
		self.tvrage = TVRage(api_key='XwJ7KGdTfep9EpsZBf8m')

		self._check_suffix = re.compile('^(?P<SeriesName>.*)[ \._\-][\(]?(?P<year>(?:19|20)\d{2}|us).*$', re.I)
		self.confidenceFactor = 90
		self.last_request = {'LastRequestName': ''}

	def getShowInfo(self, request):
		log.trace('getShowInfo: Input Parm: {}'.format(request))

		if type(request) == dict:
			if 'SeriesName' in request and request['SeriesName'] is not None:
				_suffix = self._check_suffix.match(request['SeriesName'].rstrip())
				if _suffix:
					_series_name = '{} ({})'.format(_suffix.group('SeriesName'), _suffix.group('year').upper())
					request['SeriesName'] = _series_name.rstrip()
					log.debug('getDetailsAll: Request: Modified %s' % request)
				SeriesDetails = request
			else:
				error_msg = 'getDetails: Request Missing "SeriesName" Key: {!s}'.format(request)
				log.trace(error_msg)
				raise DictKeyError(error_msg)
		else:
			error_msg = 'getDetails: Invalid object type passed, must be DICT, received: {}'.format(type(request))
			log.trace(error_msg)
			raise InvalidArgumentType(error_msg)

		SeriesDetails = self._adj_episode(SeriesDetails)

		#Valid Request: Locate Show IDs
		SeriesDetails = self._identify_show(SeriesDetails)

		if 'TVDBSeriesID' in SeriesDetails :
			try:
				SeriesDetails = self.getEpisodeInfo(SeriesDetails)
				log.debug('getSeriesInfo: Series Data Returned: {!s}'.format(SeriesDetails))
			except SeriesNotFound:
				SeriesDetails = self._retrieve_tvrage_info(SeriesDetails)
		elif 'tvrage_id' in SeriesDetails:
			self._retrieve_tvrage_info(SeriesDetails)

		return SeriesDetails

	def _identify_show(self, SeriesDetails):

		_series_name = SeriesDetails['SeriesName'].rstrip()
		if self.last_request['LastRequestName'] == _series_name:
			SeriesDetails.update(self.last_request)
			return SeriesDetails
		else:
			self.last_request = {'LastRequestName': _series_name}

		try:
			SeriesDetails['SeriesName'] = self._check_for_alias(_series_name)
		except IndexError:
			pass

		options = {'trakt': self._get_trakt_id,
				   'tvdb': self._get_tvdb_id,
				   'tvrage': self._get_tvrage_id
		}

		try:
			for service in ['tvdb', 'trakt', 'tvrage']:
				try:
					results = options[service](SeriesDetails['SeriesName'], **SeriesDetails)
					SeriesDetails['SeriesName'] = results['title']
					if results['service'] is not 'tvrage':
						SeriesDetails['tvdb_id'] = results['tvdb_id']
						SeriesDetails['imdb_id'] = results['imdb_id']
						SeriesDetails['TVDBSeriesID'] = SeriesDetails['tvdb_id']
					if results['service'] in ['trakt', 'tvrage']:
						SeriesDetails['tvrage_id'] = results['tvrage_id']
					if 'tvrage_id' in SeriesDetails:
						raise GetOutOfLoop
				except SeriesNotFound:
					pass
			if any([key in SeriesDetails for key in ['tvrage_id', 'tvdb_id']]):
				raise GetOutOfLoop
			self.last_request = {'LastRequestName': ''}
			raise SeriesNotFound('ALL: Unable to locate series: {}'.format(SeriesDetails['SeriesName']))
		except GetOutOfLoop:
			pass

		self.last_request['SeriesName'] = SeriesDetails['SeriesName']
		if 'tvdb_id' in SeriesDetails:
			self.last_request['tvdb_id'] = SeriesDetails['tvdb_id']
			self.last_request['TVDBSeriesID'] = SeriesDetails['tvdb_id']
		if 'imdb_id' in SeriesDetails:
			self.last_request['imdb_id'] = SeriesDetails['imdb_id']
		if 'tvrage_id' in SeriesDetails:
			self.last_request['tvrage_id'] = SeriesDetails['tvrage_id']

		return SeriesDetails

	def _get_tvdb_id(self, series_name, **kwargs):

		results = {}
		try:
			_matches = self.db.search(series_name, "en")
			for _item in _matches:
				_item.update()
				if 'tvdb_id' in kwargs:
					if int(kwargs['tvdb_id']) <> _item.seriesid:
						continue
				results['title'] = self._decode_name(_item.SeriesName)
				if _matching(series_name, results['title']):
					results['tvdb_id'] = _item.seriesid
					results['imdb_id'] = self._decode_name(_item.IMDB_ID)
					log.debug('_get_tvdb_id: Series Found - TVDB ID: {:>8} Name: {}'.format(results['tvdb_id'],
																						   results['title']))
					raise GetOutOfLoop
				if not "AliasNames" in _item:
					raise SeriesNotFound('TVDB: Unable to locate series: {}'.format(series_name))

				if not type(_item.AliasNames) == list:
					_item.AliasNames = [_item.AliasNames]
				for _new_name in _item.AliasNames:
					results['title'] = self._decode_name(_new_name)
					if _matching(series_name, results['title']):
						results['tvdb_id'] = _item.seriesid
						results['imdb_id'] = self._decode_name(_item.IMDB_ID)
						log.debug('_get_tvdb_id: Series Found - TVDB ID: {:>8} Name: {}'.format(results['tvdb_id'],
																							   results['title']))
						raise GetOutOfLoop
			raise SeriesNotFound('TVDB: Unable to locate series: {}'.format(series_name))
		except GetOutOfLoop:
			pass
		except:
			an_error = traceback.format_exc(1)
			log.verbose(traceback.format_exception_only(type(an_error), an_error)[-1])
			raise DataRetrievalError(an_error)
		results['service'] = 'tvdb'
		return results

	def _get_trakt_id(self, series_name, **kwargs):

		try:
			show = TVShow(series_name)
			if 'tvdb_id' in kwargs:
				if int(kwargs['tvdb_id']) <> show.tvdb_id:
					raise SeriesNotFound('trakt: Unable to locate series: {}'.format(series_name))
		except:
			an_error = traceback.format_exc(1)
			log.verbose(traceback.format_exception_only(type(an_error), an_error)[-1])
			raise SeriesNotFound(an_error)

		results = {}

		results['title'] = self._decode_name(show.title)
		if not _matching(series_name, results['title']):
			raise SeriesNotFound('trakt: Unable to locate series: {}'.format(series_name))
		results['tvdb_id'] = show.tvdb_id
		results['tvrage_id'] = show.tvrage_id
		results['imdb_id'] = self._decode_name(show.imdb_id)

		results['service'] = 'trakt'
		return results

	def _get_tvrage_id(self, series_name, **kwargs):

		results = {}
		try:
			if 'tvrage_id' in kwargs:
				return results
			show_list = self.tvrage.search(series_name)
			for show in show_list:
				if _matching(series_name, show.name):
					raise GetOutOfLoop
			raise SeriesNotFound
		except GetOutOfLoop:
			pass
		except exc:
			an_error = traceback.format_exc()
			log.verbose(traceback.format_exception_only(type(an_error), an_error)[-1])
			raise SeriesNotFound(an_error)

		results['title'] = show.name
		results['tvrage_id'] = show.showid

		results['service'] = 'tvrage'
		return results

	def _get_pytvrage_id(self, series_name, **kwargs):

		results = {}
		try:
#			if 'tvrage_id' in kwargs:
#				return results
			show_list = feeds.search(series_name)
			for show in show_list:
				if _matching(series_name, show.name):
					raise GetOutOfLoop
			raise SeriesNotFound
		except GetOutOfLoop:
			pass
		except:
			an_error = traceback.format_exc()
			log.verbose(traceback.format_exception_only(type(an_error), an_error)[-1])
			raise SeriesNotFound(an_error)

		results['title'] = show.name
		results['tvrage_id'] = show.showid

		results['service'] = 'tvrage'
		return results

	def _decode_name(self, series_name):

		series_name = unicodedata.normalize('NFKD', series_name).encode('ascii', 'ignore')
		series_name = series_name.replace("&amp;", "&").replace("/", "_")

		return series_name


	def _check_for_alias(self, series_name):
		# Check for Alias
		try:
			alias_name = difflib.get_close_matches(series_name, self.settings.SeriesAliasList, 1, cutoff=0.9)
			series_name = self.settings.SeriesAliasList[alias_name[0]].rstrip()
		except IndexError, exc:
			pass

		return series_name

	def _adj_episode(self, SeriesDetails):
		for _entry in self.settings.EpisodeAdjList:
			if _entry['SeriesName'] == SeriesDetails['SeriesName'] and 'SeasonNum' in SeriesDetails:
				if _entry['SeasonNum'] == SeriesDetails['SeasonNum']:
					if _entry['Begin'] <= SeriesDetails['EpisodeNums'][0] and _entry['End'] >= SeriesDetails['EpisodeNums'][0]:
						SeriesDetails['SeasonNum'] = SeriesDetails['SeasonNum'] + _entry['AdjSeason']
						SeriesDetails['EpisodeNums'][0] = SeriesDetails['EpisodeNums'][0] + _entry['AdjEpisode']
						return SeriesDetails
		return SeriesDetails

	def getEpisodeInfo(self, SeriesDetails):
		log.trace("getEpisodeInfo: Retrieving Episodes - %s ID: %s" % (SeriesDetails['SeriesName'], SeriesDetails['TVDBSeriesID']))

		_err_msg_1 = "getEpisodeInfo: Season/Episode Not Found - {SeriesName}  ID: {TVDBSeriesID}"
		_err_msg_2 = "getEpisodeInfo: Connection Issues Retrieving Series and Episode Info - {SeriesName}, ID: {TVDBSeriesID}"
		_err_msg_3 = "getEpisodeInfo: Unknown Error Retrieving Series and Episode Info - {SeriesName}, ID: {TVDBSeriesID}"
		_err_msg_4 = "getEpisodeInfo: No Episode Data Found - {SeriesName}, ID: {TVDBSeriesID}"
		_trace_msg_1 = 'getEpisodeInfo: Checking for SeasonNum & EpisodeNum Match: {SeriesName} {TVDBSeriesID}'

		SeriesDetails['EpisodeData'] = []

		try:
			_series = self.db.get_series( SeriesDetails['TVDBSeriesID'], "en" )
			if 'SeasonNum' in SeriesDetails:
				_season = _series[SeriesDetails['SeasonNum']]
				log.debug('Season: {}'.format(_season))
				if 'EpisodeNums' in SeriesDetails:
					for epno in SeriesDetails['EpisodeNums']:
						_episode = _season[epno]
						self._load_data(_season, _episode, SeriesDetails)
				else:
					for _episode in _season:
						self._load_data(_season, _episode, SeriesDetails)
			else:
				for _season in _series:
					log.debug('Season: {}'.format(_season.season_number))
					for _episode in _season:
						self._load_data(_season, _episode, SeriesDetails)
		except TVDBIndexError, message:
			log.error(_err_msg_1.format(**SeriesDetails))
			raise EpisodeNotFound(_err_msg_1.format(**SeriesDetails))
		except IOError, message:
			log.error(_err_msg_2.format(**SeriesDetails))
			raise DataRetrievalError(_err_msg_2.format(**SeriesDetails))

		if len(SeriesDetails['EpisodeData']) > 0:
			return SeriesDetails
		else:
			log.debug(_err_msg_4.format(**SeriesDetails))
			raise EpisodeNotFound(_err_msg_4.format(**SeriesDetails))

	def _load_data(self, _season, _episode, SeriesDetails):
		if type(_episode.EpisodeName) == unicode:
			_episode_name = unicodedata.normalize('NFKD', _episode.EpisodeName).encode('ascii', 'ignore')
			_episode_name = _episode_name.replace("&amp;", "&").replace("/", "_")
		else:
			_episode_name = str(_episode.EpisodeName)

		SeriesDetails['EpisodeData'].append({'SeasonNum'    : _season.season_number,
											 'EpisodeNum'   : _episode.EpisodeNumber,
											 'EpisodeTitle' : _episode_name,
											 'DateAired'    :  _episode.FirstAired})
		log.debug('{} {} {} {}'.format(_season.season_number, _episode.EpisodeNumber, _episode_name, _episode.FirstAired))


	def _retrieve_tvrage_info(self, SeriesDetails):
		log.debug('_retrieve_tvrage_info: Input Parm: {!s}'.format(SeriesDetails))

		SeriesDetails['EpisodeData'] = []
		if 'EpisodeNums' in SeriesDetails:
			for epno in SeriesDetails['EpisodeNums']:
				try:
					_epinfo= self.tvrage.get_episodeinfo(SeriesDetails['tvrage_id'],
														   SeriesDetails['SeasonNum'],
														   epno)
					SeriesDetails['EpisodeData'].append({'SeasonNum' : SeriesDetails['SeasonNum'],
														 'EpisodeNum' : epno,
														 'EpisodeTitle' : _epinfo.episode['title'],
														 'DateAired': _epinfo.episode['airdate']})
				except KeyError:
					raise EpisodeNotFound("TVRage: No Data Episode Found - {SeriesName}  Season: {SeasonNum}  Episode(s): {EpisodeNums}".format(**SeriesDetails))
		else:
			try:
				_ep_list= self.tvrage.get_episode_list(SeriesDetails['tvrage_id'])
				for season in _ep_list.seasons:
					for episode in season.episodes:
						SeriesDetails['EpisodeData'].append({'SeasonNum' : season.no,
															 'EpisodeNum' : episode.seasonnum,
															 'EpisodeTitle' : episode.title,
															 'DateAired': episode.airdate})
			except KeyError:
				an_error = traceback.format_exc()
				log.verbose(traceback.format_exception_only(type(an_error), an_error)[-1])
				raise EpisodeNotFound("TVRage: No Data Episode Found - {SeriesName}  Season: {SeasonNum}  Episode(s): {EpisodeNums}".format(**SeriesDetails))
		return SeriesDetails

	def check_series_name(self, pathname):
		log.trace("="*30)
		log.trace("check_movie_names method: pathname:{}".format(pathname))

		self.regex_repack = re.compile('^.*(repack|proper).*$', re.IGNORECASE)

		pathname = os.path.abspath(pathname)

		if os.path.isfile(pathname):
			log.debug("-"*30)
			log.debug("Series Directory: %s" % os.path.split(pathname)[0])
			log.debug("Series Filename:  %s" % os.path.split(pathname)[1])
			self.check_file(pathname)
		elif os.path.isdir(pathname):
			log.debug("-"*30)
			log.debug("Series Directory: %s" % pathname)
			for _root, _dirs, _files in os.walk(os.path.abspath(pathname)):
				_dirs.sort()
				for _dir in _dirs[:]:
					# Process Enbedded Directories
					if _ignored(_dir):
						_dirs.remove(_dir)

				_files.sort()
				for _file in _files:
					# _path_name = os.path.join(_root, _file)
					log.trace("Series Filename: %s" % _file)
					if _ignored(_file):
						continue
					self.check_file(_root, _file)
		return None

	def check_file(self, directory, filename):
		pathname = os.path.join(directory, filename)
		try:
			# Get File Details
			_last_series = self.last_request['LastRequestName']
			_parse_details = parser.getFileDetails(pathname)
			_seriesinfo_answer = parser.getFileDetails(pathname)
			_seriesinfo_answer = library.getShowInfo(_seriesinfo_answer)
		except Exception:
			an_error = traceback.format_exc()
			log.verbose(traceback.format_exception_only(type(an_error), an_error)[-1])
			sys.exc_clear()
			return

		if _parse_details['SeriesName'] != _seriesinfo_answer['SeriesName']:
			if _last_series != _parse_details['SeriesName']:
				log.info('-'*40)
				log.info('Rename Required: {} (Current)'.format(_parse_details['SeriesName']))
				log.info('                 {} (Correct)'.format(_seriesinfo_answer['SeriesName']))

		_seriesinfo_answer['EpisodeNumFmt'] = rename._format_episode_numbers(_seriesinfo_answer)
		_seriesinfo_answer['EpisodeTitle'] = rename._format_episode_name(_seriesinfo_answer['EpisodeData'], join_with=self.settings.ConversionsPatterns['multiep_join_name_with'])
#		_seriesinfo_answer['DateAired'] = rename._get_date_aired(_seriesinfo_answer)
		_seriesinfo_answer['BaseDir'] = self.settings.SeriesDir

		_repack = self.regex_repack.search(pathname)
		if _repack: pathname_2 = self.settings.ConversionsPatterns['proper_fqn'] % _seriesinfo_answer
		else: pathname_2 = self.settings.ConversionsPatterns['std_fqn'] % _seriesinfo_answer
		if pathname != pathname_2:
			if os.path.basename(pathname) != os.path.basename(pathname_2):
				log.info('-'*40)
				log.info('{} (Series)'.format(_seriesinfo_answer['SeriesName']))
				log.info('Rename Required: {} (Correct)'.format(os.path.basename(pathname_2)))
				log.info('                 {} (Current)'.format(filename))

		s = pathname.decode('ascii', 'ignore')
		if s != pathname:
			log.warning('INVALID CHARs: {} vs {}'.format(pathname - s, pathname))


if __name__ == "__main__":

	logger.initialize()

	log.trace("MAIN: -------------------------------------------------")
	from library.series.fileparser import FileParser
	from library.series.rename import RenameSeries
	import traceback

	library = SeriesInfo()
	parser = FileParser()
	rename = RenameSeries()
	__main__group = library.options.parser.add_argument_group("Get SeriesInfo Information Options", description=None)
	__main__group.add_argument("--Error-Log", dest="errorlog", action="store_true", default=False,
								help="Create Seperate Log for Errors")

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

	logger.start(log_file, log_level, timed=False, errorlog=library.args.errorlog)

	series_details = {}
	if library.args.season:
		series_details['SeasonNum'] = library.args.season
	if library.args.epno:
		series_details['EpisodeNums'] = library.args.epno
	if library.args.series_name:
		series_details = {'SeriesName' : library.args.series_name}
		answer = library.getShowInfo(series_details)
		print '-'*40
		print ('Series: {SeriesName}'.format(**answer))
		for episode in sorted(answer['EpisodeData']):
			print ('Season: {SeasonNum}  Episode: {EpisodeNum} Title: {EpisodeTitle}'.format(**episode))
		sys.exit(0)
	elif len(library.args.library) > 0:
		for pathname in library.args.library:
			library.check_series_name(pathname)
