#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Author: AJ Reynolds
Date: 07-19-2014
Purpose:
Program to add entries to the TRAKT Movie Watchlist from a list of entries in a file

ABOUT
Movie names are one per line. The ideal format is "<name> <year>"
It is not required to have a year in the name but it helps IMDB
The whole idea is that this script will clean up the names before searching
IMDB for the movie so that it can be added by imdb_id to your trakt account

Titles that can't be added will be put in a file named FILE.unknown

Often you can make a listing of all your movies by running something like 'ls -1 > movies.txt'
on the directory that you dump all your movies in.

Examples of dirty movie names that can be cleaned:
    Shame.2011.720p.BluRay.x264.YIFY.mp4
    Quadrophenia.1979.DVDRIP-ZEKTORM.mp4
    Lars.and.the.Real.Girl.2007.720p.BluRay.X264-AMIABLE.mkv
"""
from library import Library
from common import logger
from common.exceptions import MovieNotFound, SeriesNotFound
from pytvdbapi import api
import logging
import os
import sys
import tmdb3
import unicodedata
import urllib2
import json
import base64
import hashlib
import socket

import trakt
from trakt.users import User, UserList
from trakt.movies import Movie
from trakt.tv import TVShow, TVSeason, TVEpisode, trending_shows, TraktRating, TraktStats, rate_shows, rate_episodes, genres, get_recommended_shows, dismiss_recommendation
# from trakt.traktcalendar import PremiereCalendar, ShowCalendar, UserCalendar
# from trakt.people import Person


__pgmname__ = 'testtrakt'
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


class TestTrakt(Library):

    def __init__(self):
        log.trace('__init__ method: Started')

        super(TestTrakt, self).__init__()

        trakt_auth_group = self.options.parser.add_mutually_exclusive_group()
        trakt_auth_group.add_argument("-y", "--grumpy", dest="HostName", default='grumpy',
            action="store_const", const="grumpy",
            help="Entires for Grumpy")
        trakt_auth_group.add_argument("-t", "--tigger", dest="HostName",
            action="store_const", const="tigger",
            help="Entires for Tigger")
        trakt_auth_group.add_argument("-g", "--goofy", dest="HostName",
            action="store_const", const="goofy",
            help="Entries for Goofy")
        trakt_auth_group.add_argument("-e", "--eeyore", dest="HostName",
            action="store_const", const="eeyore",
            help="Entries for Eeore")
        trakt_auth_group.add_argument("-p", "--pluto", dest="HostName",
            action="store_const", const="pluto",
            help="Entries for Pluto")

        trakt_action = self.options.parser.add_mutually_exclusive_group()
        trakt_action.add_argument("-a", "--add", dest="ActionTaken",
            action="store_const", const="add", default='add',
            help="Add entries to list")
        trakt_action.add_argument("-d", "--delete", dest="ActionTaken",
            action="store_const", const="delete",
            help="Delete entries from list")
        trakt_action.add_argument("--dump", dest="ActionTaken",
            action="store_const", const="dump",
            help="Dump the entries found in the selected list")

        trakt_type = self.options.parser.add_mutually_exclusive_group()
        trakt_type.add_argument("-s", "--show", dest="Type",
            action="store_const", const="show", default='show',
            help="Update list with show information")
        trakt_type.add_argument("-m", "--movie", dest="Type",
            action="store_const", const="movie",
            help="Update list with movie information")
        trakt_type.add_argument("-l", "--lists", dest="Type",
            action="store_const", const="lists",
            help="Update personal list (MyShow) with show or movie")
        trakt_type.add_argument("-u", "--users", dest="Type",
            action="store_const", const="users",
            help="Work with User Information")
        trakt_type.add_argument("--cleanup", dest="Type",
            action="store_const", const="cleanup",
            help="Cleanup based on lists")

        trakt_library = self.options.parser.add_mutually_exclusive_group()
        trakt_library.add_argument("--library", dest="Target",
            action="store_const", const="library", default='library',
            help="Make changes to Library")
        trakt_library.add_argument("--seen", dest="Target",
            action="store_const", const="seen",
            help="Make changes to Seen")
        trakt_library.add_argument("--watchlist", dest="Target",
            action="store_const", const="watchlist",
            help="Make changes to watchlist")
        trakt_library.add_argument("--named-list", dest="listName",
            action="store", nargs='?', default='myshows', const="myshows",
            help="Make changes to the list with this name")

        TMDB_group = self.options.parser.add_argument_group("Get TMDB Information Options", description=None)
        TMDB_group.add_argument("--movie-name", type=str, dest='movie_name', nargs='?')
        TMDB_group.add_argument("--year", type=int, dest='year', nargs='?')

        ep_group = self.options.parser.add_argument_group("Episode Detail Options", description=None)
        ep_group.add_argument("--series-name", type=str, dest='series_name')
        ep_group.add_argument("--season", type=int, dest='season')
        ep_group.add_argument("--epno", type=int, action='append', dest='epno')

        tmdb3.set_key('587c13e576f991c0a653f783b290a065')
        tmdb3.set_cache(filename='tmdb3.cache')

        self.db = api.TVDB("959D8E76B796A1FB")

        return

    def ProcessRequest(self):

        profiles = self.settings.GetHostConfig(requested_host=[socket.gethostname(), self.args.HostName])
        self.args.TraktUserID = profiles[self.args.HostName]['TraktUserID']
        self.args.TraktPassWord = profiles[self.args.HostName]['TraktPassWord']
        self.args.TraktHashPswd = hashlib.sha1(profiles[self.args.HostName]['TraktPassWord']).hexdigest()
        self.args.TraktAPIKey = profiles[self.args.HostName]['TraktAPIKey']
        self.args.TraktBase64Key = base64.encodestring(self.args.TraktUserID+':'+self.args.TraktPassWord)

        if self.args.TraktAPIKey:
            trakt.api_key = self.args.TraktAPIKey
            trakt.authenticate(self.args.TraktUserID, self.args.TraktPassWord)
        else:
            trakt.api_key = self.settings.TraktAPIKey
            trakt.authenticate(self.settings.TraktUserID, self.args.TraktPassWord)

        if self.args.series_name:
            self.args.Type = 'show'
        elif self.args.movie_name:
            self.args.Type = 'movie'

        options = {'show': self.show,
                    'movie': self.movie,
                    'lists': self.lists,
                    'users': self.users,
                    'cleanup': self.cleanup
        }

        args = {'show': self.args.series_name,
                'movie': (self.args.movie_name, self.args.year),
                'lists': None,
                'users': None,
                'cleanup': None
        }

        options[self.args.Type](args[self.args.Type])

        return

    def show(self, series_name):

        try:
            _tvdb_id = self.settings.TvdbIdList[series_name]
            _show = self.db.get_series(_tvdb_id, "en" )
        except:
            try:
                _show = self.db.get_series(series_name, "en" )
            except:
                log.warn('Series Not Found: {}'.format(series_name))
                raise SeriesNotFound('tvdb - Series Not Found: {} tvdbid: {}'.format(series_name, _tvdb_id))

        self.request = {}
        self.request['tvdb_id'] = _show.id
        self.request['imdb_id'] = _show.IMDB_ID
        self.request['title'] = _show.SeriesName

        if self.args.ActionTaken == 'delete':
            if self.args.Target in ['seen', 'episode/unseen']:
                _episodes = []
                for season in _show:
                    for episode in season:
                        _episodes.append({'season': season.season_number, 'episode': episode.EpisodeNumber})
                self.request['episodes'] = _episodes
                self.args.Target = 'episode/unseen'
            else:
                self.args.Target = 'un'+self.args.Target
        if self.args.Type == 'lists':
            self.request['type'] = 'show'

        if self.args.Target in ['watchlist', 'unwatchlist']:
            response = self.post_data()
            log.info('{}: {}'.format(_show.SeriesName, response))
        else:
            response = self.post_show()
            log.info('{}: {}'.format(_show.SeriesName, response))

        return

    def movie(self, movie_name, year):

        try:
            movie = list(tmdb3.searchMovieWithYear('{} ({})'.format(movie_name, year)))
            if len(movie) == 0:
                raise IndexError
            if type(movie) is list:
                movie = movie[0]
        except IndexError:
            try:
                movie = list(tmdb3.searchMovie(movie_name))
                if len(movie) > 0:
                    movie = movie[0]
                else:
                    raise MovieNotFound('Movie Not Found: {} ({})'.format(movie_name, year))
            except:
                raise MovieNotFound('Movie Not Found: {} ({})'.format(movie_name, year))

        self.request = {}
        self.request['title'] = movie.title
        self.request['imdb_id'] = movie.imdb
        self.request['tmdb_id'] = movie.id
        if movie.releasedate:
            self.request['year'] = str(movie.releasedate.year)
        else:
            self.request['year'] = None

        if self.args.ActionTaken == 'delete':
            if self.args.Target in ['watchlist', 'library', 'seen']:
                self.args.Target = 'un'+self.args.Target
        if self.args.Type == 'lists':
            self.request['type'] = 'movie'

        response = self.post_data()
        log.info('{}: {}'.format(movie.title, response))

        return

    def lists(self, args):

        # self.args.Target = 'items'
        # self.Action = '/{}'.format(self.args.ActionTaken)
        #
        # elif self.args.Type == 'lists':
        # 	if self.showCounter + self.movieCounter > self.batchSize:
        # 		self.movieEntries.extend(self.showEntries)
        # 		self.post_data(self.movieEntries)
        # 		self.movieCounter = 0
        # 		self.movieEntries = []
        # 		self.showCounter = 0
        # 		self.showEntries = []

        return

    def users(self, args):

        return


    def cleanup(self, args):

        #Cleanup Seen Shows
        trakt_user = User(self.args.TraktUserID)
        trakt_list = trakt_user.shows
        trakt_collected = trakt_user.show_collection

        trakt_list_names = {_item.title: _item for _item in trakt_list}
        trakt_collected_names = {_item.title: _item for _item in trakt_collected}

        trakt_unseen_needed = [trakt_list_names[x] for x in trakt_list_names if x not in trakt_collected_names]

        self.args.Type = 'show'
        self.args.Target = 'seen'
        self.args.ActionTaken = 'delete'

        for _item in trakt_unseen_needed:
            try:
                self.show(_item.title)
            except:
                pass

        #Cleanup Shows Watchlist
        trakt_watchlist = trakt_user.show_watchlist
        trakt_watchlist_names = {_item.title: _item for _item in trakt_watchlist}
        trakt_unwatchlist_needed = [trakt_collected_names[x] for x in trakt_watchlist_names if x in trakt_collected_names]

        self.args.Target = 'watchlist'
        self.args.ActionTaken = 'delete'

        for _item in trakt_unwatchlist_needed:
            try:
                self.show(_item.title)
            except:
                pass

        #Cleanup Seen Movies
        trakt_list = trakt_user.movies
        trakt_collected = trakt_user.movie_collection
#        trakt_collected = []
        trakt_list_names = {_item.title: _item for _item in trakt_list}
        trakt_collected_names = {_item.title: _item for _item in trakt_collected}

        trakt_unseen_needed = [trakt_list_names[x] for x in trakt_list_names if x not in trakt_collected_names]

        self.args.Type = 'movie'
        self.args.Target = 'seen'
        self.args.ActionTaken = 'delete'

        for _item in trakt_unseen_needed:
            try:
                self.movie(_item.title, _item.year)
            except:
                pass

        trakt_watchlist = trakt_user.movie_watchlist
        trakt_watchlist_names = {_item.title: _item for _item in trakt_watchlist}
        trakt_unwatchlist_needed = [trakt_collected_names[x] for x in trakt_watchlist_names if x in trakt_collected_names]

        self.args.Target = 'watchlist'
        self.args.ActionTaken = 'delete'

        for _item in trakt_unwatchlist_needed:
            try:
                self.movie(_item.title, _item.year)
            except:
                pass

        return

    def post_data(self):
        pydata = {'username': self.settings.TraktUserID, 'password': self.settings.TraktHashPswd}
        if self.args.Type == 'lists':
            pydata[self.args.Target] = self.request
            pydata['slug'] = self.args.listName
        else:
            pydata[self.args.Type+'s'] = [self.request]

        json_data = json.dumps(pydata)
        clen = len(json_data)
        _url = "http://api.trakt.tv/{}/{}/{}".format(self.args.Type, self.args.Target, self.settings.TraktAPIKey)
        req = urllib2.Request(_url, json_data, {'Content-Type': 'application/json', 'Content-Length': clen})
        f = urllib2.urlopen(req)
        response = f.read()
        f.close()
        return response

    def post_show(self):
        pydata = {'username': self.settings.TraktUserID, 'password': self.settings.TraktHashPswd}
        pydata.update(self.request)

        json_data = json.dumps(pydata)
        clen = len(json_data)
        _url = "http://api.trakt.tv/{}/{}/{}".format(self.args.Type, self.args.Target, self.settings.TraktAPIKey)
        req = urllib2.Request(_url, json_data, {'Content-Type': 'application/json', 'Content-Length': clen})
        f = urllib2.urlopen(req)
        response = f.read()
        f.close()
        return response

    def ReportTrakt(self):
        pydata = {'username': self.settings.TraktUserID, 'password': self.settings.TraktHashPswd}
        if self.args.Type == 'lists':
            pydata[self.args.Target] = self.request
            pydata['slug'] = self.args.listName
        else:
            pydata[self.args.Type+'s'] = self.request

        json_data = json.dumps(pydata)
        clen = len(json_data)
        _url = 'http://api.trakt.tv/user/list.json/{}/{}/{}'.format(self.settings.TraktAPIKey,
                                                                            self.settings.TraktUserID,
                                                                            self.args.listName)
        req = urllib2.Request(_url, json_data, {'Content-Type': 'application/json', 'Content-Length': clen})
        f = urllib2.urlopen(req)
        response = f.read()
        f.close()
        log.info(response)
        return


if __name__ == "__main__":

    logger.initialize()
    library = TestTrakt()

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
