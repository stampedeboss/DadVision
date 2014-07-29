#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Purpose:
Program to rename files associated with Movie Content

"""
from library import Library
from library.movie.fileparser import FileParser
from common import logger
from common.chkvideo import chkVideoFile
from common.exceptions import InvalidPath, InvalidFilename, UnexpectedErrorOccured, MovieNotFound
from fuzzywuzzy import fuzz
import filecmp
import fnmatch
import logging
import os
import re
import sys
import tmdb3
import shutil
import unicodedata

__pgmname__ = 'rename'
__version__ = '$Rev$'

__author__ = "@author: AJ Reynolds"
__copyright__ = "@copyright: Copyright 2011, AJ Reynolds"
__license__ = "@license: GPL"
__email__ = "@contact: stampedeboss@gmail.com"

__maintainer__ = "@organization: AJ Reynolds"
__status__ = "@status: Development"
__credits__ = []

log = logging.getLogger(__pgmname__)

def useLibraryLogging(func):

    def wrapper(self, *args, **kw):
        # Set the library name in the logger
#        from daddyvision.common import logger
        logger.set_library('movie')
        try:
            return func(self, *args, **kw)
        finally:
            logger.set_library('')

    return wrapper

class RenameMovie(Library):

    def __init__(self):
        log.trace('Rename.__init__ method: Started')

        super(RenameMovie, self).__init__()

        rename_group = self.options.parser.add_argument_group("Rename Options", description=None)
        rename_group.add_argument("--force-rename", dest="force_rename",
            action="store_true", default=False,
            help="Force Renames for Files That Already Exist")
        rename_group.add_argument("--force-delete", "--fd", dest="force_delete",
            action="store_true", default=False,
            help="Force Deletes for Files That Already Exist")
        rename_group.add_argument("--ignore_excludes", dest="ignore_excludes",
            action="store_true", default=False,
            help="Process all Files Regardless of Excludes")
        rename_group.add_argument("--no-check_video", dest="check_video",
            action="store_false", default=True,
            help="Bypass Video Checks")

        self.fileparser = FileParser()

        self.regex_repack = re.compile('^.*(repack|proper).*$', re.IGNORECASE)
        self.regex_NewMoviesDir = re.compile('^{}.*$'.format(self.settings.NewMoviesDir, re.IGNORECASE))

        tmdb3.set_key('587c13e576f991c0a653f783b290a065')
        tmdb3.set_cache(filename='tmdb3.cache')
        return

    @useLibraryLogging
    def renameMovie(self, pathname):
        log.trace("rename method: pathname:{}".format(pathname))

        pathname = os.path.abspath(pathname)

        if os.path.isfile(pathname):
            log.debug("-----------------------------------------------")
            log.debug("Movie Directory: %s" % os.path.split(pathname)[0])
            log.debug("Movie Filename:  %s" % os.path.split(pathname)[1])
            try:
                self._rename_file(pathname)
                if len(os.listdir(pathname)) == 0:
                    self._del_dir(pathname, Tree=False)
            except (MovieNotFound, InvalidFilename):
                pass
        elif os.path.isdir(pathname):
            log.debug("-----------------------------------------------")
            log.debug("Movie Directory: %s" % pathname)
            for _root, _dirs, _files in os.walk(os.path.abspath(pathname), followlinks=False):
                _dirs.sort()
                for _dir in _dirs[:]:
                    # Process Enbedded Directories
                    if self._ignored(_dir) and not self.args.ignore_excludes:
                        if self.regex_NewMoviesDir.match(_dir):
                            log.debug("Rename Deleting Directory Due to Excludes: %r" % os.path.join(_root, _dir))
                            self._del_dir(_dir, Tree=True)
                        _dirs.remove(_dir)

                    if _dir == 'VIDEO_TS':
                        self._rename_directory(_root)
                        _dirs.remove(_dir)

                _files.sort()
                for _file in _files:
                    _path_name = os.path.join(_root, _file)
                    log.debug("Movie Filename: %s" % _file)
                    if not self.args.ignore_excludes and self._ignored(_path_name):
                        if self.regex_NewMoviesDir.match(_path_name):
                            try:
                                os.remove(_path_name)
                            except InvalidFilename, UnexpectedErrorOccured:
                                pass
                        continue

                    try:
                        self._rename_file(_path_name)
                    except (MovieNotFound, InvalidFilename):
                        pass
                if os.path.exists(_root) and len(os.listdir(_root)) == 0:
                    self._del_dir(_root)

        return None

    def _rename_file(self, pathname):
        log.trace("_rename_file method: pathname:{!s}".format(pathname))

        _ext = os.path.splitext(pathname)[1][1:]
        if not _ext in self.settings.MediaExt:
            return

        if self.args.check_video:
            if chkVideoFile(pathname):
                log.error('File Failed Video Check: {}'.format(pathname))
                return

        try:
            _file_details = self.fileparser.getFileDetails(pathname)
            try:
                _file_details = self._get_tmdb_info(_file_details)
            except MovieNotFound:
                _dir_name = os.path.dirname(pathname) + '.' +_ext
                _directory_details = self.fileparser.getFileDetails(_dir_name)
                try:
                    _file_details['MovieName'] = _directory_details['MovieName']
                except KeyError:
                    raise                
                _file_details = self._get_tmdb_info(_file_details)
            _fq_new_file_name = self._get_new_filename(_file_details)

            if self._check_for_existing(_fq_new_file_name, _file_details):
                log.info('Renaming Movie: %s to %s' % (os.path.basename(_file_details['FileName']), _fq_new_file_name))
                try:
                    if not os.path.exists(os.path.split(_fq_new_file_name)[0]):
                        _new_dir = os.path.split(_fq_new_file_name)[0]
                        os.makedirs(_new_dir)
                        os.chmod(_new_dir, 0775)
                    os.rename(_file_details['FileName'], _fq_new_file_name)
                    os.chmod(_fq_new_file_name, 0664)
                    log.info("Successfully Renamed: %s" % _fq_new_file_name)
                except OSError, exc:
                    log.error("Skipping, Unable to Rename File: %s" % _file_details['FileName'])
                    log.error("Unexpected error: %s" % exc)
                    raise UnexpectedErrorOccured("Unexpected error: %s" % exc)
        except (MovieNotFound, InvalidFilename, UnexpectedErrorOccured):
            pass
        return

    def _get_tmdb_info(self, _file_details):
        log.trace("_get_tmdb_info: file details:{!s}".format(_file_details))

        _check_year = False
        try:
            if 'Year' in _file_details:
                _movie = '{MovieName} ({Year})'.format(**_file_details)
                _tmdbDetails = list(tmdb3.searchMovieWithYear(_movie))
                if not _tmdbDetails:
                    _tmdbDetails = list(tmdb3.searchMovie(_file_details['MovieName']))
                    if not _tmdbDetails:
                        raise MovieNotFound("Movie Not Found in TMDb: {}".format(_file_details['MovieName']))
                _check_year = True
            else:
                _tmdbDetails = list(tmdb3.searchMovie(_file_details['MovieName']))
                if not _tmdbDetails:
                    raise MovieNotFound("Movie Not Found in TMDb: {}".format(_file_details['MovieName']))
        except MovieNotFound:
                raise MovieNotFound("Movie Not Found in TMDb: {}".format(_file_details['MovieName']))



        if 'Year' in _file_details:
            _movie = '{MovieName} ({Year})'.format(**_file_details)
            try:
                _tmdbDetails = list(tmdb3.searchMovieWithYear(_movie))
            except IndexError:
                try:
                    _tmdbDetails = list(tmdb3.searchMovie(_file_details['MovieName']))
                except IndexError:
                    raise MovieNotFound("Movie Not Found in TMDb: {}".format(_file_details['MovieName']))
        else:
            try:
                _tmdbDetails = list(tmdb3.searchMovie(_file_details['MovieName']))
            except IndexError:
                raise MovieNotFound("Movie Not Found in TMDb: {}".format(_file_details['MovieName']))

	log.trace('TMDB Details: {}'.format(_tmdbDetails))
        for _movie in _tmdbDetails:
            _title = unicodedata.normalize('NFKD', _movie.title).encode("ascii", 'ignore')
            _title = _title.replace("&amp;", "&").replace("/", "_")

            if self._matching(_title+' '+str(_movie.releasedate.year), _file_details['MovieName']+' '+_file_details['Year']):
                break

        if not self._matching(_title, _file_details['MovieName']):
            # Check Alternate Titles: list(AlternateTitle) alternate_titles 
            _alt_title = _movie.alternate_titles
            for _alt_title in _movie.alternate_titles:
                log.trace('Check Alternate Titles: {}'.format(_alt_title.title)) 
                _alt_title = unicodedata.normalize('NFKD', _alt_title.title).encode("ascii", 'ignore')
                _alt_title = _alt_title.replace("&amp;", "&").replace("/", "_")
                if self._matching(_alt_title, _file_details['MovieName']):
                    break

            if not self._matching(_alt_title, _file_details['MovieName']):
                log.warn("Movie Not Found in TMDb: {}".format(_file_details['MovieName']))
                raise MovieNotFound("Movie Not Found in TMDb: {}".format(_file_details['MovieName']))
            _file_details['AltMovieName'] = _alt_title

        _file_details['MovieName'] = _title
        if _movie.releasedate:
            _file_details['Year'] = str(_movie.releasedate.year)

        log.trace("Movie Located in TMDB")
        return _file_details

    def _get_new_filename(self, _file_details):
        log.trace("_get_new_filename method: pathname:{!s}".format(_file_details))

        if 'Trailer' in _file_details:
            _trailer = '-trailer'
        else:
            _trailer = ''

        if 'Year' in _file_details:
            _new_dir = '%s (%s)' % (_file_details['MovieName'], _file_details['Year'])
            _new_file_name = '%s (%s)%s.%s' % (_file_details['MovieName'], _file_details['Year'], _trailer, _file_details['Ext'])
        else:
            _new_dir = '%s' % (_file_details['MovieName'])
            _new_file_name = '%s%s.%s' % (_file_details['MovieName'], _trailer, _file_details['Ext'])

        _fq_new_file_name = os.path.join(self.settings.MoviesDir, _new_dir, _new_file_name)

        return _fq_new_file_name

    def _check_for_existing(self, _fq_new_file_name, _file_details):
        log.trace("_check_for_existing method: filename: {} pathname:{!s}".format(_fq_new_file_name, _file_details))

        if not os.path.exists(_fq_new_file_name):
            return True

        if _fq_new_file_name == _file_details['FileName']:
            log.info("No Action Required - Movie Library: {}".format(os.path.split(_file_details['FileName'])[1]))
            return False

        try:
            if self.args.force_rename or self.regex_repack.search(_file_details['FileName']):
                log.warn("Replacing Existing Version with repack or Force Rename Requested: File: %r!" % (os.path.split(_fq_new_file_name)[1]))
                os.remove(_fq_new_file_name)
                return True

            log.trace("Comparing existing file to new, may run for some time.")
            if filecmp.cmp(_fq_new_file_name, _file_details['FileName']):
                log.info("Deleting New File %r, Same File already at destination!" % (os.path.split(_file_details['FileName'])[1]))
                os.remove(_file_details['FileName'])
                return False

            if os.path.getsize(_fq_new_file_name) >= os.path.getsize(_file_details['FileName']):
                if self.args.force_delete:
                    log.info("Deleting %r, Larger Version already at destination!" % (os.path.split(_file_details['FileName'])[1]))
                    os.remove(_file_details['FileName'])
                else:
                    log.info("Keeping %r in New, Larger Version already at destination!" % (os.path.split(_file_details['FileName'])[1]))
                return False

        except OSError, exc:
            log.error("Unable to remove File: %s" % _fq_new_file_name)
            log.error("Unexpected error: %s" % exc)
            return False
        return True

    def _rename_directory(self, directory):
        log.trace("_rename_directory method: pathname:{!s}".format(directory))

        _directory_details = self.fileparser.getFileDetails(directory + '.avi')
        _directory_details['FileName'] = directory

        _directory_details = self._get_tmdb_info(_directory_details)

        if 'Year' in _directory_details:
            _new_dir = '%s (%s)' % (_directory_details['MovieName'], _directory_details['Year'])
        else:
            _new_dir = '%s' % (_directory_details['MovieName'])

        _target_dir = os.path.join(self.settings.MoviesDir, _new_dir)

        if os.path.exists(_target_dir):
            if _target_dir == directory:
                log.trace('Skipping: Directory already properly named and in: {}'.format(directory))
                return
            else:
                _target_dir = os.path.join(os.path.split(self.settings.MoviesDir)[0], _new_dir)
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
            raise UnexpectedErrorOccured("Unexpected error: %s" % exc)

        return None

    def _del_dir(self, pathname, Tree=False):
        log.trace("_del_dir: pathname:{!s}".format(pathname))

        if not os.path.isdir(pathname):
            raise InvalidPath('Invalid Path was requested for deletion: {}'.format(pathname))

        try:
            log.info('Deleting Empty Directory: {}'.format(pathname))
            if Tree:
                shutil.rmtree(pathname)
            else:
                os.rmdir(pathname)
        except:
            log.warn('Delete Directory: Unable to Delete requested directory: %s' % (sys.exc_info()[1]))

    def _matching(self, value1, value2):
        log.trace("_matching: Compare: {} --> {}".format(value1, value2))

        Fuzzy = []
        Fuzzy.append(fuzz.ratio(value1, value2))
        Fuzzy.append(fuzz.token_set_ratio(value1, value2))
        Fuzzy.append(fuzz.token_sort_ratio(value1, value2))
        Fuzzy.append(fuzz.token_set_ratio(value1, value2))

        log.debug('Fuzzy Ratio" {} for {} - {}'.format(Fuzzy[0], value1, value2))
        log.debug('Fuzzy Partial Ratio" {} for {} - {}'.format(Fuzzy[1], value1, value2))
        log.debug('Fuzzy Token Sort Ratio" {} for {} - {}'.format(Fuzzy[2], value1, value2))
        log.debug('Fuzzy Token Set Ratio" {} for {} - {}'.format(Fuzzy[3], value1, value2))

        return any([fr > 85 for fr in Fuzzy])

    def _ignored(self, name):
        """ Check for ignored pathnames.
        """
        return any(fnmatch.fnmatch(name.lower(), pattern) for pattern in self.settings.ExcludeList)


if __name__ == "__main__":

    logger.initialize()
    library = RenameMovie()

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

    if len(library.args.library) < 1:
        log.warn('No pathname supplied for rename: Using default: {}'.format(library.settings.NewMoviesDir))
        library.args.library = [library.settings.NewMoviesDir]

    _lib_paths = library.args.library

    for _lib_path in _lib_paths:
        if os.path.exists(_lib_path):
            library.renameMovie(_lib_path)
        else:
            log.error('Skipping Rename: Unable to find File/Directory: {}'.format(_lib_path))

