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
import time
import unicodedata

import trakt
from trakt.users import User, UserList
from trakt.tv import TVShow, TVSeason, TVEpisode, trending_shows, TraktRating, TraktStats, rate_shows, rate_episodes, genres, get_recommended_shows, dismiss_recommendation

from pytvdbapi import api
from tvrage.api import Show, ShowNotFound

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

		self.db = api.TVDB("959D8E76B796A1FB")
		trakt.api_key = self.settings.TraktAPIKey
		trakt.authenticate(self.settings.TraktUserID, self.settings.TraktPassWord)
		self._check_suffix = re.compile('^(?P<SeriesName>.+?)[ \._\-](?P<year>[0-9][0-9][0-9][0-9]|US|us|Us)$', re.VERBOSE)
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

		try:
			SeriesDetails = self.getEpisodeInfo(SeriesDetails)
		except EpisodeNotFound, msg:
			log.error(msg)
			raise EpisodeNotFound(msg)

		log.debug('getSeriesInfo: Series Data Returned: {!s}'.format(SeriesDetails))

		return SeriesDetails

	def _identify_show(self, SeriesDetails):

		_series_name = SeriesDetails['SeriesName'].rstrip()
		if self.last_request['LastRequestName'] == _series_name:
			SeriesDetails.update(self.last_request)
			return SeriesDetails
		else:
			self.last_request = {'LastRequestName': _series_name}

		_tvdb_id = None
		try:
			_series_name = self._check_for_alias(_series_name)
		except IndexError:
			_series_name = SeriesDetails['SeriesName'].rstrip()

		# try:
		# 	_tvdb_id, _series_name = self._check_existing_shows(_series_name)
		# 	SeriesDetails['SeriesName'] = _series_name
		# 	SeriesDetails['tvdb_id'] = _tvdb_id
		# except IndexError:
		# 	_series_name = SeriesDetails['SeriesName'].rstrip()

		if not _tvdb_id:
			options = {'trakt': self._get_trakt_id,
					   'tvdb': self._get_tvdb_id,
					   'tvrage': self._get_tvrage_id
			}

			try:
				for service in ['trakt', 'tvdb', 'tvrage']:
					try:
						results = options[service](_series_name)
						if results:
							raise GetOutOfLoop
					except ShowNotFound:
						pass
				self.last_request = {'LastRequestName': ''}
				raise ShowNotFound('ALL: Unable to locate series: {}'.format(_series_name))
			except GetOutOfLoop:
				pass

			SeriesDetails['SeriesName'] = results['title']
			if results['service'] is not 'tvrage':
				SeriesDetails['tvdb_id'] = results['tvdb_id']
				SeriesDetails['imdb_id'] = results['imdb_id']
			if results['service'] in ['trakt', 'tvrage']:
				SeriesDetails['tvrage_id'] = results['tvrage_id']

			self.last_request['SeriesName'] = results['title']
			if results['service'] is not 'tvrage':
				self.last_request['tvdb_id'] = results['tvdb_id']
				self.last_request['imdb_id'] = results['imdb_id']
			if results['service'] in ['trakt', 'tvrage']:
				self.last_request['tvrage_id'] = results['tvrage_id']

		SeriesDetails['TVDBSeriesID'] = SeriesDetails['tvdb_id']
		self.last_request['TVDBSeriesID'] = SeriesDetails['tvdb_id']

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
					log.debug('_find_series_id: Series Found - TVDB ID: {:>8} Name: {}'.format(results['tvdb_id'],
																							   results['title']))
					raise GetOutOfLoop
				if not "AliasNames" in _item:
					raise ShowNotFound('TVDB: Unable to locate series: {}'.format(series_name))

				if not type(_item.AliasNames) == list:
					_item.AliasNames = [_item.AliasNames]
				for _new_name in _item.AliasNames:
					results['title'] = self._decode_name(_new_name)
					if _matching(series_name, results['title']):
						results['tvdb_id'] = _item.seriesid
						results['imdb_id'] = self._decode_name(_item.IMDB_ID)
						log.debug('_find_series_id: Series Found - TVDB ID: {:>8} Name: {}'.format(results['tvdb_id'],
																							   results['title']))
						raise GetOutOfLoop
			raise ShowNotFound('TVDB: Unable to locate series: {}'.format(series_name))
		except GetOutOfLoop:
			pass
		except:
			error_msg = "_find_series_id: Unable to retrieve Series Name Info - %s" % (series_name)
			log.trace(error_msg)
			raise DataRetrievalError(error_msg)
		results['service'] = 'tvdb'
		return results

	def _get_trakt_id(self, series_name, **kwargs):

		try:
			show = TVShow(series_name)
		except:
			raise ShowNotFound('trakt: Unable to locate series: {}'.format(series_name))

		results = {}

		results['title'] = self._decode_name(show.title)
		if not _matching(series_name, results['title']):
			raise ShowNotFound('trakt: Unable to locate series: {}'.format(series_name))
		results['tvdb_id'] = show.tvdb_id
		results['tvrage_id'] = show.tvrage_id
		results['imdb_id'] = self._decode_name(show.imdb_id)

		results['service'] = 'trakt'
		return results

	def _get_tvrage_id(self, series_name, **kwargs):

		results = {}
		try:
			show = Show(series_name)
		except:
			error_msg = "Series Not Found: _retrieve_tvrage_info: Unable to Locate Series in TVDB or TVRAGE: %s" % (_series_name)
			raise SeriesNotFound(error_msg)

		results['title'] = show.name
		if not _matching(series_name, results['title']):
			error_msg = "_retrieve_tvrage_info: Unable to Locate Series in TVDB or TVRAGE: %s" % (series_name)
			raise SeriesNotFound(error_msg)

		results['_tvrage_id'] = show.showid

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

	def _check_existing_shows(self, series_name):
		try:
			series_name = difflib.get_close_matches(series_name, self.settings.TvdbIdList, 1, cutoff=0.9)[0].rstrip()
			tvdb_id = self.settings.TvdbIdList[series_name]
			log.debug('_check_existing_shows: Found TVDB ID: {:>8} Name: {}'.format(tvdb_id, series_name))
		except IndexError, exc:
			log.debug('_find_series_id: Series Not Found: %s - Attempting Match Logic' % _series_name)

		return tvdb_id, series_name

	def _update_settings(self, series_name, tvdb_id):

		self.settings.TvdbIdList[series_name] = tvdb_id

		with open(self.settings.TvdbIdFile, "a") as _sf_obj:
			_sf_obj.write('%s\t%s\n' % (series_name, tvdb_id))

		_sf_obj.close()

		self.settings.ReloadTVDBList()
		return

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

		_err_msg_1 = "getEpisodeInfo: Season/Episode Not Found - {}  ID: {}"
		_err_msg_2 = "getEpisodeInfo: Connection Issues Retrieving Series and Episode Info - {}, ID: {}"
		_err_msg_3 = "getEpisodeInfo: Unknown Error Retrieving Series and Episode Info - {}, ID: {}"
		_err_msg_4 = "getEpisodeInfo: No Episode Data Found - {}, ID: {}"
		_trace_msg_1 = 'getEpisodeInfo: Checking for SeasonNum & EpisodeNum Match: {} {}'

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
			log.error(_err_msg_1.format(SeriesDetails['SeriesName'], SeriesDetails['TVDBSeriesID']))
			log.error(message)
			raise EpisodeNotFound(_err_msg_1.format(SeriesDetails['SeriesName'], SeriesDetails['TVDBSeriesID']))
		except IOError, message:
			log.error(_err_msg_2.format(SeriesDetails['SeriesName'], SeriesDetails['TVDBSeriesID']))
			log.error(message)
			raise DataRetrievalError(_err_msg_2.format(SeriesDetails['SeriesName'], SeriesDetails['TVDBSeriesID']))
		# except:
		# 	log.error(_err_msg_3.format(SeriesDetails['SeriesName'], SeriesDetails['TVDBSeriesID']))
		# 	raise DataRetrievalError(_err_msg_3.format(SeriesDetails['SeriesName'], SeriesDetails['TVDBSeriesID']))
			raise

		if len(SeriesDetails['EpisodeData']) > 0:
			return SeriesDetails
		else:
			log.debug(_err_msg_4.format(SeriesDetails['SeriesName'], SeriesDetails['TVDBSeriesID']))
			raise EpisodeNotFound(_err_msg_4.format(SeriesDetails['SeriesName'], SeriesDetails['TVDBSeriesID']))

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

		_series_name = SeriesDetails['SeriesName'].rstrip()

		try:
			_series = Show(_series_name)
		except:
			error_msg = "Series Not Found: _retrieve_tvrage_info: Unable to Locate Series in TVDB or TVRAGE: %s" % (_series_name)
			raise SeriesNotFound(error_msg)

		_tvrage_series_name = _series.name
		if self._matching(_series_name, _tvrage_series_name):
			error_msg = "_retrieve_tvrage_info: Unable to Locate Series in TVDB or TVRAGE: %s" % (_series_name)
			raise SeriesNotFound(error_msg)

		log.warn('_retrieve_tvrage_info: Using TVRage for Episode Data: %s' % _tvrage_series_name)
		SeriesDetails['EpisodeData'] = []
		if 'EpisodeNums' in SeriesDetails:
			for epno in SeriesDetails['EpisodeNums']:
				try:
					_episode = _series.season(SeriesDetails['SeasonNum']).episode(epno)
				except KeyError:
					log.debug("_retrieve_tvrage_info: TVDB & TVRAGE No Episode Data Found - %s" % (SeriesDetails['SeriesName']))
					raise EpisodeNotFound("_retrieve_tvrage_info: TVDB & TVRAGE No Data Episode Found - %s" % (SeriesDetails['SeriesName']))

				try:
					_date_aired = _episode.airdate
					SeriesDetails['EpisodeData'].append({'SeasonNum' : SeriesDetails['SeasonNum'],
														 'EpisodeNum' : epno,
														 'EpisodeTitle' : _episode.title,
														 'DateAired': _date_aired})
				except KeyError, msg:
					raise EpisodeNotFound(msg)
		else:
			_episodes = _series.episodes
			for _season_num in _series.episodes:
				for _episode_num in _series.episodes[_season_num]:
					try:
						_episode = _series.season(_season_num).episode(_episode_num)
						_date_aired = _episode.airdate
						SeriesDetails['EpisodeData'].append({'SeasonNum' : _season_num,
															 'EpisodeNum' : _episode_num,
															 'EpisodeTitle' : _episode.title,
															 'DateAired': _date_aired})
					except KeyError, msg:
						raise EpisodeNotFound(msg)
		return SeriesDetails


if __name__ == "__main__":

	logger.initialize()
	library = SeriesInfo()
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

	_series_details = {'SeriesName' : library.args.series_name}
	if library.args.season:
		_series_details['SeasonNum'] = library.args.season
	if library.args.epno:
		_series_details['EpisodeNums'] = library.args.epno

	_answer = library.getShowInfo(_series_details)

	print
	print _answer
