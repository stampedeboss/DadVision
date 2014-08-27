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
from exceptions import ValueError, AttributeError
import logging
import os
import sys
import urllib2
import json
import base64
import hashlib
import traceback
import fnmatch
import unicodedata
import pprint

from pytvdbapi import api
import tmdb3
import trakt
from trakt.users import User, UserList
from trakt.tv import TVShow

from library import Library
from common import logger
from common.exceptions import MovieNotFound, SeriesNotFound, EpisodeNotFound
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

		return

	def ProcessRequest(self):

		if self.args.HostName:
			for hostname in self.args.HostName:
				profiles = self.settings.GetHostConfig(requested_host=[hostname])
				self.args.TraktUserID = profiles[hostname]['TraktUserID']
				self.args.TraktPassWord = profiles[hostname]['TraktPassWord']
				self.args.TraktHashPswd = hashlib.sha1(profiles[hostname]['TraktPassWord']).hexdigest()
				self.args.TraktAPIKey = profiles[hostname]['TraktAPIKey']
				self.args.TraktBase64Key = base64.encodestring(self.args.TraktUserID+':'+self.args.TraktPassWord)

				log.info('Processing entires for: {}'.format(self.args.TraktUserID))

				if self.args.TraktAPIKey:
					trakt.api_key = self.args.TraktAPIKey
					trakt.authenticate(self.args.TraktUserID, self.args.TraktPassWord)
				else:
					trakt.api_key = self.settings.TraktAPIKey
					trakt.authenticate(self.settings.TraktUserID, self.settings.TraktPassWord)

				trakt.users.extended_output(True)
				self.trakt_user = User(self.args.TraktUserID)

				self.cleanup_shows()
				self.cleanup_movies()
				if hostname == 'grumpy':
					self.cleanup_lists()
		return

	def cleanup_shows(self):

		#Create Show Lists
		_trakt_shows_list = self.trakt_user.shows
		_trakt_shows_list_names = {_item.title: _item for _item in _trakt_shows_list}
		_trakt_shows_collected = self.trakt_user.show_collection
		_trakt_shows_collected_names = {_item.title: _item for _item in _trakt_shows_collected}
		_trakt_shows_watchlist = self.trakt_user.show_watchlist
		_trakt_shows_watchlist_names = {_item.title: _item for _item in _trakt_shows_watchlist}

		_trakt_shows_needing_unseen = [_trakt_shows_list_names[x] for x in _trakt_shows_list_names if x not in _trakt_shows_collected_names]
		_trakt_shows_needing_unwatchlist = [_trakt_shows_collected_names[x] for x in _trakt_shows_watchlist_names if x in _trakt_shows_collected_names]

		#Cleanup Seen Shows
		for _item in _trakt_shows_needing_unseen:
			try:
				_series_details = self.seriesinfo.getShowInfo({'SeriesName': _item.title}, sources=['tvdb'])
			except (SeriesNotFound, EpisodeNotFound):
				continue

			_show_entry = {}
			_show_entry['title'] = _series_details['SeriesName']
			if 'tvdb_id' in _series_details:
				_show_entry['tvdb_id'] = _series_details['tvdb_id']
			if 'imdb_id' in _series_details:
				_show_entry['imdb_id'] = _series_details['imdb_id']

			_episodes = []
			for episode in _series_details['EpisodeData']:
				_episodes.append({'season': episode['SeasonNum'], 'episode': episode['EpisodeNum']})
			_show_entry['episodes'] = _episodes

			_response = self.post_show(_show_entry, 'show', 'episode/unseen')
			log.info('{}: {}'.format(_series_details['SeriesName'], _response))

		#Cleanup Shows Watchlist
		_remove_watchlist = {'shows': []}
		for _item in _trakt_shows_needing_unwatchlist:
			try:
				_series_details = self.seriesinfo.getShowInfo({'SeriesName': _item.title}, sources=['tvdb'], epdetail=False)
			except (SeriesNotFound, EpisodeNotFound):
				continue

			_show_entry = {}
			_show_entry['title'] = _series_details['SeriesName']
			if 'tvdb_id' in _series_details:
				_show_entry['tvdb_id'] = _series_details['tvdb_id']
			if 'imdb_id' in _series_details:
				_show_entry['imdb_id'] = _series_details['imdb_id']
			_remove_watchlist['shows'].append(_show_entry)

		if _remove_watchlist['shows']:
			response = self.post_data(_remove_watchlist, 'show', 'unwatchlist')
			log.info('{}: {}'.format(_series_details['SeriesName'], response))

		return

	def cleanup_movies(self):
		_trakt_movies_list = self.trakt_user.movies
		_trakt_movies_list_names = {'{} ({})'.format(_decode(_item.title), _item.year): _item for _item in _trakt_movies_list}
		_trakt_movies_collected = self.trakt_user.movie_collection
		_trakt_movies_collected_names = {'{} ({})'.format(_decode(_item.title), _item.year): _item for _item in _trakt_movies_collected}
		_trakt_movies_watchlist = self.trakt_user.movie_watchlist
		_trakt_movies_watchlist_names = {'{} ({})'.format(_decode(_item.title), _item.year): _item for _item in _trakt_movies_watchlist}

		_trakt_movies_needing_unseen = [_trakt_movies_list_names[x] for x in _trakt_movies_list_names if x not in _trakt_movies_collected_names]
		_trakt_movies_needing_unwatchlist = [_trakt_movies_collected_names[x] for x in _trakt_movies_watchlist_names if x in _trakt_movies_collected_names]

		#Cleanup Seen Movies
		_remove_seen = {'movies': []}
		for _item in _trakt_movies_needing_unseen:
			try:
				_movie_details = self.tmdbinfo._get_details({'MovieName': _item.title, 'Year': _item.year})
			except MovieNotFound:
				log.warn('Movie Not Found: {} ({})'.format(_item.title, _item.year))
				continue

			_movie_entry = {}
			_movie_entry['title'] = _movie_details['MovieName']
			_movie_entry['imdb_id'] = _movie_details['imdb_id']
			_movie_entry['tmdb_id'] = _movie_details['tmdb_id']
			_movie_entry['year'] = str(_movie_details['Year'])
			_remove_seen['movies'].append(_movie_entry)

		if _remove_seen['movies']:
			_response = self.post_data(_remove_seen, 'movie', 'unseen')
			log.info('{}'.format(_response))

		#Cleanup Movies Watchlist
		_remove_watchlist = {'movies': []}
		for _item in _trakt_movies_needing_unwatchlist:
			try:
				_movie_details = self.tmdbinfo._get_details({'MovieName': _item.title, 'Year': _item.year})
			except MovieNotFound:
				log.warn('Movie Not Found: {} ({})'.format(_item.title, _item.year))
				continue

			_movie_entry = {}
			_movie_entry['title'] = _movie_details['MovieName']
			_movie_entry['imdb_id'] = _movie_details['imdb_id']
			_movie_entry['tmdb_id'] = _movie_details['tmdb_id']
			_movie_entry['year'] = str(_movie_details['Year'])
			_remove_watchlist['movies'].append(_movie_entry)

		if _remove_watchlist['movies']:
			_response = self.post_data(_remove_watchlist, 'movie', 'unwatchlist')
			log.info('{}'.format(_response))

		return

	def cleanup_lists(self):

		#Delete all entries from std-shows to prepare for reload
		_trakt_top_shows = self.trakt_user.get_list('topshows')
		_trakt_top_shows_names = {_item.title: _item for _item in _trakt_top_shows.items}
		_trakt_std_shows_list = self.trakt_user.get_list('stdshows')

		_remove_show = {'slug': 'stdshows', 'items': []}
		for show in _trakt_std_shows_list.items:
			show_entry = {}
			show_entry['type'] = 'show'
			show_entry['title'] = show.title
			show_entry['tvdb_id'] = show.tvdb_id
			_remove_show['items'].append(show_entry)

		if _remove_show['items']:
			_type = 'lists'
			_target = 'items/{}'.format('delete')
			_response = self.post_data(_remove_show, _type, _target)
			log.info('{}: {}'.format('std-shows', _response))

		#Reload entries to std-shows, exclude top-shows and shows that have ended
		_load_shows = {'slug': 'stdshows', 'items': []}
		_shows_processed = 0
		_shows_ended = 0
		for _dir in os.listdir(self.settings.SeriesDir):
			if _ignored(_dir): continue
			if _dir in _trakt_top_shows_names:
				continue
			try:
				_series_details = self.seriesinfo.getShowInfo({'SeriesName': _dir}, sources=['tvdb'], epdetail=False)
				if _series_details['status'] == 'Canceled/Ended':
					_shows_ended += 1
					continue
			except (SeriesNotFound, EpisodeNotFound):
				log.warn('{}: Show Not Found' .format(_dir))
				continue
			except:
				log.warn('Issue with Series Info: {}'.format(pprint.pformat(_series_details, indent=1, depth=1)))
				an_error = traceback.format_exc()
				log.debug(traceback.format_exception_only(type(an_error), an_error)[-1])
				continue
			_shows_processed += 1
			show_entry = {}
			show_entry['type'] = 'show'
			show_entry['title'] = _series_details['SeriesName']
			show_entry['tvdb_id'] = _series_details['tvdb_id']
			_load_shows['items'].append(show_entry)
			quotient, remainder = divmod(_shows_processed, 10)
			if remainder == 0:
				log.info('Ready for Reload: {}  Skipped-Canceled/Ended: {}'.format(_shows_processed, _shows_ended))


		if _load_shows['items']:
			_type = 'lists'
			_target = 'items/{}'.format('add')
			_response = self.post_data(_load_shows, _type, _target)
			log.info(_response)

		return

	def users(self, args):

		return

	def post_data(self, request, type, target):
		pydata = {'username': self.args.TraktUserID, 'password': self.args.TraktHashPswd}
		pydata.update(request)
		json_data = json.dumps(pydata)
		clen = len(json_data)
		_url = "http://api.trakt.tv/{}/{}/{}".format(type, target, self.settings.TraktAPIKey)
		req = urllib2.Request(_url, json_data, {'Content-Type': 'application/json', 'Content-Length': clen})
		f = urllib2.urlopen(req)
		response = f.read()
		f.close()
		return response

	def post_show(self, request, type, target):
		pydata = {'username': self.args.TraktUserID, 'password': self.args.TraktHashPswd}
		pydata.update(request)
		json_data = json.dumps(pydata)
		clen = len(json_data)
		_url = "http://api.trakt.tv/{}/{}/{}".format(type, target, self.settings.TraktAPIKey)
		req = urllib2.Request(_url, json_data, {'Content-Type': 'application/json', 'Content-Length': clen})
		f = urllib2.urlopen(req)
		response = f.read()
		f.close()
		return response


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
