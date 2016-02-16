#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Purpose:
Program to rename files associated with Movie Content

"""
import logging
import os
import re
import sys
import unicodedata
import fnmatch

import tmdb3

from library import Library
from common import logger
from common.exceptions import MovieNotFound, DictKeyError, InvalidArgumentType
from common.matching import matching


__pgmname__ = 'gettmdb'
__version__ = '$Rev: 341 $'

__author__ = "@author: AJ Reynolds"
__copyright__ = "@copyright: Copyright 2014, AJ Reynolds"
__license__ = "@license: GPL"
__email__ = "@contact: stampedeboss@gmail.com"

__maintainer__ = "@organization: AJ Reynolds"
__status__ = "@status: Development"
__credits__ = []

log = logging.getLogger(__pgmname__)


def uselibrarylogging(func):
    """

    :param func:
    :return:
    """

    def wrapper(self, *args, **kw):
        # Set the library name in the logger
        # from daddyvision.common import logger
        """

        :param self:
        :param args:
        :param kw:
        :return:
        """
        logger.set_library('movie')
        try:
            return func(self, *args, **kw)
        finally:
            logger.set_library('')

    return wrapper


class GetOutOfLoop(Exception):
    pass


def _ignored(name):
    """ Check for ignored pathnames.
    """
    rc = []
    if name == 'New': rc.append(True)
    rc.append(any(fnmatch.fnmatch(name.lower(), pattern) for pattern in library.settings.ExcludeList))
    rc.append(any(fnmatch.fnmatch(name.lower(), pattern) for pattern in library.settings.IgnoreGlob))
    return any(rc)


class TMDBInfo(Library):
    """

    :return:
    """

    def __init__(self):
        log.trace("INIT: =================================================")
        log.trace('TMDBInfo.__init__ method: Started')

        super(TMDBInfo, self).__init__()

        TMDB_group = self.options.parser.add_argument_group("Get TMDB Information Options", description=None)
        TMDB_group.add_argument("--movie", type=str, dest='MovieName', nargs='?')
        TMDB_group.add_argument("--year", type=int, dest='Year', nargs='?')

        tmdb3.set_key('587c13e576f991c0a653f783b290a065')
        tmdb3.set_cache(filename='tmdb3.cache')

        self._check_suffix = re.compile('^(?P<MovieName>.+?)[ \._\-\(]*?(?P<Year>[1|2][0|9]\d\d)(:P.*)?', re.VERBOSE)
        self._check_part = re.compile('^(?P<MovieName>.*\([1|2][0|9]\d\d\))[ \._\-\(]*(?P<Part>part.\d)[\)]?.*', re.IGNORECASE)

        return

    def retrieve_info(self, request):
        """

        :param request:
        :return: :raise MovieNotFound:
        """
        log.trace("=================================================")
        log.trace("retrieve_info method: request:{}".format(request))

        moviedetails = request
        if type(moviedetails) == dict:
            if 'MovieName' in moviedetails and moviedetails['MovieName'] is None:
                error_msg = 'LocaateMovie: Request Missing "MovieName" Value: {!s}'.format(moviedetails)
                log.trace(error_msg)
                raise DictKeyError(error_msg)
        else:
            error_msg = 'retrieve_info: Invalid object type, must be DICT, received: {}'.format(type(moviedetails))
            log.trace(error_msg)
            raise InvalidArgumentType(error_msg)

        if self.args.MovieName:
            moviedetails['MovieName'] = self.args.MovieName
        if self.args.Year:
            moviedetails['Year'] = int(self.args.Year)

        _suffix = self._check_suffix.match(moviedetails['MovieName'])
        if _suffix:
            moviedetails['MovieName'] = '{} '.format(_suffix.group('MovieName')).rstrip()
            if 'Year' not in moviedetails:
                moviedetails['Year'] = '{}'.format(_suffix.group('Year'))
            log.debug('retrieve_info: Request: Modified {}'.format(moviedetails))

        if 'Year' in moviedetails:
            moviedetails['Year'] = int(moviedetails['Year'])

        try:
            moviedetails = self._get_details(moviedetails)
        except MovieNotFound:
            raise

        return moviedetails

    def _get_details(self, moviedetails):
        log.trace("=================================================")
        log.trace("_get_details: Movie Details:{!s}".format(moviedetails))

        if 'Year' in moviedetails:
            _movie = '{MovieName} ({Year})'.format(**moviedetails)
            tmdb_details = list(tmdb3.searchMovieWithYear(_movie))
            try:
                moviedetails = self.review_entries(tmdb_details, moviedetails)
            except MovieNotFound:
                tmdb_details = list(tmdb3.searchMovie(moviedetails['MovieName']))
                if not tmdb_details:
                    raise
                try:
                    moviedetails = self.review_entries(tmdb_details, moviedetails)
                except MovieNotFound:
                    raise
        else:
            tmdb_details = list(tmdb3.searchMovie(moviedetails['MovieName']))
            moviedetails = self.review_entries(tmdb_details, moviedetails)

        return moviedetails

    @staticmethod
    def review_entries(tmdbDetails, moviedetails):

        """

        :param tmdbDetails:
        :param moviedetails:
        :param chkyear:
        :return: :raise MovieNotFound:
        """
        log.trace("=================================================")
        log.trace('Reviewing TMDB Details: {}'.format(tmdbDetails))

        if not tmdbDetails:
            raise MovieNotFound("Movie Not Found in TMDb: {}".format(moviedetails['MovieName']))

        _title = ''
        try:
            for _movie in tmdbDetails:
                _title = unicodedata.normalize('NFKD', _movie.title).encode("ascii", 'ignore')
                _title = _title.replace("&amp;", "&").replace("/", "_")

                if 'Year' in moviedetails:
                    if matching(_title.lower() + ' ' + str(_movie.releasedate.year),
                                 moviedetails['MovieName'].lower() + ' ' + str(moviedetails['Year'])):
                        moviedetails['MovieName'] = _title
                        raise GetOutOfLoop
                else:
                    if matching(_title.lower(), moviedetails['MovieName'].lower()):
                        moviedetails['MovieName'] = _title
                        raise GetOutOfLoop
                # Check Alternate Titles: list(AlternateTitle) alternate_titles
                _alt_title = _movie.alternate_titles
                for _alternate_title in _movie.alternate_titles:
                    _alt_title = unicodedata.normalize('NFKD', _alternate_title.title).encode("ascii", 'ignore')
                    _alt_title = _alt_title.replace("&amp;", "&").replace("/", "_")
                    log.trace('Check Alternate Titles: {}'.format(_alt_title.title))
                    if _alt_title and matching(_alt_title, moviedetails['MovieName']):
                        moviedetails['MovieName'] = _title
                        moviedetails['AltMovieName'] = _alt_title
                        raise GetOutOfLoop
            log.warn("Movie Not Found in TMDb: {}".format(moviedetails['MovieName']))
            raise MovieNotFound("Movie Not Found in TMDb: {}".format(moviedetails['MovieName']))
        except GetOutOfLoop:
            if _movie.releasedate:
                moviedetails['releasedate'] = _movie.releasedate
                if 'Year' in moviedetails:
                    if (-2 < (moviedetails['Year'] - _movie.releasedate.year) < 2):
                        moviedetails['Year'] = _movie.releasedate.year
                    elif 'AltMovieName' in moviedetails:
                        msg = "Movie Found with matching Alternate Title, Years too far apart: {} - {}/{}".format(
                            moviedetails['FileName'],
                            moviedetails['MovieName'],
                            _movie.releasedate.year)
                        log.warning(msg)
                        raise MovieNotFound(msg)
                    else:
                        msg = "Movie name found, Years too far apart: {} - {}/{}".format(moviedetails['MovieName'],
                                                                                         moviedetails['Year'],
                                                                                         _movie.releasedate.year)
                        log.warning(msg)
                        raise MovieNotFound(msg)
                else:
                    moviedetails['Year'] = _movie.releasedate.year

        moviedetails['tmdb_id'] = _movie.id
        moviedetails['imdb_id'] = _movie.imdb


        log.trace("Movie Located in TMDB")
        return moviedetails

    def check_movie_names(self, pathname):
        log.trace("=================================================")
        log.trace("check_movie_names method: pathname:{}".format(pathname))

        pathname = os.path.abspath(pathname)

        if os.path.isfile(pathname):
            log.debug("-----------------------------------------------")
            log.debug("Movie Directory: %s" % os.path.split(pathname)[0])
            log.debug("Movie Filename:  %s" % os.path.split(pathname)[1])
            self.check_file(pathname)
        elif os.path.isdir(pathname):
            log.debug("-----------------------------------------------")
            log.debug("Movie Directory: %s" % pathname)
            for _root, _dirs, _files in os.walk(os.path.abspath(pathname)):
                _dirs.sort()
                for _dir in _dirs[:]:
                    # Process Enbedded Directories
                    if _ignored(_dir):
                        _dirs.remove(_dir)

                _files.sort()
                for _file in _files:
                    # _path_name = os.path.join(_root, _file)
                    log.trace("Movie Filename: %s" % _file)
                    if _ignored(_file):
                        continue
                    self.check_file(_root, _file)
        return None

    def check_file(self, directory, filename):
        pathname = os.path.join(directory, filename)
        try:
            # Get Directory Details
            _dir_details = parser.getFileDetails(os.path.join(directory, directory + ".mkv"))
            _dir_answer = library.retrieve_info(_dir_details)

            # Get File Details
            _file_details = parser.getFileDetails(filename)
            _file_answer = library.retrieve_info(_file_details)
        except Exception:
            log.error('MovieNotFound {}'.format(os.path.join(directory, filename)))
            # an_error = traceback.format_exc(1)
            #			log.error(traceback.format_exception_only(type(an_error), an_error)[-1])
            #			print 'Exception in user code:'
            #			print '-'*60
            #			traceback.print_exc(file=sys.stdout)
            #			print '-'*60
            sys.exc_clear()
            return

        if _dir_details['Year'] != _dir_answer['Year']:
            log.info('Rename Required: {} (Year) (Current) - Directory'.format(os.path.basename(directory)))
            log.info('                 {MovieName} ({Year})'.format(**_dir_answer))

        if os.path.basename(directory) != '{MovieName} ({Year})'.format(**_dir_answer):
            log.info('Rename Required: {} (Current) - Directory'.format(os.path.basename(directory)))
            log.info('                 {MovieName} ({Year})'.format(**_dir_answer))

        if _file_details['Year'] != _file_answer['Year']:
            log.info('Rename Required: {} (Year) (Current)'.format(filename))
            log.info('                 {MovieName} ({Year})'.format(**_file_answer))

        test1 = os.path.splitext(filename)[0]
        test2 = '{MovieName} ({Year})'.format(**_file_answer)
        _part = self._check_part.match(test1)
        if _part:
            test1 = _part.group('MovieName').rstrip()
        if test1 != test2:
            log.info('Rename Required: {} (Current)'.format(filename))
            log.info('                 {MovieName} ({Year})'.format(**_file_answer))

        s = pathname.decode('ascii', 'ignore')
        if s != pathname:
            log.warning('INVALID CHARs: {} vs {}'.format(pathname - s, pathname))

# log.info(_dir_answer)


if __name__ == "__main__":

    logger.initialize()
    log.trace("MAIN: -------------------------------------------------")
    from library.movie.fileparser import FileParser
    from library.movie.rename import RenameMovie

    library = TMDBInfo()
    parser = FileParser()
    rename = RenameMovie()
    __main__group = library.options.parser.add_argument_group("Get TMDB Information Options", description=None)
    __main__group.add_argument("--Error-Log", dest="errorlog", action="store_true", default=False,
                                help="Create Seperate Log for Errors")

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

    logger.start(log_file, log_level, timed=True, errorlog=library.args.errorlog)
    library.settings.IgnoreGlob.extend(['*.ifo', '*.bup', '*.vob'])
    _MovieDetails = {}
    _answer = ''

    if library.args.Year:
        _MovieDetails['Year'] = library.args.Year
    if library.args.MovieName:
        _MovieDetails['MovieName'] = library.args.MovieName
        _answer = library.retrieve_info(_MovieDetails)
        log.info(_answer)
        sys.exit(0)
    elif len(library.args.library) > 0 and 'MovieName' not in _MovieDetails:
        for pathname in library.args.library:
            library.check_movie_names(pathname)
