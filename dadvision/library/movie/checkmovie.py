#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Purpose:
	 Scan Movie Library and report any possible issues discovered
'''

import fnmatch
import os
import sys

import logger
from dadvision.library import Library

__pgmname__ = 'movie.check'

__author__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"

__maintainer__ = __author__

__copyright__ = "Copyright 2011, AJ Reynolds"
__license__ = "GPL"

log = logger.logging.getLogger(__pgmname__)

class CheckMovies(Library):
	'''
	classdocs
	'''

	def __init__(self, **kwargs):

		super(CheckMovies, self).__init__()

	def check_movies(self, pathname):
		_files_checked = 0

		log.info("==== Begin Scan: {} ====".format(pathname))

		for _root, _dirs, _files in os.walk(os.path.abspath(pathname), followlinks=True):
			_formats_found = {}
			_file_names = []
			_number_of_formats = 0
			if _dirs != None:
				_dirs.sort()
				_dirs_temp = sorted(_dirs)
				for _dir in _dirs_temp:
					if self.ignored(_dir):
						_dirs.remove(_dir)
						log.trace('Removing Dir: %s' % _dir)
						continue
			_files.sort()
			for _file in _files:
				_ext = os.path.splitext(_file)[1][1:].lower()
				if _ext in ['ifo', 'bup']:
					_files_checked += 1
					continue
				if _ext in self.settings.MediaExt:
					_files_checked += 1
					if _ext == 'vob':
						_formats_found['dvd'] = True
						if 'DVD' not in _file_names:
							_file_names.append('DVD')
					else:
						_formats_found[_ext] = True
						_file_names.append(_file)

			for _entry in _formats_found:
				if _entry == 'ifo' or _entry == 'bup':
					continue
				_number_of_formats += 1

			if _number_of_formats > 1:
				log.info('Possible Dups Found: {}'.format(_root))
				for _file in _file_names:
					log.info('    FileName: {}'.format(_file))

	def ignored(self, name):
		""" Check for ignored pathnames.
		"""
		return any(fnmatch.fnmatch(name.lower(), pattern) for pattern in (self.settings.ExcludeList + self.settings.ExcludeScanList) + self.settings.IgnoreGlob)


if __name__ == '__main__':

	logger.initialize()
	Library.args = Library.cmdoptions.ParseArgs(sys.argv[1:])

	if not Library.args.filespec:
		Library.args.filespec = [Library.settings.MoviesDir]
	if type(Library.args.filespec) != list:
		Library.args.filespec = [Library.args.filespec]

	library = CheckMovies()
	for _lib_path in Library.args.filespec:
		if os.path.exists(_lib_path):
			library.check_movies(_lib_path)
		else:
			log.error('Library Not Found: {}'.format(_lib_path))
