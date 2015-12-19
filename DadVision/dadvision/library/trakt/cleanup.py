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
import os
import fnmatch
import difflib
import unidecode

import tmdb3
from pytvdbapi import api, error
from tqdm import tqdm

from common import logger
from common.decode import decode
from library import Library
from library.trakt.show import getShow
from library.trakt.user import *
from library.movie.gettmdb import TMDBInfo

from slugify import Slugify


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
dirslug = Slugify(pretranslate={"'": '_'}, translate=unidecode.unidecode, to_lower=True)

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

		trakt_options_group = self.options.parser.add_argument_group("Options", description=None)
		trakt_options_group.add_argument("-c", "--clear", dest="Clear", nargs='*',
			 action='store', default='None',
						 help='Clear/Delete all entries in requested area: shows, movies')
		trakt_options_group.add_argument("-l", "--list", dest="list", nargs='*',
			 action='store', default='None',
						 help='Clear/Delete all entries in requested area: shows, movies')

		tmdb3.set_key('587c13e576f991c0a653f783b290a065')
		tmdb3.set_cache(filename='tmdb3.cache')

		self.db = api.TVDB("959D8E76B796A1FB")
		self.tmdbinfo = TMDBInfo()

		self._collectedShows = []
		self._watchedShows = []
		self._watchlistShows = []
		self._trakt_sdtv = []
		self._trakt_720P = []
		self._trakt_list = []

		self.errorLog = []

		return

	def ProcessRequest(self):

		if not self.args.HostName:
			self.args.HostName = ['grumpy']

		for self._hostname in self.args.HostName:
			profiles = self.settings.GetHostConfig(requested_host=[self._hostname])
			self.args.TraktUserID = profiles[self._hostname]['TraktUserID']
			self.args.TraktAuthorization = profiles[self._hostname]['TraktAuthorization']

			log.info('Processing entires for: {}'.format(self.args.TraktUserID))

			if 'movies' in self.args.Clear:
				self.clear_movies()
				sys.exit(0)

			self.getTrakt()
			self.cleanup_shows()
			self.cleanup_movies()

		return

	def getTrakt(self):

		log.info('Retrieving Shows in Collection')
		self._collectedShows = getCollection(self.args.TraktUserID,
										self.args.TraktAuthorization,
										entrytype='shows',
										rtn=dict)
		if type(self._collectedShows) == HTTPError:
			log.error('Shows Collected: Invalid Return Code - {}'.format(self._collectedShows))
			sys.exit(99)

		log.info('Retrieving Shows that are marked as Watched')
		self._watchedShows = getWatched(self.args.TraktUserID,
							 self.args.TraktAuthorization,
							 entrytype='shows',
							 rtn=dict)
		if type(self._watchedShows) == HTTPError:
			log.error('Shows Watched: Invalid Return Code - {}'.format(self._watchedShows))
			sys.exit(99)

		log.info('Retrieving Shows on WatchList')
		self._watchlistShows = getWatchList(self.args.TraktUserID,
								 self.args.TraktAuthorization,
								 entrytype='shows',
								 rtn=dict)
		if type(self._watchlistShows) == HTTPError:
			log.error('Shows Watchlist: Invalid Return Code - {}'.format(self._watchlistShows))
			sys.exit(99)

		if self._hostname != 'grumpy':
			return


		self._trakt_720P = getList(self.args.TraktUserID,
										  self.args.TraktAuthorization,
										  list=self.settings.TraktFollowed720,
										  rtn=dict)
		if type(self._trakt_720P) == HTTPError:
			log.error('{}: Invalid Return Code - {}'.format(self.settings.TraktFollowed720, self._trakt_720P))
			sys.exit(99)

		self._trakt_sdtv = getList(self.args.TraktUserID,
										   self.args.TraktAuthorization,
										   list=self.settings.TraktFollowed,
										   rtn=dict)
		if type(self._trakt_sdtv) == HTTPError:
			log.error('{}: Invalid Return Code - {}'.format(self.settings.TraktFollowed, self._trakt_sdtv))
			sys.exit(99)

		self._trakt_list = dict(self._trakt_720P)
		self._trakt_list.update(self._trakt_sdtv)

		return



	def cleanup_shows(self):

		if self._hostname == 'grumpy':
			self.dir_check()

		#Create Show Lists
		_removeFromHistory = [self._watchedShows[x] for x in self._watchedShows if x not in self._collectedShows]
		_removeFromWatchlist = [self._collectedShows[x] for x in self._watchlistShows if x in self._collectedShows]

		log.info('Shows in Collection: {}'.format(len(self._collectedShows)))
		log.info('Watched Show Entries: {}'.format(len(self._watchedShows)))
		log.info('Watchlist Show Entries: {}'.format(len(self._watchlistShows)))

		#Cleanup Show History
		if _removeFromHistory:
			_rc = removeFromHistory(self.args.TraktUserID,
			                        self.args.TraktAuthorization,
			                        entries=_removeFromHistory)
			log.info('Seen Shows Cleaned Up: {}  Not Found: {}'.format(_rc['deleted']['episodes'],
																	  _rc['not_found']['shows']))
		else:
			log.info('No Show History Cleanup Needed')

	# 	#Cleanup Shows Watchlist
		if _removeFromWatchlist:
			_rc = removeFromWatchlist(self.args.TraktUserID,
									   self.args.TraktAuthorization,
									   entries=_removeFromWatchlist)
			log.info('Show Watchlist Cleaned Up: {}  Not Found: {}'.format(_rc['deleted']['shows'],
																		  _rc['not_found']['shows']))
		else:
			log.info('No Show Watchlist Cleanup Needed')

		if self._hostname != 'grumpy':
			return

		_remove_shows = []
		for _entry in tqdm(self._trakt_sdtv, desc=self.settings.TraktFollowed):
			if _entry in self._collectedShows:
				continue
			_remove_shows.append(self._trakt_sdtv[_entry])
		print("\n")

		if _remove_shows:
			for _entry in _remove_shows:
				log.info('{} - Removing: {}'.format(self.settings.TraktFollowed, _entry.title))
				del self._trakt_sdtv[_entry.slug]

			_rc = removeFromList(self.args.TraktUserID,
								self.args.TraktAuthorization,
								list=self.settings.TraktFollowed, entries=_remove_shows)

			log.info('{} Removed: {}  Not Found: {}'.format(self.settings.TraktFollowed,
															_rc['deleted']['shows'],
															_rc['not_found']['shows']))

		_remove_shows = []
		for _entry  in tqdm(self._trakt_720P, desc=self.settings.TraktFollowed720):
			if _entry in self._collectedShows:
				continue
			_remove_shows.append(self._trakt_720P[_entry])
		print("\n")

		if _remove_shows:
			for _entry in _remove_shows:
				log.info('Removing: {}'.format(_entry.title))
				del self._trakt_720P[_entry.slug]
			_rc = removeFromList(self.args.TraktUserID,
								self.args.TraktAuthorization,
								list=self.settings.TraktFollowed720, entries=_remove_shows)

			log.info('{} Removed: {}  Not Found: {}'.format(self.settings.TraktFollowed720,
															_rc['deleted']['shows'],
															_rc['not_found']['shows']))

		return

	def dir_check(self):

		#load entries to SDTV, excluding shows in 720P and any that have ended
		_remove_shows = []
		_new_shows = []
		_newly_collected = []

		_missing = sorted(self._collectedShows)

		for _dir in tqdm(sorted(os.listdir(self.settings.SeriesDir)), desc='Check Lists'):

			if _ignored(_dir): continue

			_show = self.findShow(_dir)

			if _show is None: continue

			if _show.slug in self._collectedShows:
				if _show.slug in _missing:
					_missing.remove(_show.slug)
				if _show.slug in self._trakt_list:
					if _show.status == 'Ended':
						_remove_shows.append(_show)
				elif _show.status in ['Other', 'Continuing']:
					_new_shows.append(_show)
				continue
			_newly_collected.append(_show)
			if _show.status == 'Continuing':
				if not _show.slug in self._trakt_list:
					_new_shows.append(_show)
		print("\n")

		if self.errorLog:
			for _entry in self.errorLog:
				log.warning(_entry)

		if _new_shows:
			for _entry in _new_shows:
				log.info('Adding to {}: {}'.format(self.settings.TraktFollowed, _entry.title))
			_rc = addToList(self.args.TraktUserID,
							self.args.TraktAuthorization,
							list=self.settings.TraktFollowed, entries=_new_shows)

			log.info('New Shows Added: {}  Existed: {}  Not Found: {}'.format(_rc['added']['shows'],
																			  _rc['existing']['shows'],
																			  _rc['not_found']['shows']))

		if _newly_collected:
			for _entry in _newly_collected:
				log.info('Adding to Collection: {}'.format(_entry.title))
			_rc = addToCollection(self.args.TraktUserID,
							self.args.TraktAuthorization,
							entries=_newly_collected)

			log.info('New Episodes Added: {}  Existed: {}  Not Found: {}'.format(_rc['added']['episodes'],
																			  _rc['existing']['episodes'],
																			  _rc['not_found']['episodes']))

		if _remove_shows:
			for _entry in _remove_shows:
				log.info('Removing: {}'.format(_entry.title))
			_rc = removeFromList(self.args.TraktUserID,
								self.args.TraktAuthorization,
								list=self.settings.TraktFollowed720, entries=_remove_shows)
			log.info('{} Removed: {}  Not Found: {}'.format(self.settings.TraktFollowed720,
			                                                _rc['deleted']['shows'],
															_rc['not_found']['shows']))

			_rc = removeFromList(self.args.TraktUserID,
								self.args.TraktAuthorization,
								list=self.settings.TraktFollowed, entries=_remove_shows)
			log.info('{} Removed: {}  Not Found: {}'.format(self.settings.TraktFollowed,
			                                                _rc['deleted']['shows'],
															_rc['not_found']['shows']))

		if _missing:
			_remove_shows = []
			for key in _missing:
				_remove_shows.append(self._collectedShows[key])
				del self._collectedShows[key]

			_rc = removeFromCollection(userid=self.args.TraktUserID,
									   authorization=self.args.TraktAuthorization,
									   entries=_remove_shows)
			log.info('{} Removed: {}  Not Found: {}'.format(self.settings.TraktFollowed,
			                                                _rc['deleted']['episodes'],
															_rc['not_found']['shows']))


		return

	def findShow(self, _dir):


		if dirslug(_dir) in self._collectedShows:
			return self._collectedShows[dirslug(_dir)]

		# Check Collected for Alternate Name
		try:
			_show_list = difflib.get_close_matches(dirslug(_dir), self._collectedShows, 5, cutoff=0.6)
			if len(_show_list) > 0:
				for _entry in _show_list:
					_show = self.db.get_series(self._collectedShows[_entry].tvdb_id, 'en')
					if _dir.lower() == decode(_show.SeriesName).lower():
						return self._collectedShows[_entry]
		except error.TVDBIdError:
			self.errorLog.append('Unable to locate Series in TVDB: {}'.format(_dir))
			return None
		except KeyError:
			pass

		# NEW SHOW
		_show_list = getShow(_dir,
		                     list,
							 self.args.TraktUserID,
							 self.args.TraktAuthorization,
							)
		if type(_show_list) == HTTPError:
			self.errorLog.append('Unable to locate Series: {}'.format(_dir))
			return None

		try:
			for _entry in _show_list:
				_show = self.db.get_series(_entry.tvdb_id, 'en')
				if _dir.lower() == decode(_show.SeriesName).replace("/", "").lower():
					return _entry
		except error.TVDBIdError:
			self.errorLog.append('TBDBIdError: Skipping - {}'.format(_show_list))

		self.errorLog.append('Unable to locate Series: {}'.format(_dir))
		return None


	def cleanup_movies(self):
		_watched = getWatched(self.args.TraktUserID,
							 self.args.TraktAuthorization,
							 entrytype='movies',
							 rtn=dict)
		if type(_watched) == HTTPError:
			log.error('Watched: Invalid Return Code - {}'.format(_watched))

		_collectedMovies = getCollection(self.args.TraktUserID,
								  self.args.TraktAuthorization,
								  entrytype='movies',
								  rtn=dict)
		if type(_collectedMovies) == HTTPError:
			log.error('Collected: Invalid Return Code - {}'.format(_collectedMovies))

		_watchlist = getWatchList(self.args.TraktUserID,
								 self.args.TraktAuthorization,
								 entrytype='movies',
								 rtn=dict)
		if type(_watchlist) == HTTPError:
			log.error('WatchList: Invalid Return Code - {}'.format(_watchlist))

		_remove_movies = [_watched[x] for x in _watched if x not in _collectedMovies]
		_unwatchlist_movies = [_collectedMovies[x] for x in _watchlist if x in _collectedMovies]

		if 'movies' in self.args.list:
			for key, val in _collectedMovies.items():
				log.info(key)

		log.info('Movies in Collection: {}'.format(len(_collectedMovies)))
		log.info('Watched Movie Entries: {}'.format(len(_watched)))
		log.info('Movie Watchlist Entries: {}'.format(len(_watchlist)))

		# Remove Movies
		if _remove_movies:
			_rc = removeFromHistory(self.args.TraktUserID,
								   self.args.TraktAuthorization,
								   entries=_remove_movies)
			log.info('Movie History Cleaned Up: {}  Not Found: {}'.format(_rc['deleted']['movies'],
																		  _rc['not_found']['movies']))
		else:
			log.info('No Movie History Cleanup Needed')

		#Cleanup Movie Watchlist
		if _unwatchlist_movies:
			_rc = removeFromWatchlist(self.args.TraktUserID,
									   self.args.TraktAuthorization,
									   entries=_unwatchlist_movies)

			log.info('Movies Watchlist Cleaned Up: {}  Not Found: {}'.format(_rc['deleted']['movies'],
																			 _rc['not_found']['movies']))
		else:
			log.info('No Movie Watchlist Cleanup Needed')
		return

	def clear_movies(self):

		_watched = getWatched(self.args.TraktUserID,
							 self.args.TraktAuthorization,
							 entrytype='movies')
		if type(_watched) == HTTPError:
			log.error('Watched: Invalid Return Code - {}'.format(_watched))

		_collectedShows = getCollection(self.args.TraktUserID,
								  self.args.TraktAuthorization,
								  entrytype='movies')
		if type(_collectedShows) == HTTPError:
			log.error('Watched: Invalid Return Code - {}'.format(_collectedShows))

		# Remove Watched Entries for Movies
		if _watched:
			_rc = removeFromHistory(self.args.TraktUserID,
								   self.args.TraktAuthorization,
								   entries=_watched)
			log.info(_rc)

		# Remove Collection Entries for Movies
		if _collectedShows:
			_rc = removeFromCollection(self.args.TraktUserID,
									   self.args.TraktAuthorization,
									   entries=_collectedShows)
			log.info(_rc)

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
