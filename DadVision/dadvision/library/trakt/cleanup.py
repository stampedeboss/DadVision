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

import tmdb3
from pytvdbapi import api, error
from tqdm import tqdm

from common import logger
from library import Library
from library.trakt.show import getShow
from library.trakt.user import *
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

		return

	def ProcessRequest(self):

		if self.args.HostName:
			for hostname in self.args.HostName:
				profiles = self.settings.GetHostConfig(requested_host=[hostname])
				self.args.TraktUserID = profiles[hostname]['TraktUserID']
				self.args.TraktAuthorization = profiles[hostname]['TraktAuthorization']

				log.info('Processing entires for: {}'.format(self.args.TraktUserID))

				if hostname == 'grumpy':
					self.cleanup_lists()

				if self.args.Clear == 'None':
					self.cleanup_shows()
					self.cleanup_movies()
					return
				if 'shows' in self.args.Clear:
					pass
#					self.clear_shows()
				if 'movies' in self.args.Clear:
					self.clear_movies()
		return

	def cleanup_shows(self):

		#Create Show Lists
		_watched = getWatched(self.args.TraktUserID,
						     self.args.TraktAuthorization,
							 entrytype='shows',
							 rtn=dict)
		if type(_watched) == HTTPError:
			log.error('Watched: Invalid Return Code - {}'.format(_watched))

		_collected = getCollection(self.args.TraktUserID,
								  self.args.TraktAuthorization,
								  entrytype='shows',
								  rtn=dict)
		if type(_collected) == HTTPError:
			log.error('Collected: Invalid Return Code - {}'.format(_collected))

		_watchlist = getWatchList(self.args.TraktUserID,
								 self.args.TraktAuthorization,
								 entrytype='shows',
								 rtn=dict)
		if type(_watchlist) == HTTPError:
			log.error('Watchlist: Invalid Return Code - {}'.format(_watchlist))

		_remove_shows = [_watched[x] for x in _watched if x not in _collected]
		_unwatchlist_shows = [_collected[x] for x in _watchlist if x in _collected]

		if 'shows' in self.args.list:
			for key, val in _collected:
				log.info(key)

		log.info('Shows in Collection: {}'.format(len(_collected)))
		log.info('Watched Show Entries: {}'.format(len(_watched)))
		log.info('Watchlist Show Entries: {}'.format(len(_watchlist)))

		#Cleanup Seen Shows
		if _remove_shows:
			_rc = removeFromHistory(self.args.TraktUserID,
								   self.args.TraktAuthorization,
								   entries=_remove_shows)
			log.info('Seen Shows Cleaned Up: {}  Not Found: {}'.format(_rc['deleted']['shows'],
	                                                                  _rc['not_found']['shows']))
		else:
			log.info('No Show History Cleanup Needed')

	# 	#Cleanup Shows Watchlist
		if _unwatchlist_shows:
			_rc = removeFromWatchlist(self.args.TraktUserID,
									   self.args.TraktAuthorization,
									   entries=_unwatchlist_shows)
			log.info('Show Watchlist Cleaned Up: {}  Not Found: {}'.format(_rc['deleted']['shows'],
	                                                                      _rc['not_found']['shows']))
		else:
			log.info('No Show Watchlist Cleanup Needed')

		return

	def cleanup_movies(self):
		_watched = getWatched(self.args.TraktUserID,
						     self.args.TraktAuthorization,
							 entrytype='movies',
							 rtn=dict)
		if type(_watched) == HTTPError:
			log.error('Watched: Invalid Return Code - {}'.format(_watched))

		_collected = getCollection(self.args.TraktUserID,
								  self.args.TraktAuthorization,
								  entrytype='movies',
								  rtn=dict)
		if type(_collected) == HTTPError:
			log.error('Collected: Invalid Return Code - {}'.format(_collected))

		_watchlist = getWatchList(self.args.TraktUserID,
								 self.args.TraktAuthorization,
								 entrytype='movies',
								 rtn=dict)
		if type(_watchlist) == HTTPError:
			log.error('WatchList: Invalid Return Code - {}'.format(_watchlist))

		_remove_movies = [_watched[x] for x in _watched if x not in _collected]
		_unwatchlist_movies = [_collected[x] for x in _watchlist if x in _collected]

		if 'movies' in self.args.list:
			for key, val in _collected.items():
				log.info(key)

		log.info('Movies in Collection: {}'.format(len(_collected)))
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

		_collected = getCollection(self.args.TraktUserID,
								  self.args.TraktAuthorization,
								  entrytype='movies')
		if type(_collected) == HTTPError:
			log.error('Watched: Invalid Return Code - {}'.format(_collected))

		# Remove Watched Entries for Movies
		if _watched:
			_rc = removeFromHistory(self.args.TraktUserID,
								   self.args.TraktAuthorization,
								   entries=_watched)
			log.info(_rc)

		# Remove Collection Entries for Movies
		if _collected:
			_rc = removeFromCollection(self.args.TraktUserID,
									   self.args.TraktAuthorization,
									   entries=_collected)
			log.info(_rc)

		return


	def cleanup_lists(self):

		_collected = getCollection(self.args.TraktUserID,
								  self.args.TraktAuthorization,
								  entrytype='shows',
								  rtn=dict)
		if type(_collected) == HTTPError:
			log.error('Collected: Invalid Return Code - {}'.format(_collected))

		_trakt_top_shows = getList(self.args.TraktUserID,
										  self.args.TraktAuthorization,
										  list='topshows',
										  rtn=dict)
		if type(_trakt_top_shows) == HTTPError:
			log.error('Top Shows: Invalid Return Code - {}'.format(_trakt_top_shows))

		_trakt_std_shows = getList(self.args.TraktUserID,
										   self.args.TraktAuthorization,
										   list='stdshows',
										   rtn=dict)
		if type(_trakt_std_shows) == HTTPError:
			log.error('Std Shows: Invalid Return Code - {}'.format(_trakt_std_shows))

		_new_shows = []
		_remove_shows = []
		_newly_collected = []

		for _entry in tqdm(_trakt_std_shows, desc='Std Shows'):
			if _entry in _collected:
				continue
			_remove_shows.append(_trakt_std_shows[_entry])

		for _entry  in tqdm(_trakt_top_shows, desc='TopShows'):
			if _entry in _collected:
				continue
			_remove_shows.append(_trakt_top_shows[_entry])

		#load entries to std-shows, exclude shows in top-shows and any that have ended
		for _dir in tqdm(os.listdir(self.settings.SeriesDir), desc='Check Lists'):

			_entry = None
			_rc = None
			_show = None
			_show_list = None

			if _ignored(_dir): continue

			if _dir in _trakt_top_shows:
				if _trakt_top_shows[_dir].status in ['Canceled/Ended']:
					_remove_shows.append(_trakt_top_shows[_dir])
				continue
			if _dir in _trakt_std_shows:
				if _trakt_std_shows[_dir].status in ['Canceled/Ended']:
					_remove_shows.append(_trakt_std_shows[_dir])
				continue
			if _dir in _collected:
				if _collected[_dir].status == 'Canceled/Ended':
					continue
				_new_shows.append(_collected[_dir])
				continue

			# Check Collected for Alternate Name
			try:
				_show_list = difflib.get_close_matches(_dir, _collected, 5, cutoff=0.6)
				if len(_show_list) > 0:
					for _entry in _show_list:
						_show = self.db.get_series(_collected[_entry].tvdb_id, 'en')
						if _dir.lower() == decode(_show.SeriesName).lower():
							raise GetOutOfLoop
			except error.TVDBIdError:
				continue
			except KeyError:
				pass
			except GetOutOfLoop:
				if _entry in _trakt_top_shows or _entry in _trakt_std_shows:
					if _show.Status in [u"Ended"]:
						_remove_shows.append(_collected[_entry])
					continue
				if _show.Status == u"Ended":
					continue
				_new_shows.append(_collected[_entry])
				continue

			_show_list = getShow(self.args.TraktUserID,
							    self.args.TraktAuthorization,
								show=_dir,
								rtn=list)
			if type(_show_list) == HTTPError:
				continue

			try:
				for _entry in _show_list:
					_show = self.db.get_series(_entry.tvdb_id, 'en')
					if _dir.lower() == decode(_show.SeriesName).lower():
						_new_shows.append(_entry)
						_newly_collected.append(_entry)
						break
			except error.TVDBIdError:
				_new_shows.extend(_show_list)
				_newly_collected.extend(_show_list)

		if _new_shows:
			for _entry in _new_shows:
				log.info('Adding: {}'.format(_entry.title))
			_rc = addToList(self.args.TraktUserID,
			                self.args.TraktAuthorization,
			                list='stdshows', entries=_new_shows)

			log.info('New Shows Added: {}  Existed: {}  Not Found: {}'.format(_rc['added']['shows'],
			                                                                  _rc['existing']['shows'],
			                                                                  _rc['not_found']['shows']))

		if _remove_shows:
			for _entry in _remove_shows:
				log.info('Removing: {}'.format(_entry.title))
			_rc = removeFromList(self.args.TraktUserID,
			                    self.args.TraktAuthorization,
			                    list='topshows', entries=_remove_shows)

			log.info('TopShows Removed: {}  Not Found: {}'.format(_rc['deleted']['shows'],
                                                                  _rc['not_found']['shows']))

			_rc = removeFromList(self.args.TraktUserID,
			                    self.args.TraktAuthorization,
			                    list='stdshows', entries=_remove_shows)

			log.info('StdShows Removed: {}  Not Found: {}'.format(_rc['deleted']['shows'],
                                                                  _rc['not_found']['shows']))

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
