#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Author: AJ Reynolds
Date: 12-11-2010
Purpose:
Program to rename and update Modification Time to Air Date

"""
import datetime
import logging
import os
import re
import shutil
import socket
import sqlite3
import sys
import time
import traceback
import unicodedata
from exceptions import IOError

from common.exceptions import (SeriesNotFound, SeasonNotFound, EpisodeNotFound,
							   DuplicateFilesFound, InvalidFilename,
							   UnexpectedErrorOccured)
from dadvision import DadVision
from library import Library, ignored
from library.series import Series
from library.series.fileparser import FileParser

import logger
from MyTrakt.user import getList

__pgmname__ = 'rename'

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


class RenameSeries(Series):

	def __init__(self):
		log.trace('__init__ method: Started')

		super(RenameSeries, self).__init__()

		series_group = DadVision.cmdoptions.parser.add_argument_group("Series Overrides", description=None)
		series_group.add_argument("--sn", "--name", dest='series_name',
			type=str, default=None, nargs='?',
			help="Override Parsed Series Name with this value")

		self.parser = FileParser()
		self.topShows = getList(list='topshows', rtn=dict)

		self.regex_repack = re.compile('^.*(repack|proper).*$', re.IGNORECASE)
		self.check_suffix = re.compile('^(?P<seriesname>.+?)[ \._\-](?P<year>[0-9][0-9][0-9][0-9]|US|us|Us)$', re.VERBOSE)
		self.regex_SeriesDir = re.compile('^{}.*$'.format(DadVision.settings.SeriesDir), re.IGNORECASE)
#        self.check_year = re.compile('^(?P<seriesname>.+?)[ \._\-](?P<year>[0-9][0-9][0-9][0-9])$', re.VERBOSE)
#        self.check_US = re.compile('^(?P<seriesname>.+?)[ \._\-](?P<country>US)$', re.VERBOSE)

		self.hostname = socket.gethostname()
		self.xbmc_update_required = False

		self._last_series = None

		self.existing_series = os.listdir(DadVision.settings.SeriesDir)

		return

	@useLibraryLogging
	def renameSeries(self, pathname):
		log.trace("rename method: pathname:{}".format(pathname))

		if os.path.isfile(pathname):
			log.debug("-----------------------------------------------")
			log.debug("Directory: %s" % os.path.split(pathname)[0])
			log.debug("Filename:  %s" % os.path.split(pathname)[1])
			try:
				self.renameFile(os.path.realpath(pathname))
			except (SeriesNotFound, SeasonNotFound, EpisodeNotFound), msg:
				an_error = traceback.format_exc()
				log.verbose(traceback.format_exception_only(type(an_error), an_error)[-1])
				log.error('Unable to Rename File: {}'.format(msg))
		elif os.path.isdir(pathname):
			for _root, _dirs, _files in os.walk(os.path.abspath(pathname), followlinks=False):
				for _dir in _dirs[:]:
					if ignored(_dir):
						log.debug("Ignoring %r" % os.path.join(_root, _dir))
						self._del_dir(os.path.join(_root, _dir), Tree=True)
						continue

				if _dirs == [] and _files == []:
					self._del_dir(_root)
					continue
				elif _files == []:
					continue

				_files.sort()
				for _file_name in _files:
					_path_name = os.path.join(_root, _file_name)
					log.debug("-----------------------------------------------")
					log.debug("Filename: %s" % _path_name)
					ext = os.path.splitext(_path_name)[1][1:]
					if ignored(_file_name) or os.path.splitext(_file_name)[1][1:] not in DadVision.settings.MediaExt:
						self._del_file(_path_name)
						self._del_dir(_root)
						continue
					try:
						self.renameFile(_path_name)
					except (SeriesNotFound, SeasonNotFound, EpisodeNotFound), msg:
						an_error = traceback.format_exc()
						log.verbose(traceback.format_exception_only(type(an_error), an_error)[-1])
						log.error('Unable to Rename File: {}'.format(msg))
						continue
			if self.xbmc_update_required:
				try:
					cmd = 'xbmc-send --host=happy --action="XBMC.UpdateLibrary(video)"'
					os.system(cmd)
					log.trace("TV Show Rename Trigger Successful")
				except OSError, exc:
					log.error("TV Show Rename Trigger Failed: %s" % exc)
		else:
			raise InvalidFilename('Invalid Request, Neither File or Directory: %s' % pathname)

	def renameFile(self, pathname):

		log.info('-'*70)
		_series = None

		try:
			_series = self.getShowInfo(pathname)
			_series = self.getFileName(_series)
		except (SeasonNotFound, EpisodeNotFound):
			if _series and _series.title:
				log.error('SERIES: {}'.format(_series.title))
			raise

		log.info('SERIES: {}'.format(_series.fileDetails.seriesTitle))

		_season_folder = os.path.dirname(_series.fileDetails.newName)
		_series_folder = os.path.dirname(_season_folder)

		log.info('Renamed: SEASON: {}'.format(_series.fileDetails.seasonNum))
		if not os.path.exists(_season_folder):
			os.makedirs(_season_folder)
			os.chmod(_season_folder, 0775)
			os.chmod(_series_folder, 0775)
		else:
			_series = self._replace_existing(_series)

		if _series.fileDetails.fileName == _series.fileDetails.newName:
			log.info('Processed:   SEASON: {} FILE: {}'.format(_series.fileDetails.seasonNum,
																  os.path.basename(_series.fileDetails.newName)))
			self._update_date(_series)
			return
		else:
			os.rename(_series.fileDetails.fileName, _series.fileDetails.newName)
			os.chmod(_series.fileDetails.newName, 0664)
			log.info('Renamed:   FILE: {}'.format(os.path.basename(_series.fileDetails.newName)))
			log.info('Renamed:    New: {}'.format(os.path.basename(_series.fileDetails.fileName)))
			self._update_date(_series)
			self._del_dir(os.path.dirname(_series.fileDetails.fileName))
			self.xbmc_update_required = True

		if self.hostname == 'grumpy':
			try:
				self.db = sqlite3.connect(DadVision.settings.DBFile)
				self.cursor = self.db.cursor()
				self.cursor.execute('INSERT INTO Files(SeriesName, SeasonNum, EpisodeNum, Filename) \
						 VALUES ("{}", {}, {}, "{}")'.format(_series.fileDetails.seriesTitle,
															 _series.fileDetails.seasonNum,
															 _series.fileDetails.episodeNums[0],
															 _series.fileDetails.fileName
															 )
							   )
				self.db.commit()
				self.db.close()
			except  sqlite3.IntegrityError, e:
				self.db.close()
			except sqlite3.Error, e:
				self.db.close()
				raise UnexpectedErrorOccured("File Information Insert: {} {}".format(e, _series.__dict__))

		return

	def getShowInfo(self, pathname):
		try:
			_series = Series(**self.parser.getFileDetails(pathname))
			if self.args.series_name:
				_series.title = self.args.series_name
				_series.fileDetails.seriesTitle = self.args.series_name
			if self._last_series:
				if self._last_series.title == _series.title:
					_series.merge(self._last_series)
					return _series
			_series = _series.search(rtn=object)
			if self._last_series:
				if self._last_series.title == _series.title:
					_series.merge(self._last_series)
					return _series
			_series.tvdb_id = _series.tvdb_id
			_series.seasons = 'Load'
		except (KeyError, TypeError), msg:
			raise SeriesNotFound('SeriesNotFound: {}'.format(pathname))
		except (InvalidFilename, SeriesNotFound, SeasonNotFound, EpisodeNotFound), msg:
			raise
		if _series.seasons is None:
			raise SeriesNotFound('SeriesNotFound: {}'.format(pathname))

		self._last_series = _series
		return _series

	def getFileName(self, _series):

		join_with = DadVision.settings.ConversionsPatterns['multiep_join_name_with']
		_ep_title = []
		_episodes = _series.episode(_series.fileDetails.seasonNum,
								   _series.fileDetails.episodeNums)
		for _entry in _episodes:
			_ep_title.append(_entry.title)

		setattr(_series.fileDetails, 'baseDir', DadVision.settings.SeriesDir)

		setattr(_series.fileDetails, 'episodeNumFmt', self._format_episode_numbers(_series.fileDetails))

		setattr(_series.fileDetails, 'episodeTitle', self._format_episode_name(_ep_title, join_with=join_with))

		_repack = self.regex_repack.search(_series.fileDetails.fileName)
		if _repack:
			_new_name = DadVision.settings.ConversionsPatterns['proper_fqn'] % _series.fileDetails.__dict__
		else:
			_new_name = DadVision.settings.ConversionsPatterns['std_fqn'] % _series.fileDetails.__dict__

		_series.fileDetails.newName = _new_name

		return _series

	def _replace_existing(self, series):

		_directory = os.path.dirname(series.fileDetails.newName)
		_title_new = os.path.splitext(os.path.basename(series.fileDetails.newName))[0]
		_ep_new = _title_new.split(None, 1)[0]
		_dup_queue = []

		for _file in [f for f in os.listdir(_directory) if f.split(None, 1)[0] == _ep_new]:
			_dup_queue.append(os.path.join(_directory, _file))

		if not _dup_queue:
			return series

		# Remove Entry if In Place Rename is requested
		if len(_dup_queue) == 1:
			if _dup_queue[0] == series.fileDetails.fileName:
				return series


		_dup_queue.append(series.fileDetails.fileName)
		_selected_file = self._best_duplicate(series, _dup_queue)

		if _selected_file == series.fileDetails.fileName:
			return series
		else:
			if os.path.exists(series.fileDetails.fileName):
				log.info('Deleted:   FILE: {}'.format(os.path.basename(series.fileDetails.fileName)))
				self._del_file(series.fileDetails.fileName)
				self._del_dir(os.path.dirname(series.fileDetails.fileName))
			else:
				self._del_dir(os.path.dirname(series.fileDetails.fileName))

			series.fileDetails.fileName = _selected_file
			series.fileDetails.ext = os.path.splitext(os.path.basename(_selected_file))[1][1:].lower()
			series = self.getFileName(series)
			return series

	def _best_duplicate(self, series, queue):

		if len(queue) == 1: return queue.pop()

		if series.title in self.topShows:
			series.topShow = True
			_desired_quality = ['mkv']
			_acceptable_quality = ['mp4', 'avi']
		else:
			series.topShow = False
			_desired_quality = ['mp4']
			_acceptable_quality = ['mkv', 'avi']

		_available = [x for x in queue if os.path.splitext(x)[1][1:] in _desired_quality]
		if not _available:
			_available = [x for x in queue if os.path.splitext(x)[1][1:] in _acceptable_quality]

		if _available:
			while len(queue) > 0:
				_file_1 = queue.pop()
				if _file_1 not in _available:
					log.info('Deleted:   FILE: {}'.format(os.path.basename(_file_1)))
					self._del_file(_file_1)
		else:
			raise DuplicateFilesFound

		if not _available:
			return None

		if len(_available) == 1: return _available[0]

		_file_1 = _available.pop()
		while len(_available) > 0:
			_file_2 = _available.pop()
			_selected_file = self._evaluate_keeper(_file_1,
												   _file_2,
												   series.topShow )
			if _selected_file == _file_2:
				log.info('Deleted:   FILE: {}'.format(os.path.basename(_file_1)))
				self._del_file(_file_1)
				_file_1 = _file_2
			else:
				log.info('Deleted:   FILE: {}'.format(os.path.basename(_file_2)))
				self._del_file(_file_2)

		return _file_1

	def _evaluate_keeper(self, file_1, file_2, top_show):

		_ext_1 = os.path.splitext(os.path.basename(file_1))[1][1:].lower()
		_ext_2 = os.path.splitext(os.path.basename(file_2))[1][1:].lower()

		if _ext_1 == _ext_2:
			if self.regex_repack.search(file_2):
				return file_2
			elif self.regex_repack.search(file_1):
				return file_1
		if _ext_1 == 'avi':
			if _ext_2 in ['avi']:
				if os.path.getsize(file_2) >= os.path.getsize(file_1): return file_2
				else: return file_1
			if _ext_2 in ['mp4', 'mkv']: return file_2
			if _ext_2 in ['bup', 'divx', 'ifo', 'mpeg', 'mpg', 'img', 'iso', 'vob', '3gp', 'ts']:
				if os.path.getsize(file_1) > 100000000: return file_1
				else: return file_2
		elif _ext_1 == 'mp4':
			if top_show and _ext_2 in ['mkv']: return file_2
			if _ext_2 in ['mp4']:
				if os.path.getsize(file_2) >= os.path.getsize(file_1): return file_2
			return file_1
		elif _ext_1 == 'mkv':
			if not top_show and _ext_2 in ['mp4']: return file_2
			if _ext_2 in ['mkv']:
				if os.path.getsize(file_2) >= os.path.getsize(file_1): return file_2
			return file_1
		elif _ext_2 in ['mp4', 'mkv', 'avi']:
			return file_2
		else:
			return file_1

	def _update_date(self, series):

		_date_aired = series.episode(series.fileDetails.seasonNum, series.fileDetails.episodeNums)[0].first_aired
		cur_date = time.localtime(os.path.getmtime(series.fileDetails.newName))
		if _date_aired:
			_date_aired = datetime.datetime.combine(_date_aired, datetime.time())
			tt = _date_aired.timetuple()
			log.debug('Current File Date: %s  Air Date: %s' % (time.asctime(cur_date), time.asctime(tt)))
			tup_cur = [cur_date[0],
					   cur_date[1],
					   cur_date[2],
					   cur_date[3],
					   cur_date[4],
					   cur_date[5],
					   cur_date[6],
					   cur_date[7],
					   -1]
			tup = [tt[0], tt[1], tt[2], 20, 0, 0, tt[6], tt[7], tt[8]]
			if tup != tup_cur:
				time_epoc = time.mktime(tup)
				try:
					log.info("Updating First Aired: %s" % _date_aired)
					os.utime(series.fileDetails.newName, (time_epoc, time_epoc))
				except (OSError, IOError), exc:
					log.error("Skipping, Unable to update time: %s" % series.fileDetails.newName)
					log.error("Unexpected error: %s" % exc)
			else:
					log.info("First Aired Correct: %s" % _date_aired)
		else:
			log.warn('_update_date: Unable to update the Date Aired, Missing Information')

	def _format_episode_numbers(self, file_details):
		"""Format episode number(s) into string, using configured values
		"""
		if hasattr(file_details, "episodeNums"):
			if len(file_details.episodeNums) == 1:
				_episode_num_fmt = DadVision.settings.ConversionsPatterns['episode_single'] % file_details.episodeNums[0]
			else:
				_episode_num_fmt = DadVision.settings.ConversionsPatterns['episode_separator'].join(DadVision.settings.ConversionsPatterns['episode_single'] % x for x in file_details.episodeNums)
		else:
			raise EpisodeNotFound('EpisodeNotFound: {} - S {} E {}'.format(file_details.seriesTitle,
																		   file_details.seasonNum,
																		   file_details.episodeNums))
		return _episode_num_fmt

	def _format_episode_name(self, episodes, join_with):
		"""Takes a list of episode names, formats them into a string.
		If two names are supplied, such as "Pilot (1)" and "Pilot (2)", the
		returned string will be "Pilot (1-2)"

		If two different episode names are found, such as "The first", and
		"Something else" it will return "The first, Something else"
		"""

		if len(episodes) == 0:
			raise EpisodeNotFound('formatEpisodeName no Episode Titles Found: {!s}'.format(episodes))

		_names = []
		for _new_name in episodes:
			if type(_new_name) == unicode:
				_new_name = unicodedata.normalize('NFKD', _new_name).encode('ascii', 'ignore')
			_new_name = _new_name.replace("&amp;", "&").replace("/", "_")
			_names.append(_new_name)

		if len(_names) == 1:
			log.debug("formatEpisodeName: Only One Episode Name Found: %s" % (_names[0]))
			return _names[0]

		_found_names = []
		_numbers = []

		for _cname in _names:
			_number = re.match("(.*) \(([0-9]+)\)$", _cname)
			if _number:
				_ep_name, _ep_no = _number.group(1), _number.group(2)
				if len(_found_names) > 0 and _ep_name not in _found_names:
					log.debug("formatEpisodeName: Episode Name: %s" % (join_with.join(_names)))
					return join_with.join(_names)
				_found_names.append(_ep_name)
				_numbers.append(int(_ep_no))
			else:
				# An episode didn't match
				log.debug("formatEpisodeName: Episode Name: %s" % (join_with.join(_names)))
				return join_with.join(_names)

		_names = []
		_start, _end = min(_numbers), max(_numbers)
		_names.append("%s (%d-%d)" % (_found_names[0], _start, _end))
		log.debug("Episode Name: %s" % (join_with.join(_names)))
		return join_with.join(_names)

	def _del_dir(self, pathname, Tree=False):
		log.trace("_del_dir: pathname:{!s}".format(pathname))

		if not os.path.isdir(pathname):
			log.error('Invalid Path was requested for deletion: {}'.format(pathname))
			return

		_curr_dir = pathname
		_base_dir = DadVision.settings.NewSeriesDir
		if not re.match('^{}.*'.format(_base_dir), pathname): return

		try:
			if Tree:
				shutil.rmtree(pathname)
			else:
				while _curr_dir != _base_dir:
					if len(os.listdir(_curr_dir)) != 0: return
					os.rmdir(_curr_dir)
					log.verbose('Deleting Directory as Requested: {}'.format(pathname))
					_curr_dir = os.path.dirname(_curr_dir)
		except:
			an_error = traceback.format_exc()
			log.error(traceback.format_exception_only(type(an_error), an_error)[-1])
			log.warn('Delete Directory: Unable to Delete requested directory: %s' % (sys.exc_info()[1]))

		return


	def _del_file(self, pathname):
		log.trace("_del_file: pathname:{!s}".format(pathname))

		_check_download = pathname[:len(os.path.dirname(DadVision.settings.DownloadDir))]
		_check_dadvision = pathname[:len(os.path.dirname(DadVision.settings.SeriesDir))]

		try:
			if os.path.isdir(pathname):
				log.error('InvalidPath was requested for deletion: {}'.format(pathname))
				return
			if _check_dadvision == os.path.dirname(DadVision.settings.SeriesDir):
				raise _get_out_of_loop
			if _check_download == os.path.dirname(DadVision.settings.DownloadDir):
				if not self.args.force_delete:
					raise _get_out_of_loop
			return
		except _get_out_of_loop:
			pass

		try:
			log.verbose('Deleting File as Requested: {}'.format(pathname))
			os.remove(pathname)
		except:
			log.warn('Delete File: Unable to Delete requested file: %s' % (sys.exc_info()[1]))


class _get_out_of_loop(Exception):
	pass

if __name__ == "__main__":


	logger.initialize()

	library = RenameSeries()

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

	for _lib_path in library.args.library:
		if os.path.exists(_lib_path):
			try:
				library.renameSeries(_lib_path)
			except:
				an_error = traceback.format_exc()
				log.error(traceback.format_exception_only(type(an_error), an_error)[-1])
		else:
			log.error('Skipping Rename: Unable to find File/Directory: {}'.format(_lib_path))
