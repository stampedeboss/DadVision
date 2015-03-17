#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Author: AJ Reynolds
Date: 01-24-2015
Purpose:
Program to cleanup the various lists and entries used from the TRAKT
website to support syncrmt and other DadVision modules.

ABOUT
Current functions:
 Remove entries from the watchlist that have been delivered.
 Repopulate the std-shows list
"""
from __future__ import division
from urllib2 import Request, urlopen
import logging
import json
import os
import sys

from library import Library
from common import logger
from library.series import Series
from library.movie import Movie


__pgmname__ = 'traktTV'
__version__ = '@version: $Rev: 462 $'

__author__ = "@author: AJ Reynolds"
__copyright__ = "@copyright: Copyright 2015, AJ Reynolds"
__status__ = "@status: Development"
__license__ = "@license: GPL"

__maintainer__ = "@organization: AJ Reynolds"
__credits__ = []

log = logging.getLogger(__pgmname__)


def use_library_logging(func):

	def wrapper(self, *args, **kw):
		# Set the library name in the logger
		logger.set_library(self.args.hostname.upper())
		try:
			return func(self, *args, **kw)
		finally:
			logger.set_library('')

	return wrapper

client_id = '54d65f67401b045bc720ef109d4d05a107c0f5e28badf2f413f89f9bee514ae7'
client_secret = '85f06b5b6d29265a8be4fa113bbaefb0dd58826cbfd4b85da9a709459a0cb9b1'


class myLibrary(Library):

	def __init__(self):
		super(myLibrary, self).__init__()


	def getWatchList(self, userid, authorization, entrytype='shows'):

		_watchlist = []

		_url = 'https://api-v2launch.trakt.tv/users/{}/watchlist/{}'.format(userid, entrytype)

		headers = {
		  'Content-Type': 'application/json',
		  'trakt-api-version': '2',
		  'trakt-api-key': client_id,
		  'Authorization': authorization
		}

		request = Request(_url, headers=headers)
		response_body = urlopen(request).read()
		data = json.loads(response_body.decode('UTF-8', 'ignore'))

		for entry in data:
			if entrytype == 'shows':
				_watchlist.append(Series(**entry))
			else:
				_watchlist.append(Movie(**entry))

		return _watchlist


	def removeFromWatchlist(self, userid, authorization, entries=None, entrytype=None):

		_list = []

		if entries is None:
			return 'No Data'

		if entrytype is None:
			entrytype = type(entries[0])
			if entrytype == Movie:
				entrytype = 'movies'
			elif entrytype == Series:
				entrytype = 'shows'

		for entry in entries:
			if hasattr(entry, 'ids'):
				_list.append({'ids': entry.ids})
			else:
				show_entry = {}
				if entry.imdb_id:
					show_entry['imdb'] = entry.imdb_id
				if entry.tmdb_id:
					show_entry['tmdb'] = entry.tmdb_id
				if entry.tvdb_id:
					show_entry['tvdb'] = entry.tvdb_id
				if entry.tvrage_id:
					show_entry['tvrage'] = entry.tvrage_id
				_list.append({'ids': show_entry})

		_url = 'https://api-v2launch.trakt.tv/sync/watchlist/remove'

		if entrytype == 'shows':
			json_data = json.dumps({'shows': _list})
		else:
			json_data = json.dumps({'movies': _list})
		clen = len(json_data)

		headers = {
					'Content-Type': 'application/json',
					'trakt-api-version': '2',
					'trakt-api-key': client_id,
					'Authorization': authorization,
					'Content-Length': clen
				}

		request = Request(_url, data=json_data, headers=headers)
		response_body = urlopen(request).read()
		data = json.loads(response_body.decode('UTF-8', 'ignore'))

		return data


	def getCollection(self, userid, authorization, entrytype='shows'):

		_collected = []

#		_url = 'https://api-v2launch.trakt.tv/users/{}/collection/{}'.format(userid, entrytype)

		_url = 'https://api-v2launch.trakt.tv/sync/collection/{}'.format(entrytype)

		headers = {
		  'Content-Type': 'application/json',
		  'trakt-api-version': '2',
		  'trakt-api-key': client_id,
		  'Authorization': authorization
		}

		request = Request(_url, headers=headers)
		response_body = urlopen(request).read()
		data = json.loads(response_body.decode('UTF-8', 'ignore'))

		for entry in data:
			if entrytype == 'shows':
				_collected.append(Series(**entry))
			else:
				_collected.append(Movie(**entry))

		return _collected


	def getWatched(self, userid, authorization, entrytype='shows'):

		_watchedlist = []

		_url = 'https://api-v2launch.trakt.tv/users/{}/watched/{}'.format(userid, entrytype)

		headers = {
		  'Content-Type': 'application/json',
		  'trakt-api-version': '2',
		  'trakt-api-key': client_id,
		  'Authorization': authorization
		}

		request = Request(_url, headers=headers)
		response_body = urlopen(request).read()
		data = json.loads(response_body.decode('UTF-8', 'ignore'))

		for entry in data:
			if entrytype == 'shows':
				_watchedlist.append(Series(**entry))
			else:
				_watchedlist.append(Movie(**entry))

		return _watchedlist


	def getList(self, userid, authorization, list='stdshows'):

		_list = []

		_url = 'https://api-v2launch.trakt.tv/users/{}/lists/{}/items'.format(userid, list)

		headers = {
		  'Content-Type': 'application/json',
		  'trakt-api-version': '2',
		  'trakt-api-key': client_id,
		  'Authorization': authorization
		}

		request = Request(_url, headers=headers)
		response_body = urlopen(request).read()
		data = json.loads(response_body.decode('UTF-8', 'ignore'))

		for entry in data:
			_list.append(Series(**entry))
#		else:
#			_list.append(Movie(**entry))

		return _list

	def addToList(self, userid, authorization, list='stdshows', entries=None):

		_list = []

		if entries is None:
			return 'No Data'

		for entry in entries:
			if hasattr(entry, 'ids'):
				_list.append({'ids': entry.ids})
			else:
				show_entry = {}
				if entry.imdb_id:
					show_entry['imdb'] = entry.imdb_id
				if entry.tmdb_id:
					show_entry['tmdb'] = entry.tmdb_id
				if entry.tvdb_id:
					show_entry['tvdb'] = entry.tvdb_id
				if entry.tvrage_id:
					show_entry['tvrage'] = entry.tvrage_id
				_list.append({'ids': show_entry})

		_url = 'https://api-v2launch.trakt.tv/users/{}/lists/{}/items'.format(userid, list)

		json_data = json.dumps({'shows': _list})
		clen = len(json_data)

		headers = {
		  'Content-Type': 'application/json',
		  'trakt-api-version': '2',
		  'trakt-api-key': client_id,
		  'Authorization': authorization,
		  'Content-Length': clen
		}

		request = Request(_url, data=json_data, headers=headers)
		response_body = urlopen(request).read()
		data = json.loads(response_body.decode('UTF-8', 'ignore'))

		return data


	def removeFromList(self, userid, authorization, list='stdshows', entries=None):

		_list = []

		if entries is None:
			return 'No Data'

		for entry in entries:
			if hasattr(entry, 'ids'):
				_list.append({'ids': entry.ids})
			else:
				show_entry = {}
				if entry.imdb_id:
					show_entry['imdb'] = entry.imdb_id
				if entry.tmdb_id:
					show_entry['tmdb'] = entry.tmdb_id
				if entry.tvdb_id:
					show_entry['tvdb'] = entry.tvdb_id
				if entry.tvrage_id:
					show_entry['tvrage'] = entry.tvrage_id
				_list.append({'ids': show_entry})

		_url = 'https://api-v2launch.trakt.tv/users/{}/lists/{}/items/remove'.format(userid, list)

		json_data = json.dumps({'shows': _list})
		clen = len(json_data)

		headers = {
					'Content-Type': 'application/json',
					'trakt-api-version': '2',
					'trakt-api-key': client_id,
					'Authorization': authorization,
					'Content-Length': clen
				}
		request = Request(_url, data=json_data, headers=headers)
		response_body = urlopen(request).read()
		data = json.loads(response_body.decode('UTF-8', 'ignore'))

		return data


	def removeFromHistory(self, userid, authorization, entries=None, entrytype=None):

		_list = []

		if entries is None:
			return 'No Data'

		if entrytype is None:
			entrytype = type(entries[0])
			if entrytype == Movie:
				entrytype = 'movies'
			elif entrytype == Series:
				entrytype = 'shows'

		for entry in entries:
			if hasattr(entry, 'ids'):
				_list.append({'ids': entry.ids})
			else:
				show_entry = {}
				if entry.imdb_id:
					show_entry['imdb'] = entry.imdb_id
				if entry.tmdb_id:
					show_entry['tmdb'] = entry.tmdb_id
				if entry.tvdb_id:
					show_entry['tvdb'] = entry.tvdb_id
				if entry.tvrage_id:
					show_entry['tvrage'] = entry.tvrage_id
				_list.append({'ids': show_entry})

		_url = 'https://api-v2launch.trakt.tv/sync/history/remove'

		if entrytype == 'shows':
			json_data = json.dumps({'shows': _list})
		else:
			json_data = json.dumps({'movies': _list})
		clen = len(json_data)

		headers = {
					'Content-Type': 'application/json',
					'trakt-api-version': '2',
					'trakt-api-key': client_id,
					'Authorization': authorization,
					'Content-Length': clen
				}

		request = Request(_url, data=json_data, headers=headers)
		response_body = urlopen(request).read()
		data = json.loads(response_body.decode('UTF-8', 'ignore'))

		return data

	def removeFromCollection(self, userid, authorization, entries=None, entrytype=None):

		_list = []

		if entries is None:
			return 'No Data'

		if entrytype is None:
			entrytype = type(entries[0])
			if entrytype == Movie:
				entrytype = 'movies'
			elif entrytype == Series:
				entrytype = 'shows'

		for entry in entries:
			if hasattr(entry, 'ids'):
				_list.append({'ids': entry.ids})
			else:
				show_entry = {}
				if entry.imdb_id:
					show_entry['imdb'] = entry.imdb_id
				if entry.tmdb_id:
					show_entry['tmdb'] = entry.tmdb_id
				if entry.tvdb_id:
					show_entry['tvdb'] = entry.tvdb_id
				if entry.tvrage_id:
					show_entry['tvrage'] = entry.tvrage_id
				_list.append({'ids': show_entry})

		_url = 'https://api-v2launch.trakt.tv/sync/collection/remove'

		if entrytype == 'shows':
			json_data = json.dumps({'shows': _list})
		else:
			json_data = json.dumps({'movies': _list})
		clen = len(json_data)

		headers = {
					'Content-Type': 'application/json',
					'trakt-api-version': '2',
					'trakt-api-key': client_id,
					'Authorization': authorization,
					'Content-Length': clen
				}

		request = Request(_url, data=json_data, headers=headers)
		response_body = urlopen(request).read()
		data = json.loads(response_body.decode('UTF-8', 'ignore'))

		return data


if __name__ == '__main__':

	logger.initialize()
	library = myLibrary()

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

	for entry in library.settings.Hostnames:
		print entry
		library.settings.ReloadHostConfig(entry)
		print library.settings.TraktUserID, library.settings.TraktAuthorization
		list = library.getList(library.settings.TraktUserID, library.settings.TraktAuthorization, 'stdshows')
#        collection = library.getCollection(library.settings.TraktUserID, library.settings.TraktAuthorization)
#		print collection
