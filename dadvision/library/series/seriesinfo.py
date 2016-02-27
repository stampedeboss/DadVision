#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Purpose:
		Configuration and Run-time settings for the XBMC Support Programs
"""
import datetime
import difflib
import logging
import os.path
import re
import sys
import traceback
from collections import defaultdict

from common import matching
from common.exceptions import InvalidArgumentType, InvalidArgumentValue, DictKeyError, GetOutOfLoop
from common.exceptions import SeriesNotFound, EpisodeNotFound
from library import Library
from pytvdbapi import api, error
from pytvdbapi.error import TVDBAttributeError, TVDBIndexError, TVDBValueError
from trakt.tv import TVShow
from trakt.users import User
from tvrage import feeds

import logger
import trakt
from series import Series

__pgmname__ = 'seriesinfo'

__author__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"

__maintainer__ = __author__

__copyright__ = "Copyright 2011, AJ Reynolds"
__license__ = "GPL"

FlexGetConfig = os.path.join(os.path.expanduser('~'), '.flexget', 'config.series')
log = logging.getLogger(__pgmname__)


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


class SeriesInfo(Library):

	def __init__(self, rtnDict=True):
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
				action="store_false", default=False,
				help="Information to come from trakt.tv")

		self.db = api.TVDB("959D8E76B796A1FB")

		self.trakt_user = None

		self._check_suffix = re.compile('^(?P<SeriesName>.*)[ \._\-][\(](?P<Suffix>(?:19|20)\d{2}|[a-zA-Z]*)[\)].*$', re.I)

		self.last_series = Series()
		self.series = Series()
		self.rtnDict = rtnDict

	def getShowInfo(self, request, processOrder=['tvdb', 'tvrage'], epdetail=True):
		log.trace('getShowInfo: Input Parm: {}'.format(request))

		if not epdetail:
			self.args.get_episodes = False

		try:
			if self.args.processes is not None:
				processOrder = self.args.processes
			elif type(processOrder) == list:
				_s = set(['tvdb', 'trakt', 'tvrage'])
				_diff = [_x for _x in processOrder if _x not in _s]
				if _diff:
					raise InvalidArgumentValue('processOrder must be: {}'.format('tvdb, trakt, tvrage'))
		except:
			raise InvalidArgumentType('processOrder must be list, received: {}'.format(type(processOrder)))

		if type(request) == dict:
			if 'SeriesName' in request and request['SeriesName'] is not None:
				if self.args.series_name is not None:
					request['SeriesName'] = self.args.series_name
				if self.args.season is not None:
					request['SeasonNum'] = self.args.season
				if self.args.epno is not None:
					request['EpisodeNums'] = self.args.epno
				self.series = Series(**request)
			elif self.args.series_name is not None:
				self.series.title = self.args.series_name
				if self.args.season is not None:
					self.series.season = self.args.season
				if self.args.epno is not None:
					self.series.episodeNums = self.args.epno
			else:
				error_msg = 'getDetails: Request Missing "SeriesName" Key: {!s}'.format(request)
				log.trace(error_msg)
				raise DictKeyError(error_msg)
		else:
			error_msg = 'getDetails: Invalid object type passed, must be DICT, received: {}'.format(type(request))
			log.trace(error_msg)
			raise InvalidArgumentType(error_msg)

		self._checkForAlias()
#		if  hasattr(self.series, 'episodenums'):
#			self._adjEpisodeNums()

		#Valid Request: Locate Show IDs
		try:
			self._getInfoFromProviders(processOrder)
		except SeriesNotFound:
			if self.series.titleSuffix:
				self.series.title = self.series.titleBase
				self._getInfoFromProviders(processOrder)
		except KeyboardInterrupt:
			sys.exit(8)

		if self.args.get_episodes:
			ep_get = {'tvdb_id': self._tvdbEpisodeInfo, 'tvrage_id': self._tvrageEpisideInfo}

			try:
				if self.series.tvdb_id :
					service = 'tvdb_id'
				elif self.series.tvrage_id:
					service = 'tvrage_id'
				else: raise SeriesNotFound
				ep_get[service]()
			except KeyboardInterrupt:
				sys.exit(8)

		if self.rtnDict: return self.series.getDict()
		else: return self.series

	def _getInfoFromProviders(self, processOrder):

		if self.last_series.title == self.series.title:
			self.series.copyShow(self.last_series)
			return
		else:
			self.last_series = Series(title=self.series.title)

		options = {'tvdb': self._tvdbGetInfo,
				   'trakt': self._traktGetInfo,
				   'tvrage': self._tvrageGetInfo}

		try:
			for service in processOrder:
				try:
					options[service]()
					if self.series.keysFound:
#						if not self.series.tvdb_id and 'tvdb' in processOrder:
#							self.series.title = re.sub(' and ', ' & ', self.series.title)
#							options['tvdb']()
						raise GetOutOfLoop
				except SeriesNotFound:
					sys.exc_clear()
				except GetOutOfLoop:
					raise GetOutOfLoop
				except:
					_an_error = traceback.format_exc()
					log.debug(traceback.format_exception_only(type(_an_error), _an_error)[-1])
					raise SeriesNotFound
			if self.series.keysFound:
				raise GetOutOfLoop
			self.last_request = {'LastRequestName': ''}
			raise SeriesNotFound('ALL: Unable to locate series: {}'.format(self.series.title))
		except GetOutOfLoop:
			sys.exc_clear()

		self.last_series.copyShow(self.series)

		return

	def _traktGetInfo(self):

		try:
			if not self.trakt_user:
				trakt.api_key = self.settings.TraktAPIKey
				trakt.authenticate(self.settings.TraktUserID, self.settings.TraktPassWord)
				self.trakt_user = User(self.settings.TraktUserID)
		except:
			raise SeriesNotFound('trakt: Unable to connect to trakt service: {}'.format(self.settings.TraktUserID))

		show = TVShow(self.series.title)
		if not show.tvdb_id:
			raise SeriesNotFound('trakt: Unable to locate series: {}'.format(self.series.title))

		_title = self.decode(show.title)
		if not matching(self.series.title.lower(), _title.lower(), factor=85):
			raise SeriesNotFound('trakt: Unable to locate series: {}'.format(self.series.title))

		if not self.series.source:
			self.series.source = 'trakt'
			self.series.title = show.title

		if show.tvdb_id and self.series.tvdb_id is None:
			self.series.tvdb_id = show.tvdb_id

		if hasattr(show, 'tvrage_id') and show.tvrage_id:
			if self.series.tvrage_id is None:
				self.series.tvrage_id = show.tvrage_id

		if hasattr(show, 'imdb_id') and show.imdb_id:
			if self.series.imdb_id is None:
				self.series.imdb_id = self.decode(show.imdb_id)

#		if show.status and 'status' not in results:
#			results['status'] = series.status

		return

	def _tvdbGetInfo(self):

		try:
			_shows = self.db.search(self.series.titleBase, "en")
		except (TVDBAttributeError, TVDBIndexError, TVDBValueError, error.BadData):
			_an_error = traceback.format_exc()
			log.debug(traceback.format_exception_only(type(_an_error), _an_error)[-1])
			raise SeriesNotFound

		if len(_shows) == 0: raise SeriesNotFound
		if len(_shows) == 1:
			if matching(self.series.title.lower(), self.decode(_shows[0].SeriesName).lower(), factor=85):
				_shows[0].update()
				_series = Series(tvdb=_shows[0])

				self.series.update(_series)
				self.series.source = 'tvdb'
				self.series.tvdb_info = _series
				return
			else:
				raise SeriesNotFound

		_rankings = {'Continuing': {}, 'Ended': {}, 'Other': {}}
		for _show in _shows:
			_title_suffix = self._check_suffix.match(self.decode(_show.SeriesName))
			if _title_suffix:
				_score = matching(self.series.titleBase.lower(), _title_suffix.group('SeriesName').lower())
			else:
				_score = matching(self.series.titleBase.lower(), self.decode(_show.SeriesName).lower())
			if _score < 90:
				continue

			_show.update()
			_series = Series(tvdb=_show)
			if _score in _rankings[_series.status]:
				_rankings[_series.status][_score][_series.title] = _series
			else:
				_rankings[_series.status][_score] = {_series.title: _series}

		if not _rankings: raise SeriesNotFound

		self._reviewShowData(_rankings, 'tvdb')

		return

	def _tvrageGetInfo(self):

		_shows = feeds.search(self.series.titleBase)
		if not _shows: raise SeriesNotFound
		if len(_shows) == 1:
			_series = Series(tvrage=etree_to_dict(_shows[0])['show'])
			if matching(self.series.title.lower(), _series.title.lower(), factor=85):
				_series = Series(tvrage=_shows[0])
				self.series.update(_series)
				self.series.source = 'tvrage'
				self.series.tvrage_info = _series
				return
			else:
				raise SeriesNotFound

		_rankings = {}
		for _show in _shows:
			_series = Series(tvrage=etree_to_dict(_show)['show'])
			_score = matching(self.series.title.lower(), self.decode(_series.titleBase.lower()))
			if _score < 85:
				continue

			if _score in _rankings[_series.status]:
				_rankings[_series.status][_score][_series.title] = _series
			else:
				_rankings[_series.status][_score] = {_series.title: _series}

		if not _rankings:
			raise SeriesNotFound

		self._reviewShowData(_rankings, 'tvrage')

		return

	def _reviewShowData(self, _rankings, source):

		_check_order = ['Continuing', 'Ended', 'Other']
		_show_status = {'Continuing': self._activeShows,
				        'Ended': self._notActiveShows,
				        'Other': self._notActiveShows}

		for _status in _check_order:
			if len(_rankings[_status]) > 0:
				found = _show_status[_status](_rankings[_status], source)
				if found: return

		raise SeriesNotFound

	def _activeShows(self, _list, source):
		_check_order = ['Country', 'Year', None]
		for key in sorted(_list, reverse=True):
			for _check in _check_order:
				for _series in _list[key].itervalues():
					if _series.titleType != _check:
						continue
					if _check == 'Country':
						if self.series.titleType == 'Country':
							if self.series.country != _series.country:
								continue
						elif _series.country != 'US':
							continue
					if _check == 'Year':
						if self.series.titleType == 'Year':
							if self.series.titleSuffix != _series.titleSuffix:
								continue
					if matching(_series.titleBase, self.series.titleBase, factor=98):
						self.series.update(_series)
						self.series.source = source
						if source == 'tvdb':
							self.series.tvdb_info = _series
						elif source == 'tvrage':
							self.series.tvrage_info = _series
						return True
		return False

	def _notActiveShows(self, _list, source):
		_check_order = ['Match', 'Country', 'Year', None]
		for key in sorted(_list, reverse=True):
			for _check in _check_order:
				for _series in _list[key].itervalues():
					if _check == 'Match':
						if _series.titleType == self.series.titleType:
							if matching(_series.title, self.series.title, factor=98):
								self.series.update(_series)
								self.series.source = source
								if source == 'tvdb':
									self.series.tvdb_info = _series
								elif source == 'tvrage':
									self.series.tvrage_info = _series
								return True
					elif _series.titleType == _check:
						if matching(_series.titleBase, self.series.titleBase, factor=98):
							self.series.update(_series)
							self.series.source = source
							if source == 'tvdb':
								self.series.tvdb_info = _series
							elif source == 'tvrage':
								self.series.tvrage_info = _series
							return True
		return False

	def _checkForAlias(self):
		# Check for Alias
		alias_name = difflib.get_close_matches(self.series.title, self.settings.SeriesAliasList, 1, cutoff=0.9)
		if len(alias_name) > 0:
			self.series.title = self.settings.SeriesAliasList[alias_name[0]].rstrip()
		return

	def _adjEpisodeNums(self):
		for _entry in self.settings.EpisodeAdjList:
			if _entry['SeriesName'] == self.series.title and self.series.season:
				if _entry['SeasonNum'] == self.series.season:
					if _entry['Begin'] <= self.series.episodeNums[0] and _entry['End'] >= self.series.episodeNums[0]:
						self.series.season = self.series.season + _entry['AdjSeason']
						self.series.episodeNums[0] = self.series.episodeNums[0] + _entry['AdjEpisode']
						return
		return

	def _tvdbEpisodeInfo(self):
		log.trace("_tvdbEpisodeInfo: Retrieving Episodes - %s ID: %s" % (self.series.title, self.series.tvdb_id))

		_err_msg_1 = "TVDB: No Episode Data Found - {SeriesName}, ID: {tvdb_id}"
		_err_msg_2 = "TVDB: Connection Issues Retrieving Series and Episode Info - {SeriesName}, ID: {tvdb_id}"

		try:
			self.series.episodeData = []
			_series = self.db.get_series(self.series.tvdb_id, "en" )
			_seasons = self._tvdbBuildTVSeason(_series)
			self.series.seasons = _seasons
			if self.series.season is not None:
				_season = _series[self.series.season]
				if self.series.episodeNums:
					for epno in self.series.episodeNums:
						_episode = _season[epno]
						self.series.addEpisode(_season, _episode)
				else:
					for _episode in _season:
						self.series.addEpisode(_season, _episode)
			else:
				for _season in _series:
					log.debug('Season: {}'.format(_season.season_number))
					for _episode in _season:
						self.series.addEpisode(_season, _episode)
		except TVDBIndexError, message:
			_an_error = traceback.format_exc()
			log.debug(traceback.format_exception_only(type(_an_error), _an_error)[-1])
			log.debug(_err_msg_1.format(**self.series.getDict()))
			raise EpisodeNotFound(_err_msg_1.format(**self.series.getDict()))
		except IOError, message:
			_an_error = traceback.format_exc()
			log.debug(traceback.format_exception_only(type(_an_error), _an_error)[-1])
			log.debug(_err_msg_2.format(**self.series.getDict()))
			raise EpisodeNotFound(_err_msg_2.format(**self.series.getDict()))

		return

	def _tvdbBuildTVSeason(self, _series):
		_seasons = {}
		for _season in _series:
			_season_number = '<Season {0:02}>'.format(_season.season_number)
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
				_my_tv_episode = TVEpisode(series=self.series.title, **_myepisode)
				_myseason['episodes'][_episode_number] = _my_tv_episode
			_my_tv_season = TVSeason(series=self.series.title, **_myseason)
			_seasons[_season_number] = _my_tv_season
		return _seasons

	def _tvrageEpisideInfo(self):
		log.debug('_tvrageEpisideInfo: Input Parm: {!s}'.format(self.series.getDict()))

		self.series.episodeData = []
		_epinfo = etree_to_dict(feeds.episode_list(self.series.tvrage_id, node='Episodelist'))['Episodelist']['Season']
		_seasons = self._tvrageBuildTVSeason(_epinfo)
		self.series.seasons = _seasons
		if self.series.season is not None:
			_season = self.series.seasons['<Season {0:04}>'.format(int(self.series.season))]
			if self.series.episodeNums:
				for epno in self.series.episodeNums:
					_episode = _season.episodes['E{0:02d}'.format(int(epno))]
					self.series.addRageEpisode(_season, _episode)
			else:
				for _episode in _season.episodes.itervalues():
					self.series.addRageEpisode(_season, _episode)
		else:
			for _season in _seasons.itervalues():
				for _episode in _season.episodes.itervalues():
					self.series.addRageEpisode(_season, _episode)

		return

	def _tvrageBuildTVSeason(self, _epinfo):
		_seasons = {}
		for _season in _epinfo:
			_season_number = '<Season {0:04}>'.format(int(_season['@no']))
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
					_my_tv_episode = TVEpisode(series=self.series.title, **_myepisode)
					_myseason['episodes'][_episode_number] = _my_tv_episode
				_my_tv_season = TVSeason(series=self.series.title, **_myseason)
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
				_my_tv_episode = TVEpisode(series=self.series.title, **_myepisode)
				_myseason['episodes'][_episode_number] = _my_tv_episode

			_my_tv_season = TVSeason(series=self.series.title, **_myseason)
			_seasons[_season_number] = _my_tv_season
		return _seasons

def __printAnswer(answer):
	pp = pprint.PrettyPrinter(indent=1, depth=1)
	print '-'*60
	pp.pprint(answer)
	print '-'*60

if __name__ == "__main__":

	logger.initialize()

	log.trace("MAIN: -------------------------------------------------")
	from series import FileParser
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
			print pathname
			if os.path.exists(pathname):
				myrequest = parser.getFileDetails(pathname)
				if library.args.series_name:
					myrequest['SeriesName'] = library.args.series_name
				if library.args.season:
					myrequest['SeasonNum'] = library.args.season
				if library.args.epno:
					myrequest['EpisodeNums'] = library.args.epno
				else:
					myrequest['SeriesName'] = pathname
					library.args.series_only = True
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
