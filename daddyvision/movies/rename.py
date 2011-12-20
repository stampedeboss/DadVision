#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Author: AJ Reynolds
Date: 12-11-2010
Purpose:
Program to rename movies files

"""
from daddyvision.common.exceptions import InvalidFilename, RegxSelectionError, ConfigValueError
from daddyvision.common.exceptions import DataRetrievalError, EpisodeNotFound, SeriesNotFound
from daddyvision.movies.fileparser import FileParser
from daddyvision.common import logger
from daddyvision.series.episodeinfo import EpisodeDetails
from logging import INFO, WARNING, ERROR, DEBUG
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import re
import os
import sys
import filecmp
import fnmatch
import logging
import datetime
import time
import unicodedata
import tmdb
from pIMDB import pIMDB

'''
import tmdb

    tmdb.configure('587c13e576f991c0a653f783b290a065')
    movie = tmdb.search("Fight Club")
    #movie[0].keys()
    movie[0]["rating"]
    or
    movie = tmdb.tmdb("Fight Club")
    rating = movie.getRating()
    language = movie.getLanguage()

    imdb lookup:
    import tmdb
    imdb_movie = tmdb.imdb(title="Fight Club") # title = "Fight Club" or id=tt30330 ->imdb_idb
    rating = imdb_movie.getRating()
    runtime = imdb_movie.getRuntime()

tmdb.tmdb methods:
    > getRating()
    > getVotes()
    > getName()
    > getLanguage()
    > getCertification()
    > getUrl()
    > getOverview()
    > getPopularity()
    > getOriginalName()
    > getLastModified()
    > getImdbId()
    > getReleased()
    > getScore()
    > getAdult()
    > getVersion()
    > getTranslated()
    > getType()
    > getId()
    > getAlternativeName()
    > getPoster()
    > getBackdrop()

tmdb.imdb methods
    > getRuntime()
    > getCategories()
    > getRating()
    > getVotes()
    > getName()
    > getLanguage()
    > getCertification()
    > getUrl()
    > getOverview()
    > getPopularity()
    > getOriginalName()
    > getLastModified()
    > getImdbId()
    > getReleased()
    > getAdult()
    > getVersion()
    > getTranslated()
    > getType()
    > getId()
    > getAlternativeName()
    > getPoster()
    > getBackdrop()
'''


__author__ = "AJ Reynolds"
__copyright__ = "Copyright 2011, AJ Reynolds"
__credits__ = []
__license__ = "GPL"

__pgmname__ = 'rename'
__version__ = '$Rev$'

__maintainer__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"
__status__ = "Development"

log = logging.getLogger(__pgmname__)

def useLibraryLogging(func):

    def wrapper(self, *args, **kw):
        # Set the library name in the logger
        from daddyvision.common import logger
        logger.set_library('movie')
        try:
            return func(self, *args, **kw)
        finally:
            logger.set_library('')

    return wrapper

class Rename(object):

    def __init__(self, config):
        log.trace('__init__ method: Started')

        self.config = config
        self.parser = FileParser(self.config)
        self.regex_repack = re.compile('^.*(repack|proper).*$', re.IGNORECASE)
        self.regex_NewDir = re.compile('^{}.*$'.format(os.path.join(os.path.split(self.config.MoviesDir)[0], self.config.NewDir), re.IGNORECASE))
        self.regex_MoviesDir = re.compile('^{}.*$'.format(self.config.MoviesDir), re.IGNORECASE)
        tmdb.configure('587c13e576f991c0a653f783b290a065')
        return

    @useLibraryLogging
    def rename(self, pathname):
        log.trace("rename method: pathname:{}".format(pathname))

        if os.path.isfile(pathname):
            log.debug("-----------------------------------------------")
            log.debug("Movie Directory: %s" % os.path.split(pathname)[0])
            log.debug("Movie Filename:  %s" % os.path.split(pathname)[1])

            self._rename_file(pathname)

        elif os.path.isdir(pathname):
            for _root, _dirs, _files in os.walk(os.path.abspath(pathname),followlinks=False):
                for _dir in _dirs[:]:
                    if _dir == 'VIDEO_TS':
                        self._rename_directory(_root)
                        _dirs.remove(_dir)
                    if self._ignored(_dir):
                        _dirs.remove(_dir)
                        log.debug("Ignoring %r" % os.path.join(_root, _dir))
                _files.sort()
                for _file in _files:
                    _path_name = os.path.join(_root, _file)
                    log.debug("-----------------------------------------------")
                    log.debug("Filename: %s" % _file)
                    _file_details = self.parser.getFileDetails(_path_name)

                    if _file_details['Ext'] not in self.config.MediaExt:
                        if os.path.split(_root)[0] != self.config.MoviesDir and os.path.basename(_root) != 'extrathumbs':
                            os.remove(_file_details['FileName'])
                            self._del_dir(_file_details['FileName'])
                    else:
                        _fq_new_file_name = self._rename_file(_file_details)
                        
        if self.regex_NewDir.match(pathname):
            _base_dir = os.path.join(os.path.split(self.config.MoviesDir)[0],self.config.NewDir)
        elif self.regex_MoviesDir.match(pathname):
            _base_dir = self.config.MoviesDir
        else:
            _base_dir = os.path.split(pathname)[0]
        for _root, _dirs, _files in os.walk(_base_dir, topdown=False, followlinks=False):
            for _name in _dirs:
                _dir_name = os.path.join(_root,_name)
                try:
                    if not os.listdir(_dir_name):
                        self._del_dir(_dir_name, file=False)
                except:
                    continue
        log.info('Run Complete')
        return None

    def _rename_file(self, _file_details):
        log.trace("_rename_file method: pathname:{!s}".format(_file_details))

        _movie = tmdb.tmdb(_file_details['MovieName'])

        _num_of_movies = _movie.getTotal()
        _movie_titles = []
        
        for i in range(0, (_num_of_movies)):
            _movie_titles.append(_movie.getName(i))

        if _num_of_movies > 0:
            _choice = process.extractOne(_file_details['MovieName'], _movie_titles)
            if _choice[1] > 85:
                _index = _movie_titles.index(_choice[0])
                _file_details['MovieName'] = _choice[_index]
                if 'Year' not in _file_details:
                    _file_details['Year'] = int(_movie.getReleased(_index)[0:4])
        else:
            pass

        if 'Trailer' in _file_details:
            _trailer = '-trailer'
        else:
            _trailer = ''

        if 'Year' in _file_details:
            _new_dir = '%s (%s)' % (_file_details['MovieName'], _file_details['Year'])
            _new_file_name = '%s (%s)%s.%s' % (_file_details['MovieName'], _file_details['Year'], _trailer,_file_details['Ext'])
        else:
            _new_dir = '%s' % (_file_details['MovieName'])
            _new_file_name = '%s%s.%s' % (_file_details['MovieName'], _trailer,_file_details['Ext'])

        _fq_new_file_name = os.path.join(self.config.MoviesDir, _new_dir, _new_file_name)

        _repack  = self.regex_repack.search(_file_details['FileName'])

        if os.path.exists(_fq_new_file_name):
            if _repack:
                os.remove(_fq_new_file_name)
            elif filecmp.cmp(_fq_new_file_name, _file_details['FileName']):
                if _fq_new_file_name != _file_details['FileName']:
                    log.info("Deleting %r, already at destination!" % (os.path.split(_file_details['FileName'])[1],))
                    os.remove(_file_details['FileName'])
                    self._del_dir(_file_details['FileName'])
                    return
                else:
                    log.info("Skipping: file: %r, at already at destination!" % (os.path.split(_file_details['FileName'])[1],))
                    return

        log.info('Renaming Movie: %s to %s' % (os.path.basename(_file_details['FileName']), _new_file_name))
        try:
            if not os.path.exists(os.path.split(_fq_new_file_name)[0]):
                os.makedirs(os.path.split(_fq_new_file_name)[0])
                if os.getgid() == 0:
                    os.chown(os.path.split(_fq_new_file_name)[0], 1000, 100)
            os.rename(_file_details['FileName'], _fq_new_file_name)
            log.info("Successfully Renamed: %s" % _fq_new_file_name)
            self._del_dir(_file_details['FileName'])
        except OSError, exc:
            log.error("Skipping, Unable to Rename File: %s" % _file_details['FileName'])
            log.error("Unexpected error: %s" % exc)

        return _fq_new_file_name

    def _rename_directory(self, dir):
        log.trace("_rename_dir method: pathname:{!s}".format(dir))

        _directory_details = self.parser.getFileDetails(dir+'.avi')
        _directory_details['FileName'] = dir 

        _movie = tmdb.tmdb(_directory_details['MovieName'])
        _num_of_movies = _movie.getTotal()
        _movie_titles = []
        
        for i in range(0, (_num_of_movies)):
            _movie_titles.append(_movie.getName(i))
            
        if _num_of_movies > 0:
            _choice = process.extractOne(_directory_details['MovieName'], _movie_titles)
            if _choice[1] > 85:
                _index = _movie_titles.index(_choice[0])
                _directory_details['MovieName'] = _choice[_index]
                _directory_details['Year'] = int(_movie.getReleased(_index)[0:4])
        else:
            pass

        if 'Year' in _directory_details:
            _new_dir = '%s (%s)' % (_directory_details['MovieName'], _directory_details['Year'])
        else:
            _new_dir = '%s' % (_directory_details['MovieName'])
            
        _target_dir = os.path.join(self.config.MoviesDir, _new_dir)

        if os.path.exists(_target_dir):
            if _target_dir == dir:
                log.info('Skipping: Directory already properly named and in: {}'.format(dir) )
                return
            else:
                _target_dir = os.path.join(os.path.split(self.config.MoviesDir)[0], _new_dir)
                if os.path.exists(_target_dir):
                    log.warn("Unable to process, Directory: %s, already at destination!" % (_target_dir))
                    return

        log.info('Renaming Movie Directory: %s to %s' % (os.path.basename(dir), _target_dir))
        try:
            os.rename(dir, _target_dir)
            log.info("Successfully Renamed: %s" % _target_dir)
        except OSError, exc:
            log.error("Skipping, Unable to Rename Directory: %s" % dir)
            log.error("Unexpected error: %s" % exc)

        return None

    def _ignored(self, name):
        """ Check for ignored pathnames.
        """
        return any(fnmatch.fnmatch(name.lower(), pattern) for pattern in self.config.ExcludeList)

    def _del_dir(self, pathname, file=True):
        log.trace("_del_dir: pathname:{!s}".format(pathname))

        if file:
            _cur_dir = os.path.split(pathname)[0]
        else:
            _cur_dir = pathname

        if self.regex_NewDir.match(pathname):
            _base_dir = os.path.join(os.path.split(self.config.MoviesDir)[0],self.config.NewDir)
        elif self.regex_MoviesDir.match(pathname):
            _base_dir = self.config.MoviesDir
        else:
            _base_dir = os.path.split(pathname)[0]

        while _base_dir != _cur_dir:
            if len(os.listdir(_cur_dir)) == 0:
                try:
                    os.rmdir(_cur_dir)
                    log.info('Deleting Empty Directory: {}'.format(_cur_dir))
                    _cur_dir = os.path.split(_cur_dir)[0]
                    continue
                except:
                    log.warn('_del_dir: Unable to Delete: %s' % (sys.exc_info()[1]))
                    return
            else:
                return
        return


if __name__ == "__main__":

    from daddyvision.common.settings import Settings
    from daddyvision.common.options import OptionParser, CoreOptionParser

    logger.initialize()

    parser = CoreOptionParser()
    options, args = parser.parse_args()

    log_level = logging.getLevelName(options.loglevel.upper())
    log_file = os.path.expanduser(options.logfile)

    # If an absolute path is not specified, use the default directory.
    if not os.path.isabs(log_file):
        log_file = os.path.join(logger.LogDir, log_file)

    logger.start(log_file, log_level)

    log.debug("Parsed command line options: {!s}".format(options))
    log.debug("Parsed arguments: %r" % args)

    _config_settings = Settings()

    _path_name = ''
    for i in range(len(args)):
        _path_name = '%s %s'% (_path_name, args[i])
    _path_name = _path_name.lstrip().rstrip()
    if len(_path_name) == 0:
        _new_movies_dir = os.path.join ( os.path.split(_config_settings.MoviesDir)[0], _config_settings.NewDir )
        msg = 'Missing Scan Starting Point (Input Directory), Using Default: {}'.format(_new_movies_dir)
        log.info(msg)
        _path_name = _new_movies_dir

    if not os.path.exists(_path_name):
        log.error('Invalid arguments file or path name not found: %s' % _path_name)
        sys.exit(1)

    rename = Rename(_config_settings)
    _new_fq_name = rename.rename(_path_name)