# -*- coding: UTF-8 -*-
"""
Purpose:

"""

import re
from datetime import date
from time import mktime, strptime
from tvrage import feeds
from tvrage.util import _fetch, parse_synopsis
from tvrage.exceptions import (ShowHasEnded, FinaleMayNotBeAnnouncedYet,
                                ShowNotFound, NoNewEpisodesAnnounced)


__pgmname__ = 'TVSeries'
__version__ = '@version: $Rev: 418 $'

__author__ = "@author: AJ Reynolds"
__email__ = "@contact: stampedeboss@gmail.com"
__copyright__ = "@copyright: Copyright 2014, AJ Reynolds"
__license__ = "@license: GPL"

__maintainer__ = "@organization: AJ Reynolds"
__status__ = "@status: Development"
__credits__ = []

class TVSeries(object):
	"""A Class representing a TV Show object"""

	def __init__(self, title='New', **kwargs):
		super(TVSeries, self).__init__()

		__options = {'name': self._set_title,
					'SeriesName': self._set_title,
					'seriesid': self._set_tvdb_id,
					'showid': self._set_tvrage_id,
					'IMDB_ID': self._set_imdb_id,
					'status': self._set_status,
					'Status': self._set_status,
					'aliasnames': self._set_alias,
					'AliasNames': self._set_alias,
					'Network': self._set_network,
					'FirstAired': self._set_firstAired
		}
		self.title = title
		self.titleBase = self.titleSuffix = self.titleType = None
		self.tvdb_id = None
		self.imdb_id = None
		self.tvrage_id = None
		self.status = None
		self.seasons = {}
		self.firstAired = None
		self.country = None
		self.network = None
		self.aliasNames = None
		self._topShow = None
		attrs = ['tvdb_id', 'tvrage_id', 'imdb_id', 'seasons', 'firstAired',
		        'started', 'ended', 'country', 'network', 'topShow']
		if len(kwargs) > 0:
			for key, val in kwargs.items():
				if key in ['seriesdetails']:
					for key2, val2 in val.iteritems():
						try: __options[key2](key2, val2)
						except KeyError:
							if key2 in attrs:
								setattr(self, key2, val2)
							continue
				elif key == 'tvrage':
					for key2, val2 in val.iteritems():
						try: __options[key2](key2, val2)
						except KeyError:
							if key2 in attrs:
								setattr(self, key2, val2)
							continue
				elif key == 'tvdb':
					for key2, val2 in vars(val).iteritems():
						if key2 == 'data':
							for key3, val3 in val2.iteritems():
								try: __options[key3](key3, val3)
								except KeyError:
									if key3 in attrs:
										setattr(self, key3, val3)
									continue
				else:
					setattr(self, key, val)

	@property
	def title(self):
		"""The series title."""
		return self._title
	@title.setter
	def title(self, value):
		if value is None: return
		__check_suffix = re.compile('^(?P<SeriesName>.*)[ \._\-][\(]?(?P<Suffix>(?:19|20)\d{2}|us).*$', re.I)
		__suffix_present = __check_suffix.match(value.encode('ascii', 'ignore'))
		self._title = unicode(value)
		setattr(self, 'titleBase', unicode(value))
		if __suffix_present:
			setattr(self, 'titleBase', unicode(__suffix_present.group('SeriesName')))
			setattr(self, 'titleSuffix', __suffix_present.group('Suffix'))
			if __suffix_present.group('Suffix').isdigit():
				setattr(self, 'titleType', 'Year')
			else:
				setattr(self, 'titleType', 'Country')
		return

	def _set_tvdb_id(self, key, tvdb_id):
		setattr(self, 'tvdb_id', tvdb_id)
		return

	def _set_tvrage_id(self, key, tvrage_id):
		setattr(self, 'tvrage_id', tvrage_id)
		return

	def _set_imdb_id(self, key, tvrage_id):
		setattr(self, 'imdb_id', tvrage_id)
		return

	def _set_status(self, key, status):
		if status in ['New Series', 'Returning Series', 'Continuing', 'Hiatus']:
			setattr(self, 'status', 'Continuing')
		elif status in ['Canceled/Ended', 'Ended']:
			setattr(self, 'status', 'Canceled/Ended')
		else:
			setattr(self, 'status', 'Other')
		return

	def _set_alias(self, key, val):
		setattr(self, 'aliasNames', val)
		return

	def _set_network(self, key, val):
		setattr(self, 'network', val)
		return

	def _set_firstAired(self, key, FirstAired):
		if type(FirstAired) is date:
			setattr(self, 'firstAired', FirstAired.year)
		return

	def _set_selected_attr(self, key, val):
		setattr(self, key, val)

	@property
	def _search_title(self):
		"""The title of this :class:`TVShow` formatted in a searchable way"""
		_title = self.title.replace(' ', '-').lower()
		_title = _title.replace('&', 'and')
		_title = re.sub('[^A-Za-z0-9\-]+', '', _title)
		return _title

	def search(self, show):
		pass

	def __str__(self):
		"""Return a string representation of a :class:`TVShow`"""
		header = '<TVSeries>'
	 	header = map(str, header)
	 	header = ' '.join(header)
		return '{}: {}'.format(header, self.title.encode('ascii', 'ignore'))
	__repr__ = __str__


class TVSeason(object):
	"""Container for TV Seasons"""
	def __init__(self, series, **kwargs):
		super(TVSeason, self).__init__()
		self.series = series
		self.season = None
		self.episodes = {}
		if len(kwargs) > 0:
			for key, val in kwargs.items():
				setattr(self, key, val)

	def load_episodes(self, episodedata, **kwargs):
		pass

	def search(self, show, season):
		pass

	def __str__(self):
		header = '<TVSeason>'
	 	header = map(str, header)
	 	header = ' '.join(header)
		return '{0}: {1}  Season: {2:2d}'.format(header, self.series, self.season)
	__repr__ = __str__


class TVEpisode(object):
	"""Container for TV Episodes"""
	def __init__(self, series, **kwargs):
		super(TVEpisode, self).__init__()
		self.series = series
		self.season = None
		self.episode = None
		self.title = None
		self.first_aired = None
		self.tvdb_episode_id =  None
		if len(kwargs) > 0:
			for key, val in kwargs.items():
				setattr(self, key, val)

	def search(self, show, season, episode_num):
		pass

	def __repr__(self):
		return '<TVEpisode>: {0} S{1:02d}E{2:02d} {3}'.format(self.series, self.season,
												  self.episode, self.title)
	__str__ = __repr__

	# @property
	# def _standard_args(self):
	# 	"""JSON representation of this :class:`TVEpisode` as used by several
	# 	method calls
	# 	"""
	# 	return {'imdb_id': self.imdb_id, 'tvdb_id': self.tvdb_id,
	# 			'title': self.title, 'year': self.year,
	# 			'episodes': [{'season': self.season, 'episode': self.episode}]}

