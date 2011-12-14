#!/usr/bin/env python
"""
Author: AJ Reynolds
Date: 12-11-2010
Purpose:
Program to rename movies files

"""
from daddyvision.common.exceptions import InvalidFilename, RegxSelectionError, ConfigValueError
from daddyvision.common.exceptions import DataRetrievalError, EpisodeNotFound, SeriesNotFound
from daddyvision.common.fileparser import FileParser
from daddyvision.common import logger
from daddyvision.series.episodeinfo import EpisodeDetails
from logging import INFO, WARNING, ERROR, DEBUG
import re
import os
import sys
import filecmp
import fnmatch
import logging
import datetime
import time
import unicodedata

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

        self.regex_repack = re.compile('^.*(repack|proper).*$', re.IGNORECASE)
        self.regex_Movie = re.compile('^(?P<moviename>.+?)[ \._\-](?P<year>[0-9][0-9][0-9][0-9]).*$', re.VERBOSE)

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
                    if self._ignored(_dir):
                        _dirs.remove(_dir)
                        log.debug("Ignoring %r" % os.path.join(_root, _dir))
                _files.sort()
                for _file in _files:
                    _path_name = os.path.join(_root, _file)
                    log.debug("-----------------------------------------------")
                    log.debug("Filename: %s" % _path_name)
                    self._rename_file(_path_name)

    def _rename_file(self, pathname):
        match  = self.regex_Movie.search(os.path.split(pathname)[1])
        if match:
            moviename = self.cleanRegexedMovieName(match.group('moviename'))
            year = match.group('year')
            ext = os.path.splitext(pathname)[1]
            NewDir = '%s (%s)' % (moviename, year)
            NewName = '%s (%s)%s' % (moviename, year, ext)
            fqNewName = os.path.join(os.path.split(self.config.MoviesDir)[0], os.path.join(NewDir, NewName))
            repack  = self.regex_repack.search(pathname)
            if os.path.exists(fqNewName):
                if repack:
                    os.remove(fqNewName)
                elif filecmp.cmp(fqNewName, pathname):
                    log.info("Deleting %r, already at destination!" % (os.path.split(pathname)[1],))
                    os.remove(pathname)
                    self._del_dir(pathname)
                    return

            log.info('Renaming Movie: %s to %s' % (os.path.basename(pathname), NewName))
            try:
                if not os.path.exists(os.path.split(fqNewName)[0]):
                    os.makedirs(os.path.split(fqNewName)[0])
                    if os.getgid() == 0:
                        os.chown(os.path.split(fqNewName)[0], 1000, 100)
                os.rename(pathname, fqNewName)
                log.info("Successfully Renamed: %s" % fqNewName)
                self._del_dir(pathname)
            except OSError, exc:
                log.error("Skipping, Unable to Rename File: %s" % pathname)
                log.error("Unexpected error: %s" % exc)
        else:
            _ext = os.path.splitext(pathname)[1][1:4]
            if _ext not in self.config.MediaExt:
                os.remove(pathname)
                self._del_dir(pathname)

    def _ignored(self, name):
        """ Check for ignored pathnames.
        """
        return any(fnmatch.fnmatch(name.lower(), pattern) for pattern in self.config.ExcludeList)

    def cleanRegexedMovieName(self, moviename):
        """Cleans up name by removing any . and _
        characters, along with any trailing hyphens.
        """
        moviename = re.sub("(\D)[.](\D)", "\\1 \\2", moviename)
        moviename = re.sub("(\D)[.]", "\\1 ", moviename)
        moviename = re.sub("[.](\D)", " \\1", moviename)
        moviename = moviename.replace("_", " ")
        moviename = re.sub("-$", "", moviename)
        return moviename.strip()

    def _del_dir(self, pathname):
        _base_dir = os.path.join(os.path.split(self.config.SeriesDir)[0],self.config.NewDir)
        _last_dir = os.path.split(pathname)[0]
        while _last_dir != _base_dir:
            if len(os.listdir(_last_dir)) == 0:
                try:
                    os.rmdir(os.path.split(pathname)[0])
                    _last_dir = os.path.split(_last_dir)[0]
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