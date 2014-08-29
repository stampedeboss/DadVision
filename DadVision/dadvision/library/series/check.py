#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Purpose:
   Program to perform various tasks (check for missing episodes, locate duplication files, etc).
   Assist with maintaining a Library of Series and Episode files.

"""
from __future__ import division
from datetime import datetime, date, timedelta
from library.series.seriesobj import TVSeries, TVSeason, TVEpisode
import difflib
import fnmatch
import logging
import os
import re
import sys
import traceback

from common.exceptions import (SeriesNotFound, EpisodeNotFound)
from common import logger
from library import Library
from library.series.seriesinfo import SeriesInfo
from library.series.fileparser import FileParser
from library.series.rename import RenameSeries
from fuzzywuzzy import fuzz

import trakt
from trakt.users import User, UserList
from trakt.tv import TVShow


__pgmname__ = 'check'
__version__ = '$Rev$'

__author__ = "@author: AJ Reynolds"
__email__ = "@contact: stampedeboss@gmail.com"
__copyright__ = "@copyright: Copyright 2011, AJ Reynolds"
__license__ = "@license: GPL"

__maintainer__ = "@organization: AJ Reynolds"
__status__ = "@status: Development"
__credits__ = []

log = logging.getLogger(__pgmname__)


def _matching(value1, value2, factor=85):
	log.trace("=================================================")
	log.trace("_matching: Compare: {} --> {}".format(value1, value2))

	fuzzy = []
	fuzzy.append(fuzz.ratio(value1, value2))
	fuzzy.append(fuzz.partial_ratio(value1, value2))
	fuzzy.append(fuzz.token_set_ratio(value1, value2))
	fuzzy.append(fuzz.token_sort_ratio(value1, value2))

	log.verbose("=" * 50)
	log.verbose('Fuzzy Compare: {} - {}'.format(value1, value2))
	log.verbose("-" * 50)
	log.verbose('{}: Simple Ratio'.format(fuzzy[0]))
	log.verbose('{}: Partial Ratio'.format(fuzzy[1]))
	log.verbose('{}: Token Set Ratio'.format(fuzzy[2]))
	log.verbose('{}: Token Sort Ratio'.format(fuzzy[3]))
	log.verbose(any([fr > factor for fr in fuzzy]))

	return any([fr > factor for fr in fuzzy])


class GetOutOfLoop(Exception):
	pass


def _ignored(name):
	""" Check for ignored pathnames.
	"""
	rc = []
	if name == 'New': rc.append(True)
	rc.append(any(fnmatch.fnmatch(name.lower(), pattern) for pattern in library.settings.ExcludeList))
	rc.append(any(fnmatch.fnmatch(name.lower(), pattern) for pattern in library.settings.IgnoreGlob))
	return any(rc)


class CheckSeries(Library):

	def __init__(self):
		log.trace('__init__ method: Started')

		super(CheckSeries, self).__init__()

		check_group1= self.options.parser.add_argument_group("Series Unique Options", description=None)
		check_group1.add_argument("-x", "--no-excludes", dest="no_excludes",
			action="store_true", default=False,
			help="Ignore Exclude File")
		check_group1.add_argument("-s", "--include-specials", dest="specials",
			action="store_true", default=False,
			help="Include specials in checks)")
		check_group1.add_argument("-r", "--remove", dest="remove",
			action="store_true", default=False,
			help="Remove duplicate files that are found in the duplicate check")
		check_group1.add_argument("-d", "--days", dest="age_limit",
			action="store", type=int, default=120,
			help="Limit check back x number of days, default 30")
		check_group1.add_argument("-f", "--no-age-limit-requested", dest="age_limit",
			action="store_const", const=99999,
			help="Full Check")
		check_group1.add_argument("--dco", '--dup-check-only', dest="dup_check_only",
			action="store_true", default=False,
			help="Duplicate File Check Only")

		trakt.api_key = self.settings.TraktAPIKey
		trakt.authenticate(self.settings.TraktUserID, self.settings.TraktPassWord)
		self.trakt_user = User(self.settings.TraktUserID)
		self.parser = FileParser()
		self.seriesinfo = SeriesInfo()
		self.rename = RenameSeries()

		self.regex_season = re.compile('^(?:Season).(?P<SeasonNum>[0-9]+)$', re.I)
		self.regex_episode = re.compile('^(?:E)(?P<EpisodeNum>[0-9][0-9])[\-]?(?:E)?(?P<EpisodeNum2>[0-9][0-9])?(?P<EpisodeName>.+)?\.(?P<Ext>.+?)$', re.I)
		self.regex_repack = re.compile('^.*(repack|proper).*$', re.IGNORECASE)

		return

	def check(self, pathname):
		log.trace('check: Pathname Requested: {}'.format(pathname))

		pathname = os.path.abspath(pathname)
		_series_details = []

		self._trakt_top_shows = self.trakt_user.get_list('topshows')
		self._trakt_top_shows_names = {_item.title: _item for _item in self._trakt_top_shows.items}

		log.info("==== Begin Scan: {} ====".format(pathname))
		_series = self.getSeriesData(pathname)

		if self.args.dup_check_only:
			sys.exit(0)


		for _show_name, _file_data in sorted(_series.iteritems()):
			DadVision = _file_data['DadVision']
			try:
				_tv_series = self.seriesinfo.getShowInfo({'SeriesName': _show_name}, sources=['tvdb'])['TVSeries']
			except (SeriesNotFound, EpisodeNotFound):
				an_error = traceback.format_exc()
				log.verbose(traceback.format_exception_only(type(an_error), an_error)[-1])
				log.warn("Skipping series: %s" % (_show_name))

			date_boundry = date.today() - timedelta(days=self.args.age_limit)
			missing = {}
			for _season in sorted(_tv_series.seasons.itervalues()):
				if not self.args.specials and _season.season == 0:
					continue
				for _episode in _season.episodes.itervalues():
					if _episode.first_aired:
						if _episode.first_aired < date_boundry or _episode.first_aired >= datetime.today().date():
							continue
						try:
							if _episode.episode not in DadVision[_season.season]:
								raise KeyError
						except KeyError:
							if _season.season in missing:
								missing[int(_season.season)].append(_episode.episode)
							else:
								missing[int(_season.season)] = [_episode.episode]

			_total_missing = 0
			for _missing_season, _missing_episodes in missing.iteritems():
				_total_missing += len(_missing_episodes)
			message = "Missing %3i episode(s) - SERIES: %-35.35s" % (_total_missing, _show_name)
			if _total_missing > 0:
				log.warning(message)
			else:
				log.info(message)

			season_message = "         Season: {}  Episode: ALL"
			message = "         Season: {}  Episode: {}  Aired: {} Title: {}"
			for key, val in sorted(missing.iteritems()):
				_season_number = u'<Season {0:02}>'.format(key)
				_episodes = _tv_series.seasons[_season_number].episodes
				_season_num_msg = "S%2.2d" % key
				if len(val) == len(_episodes):
					log.error(season_message.format(_season_num_msg))
				else:
					for _ep_no in sorted(val):
						_ep_no_fmt = "E%2.2d" % _ep_no
						_episode = _episodes[_ep_no_fmt]
						if _episode.first_aired:
							_first_aired = _episode.first_aired
						else:
							_first_aired = "Unknown"
						log.error(message.format(_episode.episode,
												 _ep_no,
												 _first_aired,
												 _episode.title.encode('utf8', 'replace').replace("&amp;", "&")))

		sys.exit()

	def getSeriesData(self, pathname):

		_prefix = os.path.commonprefix([pathname, self.settings.SeriesDir])
		if not _prefix == self.settings.SeriesDir:
			raise
		elif not os.path.abspath(pathname) == self.settings.SeriesDir:
			return [os.path.basename(pathname)]

		_series = {}
		_series_dir = os.listdir(os.path.abspath(pathname))
		_series_dir.sort()
		_series_temp = sorted(_series_dir)
		for _show in _series_temp:
			if _ignored(_show):
				_series_dir.remove(_show)
				log.trace('Removing Series: %s' % _show)
		_shows_processed = 0
		for _show in _series_dir:
			_shows_processed += 1
			_series[_show] = {}

			#Check for Duplicate Series Directories
			_matches = difflib.get_close_matches(_show, _series_dir, 2, cutoff=0.9)
			if len(_matches) > 1:
				log.warning('Possible Duplicate Directories: {} - {}'.format(_matches[0], _matches[1]))

			DadVision = {}
			_dup_list = {}
			#Load Episode Data
			_seasons = os.listdir(os.path.join(self.settings.SeriesDir,_show))
			for _season in _seasons:
				_parsed_details = self.regex_season.match(_season)
				if not _parsed_details: continue

				_season_number = int(_parsed_details.group('SeasonNum'))
				DadVision[_season_number] = []
				_dup_list[_season_number] = {}

				_episodes = os.listdir(os.path.join(self.settings.SeriesDir,_show, _season))
				for _episode in _episodes:
					if not os.path.splitext(_episode)[1][1:] in self.settings.MediaExt:
						continue

					_parsed_details = self.regex_episode.match(_episode)
					if not _parsed_details: continue

					_epno = [int(_parsed_details.group('EpisodeNum'))]
					if _parsed_details.group('EpisodeNum2') in _dup_list[_season_number]:
						_epno_2 = [int(_parsed_details.group('EpisodeNum2'))]
					else:
						_epno_2 = []

					_pathname = os.path.join(pathname, _show, _season, _episode)
					_dup_entry = {'series': _show,
								  'season': _season_number,
								  'epno': _parsed_details.group('EpisodeNum'),
								  'title': _parsed_details.group('EpisodeName'),
								  'ext': _parsed_details.group('Ext'),
								  'file': _pathname}
					if _parsed_details.group('EpisodeNum2'):
						_dup_entry['epno_2'] = _parsed_details.group('EpisodeNum2')

					for _ep_no in _epno:
						if _ep_no in _dup_list[_season_number]:
							_dup_list[_season_number][_ep_no].append(_dup_entry)
						else:
							_dup_list[_season_number][_ep_no] = [_dup_entry]

					for _ep_no in _epno_2:
						if _ep_no in _dup_list[_season_number]:
							_dup_list[_season_number][_ep_no].append(_dup_entry)
						elif _epno_2:
							_dup_list[_season_number][_ep_no] = [_dup_entry]

					if _epno not in DadVision[_season_number]:
						DadVision[_season_number].append(int(_parsed_details.group('EpisodeNum')))

					if _parsed_details.group('EpisodeNum2'):
						DadVision[_season_number].append(int(_parsed_details.group('EpisodeNum2')))

			_series[_show]['DadVision'] = DadVision
			# quotient, remainder = divmod(_shows_processed, 100)
			# if remainder == 0:
			# 	log.info('Ready for Check: {}'.format(_shows_processed))
			self.processDups(_dup_list)
		return _series

	def processDups(self, candidates):

		dups = []
		for _season, _episodes in candidates.iteritems():
			for _epno, _episode in _episodes.iteritems():
				if len(_episode) > 1:
					for _file in _episode:
						log.verbose('DUPLICATE: {series}: Season: {season}  {file} '.format(**_file))
					dups.append(_episode)
		if dups: self._handle_dups(dups)

	def _handle_dups(self, dups):

		fmt_dups = '{0: <8.8s} {1: <8.8s} SERIES: {2: <25.25s} SEA:{3:2d} 1: {4: <35.35s} 2: {5: <35.35s}'

		_prefered_fmts = ['mp4', 'mkv']

		for _episode in dups:
			file_1 = _episode[0]
			for i in range(1, len(_episode)):
				file_2 = _episode[i]

				if file_1['series'] in self._trakt_top_shows_names:
					_TOP_SHOW = True
				else:
					_TOP_SHOW = False

				if not self.args.remove:
					log.info(fmt_dups.format('Duplicate', 'Found',
										file_1['series'], file_1['season'],
										os.path.basename(file_1['file']),
						                os.path.basename(file_2['file'])))
					continue
				if file_1['ext'] == file_2['ext']:
					if self.regex_repack.search(file_1['file']):
						self. _delete_dup(file_1, file_2)
					elif self.regex_repack.search(file_2['file']):
						self. _delete_dup(file_2, file_1)
					else:
						try:
							_file_parsed = self.parser.getFileDetails(file_1['file'])
							_series_details = self.seriesinfo.getShowInfo(_file_parsed, sources=['tvdb'])
							_new_name, _file_details = self.rename.getFileName(_series_details)
							if _new_name == file_1['file']:
								self. _delete_dup(file_1, file_2)
							else:
								_file_parsed = self.parser.getFileDetails(file_2['file'])
								_series_details = self.seriesinfo.getShowInfo(_file_parsed)
								_new_name, _file_details = self.rename.getFileName(_series_details)
								if _new_name == file_2['file']:
									self. _delete_dup(file_2, file_1)
								elif os.path.getsize(file_1['file']) > os.path.getsize(file_2['file']):
									self.rename._rename_file(file_1['file'])
								else:
									self.rename._rename_file(file_2['file'])
						except SeriesNotFound, EpisodeNotFound:
							continue
						except KeyboardInterrupt:
							sys.exit(8)
						except:
							an_error = traceback.format_exc()
							log.error(traceback.format_exception_only(type(an_error), an_error)[-1])
				elif file_1['ext'] == 'avi' and file_2['ext'] in _prefered_fmts:
					self. _delete_dup(file_2, file_1)
				elif file_2['ext'] == 'avi' and file_1['ext'] in _prefered_fmts:
					self. _delete_dup(file_1, file_2)
				elif file_1['ext'] == 'mkv' and file_2['ext'] == 'mp4':
					if _TOP_SHOW:
						self. _delete_dup(file_1, file_2)
					else:
						self. _delete_dup(file_2, file_1)
				elif file_1['ext'] == 'mp4' and file_2['ext'] == 'mkv':
					if _TOP_SHOW:
						self. _delete_dup(file_2, file_1)
					else:
						self. _delete_dup(file_1, file_2)

				if os.path.exists(file_2['file']):
					file_1 = _episode[i]

	def _delete_dup(self, keep, delete, choose=False):
		fmt_dups = '\n{0: <8.8s} {1: <8.8s} SERIES: {2: <25.25s} SEASON:{3:2d} KEEPING: {4: <35.35s} REMOVING: {5: <35.35s}\n'
		dup_choose = '\n{0: <8.8s} {1: <8.8s} SERIES: {2: <25.25s} SEASON:{3:2d} FILE TO DELETE:  1: {4: <35.35s} 2: {5: <35.35s}\n'
		root_logger = logging.getLogger()

		root_logger.disabled = True
		self._list_dir(os.path.dirname(keep['file']))

		_delete = ''
		if self.args.remove:
			if choose:
				while _delete not in ['1', '2', "n"]:
					_delete = raw_input(dup_choose.format('Delete',
										'(1/2/n)',
										keep['series'], delete['season'],
										os.path.basename(keep['file']),
										os.path.basename(delete['file'])))
				if _delete == '2':
					try:
						self.rename._rename_file(delete['file'])
#						os.remove(delete['file'])
					except OSError:
						an_error = traceback.format_exc()
						log.verbose(traceback.format_exception_only(type(an_error), an_error)[-1])
						_delete = 'e'
				elif _delete == '1':
					try:
						self.rename._rename_file(keep['file'])
#						os.remove(keep['file'])
					except OSError:
						an_error = traceback.format_exc()
						log.verbose(traceback.format_exception_only(type(an_error), an_error)[-1])
						_delete = 'e'
			else:
				while _delete.lower() not in ['y', 'n']:
					_delete = raw_input(fmt_dups.format('Delete', 'Y/N',
														keep['series'], delete['season'],
														os.path.basename(keep['file']),
														os.path.basename(delete['file'])))
				if _delete.lower() == 'y':
					try:
						os.remove(delete['file'])
					except OSError:
						an_error = traceback.format_exc()
						log.verbose(traceback.format_exception_only(type(an_error), an_error)[-1])
						_delete = 'e'

		root_logger.disabled = False
		if _delete.lower() in ['y', '2']:
			log.info(fmt_dups.format('Delete', 'Complete',
									 keep['series'], delete['season'],
									 os.path.basename(keep['file']),
									 os.path.basename(delete['file'])))
		elif _delete.lower() in ['1']:
			log.info(fmt_dups.format('Delete', 'Complete',
									 delete['series'], keep['season'],
									 os.path.basename(delete['file']),
									 os.path.basename(keep['file'])))
		elif _delete.lower() == 'e':
			log.info(fmt_dups.format('Delete', 'ERROR',
									 keep['series'], delete['season'],
									 os.path.basename(keep['file']),
									 os.path.basename(delete['file'])))
		else:
			log.info(fmt_dups.format('Delete', 'Skipped',
									 keep['series'], delete['season'],
									 os.path.basename(keep['file']),
									 os.path.basename(delete['file'])))

	def _rename_dup(self, keep, delete):
		return
		fmt_dups = '{0: <8.8s} {1: <8.8s} SERIES: {2: <25.25s} SEA: {3:02d} KEEPING: {4: <35.35s} REMOVING: {5: <35.35s}'
		log.info(fmt_dups.format('Rename', '',
								 keep['series'], delete['season'],
								 os.path.basename(keep['file']), os.path.basename(delete['file'])))

	def _list_dir(self, path):
		from subprocess import call
		p = call(['ls', '-l', path], shell=False)

if __name__ == "__main__":

#	from library import Library
	from logging import INFO, WARNING, ERROR

	logger.initialize()

	library = CheckSeries()

	Library.args = library.options.parser.parse_args(sys.argv[1:])
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

	if library.args.no_excludes:
		library.settings.ExcludeScanList = []

	if len(library.args.library) == 0:
		msg = 'Missing Scan Starting Point (Input Directory), Using Default: {}'.format(library.settings.SeriesDir)
		log.info(msg)
		library.args.library = [library.settings.SeriesDir]

	for _lib_path in library.args.library:
		if os.path.exists(_lib_path):
			library.check(_lib_path)
		else:
			log.warn('Skipping Rename: Unable to find File/Directory: {}'.format(_lib_path))



