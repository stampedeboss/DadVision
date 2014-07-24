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
from common.exceptions import UnexpectedErrorOccured, MovieNotFound
import trakt
from trakt.movies import Movie, updated_movies, genres, trending_movies, rate_movies, dismiss_recommendation, get_recommended_movies
# from trakt.tv import TVShow, TVSeason, TVEpisode, trending_shows, TraktRating, TraktStats, rate_shows, rate_episodes, genres, get_recommended_shows, dismiss_recommendation
# from trakt.calendar import PremiereCalendar, ShowCalendar, UserCalendar
# from trakt.people import Person
# from trakt.users import User, UserCalendar, UserList, Request
from fuzzywuzzy import fuzz
import logging
import os
import re
import sys
import time
import tmdb3
import unicodedata


__pgmname__ = 'trakt.tv.watchlist'
__version__ = '$Rev: 297 $'

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

class GetTrakt(Library):

    def __init__(self):
        log.trace('__init__ method: Started')

        super(GetTrakt, self).__init__()

        trakt_auth_group = self.options.parser.add_mutually_exclusive_group()
        trakt_auth_group.add_argument("--grumpy", dest="HostName", default='grumpy',
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

        trakt_list_area = self.options.parser.add_mutually_exclusive_group()
        trakt_list_area.add_argument("-m", "--movies", dest="TypeName",
            action="store_const", const="movies", default='movies',
            help="Make changes to Movies")
        trakt_list_area.add_argument("-s", "--series", dest="TypeName",
            action="store_const", const="shows",
            help="Make changes to Series")

        trakt.api_key = self.settings.TraktAPIKey
        trakt.authenticate(self.settings.TraktUserID, self.settings.TraktPassWord)
        tmdb3.set_key('587c13e576f991c0a653f783b290a065')
        tmdb3.set_cache(filename='tmdb3.cache')

        self.parse_year = re.compile(
            '''                                     # RegEx 6  YEAR
            (?P<MovieName>.*?)
            [\(\[]?[\._\ \-]?
            (?P<Year>(19|20)[0-9][0-9])
            [\)\]]?[\._ \-]?
            (?P<Keywords>.+)?
            ''',
            re.X | re.I)

        return

    @use_library_logging
    def Lookup(self):

        for _movie in os.listdir(self.settings.MoviesDir):
            if _movie == 'New':
                next

            try:
                _entry = list(tmdb3.searchMovieWithYear(_movie))[0]
                _movie_title = unicodedata.normalize('NFKD', _entry.title).encode("ascii", 'ignore')
                _movie_title = _movie_title.replace("&amp;", "&").replace("/", "_")
                _imdb_id = unicodedata.normalize('NFKD', _entry.imdb).encode("ascii", 'ignore')

                if _entry.releasedate:
                    _year = str(_entry.releasedate.year)

                log.info('{} ({}) - tmdb_id: {}  imdb_id: {}'.format(_movie_title,
                                                                     _year,
                                                                     str(_entry.id),
                                                                     _imdb_id))

    #            movie = Movie(_movie_title, _year, imdb_id=_imdb_id, tmdb_id=_entry.id)

                movie = Movie(_movie_title, _year)
                movie.remove_from_watchlist()
            except:
	            log.warn('Movie Not Found: {}'.format(_movie))

        return

    def _ignored(self, name):
        """ Check for ignored pathnames.
        """
        return any(fnmatch.fnmatch(name.lower(), pattern) for pattern in self.settings.ExcludeList)


if __name__ == "__main__":

    logger.initialize()
    library = GetTrakt()

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

    library.Lookup()
