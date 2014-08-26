# -*- coding: UTF-8 -*-
"""
Purpose:

"""

import re
import datetime

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

	__check_suffix = re.compile('^(?P<SeriesName>.*)[ \._\-][\(]?(?P<Suffix>(?:19|20)\d{2}|us).*$', re.I)

	def __init__(self, title='', **kwargs):
		super(TVSeries, self).__init__()

		__options = {'name': self._set_title,
					'title': self._set_title,
		            'SeriesName': self._set_title,
					'seriesid': self._set_tvdb_id,
					'showid': self._set_tvrage_id,
					'IMDB_ID': self._set_imdb_id,
					'status': self._set_status,
					'Status': self._set_status,
					'FirstAired': self._set_year,
					'Network': self._set_network,
					'tvdb_id': self._set_selected_attr,
					'tvrage_id': self._set_selected_attr,
					'imdb_id': self._set_selected_attr,
					'year': self._set_selected_attr,
					'started': self._set_selected_attr,
					'seasons': self._set_selected_attr,
					'ended': self._set_selected_attr,
					'country': self._set_selected_attr,
					'network': self._set_selected_attr,
					'AliasNames': self._set_selected_attr
		}
		self.title = unicode(title)
		self.title_base = self.title_suffix = self.title_type = None
		self.tvdb_id = None
		self.imdb_id = None
		self.tvrage_id = None
		self.status = None
		self.seasons = []
		self.year = None
		self.country = None
		self.network = None
		self.AliasNames = None
		if len(kwargs) > 0:
			for key, val in kwargs.items():
				if key == 'tvrage':
					for key2, val2 in vars(val).iteritems():
						try: __options[key2](key2, val2)
						except KeyError: continue
				elif key == 'tvdb':
					for key2, val2 in vars(val).iteritems():
						if key2 == 'data':
							for key3, val3 in val2.iteritems():
								try: __options[key3](key3, val3)
								except KeyError: continue
				else:
					setattr(self, key, val)

	def _set_title(self, key, title):
		setattr(self, 'title', unicode(title))
		setattr(self, 'title_base', unicode(title))
		_suffix_present = TVSeries.__check_suffix.match(title.encode('ascii', 'ignore'))
		if _suffix_present:
			setattr(self, 'title_base', unicode(_suffix_present.group('SeriesName')))
			setattr(self, 'title_suffix', _suffix_present.group('Suffix'))
			if _suffix_present.group('Suffix').isdigit():
				setattr(self, 'title_type', 'Year')
			else:
				setattr(self, 'title_type', 'Country')
		return

	def _set_tvdb_id(self, key, tvdb_id):
		setattr(self, 'tvdb_id', tvdb_id)
		return

	def _set_tvrage_id(self, key, tvrage_id):
		setattr(self, 'tvrage_id', tvrage_id)
		return

	def _set_imdb_id(self, key, imdb_id):
		setattr(self, 'imdb_id', imdb_id)
		return

	def _set_network(self, key, network):
		setattr(self, 'network', network)
		return

	def _set_status(self, key, status):
		if status in ['New Series', 'Returning Series', 'Continuing', 'Hiatus']:
			setattr(self, 'status', 'Continuing')
		elif status in ['Canceled/Ended', 'Ended']:
			setattr(self, 'status', 'Canceled/Ended')
		else:
			setattr(self, 'status', 'Other')
		return

	def _set_year(self, key, FirstAired):
		if type(FirstAired) is datetime.date:
			setattr(self, 'year', FirstAired.year)
		return

	def _set_selected_attr(self, key, val):
		setattr(self, key, unicode(val))

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
		return '<TVSeries> {}'.format(self.title.encode('ascii', 'ignore'))
	__repr__ = __str__


class TVSeason(object):
	"""Container for TV Seasons"""
	def __init__(self, show, season=1):
		super(TVSeason, self).__init__()
		self.show = show
		self.season = season
		self.episodes = []
		self.tvdb_id = self.imdb_id = None
		try:
			self.search(self.show, self.season)
		except ValueError:
			return

	def search(self, show, season):
		pass

	def __str__(self):
		title = ['<TVSeason>:', self.show, 'Season', self.season]
		title = map(str, title)
		return ' '.join(title)
	__repr__ = __str__


class TVEpisode(object):
	"""Container for TV Episodes"""
	def __init__(self, show, season, episode_num=-1, episode_data=None):
		super(TVEpisode, self).__init__()
		self.show = show
		self.season = season
		self.episode = episode_num
		self.overview = self.title = self.year = self.tvdb_id =  None
		self._stats = self.imdb_id = None
		if episode_data is None and episode_num == -1:
			# Do nothing, not enough info given
			pass
		elif episode_num != -1 and episode_data is None:
			self.search(self.show, self.season, self.episode)
		else:  # episode_data != None
			for key, val in episode_data.items():
				if key != 'episode':
					setattr(self, key, val)

	def search(self, show, season, episode_num):
		pass

	def __repr__(self):
		return '<TVEpisode>: {} S{}E{} {}'.format(self.show, self.season,
												  self.episode, self.title)
	__str__ = __repr__

	@property
	def _standard_args(self):
		"""JSON representation of this :class:`TVEpisode` as used by several
		method calls
		"""
		return {'imdb_id': self.imdb_id, 'tvdb_id': self.tvdb_id,
				'title': self.title, 'year': self.year,
				'episodes': [{'season': self.season, 'episode': self.episode}]}


class Show(object):
	"""represents a TV show description from tvrage.com

	this class is kind of a wrapper around the following of tvrage's xml feeds:
	* http://www.tvrage.com/feeds/search.php?show=SHOWNAME
	* http://www.tvrage.com/feeds/episode_list.php?sid=SHOWID
	"""

	def __init__(self, name):
		self.shortname = name
		self.episodes = {}

		# the following properties will be populated dynamically
		self.genres = []
		self.showid = ''
		self.name = ''
		self.link = ''
		self.country = ''
		self.status = ''
		self.classification = ''
		self.started = 0
		self.ended = 0
		self.seasons = 0

	@property
	def pilot(self):
		"""returns the pilot/1st episode"""
		return self.episodes[1][1]


class Season(dict):
	"""represents a season container object"""

	is_current = False

	def episode(self, n):
		"""returns the nth episode"""
		return self[n]

	@property
	def premiere(self):
		"""returns the season premiere episode"""
		return self[1]  # analog to the real world, season is 1-based

	@property
	def finale(self):
		"""returns the season finale episode"""
		if not self.is_current:
			return self[len(self.keys())]
		else:
			raise FinaleMayNotBeAnnouncedYet('this is the current season...')


class Episode(object):
	"""represents an tv episode description from tvrage.com"""

	def __init__(self, show, season, airdate, title, link, number, prodnumber):
		self.show = show
		self.season = season
		try:
			self.airdate = date.fromtimestamp(mktime(
				strptime(airdate, '%Y-%m-%d')))
		except ValueError:
			self.airdate = None
		self.title = title
		self.link = link
		self.number = number
		self.prodnumber = prodnumber
		self.recap_url = link + '/recap'
		self.id = link.split('/')[-1]

	def __unicode__(self):
		return u'%s %sx%02d %s' % (self.show,
								   self.season, self.number, self.title)

	__str__ = __repr__ = __unicode__

	@property
	def summary(self):
		"""parses the episode's summary from the episode's tvrage page"""
		try:
			page = _fetch(self.link).read()
			if not 'Click here to add a summary' in page:
				summary = parse_synopsis(page, cleanup='var addthis_config')
				return summary
		except Exception, e:
			print('Episode.summary: %s, %s' % (self, e))
		return 'No summary available'

	@property
	def recap(self):
		"""parses the episode's recap text from the episode's tvrage recap
		page"""
		try:
			page = _fetch(self.recap_url).read()
			if not 'Click here to add a recap for' in page:
				recap = parse_synopsis(page,
									   cleanup='Share this article with your'
									   ' friends')
				return recap
		except Exception, e:
			print('Episode.recap:urlopen: %s, %s' % (self, e))
		return 'No recap available'
