#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Purpose:
		Configuration and Run-time settings for the XBMC Support Programs
"""
from library import Library
from common import logger
from common.exceptions import InvalidArgumentType, InvalidArgumentValue, DictKeyError, DataRetrievalError
from common.exceptions import SeriesNotFound, EpisodeNotFound
from library.series.seriesobj import TVSeries, TVSeason, TVEpisode
from pytvdbapi.error import TVDBAttributeError, TVDBIndexError, TVDBValueError
from fuzzywuzzy import fuzz
import common
import datetime
import difflib
import logging
import os.path
import re
import sys
import fnmatch
import unicodedata
import traceback

import trakt
from trakt.users import User
from trakt.tv import TVShow

from pytvdbapi import api, error

from tvrage import feeds
from tvrage.exceptions import ShowHasEnded, NoNewEpisodesAnnounced, FinaleMayNotBeAnnouncedYet, ShowNotFound
from xml.etree.ElementTree import tostring, tostringlist

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


from collections import defaultdict
def etree_to_dict(t):
	d = {t.tag: {} if t.attrib else None}
	children = list(t)
	if children:
		dd = defaultdict(list)
		for dc in map(etree_to_dict, children):
			for k, v in dc.iteritems():
				dd[k].append(v)
		d = {t.tag: {k:v[0] if len(v) == 1 else v for k, v in dd.iteritems()}}
	if t.attrib:
		d[t.tag].update(('@' + k, v) for k, v in t.attrib.iteritems())
	if t.text:
		text = t.text.strip()
		if children or t.attrib:
			if text:
			  d[t.tag]['#text'] = text
		else:
			d[t.tag] = text
	return d


def _decode(coded_text):

	if type(coded_text) is unicode:
		decoded_text = unicodedata.normalize('NFKD', coded_text).encode('ascii', 'ignore')
		decoded_text = decoded_text.replace("&amp;", "&").replace("/", "_")
	else:
		decoded_text = coded_text

	return decoded_text


def _matching(value1, value2, factor=85):
	log.trace("=================================================")
	log.trace("_matching: Compare: {} --> {}".format(value1, value2))

	fuzzy = []
	fuzzy.append(fuzz.ratio(value1, value2))
	fuzzy.append(fuzz.partial_ratio(value1, value2))
	fuzzy.append(fuzz.token_set_ratio(value1, value2))
	fuzzy.append(fuzz.token_sort_ratio(value1, value2))

	log.trace("=" * 50)
	log.trace('Fuzzy Compare: {} - {}'.format(value1, value2))
	log.trace("-" * 50)
	log.trace('{}: Simple Ratio'.format(fuzzy[0]))
	log.trace('{}: Partial Ratio'.format(fuzzy[1]))
	log.trace('{}: Token Set Ratio'.format(fuzzy[2]))
	log.trace('{}: Token Sort Ratio'.format(fuzzy[3]))
	log.trace(any([fr > factor for fr in fuzzy]))

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
		seriesinfo_group.add_argument("--sn", "--name", type=str, dest='series_name')
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

		self.db = api.TVDB("959D8E76B796A1FB")

		trakt.api_key = self.settings.TraktAPIKey
		trakt.authenticate(self.settings.TraktUserID, self.settings.TraktPassWord)
		self.trakt_user = User(self.settings.TraktUserID)

#		self.tvrage = TVRage(api_key='XwJ7KGdTfep9EpsZBf8m')

		self._check_suffix = re.compile('^(?P<SeriesName>.*)[ \._\-][\(]?(?P<Suffix>(?:19|20)\d{2}|us).*$', re.I)

		self.confidenceFactor = 90
		self.last_request = {'LastRequestName': ''}

	def getShowInfo(self, request, sources=['tvdb', 'trakt', 'tvrage'], epdetail=True):
		log.trace('getShowInfo: Input Parm: {}'.format(request))

		if not epdetail:
			self.args.get_episodes = False

		std_processes = ['tvdb', 'trakt', 'tvrage']
		if self.args.processes:
			_process_order = self.args.processes
		elif not type(sources) == list:
			raise InvalidArgumentType('sources must be list, received: {}'.format(type(sources)))
		else:
			_s = set(std_processes)
			_diff = [_x for _x in sources if _x not in _s]
			if _diff:
				raise InvalidArgumentValue('sources must be: {}'.format(std_processes))
			_process_order = sources

		if type(request) == dict:
			if 'SeriesName' in request and request['SeriesName'] is not None:
				if self.args.series_name is not None:
					request['SeriesName'] = self.args.series_name
				if self.args.season is not None:
					request['SeasonNum'] = self.args.season
				if self.args.epno is not None:
					request['EpisodeNums'] = self.args.epno
				_suffix = self._check_suffix.match(request['SeriesName'])
				if _suffix:
					_series_name = '{} ({})'.format(_suffix.group('SeriesName'), _suffix.group('Suffix').upper())
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
			SeriesDetails = self._identify_show(SeriesDetails, _process_order)
		except (common.exceptions.SeriesNotFound, EpisodeNotFound):
			if _suffix:
				SeriesDetails['SeriesName'] = _suffix.group('SeriesName')
				SeriesDetails = self._identify_show(SeriesDetails)
		except KeyboardInterrupt:
			sys.exit(8)
		except:
			an_error = traceback.format_exc()
			log.debug(traceback.format_exception_only(type(an_error), an_error)[-1])
			raise

		if self.args.get_episodes:
			ep_get = {'tvdb_id': self._tvdbEpisodeInfo, 'tvrage_id': self._tvrageEpisideInfo}

			try:
				if 'tvdb_id' in SeriesDetails  and SeriesDetails['tvdb_id']:
					service = 'tvdb_id'
				elif 'tvrage_id' in SeriesDetails and SeriesDetails['tvrage_id']:
					service = 'tvrage_id'
				else:
					raise common.exceptions.SeriesNotFound
				SeriesDetails = ep_get[service](SeriesDetails)
			except EpisodeNotFound, SeriesNotFound:
				raise EpisodeNotFound
			except KeyboardInterrupt:
				sys.exit(8)

		return SeriesDetails

	def _identify_show(self, SeriesDetails, _process_order):

		_series_name = SeriesDetails['SeriesName'].rstrip()
		if self.last_request['LastRequestName'] == _series_name:
			SeriesDetails.update(self.last_request)
			return SeriesDetails
		else:
			self.last_request = {'LastRequestName': _series_name}

		options = {'tvdb': self._get_tvdb_id,
				   'trakt': self._get_trakt_id,
				   'tvrage': self._get_tvrage_id}

		try:
			for service in _process_order:
				try:
					SeriesDetails = options[service](SeriesDetails)
					if 'tvdb_id' in SeriesDetails or 'tvrage_id' in SeriesDetails:
						if 'tvdb_id' not in SeriesDetails and 'tvdb' in _process_order:
							SeriesDetails = options['tvdb'](SeriesDetails)
						raise GetOutOfLoop
				except SeriesNotFound:
					sys.exc_clear()
				except GetOutOfLoop:
					raise GetOutOfLoop
#				except:
#					an_error = traceback.format_exc()
#					log.debug(traceback.format_exception_only(type(an_error), an_error)[-1])
#					raise
			if any([key in SeriesDetails for key in ['tvrage_id', 'tvdb_id']]):
				raise GetOutOfLoop
			self.last_request = {'LastRequestName': ''}
			raise SeriesNotFound('ALL: Unable to locate series: {}'.format(SeriesDetails['SeriesName']))
		except GetOutOfLoop:
			sys.exc_clear()

		SeriesDetails['TVSeries'] = TVSeries(seriesdetails=SeriesDetails)

		self.last_request['SeriesName'] = SeriesDetails['SeriesName']
		if 'tvdb_id' in SeriesDetails:
			self.last_request['tvdb_id'] = SeriesDetails['tvdb_id']
			#TODO: Delete	self.last_request['TVDBSeriesID'] = SeriesDetails['tvdb_id']
		if 'imdb_id' in SeriesDetails:
			self.last_request['imdb_id'] = SeriesDetails['imdb_id']
		if 'tvrage_id' in SeriesDetails:
			self.last_request['tvrage_id'] = SeriesDetails['tvrage_id']
		if 'TVSeries' in SeriesDetails:
			self.last_request['TVSeries'] = SeriesDetails['TVSeries']

		return SeriesDetails

	def _get_trakt_id(self, series_name, **kwargs):

		_results = {}
		show = TVShow(series_name)

		if not show.tvdb_id: raise SeriesNotFound
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

	def _get_tvdb_id(self, SeriesDetails):

		_candidates = {}

		try:
			_title_suffix = self._check_suffix.match(SeriesDetails['SeriesName'])
			if _title_suffix:
				_matches = self.db.search(_title_suffix.group('SeriesName'), "en")
			else:
				_matches = self.db.search(SeriesDetails['SeriesName'], "en")
			if not _matches: raise SeriesNotFound
			if len(_matches) == 1:
				if _matching(SeriesDetails['SeriesName'].lower(), _decode(_matches[0].SeriesName).lower(), factor=90):
					_matches[0].update()
					_series = TVSeries(tvdb=_matches[0])
					SeriesDetails = self._load_series_info(_series, SeriesDetails, 'tvdb')
					return SeriesDetails
				else:
					raise SeriesNotFound
			for _show in _matches:
				_title_suffix = self._check_suffix.match(_decode(_show.SeriesName))
				if _title_suffix:
					if not _matching(SeriesDetails['SeriesName'].lower(), _title_suffix.group('SeriesName').lower()):
						continue
				else:
					if not _matching(SeriesDetails['SeriesName'].lower(), _decode(_show.SeriesName).lower()):
						continue

				_show.update()
				_series = TVSeries(tvdb=_show)
				_candidates[_series.title] = _series
		except (TVDBAttributeError, TVDBIndexError, TVDBValueError, error.BadData):
			an_error = traceback.format_exc()
			log.debug(traceback.format_exception_only(type(an_error), an_error)[-1])
			raise SeriesNotFound

		if not _candidates:
			raise SeriesNotFound

		SeriesDetails = self._find_show(_candidates, SeriesDetails, 'tvdb')

		return SeriesDetails

	def _get_tvrage_id(self, SeriesDetails):

		if 'tvrage_id' in SeriesDetails:
			return {}

		_candidates = {}

		try:
			_title_suffix = self._check_suffix.match(SeriesDetails['SeriesName'])
			if _title_suffix:
				_matches = feeds.search(_title_suffix.group('SeriesName'))
			else:
				_matches = feeds.search(SeriesDetails['SeriesName'])
			if not _matches: raise SeriesNotFound
			if len(_matches) == 1:
				_series = TVSeries(tvrage=etree_to_dict(_matches[0])['show'])
				if _matching(SeriesDetails['SeriesName'].lower(), _series.title.lower(), factor=90):
					SeriesDetails = self._load_series_info(_series, SeriesDetails, 'tvrage')
					SeriesDetails['service'] = 'tvrage'
					return SeriesDetails
				else:
					raise SeriesNotFound
			for _show in _matches:
				_series = TVSeries(tvrage=etree_to_dict(_show)['show'])
				if _series.title_suffix:
					if _matching(SeriesDetails['SeriesName'].lower(), _decode(_series.title_base.lower())):
						_candidates[_series.title] = _series
				else:
					if _matching(SeriesDetails['SeriesName'].lower(), _decode(_series.title).lower()):
						_candidates[_series.title] = _series
		except ShowNotFound:
			an_error = traceback.format_exc()
			log.debug(traceback.format_exception_only(type(an_error), an_error)[-1])
			raise SeriesNotFound

		if not _candidates:
			raise SeriesNotFound

		SeriesDetails = self._find_show(_candidates, SeriesDetails, 'tvrage')

		return SeriesDetails

	def _find_show(self, _series_list, SeriesDetails, source):

		_check_order = ['Continuing', 'Canceled/Ended', 'Other']
		_series_name = {'title': unicode(SeriesDetails['SeriesName'])}
		_series_name['base'] = unicode(SeriesDetails['SeriesName'])
		_series_name['suffix'] = None
		_series_name['type'] = None
		_series_suffix = self._check_suffix.match(SeriesDetails['SeriesName'])
		if _series_suffix:
			_series_name['base'] = _series_suffix.group('SeriesName')
			_series_name['suffix'] = _series_suffix.group('Suffix')
			if _series_suffix.group('Suffix').isdigit():
				_series_name['type'] = 'Year'
			else:
				_series_name['type'] = 'Country'

		try:
			#Look for Exact Match in Current Shows
			_candidates = [_series_list[x] for x in _series_list if _series_list[x].status == _check_order[0]]
			_found, SeriesDetails = self._compare_entries(_candidates, SeriesDetails, _series_name, source)
			if _found:
				raise GetOutOfLoop

			#Look for Exact Match in Canceled and Other
			_candidates = [_series_list[x] for x in _series_list if _series_list[x].status in [_check_order[1], _check_order[2]]]
			_found, SeriesDetails = self._compare_entries(_candidates, SeriesDetails, _series_name, source)
			if _found:
				raise GetOutOfLoop

			#Check for imdb_id
			for _status in _check_order:
				_candidates = [_series_list[x] for x in _series_list if _series_list[x].status == _status and _series_list[x].imbd_id is not None]
				if _candidates:
					SeriesDetails = self._load_series_info(_candidates[0], SeriesDetails, source)
					raise GetOutOfLoop

			#Check for country
			for _status in _check_order:
				_candidates = [_series_list[x] for x in _series_list if _series_list[x].status == _status and _series_list[x].country == 'US']
				if _candidates:
					SeriesDetails = self._load_series_info(_candidates[0], SeriesDetails, source)
				raise GetOutOfLoop

			#Take 1st item
			for _status in _check_order:
				_candidates = [_series_list[x] for x in _series_list if _series_list[x].status == _status]
				SeriesDetails = self._load_series_info(_candidates[0], SeriesDetails, source)
				raise GetOutOfLoop

			#TODO: "AliasNames" in _item:
			raise SeriesNotFound('Unable to locate series: {}'.format(_decode(SeriesDetails['SeriesName'])))

		except GetOutOfLoop:
			sys.exc_clear()
			return SeriesDetails

	def _compare_entries(self, _candidates, SeriesDetails, _series_name, source):

		if _series_name['type'] is None:
			_candidates_suffix = [x for x in _candidates if x.title_type is not None and x.title_base == _series_name['base']]
			if _candidates_suffix:
				_candidates = _candidates_suffix
		try:
			for _series in _candidates:
				if fuzz.ratio(_series.title.lower(), _series_name['title'].lower()) >= 90:
					_results = self._load_series_info(_series, SeriesDetails, source)
					raise GetOutOfLoop

			for _series in _candidates:
				if _series_name['type'] is None and _series.title_suffix is None:
					if fuzz.ratio(_series.title.lower(), _series_name['title'].lower()) >= 90:
						_results = self._load_series_info(_series, SeriesDetails, source)
						raise GetOutOfLoop
					else:
						continue

				if _series_name['type'] is None or _series.title_type is None:
					if fuzz.ratio(_series.title_base.lower(), _series_name['base'].lower()) >= 90:
						SeriesDetails = self._load_series_info(_series, SeriesDetails, source)
						raise GetOutOfLoop
					else:
						continue

				if fuzz.ratio(_series.title_base.lower(), _series_name['base'].lower()) >= 90:
					if _series.title_type != _series_name['type']:
						SeriesDetails = self._load_series_info(_series, SeriesDetails, source)
						raise GetOutOfLoop
					elif _series.title_suffix == _series_name['suffix']:
						SeriesDetails = self._load_series_info(_series, SeriesDetails, source)
						raise GetOutOfLoop
			raise SeriesNotFound
		except GetOutOfLoop:
			return True, SeriesDetails
		except SeriesNotFound:
			return False, SeriesDetails

		raise RuntimeError

	def _load_series_info(self, series, results, source):
		if 'source' not in results:
			results['SeriesName'] = series.title
			results['source'] = [source]
			_trakt_top_shows = self.trakt_user.get_list('topshows')
			_trakt_top_shows_names = {_item.title: _item for _item in _trakt_top_shows.items}
			results['top_show'] = False
			if series.title in _trakt_top_shows_names:
				results['top_show'] = True
		if series.tvdb_id and 'tvdb_id' not in results:
			results['tvdb_id'] = series.tvdb_id
			#TODO: Delete	results['TVDBSeriesID'] = series.tvdb_id
		if series.imdb_id and 'imdb_id' not in results:
			results['imdb_id'] = series.imdb_id
		if series.tvrage_id and 'tvrage_id' not in results:
			results['tvrage_id'] = series.tvrage_id
		if series.status and 'status' not in results:
			results['status'] = series.status

		return results

	def _check_for_alias(self, series_name):
		# Check for Alias
		try:
			alias_name = difflib.get_close_matches(series_name, self.settings.SeriesAliasList, 1, cutoff=0.9)
			series_name = self.settings.SeriesAliasList[alias_name[0]].rstrip()
		except IndexError:
			an_error = traceback.format_exc()
			sys.exc_clear()
#			log.debug(traceback.format_exception_only(type(an_error), an_error)[-1])

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

	def _tvdbEpisodeInfo(self, SeriesDetails):
		log.trace("_tvdbEpisodeInfo: Retrieving Episodes - %s ID: %s" % (SeriesDetails['SeriesName'], SeriesDetails['tvdb_id']))

		_err_msg_1 = "TVDB: No Episode Data Found - {SeriesName}, ID: {tvdb_id}"
		_err_msg_2 = "TVDB: Connection Issues Retrieving Series and Episode Info - {SeriesName}, ID: {tvdb_id}"

		try:
			SeriesDetails['EpisodeData'] = []
			_series = self.db.get_series( SeriesDetails['tvdb_id'], "en" )
			_seasons = self._build_tvseason_tvdb(_series, SeriesDetails)
			SeriesDetails['TVSeries'].seasons = _seasons
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
			log.debug(traceback.format_exception_only(type(an_error), an_error)[-1])
			log.debug(_err_msg_1.format(**SeriesDetails))
			raise EpisodeNotFound(_err_msg_1.format(**SeriesDetails))
		except IOError, message:
			an_error = traceback.format_exc()
			log.debug(traceback.format_exception_only(type(an_error), an_error)[-1])
			log.debug(_err_msg_2.format(**SeriesDetails))
			raise DataRetrievalError(_err_msg_2.format(**SeriesDetails))

		return SeriesDetails

	def _build_tvseason_tvdb(self, _series, SeriesDetails):
		_seasons = {}
		for _season in _series:
			_season_number = u'<Season {0:02}>'.format(_season.season_number)
			_myseason = {"season": _season.season_number}
			_myseason['episodes'] = {}
			for _episode in _season:
				_myepisode = {}
				_episode_number = 'E{0:02d}'.format(_episode.EpisodeNumber)
				_myepisode['season'] = _season.season_number
				_myepisode['episode'] = _episode.EpisodeNumber
				_myepisode['title'] = _episode.EpisodeName
				_myepisode['first_aired'] = _episode.FirstAired
				_myepisode['tvdb_episode_id'] = _episode.id
				if _myepisode["season"] == 0:
					_myepisode['special'] = True
					_myepisode['airsbefore_season'] = _episode.airsbefore_season
					_myepisode['airsbefore_episode'] = _episode.airsbefore_episode
					_myepisode['airsafter_season'] = _episode.airsafter_season
				else:
					_myepisode['special'] = False
				_my_tv_episode = TVEpisode(series=SeriesDetails['SeriesName'], **_myepisode)
				_myseason['episodes'][_episode_number] = _my_tv_episode
			_my_tv_season = TVSeason(series=SeriesDetails['SeriesName'], **_myseason)
			_seasons[_season_number] = _my_tv_season
		return _seasons

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

	def _tvrageEpisideInfo(self, SeriesDetails):
		log.debug('_tvrageEpisideInfo: Input Parm: {!s}'.format(SeriesDetails))

		SeriesDetails['EpisodeData'] = []

		_epinfo = etree_to_dict(feeds.episode_list(SeriesDetails['tvrage_id'], node='Episodelist'))['Episodelist']['Season']
		_seasons = self._build_tvseason_tvrage(_epinfo, SeriesDetails)
		SeriesDetails['TVSeries'].seasons = _seasons

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
					log.debug(traceback.format_exception_only(type(an_error), an_error)[-1])
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
				log.debug(traceback.format_exception_only(type(an_error), an_error)[-1])
				raise EpisodeNotFound("TVRage: No Data Episode Found - {SeriesName}  Season: {SeasonNum}  Episode(s): {EpisodeNums}".format(**SeriesDetails))
		return SeriesDetails

	def _build_tvseason_tvrage(self, _epinfo, SeriesDetails):
		_seasons = {}
		for _season in _epinfo:
			_season_number = u'<Season {0:04}>'.format(int(_season['@no']))
			_myseason = {"season": int(_season['@no'])}
			_myseason['episodes'] = {}
			if type(_season['episode']) is list:
				for _episode in _season['episode']:
					_myepisode = {}
					_episode_number = 'E{0:02d}'.format(int(_episode['seasonnum']))
					_myepisode['season'] = int(_season['@no'])
					_myepisode['episode'] = int(_episode['seasonnum'])
					_myepisode['title'] = _episode['title']
					_myepisode['first_aired'] = datetime.datetime.strptime(_episode['airdate'], '%Y-%m-%d').date()
					_myepisode['tvdb_episode_id'] = None
					if _myepisode["season"] == 0:
						_myepisode['special'] = True
					else:
						_myepisode['special'] = False
					_my_tv_episode = TVEpisode(series=SeriesDetails['SeriesName'], **_myepisode)
					_myseason['episodes'][_episode_number] = _my_tv_episode
				_my_tv_season = TVSeason(series=SeriesDetails['SeriesName'], **_myseason)
				_seasons[_season_number] = _my_tv_season
			else:
				_myepisode = {}
				_episode = _season['episode']
				_episode_number = 'E{0:02d}'.format(int(_episode['seasonnum']))
				_myepisode['season'] = int(_season['@no'])
				_myepisode['episode'] = int(_episode['seasonnum'])
				_myepisode['title'] = _episode['title']
				_myepisode['first_aired'] = datetime.datetime.strptime(_episode['airdate'], '%Y-%m-%d').date()
				_myepisode['tvdb_episode_id'] = None
				if _myepisode["season"] == 0:
					_myepisode['special'] = True
				else:
					_myepisode['special'] = False
				_my_tv_episode = TVEpisode(series=SeriesDetails['SeriesName'], **_myepisode)
				_myseason['episodes'][_episode_number] = _my_tv_episode


			_my_tv_season = TVSeason(series=SeriesDetails['SeriesName'], **_myseason)
			_seasons[_season_number] = _my_tv_season
		return _seasons

def __printAnswer(answer):
	print '-'*40
	pp = pprint.PrettyPrinter(indent=1, depth=1)
	pp.pprint(answer)
	print '-'*40
	print '-'*60
	pp.pprint(answer['TVSeries'])
	for season, val in sorted(answer['TVSeries'].seasons.iteritems()):
		pp.pprint(val)
		for episode, val2 in sorted(val.episodes.iteritems()):
				pp.pprint(val2)


if __name__ == "__main__":

	logger.initialize()

	log.trace("MAIN: -------------------------------------------------")
	from library.series.fileparser import FileParser
	import pprint

	library = SeriesInfo()
	parser = FileParser()

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

	myrequest = {}
	if len(library.args.library) > 0:
		for pathname in library.args.library:
			myrequest = parser.getFileDetails(pathname)
			if library.args.series_name:
				myrequest['SeriesName'] = library.args.series_name
			if library.args.season:
				myrequest['SeasonNum'] = library.args.season
			if library.args.epno:
				myrequest['EpisodeNums'] = library.args.epno
				answer = library.getShowInfo(myrequest)
				__printAnswer(answer)
	elif library.args.series_name:
			if library.args.season:
				myrequest['SeasonNum'] = library.args.season
			if library.args.epno:
				myrequest['EpisodeNums'] = library.args.epno
			if library.args.series_name:
				myrequest['SeriesName'] = library.args.series_name
				answer = library.getShowInfo(myrequest)
				__printAnswer(answer)
