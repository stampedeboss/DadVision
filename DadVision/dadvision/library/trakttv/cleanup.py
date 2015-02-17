#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Author: AJ Reynolds
Date: 07-19-2014
Purpose:
Program to cleanup the various lists and entries used from the TRAKT
website to support syncrmt and other DadVision modules.

ABOUT
Current functions:
 Remove entries from the watchlist that have been delivered.
 Repopulate the std-shows list
"""
from __future__ import division
import logging
import os
import sys
import traceback
import fnmatch
import unicodedata

import tmdb3
from pytvdbapi import api
from fuzzywuzzy import fuzz

from common import logger
from common.exceptions import SeriesNotFound, EpisodeNotFound
from library import Library
from library.trakttv.user import myLibrary
from library.series.seriesinfo import SeriesInfo
from library.movie.gettmdb import TMDBInfo


__pgmname__ = 'cleanup'
__version__ = '$Rev$'

__author__ = "@author: AJ Reynolds"
__copyright__ = "@copyright: 2014, AJ Reynolds"
__credits__ = []
__license__ = "@license: GPL"

__maintainer__ = "AJ Reynolds"
__email__ = "@contact: stampedeboss@gmail.com"
__status__ = "Development"

__date__ = '2014-07-19'
__updated__ = '2014-07-19'

program_version_message = '%%(prog)s %s (%s)' % (__version__, __updated__)
program_license = '''

Created by AJ Reynolds on %s.
Copyright 2014 AJ Reynolds. All rights reserved.

Licensed under the GPL License

Distributed on an "AS IS" basis without warranties
or conditions of any kind, either express or implied.

USAGE
''' % (str(__date__))

log = logging.getLogger(__pgmname__)

def _matching(value1, value2, factor=None):
	"""

	:rtype : object
	"""
	log.trace("=================================================")
	log.trace("_matching: Compare: {} --> {}".format(value1, value2))

	fuzzy = []
	fuzzy.append(fuzz.ratio(value1.lower(), value2.lower()))
	fuzzy.append(fuzz.partial_ratio(value1.lower(), value2.lower()))
	fuzzy.append(fuzz.token_set_ratio(value1.lower(), value2.lower()))
	fuzzy.append(fuzz.token_sort_ratio(value1.lower(), value2.lower()))

	log.trace("=" * 50)
	log.trace('Fuzzy Compare: {} - {}'.format(value1.lower(), value2.lower()))
	log.trace("-" * 50)
	log.trace('{}: Simple Ratio'.format(fuzzy[0]))
	log.trace('{}: Partial Ratio'.format(fuzzy[1]))
	log.trace('{}: Token Set Ratio'.format(fuzzy[2]))
	log.trace('{}: Token Sort Ratio'.format(fuzzy[3]))
	log.trace(any([fr > factor for fr in fuzzy]))

	if factor:
		return any([fr >= factor for fr in fuzzy])

	score = 0
	entries = 0
	for fr in fuzzy:
		score += fr
		if fr > 0: entries += 1
	score = score/entries
	return score

def _decode(coded_text):

	decoded_text = unicodedata.normalize('NFKD', coded_text).encode('ascii', 'ignore')
	decoded_text = decoded_text.replace("&amp;", "&").replace("/", "_")

	return decoded_text


def _ignored(name):
	""" Check for ignored pathnames.
	"""
	rc = [False]
	if name == 'New': rc.append(True)
	rc.append(any(fnmatch.fnmatch(name.lower(), pattern) for pattern in library.settings.ExcludeList))
	return any(rc)


class GetOutOfLoop(Exception):
	pass


class CleanUp(Library):

	def __init__(self):
		log.trace('__init__ method: Started')

		super(CleanUp, self).__init__()

		trakt_auth_group = self.options.parser.add_argument_group("Profiles", description=None)
		trakt_auth_group.add_argument("-y", "--grumpy", dest="HostName",
			action="append_const", const="grumpy",
			help="Entires for Grumpy")
		trakt_auth_group.add_argument("-t", "--tigger", dest="HostName",
			action="append_const", const="tigger",
			help="Entires for Tigger")
		trakt_auth_group.add_argument("-g", "--goofy", dest="HostName",
			action="append_const", const="goofy",
			help="Entries for Goofy")
		trakt_auth_group.add_argument("-e", "--eeyore", dest="HostName",
			action="append_const", const="eeyore",
			help="Entries for Eeore")
		trakt_auth_group.add_argument("-p", "--pluto", dest="HostName",
			action="append_const", const="pluto",
			help="Entries for Pluto")

		tmdb3.set_key('587c13e576f991c0a653f783b290a065')
		tmdb3.set_cache(filename='tmdb3.cache')

		self.db = api.TVDB("959D8E76B796A1FB")

		self.seriesinfo = SeriesInfo()
		self.tmdbinfo = TMDBInfo()
		self.mylibrary = myLibrary()

		return

	def ProcessRequest(self):

		if self.args.HostName:
			for hostname in self.args.HostName:
				profiles = self.settings.GetHostConfig(requested_host=[hostname])
				self.args.TraktUserID = profiles[hostname]['TraktUserID']
				self.args.TraktAuthorization = profiles[hostname]['TraktAuthorization']

				log.info('Processing entires for: {}'.format(self.args.TraktUserID))

				self.cleanup_shows()
				self.cleanup_movies()
				if hostname == 'grumpy':
					self.cleanup_lists()
		return

	def cleanup_shows(self):

		#Create Show Lists
		_watched = self.mylibrary.getWatched(self.args.TraktUserID,
										     self.args.TraktAuthorization,
											 entrytype='shows')
		_watched_names = {_item.title: _item for _item in _watched}
		_collected = self.mylibrary.getCollection(self.args.TraktUserID,
												  self.args.TraktAuthorization,
												  entrytype='shows')
		_collected_names = {_item.title: _item for _item in _collected}
		_watchlist = self.mylibrary.getWatchList(self.args.TraktUserID,
												 self.args.TraktAuthorization,
												 entrytype='shows')
		_watchlist_names = {_item.title: _item for _item in _watchlist}

		_remove_shows = [_watched_names[x] for x in _watched_names if x not in _collected_names]
		_unwatchlist_shows = [_collected_names[x] for x in _watchlist_names if x in _collected_names]

		#Cleanup Seen Shows
		if _remove_shows:
			_rc = self.mylibrary.removeFromHistory(self.args.TraktUserID,
												   self.args.TraktAuthorization,
												   entries=_remove_shows)
			log.info(_rc)
		else:
			log.info('No Show History Cleanup Needed')

	# 	#Cleanup Shows Watchlist
		if _unwatchlist_shows:
			_rc = self.mylibrary.removeFromWatchlist(self.args.TraktUserID,
												   self.args.TraktAuthorization,
												   entries=_unwatchlist_shows)
			log.info(_rc)
		else:
			log.info('No Show Watchlist Cleanup Needed')

		return
	#
	def cleanup_movies(self):
		_watched = self.mylibrary.getWatched(self.args.TraktUserID,
										     self.args.TraktAuthorization,
											 entrytype='movies')
		_watched_names = {_item.title: _item for _item in _watched}
		_collected = self.mylibrary.getCollection(self.args.TraktUserID,
												  self.args.TraktAuthorization,
												  entrytype='movies')
		_collected_names = {_item.title: _item for _item in _collected}
		_watchlist = self.mylibrary.getWatchList(self.args.TraktUserID,
												 self.args.TraktAuthorization,
												 entrytype='movies')
		_watchlist_names = {_item.title: _item for _item in _watchlist}

		_remove_movies = [_watched_names[x] for x in _watched_names if x not in _collected_names]
		_unwatchlist_movies = [_collected_names[x] for x in _watchlist_names if x in _collected_names]

		# Remove Movies
		if _remove_movies:
			_rc = self.mylibrary.removeFromHistory(self.args.TraktUserID,
												   self.args.TraktAuthorization,
												   entries=_remove_movies)
			log.info(_rc)
		else:
			log.info('No Movie History Cleanup Needed')

		#Cleanup Movie Watchlist
		if _unwatchlist_movies:
			_rc = self.mylibrary.removeFromWatchlist(self.args.TraktUserID,
												   self.args.TraktAuthorization,
												   entries=_unwatchlist_movies)

			log.info(_rc)
		else:
			log.info('No Movie Watchlist Cleanup Needed')
		return

	def cleanup_lists(self):

		#Delete all entries from std-shows to prepare for reload
		_trakt_top_shows = self.mylibrary.getList(self.args.TraktUserID,
												  self.args.TraktAuthorization,
												  list='topshows')
		_trakt_top_shows_names = {_item.title: _item for _item in _trakt_top_shows}
		_trakt_std_shows = self.mylibrary.getList(self.args.TraktUserID,
													   self.args.TraktAuthorization,
													   list='stdshows')
		_trakt_std_shows_names = {_item.title: _item for _item in _trakt_std_shows}

		#Reload entries to std-shows, exclude top-shows and shows that have ended
		_new_shows = []
		_shows_processed = 0
		_shows_added = 0

		for _dir in os.listdir(self.settings.SeriesDir):
			_shows_processed += 1
			quotient, remainder = divmod(_shows_processed, 10)
			if remainder == 0:
				log.info('Shows Processes: {}  New Shows: {}'.format(_shows_processed, _shows_added))
			if _ignored(_dir): continue
			if _dir in _trakt_top_shows_names or _dir in _trakt_std_shows_names:
				continue
			try:
				_series_details = self.seriesinfo.getShowInfo({'SeriesName': _dir},
															  processOrder=['tvdb'],
															  epdetail=False)
				if _series_details['status'] == 'Canceled/Ended':
					continue
				if _series_details['TVSeries'].titleBase in _trakt_top_shows_names:
					continue
				if _series_details['TVSeries'].titleBase in _trakt_std_shows_names:
					continue
			except (SeriesNotFound, EpisodeNotFound):
				log.warn('{}: Show Not Found' .format(_dir))
				continue
			except:
				log.warn('Issue with Series Info: {}'.format(_dir))
				an_error = traceback.format_exc()
				log.debug(traceback.format_exception_only(type(an_error), an_error)[-1])
				continue
			_shows_added += 1
			_new_shows.append(_series_details['TVSeries'])

		if _new_shows:
			for entry in _new_shows:
				log.info('Adding: {}'.format(entry.title))
			_rc = self.mylibrary.addToList(self.args.TraktUserID,
			                               self.args.TraktAuthorization,
			                               list='stdshows', entries=_new_shows)
			log.info(_rc)

		return

	def users(self, args):

		return


if __name__ == "__main__":

	logger.initialize()
	library = CleanUp()

	Library.args = library.options.parser.parse_args(sys.argv[1:])
	log.debug("Parsed command line: {!s}".format(library.args))

	log_level = logging.getLevelName(library.args.loglevel.upper())

	if library.args.logfile == 'daddyvision.log':
		log_file = '{}.log'.format(__pgmname__)
	else:
		log_file = os.path.expanduser(library.args.logfile)

	# If an absolute path is not specified, use the default directory.
	if not os.path.isabs(log_file):
		logger.LogDir = os.path.join(logger.LogDir, 'trakt')
		log_file = os.path.join(logger.LogDir, log_file)

	library.args.logfile = log_file

	logger.start(log_file, log_level, timed=False)

	library.ProcessRequest()
