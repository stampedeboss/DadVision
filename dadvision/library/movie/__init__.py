# -*- coding: UTF-8 -*-
'''
	Initialization Routine for movies

	Routine is call on any import of a module in the library

'''

import os
import re
from guessit import guessit
from titlecase import titlecase

from common.exceptions import MovieNotFound


__pgmname__ = 'movie'

__author__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"

__maintainer__ = __author__

__copyright__ = "Copyright 2011, AJ Reynolds"
__license__ = "GPL"


class Movie(object):

	def __init__(self, **kwargs):

		super(Movie, self).__init__()

		self.title = None
		self.alternative_title = None
		self.ids = None
		self.year = None
		self.plays = None
		self.cast = None
		self.container = None
		self.mimetype = None
		self.filename = None

		self.load_attr(kwargs)

		return

	def load_attr(self, kwargs):

		if len(kwargs) > 0:
			for key, val in kwargs.items():
				if key in ['movie' ]:
					self.load_attr(val)
					continue
				if not hasattr(self, key):
					continue
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

	def search(self, movie):
		pass

	def media_details(self, fq_name):

		_path, _file_name = os.path.split(fq_name)
		_movie_details = guessit(_file_name, '-t movie')

		if 'alternative_title' in _movie_details:
			_save_title = _movie_details['title']
			_movie_details['title'] = _movie_details['alternative_title']
			_movie_details['alternative_title'] = _save_title
		if 'title' in _movie_details:
			_movie_details['title'] = titlecase(_movie_details['title'])
		else:
			raise MovieNotFound('Guessit unable to determine title')

		self.filename = fq_name
		self.load_attr(_movie_details)

		return self

	def __str__(self):
		"""Return a string representation of a :class:`Movie`"""
		header = '<Movie>'
		header = map(str, header)
		header = ' '.join(header)
		return '{}: {}'.format(header, self.title.encode('ascii', 'ignore'))
	__repr__ = __str__

if __name__ == '__main__':

	import sys
	from dadvision.library import Library
	Library.args = Library.cmdoptions.ParseArgs(sys.argv[1:])

	movie = Movie()

	if Library.args.filespec:
		movie = movie.media_details(Library.args.filespec[0])

	pass