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
import re
import sys
import tmdb3
import unicodedata
import fnmatch
import urllib2
import json

# import trakt
# from trakt.movies import Movie
# from trakt.users import User, UserList
# from trakt import BaseAPI
#from trakt.tv import TVShow, TVSeason, TVEpisode, trending_shows, TraktRating, TraktStats, rate_shows, rate_episodes, genres, get_recommended_shows, dismiss_recommendation
#from trakt.traktcalendar import PremiereCalendar, ShowCalendar, UserCalendar
#from trakt.people import Person
#from fuzzywuzzy import fuzz


__pgmname__ = 'Trakt_tv.manage'
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

def use_library_logging(func):

    def wrapper(self, *args, **kw):
        # Set the library name in the logger
        logger.set_library('trakt')
        try:
            return func(self, *args, **kw)
        finally:
            logger.set_library('')

    return wrapper


class ManageTrakt(Library):

    def __init__(self):
        log.trace('__init__ method: Started')

        super(ManageTrakt, self).__init__()

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
            help="Make changes to watchlist")

        # trakt.api_key = self.settings.TraktAPIKey
        # trakt.authenticate(self.settings.TraktUserID, self.settings.TraktPassWord)
        tmdb3.set_key('587c13e576f991c0a653f783b290a065')
        tmdb3.set_cache(filename='tmdb3.cache')
        self.db = api.TVDB("959D8E76B796A1FB")

        self.movieEntries =[]
        self.movieCounter = 0

        self.showEntries =[]
        self.showCounter = 0

        self.batchSize = 50

        self.Re_Parse = re.compile(
            '''                                     # RegEx 6  YEAR
            (?P<MovieName>.*?)
            [\._ \-][\(\[]?
            (?P<Year>(19|20)[0-9][0-9])
            [\)\]]?[\._ \-]?
            (?P<Keywords>.+)?$
            ''',
            re.X | re.I)

        return

    @use_library_logging
    def ProcessRequest(self, request):

        self._processOptions()

        if request == 'listdir':
            if self.args.Type == 'show':
                _target_dir = self.settings.SeriesDir
            elif self.args.Type == 'movie':
                _target_dir = self.settings.MoviesDir
            else:
                log.warn("ListDir can only be used with Shows and Movies, defaulting to Shows")
                _target_dir = self.settings.SeriesDir

            for _entry in sorted(os.listdir(_target_dir)):
                if self._ignored(_entry):
                    next
                self.ProcessEntry(_entry)

        elif request == 'file':
            for _input_file in self.args.library:
                if os.path.exists(_input_file):
                    with open(_input_file, 'r') as _file_in:
                        for _entry in _file_in:
                            _entry = _entry.rstrip()
                            if self._ignored(_entry):
                                next
                            self.ProcessEntry(_entry)
                else:
                    log.error('Requested File Does Not Exist: {}'.format(_input_file))

        if len(self.movieEntries) > 0:
            self.ProcessEntry('Junk', final=True)

    def ProcessEntry(self, entry, final=False):

        if final:
            self.movieCounter = self.batchSize + 1
            self.showCounter = self.batchSize + 1
            self.ProcessBatch()
            return

        try:
            _tvdb_id = None
            _tvdb_id = self.settings.TvdbIdList[entry]
            try:
                _details = self.GetSeriesDetails(entry, _tvdb_id)
            except SeriesNotFound:
                log.warn('Series Not Found: {} tvdbid: {}'.format(entry, _tvdb_id))
                return
        except KeyError:
            try:
                _details = self.GetMovieDetails(entry)
            except MovieNotFound:
                log.warn('Movie Not Found: {}'.format(entry))
                return

        log.info('{}:  {}'.format('Queued', _details))
#        log.info('{}:  {Title} ({Year}) - tmdb_id: {TMDB_ID}  imdb_id: {IMDB_ID}'.format('Queued', **_details))
        self.ProcessBatch()

        return

    def ProcessBatch(self):
        if self.args.Type == 'movie':
            if self.movieCounter >= self.batchSize:
                self.post_data(self.movieEntries)
                self.movieEntries = []
                self.movieCounter = 0
        elif self.args.Type == 'show':
            if self.showCounter >= self.batchSize:
                if self.args.Target in ['watchlist', 'unwatchlist']:
                    self.post_data(self.showEntries)
                else:
                    self.post_show(self.showEntries)
                self.showEntries = []
                self.showCounter = 0
        elif self.args.Type == 'lists':
            if self.showCounter + self.movieCounter > self.batchSize:
                self.movieEntries.extend(self.showEntries)
                self.post_data(self.movieEntries)
                self.movieCounter = 0
                self.movieEntries = []
                self.showCounter = 0
                self.showEntries = []
        return

    def GetMovieDetails(self, entry):

        try:
            _tmdbDetails = list(tmdb3.searchMovieWithYear(entry))[0]
        except IndexError:
            try:
                _tmdbDetails = self.Re_Parse.match(entry)
                if _tmdbDetails:
                    _tmdbDetails = list(tmdb3.searchMovie(_tmdbDetails.group('MovieName')))
                    if len(_tmdbDetails) > 0:
                        _tmdbDetails = _tmdbDetails[0]
                    else:
                        raise MovieNotFound('Movie Not Found: {}'.format(entry))
                else:
                    raise MovieNotFound('Movie Not Found: {}'.format(entry))
            except MovieNotFound:
                log.warn('Movie Not Found: {}'.format(entry))
                raise MovieNotFound('Movie Not Found: {}'.format(entry))

        _details = {}
        _details['imdb_id'] = unicodedata.normalize('NFKD', _tmdbDetails.imdb).encode("ascii", 'ignore')

        # _details['title'] = unicodedata.normalize('NFKD', _tmdbDetails.title).encode("ascii", 'ignore')
        # _details['title'] = _details['title'].replace("&amp;", "&").replace("/", "_")
        #
        # if _tmdbDetails.releasedate:
        #     _details['year'] = str(_tmdbDetails.releasedate.year)
        # else:
        #     _details['tear'] = None

        if self.args.Target == 'lists':
            _details['type'] = 'movie'

        self.movieCounter += 1
        self.movieEntries.append(_details)

        return _details

    def GetSeriesDetails(self, entry, tvdb_id):
        try:
            _tvdbDetails = self.db.get_series(tvdb_id, "en" )
        except:
            log.warn('Series Not Found: {}'.format(entry))
            raise SeriesNotFound('tvdb - Series Not Found: {} tvdbid: {}'.format(entry, tvdb_id))

        _details = {}
        _details['tvdb_id'] = _tvdbDetails.id

        # _details['title'] = unicodedata.normalize('NFKD', _tvdbDetails.SeriesName).encode("ascii", 'ignore')
        # _details['title'] = _details['title'].replace("&amp;", "&").replace("/", "_")
        # _details['imdb_id'] = unicodedata.normalize('NFKD', _tvdbDetails.IMDB_ID).encode("ascii", 'ignore')

        # if _tvdbDetails.FirstAired:
        #     _details['year'] = str(_tvdbDetails.FirstAired.year)
        # else:
        #     _details['year'] = None

        if self.args.Target == 'lists':
            _details['type'] = 'show'

        self.showCounter += 1
        self.showEntries.append(_details)

        return _details

    def post_data(self, entry_data):
        pydata = {'username': self.settings.TraktUserID, 'password': self.settings.TraktHashPswd}
        if self.args.Type == 'lists':
            pydata[self.args.Target] = entry_data
            pydata['slug'] = self.args.listName
        else:
            pydata[self.args.Type+'s'] = entry_data

        json_data = json.dumps(pydata)
        clen = len(json_data)
        _url = "http://api.trakt.tv/{}/{}{}/{}".format(self.args.Type, self.args.Target, self.Action, self.settings.TraktAPIKey)
        req = urllib2.Request(_url, json_data, {'Content-Type': 'application/json', 'Content-Length': clen})
        f = urllib2.urlopen(req)
        response = f.read()
        f.close()
        log.info(response)
        return

    def post_show(self, entry_data):
        for entry in entry_data:
            pydata = {'username': self.settings.TraktUserID, 'password': self.settings.TraktHashPswd}
            pydata.update(entry)

            json_data = json.dumps(pydata)
            clen = len(json_data)
            _url = "http://api.trakt.tv/{}/{}{}/{}".format(self.args.Type, self.args.Target, self.Action, self.settings.TraktAPIKey)
            req = urllib2.Request(_url, json_data, {'Content-Type': 'application/json', 'Content-Length': clen})
            f = urllib2.urlopen(req)
            response = f.read()
            f.close()
            log.info(response)
        return

    def _processOptions(self):

        self.settings.ReloadHostConfig(self.args.HostName)
#        trakt.api_key = self.settings.TraktAPIKey
#        trakt.authenticate(self.settings.TraktUserID, self.settings.TraktPassWord)

        if self.args.Type == 'lists':
            self.args.Target = 'items'
            self.Action = '/{}'.format(self.args.ActionTaken)
        else:
            self.Action = ''
            if self.args.ActionTaken == 'delete':
                self.args.Target = 'un'+self.args.Target

    def _ignored(self, name):
        """ Check for ignored pathnames.
        """
        return any(fnmatch.fnmatch(name.lower(), pattern) for pattern in self.settings.ExcludeList)


if __name__ == "__main__":

    logger.initialize()
    library = ManageTrakt()

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

    logger.start(log_file, log_level, timed=False, error=True)

    # whitelist = __pgmname__.split('.')
    # whitelist = 'watchlist'
    # whitelist_handlers = ['Console']
    # for handler in logging.root.handlers:
    #     if handler.name in whitelist_handlers:
    #         handler.addFilter(logger.Whitelist(whitelist))

    if library.args.library:
        library.ProcessRequest('file')
    else:
        library.ProcessRequest('listdir')
