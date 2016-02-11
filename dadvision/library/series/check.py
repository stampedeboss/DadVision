#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Purpose:
   Program to perform various tasks (check for missing episodes, locate duplication files, etc).
   Assist with maintaining a Library of Series and Episode files.

"""
from __future__ import division
from datetime import datetime, date, timedelta
import difflib
import fnmatch
import os
import re
import traceback
import unicodedata

from fuzzywuzzy import fuzz
from tqdm import tqdm

from common.exceptions import (SeriesNotFound)
from common import logger
from library import Library
from library.series import Series
from library.trakt.user import *
from library.series.fileparser import FileParser
from library.series.rename import RenameSeries


__pgmname__ = 'check'
__version__ = '$Rev: 474 $'

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

	log.trace("=" * 50)
	log.trace('Fuzzy Compare: {} - {}'.format(value1, value2))
	log.trace("-" * 50)
	log.trace('{}: Simple Ratio'.format(fuzzy[0]))
	log.trace('{}: Partial Ratio'.format(fuzzy[1]))
	log.trace('{}: Token Set Ratio'.format(fuzzy[2]))
	log.trace('{}: Token Sort Ratio'.format(fuzzy[3]))
	log.verbose('Match {}: {}'.format(any([fr > factor for fr in fuzzy]), fuzzy))

	return any([fr > factor for fr in fuzzy])


def _decode(coded_text):

	if type(coded_text) is unicode:
		decoded_text = unicodedata.normalize('NFKD', coded_text).encode('ascii', 'ignore')
		decoded_text = decoded_text.replace("&amp;", "&").replace("/", "_")
	else:
		decoded_text = coded_text

	return decoded_text


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
		check_group1.add_argument("-a", "--all-shows", dest="all_shows",
								  action="store_true", default=False,
								  help="Process all shows not just Continuing")
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
								  action="store", type=int, default=180,
								  help="Limit check back x number of days, default 30")
		check_group1.add_argument("-f", "--no-age-limit-requested", dest="age_limit",
								  action="store_const", const=99999,
								  help="Full Check")
		check_group1.add_argument("--dco", '--dup-check-only', dest="dup_check_only",
								  action="store_true", default=False,
								  help="Duplicate File Check Only")
		check_group1.add_argument("--check", '--check-names', dest="check_names",
								  action="store_true", default=False,
								  help="Perform Name Check")
		check_group1.add_argument("--check-quick", dest="quick",
								  action="store_true", default=False,
								  help="Perform Name Check")

		self.parser = FileParser()
		self.rename = RenameSeries()
		self.Series = Series()

		self.regex_season = re.compile('^(?:Season).(?P<SeasonNum>[0-9]+)$', re.I)
		self.regex_episode = re.compile('^(?:E)(?P<EpisodeNum>[0-9][0-9])[\-]?(?:E)?(?P<EpisodeNum2>[0-9][0-9])?(?P<EpisodeName>.+)?\.(?P<Ext>.+?)$', re.I)
		self.regex_repack = re.compile('^.*(repack|proper).*$', re.IGNORECASE)

		self.last_request = {}
		self.last_request['LastRequestName'] = ''
		self._trakt_top_shows = None

		return

	def check(self, pathname):
		log.trace('check: Pathname Requested: {}'.format(pathname))

		pathname = os.path.abspath(pathname)
		_series_details = []

		log.info("==== Begin Scan: {} ====".format(pathname))
		print("==== Begin Scan: {} ====".format(pathname))

		if self.args.check_names:
			self.check_series_name(pathname)
			sys.exit(0)

		if self.args.quick:
			self.check_series_name_quick(pathname)
			sys.exit(0)

		_seriesData = self.getSeriesData(pathname)

		if self.args.dup_check_only:
			sys.exit(0)

		for _show_name, _file_data in tqdm(sorted(_seriesData.iteritems()),
										   mininterval=0.5,
										   miniters=1,
										   leave=True):
			DadVision = _file_data['DadVision']
			try:
				_series = self.Series.search(title=_show_name, rtn=object)
				if _series.status == 'Continuing' or self.args.all_shows:
					_series.seasons = 'Load'
				else:
					continue
				if _series.seasons is None:
					raise SeriesNotFound
			except KeyboardInterrupt:
				sys.exit(99)
			except (SeriesNotFound), msg:
				print('\nSeries Not Found, Skipping: {}'.format(_show_name))
				log.error('Series Not Found, Skipping: {}'.format(_show_name))
				continue

			date_boundry = date.today() - timedelta(days=self.args.age_limit)
			missing = {}
			if _series.seasons is None:
				print('\nSeries Season Data Not Found, Skipping: {}'.format(_show_name))
				log.error('Series Season Data Not Found, Skipping: {}'.format(_show_name))
				continue
			for _season in sorted(_series.seasons.itervalues()):
				if not self.args.specials and _season.number == 0:
					continue
				if _season.episodes is None:
					print('\nSeries Episode Data Not Found, Skipping: {} - Season {}'.format(_show_name,
																							 _season.number))
					log.error('Series Episode Data Not Found, Skipping: {} - Season {}'.format(_show_name,
																							   _season.number))
					continue
				for _episode in _season.episodes.itervalues():
					try:
						if _episode.number not in DadVision[_season.number]:
							raise KeyError
					except KeyboardInterrupt:
						sys.exit(99)
					except KeyError:
						try:
							_episode.getDetails()
						except HTTPError:
							print('\nSeries Episode Data Not Found, Skipping: {} - Season {}'.format(_show_name,
																									 _season.number))
							log.error('Series Episode Data Not Found, Skipping: {} - Season {}'.format(_show_name,
																									   _season.number))
							continue
						if not _episode.first_aired:
							continue
						if _episode.first_aired < date_boundry or \
						   _episode.first_aired >= datetime.today().date():
							continue
						if _season.number in missing:
							missing[int(_season.number)].append(_episode.number)
						else:
							missing[int(_season.number)] = [_episode.number]

			_total_missing = 0
			for _missing_season, _missing_episodes in missing.iteritems():
				_total_missing += len(_missing_episodes)
			message = "Missing %3i episode(s) - SERIES: %-35.35s" % (_total_missing, _show_name)
			if _total_missing > 0:
				print('\n  {}'.format(message))
				log.warning(message)

			season_message = "         Season: {}  Episode: ALL"
			message = "         Season: {}  Episode: {}  Aired: {} Title: {}"
			for key, val in sorted(missing.iteritems()):
				_season_number = u'<Season {0:02}>'.format(key)
				_episodes = _series.seasons[_season_number].episodes
				_season_num_msg = "S%2.2d" % key
				if len(val) == len(_episodes):
#					print(season_message.format(_season_num_msg))
					log.warning(season_message.format(_season_num_msg))
				else:
					for _ep_no in sorted(val):
						_ep_no_fmt = "E%2.2d" % _ep_no
						_episode = _episodes[_ep_no_fmt]
						if _episode.first_aired:
							_first_aired = _episode.first_aired
						else:
							_first_aired = "Unknown"
#						print(message.format(key,
#											 _ep_no,
#											 _first_aired,
#											 _decode(_episode.title)))
						log.warning(message.format(key,
												 _ep_no,
												 _first_aired,
												 _decode(_episode.title)))

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
				print('WARNING: Possible Duplicate Directories: {} - {}'.format(_matches[0], _matches[1]))
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

		if self._trakt_top_shows is None:
			self._trakt_top_shows = getList(list='topshows',
											userid=self.settings.TraktUserID,
											authorization=self.settings.TraktAuthorization,
											rtn=dict)
			if type(self._trakt_top_shows) == HTTPError:
				print('Collection: Invalid Return Code - {}'.format(self._trakt_top_shows))
				log.error('Collection: Invalid Return Code - {}'.format(self._trakt_top_shows))
				sys.exit(99)

		fmt_dups = '{0: <8.8s} {1: <8.8s} SERIES: {2: <25.25s} SEA:{3:2d} 1: {4: <35.35s} 2: {5: <35.35s}'

		_prefered_fmts = ['mp4', 'mkv']

		for _episode in dups:
			file_1 = _episode[0]
			for i in range(1, len(_episode)):
				file_2 = _episode[i]

				if file_1['series'] in self._trakt_top_shows:
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
							_series_details = self.seriesinfo.getShowInfo(_file_parsed,  processOrder=['tvdb'])
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
									self.rename.renameFile(file_1['file'])
								else:
									self.rename.renameFile(file_2['file'])
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
						self.rename.renameFile(delete['file'])
#						os.remove(delete['file'])
					except KeyboardInterrupt:
						sys.exit(8)
					except OSError:
						an_error = traceback.format_exc()
						log.debug(traceback.format_exception_only(type(an_error), an_error)[-1])
						_delete = 'e'
				elif _delete == '1':
					try:
						self.rename.renameFile(keep['file'])
#						os.remove(keep['file'])
					except KeyboardInterrupt:
						sys.exit(8)
					except OSError:
						an_error = traceback.format_exc()
						log.debug(traceback.format_exception_only(type(an_error), an_error)[-1])
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
					except KeyboardInterrupt:
						sys.exit(8)
					except OSError:
						an_error = traceback.format_exc()
						log.debug(traceback.format_exception_only(type(an_error), an_error)[-1])
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


	def check_series_name(self, pathname):
		log.trace("="*30)
		log.trace("check_series_name method: pathname:{}".format(pathname))

		pathname = os.path.abspath(pathname)

		if os.path.isfile(pathname):
			log.debug("-"*30)
			log.debug("Series Directory: %s" % os.path.split(pathname)[0])
			log.debug("Series Filename:  %s" % os.path.split(pathname)[1])
			self.check_file(pathname)
		elif os.path.isdir(pathname):
			log.debug("-"*30)
			log.debug("Series Directory: %s" % pathname)
			for _root, _dirs, _files in os.walk(os.path.abspath(pathname)):
				_dirs.sort()
				for _dir in _dirs[:]:
					# Process Enbedded Directories
					if _ignored(_dir):
						_dirs.remove(_dir)

				_files.sort()
				for _file in _files:
					# _path_name = os.path.join(_root, _file)
					log.trace("Series Filename: %s" % _file)
					if _ignored(_file):
						continue
					self.check_file(_root, _file)
		return None

	def check_file(self, directory, filename):
		pathname = os.path.join(directory, filename)
		try:
			# Get File Details
			_last_series = self.last_request['LastRequestName']
			_parse_details = self.parser.getFileDetails(pathname)
			_seriesinfo_answer = self.parser.getFileDetails(pathname)
			_seriesinfo_answer = self.seriesinfo.getShowInfo(_seriesinfo_answer)
		except KeyboardInterrupt:
			sys.exit(8)
		except Exception:
			an_error = traceback.format_exc()
			log.debug(traceback.format_exception_only(type(an_error), an_error)[-1])
			sys.exc_clear()
			return

		log.trace('processing: {} vs {}'.format(_parse_details['SeriesName'], _seriesinfo_answer['SeriesName']))
		if _parse_details['SeriesName'] != _seriesinfo_answer['SeriesName']:
			if _last_series != _parse_details['SeriesName']:
				log.info('-'*40)
				log.info('Rename Required: {} (Current)'.format(_parse_details['SeriesName']))
				log.info('                 {} (Correct)'.format(_seriesinfo_answer['SeriesName']))

		if not self.args.quick:
			_seriesinfo_answer['EpisodeNumFmt'] = self.rename._format_episode_numbers(_seriesinfo_answer)
			_seriesinfo_answer['EpisodeTitle'] = self.rename._format_episode_name(_seriesinfo_answer['EpisodeData'], join_with=self.settings.ConversionsPatterns['multiep_join_name_with'])
	#		_seriesinfo_answer['DateAired'] = self.rename._get_date_aired(_seriesinfo_answer)
			_seriesinfo_answer['BaseDir'] = self.settings.SeriesDir

			_repack = self.regex_repack.search(pathname)
			if _repack: pathname_2 = self.settings.ConversionsPatterns['proper_fqn'] % _seriesinfo_answer
			else: pathname_2 = self.settings.ConversionsPatterns['std_fqn'] % _seriesinfo_answer
			if pathname != pathname_2:
				if os.path.basename(pathname) != os.path.basename(pathname_2):
					log.info('-'*40)
					log.info('{} (Series)'.format(_seriesinfo_answer['SeriesName']))
					log.info('Rename Required: {} (Correct)'.format(os.path.basename(pathname_2)))
					log.info('                 {} (Current)'.format(filename))

		s = _decode(pathname)
		if s != pathname:
			log.warning('INVALID CHARs: {} vs {}'.format(pathname - s, pathname))


	def check_series_name_quick(self, pathname):
		log.trace("="*30)
		log.trace("check_series_names_quick method: pathname:{}".format(pathname))

		self.regex_repack = re.compile('^.*(repack|proper).*$', re.IGNORECASE)
		pathname = os.path.abspath(pathname)

		if os.path.isfile(pathname):
			log.error("-"*30)
			log.error("File name passed must be Directory:  %s" % pathname)
			sys.exit()

		log.debug("-"*30)
		log.debug("Series Directory: %s" % pathname)
		for _dir in sorted(os.listdir(os.path.abspath(pathname))):
			if _ignored(_dir):
					continue
			_path_name = os.path.join(os.path.abspath(pathname), _dir, 'Season 1')
			self.check_file(_path_name, 'E01 Test.mkv')

		return None


if __name__ == "__main__":

#	from library import Library

	logger.initialize(console=False)

	library = CheckSeries()

	Library.args = library.options.parser.parse_args(sys.argv[1:])
	log.debug("Parsed command line: {!s}".format(library.args))

	log_level = logging.getLevelName(library.args.loglevel.upper())

	if library.args.logfile == 'daddyvision.log':
		log_file = '{}.log'.format('check_series')
	else:
		log_file = os.path.expanduser(library.args.logfile)

	# If an absolute path is not specified, use the default directory.
	if not os.path.isabs(log_file):
		log_file = os.path.join(logger.LogDir, log_file)

	logger.start(log_file, log_level, timed=False)

	if library.args.no_excludes:
		library.settings.ExcludeScanList = []

	if len(library.args.library) == 0:
		msg = 'Missing Scan Starting Point (Input Directory), Using Default: {}'.format(library.settings.SeriesDir)
		print(msg)
		log.info(msg)
		library.args.library = [library.settings.SeriesDir]

	for _lib_path in library.args.library:
		if os.path.exists(_lib_path):
			library.check(_lib_path)
		else:
			print('Skipping Rename: Unable to find File/Directory: {}'.format(_lib_path))
			log.warn('Skipping Rename: Unable to find File/Directory: {}'.format(_lib_path))

	with open(log_file, 'r') as fin:
		print(fin.read())

