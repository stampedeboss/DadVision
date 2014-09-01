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
from common.exceptions import (RegxSelectionError, SeriesNotFound, EpisodeNotFound, DuplicateFilesFound,
							   FailedVideoCheck, InvalidFilename, UnexpectedErrorOccured, InvalidPath)
from common.chkvideo import chkVideoFile
from library.series.fileparser import FileParser
from library.series.seriesinfo import SeriesInfo
from exceptions import IOError
import datetime
import fnmatch
import logging
import os
import re
import sys
import time
import unicodedata
import sqlite3
import socket
import traceback
import shutil

import trakt
from trakt.users import User

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


def _del_dir(pathname, Tree=False, base_dir='/srv/DadVision/Series/New/'):
	log.trace("_del_dir: pathname:{!s}".format(pathname))

	if not os.path.isdir(pathname):
		raise InvalidPath('Invalid Path was requested for deletion: {}'.format(pathname))

	_curr_dir = pathname
	_base_dir = base_dir
	if not re.match('^{}.*'.format(_base_dir), pathname): return

	try:
		if Tree:
			shutil.rmtree(pathname)
		else:
			while _curr_dir != _base_dir:
				if len(os.listdir(_curr_dir)) != 0: return
				os.rmdir(pathname)
				log.verbose('Deleting Directory as Requested: {}'.format(pathname))
				_curr_dir = os.path.dirname(_curr_dir)
	except:
		log.warn('Delete Directory: Unable to Delete requested directory: %s' % (sys.exc_info()[1]))

	return



def _del_file(pathname, base_dir='/srv/DadVision/Series/New/'):
	log.trace("_del_file: pathname:{!s}".format(pathname))

	if not re.match('^{}.*'.format(base_dir), pathname): return
	if os.path.isdir(pathname):
		raise InvalidPath('Path was requested for deletion: {}'.format(pathname))

	try:
		log.verbose('Deleting File as Requested: {}'.format(pathname))
		os.remove(pathname)
	except:
		log.warn('Delete File: Unable to Delete requested file: %s' % (sys.exc_info()[1]))


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

		self.regex_repack = re.compile('^.*(repack|proper).*$', re.IGNORECASE)
		self.check_suffix = re.compile('^(?P<seriesname>.+?)[ \._\-](?P<year>[0-9][0-9][0-9][0-9]|US|us|Us)$', re.VERBOSE)
		self.regex_SeriesDir = re.compile('^{}.*$'.format(self.settings.SeriesDir), re.IGNORECASE)
#        self.check_year = re.compile('^(?P<seriesname>.+?)[ \._\-](?P<year>[0-9][0-9][0-9][0-9])$', re.VERBOSE)
#        self.check_US = re.compile('^(?P<seriesname>.+?)[ \._\-](?P<country>US)$', re.VERBOSE)

		self.hostname = socket.gethostname()
		self.xbmc_update_required = False

		self.dup_queue = []
		self.dup_better_queue = []

		return

	@useLibraryLogging
	def renameSeries(self, pathname):
		log.trace("rename method: pathname:{}".format(pathname))

		_last_series = None

		if os.path.isfile(pathname):
			log.debug("-----------------------------------------------")
			log.debug("Directory: %s" % os.path.split(pathname)[0])
			log.debug("Filename:  %s" % os.path.split(pathname)[1])
			self._rename_file(pathname)
		elif os.path.isdir(pathname):
			for _root, _dirs, _files in os.walk(os.path.abspath(pathname), followlinks=False):
				for _dir in _dirs[:]:
					if self._ignored(_dir):
						log.debug("Ignoring %r" % os.path.join(_root, _dir))
						_del_dir(os.path.join(_root, _dir), Tree=True)
						continue

				if _dirs == [] and _files == []:
					_del_dir(_root)
					continue
				elif _files == []:
					continue

				_files.sort()
				for _file_name in _files:
					_path_name = os.path.join(_root, _file_name)
					log.debug("-----------------------------------------------")
					log.debug("Filename: %s" % _path_name)
					ext = os.path.splitext(_path_name)[1][1:]
					if self._ignored(_path_name) or os.path.splitext(_path_name)[1][1:] not in self.settings.MediaExt:
						_del_file(_path_name)
						_del_dir(_root)
						continue
					try:
						self._rename_file(_path_name)
					except (IOError, InvalidFilename, RegxSelectionError, SeriesNotFound, EpisodeNotFound), msg:
						an_error = traceback.format_exc(1)
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

	def _rename_file(self, pathname, bypass_dup_check=False):

		if self.args.check_video:
			if chkVideoFile(pathname):
				log.error('File Failed Video Check: {}'.format(pathname))
				raise FailedVideoCheck('File Failed Video Check: {}'.format(pathname))
		try:
			_file_details = self.parser.getFileDetails(pathname)
			_file_details = self.seriesinfo.getShowInfo(_file_details)
		except (InvalidFilename, RegxSelectionError, SeriesNotFound, EpisodeNotFound), msg:
			_dir_details = self.parser.getFileDetails(os.path.join(os.path.dirname(pathname), 'E01.txt'))
			_file_details['SeriesName'] = _dir_details['SeriesName']
			_file_details = self.seriesinfo.getShowInfo(_file_details)

		_new_name, _file_details = self.getFileName(_file_details)
		_season_folder = os.path.dirname(_new_name)
		_series_folder = os.path.dirname(_season_folder)
		_file_exists = False

		if os.path.exists(_season_folder):
			if not bypass_dup_check:
				_file_exists = self._check_for_dups(_file_details, _new_name)
		else:
			os.makedirs(_season_folder)
			os.chmod(_season_folder, 0775)
			os.chown(_season_folder, 1000, 100)
			os.chmod(_series_folder, 0775)
			os.chown(_series_folder, 1000, 100)

		if _file_exists:
			log.info('SERIES:  {}'.format(_file_details['SeriesName']))
			log.info('Updated: SEASON: {}'.format(_file_details['SeasonNum']))
			log.info('Updated:   FILE: {}'.format(os.path.basename(_new_name)))
		else:
			os.rename(_file_details['FileName'], _new_name)
			os.chmod(_new_name, 0664)
			os.chown(_new_name, 1000, 100)
			log.info('SERIES:  {}'.format(_file_details['SeriesName']))
			log.info('Renamed: SEASON: {}'.format(_file_details['SeasonNum']))
			log.info('Renamed:   FILE: {}'.format(os.path.basename(_new_name)))
			log.info('Renamed: CURRENT {}'.format(os.path.basename(_file_details['FileName'])))

		self._update_date(_file_details, _new_name)
		if os.path.exists(_file_details['FileName']) and self.args.force_delete:
			_del_file(_file_details['FileName'])
		_del_dir(os.path.dirname(_file_details['FileName']))
		self.xbmc_update_required = True

		if self.hostname == 'grumpy':
			try:
				self.db = sqlite3.connect(self.settings.DBFile)
				self.cursor = self.db.cursor()
				self.cursor.execute('INSERT INTO Files(SeriesName, SeasonNum, EpisodeNum, Filename) \
						 VALUES ("{}", {}, {}, "{}")'.format(_file_details['SeriesName'],
															 _file_details['SeasonNum'],
															 _file_details['EpisodeNums'][0],
															 _file_details['FileName']
															 )
							   )
#                file_id = int(self.cursor.lastrowid)
				self.db.commit()
				self.db.close()
			except  sqlite3.IntegrityError, e:
				self.db.close()
			except sqlite3.Error, e:
				self.db.close()
				raise UnexpectedErrorOccured("File Information Insert: {} {}".format(e, _file_details))

		return

	def getFileName(self, _file_details):

		_file_details['EpisodeNumFmt'] = self._format_episode_numbers(_file_details)
		_file_details['EpisodeTitle'] = self._format_episode_name(_file_details['EpisodeData'],
																  join_with=self.settings.ConversionsPatterns['multiep_join_name_with'])
		_file_details['DateAired'] = self._get_date_aired(_file_details)
		_file_details['BaseDir'] = self.settings.SeriesDir

		_repack = self.regex_repack.search(_file_details['FileName'])
		if _repack:
			_new_name = self.settings.ConversionsPatterns['proper_fqn'] % _file_details
		else:
			_new_name = self.settings.ConversionsPatterns['std_fqn'] % _file_details

		return _new_name, _file_details

	def _check_for_dups(self, file_details, _new_name):

		_directory = os.path.dirname(_new_name)
		_title_new = os.path.splitext(os.path.basename(_new_name))[0]
		_ep_new = _title_new.split(None, 1)[0]

		for _file in [f for f in os.listdir(_directory)
		              if f.split(None, 1)[0] == _ep_new and os.path.join(_directory, f) != file_details['FileName']]:
			self.dup_queue.append(os.path.join(_directory, _file))

		if not self.dup_queue: return False

		_min_met = False
		if file_details['top_show']:
			_desired_quality = ['mkv']
			_acceptable_quality = ['mp4', 'avi']
		else:
			_desired_quality = ['mp4']
			_acceptable_quality = ['mkv', 'avi']

		if file_details['Ext'] in _desired_quality + _acceptable_quality:
			_min_met = True
		_last_file = self._clean_out_queue(_desired_quality, _acceptable_quality, _min_met)

		if _last_file is None: return False

		_selected_file = self._evaluate_keeper(file_details['FileName'],
		                                       _last_file,
		                                       file_details['top_show'] )

		if _selected_file == file_details['FileName']:
			_del_file(_last_file)
			return False
		else:
			if os.path.splitext(os.path.basename(_selected_file))[0] != _title_new:
				self._rename_file(_selected_file, bypass_dup_check=True)

		return True

	def _evaluate_keeper(self, file_1, file_2, top_show):

		_ext_1 = os.path.splitext(os.path.basename(file_1))[1][1:].lower()
		_ext_2 = os.path.splitext(os.path.basename(file_2))[1][1:].lower()

		if _ext_1 == _ext_2:
			if self.regex_repack.search(file_1):
				return file_1
			elif self.regex_repack.search(file_2):
				return file_2
		if _ext_1 == 'avi':
			if _ext_2 in ['avi']:
				if os.path.getsize(file_1) < os.path.getsize(file_2): return file_2
				else: return file_1
			if _ext_2 in ['mp4', 'mkv']: return file_2
			if _ext_2 in ['bup', 'divx', 'ifo', 'mpeg', 'mpg', 'img', 'iso', 'vob', '3gp', 'ts']:
				if os.path.getsize(file_1) > 100000000: return file_1
				else: return file_2
		elif _ext_1 == 'mp4':
			if top_show and _ext_2 in ['mkv']: return file_2
			if _ext_2 in ['mp4']:
				if os.path.getsize(file_1) < os.path.getsize(file_2): return file_2
			return file_1
		elif _ext_1 == 'mkv':
			if not top_show and _ext_2 in ['mp4']: return file_2
			if _ext_2 in ['mkv']:
				if os.path.getsize(file_1) < os.path.getsize(file_2): return file_2
			return file_1
		elif _ext_2 in ['mp4', 'mkv', 'avi']:
			return file_2
		else:
			return file_1

	def _clean_out_queue(self, _desired_quality, _acceptable_quality, _min_met):

		if len(self.dup_queue) == 1: return self.dup_queue.pop()

		_available = [x for x in self.dup_queue if os.path.splitext(x)[1][1:] in _desired_quality]
		if not _available:
			_available = [x for x in self.dup_queue if os.path.splitext(x)[1][1:] in _acceptable_quality]

		if _min_met:
			while len(self.dup_queue) > 0:
				_file_1 = self.dup_queue.pop()
				if _file_1 not in _available:
					_del_file(_file_1)
		elif _available:
			while len(self.dup_queue) > 0:
				_file_1 = self.dup_queue.pop()
				if _file_1 not in _available:
					_del_file(_file_1)
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
			                                       top_show )
			if _selected_file == _file_2:
				_del_file(_file_1)
				_file_1 = _file_2
			else:
				_del_file(_file_2)

		return _file_1

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

	def _ignored(self, name):
		""" Check for ignored pathnames.
		"""
		_skip = []
		_skip.append(any(fnmatch.fnmatch(name.lower(), pattern) for pattern in self.settings.IgnoreGlob))
		_skip.append(any(fnmatch.fnmatch(name.lower(), pattern) for pattern in self.settings.ExcludeList))
		return any(_skip)

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
