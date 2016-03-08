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

import difflib
import os

import tmdb3
import unidecode
from dadvision import DadVision
from library import Library
from library.MyTrakt.show import getShow
from library.MyTrakt.user import *
from pytvdbapi import api, error
from slugify import Slugify
from tqdm import tqdm

import logger
#from movie import TMDBInfo

__pgmname__ = 'cleanup'

__author__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"

__maintainer__ = __author__

__copyright__ = "Copyright 2011, AJ Reynolds"
__license__ = "GPL"

log = logging.getLogger(__pgmname__)
dirslug = Slugify(pretranslate={"'": '_'}, translate=unidecode.unidecode, to_lower=True)

class CleanUp(Library):

	def __init__(self):
		log.trace('__init__ method: Started')

		super(CleanUp, self).__init__()

		trakt_auth_group = DadVision.cmdoptions.parser.add_argument_group("Profiles", description=None)
		trakt_auth_group.add_argument("-y", "--grumpy", dest="HostName",
			action="append_const", const="grumpy",
			help="Entries for Grumpy")
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

		trakt_options_group = DadVision.cmdoptions.parser.add_argument_group("Options", description=None)
		trakt_options_group.add_argument("-c", "--clear", dest="Clear", nargs='*',
			 action='store', default='None',
						 help='Clear/Delete all entries in requested area: shows, movies')
		trakt_options_group.add_argument("-l", "--list", dest="list", nargs='*',
			 action='store', default='None',
						 help='Clear/Delete all entries in requested area: shows, movies')

		tmdb3.set_key('587c13e576f991c0a653f783b290a065')
		tmdb3.set_cache(filename='tmdb3.cache')

		self.db = api.TVDB("959D8E76B796A1FB")
		#self.tmdbinfo = TMDBInfo()

		self._collectedShows = []
		self._watchedShows = []
		self._watchlistShows = []
		self._trakt_sdtv = []
		self._trakt_720P = []
		self._trakt_list = []

		self.errorLog = []

		return

	def ProcessRequest(self):

		if not DadVision.args.HostName:
			DadVision.args.HostName = ['grumpy']

		for self._hostname in DadVision.args.HostName:
			profiles = DadVision.settings.GetHostConfig(requested_host=[self._hostname])
			DadVision.args.TraktUserID = profiles[self._hostname]['TraktUserID']
			DadVision.args.TraktAuthorization = profiles[self._hostname]['TraktAuthorization']

			log.info('Processing entires for: {}'.format(DadVision.args.TraktUserID))

			if 'movies' in DadVision.args.Clear:
				self.clear_movies()
				sys.exit(0)

			self.getTrakt()
			self.cleanup_shows()
			self.cleanup_movies()

		return

	def getTrakt(self):

		log.info('Retrieving Shows in Collection')
		self._collectedShows = getCollection(DadVision.args.TraktUserID,
										DadVision.args.TraktAuthorization,
										entrytype='shows',
										rtn=dict)
		if type(self._collectedShows) == HTTPError:
			log.error('Shows Collected: Invalid Return Code - {}'.format(self._collectedShows))
			sys.exit(99)

		log.info('Retrieving Shows that are marked as Watched')
		self._watchedShows = getWatched(DadVision.args.TraktUserID,
							 DadVision.args.TraktAuthorization,
							 entrytype='shows',
							 rtn=dict)
		if type(self._watchedShows) == HTTPError:
			log.error('Shows Watched: Invalid Return Code - {}'.format(self._watchedShows))
			sys.exit(99)

		log.info('Retrieving Shows on WatchList')
		self._watchlistShows = getWatchList(DadVision.args.TraktUserID,
								 DadVision.args.TraktAuthorization,
								 entrytype='shows',
								 rtn=dict)
		if type(self._watchlistShows) == HTTPError:
			log.error('Shows Watchlist: Invalid Return Code - {}'.format(self._watchlistShows))
			sys.exit(99)

		if self._hostname != 'grumpy':
			return


		self._trakt_720P = getList(DadVision.args.TraktUserID,
										  DadVision.args.TraktAuthorization,
										  list=DadVision.settings.TraktFollowed720,
										  rtn=dict)
		if type(self._trakt_720P) == HTTPError:
			log.error('{}: Invalid Return Code - {}'.format(DadVision.settings.TraktFollowed720, self._trakt_720P))
			sys.exit(99)

		self._trakt_sdtv = getList(DadVision.args.TraktUserID,
										   DadVision.args.TraktAuthorization,
										   list=DadVision.settings.TraktFollowed,
										   rtn=dict)
		if type(self._trakt_sdtv) == HTTPError:
			log.error('{}: Invalid Return Code - {}'.format(DadVision.settings.TraktFollowed, self._trakt_sdtv))
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
			_rc = removeFromHistory(DadVision.args.TraktUserID,
			                        DadVision.args.TraktAuthorization,
			                        entries=_removeFromHistory)
			log.info('Seen Shows Cleaned Up: {}  Not Found: {}'.format(_rc['deleted']['episodes'],
																	  _rc['not_found']['shows']))
		else:
			log.info('No Show History Cleanup Needed')

	# 	#Cleanup Shows Watchlist
		if _removeFromWatchlist:
			_rc = removeFromWatchlist(DadVision.args.TraktUserID,
									   DadVision.args.TraktAuthorization,
									   entries=_removeFromWatchlist)
			log.info('Show Watchlist Cleaned Up: {}  Not Found: {}'.format(_rc['deleted']['shows'],
																		  _rc['not_found']['shows']))
		else:
			log.info('No Show Watchlist Cleanup Needed')

		if self._hostname != 'grumpy':
			return

		_remove_shows = []
		for _entry in tqdm(self._trakt_sdtv, desc=DadVision.settings.TraktFollowed):
			if _entry in self._collectedShows:
				continue
			_remove_shows.append(self._trakt_sdtv[_entry])
		print("\n")

		if _remove_shows:
			for _entry in _remove_shows:
				log.info('{} - Removing: {}'.format(DadVision.settings.TraktFollowed, _entry.title))
				del self._trakt_sdtv[_entry.slug]

			_rc = removeFromList(DadVision.args.TraktUserID,
								DadVision.args.TraktAuthorization,
								list=DadVision.settings.TraktFollowed, entries=_remove_shows)

			log.info('{} Removed: {}  Not Found: {}'.format(DadVision.settings.TraktFollowed,
															_rc['deleted']['shows'],
															_rc['not_found']['shows']))

		_remove_shows = []
		for _entry  in tqdm(self._trakt_720P, desc=DadVision.settings.TraktFollowed720):
			if _entry in self._collectedShows:
				continue
			_remove_shows.append(self._trakt_720P[_entry])
		print("\n")

		if _remove_shows:
			for _entry in _remove_shows:
				log.info('Removing: {}'.format(_entry.title))
				del self._trakt_720P[_entry.slug]
			_rc = removeFromList(DadVision.args.TraktUserID,
								DadVision.args.TraktAuthorization,
								list=DadVision.settings.TraktFollowed720, entries=_remove_shows)

			log.info('{} Removed: {}  Not Found: {}'.format(DadVision.settings.TraktFollowed720,
															_rc['deleted']['shows'],
															_rc['not_found']['shows']))

		return

	def dir_check(self):

		#load entries to SDTV, excluding shows in 720P and any that have ended
		_remove_shows = []
		_new_shows = []
		_newly_collected = []

		_missing = sorted(self._collectedShows)

		for _dir in tqdm(sorted(os.listdir(DadVision.settings.SeriesDir)), desc='Check Lists'):

			if self._ignored(_dir): continue

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
				log.info('Adding to {}: {}'.format(DadVision.settings.TraktFollowed, _entry.title))
			_rc = addToList(DadVision.args.TraktUserID,
							DadVision.args.TraktAuthorization,
							list=DadVision.settings.TraktFollowed, entries=_new_shows)

			log.info('New Shows Added: {}  Existed: {}  Not Found: {}'.format(_rc['added']['shows'],
																			  _rc['existing']['shows'],
																			  _rc['not_found']['shows']))

		if _newly_collected:
			for _entry in _newly_collected:
				log.info('Adding to Collection: {}'.format(_entry.title))
			_rc = addToCollection(DadVision.args.TraktUserID,
							DadVision.args.TraktAuthorization,
							entries=_newly_collected)

			log.info('New Episodes Added: {}  Existed: {}  Not Found: {}'.format(_rc['added']['episodes'],
																			  _rc['existing']['episodes'],
																			  _rc['not_found']['episodes']))

		if _remove_shows:
			for _entry in _remove_shows:
				log.info('Removing: {}'.format(_entry.title))
			_rc = removeFromList(DadVision.args.TraktUserID,
								DadVision.args.TraktAuthorization,
								list=DadVision.settings.TraktFollowed720, entries=_remove_shows)
			log.info('{} Removed: {}  Not Found: {}'.format(DadVision.settings.TraktFollowed720,
			                                                _rc['deleted']['shows'],
															_rc['not_found']['shows']))

			_rc = removeFromList(DadVision.args.TraktUserID,
								DadVision.args.TraktAuthorization,
								list=DadVision.settings.TraktFollowed, entries=_remove_shows)
			log.info('{} Removed: {}  Not Found: {}'.format(DadVision.settings.TraktFollowed,
			                                                _rc['deleted']['shows'],
															_rc['not_found']['shows']))

		if _missing:
			_remove_shows = []
			for key in _missing:
				_remove_shows.append(self._collectedShows[key])
				del self._collectedShows[key]

			_rc = removeFromCollection(userid=DadVision.args.TraktUserID,
									   authorization=DadVision.args.TraktAuthorization,
									   entries=_remove_shows)
			log.info('{} Removed: {}  Not Found: {}'.format(DadVision.settings.TraktFollowed,
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
					if _dir.lower() == self.decode(_show.SeriesName).lower():
						return self._collectedShows[_entry]
		except error.TVDBIdError:
			self.errorLog.append('Unable to locate Series in TVDB: {}'.format(_dir))
			return None
		except KeyError:
			pass

		# NEW SHOW
		_show_list = getShow(_dir,
		                     list,
							 DadVision.args.TraktUserID,
							 DadVision.args.TraktAuthorization,
							)
		if type(_show_list) == HTTPError:
			self.errorLog.append('Unable to locate Series: {}'.format(_dir))
			return None

		try:
			for _entry in _show_list:
				_show = self.db.get_series(_entry.tvdb_id, 'en')
				if _dir.lower() == self.decode(_show.SeriesName).replace("/", "").lower():
					return _entry
		except error.TVDBIdError:
			self.errorLog.append('TBDBIdError: Skipping - {}'.format(_show_list))

		self.errorLog.append('Unable to locate Series: {}'.format(_dir))
		return None


	def cleanup_movies(self):
		_watched = getWatched(DadVision.args.TraktUserID,
							 DadVision.args.TraktAuthorization,
							 entrytype='movies',
							 rtn=dict)
		if type(_watched) == HTTPError:
			log.error('Watched: Invalid Return Code - {}'.format(_watched))

		_collectedMovies = getCollection(DadVision.args.TraktUserID,
								  DadVision.args.TraktAuthorization,
								  entrytype='movies',
								  rtn=dict)
		if type(_collectedMovies) == HTTPError:
			log.error('Collected: Invalid Return Code - {}'.format(_collectedMovies))

		_watchlist = getWatchList(DadVision.args.TraktUserID,
								 DadVision.args.TraktAuthorization,
								 entrytype='movies',
								 rtn=dict)
		if type(_watchlist) == HTTPError:
			log.error('WatchList: Invalid Return Code - {}'.format(_watchlist))

		_remove_movies = [_watched[x] for x in _watched if x not in _collectedMovies]
		_unwatchlist_movies = [_collectedMovies[x] for x in _watchlist if x in _collectedMovies]

		if 'movies' in DadVision.args.list:
			for key, val in _collectedMovies.items():
				log.info(key)

		log.info('Movies in Collection: {}'.format(len(_collectedMovies)))
		log.info('Watched Movie Entries: {}'.format(len(_watched)))
		log.info('Movie Watchlist Entries: {}'.format(len(_watchlist)))

		# Remove Movies
		if _remove_movies:
			_rc = removeFromHistory(DadVision.args.TraktUserID,
								   DadVision.args.TraktAuthorization,
								   entries=_remove_movies)
			log.info('Movie History Cleaned Up: {}  Not Found: {}'.format(_rc['deleted']['movies'],
																		  _rc['not_found']['movies']))
		else:
			log.info('No Movie History Cleanup Needed')

		#Cleanup Movie Watchlist
		if _unwatchlist_movies:
			_rc = removeFromWatchlist(DadVision.args.TraktUserID,
									   DadVision.args.TraktAuthorization,
									   entries=_unwatchlist_movies)

			log.info('Movies Watchlist Cleaned Up: {}  Not Found: {}'.format(_rc['deleted']['movies'],
																			 _rc['not_found']['movies']))
		else:
			log.info('No Movie Watchlist Cleanup Needed')
		return

	def clear_movies(self):

		_watched = getWatched(DadVision.args.TraktUserID,
							 DadVision.args.TraktAuthorization,
							 entrytype='movies')
		if type(_watched) == HTTPError:
			log.error('Watched: Invalid Return Code - {}'.format(_watched))

		_collectedShows = getCollection(DadVision.args.TraktUserID,
								  DadVision.args.TraktAuthorization,
								  entrytype='movies')
		if type(_collectedShows) == HTTPError:
			log.error('Watched: Invalid Return Code - {}'.format(_collectedShows))

		# Remove Watched Entries for Movies
		if _watched:
			_rc = removeFromHistory(DadVision.args.TraktUserID,
								   DadVision.args.TraktAuthorization,
								   entries=_watched)
			log.info(_rc)

		# Remove Collection Entries for Movies
		if _collectedShows:
			_rc = removeFromCollection(DadVision.args.TraktUserID,
									   DadVision.args.TraktAuthorization,
									   entries=_collectedShows)
			log.info(_rc)

		return


if __name__ == "__main__":

	import pprint
	from sys import argv
	from logging import DEBUG; TRACE = 5; VERBOSE = 15

	DadVision.logger.initialize(level=DEBUG)
	cleanup = CleanUp()
	DadVision.args = DadVision.cmdoptions.ParseArgs(argv[1:])

	DadVision.logger.start(DadVision.args.logfile, DEBUG, timed=DadVision.args.timed)

	cleanup.ProcessRequest()

	'''
	if len(DadVision.args.pathname) > 0:
		for pathname in DadVision.args.pathname:
			try:
				#series.media_details(pathname)
				series.search(title='Star Trek TNG')
				#series.rename()
			except Exception, e:
				an_error = traceback.format_exc()
				raise
	pp = pprint.PrettyPrinter(indent=1, depth=2)
	print '-'*80
	pp.pprint(series.__dict__)

	'''