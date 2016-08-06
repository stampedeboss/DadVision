#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
	Initialization Routine for a Series

'''

import datetime
import logging
import traceback

from dateutil import parser
from os.path import basename, dirname, relpath, split

from common.exceptions import SeriesNotFound, SeasonNotFound, EpisodeNotFound, NotMediaFile, GetOutOfLoop
from library import matching, media, decode
from MyTrakt.show import getShow, searchShow, getSeasons, getEpisode

__pgmname__ = 'series'

__author__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"

__maintainer__ = __author__

__copyright__ = "Copyright 2016, AJ Reynolds"
__license__ = "GPL"

log = logging.getLogger(__pgmname__)

class Series(object):

	def __init__(self, **kwargs):

		super(Series, self).__init__()

		self._title = None
		self._status = None
		self.titleTVDB = None
		self.year = None
		self.ids = {'imdb': None, 'tmdb': None,
					'MyTrakt': None, 'tvdb': None,
					'tvrage': None, 'slug': None}
		self.country = None
		self.number_of_seasons = None
		self.number_of_episodes = None
		self._seasons = None
		self.networks = None
		self.alias = None
		self.overview = None
		self.airs = {u'timezone': 'Not Specified', u'day': None, u'time': None}
		self._first_air_date = None
		self.last_air_date = None
		self.genres = None
		self.media_info = None
		self.validated = False
		self.series_id = None

		self.load_attr(kwargs)
		return

	def load_attr(self, kwargs):
		if len(kwargs) > 0:
			alias={}
			for key, val in kwargs.items():
				if key in alias:
					key = alias[key]
				if key in ['show', 'tvrage', 'tvdb']:
					self.load_attr(val)
					continue
				if not hasattr(self, key):
					continue
				setattr(self, key, decode(val))
		return

	@property
	def title(self):
		"""The series title."""
		return self._title
	@title.setter
	def title(self, value):
		if value is None:
			return
		self._title = value

	@property
	def slug(self):
		"""The series slug."""
		return self.ids['slug']
	@slug.setter
	def slug(self, value):
		if value is '' or value is None:
			return
		self, self.ids['slug'] = value
		return

	@property
	def imdb_id(self):
		"""The series imdb_id"""
		return self.ids['imdb']
	@imdb_id.setter
	def imdb_id(self, value):
		if value is '' or value is None:
			return
		self.ids['imdb'] = value
		return

	@property
	def tmdb_id(self):
		"""The series tmdb id."""
		return self.ids['tmdb']
	@tmdb_id.setter
	def tmdb_id(self, value):
		if value is '' or value is None:
			return
		self.ids['tmdb'] = int(value)
		return

	@property
	def trakt_id(self):
		"""The series MyTrakt id."""
		return self.ids['MyTrakt']
	@trakt_id.setter
	def trakt_id(self, value):
		if value is '' or value is None:
			return
		self.ids['MyTrakt'] = int(value)
		return

	@property
	def tvdb_id(self):
		"""The series tvdb id."""
		return self.ids['tvdb']
	@tvdb_id.setter
	def tvdb_id(self, value):
		if value is '' or value is None:
			return
		self.ids['tvdb'] = value
		return

	@property
	def tvrage_id(self):
		"""The series tvrage id."""
		return self.ids['tvrage']
	@tvrage_id.setter
	def tvrage_id(self, value):
		if value is '' or value is None:
			return
		self.ids['tvrage'] = value
		return

	@property
	def status(self):
		"""The series status."""
		return self._status
	@status.setter
	def status(self, value):
		if value is None:
			setattr(self._status, None)
			return
		if value.lower() in ['new series', 'returning series', 'continuing', 'hiatus']:
			setattr(self, '_status', 'Continuing')
		elif value.lower() in ['canceled/ended', 'ended']:
			setattr(self, '_status', 'Ended')
		else:
			setattr(self, '_status', 'Other')
		return

	@property
	def in_production(self):
		"""The series status."""
		return self._status
	@in_production.setter
	def in_production(self, value):
		if value is None:
			setattr(self._status, None)
			return
		if value:
			setattr(self, '_status', 'Continuing')
		else:
			setattr(self, '_status', 'Ended')
		return

	@property
	def first_air_date(self):
		"""The series premier date"""
		return self._first_aired_date
	@first_air_date.setter
	def first_air_date(self, value):
		if value is '' or value is None:
			return
		if type(value) in [unicode, str]:
			value = parser.parse(value)
		if type(value) is datetime.date:
			setattr(self, '_first_air_date', value)
		elif type(value) is datetime.datetime:
			setattr(self, '_first_air_date', value.date())
		return

	@property
	def seasons(self):
		"""The series season data"""
		return self._seasons
	@seasons.setter
	def seasons(self, value):
		if not value:
			return
		self._seasons = {}
		for season, data in value.items():
			self._seasons['<Season {0:02}>'.format(season)] = Season(**data._data)

	def copy(self):
		_series = Series()
		for key, val in self.__dict__.iteritems():
			if val is not None:
				setattr(_series, key, val)
		return _series

	def merge(self, source):
		for key, val in source.__dict__.iteritems():
			if val is not None:
				setattr(self, key, val)
		return self

	def search(self, title=None, year=None, country=None):
		if title: self.title = title
		if country: self.country = country
		if year: self.year = year
		#self.tmdb_info()
		self.trakt()
		return

	def media_details(self, pathname):
		from guessit import guessit
		from common.settings import Settings
		settings = Settings()

		if not media(pathname):
			raise NotMediaFile

		try:
			_dir, _fn = split(pathname)
			if basename(_dir)[:6] == 'Season':
				_fn = relpath(pathname, settings.SeriesDir)

			_series = guessit(pathname, '-t episode')
			self.media_info = MediaInfo(self, filename=pathname, **_series)
		except Exception, e:
			_series = guessit(dirname(pathname), '-t episode')
			self.media_info = MediaInfo(self, filename=pathname, **_series)
		return self

	def tmdb_info(self):
		from tmdb3 import searchSeries, set_cache, set_key, set_locale, get_locale
		set_key('587c13e576f991c0a653f783b290a065')
		set_cache(filename='/tmp/tmdb3.cache')
		set_locale('en', 'us')
		_locale = get_locale()

		try:
			tmdb_results = searchSeries(self.title, first_air_date_year=self.year, locale=_locale)
			for _series in tmdb_results:
				if self.country:
					if not self.country in _series.origin_countries:
						continue
				if self.year:
					if not self.year == _series.first_air_date.year():
						continue
				if self.title == decode(_series.name):
					raise GetOutOfLoop(_series)
			raise SeriesNotFound("Series Not Found in TMDb: {}".format(self.title))
		except GetOutOfLoop, e:
			_series = e.message
			alias = {'name': 'title',
					'id': 'tmdb_id',
					'origin_countries': 'country'}
			for key in dir(_series):
				if key[:1] == '_': continue
				if key in alias: key2 = alias[key]
				else: key2  = key
				if not hasattr(self, key2):
					continue
				setattr(self, key2, decode(getattr(_series, key)))
		except:
			an_error = traceback.format_exc()
			raise

		self.validated = True

	def tvdb_info(self):
		from pytvdbapi import api
		from pytvdbapi.error import ConnectionError, TVDBNotFoundError, TVDBIdError
		db = api.TVDB("959D8E76B796A1FB")

		try:
			_tvdb = db.get_series(self.tvdb_id, "en")
			self.titleTVDB = _tvdb.SeriesName
			if type(self.titleTVDB) is unicode:
				self.titleTVDB = self.titleTVDB.encode('ascii', 'ignore')

			if not self.title == self.titleTVDB:
				if self.alias is None: self.alias = []
				self.alias.append(self.titleTVDB)

			if hasattr(self, 'fileDetails'):
				self.fileDetails.seriesTitle = self.titleTVDB
		except (ConnectionError, TVDBNotFoundError, TVDBIdError):
			an_error = traceback.format_exc()
			self.ids['tvdb'] = None

	def trakt(self, title=None, year=None, country=None):
		from trakt import init, core
		core.OAUTH_TOKEN = u'bearer 46654942dd1e4d0ac76a4a3f133b5f9e47abcc80c6d307c645c395cf98a786a1'
		core.CLIENT_ID = '54d65f67401b045bc720ef109d4d05a107c0f5e28badf2f413f89f9bee514ae7'
		core.CLIENT_SECRET = '85f06b5b6d29265a8be4fa113bbaefb0dd58826cbfd4b85da9a709459a0cb9b1'
		from trakt.tv import TVShow

		it_crowd = TVShow(title)

		return

	def trakt_info(self, title=None, year=None, country=None):
		from urllib2 import HTTPError
		_filterOrder = ['tz', 'status', 'rating', 'scores', 'newest']
		_filter_options = {'scores': self._flt_scores,
						   'tz': self._flt_tz,
						   'match': self._flt_match,
						   'rating': self._flt_rating,
						   'status': self._flt_status,
						   'newest': self._flt_newest}

		if self.trakt_id is not None:
			if None in [self.status]:
				try:
					_kwargs = getShow(show=self.trakt_id, rtn=str)
				except HTTPError:
					return
				self.load_attr(_kwargs)
				return
		try:
			if not title is None:
				self.title = title
			if self.year:
				self._list = searchShow(show=self.title, year=self.year, rtn=list)
				for _entry in self._list:
					if _entry.year == self.year:
						continue
					_entry.title = 'SKIP'
				self._list = filter(_filter_options['match'], self._list)
				if type(self._list) is HTTPError or not len(self._list) > 0:
					self._list = searchShow(show=self.title, rtn=list)
			elif self.country:
				self._list = searchShow(show=self.title, rtn=list)
				if type(self._list) is HTTPError or not len(self._list) > 0:
					raise SeriesNotFound
				for _entry in self._list:
					if _entry.country:
						if _entry.country.upper() == self.country:
							continue
						_entry.title = 'SKIP'
			else:
				self._list = searchShow(show=self.title, rtn=list)
		except:
			_an_error = traceback.format_exc()
			raise SeriesNotFound

		if type(self._list) is HTTPError or not len(self._list) > 0:
			raise SeriesNotFound

		_new_list = filter(_filter_options['match'], self._list)
		if len(_new_list) > 0:
			self._list = _new_list

		if type(self._list) is HTTPError:
			raise SeriesNotFound('SeasonNotFound: {}'.format(self.title))
		elif rtn is list or len(self._list) < 2:
			pass
		else:
			for _filter in _filterOrder:
				try:
					_newlist = filter(_filter_options[_filter], self._list)
					if len(_newlist) == 1:
						self._list = _newlist
						break
					elif len(_newlist) == 0:
						if _filter in ['match', 'tz']:
							continue
						else:
							break
					else:
						self._list = _newlist
				except:
					_an_error = traceback.format_exc()
					#log.debug(traceback.format_exception_only(type(_an_error), _an_error)[-1])
					continue

		if not matching(self.title, self._list[0].title, 70):
			raise SeriesNotFound('SeasonNotFound: {}'.format(self.title))

		if hasattr(self, 'fileDetails'):
			for _entry in self._list:
				setattr(_entry, 'fileDetails', self.fileDetails)
				if _entry.titleTVDB:
					_entry.fileDetails.seriesTitle = _entry.titleTVDB
				else:
					_entry.fileDetails.seriesTitle = _entry.title

		if type(self._list) is HTTPError:
			raise
		elif len(self._list) == 0:
			raise SeriesNotFound('SeriesNotFound: {}'.format(self.title))
		elif rtn is list:
			for _entry in self._list:
				delattr(_entry, 'score')
			return self._list
		elif rtn is object:
			_entry = self._list[0]
			delattr(_entry, 'score')
			return _entry

	# Series Filters
	def _flt_tz(self, x): return x.airs['timezone'] == u'America/New_York'
	def _flt_status(self, x): return x.status in ['Continuing', 'Ended']
	def _flt_scores(self, x): return x.score == max(x.score for x in self._list)
	def _flt_newest(self, x): return x.first_aired == max(x.first_aired for x in self._list)
	def _flt_rating(self, x): return x.rating == max(x.rating for x in self._list)
	def _flt_match(self, x): return matching(x.title, self.title) \
			== max([max(matching(x.title, self.title) for x in self._list), 60])

	def __str__(self):
		"""Return a string representation of a :class:`TVShow`"""
		header = '<Series>'
		header = map(str, header)
		header = ' '.join(header)
		return '{}: {}'.format(header, self.title)
	__repr__ = __str__


class MediaInfo(object):
	def __init__(self, parent, **kwargs):
		super(MediaInfo, self).__init__()
		self.parent = parent

		self.filename = None
		self.season = None
		self.episode = None
		self.episode_title = None
		self.mimetype = None
		self.container = None

		self.load_attr(kwargs)
		return

	def load_attr(self, kwargs):
		if len(kwargs) > 0:
			alias = {}
			for key, val in kwargs.items():
				if key in alias:
					key = alias[key]
				if not hasattr(self, key):
					continue
				setattr(self, key, decode(val))
		return

	@property
	def title(self):
		return self.parent.title
	@title.setter
	def title(self, value):
		if value is None:
			return
		self.parent.title = value

	@property
	def year(self):
		return self.parent.year
	@year.setter
	def year(self, value):
		if value is None:
			return
		self.parent.year = value

	@property
	def country(self):
		return self.parent.country
	@country.setter
	def country(self, value):
		if value is None:
			return
		self.parent.country = value

	def __str__(self):
		"""Return a string representation of a :class:`TVShow`"""
		header = '<MediaInfo>'
		header = map(str, header)
		header = ' '.join(header)
		return '{}: {}'.format(header, self.filename)
	__repr__ = __str__


class Season(object):
	"""Container for Season"""
	def __init__(self, **kwargs):
		super(Season, self).__init__()

		self.season_number = None
		self.season_name = None
		self.ids = {'imdb': None, 'tmdb': None,
					'MyTrakt': None, 'tvdb': None,
					'tvrage': None, 'slug': None}
		self._episodes = None
		self.air_date = None
		self.series_id = None

		if len(kwargs) > 0:
			alias = {'name': 'season_name',
			         'episodes': 'episodes',
			         'id': 'tmdb_id',
					'origin_countries': 'country'}
			for key, val in kwargs.items():
				if key in alias: key2 = alias[key]
				else: key2 = key
				if not hasattr(self, key2):
					continue
				setattr(self, key2, decode(val))

	@property
	def tmdb_id(self):
		"""The series tmdb id."""
		return self.ids['tmdb']
	@tmdb_id.setter
	def tmdb_id(self, value):
		if value is '' or value is None:
			return
		self.ids['tmdb'] = int(value)
		return
		return

	@property
	def trakt_id(self):
		"""The series MyTrakt id."""
		return self.ids['MyTrakt']
	@trakt_id.setter
	def trakt_id(self, value):
		if value is '' or value is None:
			return
		self.ids['MyTrakt'] = int(value)
		return

	@property
	def tvdb_id(self):
		"""The series tvdb id."""
		return self.ids['tvdb']
	@tvdb_id.setter
	def tvdb_id(self, value):
		if value is '' or value is None:
			return
		self.ids['tvdb'] = value

		return

	@property
	def tvrage_id(self):
		"""The series tvrage id."""
		return self.ids['tvrage']
	@tvrage_id.setter
	def tvrage_id(self, value):
		if value is '' or value is None:
			return
		self.ids['tvrage'] = value
		return

	@property
	def episodes(self, number=None):
		"""The series Episode"""
		return self._episodes
	@episodes.setter
	def episodes(self, episodes=None):
		if not episodes:
			return
		self._episodes = {}
		for epno, episode in episodes.items():
			self._episodes['<E{0:02d}>'.format(epno)] = Episode(**episode._data)

	def __str__(self):
		"""Return a string representation of a :class:`Season`"""
		return '<Season>: {0:02d}'.format(self.season_number)
	__repr__ = __str__


class Episode(object):
	"""Container for Episodes"""
	def __init__(self, **kwargs):
		super(Episode, self).__init__()
		self.season_number = None
		self.episode_number = None
		self.episode_title = None
		self.ids = {'imdb': None, 'tmdb': None,
					'MyTrakt': None, 'tvdb': None,
					'tvrage': None, 'slug': None}
		self._first_aired = None
		self.series_id = None

		self.load_attr(kwargs)

	def load_attr(self, kwargs):
		if len(kwargs) > 0:
			alias = {'name': 'episode_title',
			         'id': 'tmdb_id',
					'origin_countries': 'country'}
			for key, val in kwargs.items():
				if key in alias: key2 = alias[key]
				else: key2 = key
				if not hasattr(self, key2):
					continue
				setattr(self, key2, decode(val))
		return

	@property
	def tmdb_id(self):
		"""The series tmdb id."""
		return self.ids['tmdb']
	@tmdb_id.setter
	def tmdb_id(self, value):
		if value is '' or value is None:
			return
		self.ids['tmdb'] = int(value)
		return

	@property
	def trakt_id(self):
		"""The series MyTrakt id."""
		return self.ids['MyTrakt']
	@trakt_id.setter
	def trakt_id(self, value):
		if value is '' or value is None:
			return
		self.ids['MyTrakt'] = int(value)
		return

	@property
	def tvdb_id(self):
		"""The series tvdb id."""
		return self.ids['tvdb']
	@tvdb_id.setter
	def tvdb_id(self, value):
		if value is '' or value is None:
			return
		self.ids['tvdb'] = value
		return

	@property
	def tvrage_id(self):
		"""The series tvrage id."""
		return self.ids['tvrage']
	@tvrage_id.setter
	def tvrage_id(self, value):
		if value is '' or value is None:
			return
		self.ids['tvrage'] = value
		return

	@property
	def first_aired(self):
		"""The episode premier date"""
		return self._first_aired
	@first_aired.setter
	def first_aired(self, value):
		if type(value) in [unicode, str]:
			value = parser.parse(value)
		if type(value) is datetime.date:
			setattr(self, '_first_aired', value)
		elif type(value) is datetime.datetime:
			setattr(self, '_first_aired', value.date())
		return

	def __str__(self):
		return '<Episode>: {0:03}'.format(self.episode_number)
	__repr__ = __str__


if __name__ == '__main__':

	from library import Library
	import pprint

	from sys import argv
	from logging import INFO, DEBUG, ERROR; TRACE = 5; VERBOSE = 15
	Library.logger.initialize(level=DEBUG)
	Library.args = Library.cmdoptions.ParseArgs(argv[1:])
	Library.logger.start(Library.args.logfile, Library.args.loglevel, timed=Library.args.timed)

	log.info("*** LOGGING STARTED ***")

	series = Series()
	series.search(title='Star Trek TNG')

	if len(Library.args.pathname) > 0:
		for pathname in Library.args.pathname:
			try:
				#series.media_details(pathname)
				series.search(title='Star Trek TNG')
				#series.rename()
			except Exception, e:
				an_error = traceback.format_exc()
				raise
	pp = pprint.PrettyPrinter(indent=1, depth=2)
	print '-'*80
	pp.pprint(series.__dict__)
