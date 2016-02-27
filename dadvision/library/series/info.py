#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Author: AJ Reynolds
Date: 12-11-2010
Purpose:
Program to rename and update Modification Time to Air Date

"""
import logging
import os
import re
import sys
import traceback

from common.exceptions import (SeriesNotFound, SeasonNotFound, EpisodeNotFound,
                               InvalidFilename)
from library import Library

import logger
from series import FileParser
from series import Series

__pgmname__ = 'info'

__author__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"

__maintainer__ = __author__

__copyright__ = "Copyright 2011, AJ Reynolds"
__license__ = "GPL"

log = logging.getLogger(__pgmname__)

def useLibraryLogging(func):

	def wrapper(self, *args, **kw):
		# Set the library name in the logger
		logger.set_library('series')
		try:
			return func(self, *args, **kw)
		finally:
			logger.set_library('')

	return wrapper


class seriesInfo(Library):

	def __init__(self):
		log.trace('__init__ method: Started')

		super(seriesInfo, self).__init__()

		seriesinfo_group = self.options.parser.add_argument_group("Episode Detail Options", description=None)
		seriesinfo_group.add_argument("--sn", "--name", type=str, dest='series_name')
		seriesinfo_group.add_argument("--season", type=int, dest='season')
		seriesinfo_group.add_argument("--epno", type=int, action='append', dest='epno')

		seriesinfo_group.add_argument("--series-only", "--so", dest="get_episodes",
				action="store_false", default=False,
				help="Information to come from trakt.tv")
		'''
		seriesinfo_group.add_argument("--tvdb", dest="processes",
				action="append_const", const='tvdb',
				help="Information to come from TVDB")
		seriesinfo_group.add_argument("--tvrage", dest="processes",
				action="append_const", const='tvrage',
				help="Information to come from TVRage")
		seriesinfo_group.add_argument("--trakt", dest="processes",
				action="append_const", const='trakt',
				help="Information to come from trakt.tv")
		'''

		self.parser = FileParser()

		self.regex_repack = re.compile('^.*(repack|proper).*$', re.IGNORECASE)
		self.check_suffix = re.compile('^(?P<seriesname>.+?)[ \._\-](?P<year>[0-9][0-9][0-9][0-9]|US|us|Us)$', re.VERBOSE)
		self.regex_SeriesDir = re.compile('^{}.*$'.format(self.settings.SeriesDir), re.IGNORECASE)

		self.selected_file = None

		return

	@useLibraryLogging
	def fileLookup(self, pathname):
		log.trace("fileLookup method: pathname:{}".format(pathname))

		if os.path.isfile(pathname):
			log.debug("-----------------------------------------------")
			log.debug("Directory: %s" % os.path.split(pathname)[0])
			log.debug("Filename:  %s" % os.path.split(pathname)[1])
			try:
				self._processFile(pathname)
			except (SeriesNotFound, SeasonNotFound, EpisodeNotFound), msg:
				an_error = traceback.format_exc()
				log.verbose(traceback.format_exception_only(type(an_error), an_error)[-1])
				log.error('Unable to Rename File: {}'.format(msg))

		elif os.path.isdir(pathname):
			for _root, _dirs, _files in os.walk(os.path.abspath(pathname), followlinks=False):
				for _dir in _dirs[:]:
					if self._ignored(_dir):
						log.debug("Ignoring %r" % os.path.join(_root, _dir))
						continue

				if _dirs == [] and _files == []:
					continue
				elif _files == []:
					continue

				_files.sort()
				for _file_name in _files:
					_path_name = os.path.join(_root, _file_name)
					log.debug("-----------------------------------------------")
					log.debug("Filename: %s" % _path_name)
					ext = os.path.splitext(_path_name)[1][1:]
					if self._ignored(_file_name) or os.path.splitext(_file_name)[1][1:] not in self.settings.MediaExt:
						continue
					try:
						self._processFile(_path_name)
					except (SeriesNotFound, SeasonNotFound, EpisodeNotFound), msg:
						an_error = traceback.format_exc()
						log.verbose(traceback.format_exception_only(type(an_error), an_error)[-1])
						log.error('Unable to Rename File: {}'.format(msg))
						continue
		else:
			raise InvalidFilename('Invalid Request, Neither File or Directory: %s' % pathname)

	def _processFile(self, pathname):

		_file_details = self.parser.getFileDetails(pathname)
		for key, value in _file_details.iteritems():
			log.info('Key: {}   Value: {}'.format(key, value))

		redirect_response = raw_input('Press any key to continue:  ')
		_series = Series(**_file_details)
		_series = self.getShowInfo(_series)

		for key, value in _series.__dict__.iteritems():
			log.info('Key: {}   Value: {}'.format(key, value))

		return

	def getShow(self):
		_series = Series(title=self.args.series_name)
		_series = self.getShowInfo(_series)

		for key, value in _series.__dict__.iteritems():
			log.info('Key: {}   Value: {}'.format(key, value))
		return

	def getShowInfo(self, _series):
		try:
			_series = _series.search(rtn=object)
			_series.tvdb_id = _series.tvdb_id
			_series.seasons = 'Load'
		except (KeyError, TypeError), msg:
			raise SeriesNotFound('SeriesNotFound: {}'.format(_series.title))
		except (SeriesNotFound, SeasonNotFound, EpisodeNotFound), msg:
			raise
		if _series.seasons is None:
			raise SeriesNotFound('SeriesNotFound: {}'.format(pathname))

		return _series


class _get_out_of_loop(Exception):
	pass

if __name__ == "__main__":


	logger.initialize()

	library = seriesInfo()

	Library.args = library.options.parser.parse_args(sys.argv[1:])
	log.debug("Parsed command line: {!s}".format(library.args))

	log_level = logging.getLevelName(library.args.loglevel.upper())

	if library.args.logfile == 'daddyvision.log':
		log_file = '{}.log'.format(__pgmname__)
	else:
		log_file = os.path.expanduser(library.args.logfile)

	# If an absolute path is not specified, use the default directory.
	if not os.path.isabs(log_file):
		log_file = os.path.join(logger.LogDir, __pgmname__, log_file)

	logger.start(log_file, log_level, timed=True)

	if len(library.args.library) == 0:
		msg = 'Missing Scan Starting Point (Input Directory), Using Default: {}'.format(library.settings.NewSeriesDir)
		log.info(msg)
		library.args.library = [library.settings.NewSeriesDir]

	if library.args.series_name is not None:
		library.getShow()
	else:
		for _lib_path in library.args.library:
			if os.path.exists(_lib_path):
				try:
					library.fileLookup(_lib_path)
				except:
					an_error = traceback.format_exc()
					log.error(traceback.format_exception_only(type(an_error), an_error)[-1])
			else:
				log.error('Skipping Lookup: Unable to find File/Directory: {}'.format(_lib_path))
