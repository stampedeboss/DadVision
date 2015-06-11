# -*- coding: UTF-8 -*-
'''
	Initialization Routine for movies

	Routine is call on any import of a module in the library

'''
import re


__pgmname__ = 'movie'

__version__ = '@version: $Rev$'

__author__ = "@author: AJ Reynolds"
__copyright__ = "@copyright: Copyright 2011, AJ Reynolds"
__status__ = "@status: Development"
__license__ = "@license: GPL"

__maintainer__ = "@organization: AJ Reynolds"
__credits__ = []

class Movie(object):

	def __init__(self, **kwargs):

		super(Movie, self).__init__()

		self.title = None
		self.ids = None
		self.year = None
		self.plays = None

		self.load_attr(kwargs)

		return

	def load_attr(self, kwargs):
		__skip_attr = ["search", "available_translations", "homepage", "votes",
		               "trailer", "updated_at", 'airs', 'listed_at', 'type', 'last_collected_at']

		if len(kwargs) > 0:
			for key, val in kwargs.items():
				if key in __skip_attr:
					continue
				if key in ['movie']:
					self.load_attr(val)
				else:
					if val is unicode:
						setattr(self, key, val).encode('ascii', 'ignore')
					else:
						setattr(self, key, val)
		return

	@property
	def slug(self):
		"""The series slug."""
		return self.ids['slug']
	@slug.setter
	def slug(self, value):
		if value is None:
			return
		setattr(self, self.ids['slug'], value)
		return

	@property
	def imdb_id(self):
		"""The series imdb_id"""
		return self.ids['imdb']
	@imdb_id.setter
	def imdb_id(self, value):
		if value is None:
			return
		setattr(self, self.ids['imdb_id'], value)
		return

	@property
	def tmdb_id(self):
		"""The series tmdb id."""
		return self.ids['tmdb']
	@tmdb_id.setter
	def tmdb_id(self, value):
		if value is None:
			return
		setattr(self, self.ids['tmdb'], int(value))
		return

	@property
	def trakt_id(self):
		"""The series trakt id."""
		return self.ids['trakt']
	@trakt_id.setter
	def trakt_id(self, value):
		if value is None:
			return
		setattr(self, self.ids['trakt'], int(value))
		return

	@property
	def _search_title(self):
		"""The title of this :class:`Movie` formatted in a searchable way"""
		_title = self.title.replace(' ', '-').lower()
		_title = _title.replace('&', 'and')
		_title = re.sub('[^A-Za-z0-9\-]+', '', _title)
		return _title

	def search(self, show):
		pass

	def __str__(self):
		"""Return a string representation of a :class:`Movie`"""
		header = '<Movie>'
		header = map(str, header)
		header = ' '.join(header)
		return '{}: {}'.format(header, self.title.encode('ascii', 'ignore'))
	__repr__ = __str__

