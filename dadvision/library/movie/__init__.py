# -*- coding: UTF-8 -*-
'''
	Initialization Routine for movies

	Routine is call on any import of a module in the library

'''

from os.path import dirname, split, splitext, exists, join

from unidecode import unidecode
from slugify import Slugify

from dadvision import DadVision
from chkvideo import chkVideoFile
from common.exceptions import (MovieNotFound, NotMediaFile, TitleFromFileError,
                               InvalidFilename, FailedVideoCheck)
from library import rename_file, duplicate, media

myslug = Slugify(pretranslate={"'": "_"}, translate=unidecode, to_lower=True)

__pgmname__ = 'movie'

__author__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"

__maintainer__ = __author__

__copyright__ = "Copyright 2011, AJ Reynolds"
__license__ = "GPL"

log = DadVision.logger.getLogger(__pgmname__)


def uselibrarylogging(func):
	from common import logger
	def wrapper(self, *args, **kw):
		"""
		Set the library name in the logger
		"""
		logger.set_library('movie')
		try:
			return func(self, *args, **kw)
		finally:
			logger.set_library('')

	return wrapper


class Movie(object):

	def __init__(self, **kwargs):

		super(Movie, self).__init__()

		self.title = None
		self.alternate_title = None
		self.ids = {"imdb": None, "tmdb": None, "trakt": None, "slug": None}
		self.year = None
		self.plays = None
		self.cast = None
		self.container = None
		self.mimetype = None
		self.filename = None
		self.other = None
		self.validated = False

		self.load_attr(kwargs)

		return

	def load_attr(self, kwargs):

		if len(kwargs) > 0:
			for key, val in kwargs.items():
				if key in ['movie']:
					self.load_attr(val)
					continue
				if key == 'ids':
					for key2, val2 in val.iteritems():
						if val2:
							self.ids[key2] = val2
				if not val:
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
		self.ids['slug'] = str(myslug(value))
		return

	@property
	def imdb_id(self):
		"""The series imdb_id"""
		return self.ids['imdb']
	@imdb_id.setter
	def imdb_id(self, value):
		if value is None:
			return
		self.ids['imdb'] = str(value)
		return

	@property
	def tmdb_id(self):
		"""The series tmdb id."""
		return self.ids['tmdb']
	@tmdb_id.setter
	def tmdb_id(self, value):
		if value is None:
			return
		self.ids["tmdb"] = int(value)
		return

	@property
	def trakt_id(self):
		"""The series trakt id."""
		return self.ids['trakt']
	@trakt_id.setter
	def trakt_id(self, value):
		if value is None:
			return
		self.ids['trakt'] = int(value)
		return

	@property
	def _search_title(self):
		"""The title of this :class:`Movie` formatted in a searchable way"""
		return myslug(self.title)

	def copy(self):
		movie = Movie()
		for key, val in self.__dict__.itervalues():
			if not key == 'ids' and val:
				setattr(movie, key, val)
			elif key == 'ids':
				for key2, val2 in val.iteritems():
					if val2: movie.ids[key2] = val2
		return movie

	def rename(self, pathname=None):

		if pathname:
			self.filename = pathname
			self.media_details(pathname)
		if not self.filename \
				or not exists(self.filename) \
				or not self.filename[:len(DadVision.settings.MoviesDir)] == DadVision.settings.MoviesDir:
			raise InvalidFilename("Filename missing or does not exist")

		if DadVision.args.check_video:
			if chkVideoFile(self.filename):
				log.error('File Failed Video Check: {}'.format(self.filename))
				raise FailedVideoCheck("File Failed Video Check: {}".format(self.filename))

		try:
			if not self.validated:
				self.search()
			_year = ""
			if self.year:
				_year = " ({})".format(self.year)
			_other = ""
			if self.other and not self.other.lower() == 'proper':
				_other = " [{}]".format(self.other)
			new_dirname = "".join([self.title, _year])
			new_filename = "".join([new_dirname, _other, ".", self.container])
			new_filename_fq = join(DadVision.settings.MoviesDir, new_dirname, new_filename)
			if duplicate(self.filename, new_filename_fq, self.other): return
			rename_file(self.filename, new_filename_fq)
		except (MovieNotFound, TitleFromFileError, NotMediaFile), e:
			log.error("Unable to locate movie information, rename canceled")
			raise

		return

	def search(self):
		from movie.tmdb import TMDB
		self.__class__ = type('TMDB', (Movie, TMDB) ,{})
		try:
			self.tmdb()
			self.validated = True
		except MovieNotFound:
			# Movie wasn't found by filename try Directory Name
			if dirname(self.filename) in [DadVision.settings.NewMoviesDir,
			                              DadVision.settings.MoviesDir]:
				raise
			movie = Movie()
			movie.media_details(dirname(self.filename) + splitext(self.filename)[1])
			movie.search()
			delattr(movie, 'filename')
			self.load_attr(movie.__dict__)

	def media_details(self, fq_name):
		from guessit import guessit
		from titlecase import titlecase

		if not media(fq_name):
			raise NotMediaFile

		_path, _file_name = split(fq_name)
		_movie_details = guessit(_file_name, '-t movie')

		if 'alternative_title' in _movie_details:
			_save_title = _movie_details['title']
			_movie_details['title'] = _movie_details['alternative_title']
			_movie_details['alternative_title'] = _save_title
		if 'title' in _movie_details:
			_movie_details['title'] = titlecase(_movie_details['title'])
		else:
			raise TitleFromFileError('Guessit unable to determine title')

		self.filename = fq_name
		self.load_attr(_movie_details)
		return

	def __str__(self):
		"""Return a string representation of a :class:`Movie`"""
		header = '<Movie>'
		header = map(str, header)
		header = ' '.join(header)
		return '{}: {}'.format(header, self.title.encode('ascii', 'ignore'))
	__repr__ = __str__

if __name__ == '__main__':

	from sys import argv
	from logging import DEBUG; TRACE = 5; VERBOSE = 15

	DadVision.logger.initialize(level=DEBUG)

	from common.cmdoptions_rn import CmdOptionsRn
	from movie.cmdoptions import CmdOptions
	rnCmd = CmdOptionsRn()
	movieCmd = CmdOptions()
	DadVision.args = DadVision.cmdoptions.ParseArgs(argv[1:])

	DadVision.logger.start(DadVision.args.logfile, DEBUG, timed=DadVision.args.timed)

	movie = Movie()

	if len(DadVision.args.pathname) > 0:
		for pathname in DadVision.args.pathname:
			try:
				movie.media_details(pathname)
				movie.search()
				movie.rename()
			except Exception, e:
				pass
		print