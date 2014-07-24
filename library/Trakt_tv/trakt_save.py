#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Author: AJ Reynolds
Date: 07-19-2014
Purpose:
Program to add entries to the TRAKT database from a list of entries in a file

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
from common.cmdoptions import CmdOptions
import base64
import logging
import os
import re
import sys
import urllib2
import json
import time
import hashlib

__pgmname__ = os.path.basename(sys.argv[0])
__version__ = '$Rev: 297 $'

__author__ = "@author: AJ Reynolds"
__copyright__ = "@copyright: 2014, AJ Reynolds"
__credits__ = []
__license__ = "@license: GPL"

__maintainer__ = "AJ Reynolds"
__email__ = "@contact: stampedeboss@gmail.com"
__status__ = "Development"

__date__ = '2014-07-1925'
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

user_info = {
              'grumpy' : {'UserName' : 'stampedeboss',
                      'PassWord' : '0husKi3s',
                      'Base64Key' : base64.encodestring('stampedeboss:0husKi3s'),
                      'APIKey' : '895ba4c88694e9ae8543afb2fac89d2f'},
              'tigger' : {'UserName' : 'alyr0923',
                      'PassWord' : '09sb44bbs',
                      'Base64Key' : base64.encodestring('alyr0923:09sb44bb'),
                      'APIKey' : '82863444689db8620d5d16e677bf99ac'},
              'goofy' : {'UserName' : 'alyr0923',
                      'PassWord' : '09sb44bbs',
                      'Base64Key' : base64.encodestring('kimr9999:beatles1964'),
                      'APIKey' : '82863444689db8620d5d16e677bf99ac'}
      }

def use_library_logging(func):

    def wrapper(self, *args, **kw):
        # Set the library name in the logger
        logger.set_library('trakt')
        try:
            return func(self, *args, **kw)
        finally:
            logger.set_library('')

    return wrapper

class Trakt(Library):

    def __init__(self):
        log.trace('__init__ method: Started')

        super(Trakt, self).__init__()

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

        trakt_runtime_group = self.options.parser.add_argument_group("", description=None)
        trakt_runtime_group.add_argument("--dry-run", dest="DryRun",
            action="store_true", default=False,
            help="Don't do anything, just show what would happen")

        trakt_subparsers = self.options.parser.add_subparsers(title='subcommands',
                                                              dest="CommandName",
                                                              description='valid subcommands',
                                                  help='additional help')

        trakt_list = trakt_subparsers.add_parser("list")
        trakt_list_area = trakt_list.add_mutually_exclusive_group()
        trakt_list_area.add_argument("--collection", dest="AreaName", default='collection',
            action="store_const", const="collection",
            help="Entires in Collection")
        trakt_list_area.add_argument("--all", dest="AreaName",
            action="store_const", const="all", default="library",
            help="All Entries regardless of status")
        trakt_list_area.add_argument("--watched", dest="AreaName",
            action="store_const", const="watched",
            help="Entries that have been Watched")
        trakt_list_area.add_argument("--watchlist", dest="AreaName",
            action="store_const", const="watchlist",
            help="Entries on the WatchList")

        trakt_list_func = trakt_list.add_mutually_exclusive_group()
        trakt_list_func.add_argument("-a", "--add", dest="FunctionName",
            action="store_const", const="add",
            help="Add Entries to the Library/List")
        trakt_list_func.add_argument("-r", "--remove", dest="FunctionName",
            action="store_const", const="remove",
            help="Remove Entries from the request Library/List")
        trakt_list_func.add_argument("-c", "--copy", dest="FunctionName",
            action="store_const", const="copy",
            help="Copy Entries to the Library/List")


        trakt_movies = trakt_subparsers.add_parser("movies")
        trakt_movies_func = trakt_movies.add_mutually_exclusive_group()
        trakt_movies_func.add_argument("-a", "--add", dest="FunctionName",
            action="store_const", const="add",
            help="Add Entries to the Library/List")
        trakt_movies_func.add_argument("-r", "--remove", dest="FunctionName",
            action="store_const", const="remove",
            help="Remove Entries from the request Library/List")
        trakt_movies_func.add_argument("-c", "--copy", dest="FunctionName",
            action="store_const", const="copy",
            help="Copy Entries to the Library/List")

        trakt_movies_lib = trakt_movies.add_mutually_exclusive_group()
        trakt_movies_lib.add_argument("--library", dest="ListName",
            action="store_const", const="library",
            help="Entries on the WatchList")
        trakt_movies_lib.add_argument("-w", "--watchlist", dest="LibName",
            action="store_const", const="watchlist",
            help="Entries on the WatchList")
        trakt_movies_lib.add_argument("--seen", dest="ListName",
            action="store_const", const="seen",
            help="Seen Entires")


        trakt_series = trakt_subparsers.add_parser("series")
        trakt_series_func = trakt_series.add_mutually_exclusive_group()
        trakt_series_func.add_argument("-a", "--add", dest="FunctionName",
            action="store_const", const="add",
            help="Add Entries to the Library/List")
        trakt_series_func.add_argument("-r", "--remove", dest="FunctionName",
            action="store_const", const="remove",
            help="Remove Entries from the request Library/List")
        trakt_series_func.add_argument("-c", "--copy", dest="FunctionName",
            action="store_const", const="copy",
            help="Copy Entries to the Library/List")

        trakt_series_Lib = trakt_series.add_mutually_exclusive_group()
        trakt_series_Lib.add_argument("--library", dest="ListName",
            action="store_const", const="library",
            help="Entries on the WatchList")
        trakt_series_Lib.add_argument("-w", "--watchlist", dest="LibName",
            action="store_const", const="watchlist",
            help="Entries on the WatchList")
        trakt_series_Lib.add_argument("--seen", dest="ListName",
            action="store_const", const="seen",
            help="Seen Entires")

        self._sources = 'brrip|r5|dvdrip|src|dvdscr|pvvrip|cam|telesync| ts |wp|workprint|hdweb|bdrip|bluray'
        self._codecs = 'xvid|x264|264|h264|divx|aac|mp3|ac3|dts'
        self._resolutions = 'PAL|NTSC|720p|1080p|1080i|720|1080'
        self._extentions = 'mkv|avi|mp4|m4v|mov'

        self._watchlist = 0
        self._formatting=['title','disk','year','source','codec']

        return

    @use_library_logging
    def Copy(self):
        base64string = base64.encodestring(self.args.UserName + ":0husKi3s" )
        req = urllib2.Request("http://api.trakt.tv/user/library/{}/{}.json/{}/{}".format(self.args.LibName,
                                                                                         self.args.ListName,
                                                                                         self.args.APIKey,
                                                                                         self.args.UserName))
        req.add_header("Authorization", "Basic {}".format(base64string))
        response = json.load(urllib2.urlopen(req))
        for entry in response:
            log.info(entry['title'])

        return

    @use_library_logging
    def AddMovie(self, pathname):

        fin = open(pathname, 'r')
        fout_unknown = open(pathname+".unknown", 'w')
        imdb_id_list = []

        for name in fin:
            d = self.get_data(name)

            _year_msg = ''
            if 'year' in d:
                _year_msg = " " + d['year']
                imdbinfo = self.get_imdb_info(d['cleanname'],d['year'])
            else:
                imdbinfo = self.get_imdb_info(d['cleanname'])

            if imdbinfo['Response'] != 'False':
                imdb_id = imdbinfo['imdbID']
                imdb_title = imdbinfo['Title']
                imdb_year = imdbinfo['Year']
                log.info("{}{}:  imdb: {} {} {}".format(d['cleanname'], _year_msg, imdb_title, imdb_year ,imdb_id))

                imdb_id_list.append({'imdb_id':imdb_id})

                # send batch of 100 IMDB IDs
                if len(imdb_id_list) >= 10:
                    self.send_data(imdb_id_list)
                    imdb_id_list = []
            else:
                # write out any names that can't be found in imdb so that you can fix them
                log.info('{}{}: imdb nothing found'.format(d['cleanname'], _year_msg))
                fout_unknown.write(name.strip()+'\n')
            time.sleep(1)

        # send unset IDs in list
        if len(imdb_id_list) > 0:
            self.send_data(imdb_id_list)

        return


    @use_library_logging
    def UpdateLibrary(self, pathname):

        fin = open(pathname, 'r')
        fout_unknown = open(pathname+".unknown", 'w')
        imdb_id_list = []

        for name in fin:
            d = self.get_data(name)

            _year_msg = ''
            if 'year' in d:
                _year_msg = " " + d['year']
                imdbinfo = self.get_imdb_info(d['cleanname'],d['year'])
            else:
                imdbinfo = self.get_imdb_info(d['cleanname'])

            if imdbinfo['Response'] != 'False':
                imdb_id = imdbinfo['imdbID']
                imdb_title = imdbinfo['Title']
                imdb_year = imdbinfo['Year']
                log.info("{}{}:  imdb: {} {} {}".format(d['cleanname'], _year_msg, imdb_title, imdb_year ,imdb_id))

                imdb_id_list.append({'imdb_id':imdb_id})

                # send batch of 100 IMDB IDs
                if len(imdb_id_list) >= 10:
                    self.send_data(imdb_id_list)
                    imdb_id_list = []
            else:
                # write out any names that can't be found in imdb so that you can fix them
                log.info('{}{}: imdb nothing found'.format(d['cleanname'], _year_msg))
                fout_unknown.write(name.strip()+'\n')
            time.sleep(1)

        # send unset IDs in list
        if len(imdb_id_list) > 0:
            self.send_data(imdb_id_list)

        return

    def get_data(self, filename):

        d = dict()

        log.verbose(filename.strip())

        filename = re.sub(self._extentions, '',  filename, flags=re.IGNORECASE)
        result = re.search('\d{4}', filename)
        if result and result.group() != 1080:
            d['year'] = result.group()
        # filename = re.sub('_', ' ', filename, flags=re.IGNORECASE)
        # filename = re.sub('\.', ' ', filename, flags=re.IGNORECASE)
        # filename = re.sub('-', ' ', filename, flags=re.IGNORECASE)
        # filename = re.sub(',', ' ', filename, flags=re.IGNORECASE)
        # filename = re.sub('"', ' ', filename, flags=re.IGNORECASE)
        # filename = re.sub('\s+', ' ', filename, flags=re.IGNORECASE)
        # filename = re.sub('('+self._sources+').*', '', filename, flags=re.IGNORECASE)
        # filename = re.sub('('+self._codecs+').*', '', filename, flags=re.IGNORECASE)
        # filename = re.sub('('+self._resolutions+').*', '', filename, flags=re.IGNORECASE)
        filename = re.sub('\(\d{4}\)', '', filename, flags=re.IGNORECASE)
        # filename = re.sub('\[.*', '', filename, flags=re.IGNORECASE)
        # filename = re.sub('\(.*', '', filename, flags=re.IGNORECASE)
        # filename = re.sub('\{.*', '', filename, flags=re.IGNORECASE)

        filename = filename.strip()
        d['cleanname'] = filename

        return d

    def send_data_movie(self, imdb_id_data):
        pydata = {
                'username':self.args.UserName,
                'password':self.args.PassWord,
                'movies': imdb_id_data
                }

        json_data = json.dumps(pydata)
        clen = len(json_data)
        log.verbose(json_data)

        req = urllib2.Request("https://api.trakt.tv/self.args.LibName/self.args.ListName/"+self.args.APIKey, json_data, {'Content-Type': 'application/json', 'Content-Length': clen})

        f = urllib2.urlopen(req)
        response = f.read()
        f.close()
        log.info(response)

        return

    def get_imdb_info(self, title, year=None):
        if year != None:
            s='http://omdbapi.com/?t='+title+'&y='+str(year)
        else:
            s='http://omdbapi.com/?t='+title
        url = urllib2.urlopen(s.replace(' ','+'))
        data = url.read()
        res = json.loads(data)

        return res


if __name__ == "__main__":

    logger.initialize()
    library = Trakt()

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

    library.args.UserName = user_info[library.args.UserID]['UserName']
    library.args.PassWord = hashlib.sha1(user_info[library.args.HostName]['PassWord']).hexdigest()
    library.args.Base64Key = user_info[library.args.UserID]['Base64Key']
    library.args.APIKey = user_info[library.args.UserID]['APIKey']

    if Library.args.FunctionName == "add":
        if len(library.args.library) > 0:
            for entry in library.args.library:
                library.UpdateLibrary(entry)
    elif Library.args.FunctionName == "copy":
        library.Copy()
    elif Library.args.FunctionName == "remove":
        if len(library.args.library) > 0:
            for entry in library.args.library:
                library.UpdateLibrary(entry)
