#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Author: AJ Reynolds
Date: 12-11-2010
Purpose:
Program to rename movies files

"""
from daddyvision.common import logger
from daddyvision.common.chkvideo import chkVideoFile
from daddyvision.common.exceptions import InvalidFilename
from daddyvision.common.options import OptionParser, OptionGroup
from daddyvision.movies.fileparser import FileParser
from fuzzywuzzy import fuzz
import filecmp
import fnmatch
import logging
import os
import re
import sys
import tmdb

__pgmname__     = 'rename'
__version__     = '$Rev$'

__author__      = "@author: AJ Reynolds"
__copyright__   = "@copyright: Copyright 2011, AJ Reynolds"
__license__     = "@license: GPL"
__email__       = "@contact: stampedeboss@gmail.com"

__maintainer__  = "AJ Reynolds"
__status__      = "Development"
__credits__     = []

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
        self.regex_NewDir = re.compile('^{}.*$'.format(self.config.NewMoviesDir, re.IGNORECASE))
        self.regex_MoviesDir = re.compile('^{}.*$'.format(self.config.MoviesDir), re.IGNORECASE)
        tmdb.configure('587c13e576f991c0a653f783b290a065')
        return

    @useLibraryLogging
    def rename(self, pathname, video_check=True ):
        log.trace("rename method: pathname:{}".format(pathname))

        if os.path.isfile(pathname):
            log.debug("-----------------------------------------------")
            log.debug("Movie Directory: %s" % os.path.split(pathname)[0])
            log.debug("Movie Filename:  %s" % os.path.split(pathname)[1])
            if video_check:
                if chkVideoFile(pathname):
                    log.error('File Failed Video Check: {}'.format(pathname))
                    return
            _file_details = self.parser.getFileDetails(pathname)
            self._rename_file(_file_details)

        elif os.path.isdir(pathname):
            for _root, _dirs, _files in os.walk(os.path.abspath(pathname),followlinks=False):
                _dirs.sort()
                for _dir in _dirs[:]:
                    if _dir == 'VIDEO_TS':
                        self._rename_directory(_root)
                        _dirs.remove(_dir)
                    if self._ignored(_dir) and options.ignore:
                        _dirs.remove(_dir)
                        log.debug("Ignoring %r" % os.path.join(_root, _dir))
                _files.sort()
                for _file in _files:
                    _path_name = os.path.join(_root, _file)
                    log.debug("-----------------------------------------------")
                    log.debug("Filename: %s" % _file)
                    try:
                        _file_details = self.parser.getFileDetails(_path_name)
                        if self._ignored(_path_name) and not self.regex_MovieDir.match(_path_name) and options.ignore:
                            if not self.regex_MoviesDir.match(_path_name):
                                os.remove(_file_details['FileName'])
                                self._del_dir(_file_details['FileName'])
                        else:
                            if video_check and _file_details['Ext'].lower() in self.config.MediaExt:
                                if chkVideoFile(_path_name):
                                    log.error('File Failed Video Check: {}'.format(_path_name))
                                    return
                            _fq_new_file_name = self._rename_file(_file_details)
                    except InvalidFilename:
                        pass

        if self.regex_NewDir.match(pathname):
            _base_dir = self.config.NewMoviesDir
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

        _file_details = self._get_tmdb_info(_file_details)

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
                    log.info("Deleting %r, already at destination!" % (os.path.split(_file_details['FileName'])[1]))
                    os.remove(_file_details['FileName'])
                    self._del_dir(_file_details['FileName'])
                    return
                else:
                    log.info("Skipping: file: %r, at already at destination!" % (os.path.split(_file_details['FileName'])[1]))
                    return
            else:
                if  os.path.splitext(_fq_new_file_name)[1][1:] in ['mkv', 'm2ts']:
                    if os.path.getsize(_fq_new_file_name) >= os.path.getsize(_file_details['FileName']):
                        log.warn("Skipping Rename: File: %r, Requires Manual intervention (Larger Already Exists)!" % (os.path.split(_file_details['FileName'])[1]))
                        return
                elif _file_details['Ext'] in ['mkv', 'm2ts']:
                    log.warn("Replacing Existing Non-MKV: File: %r!" % (os.path.split(_fq_new_file_name)[1]))
                else:
                    log.warn("Skipping Rename: File: %r, Requires Manual intervention (Already Exists)!" % (os.path.split(_file_details['FileName'])[1],))
                    return

        log.info('Renaming Movie: %s to %s' % (os.path.basename(_file_details['FileName']), _new_file_name))
        try:
            if not os.path.exists(os.path.split(_fq_new_file_name)[0]):
                os.makedirs(os.path.split(_fq_new_file_name)[0])
#                os.chown(os.path.split(_fq_new_file_name)[0], 1000, 100)
            os.rename(_file_details['FileName'], _fq_new_file_name)
            os.chmod(_fq_new_file_name, 0664)
#            os.chown(_fq_new_file_name, 1000, 100)
            log.info("Successfully Renamed: %s" % _fq_new_file_name)
            self._del_dir(_file_details['FileName'])
        except OSError, exc:
            log.error("Skipping, Unable to Rename File: %s" % _file_details['FileName'])
            log.error("Unexpected error: %s" % exc)

        return _fq_new_file_name

    def _rename_directory(self, directory):
        log.trace("_rename_directory method: pathname:{!s}".format(directory))

        _directory_details = self.parser.getFileDetails(directory+'.avi')
        _directory_details['FileName'] = directory

        _directory_details = self._get_tmdb_info(_directory_details)

        if 'Year' in _directory_details:
            _new_dir = '%s (%s)' % (_directory_details['MovieName'], _directory_details['Year'])
        else:
            _new_dir = '%s' % (_directory_details['MovieName'])

        _target_dir = os.path.join(self.config.MoviesDir, _new_dir)

        if os.path.exists(_target_dir):
            if _target_dir == directory:
                log.info('Skipping: Directory already properly named and in: {}'.format(directory) )
                return
            else:
                _target_dir = os.path.join(os.path.split(self.config.MoviesDir)[0], _new_dir)
                if os.path.exists(_target_dir):
                    log.warn("Unable to process, Directory: %s, already at destination!" % (_target_dir))
                    return

        log.info('Renaming Movie Directory: %s to %s' % (os.path.basename(directory), _target_dir))
        try:
            os.rename(directory, _target_dir)
            log.info("Successfully Renamed: %s" % _target_dir)
        except OSError, exc:
            log.error("Skipping, Unable to Rename Directory: %s" % directory)
            log.error("Unexpected error: %s" % exc)

        return None

    def _get_tmdb_info(self, _file_details):

        _movies = tmdb.Movies(_file_details['MovieName'])

        _movie = None

        for _movie in _movies.iter_results():
            if fuzz.ratio(_movie["title"], _file_details['MovieName']) > 85:
                break
        if _movie:
            _file_details['MovieName'] = _movie["title"]
            if _movie["release_date"]:
                _file_details['Year'] = str(_movie["release_date"][0:4])
            return _file_details
        else:
            log.warn("Movie Not Found in TMDb: {}".format(_file_details['MovieName']))
            return _file_details

    def _ignored(self, name):
        """ Check for ignored pathnames.
        """
        return any(fnmatch.fnmatch(name.lower(), pattern) for pattern in self.config.ExcludeList)

    def _del_dir(self, pathname, is_file=True):
        log.trace("_del_dir: pathname:{!s}".format(pathname))

        if is_file:
            _cur_dir = os.path.split(pathname)[0]
        else:
            _cur_dir = pathname

        if self.regex_NewDir.match(pathname):
            _base_dir = self.config.NewMoviesDir
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

class localOptions(OptionParser):

    def __init__(self, unit_test=False, **kwargs):
        OptionParser.__init__(self, **kwargs)

        group = OptionGroup(self, "Modifers")
        group.add_option("-f", "--force", dest="check",
            action="store_false", default=True,
            help="Bypass Video Check and Force Rename")
        group.add_option("--no-ignore", dest="ignore",
            action="store_false", default=True,
            help="Bypass Ignore Process and Handle all Files")
        self.add_option_group(group)


if __name__ == "__main__":

    from daddyvision.common.settings import Settings

    logger.initialize()

    parser = localOptions()
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
    rename = Rename(_config_settings)

    if len(args) == 0:
        msg = 'Missing Scan Starting Point (Input Directory), Using Default: {}'.format(_config_settings.NewMoviesDir)
        log.info(msg)
        args = [_config_settings.NewMoviesDir]
    for _path_name in args:
        _path_name = _path_name.lstrip().rstrip()

        if not os.path.exists(_path_name):
            log.error('Invalid arguments file or path name not found: %s' % _path_name)
            sys.exit(1)

        rename.rename(_path_name, options.check)