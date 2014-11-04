#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
	Initialization Routine for a Series

'''

import re
import datetime
import unicodedata

__pgmname__ = 'series'
__version__ = '@version: $Rev$'

__author__ = "@author: AJ Reynolds"
__copyright__ = "@copyright: Copyright 2011, AJ Reynolds"
__status__ = "@status: Development"
__license__ = "@license: GPL"

__maintainer__ = "@organization: AJ Reynolds"
__credits__ = []

class Series(object):

	def __init__(self, **kwargs):

		super(Series, self).__init__()

		self._title = None
		self.titleBase = self.titleSuffix = self.titleType = None
		self.imdb_id = self.tmdb_id = self.tvdb_id = self.tvrage_id = None
		self.imdb_info = self.tmdb_info = self.tvdb_info = self.tvrage_info = None
		self.season = None
		self.seasons = None
		self.episodeNums = None
		self._status = None
		self.firstAired = None
		self.country = None
		self.network = None
		self.aliasNames = None
		self.fileName = None
		self.source = None
		self._topShow = 'Unknown'
		self.episodeData = None             #transitional attribute
		self.ext = None
		self.ended = None
		self.started = None

		__keysHandler = {'name': self._set_title,
						'seriesname': self._set_title,
						'seriesid': self._set_tvdb_id,
						'tvdb_id': self._set_tvdb_id,
						'showid': self._set_tvrage_id,
						'tvrage_id': self._set_tvrage_id,
						'imdb_id': self._set_imdb_id,
						'status': self._set_status,
						'aliasnames': self._set_alias,
						'network': self._set_network,
						'firstaired': self._set_firstAired
						}

		attrs = ['seasons', 'started', 'ended', 'country', 'topShow']

		if len(kwargs) > 0:
			for key, val in kwargs.items():
				if key == 'seriesinfo':
					for key2, val2 in val.iteritems():
						try:
							__keysHandler[key2.lower()](key2, val2)
						except KeyError:
							if key2 == 'FileName':
								setattr(self, 'fileName', val2)
							elif key2 == 'SeasonNum':
								setattr(self, 'season', int(val2))
							elif key2 == 'EpisodeNums':
								setattr(self, 'episodeNums', val2)
							elif key2 == 'Ext':
								setattr(self, 'ext', val2)
							else:
								setattr(self, key, val2)
				elif key == 'tvrage':
					for key2, val2 in val.iteritems():
						try:
							__keysHandler[key2.lower()](key2, val2)
						except KeyError:
							if key2 in attrs:
								setattr(self, key2, val2)
							continue
				elif key == 'tvdb':
					for key2, val2 in vars(val).iteritems():
						if key2 == 'data':
							for key3, val3 in val2.iteritems():
								try:
									__keysHandler[key3.lower()](key3, val3)
								except KeyError:
									if key3 in attrs:
										setattr(self, key3, val3)
									continue

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

		value = value.encode('ascii', 'ignore')
		_title_parts = value.rsplit(None, 1)
		if len(_title_parts) > 1:
			_year = __year.match(_title_parts[1])
			if _year:
				_title_parts[1] = _title_parts[1].replace('(', '').replace(')', '')
				self.titleBase = _title_parts[0]
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

	def _set_title(self, key, val):
		self.title = val
		return

	@property
	def status(self):
		"""The series status."""
		return self._status
	@status.setter
	def status(self, value):
		if value in ['New Series', 'Returning Series', 'Continuing', 'Hiatus']:
			setattr(self, '_status', 'Continuing')
		elif value in ['Canceled/Ended', 'Ended']:
			setattr(self, '_status', 'Canceled/Ended')
		else:
			setattr(self, '_status', 'Other')
		return

	def _set_status(self, key, val):
		self.status = val
		return

	@property
	def topShow(self):
		if self._topShow is None:
			self.topShow.setter()
		return self._topShow
	@topShow.setter
	def topShow(self):
		if self.trakt_user:
			_trakt_top_shows = self.trakt_user.get_list('topshows')
			_trakt_top_shows_names = {_item.title: _item for _item in _trakt_top_shows.items}
			if self.title in _trakt_top_shows_names:
				self._topShow = True
			else:
				self._topShow = False
		else: self._topShow = 'Unknown'

	@property
	def _search_title(self):
		"""The title of this :class:`Series` formatted in a searchable way"""
		_title = self.title.replace(' ', '-').lower()
		_title = _title.replace('&', 'and')
		_title = re.sub('[^A-Za-z0-9\-]+', '', _title)
		return _title

	@property
	def showFromUS(self):
		if self.country == 'US':
			return True
		if self.titleType == None:
			return None
		return False

	@property
	def keysFound(self):
		if self.tvdb_id is not None or self.tvrage_id is not None:
			return True
		return False

	def _set_tvdb_id(self, key, val):
		if key == 'SeriesID': return
		setattr(self, 'tvdb_id', int(val))
		return

	def _set_tvrage_id(self, key, val):
		setattr(self, 'tvrage_id', int(val))
		return

	def _set_imdb_id(self, key, val):
		setattr(self, 'imdb_id', val.encode('ascii', 'ignore'))
		return

	def _set_firstAired(self, key, firstAired):
		if type(firstAired) is datetime.date:
			setattr(self, 'firstAired', firstAired.year)
		return

	def _set_alias(self, key, val):
		setattr(self, 'aliasNames', val)
		return

	def _set_network(self, key, val):
		setattr(self, 'network', val.encode('ascii', 'ignore'))
		return

	def search(self, show):
		pass

	def copy(self, series):
		for key, val in series.__dict__.iteritems():
			if val is not None:
				setattr(self, key, val)
		return

	def copyShow(self, series):
		for key, val in series.__dict__.iteritems():
			if key in ['season', 'episodeNums', 'ext', 'fileName', 'seriesinfo', 'episodeData']:
				continue

			if val is not None:
				setattr(self, key, val)
		return

	def update(self, series):
		for key, val in series.__dict__.iteritems():
			#Don't update if it exists
			if key not in ['_title','titleBase', 'titleType', 'titleSuffix']:
				if getattr(self, key) or val is None:
					continue

			if type(val) is unicode:
				setattr(self, key, val.encode('ascii', 'ignore'))
			else:
				setattr(self, key, val)
		return

	def getDict(self):

		SeriesDetails = {}
		SeriesDetails['SeriesName'] = self.title
		if self.episodeData:
			SeriesDetails['EpisodeData'] = self.episodeData
		if self.episodeNums:
			SeriesDetails['EpisodeNums'] = self.episodeNums
		if self.ext:
			SeriesDetails['Ext'] = self.ext
		if self.fileName:
			SeriesDetails['FileName'] = self.fileName
		if self.season:
			SeriesDetails['SeasonNum'] = self.season
		if self.tvdb_id:
			SeriesDetails['tvdb_id'] = int(self.tvdb_id)
		if self.imdb_id:
			SeriesDetails['imdb_id'] = self.imdb_id
		if self.tvrage_id:
			SeriesDetails['tvrage_id'] = self.tvrage_id
		if self.status:
			SeriesDetails['status'] = self.status
		if self.topShow:
			SeriesDetails['top_show'] = self.topShow
		if self.source:
			SeriesDetails['source'] = self.source

		SeriesDetails['TVSeries'] = self
		return SeriesDetails

	def addEpisode(self, _season, _episode):
		if type(_episode.EpisodeName) == unicode:
			_episode_name = unicodedata.normalize('NFKD', _episode.EpisodeName).encode('ascii', 'ignore')
			_episode_name = _episode_name.replace("&amp;", "&").replace("/", "_")
		else:
			_episode_name = str(_episode.EpisodeName)

		self.episodeData.append({'SeasonNum': _season.season_number,
								 'EpisodeNum': _episode.EpisodeNumber,
								 'EpisodeTitle': _episode_name,
								 'DateAired': _episode.FirstAired})


	def addRageEpisode(self, _season, _episode):
		self.episodeData.append({'SeasonNum': _season.season,
								 'EpisodeNum': _episode.episode,
								 'EpisodeTitle': _episode.title,
								 'DateAired': _episode.first_aired})


	def __str__(self):
		"""Return a string representation of a :class:`TVShow`"""
		header = '<Series>'
		header = map(str, header)
		header = ' '.join(header)
		return '{}: {}'.format(header, self.title.encode('ascii', 'ignore'))
	__repr__ = __str__

