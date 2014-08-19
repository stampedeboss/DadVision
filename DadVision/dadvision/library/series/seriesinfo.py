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
import traceback

import trakt
from trakt.users import User, UserList
from trakt.tv import TVShow, TVSeason, TVEpisode, trending_shows, TraktRating, TraktStats, rate_shows, rate_episodes, genres, get_recommended_shows, dismiss_recommendation

from pytvdbapi import api
from TVRage import TVRage, Show, ShowInfo, Season, EpisodeList, Episode, EpisodeInfo
from tvrage import feeds
from xml.etree.ElementTree import tostring

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


def _decode(coded_text):

	decoded_text = unicodedata.normalize('NFKD', coded_text).encode('ascii', 'ignore')
	decoded_text = decoded_text.replace("&amp;", "&").replace("/", "_")

	return decoded_text


def _matching(value1, value2, factor=85):
	log.trace("=================================================")
	log.trace("_matching: Compare: {} --> {}".format(value1, value2))

	fuzzy = []
	fuzzy.append(fuzz.ratio(value1, value2))
	fuzzy.append(fuzz.partial_ratio(value1, value2))
	fuzzy.append(fuzz.token_set_ratio(value1, value2))
	fuzzy.append(fuzz.token_sort_ratio(value1, value2))

	log.verbose("=" * 50)
	log.verbose('Fuzzy Compare: {} - {}'.format(value1, value2))
	log.verbose("-" * 50)
	log.verbose('{}: Simple Ratio'.format(fuzzy[0]))
	log.verbose('{}: Partial Ratio'.format(fuzzy[1]))
	log.verbose('{}: Token Set Ratio'.format(fuzzy[2]))
	log.verbose('{}: Token Sort Ratio'.format(fuzzy[3]))
	log.verbose(any([fr > factor for fr in fuzzy]))

	return any([fr >= factor for fr in fuzzy])


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
		seriesinfo_group.add_argument("--tvdb", dest="processes",
				action="append_const", const='tvdb',
				help="Information to come from TVDB")
		seriesinfo_group.add_argument("--tvrage", dest="processes",
				action="append_const", const='tvrage',
				help="Information to come from TVRage")
		seriesinfo_group.add_argument("--trakt", dest="processes",
				action="append_const", const='trakt',
				help="Information to come from trakt.tv")
		seriesinfo_group.add_argument("--series-only", "--so", dest="get_episodes",
				action="store_false", default=True,
				help="Information to come from trakt.tv")

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
				_suffix = self._check_suffix.match(request['SeriesName'])
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

		try:
			SeriesDetails['SeriesName'] = self._check_for_alias(SeriesDetails['SeriesName'])
			if 'epno' in SeriesDetails:
				SeriesDetails = self._adj_episode(SeriesDetails)
		except IndexError:
			sys.exc_clear()

		#Valid Request: Locate Show IDs
		try:
			SeriesDetails = self._identify_show(SeriesDetails)
		except SeriesNotFound:
			_suffix = self._check_suffix.match(request['SeriesName'])
			if _suffix:
				SeriesDetails['SeriesName'] = _suffix.group('SeriesName')
				SeriesDetails = self._identify_show(SeriesDetails)

		if self.args.get_episodes:
			if 'tvdb_id' in SeriesDetails  and SeriesDetails['tvdb_id']:
				try:
					SeriesDetails = self.getEpisodeInfo(SeriesDetails)
				except SeriesNotFound:
					SeriesDetails = self._retrieve_tvrage_info(SeriesDetails)
			elif 'tvrage_id' in SeriesDetails and SeriesDetails['tvrage_id']:
				self._retrieve_tvrage_info(SeriesDetails)

		return SeriesDetails

	def _identify_show(self, SeriesDetails):

		_series_name = SeriesDetails['SeriesName'].rstrip()
		if self.last_request['LastRequestName'] == _series_name:
			SeriesDetails.update(self.last_request)
			return SeriesDetails
		else:
			self.last_request = {'LastRequestName': _series_name}

		if not self.args.processes:
			_process_order = ['tvdb', 'trakt', 'tvrage']
		else:
			_process_order = self.args.processes

		options = {'tvdb': self._get_tvdb_id,
				   'trakt': self._get_trakt_id,
				   'tvrage': self._get_tvrage_id
		}

		try:
			for service in _process_order:
				try:
					_results = options[service](SeriesDetails['SeriesName'], **SeriesDetails)
					if 'title' in _results:
						SeriesDetails['SeriesName'] = _results['title']
					if 'tvdb_id' not in SeriesDetails and 'tvdb_id' in _results:
						SeriesDetails['tvdb_id'] = _results['tvdb_id']
						SeriesDetails['TVDBSeriesID'] = SeriesDetails['tvdb_id']
					if 'imdb_id' not in SeriesDetails and 'imdb_id' in _results:
						SeriesDetails['imdb_id'] = _results['imdb_id']
					if 'tvrage_id' not in SeriesDetails and 'tvrage_id' in _results:
						SeriesDetails['tvrage_id'] = _results['tvrage_id']
						if 'title' in _results and 'tvdb_id' not in SeriesDetails:
							_process_order.append('tvdb')
						else:
							raise GetOutOfLoop
				except SeriesNotFound:
					sys.exc_clear()
			if any([key in SeriesDetails for key in ['tvrage_id', 'tvdb_id']]):
				raise GetOutOfLoop
			self.last_request = {'LastRequestName': ''}
			raise SeriesNotFound('ALL: Unable to locate series: {}'.format(SeriesDetails['SeriesName']))
		except GetOutOfLoop:
			sys.exc_clear()

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

		_results = {}
		_show_list = {}
		_show_status = {'Continuing': [], 'Hiatus': [], 'Ended': [], 'Other': []}
		_check_order = ['Continuing', 'Hiatus', 'Ended']
		try:
			_matches = self.db.search(series_name, "en")
			if not _matches: raise SeriesNotFound
			if len(_matches) == 1:
				if _matching(series_name.lower(), _decode(_matches[0].SeriesName).lower(), factor=90):
					_results = self._load_tmdb_info(_decode(_matches[0].SeriesName), _matches[0], _results)
					raise GetOutOfLoop
				else:
					raise SeriesNotFound
			for _item in _matches:
				_name_decoded = _decode(_item.SeriesName)
				if not _matching(series_name.lower(), _name_decoded.lower(), factor=90):
					continue
				_item.update()
				_show_list[_name_decoded] = _item
				if _decode(_item.Status) in _check_order:
					_show_status[_decode(_item.Status)].append(_name_decoded)
				else:
					_show_status['Other'].append(_name_decoded)

			if not _show_list:
				raise SeriesNotFound

			#Look for Exact Match in Current Shows
			for _item in _show_status[_check_order[0]]:
				if fuzz.ratio(_item.lower(), series_name.lower()) > 90:
					_results = self._load_tmdb_info(_item, _show_list[_item], _results)
					raise GetOutOfLoop

			#Check for Suffix in Current Shows
			_suffix_req = self._check_suffix.match(series_name)
			for _status in [_check_order[0], _check_order[1]]:
				for _item in _show_status[_status]:
					_suffix_tmdb = self._check_suffix.match(_item)
					if _suffix_tmdb:
						if _suffix_req \
						  and fuzz.ratio(_suffix_tmdb.group('SeriesName').lower(), _suffix_req.group('SeriesName').lower()) >= 90:
							_results = self._load_tmdb_info(_item, _show_list[_item], _results)
							raise GetOutOfLoop
						elif fuzz.ratio(_suffix_tmdb.group('SeriesName').lower(), series_name.lower()):
							_results = self._load_tmdb_info(_item, _show_list[_item], _results)
							raise GetOutOfLoop

			#Look for Exact Match
			for _status in _check_order:
				for _item in _show_status[_status]:
					if fuzz.ratio(_item.lower(), series_name.lower()) >= 90:
						_results = self._load_tmdb_info(_item, _show_list[_item], _results)
						raise GetOutOfLoop

			#Check for imdb_id
			for _status in _check_order:
				for _item in _show_status[_status]:
					if 'IMDB_ID' in _show_list[_item] and _show_list[_item].IMDB_ID:
						_results = self._load_tmdb_info(_item, _show_list[_item], _results)
						raise GetOutOfLoop

			#Take 1st item
			for _status in _check_order:
				for _item in _show_status[_status]:
					_results = self._load_tmdb_info(_item, _show_list[_item], _results)
					raise GetOutOfLoop

			#TODO: "AliasNames" in _item:
			raise SeriesNotFound('TVDB: Unable to locate series: {}'.format(series_name))
		except GetOutOfLoop:
			sys.exc_clear()
		except:
			an_error = traceback.format_exc(1)
			log.verbose(traceback.format_exception_only(type(an_error), an_error)[-1])
			raise SeriesNotFound(an_error)
		_results['service'] = 'tvdb'

		return _results

	def _load_tmdb_info(self, show, entry, record):
		record['title'] = show
		record['tvdb_id'] = entry.seriesid
#		if hasattr(entry, 'IMDB_ID'):
		if 'IMDB_ID' in entry.__dict__:
			record['imdb_id'] = _decode(entry.IMDB_ID)
		return record

	def _get_trakt_id(self, series_name, **kwargs):

		_results = {}
		try:
			show = TVShow(series_name)
		except:
			an_error = traceback.format_exc(1)
			log.verbose(traceback.format_exception_only(type(an_error), an_error)[-1])
			raise SeriesNotFound(an_error)

		if not show.tvdb_id: return {}
		if 'tvdb_id' in kwargs:
			if int(kwargs['tvdb_id']) <> show.tvdb_id:
				raise SeriesNotFound('trakt: Unable to locate series: {}'.format(series_name))
		else:
			_results['title'] = _decode(show.title)

		if not _matching(series_name.lower(), _decode(show.title).lower()):
			raise SeriesNotFound('trakt: Unable to locate series: {}'.format(series_name))

		if hasattr(show, 'tvdb_id') and show.tvdb_id: _results['tvdb_id'] = show.tvdb_id
		if hasattr(show, 'tvrage_id') and show.tvrage_id: _results['tvrage_id'] = show.tvrage_id
		if hasattr(show, 'imdb_id') and show.imdb_id: _results['imdb_id'] = _decode(show.imdb_id)

		_results['service'] = 'trakt'
		return _results

	def _get_tvrage_id(self, series_name, **kwargs):

		if 'tvrage_id' in kwargs:
			return {}

		_results = {}
		_show_list = {}
		_show_status = {'New Series': [], 'Returning Series': [], 'Canceled/Ended': [], 'Other': []}
		_check_order = ['New Series', 'Returning Series', 'Canceled/Ended', 'Other']

		try:
			_matches = self.tvrage.search(series_name)
			if not _matches: raise SeriesNotFound
			if len(_matches) == 1:
				if _matching(series_name.lower(), _matches[0].name.lower(), factor=90):
					_results['title'] = _matches[0].name
					_results['tvrage_id'] = _matches[0].showid
					_results['imdb_id'] = _matches[0].IMDB_ID
					raise GetOutOfLoop
				else:
					raise SeriesNotFound
			for _item in _matches:
				if not _matching(series_name.lower(), _item.name.lower(), factor=90):
					continue
				_show_list[_item.name] = _item
				if _item.status in _check_order:
					_show_status[_item.status].append(_item.name)
				else:
					_show_status['Other'].append(_item.name)

			if not _show_list:
				raise SeriesNotFound

			#Look for Exact Match in Current Shows
			for _item in _show_status[_check_order[0]]:
				if fuzz.ratio(_item.lower(), series_name.lower()) >= 90:
					if 'tvdb_id' not in kwargs:
						_results['title'] = _item
					_results['tvrage_id'] = _show_list[_item].showid
					raise GetOutOfLoop

			#Check for Suffix in Current Shows
			for _status in [_check_order[0], _check_order[1]]:
				for _item in _show_status[_status]:
					_suffix_tvrage = self._check_suffix.match(_item)
					_suffix_req = self._check_suffix.match(series_name)
					if _suffix_tvrage:
						if _suffix_req and \
							_suffix_tvrage.group('SeriesName') == _suffix_req.group('SeriesName'):
							if 'tvdb_id' not in kwargs:
								_results['title'] = _item
							_results['tvrage_id'] = _show_list[_item].showid
							raise GetOutOfLoop
						elif _suffix_tvrage.group('SeriesName') == series_name:
							if 'tvdb_id' not in kwargs:
								_results['title'] = _item
							_results['tvrage_id'] = _show_list[_item].showid
							raise GetOutOfLoop

			#Look for Exact Match
			for _status in _check_order:
				for _item in _show_status[_status]:
					if fuzz.ratio(_item.lower(), series_name.lower()) >= 90:
						if 'tvdb_id' not in kwargs:
							_results['title'] = _item
						_results['tvrage_id'] = _show_list[_item].showid
						raise GetOutOfLoop

			#Check for country
			for _status in _check_order:
				for _item in _show_status[_status]:
					if _show_list[_item].country == 'US':
						if 'tvdb_id' not in kwargs:
							_results['title'] = _item
						_results['tvrage_id'] = _show_list[_item].showid
						raise GetOutOfLoop

			#Take 1st item
			for _status in _check_order:
				for _item in _show_status[_status]:
					if 'tvdb_id' not in kwargs:
						_results['title'] = _item
					_results['tvrage_id'] = _show_list[_item].showid
					raise GetOutOfLoop

			#TODO: "AliasNames" in _item:
			raise SeriesNotFound('TVDB: Unable to locate series: {}'.format(series_name))
		except GetOutOfLoop:
			sys.exc_clear()
		except:
			an_error = traceback.format_exc(1)
			log.verbose(traceback.format_exception_only(type(an_error), an_error)[-1])
			raise SeriesNotFound(an_error)

		return _results

	def _get_pytvrage_id(self, series_name, **kwargs):

		results = {}
		try:
#			if 'tvrage_id' in kwargs:
#				return results
			show_list = feeds.full_search(series_name)
			for show in show_list:
				if _matching(series_name, show.name):
					raise GetOutOfLoop
			raise SeriesNotFound
		except GetOutOfLoop:
			sys.exc_clear()
		except:
			an_error = traceback.format_exc()
			log.verbose(traceback.format_exception_only(type(an_error), an_error)[-1])
			raise SeriesNotFound(an_error)

		results['title'] = show.name
		results['tvrage_id'] = show.showid

		results['service'] = 'tvrage'
		return results


	def _check_for_alias(self, series_name):
		# Check for Alias
		try:
			alias_name = difflib.get_close_matches(series_name, self.settings.SeriesAliasList, 1, cutoff=0.9)
			series_name = self.settings.SeriesAliasList[alias_name[0]].rstrip()
		except IndexError:
			an_error = traceback.format_exc()
			sys.exc_clear()
#			log.verbose(traceback.format_exception_only(type(an_error), an_error)[-1])

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
		log.trace("getEpisodeInfo: Retrieving Episodes - %s ID: %s" % (SeriesDetails['SeriesName'], SeriesDetails['tvdb_id']))

		_err_msg_1 = "getEpisodeInfo: Season/Episode Not Found - {SeriesName}  ID: {tvdb_id}"
		_err_msg_2 = "getEpisodeInfo: Connection Issues Retrieving Series and Episode Info - {SeriesName}, ID: {tvdb_id}"
		_err_msg_3 = "getEpisodeInfo: Unknown Error Retrieving Series and Episode Info - {SeriesName}, ID: {tvdb_id}"
		_err_msg_4 = "getEpisodeInfo: No Episode Data Found - {SeriesName}, ID: {tvdb_id}"
		_trace_msg_1 = 'getEpisodeInfo: Checking for SeasonNum & EpisodeNum Match: {SeriesName} {tvdv_id}'

		SeriesDetails['EpisodeData'] = []

		try:
			_series = self.db.get_series( SeriesDetails['tvdb_id'], "en" )
			if 'SeasonNum' in SeriesDetails:
				_season = _series[SeriesDetails['SeasonNum']]
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
			an_error = traceback.format_exc()
			log.verbose(traceback.format_exception_only(type(an_error), an_error)[-1])
			log.error(_err_msg_1.format(**SeriesDetails))
			raise EpisodeNotFound(_err_msg_1.format(**SeriesDetails))
		except IOError, message:
			an_error = traceback.format_exc()
			log.verbose(traceback.format_exception_only(type(an_error), an_error)[-1])
			log.error(_err_msg_2.format(**SeriesDetails))
			raise DataRetrievalError(_err_msg_2.format(**SeriesDetails))

		if len(SeriesDetails['EpisodeData']) > 0:
			return SeriesDetails
		else:
			an_error = traceback.format_exc()
			log.verbose(traceback.format_exception_only(type(an_error), an_error)[-1])
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
					an_error = traceback.format_exc()
					log.verbose(traceback.format_exception_only(type(an_error), an_error)[-1])
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

		log.trace('processing: {} vs {}'.format(_parse_details['SeriesName'], _seriesinfo_answer['SeriesName']))
		if _parse_details['SeriesName'] != _seriesinfo_answer['SeriesName']:
			if _last_series != _parse_details['SeriesName']:
				log.info('-'*40)
				log.info('Rename Required: {} (Current)'.format(_parse_details['SeriesName']))
				log.info('                 {} (Correct)'.format(_seriesinfo_answer['SeriesName']))

		if not library.args.quick:
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


	def check_series_name_quick(self, pathname):
		log.trace("="*30)
		log.trace("check_series_names_quick method: pathname:{}".format(pathname))

		self.regex_repack = re.compile('^.*(repack|proper).*$', re.IGNORECASE)
		pathname = os.path.abspath(pathname)

		if os.path.isfile(pathname):
			log.error("-"*30)
			log.error("File name passed must be Directory:  %s" % pathname)
			sys.exit()

		log.debug("-"*30)
		log.debug("Series Directory: %s" % pathname)
		for _dir in sorted(os.listdir(os.path.abspath(pathname))):
			if _ignored(_dir):
					continue
			_path_name = os.path.join(os.path.abspath(pathname), _dir, 'Season 1')
			self.check_file(_path_name, 'E01 Test.mkv')

		return None


if __name__ == "__main__":

	logger.initialize()

	log.trace("MAIN: -------------------------------------------------")
	from library.series.fileparser import FileParser
	from library.series.rename import RenameSeries
	import pprint

	library = SeriesInfo()
	parser = FileParser()
	rename = RenameSeries()
	__main__group = library.options.parser.add_argument_group("Get SeriesInfo Information Options", description=None)
	__main__group.add_argument("--Error-Log", dest="errorlog", action="store_true", default=False,
								help="Create Seperate Log for Errors")
	__main__group.add_argument("-q", "--quick", dest="quick", action="store_true", default=False,
								help="Perform Quick Check, only evaluate Show Names")

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

	myrequest = {}
	if library.args.season:
		myrequest['SeasonNum'] = library.args.season
	if library.args.epno:
		myrequest['EpisodeNums'] = library.args.epno
	if library.args.series_name:
		myrequest['SeriesName'] = library.args.series_name
		answer = library.getShowInfo(myrequest)
		print '-'*40
		pp = pprint.PrettyPrinter(indent=1, depth=1)
		pp.pprint(answer)
		print '-'*40
		if 'EpisodeData' in answer:
			for episode in answer['EpisodeData']:
				print ('Season: {SeasonNum}  Episode: {EpisodeNum} Title: {EpisodeTitle}'.format(**episode))
		sys.exit(0)
	elif len(library.args.library) > 0:
		for pathname in library.args.library:
			if library.args.quick:
				library.check_series_name_quick(pathname)
			else:
				library.check_series_name(pathname)
