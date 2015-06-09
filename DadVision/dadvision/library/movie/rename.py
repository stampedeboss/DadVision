#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Purpose:
Program to rename files associated with Movie Content

"""
import filecmp
import fnmatch
import logging
import os
import re
import sys
import shutil

from common import logger
from common.chkvideo import chkVideoFile
from common.exceptions import (InvalidPath, InvalidFilename, UnexpectedErrorOccured,
							MovieNotFound, RegxSelectionError, NoValidFilesFound, NotMediaFile)
from library import Library
from library.movie.fileparser import FileParser
from library.movie.gettmdb import TMDBInfo


__pgmname__ = 'rename'
__version__ = '$Rev$'

__author__ = "@author: AJ Reynolds"
__copyright__ = "@copyright: Copyright 2011, AJ Reynolds"
__license__ = "@license: GPL"
__email__ = "@contact: stampedeboss@gmail.com"

__maintainer__ = "@organization: AJ Reynolds"
__status__ = "@status: Development"
__credits__ = []

log = logging.getLogger(__pgmname__)


def uselibrarylogging(func):
	def wrapper(self, *args, **kw):
		# Set the library name in the logger
		# from daddyvision.common import logger
		logger.set_library('movie')
		try:
			return func(self, *args, **kw)
		finally:
			logger.set_library('')

	return wrapper


def _del_dir(pathname, Tree=False):
	log.trace("_del_dir: pathname:{!s}".format(pathname))

	if not os.path.isdir(pathname):
		raise InvalidPath('Invalid Path was requested for deletion: {}'.format(pathname))

	try:
		log.info('Deleting Empty Directory: {}'.format(pathname))
		if Tree:
			shutil.rmtree(pathname)
		else:
			os.rmdir(pathname)
	except:
		log.warn('Delete Directory: Unable to Delete requested directory: %s' % (sys.exc_info()[1]))


def _del_file(pathname):
	log.trace("_del_file: pathname:{!s}".format(pathname))

	if os.path.isdir(pathname):
		raise InvalidPath('Path was requested for deletion: {}'.format(pathname))

	try:
		log.info('Deleting File as Requested: {}'.format(pathname))
		os.remove(pathname)
	except:
		log.warn('Delete File: Unable to Delete requested file: %s' % (sys.exc_info()[1]))


class RenameMovie(Library):
	def __init__(self):
		log.trace("INIT: =================================================")
		log.trace('Rename.__init__ method: Started')

		super(RenameMovie, self).__init__()

		rename_group = self.options.parser.add_argument_group("Rename Options", description=None)
		rename_group.add_argument("--force-rename", dest="force_rename",
								  action="store_true", default=False,
								  help="Force Renames for Files That Already Exist")
		rename_group.add_argument("--force-delete", "--fd", dest="force_delete",
								  action="store_true", default=False,
								  help="Force Deletes for Files That Already Exist")
		rename_group.add_argument("--ignore_excludes", dest="ignore_excludes",
								  action="store_true", default=False,
								  help="Process all Files Regardless of Excludes")
		rename_group.add_argument("--no-check_video", dest="check_video",
								  action="store_false", default=True,
								  help="Bypass Video Checks")
		rename_group.add_argument("--no-move", "--nm", dest="move",
								  action="store_false", default=True,
								  help="Do not change directories, rename in place")
		rename_group.add_argument("--dir", type=str, dest='dir',
		                          nargs='?', default=None,
								  help="Rename and place in this directory")

		self.fileparser = FileParser()
		self.tmdbinfo = TMDBInfo()

		self.regex_repack = re.compile('^.*(repack|proper).*$', re.IGNORECASE)
		self.regex_NewMoviesDir = re.compile('^{}.*$'.format(self.settings.NewMoviesDir, re.IGNORECASE))

		log.trace("INIT END: =============================================")
		return

	@uselibrarylogging
	def renameMovie(self, pathname):
		log.trace("=================================================")
		log.trace("rename method: pathname:{}".format(pathname))

		pathname = os.path.abspath(pathname)

		if os.path.isfile(pathname):
			log.debug("-----------------------------------------------")
			log.debug("Movie Directory: %s" % os.path.split(pathname)[0])
			log.debug("Movie Filename:  %s" % os.path.split(pathname)[1])
			try:
				_movie_details = self._retrieve_movie_info(pathname)
				self._rename_file(_movie_details)
			except (MovieNotFound, InvalidFilename, NotMediaFile, NoValidFilesFound):
				raise

		elif os.path.isdir(pathname):
			log.debug("-----------------------------------------------")
			log.debug("Movie Directory: %s" % pathname)
			for _root, _dirs, _files in os.walk(os.path.abspath(pathname)):
				_dirs.sort()
				for _dir in _dirs[:]:
					# Process Enbedded Directories
					if self._ignored(_dir):
						_dirs.remove(_dir)
						if self.regex_NewMoviesDir.match(_dir):
							log.trace("Deleting Excluded Directory: {}".format(os.path.join(_root, _dir)))
							_del_dir(_dir, Tree=True)

					if _dir == 'VIDEO_TS':
						self._rename_directory(_root)
						_dirs.remove(_dir)

				_files.sort()
				for _file in _files:
					_path_name = os.path.join(_root, _file)
					log.trace("Movie Filename: %s" % _file)
					if self._ignored(_path_name):
						if self.regex_NewMoviesDir.match(_path_name):
							try:
								_del_file(_path_name)
							except InvalidPath:
								pass
						continue
					try:
						_movie_details = self._retrieve_movie_info(_path_name)
						self._rename_file(_movie_details)
					except (MovieNotFound, InvalidFilename, NotMediaFile, NoValidFilesFound):
						pass

				if os.path.exists(_root) and len(os.listdir(_root)) == 0:
					_del_dir(_root)

		return None

	@uselibrarylogging
	def _retrieve_movie_info(self, pathname):
		log.trace("=================================================")
		log.trace("_retrieve_movie_info method: pathname:{!s}".format(pathname))

		_ext = os.path.splitext(pathname)[1][1:]
		if not _ext in self.settings.MediaExt:
			raise NotMediaFile

		if self.args.check_video:
			if chkVideoFile(pathname):
				log.error('File Failed Video Check: {}'.format(pathname))
				raise NoValidFilesFound

		try:
			_movie_details = self.fileparser.getFileDetails(pathname)
		except (InvalidFilename, UnexpectedErrorOccured, RegxSelectionError):
			raise
		try:
			_movie_details = self.tmdbinfo.retrieve_info(_movie_details)
		except MovieNotFound:
			try:
				# Movie wasn't found by filename try Directory Name
				_dir_name = os.path.dirname(pathname) + '.' + _ext
				_directory_details = self.fileparser.getFileDetails(_dir_name)
				_movie_details['MovieName'] = _directory_details['MovieName']
				_movie_details = self.tmdbinfo.retrieve_info(_movie_details)
			except (InvalidFilename, UnexpectedErrorOccured, RegxSelectionError):
				raise

		return _movie_details

	@uselibrarylogging
	def _rename_directory(self, directory):
		log.trace("=================================================")
		log.trace("_rename_directory method: pathname:{!s}".format(directory))

		_directory_details = self.fileparser.getFileDetails(directory + '.avi')
		_directory_details['FileName'] = directory

		_directory_details = self.tmdbinfo.retrieve_info(_directory_details)

		if 'Year' in _directory_details:
			_new_dir = '%s (%s)' % (_directory_details['MovieName'], _directory_details['Year'])
		else:
			_new_dir = '%s' % (_directory_details['MovieName'])

		_target_dir = os.path.join(self.settings.MoviesDir, _new_dir)

		if os.path.exists(_target_dir):
			if _target_dir == directory:
				log.trace('Skipping: Directory already properly named and in: {}'.format(directory))
				return
			else:
				_target_dir = os.path.join(os.path.split(self.settings.MoviesDir)[0], _new_dir)
				if os.path.exists(_target_dir):
					log.warn("Unable to process, Directory: {}, already at destination!".format(_target_dir))
					return

		log.info('Renaming Movie Directory: %s to %s' % (os.path.basename(directory), _target_dir))
		try:
			os.rename(directory, _target_dir)
			log.info("Successfully Renamed: %s" % _target_dir)
		except OSError, exc:
			log.error("Skipping, Unable to Rename Directory: %s" % directory)
			log.error("Unexpected error: %s" % exc)
			raise UnexpectedErrorOccured("Unexpected error: %s" % exc)

		return None

	@uselibrarylogging
	def _rename_file(self, movie_details):
		log.trace("=================================================")
		log.trace("_rename_file method: movie_details: {!s}".format(movie_details))

		try:
			_fq_new_file_name = self._get_new_filename(movie_details)
			if not self._duplicate_file(_fq_new_file_name, movie_details['FileName']):
				log.info('Renaming Movie: %s to %s' % (os.path.basename(movie_details['FileName']), _fq_new_file_name))
				if not os.path.exists(os.path.dirname(_fq_new_file_name)):
					_new_dir = os.path.dirname(_fq_new_file_name)
					os.makedirs(_new_dir)
					os.chmod(_new_dir, 0775)
				os.rename(movie_details['FileName'], _fq_new_file_name)
				os.chmod(_fq_new_file_name, 0664)
				log.info("Successfully Renamed: %s" % _fq_new_file_name)
				if len(os.listdir(os.path.dirname(movie_details['FileName']))) > 0:
					return
				if self.args.move:
					_del_dir(os.path.dirname(movie_details['FileName']))
		except OSError, exc:
			log.error("Skipping, Unable to Rename File: %s" % movie_details['FileName'])
			log.error("Unexpected error: %s" % exc)
			raise UnexpectedErrorOccured("Unexpected error: %s" % exc)

		return

	def _get_new_filename(self, movie_details):
		log.trace("=================================================")
		log.trace("_get_new_filename method: pathname:{!s}".format(movie_details))

		if 'Trailer' in movie_details:
			_trailer = '-trailer'
		else:
			_trailer = ''

		if 'Year' in movie_details:
			_new_dir = '%s (%s)' % (movie_details['MovieName'], movie_details['Year'])
			_new_file_name = '%s (%s)%s.%s' % (
			movie_details['MovieName'], movie_details['Year'], _trailer, movie_details['Ext'])
		else:
			_new_dir = '%s' % (movie_details['MovieName'])
			_new_file_name = '%s%s.%s' % (movie_details['MovieName'], _trailer, movie_details['Ext'])

		if self.args.dir:
			_fq_new_file_name = os.path.join(self.args.dir, _new_dir, _new_file_name)
		elif self.args.move:
			_fq_new_file_name = os.path.join(self.settings.MoviesDir, _new_dir, _new_file_name)
		else:
			_fq_new_file_name = os.path.join(os.path.dirname(os.path.dirname(movie_details['FileName'])),
			                                 _new_dir,
			                                 _new_file_name)

		return _fq_new_file_name

	def _duplicate_file(self, new_file_name, old_file_name):
		log.trace("=================================================")
		log.trace("_duplicate_file method: filename: {} pathname:{!s}".format(new_file_name, old_file_name))

		if not os.path.exists(new_file_name):
			return False

		if new_file_name == old_file_name:
			log.info("No Action Required - Movie Library: {}".format(os.path.split(old_file_name)[1]))
			return True

		try:
			if self.args.force_rename or self.regex_repack.search(old_file_name):
				log.warn("Replacing Existing Version with repack or Force Rename Requested: File: %r!" % (
				os.path.split(new_file_name)[1]))
				os.remove(new_file_name)
				return False

			log.trace("Comparing existing file to new, may run for some time.")
			if filecmp.cmp(new_file_name, old_file_name):
				log.info("Deleting New File %r, Same File already at destination!" % (
				os.path.split(old_file_name)[1]))
				os.remove(old_file_name)
				return True

			if os.path.getsize(new_file_name) >= os.path.getsize(old_file_name):
				if self.args.force_delete:
					log.info("Deleting %r, Larger Version already at destination!" % (
					os.path.split(old_file_name)[1]))
					os.remove(old_file_name)
				else:
					log.info("Keeping %r in New, Larger Version already at destination!" % (
					os.path.split(old_file_name)[1]))
				return True
		except OSError, exc:
			log.error("Unable to remove File: %s" % new_file_name)
			log.error("Unexpected error: %s" % exc)
			return True
		return False


	def _ignored(self, name):
		""" Check for ignored pathnames.
		"""
		if self.args.ignore_excludes:
			rc = False
		else:
			rc = any(fnmatch.fnmatch(name.lower(), pattern) for pattern in self.settings.ExcludeList)

		return rc


if __name__ == "__main__":

	logger.initialize()
	library = RenameMovie()

	Library.args = library.options.parser.parse_args(sys.argv[1:])
	log.trace("MAIN: -------------------------------------------------")
	log.debug("Parsed command line: {!s}".format(library.args))

	log_level = logging.getLevelName(library.args.loglevel.upper())

	if library.args.logfile == 'daddyvision.log':
		log_file = '{}.log'.format(__pgmname__)
	else:
		log_file = os.path.expanduser(library.args.logfile)

	# If an absolute path is not specified, use the default directory.
	if not os.path.isabs(log_file):
		log_file = os.path.join(logger.LogDir, log_file)

	logger.start(log_file, log_level, timed=True)

	if len(library.args.library) < 1:
		log.warn('No pathname supplied for rename: Using default: {}'.format(library.settings.NewMoviesDir))
		library.args.library = [library.settings.NewMoviesDir]

	_lib_paths = library.args.library

	for _lib_path in _lib_paths:
		if os.path.exists(_lib_path):
			library.renameMovie(_lib_path)
		else:
			log.error('Skipping Rename: Unable to find File/Directory: {}'.format(_lib_path))

