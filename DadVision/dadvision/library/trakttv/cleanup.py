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
from exceptions import ValueError
import logging
import os
import sys
import urllib2
import json
import base64
import hashlib
import socket

from pytvdbapi import api
import tmdb3
import trakt
from trakt.users import User, UserList
from trakt.tv import TVShow

from library import Library
from common import logger
from common.exceptions import MovieNotFound, SeriesNotFound
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
				# self.cleanup_lists()

		return

	def cleanup_shows(self):

		#Create Show Lists
		trakt_shows_list = self.trakt_user.shows
		trakt_shows_list_names = {_item.title: _item for _item in trakt_shows_list}

		trakt_shows_collected = self.trakt_user.show_collection
		trakt_shows_collected_names = {_item.title: _item for _item in trakt_shows_collected}

		trakt_shows_watchlist = self.trakt_user.show_watchlist
		trakt_shows_watchlist_names = {_item.title: _item for _item in trakt_shows_watchlist}

		# #Cleanup Seen Shows
		trakt_unseen_needed = [trakt_shows_list_names[x] for x in trakt_shows_list_names if x not in trakt_shows_collected_names]

		for _item in trakt_unseen_needed:
			try:
				self.show(_item.title, target='episode/unseen')
			except:
				pass

		# #Cleanup Shows Watchlist
		trakt_shows_unwatchlist_needed = [trakt_shows_collected_names[x] for x in trakt_shows_watchlist_names if x in trakt_shows_collected_names]

		for _item in trakt_shows_unwatchlist_needed:
			try:
				self.show(_item.title, target='unwatchlist')
			except:
				pass

		return

	def show(self, series_name, type='show', target='unwatchlist'):

		try:
			_series_details = self.seriesinfo.getShowInfo({'SeriesName': series_name})
		except:
			raise SeriesNotFound

		request = {}
		request['title'] = _series_details['SeriesName']
		request['tvdb_id'] = _series_details['tvdb_id']
		request['imdb_id'] = _series_details['imdb_id']
		_episodes = []

		if target in ['seen', 'episode/unseen']:
			for episode in _series_details['EpisodeData']:
				_episodes.append({'season': episode['SeasonNum'], 'episode': episode['EpisodeNum']})
			request['episodes'] = _episodes

		if type == 'lists':
			type = 'show'

		if target in ['watchlist', 'unwatchlist']:
			response = self.post_data(request, type, target)
			log.info('{}: {}'.format(_series_details['SeriesName'], response))
		else:
			response = self.post_show(request, type, target)
			log.info('{}: {}'.format(_series_details['SeriesName'], response))

		return

	def cleanup_movies(self):

		trakt_movies_list = self.trakt_user.movies
		trakt_movies_list_names = {_item.title: _item for _item in trakt_movies_list}

		trakt_movies_collected = self.trakt_user.movie_collection
		trakt_movies_collected_names = {_item.title: _item for _item in trakt_movies_collected}

		trakt_movies_watchlist = self.trakt_user.movie_watchlist
		trakt_movies_watchlist_names = {_item.title: _item for _item in trakt_movies_watchlist}

		#Cleanup Seen Movies
		trakt_movies_unseen_needed = [trakt_movies_list_names[x] for x in trakt_movies_list_names if x not in trakt_movies_collected_names]

		for _item in trakt_movies_unseen_needed:
			try:
				self.movie(_item.title, _item.year, target='unseen')
			except:
				pass

		#Cleanup Movies Watchlist
		trakt_movies_unwatchlist_needed = [trakt_movies_collected_names[x] for x in trakt_movies_watchlist_names if x in trakt_movies_collected_names]

		for _item in trakt_movies_unwatchlist_needed:
			try:
				self.movie(_item.title, _item.year, target='unwatchlist')
			except:
				pass

		return

	def movie(self, movie_name, year, type='movie', target='unwatchlist'):

		try:
			movie_details = self.tmdbinfo._get_details({'MovieName': movie_name, 'Year': year})
		except:
			raise MovieNotFound('Movie Not Found: {} ({})'.format(movie_name, year))

		request = {}
		request['title'] = movie_details['MovieName']
		request['imdb_id'] = movie_details['imdb_id']
		request['tmdb_id'] = movie_details['tmdb_id']
		request['year'] = str(movie_details['Year'])

		if type == 'lists':
			request['type'] = 'movie'

		response = self.post_data(request, type, target)
		log.info('{}: {}'.format(movie_details['MovieName'], response))

		return

	def cleanup_lists(self):

		#Delete all entries from std-shows to prepare for reload
		trakt_std_shows_list = self.trakt_user.get_list('std-shows')
		self.request = {'items': []}
		self.request['slug'] = 'std-shows'
		for show in trakt_std_shows_list.items:
			show_entry = {}
			show_entry['type'] = 'show'
			show_entry['title'] = show.title
			show_entry['tvdb_id'] = show.tvdb_id
			self.request['items'].append(show_entry)

		self.args.Type = 'lists'
		self.args.Target = 'items/{}'.format('delete')
		response = self.post_data()
		log.info(response)

		#Reload entries to std-shows, exclude top-shows and shows that have ended
		new_shows = []
		trakt_top_shows = self.trakt_user.get_list('top-shows')
		trakt_top_shows_names = {_item.title: _item for _item in trakt_top_shows.items}
		for dir in os.listdir(self.settings.SeriesDir):
			if dir in trakt_top_shows_names:
				continue
			if dir in trakt_shows_collected_names:
				continue
			try:
				show = TVShow(dir)
				new_shows.append({dir: show})
			except ValueError:
				pass

		# self.request = {'items': []}
		# self.request['slug'] = 'top-shows'
		# for show in trakt_shows_collected:
		#     if show.title in trakt_std-shows_list_names:
		#         continue
		#     if show.status == 'Ended':
		#         continue
		#     show_entry = {}
		#     show_entry['type'] = 'show'
		#     show_entry['title'] = show.title
		#     show_entry['tvdb_id'] = show.tvdb_id
		#     self.request['items'].append(show_entry)
		#
		# self.args.Type = 'lists'
		# self.args.Target = 'items/{}'.format(self.args.ActionTaken)
		# response = self.post_data()
		# log.info(response)

		return

	def lists(self, list_name):
		# http://api.trakt.tv/lists/items/add/apikey
		trakt.users.extended_output(True)
		trakt_user = User(self.args.TraktUserID)

		trakt_list = trakt_user.get_list('std-shows')
		self.request = {'items': []}
		self.request['slug'] = 'std-shows'
		for show in trakt_list.items:
			show_entry = {}
			show_entry['type'] = 'show'
			show_entry['title'] = show.title
			show_entry['tvdb_id'] = show.tvdb_id
			self.request['items'].append(show_entry)

		self.args.Type = 'lists'
		self.args.Target = 'items/{}'.format('delete')
		response = self.post_data()
		log.info(response)

		trakt_list = trakt_user.get_list('top-shows')
		trakt_list_names = {_item.title: _item for _item in trakt_list.items}
		trakt_collected = trakt_user.show_collection
		self.request = {'items': []}
		self.request['slug'] = list_name
		for show in trakt_collected:
			if show.title in trakt_list_names:
				continue
			if show.status == 'Ended':
				continue
			show_entry = {}
			show_entry['type'] = 'show'
			show_entry['title'] = show.title
			show_entry['tvdb_id'] = show.tvdb_id
			self.request['items'].append(show_entry)

		self.args.Type = 'lists'
		self.args.Target = 'items/{}'.format(self.args.ActionTaken)
		response = self.post_data()
		log.info(response)

		return

	def users(self, args):

		return


	def post_data(self, request, type, target):
		pydata = {'username': self.settings.TraktUserID, 'password': self.settings.TraktHashPswd}
		if type == 'lists':
			pydata.update(request)
		else:
			pydata[type+'s'] = [request]

		json_data = json.dumps(pydata)
		clen = len(json_data)
		_url = "http://api.trakt.tv/{}/{}/{}".format(type, target, self.settings.TraktAPIKey)
		req = urllib2.Request(_url, json_data, {'Content-Type': 'application/json', 'Content-Length': clen})
		f = urllib2.urlopen(req)
		response = f.read()
		f.close()
		return response

	def post_show(self, request, type, target):
		pydata = {'username': self.settings.TraktUserID, 'password': self.settings.TraktHashPswd}
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
