#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
	Initialization Routine for a Series

'''

import re
import datetime
import traceback
from urllib2 import HTTPError

from dateutil import parser
from pytvdbapi import api
from pytvdbapi.error import ConnectionError, TVDBNotFoundError, TVDBIdError

from common.matching import matching
from common.exceptions import SeriesNotFound, SeasonNotFound, EpisodeNotFound
from library.trakt.show import getShow, searchShow, getSeasons, getEpisode


__pgmname__ = 'series'
__version__ = '@version: $Rev$'

__author__ = "@author: AJ Reynolds"
__copyright__ = "@copyright: Copyright 2011, AJ Reynolds"
__status__ = "@status: Development"
__license__ = "@license: GPL"

__maintainer__ = "@organization: AJ Reynolds"
__credits__ = []

db = api.TVDB("959D8E76B796A1FB")


class Series(object):

	def __init__(self, **kwargs):

		super(Series, self).__init__()

		self._title = None
		self._status = None
		self._first_aired = None
		self._seasons = None
		self.titleBase = self.titleSuffix = self.titleType = self.titleTVDB = None
		self.year = None
		self.ids = {u'imdb': None, u'tmdb': None,
		            u'trakt': None, u'tvdb': None,
		            u'tvrage': None, u'slug': None}
		self.country = None
		self.network = None
		self.alias = None
		self.overview = None
		self.airs = {u'timezone': 'Not Specified', u'day': None, u'time': None}

		self.load_attr(kwargs)

		if self.trakt_id is not None:
			if None in [self.status]:
				try:
					_kwargs = getShow(show=self.trakt_id, rtn=str)
				except HTTPError:
					return
				self.load_attr(_kwargs)
#				self.seasons = {}

#		if self.tvdb_id:
#			self.tvdb_id = self.tvdb_id

		if hasattr(self, 'fileDetails'):
			setattr(self, 'fileDetails', fileDetails(self.title, **self.fileDetails))
#			delattr(self, 'fileDetails

		return

	def load_attr(self, kwargs):
		if len(kwargs) > 0:
			for key, val in kwargs.items():
				key = self._std_key(key)
				if key == '__discard':
					continue

				if key in ['show']:
					self.load_attr(val)
					continue
				elif key in ['seasons']:
					continue
				elif key in ['tvrage', 'tvdb']:
					for key2, val2 in vars(val).iteritems():
						if key2 == 'data':
							for key3, val3 in val2.iteritems():
								key3 = self._std_key(key3)
								if key == '__discard':
									continue
								if type(val3) is unicode:
									setattr(self, key3, val3.encode('ascii', 'ignore'))
								else:
									setattr(self, key3, val3)
								continue
				elif key in ['fileName', 'ext', 'seasonNum', 'episodeNums']:
					if not hasattr(self, 'fileDetails'):
						setattr(self, 'fileDetails', {})
					self.fileDetails[key] = val
				else:
					if type(val) is unicode:
						setattr(self, key, val.encode('ascii', 'ignore'))
					else:
						setattr(self, key, val)

		return

	@property
	def title(self):
		"""The series title."""
		return self._title
	@title.setter
	def title(self, value):
		if value is None:
			return

		__year = re.compile('^[\(]?(?P<year>(?:19|20)\d{2})[\)]?$', re.I)
		__country = re.compile('^[\(][a-zA-Z]*[\)]$', re.I)

		_title_parts = value.rsplit(None, 1)
		if len(_title_parts) > 1:
			_year = __year.match(_title_parts[1])
			if _year:
				_title_parts[1] = _title_parts[1].replace('(', '').replace(')', '')
				self.titleBase = _title_parts[0].replace('\'', '')
				self.titleSuffix = int(_title_parts[1])
				self.titleType = "Year"
				self._title = '{} ({})'.format(self.titleBase, self.titleSuffix)
				return
			else:
				_country = __country.match(_title_parts[1])
				if _country:
					_title_parts[1] = _title_parts[1].replace('(', '').replace(')', '')
					self.titleBase = _title_parts[0]
					self.titleSuffix = _title_parts[1].upper()
					self.titleType = "Country"
					self.country = _title_parts[1].upper()
					self._title = '{} ({})'.format(self.titleBase, self.titleSuffix)
					return

		self.titleBase = value
		self.titleSuffix = None
		self.titleType = None
		self._title = value

	@property
	def slug(self):
		"""The series slug."""
		return self.ids[u'slug']
	@slug.setter
	def slug(self, value):
		if value is None and self.ids[u'slug'] is None:
			return
		if value is '':
			value = None
		self, self.ids[u'slug'] = value
		return

	@property
	def imdb_id(self):
		"""The series imdb_id"""
		return self.ids[u'imdb']
	@imdb_id.setter
	def imdb_id(self, value):
		if value is None and self.ids[u'imdb'] is None:
			return
		if value is '':
			value = None
		self.ids[u'imdb_id'] = value
		return

	@property
	def tmdb_id(self):
		"""The series tmdb id."""
		return self.ids[u'tmdb']
	@tmdb_id.setter
	def tmdb_id(self, value):
		if value is None and self.ids[u'tmdb'] is None:
			return
		if value is '':
			value = None
		self.ids[u'tmdb'] = int(value)
		return

	@property
	def trakt_id(self):
		"""The series trakt id."""
		return self.ids[u'trakt']
	@trakt_id.setter
	def trakt_id(self, value):
		if value is None and self.ids[u'trakt'] is None:
			return
		if value is '':
			value = None
		self.ids[u'trakt'] = int(value)
		return

	@property
	def tvdb_id(self):
		"""The series tvdb id."""
		return self.ids[u'tvdb']
	@tvdb_id.setter
	def tvdb_id(self, value):
		if value is None and self.ids[u'tvdb'] is None:
			return
		if value is '':
			self.ids[u'tvdb'] = None
			if hasattr(self, 'fileDetails'):
				self.fileDetails.seriesTitle = None
			return

		self.ids[u'tvdb'] = value
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
			self.ids[u'tvdb'] = None

		return

	@property
	def tvrage_id(self):
		"""The series tvrage id."""
		return self.ids[u'tvrage']
	@tvrage_id.setter
	def tvrage_id(self, value):
		if value is None and self.ids[u'tvrage'] is None:
			return
		if value is '':
			value = None
		self.ids[u'tvrage'] = value
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
	def first_aired(self):
		"""The series premier date"""
		return self._first_aired
	@first_aired.setter
	def first_aired(self, value):
		if value is None:
			return
		if type(value) in [unicode, str]:
			value = parser.parse(value)
		if type(value) is datetime.date:
			setattr(self, '_first_aired', value)
		elif type(value) is datetime.datetime:
			setattr(self, '_first_aired', value.date())
		return

	@property
	def seasons(self):
		"""The series season data"""
		return self._seasons
	@seasons.setter
	def seasons(self, value):
		try:
			_seasons = getSeasons(self.trakt_id, rtn=str)
		except:
			_seasons = None

		if _seasons:
			self._seasons = {}
			for _entry in _seasons:
				self._seasons['<Season {0:02}>'.format(_entry['number'])] = Season(self.trakt_id, **_entry)

	def season(self, number=1):
		if '<Season {0:02}>'.format(number) in self.seasons:
			return self.seasons['<Season {0:02}>'.format(number)]
		else:
			raise SeasonNotFound('SeasonNotFound: {} - Season {}'.format(self.titleTVDB, number))

	def episode(self, snumber, number):
		_eplist = []
		_season = self.season(snumber)
		if _season:
			for _entry in number:
				if _entry > 0 and not _entry > len(_season.episodes):
					_eplist.append(_season.episodes['E{0:02d}'.format(_entry)])
		else:
			raise SeasonNotFound('SeasonNotFound: {} - Season {}'.format(self.titleTVDB, snumber))
		if _eplist:
			return _eplist
		else:
			raise EpisodeNotFound('EpisodeNotFound: {} - Season {}  Episode {}'.format(self.titleTVDB,
			                                                                           snumber,
			                                                                           number))

	def search(self, title=None, rtn=object):
		_filterOrder = ['tz', 'status', 'rating', 'scores', 'newest']
		_filter_options = {'scores': self._flt_scores,
		                   'tz': self._flt_tz,
		                   'match': self._flt_match,
		                   'rating': self._flt_rating,
		                   'status': self._flt_status,
				           'newest': self._flt_newest
							}

		try:
			if not title is None:
				self.title = title
			if self.titleType == "Year":
				self._list = searchShow(show=self.titleBase, year=self.titleSuffix, rtn=list)
				for _entry in self._list:
					if _entry.year == self.titleSuffix:
						continue
					_entry.title = 'SKIP'
				self._list = filter(_filter_options['match'], self._list)
				if type(self._list) is HTTPError or not len(self._list) > 0:
					self._list = searchShow(show=self.titleBase, rtn=list)
			elif self.titleType == 'Country':
				self._list = searchShow(show=self.titleBase, rtn=list)
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

	def copy(self):
		_series = Series()
		for key, val in self.__dict__.iteritems():
			if val is not None:
				setattr(_series, key, val)
		return _series

	def merge(self, source):
		for key, val in source.__dict__.iteritems():
			if key == 'fileDetails':
				continue
			if val is not None:
				setattr(self, key, val)
		if not self.titleTVDB is None and hasattr(self, 'fileDetails'):
			self.fileDetails.seriesTitle = self.titleTVDB
		return self

	def _std_key(self, key):
		_key_conversions = {'firstaired': 'first_aired',
							'id': 'tvdb_id',
		                    'seriesid': 'tvdb_id',
		                    'seasonnum': 'seasonNum',
		                    'episodelist': 'episodeNums',
		                    'episodenums': 'episodeNums',
		                    'filename': 'fileName',
							"available_translations": '__discard',
		                    "homepage": '__discard',
		                    "votes": '__discard',
		                    "plays": '__discard',
		                    "trailer": '__discard',
		                    "updated_at": '__discard',
		                    'listed_at': '__discard',
		                    'type': '__discard',
		                    'last_collected_at': '__discard',
		                    'last_watched_at': '__discard',
		                    "images": '__discard',
		                    'airs_dayofweek': '__discard',
		                    'airs_time': '__discard',
		                    'actors': '__discard',
		                    'networkid': '__discard',
		                    'ratingcount': '__discard',
		                    'runtime': '__discard',
		                    'actor_objects': '__discard',
		                    'added': '__discard',
		                    'addedby': '__discard',
		                    'api': '__discard',
		                    'banner': '__discard',
		                    'banner_objects': '__discard',
		                    'fanart': '__discard',
		                    'language': '__discard',
		                    'lastupdated': '__discard',
		                    'poster': '__discard',
		                    'tms_wanted_old': '__discard',
		                    'zap2it_id': '__discard',
		                    'contentrating': '__discard'
		}

		key = key.lower()
		if key in _key_conversions:
			return _key_conversions[key]
		else:
			return key

	def __str__(self):
		"""Return a string representation of a :class:`TVShow`"""
		header = '<Series>'
		header = map(str, header)
		header = ' '.join(header)
		return '{}: {}'.format(header, self.title.encode('ascii', 'ignore'))
	__repr__ = __str__


	# Series Filters
	def _flt_tz(self, x): return x.airs['timezone'] == u'America/New_York'
	def _flt_status(self, x): return x.status in ['Continuing', 'Ended']
	def _flt_scores(self, x): return x.score == max(x.score for x in self._list)
	def _flt_newest(self, x): return x.first_aired == max(x.first_aired for x in self._list)
	def _flt_rating(self, x): return x.rating == max(x.rating for x in self._list)
	def _flt_match(self, x): return matching(x.titleBase, self.titleBase) == max([max(matching(x.titleBase, self.titleBase) for x in self._list), 60])


class Season(object):
	"""Container for Seasons"""
	def __init__(self, series, **kwargs):
		super(Season, self).__init__()
		self.seriesTrakt = series
		self.number = None
		self.ids = {u'tmdb': None, u'trakt': None,
		            u'tvdb': None, u'tvrage': None}
		self._episodes = None

		if len(kwargs) > 0:
			for key, val in kwargs.items():
				if type(val) is unicode:
					setattr(self, key, val.encode('ascii', 'ignore'))
				else:
					setattr(self, key, val)


	@property
	def tmdb_id(self):
		"""The series tmdb id."""
		return self.ids[u'tmdb']
	@tmdb_id.setter
	def tmdb_id(self, value):
		if value is None and self.ids[u'tmdb'] is None:
			return
		if value is '':
			value = None
		self.ids[u'tmdb'] = int(value)
		return

	@property
	def trakt_id(self):
		"""The series trakt id."""
		return self.ids[u'trakt']
	@trakt_id.setter
	def trakt_id(self, value):
		if value is None and self.ids[u'trakt'] is None:
			return
		if value is '':
			value = None
		self.ids[u'trakt'] = int(value)
		return

	@property
	def tvdb_id(self):
		"""The series tvdb id."""
		return self.ids[u'tvdb']
	@tvdb_id.setter
	def tvdb_id(self, value):
		if value is None and self.ids[u'tvdb'] is None:
			return
		if value is '':
			value = None
		self.ids[u'tvdb'] = value

		return

	@property
	def tvrage_id(self):
		"""The series tvrage id."""
		return self.ids[u'tvrage']
	@tvrage_id.setter
	def tvrage_id(self, value):
		if value is None and self.ids[u'tvrage'] is None:
			return
		if value is '':
			value = None
		self.ids[u'tvrage'] = value
		return

	@property
	def episodes(self, number=None):
		"""The series Episode"""
		return self._episodes
	@episodes.setter
	def episodes(self, episodes=None):
		if episodes: self._episodes = {}
		for _entry in episodes:
			self._episodes['E{0:02d}'.format(_entry['number'])] = Episode(self.seriesTrakt, **_entry)

	def __str__(self):
		"""Return a string representation of a :class:`Season`"""
		return '<Season>: {0:02d}'.format(self.number)
	__repr__ = __str__


class Episode(object):
	"""Container for Episodes"""
	def __init__(self, seriesTrakt, **kwargs):
		super(Episode, self).__init__()
		self.seriesTrakt = seriesTrakt
		self.season = None
		self.number = None
		self.title = None
		self.ids = None
		self._first_aired = None

		self.load_attr(kwargs)

	def load_attr(self, kwargs):
		if len(kwargs) > 0:
			_skip_keys = ['votes', 'rating', 'updated_at', 'available_translations']
			for key, val in kwargs.items():
				if key in _skip_keys:
					continue
				if type(val) is unicode:
					setattr(self, key, val.encode('ascii', 'ignore'))
				else:
					setattr(self, key, val)
		return

	@property
	def tmdb_id(self):
		"""The series tmdb id."""
		return self.ids[u'tmdb']
	@tmdb_id.setter
	def tmdb_id(self, value):
		if value is None and self.ids[u'tmdb'] is None:
			return
		if value is '':
			value = None
		self.ids[u'tmdb'] = int(value)
		return

	@property
	def trakt_id(self):
		"""The series trakt id."""
		return self.ids[u'trakt']
	@trakt_id.setter
	def trakt_id(self, value):
		if value is None and self.ids[u'trakt'] is None:
			return
		if value is '':
			value = None
		self.ids[u'trakt'] = int(value)
		return

	@property
	def tvdb_id(self):
		"""The series tvdb id."""
		return self.ids[u'tvdb']
	@tvdb_id.setter
	def tvdb_id(self, value):
		if value is None and self.ids[u'tvdb'] is None:
			return
		if value is '':
			value = None
		self.ids[u'tvdb'] = value

		return

	@property
	def tvrage_id(self):
		"""The series tvrage id."""
		return self.ids[u'tvrage']
	@tvrage_id.setter
	def tvrage_id(self, value):
		if value is None and self.ids[u'tvrage'] is None:
			return
		if value is '':
			value = None
		self.ids[u'tvrage'] = value
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

	def getDetails(self):
		self.load_attr(getEpisode(self.seriesTrakt, self.season, self.number))
		return

	def __str__(self):
		return '<Episode>: {0:03d}'.format(self.number)
	__repr__ = __str__


class fileDetails(object):
	"""Container for Series/Episode Information"""
	def __init__(self, series, **kwargs):
		super(fileDetails, self).__init__()
		self.seriesTitle = series
		self.seasonNum = None
		self.episodeNums = None
		self.fileName = None
		self.ext = None

		if len(kwargs) > 0:
			for key, val in kwargs.items():
				setattr(self, key, val)
		return

	def add_episodes(self, episodes):
		self.episodes = episodes

	def __str__(self):
		return '<FileDetails>: {}'.format(self.seriesTitle)
	__repr__ = __str__
