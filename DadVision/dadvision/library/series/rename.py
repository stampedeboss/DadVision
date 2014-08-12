#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Author: AJ Reynolds
Date: 12-11-2010
Purpose:
Program to rename and update Modification Time to Air Date

"""
from library import Library
from common import logger
from common.exceptions import (DataRetrievalError, EpisodeNotFound,
	SeriesNotFound, DuplicateFilesFound, InvalidFilename, RegxSelectionError,
	ConfigValueError, UnexpectedErrorOccured, DuplicateRecord)
from common.chkvideo import chkVideoFile
from library.series.fileparser import FileParser
from library.series.seriesinfo import SeriesInfo
from common.cmdoptions import CmdOptions
import datetime
import filecmp
import fnmatch
import logging
import os
import re
import sys
import time
import unicodedata
import sqlite3
import socket

__pgmname__ = 'rename'
__version__ = '$Rev$'

__author__ = "@author: AJ Reynolds"
__email__ = "@contact: stampedeboss@gmail.com"
__copyright__ = "@copyright: Copyright 2011, AJ Reynolds"
__license__ = "@license: GPL"

__maintainer__ = "@organization: AJ Reynolds"
__status__ = "@status: Development"
__credits__ = []

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

class RenameSeries(Library):

	def __init__(self):
		log.trace('__init__ method: Started')

		super(RenameSeries, self).__init__()

		rename_group = self.options.parser.add_argument_group("Series Rename Options", description=None)
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

		self.seriesinfo = SeriesInfo()
		self.parser = FileParser()

		self.xbmc_update_required = False

		self.regex_repack = re.compile('^.*(repack|proper).*$', re.IGNORECASE)
		self.check_suffix = re.compile('^(?P<seriesname>.+?)[ \._\-](?P<year>[0-9][0-9][0-9][0-9]|US|us|Us)$', re.VERBOSE)
		self.regex_SeriesDir = re.compile('^{}.*$'.format(self.settings.SeriesDir), re.IGNORECASE)
#        self.check_year = re.compile('^(?P<seriesname>.+?)[ \._\-](?P<year>[0-9][0-9][0-9][0-9])$', re.VERBOSE)
#        self.check_US = re.compile('^(?P<seriesname>.+?)[ \._\-](?P<country>US)$', re.VERBOSE)

		self.hostname = socket.gethostname()

		return

	@useLibraryLogging
	def renameSeries(self, pathname):
		log.trace("rename method: pathname:{}".format(pathname))

		_last_series = None

		if os.path.isfile(pathname):
			log.debug("-----------------------------------------------")
			log.debug("Directory: %s" % os.path.split(pathname)[0])
			log.debug("Filename:  %s" % os.path.split(pathname)[1])
			try:
				_file_details = self.parser.getFileDetails(pathname)
				if self.args.check_video:
					if chkVideoFile(pathname):
						log.error('File Failed Video Check: {}'.format(pathname))
						return
				if _file_details : _file_details = self.seriesinfo.getShowInfo(_file_details)
				if _file_details : self._rename_file(_file_details)
				self.xbmc_update_required = False
			except (InvalidFilename, DuplicateFilesFound, RegxSelectionError, EpisodeNotFound, SeriesNotFound), msg:
				log.error('Unable to Rename File: {}'.format(msg))
				return
			if self.xbmc_update_required:
				try:
					cmd = 'xbmc-send --host=happy --action="XBMC.UpdateLibrary(video)"'
					os.system(cmd)
					log.trace("TV Show Rename Trigger Successful")
				except OSError, exc:
					log.error("TV Show Rename Trigger Failed: %s" % exc)
		elif os.path.isdir(pathname):
			for _root, _dirs, _files in os.walk(os.path.abspath(pathname), followlinks=False):
				for _dir in _dirs[:]:
					if self._ignored(_dir):
						log.debug("Ignoring %r" % os.path.join(_root, _dir))
						_dirs.remove(_dir)

				if _dirs == [] and _files == []:
					self._del_dir(os.path.join(_root, 'dummy'))
					continue
				elif _files == []:
					continue

				_files.sort()

				for _file_name in _files:
					_path_name = os.path.join(_root, _file_name)
					log.debug("-----------------------------------------------")
					log.debug("Filename: %s" % _path_name)
					if self._ignored(pathname) and not self.regex_SeriesDir.match(_file_name):
						try:
							os.remove(_path_name)
							self._del_dir(_path_name)
							continue
						except:
							log.info('Unable to delete: %s - %s' % (_path_name, sys.exc_info()[1]))
						continue
					try:
						_file_details = self.parser.getFileDetails(_path_name)
						if _file_details:
							if chkVideoFile(_path_name):
								log.error('File Failed Video Check: {}'.format(_path_name))
								continue
							_file_details = self.seriesinfo.getShowInfo(_file_details)
							self._rename_file(_file_details)
					except (InvalidFilename, DuplicateFilesFound, RegxSelectionError, DataRetrievalError, EpisodeNotFound, SeriesNotFound), msg:
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

	def _rename_file(self, file_details):

		file_details['EpisodeNumFmt'] = self._format_episode_numbers(file_details)
		file_details['EpisodeTitle'] = self._format_episode_name(file_details['EpisodeData'], join_with=self.settings.ConversionsPatterns['multiep_join_name_with'])
		file_details['DateAired'] = self._get_date_aired(file_details)

		file_details['BaseDir'] = self.settings.SeriesDir

		_new_name = self.settings.ConversionsPatterns['std_fqn'] % file_details
		_repack = self.regex_repack.search(file_details['FileName'])
		if _repack:
			try:
				os.remove(_new_name)
			except:
				log.info('Unable to delete: %s' % _new_name)
			_new_name = self.settings.ConversionsPatterns['proper_fqn'] % file_details
		else:
#            if os.path.exists(_new_name) and filecmp.cmp(_new_name, file_details['FileName']):
			if os.path.exists(_new_name):
				if os.path.split(_new_name)[0] == os.path.split(file_details['FileName'])[0]:
					log.info('Exists, Updating Timestamp')
					log.info('   Series: {}'.format(file_details['SeriesName']))
					log.info('   Season: {}  Episode: {}'.format(file_details['SeasonNum'], file_details['EpisodeNumFmt']))
					self._update_date(file_details, _new_name)
					return
				else:
					if self.args.force_delete:
						log.info("Deleting %r, already at destination!" % (os.path.split(file_details['FileName'])[1],))
						os.remove(file_details['FileName'])
						self._del_dir(file_details['FileName'])
						return
					elif not self.args.force_rename:
#                        log.info("Skipping Rename %r, already at destination!" % (os.path.split(file_details['FileName'])[1],))
						log.info("Skipping Rename %r, already at destination!" % _new_name)
						return

		try:
			_season_folder = os.path.split(_new_name)[0]
			_series_folder = os.path.split(_season_folder)[0]
			if not os.path.exists(_season_folder):
				os.makedirs(_season_folder)
				os.chmod(_season_folder, 0775)
#                os.chown(_season_folder, 1000, 100)
				os.chmod(_series_folder, 0775)
#                os.chown(_series_folder, 1000, 100)
			os.rename(file_details['FileName'], _new_name)
			os.chmod(_new_name, 0664)
#            os.chown(_new_name, 1000, 100)

			if self.hostname == 'grumpy':
				try:
					self.db = sqlite3.connect(self.settings.DBFile)
					self.cursor = self.db.cursor()
					self.cursor.execute('INSERT INTO Files(SeriesName, SeasonNum, EpisodeNum, Filename) \
							 VALUES ("{}", {}, {}, "{}")'.format(file_details['SeriesName'],
																 file_details['SeasonNum'],
																 file_details['EpisodeNums'][0],
																 file_details['FileName']
																 )
								   )
	#                file_id = int(self.cursor.lastrowid)
					self.db.commit()
					self.db.close()
				except  sqlite3.IntegrityError, e:
					self.db.close()
				except sqlite3.Error, e:
					self.db.close()
					raise UnexpectedErrorOccured("File Information Insert: {} {}".format(e, file_details))

			log.info('Renamed: CURRENT {}'.format(os.path.basename(file_details['FileName'])))
			log.info('Renamed: SERIES: {}'.format(file_details['SeriesName']))
			log.info('Renamed: SEASON: {}'.format(file_details['SeasonNum']))
			log.info('Renamed:   FILE: {}'.format(os.path.basename(_new_name)))
			self.xbmc_update_required = True
		except OSError, exc:
			log.error("Skipping, Unable to Rename File: %s" % file_details['FileName'])
			log.error("Unexpected error: %s" % exc)

		self._del_dir(file_details['FileName'])

		self._update_date(file_details, _new_name)

	def _update_date(self, file_details, new_name):
		if 'DateAired' not in file_details:
			log.warn('_update_date: Unable to update the Date Aired, Missing Information')
			return

		_date_aired = file_details['DateAired']
		cur_date = time.localtime(os.path.getmtime(new_name))
		if _date_aired:
			_date_aired = datetime.datetime.combine(_date_aired, datetime.time())
			tt = _date_aired.timetuple()
			log.debug('Current File Date: %s  Air Date: %s' % (time.asctime(cur_date), time.asctime(tt)))
			tup_cur = [cur_date[0], cur_date[1], cur_date[2], cur_date[3], cur_date[4], cur_date[5], cur_date[6], cur_date[7], -1]
			tup = [tt[0], tt[1], tt[2], 20, 0, 0, tt[6], tt[7], tt[8]]
			if tup != tup_cur:
				time_epoc = time.mktime(tup)
				try:
					log.info("Updating First Aired: %s" % _date_aired)
					os.utime(new_name, (time_epoc, time_epoc))
				except (OSError, IOError), exc:
					log.error("Skipping, Unable to update time: %s" % new_name)
					log.error("Unexpected error: %s" % exc)

	def _del_dir(self, pathname):
		if not re.match('^{}'.format(self.settings.NewSeriesDir), pathname):
			return

		_base_dir = self.settings.NewSeriesDir
		_curr_dir = os.path.split(pathname)[0]
		while _curr_dir != _base_dir:
			if len(os.listdir(_curr_dir)) == 0:
				try:
					os.rmdir(_curr_dir)
					_curr_dir = os.path.split(_curr_dir)[0]
					continue
				except:
					log.warn('_del_dir: Unable to Delete: %s' % (sys.exc_info()[1]))
					return
			else:
				return
		return

	def _ignored(self, name):
		""" Check for ignored pathnames.
		"""
		return any(fnmatch.fnmatch(name.lower(), pattern) for pattern in self.settings.ExcludeList)

	def _get_date_aired(self, file_details):
		if 'DateAired' in file_details:
			return file_details['DateAired']

		_dates = []
		for _episode in file_details['EpisodeData']:
			if 'DateAired' in _episode:
				_dates.append(_episode['DateAired'])

		if len(_dates) > 0:
			return _dates[0]
		else:
			return None

	def _format_episode_numbers(self, file_details):
		"""Format episode number(s) into string, using configured values
		"""
		if "EpisodeNums" in file_details:
			if len(file_details['EpisodeNums']) == 1:
				_episode_num_fmt = self.settings.ConversionsPatterns['episode_single'] % file_details['EpisodeNums'][0]
			else:
				_episode_num_fmt = self.settings.ConversionsPatterns['episode_separator'].join(self.settings.ConversionsPatterns['episode_single'] % x for x in file_details['EpisodeNums'])
		else:
			pass
		return _episode_num_fmt

	def _format_episode_name(self, EpisodeData, join_with):
		"""Takes a list of episode names, formats them into a string.
		If two names are supplied, such as "Pilot (1)" and "Pilot (2)", the
		returned string will be "Pilot (1-2)"

		If two different episode names are found, such as "The first", and
		"Something else" it will return "The first, Something else"
		"""

		_names = []
		for _episode_entry in EpisodeData:
			_new_name = _episode_entry['EpisodeTitle']
			if type(_new_name) == unicode:
				_new_name = unicodedata.normalize('NFKD', _new_name).encode('ascii', 'ignore')
			_new_name = _new_name.replace("&amp;", "&").replace("/", "_")
			_names.append(_new_name)

		if len(_names) == 0:
			raise EpisodeNotFound('formatEpisodeName no Episode Titles Found: {!s}'.format(EpisodeData))

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

class _get_out_of_loop(Exception):
	pass

if __name__ == "__main__":

	from library import Library
	from logging import INFO, WARNING, ERROR, DEBUG

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
			library.renameSeries(_lib_path)
		else:
			log.error('Skipping Rename: Unable to find File/Directory: {}'.format(_lib_path))
