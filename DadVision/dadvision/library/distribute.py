#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Purpose:
    Program to distribute the files from a source to a target library. If needed,
    the files will be unzipped and renamed to meet the library standard.
"""
from library import Library
from common import logger
from common.exceptions import (BaseDaddyVisionException,
    DataRetrievalError, EpisodeNotFound, SeriesNotFound, InvalidFilename,
    RegxSelectionError, ConfigValueError)
from library.movie.rename import RenameMovie
from library.series.rename import RenameSeries

from subprocess import Popen, PIPE
import filecmp
import fnmatch
import logging
import os
import re
import shutil
import subprocess
import sys

__pgmname__ = 'library.distribute'
__version__ = '@version: $Rev$'

__author__ = "@author: AJ Reynolds"
__copyright__ = "@copyright: Copyright 2011, AJ Reynolds"
__status__ = "@status: Development"
__license__ = "@license: GPL"

__maintainer__ = "@organization: AJ Reynolds"
__credits__ = []

log = logging.getLogger(__pgmname__)

def useLibraryLogging(func):
    def wrapper(self, *args, **kw):
        # Set the library name in the logger
        logger.set_library(self.type)
        try:
            return func(self, *args, **kw)
        finally:
            logger.set_library('')
    return wrapper

class Distribute(Library):

    def __init__(self):
        log.trace('__init__')

        super(Distribute, self).__init__()

        dist1 = self.options.parser.add_argument_group("Media Type Options", description=None)
        dist1.add_argument("-s", "--series", dest="content", default="",
            action="store_const", const="Series",
            help="Process as Series")
        dist1.add_argument("-m", "--movies", dest="content",
            action="store_const", const="Movie",
            help="Process as Movies")
        dist1.add_argument("-n", "--non-video", dest="content",
            action="store_const", const="NonVideo",
            help="Process as Non-Video")

        dist2 = self.options.parser.add_argument_group("Distribute Options", description=None)
        dist2.add_argument("--no-cleanup", dest="clean_up_name",
            action="store_false", default=True,
            help="Do not clean-up names from unpack")
        dist2.add_argument("--no-ignore", dest="ignore",
            action="store_false", default=True,
            help="Process all files, Ignore nothing")
        dist2.add_argument("--no-movies", dest="suppress_movies",
            action="store_true", default=False,
            help="Do Not Process Movie files")

        self.rename_series = RenameSeries()
        self.rename_movies = RenameMovie()

        self.type = None
        self.RegEx = []
        try:
            self.RegEx.append(re.compile('(.*)[\._ \-][s|season]([0-9]+)[e|x]?[0-9]?([^\\/]*)', re.IGNORECASE))
            self.RegEx.append(re.compile('(.*)[\._ \-][s]?([0-9]+)[e|x][0-9]?([^\\/]*)', re.IGNORECASE))
            self.RegEx.append(re.compile('(.*)[\._ \-]([0-9]+\.[0-9]+\.[0-9]+)([^\\/]*)', re.IGNORECASE))
            self.RegEx.append(re.compile('(.*)[\._ \-]season[\._ \-]([0-9]+)([^\\/]*)', re.IGNORECASE))
        except re.error, errormsg:
            log.error("Distribute.__init__: Invalid Series RegEx pattern: %s" % (errormsg))
            raise ConfigValueError("Distribute.__init__: Invalid Series RegEx: %s" % (errormsg))

        self.RAR_RE = re.compile(r"\.([rR][aA][rR]|[rR]\d{2,3})$")
        self.RAR_PART_RE = re.compile(r"\.part\d{2,3}\.rar$")

    def distribute(self, pathname):
        log.trace('ProcessFile: %s' % pathname)

        self.type, _fmt, _dest_dir = self._get_type(pathname)

        if _fmt == 'file':
            log.trace("%s file - %r..." % (type, pathname))
            pathname = self._distribute_file(pathname, _dest_dir)
        elif _fmt == 'dir':  # a folder
            log.trace("%s directory ...%r" % (type, os.path.basename(pathname)))
            _dest_dir = self._distribute_directory(pathname, _dest_dir)
        else:  # unknown error
            raise InvalidFilename("Skipping %r, doesn't exist!" % (pathname,))

        if _fmt == 'file':
            _tgt_rename = pathname
        else:
            _tgt_rename = _dest_dir

        if self.type == "Series":
            try:
                self.rename_series.renameSeries(_tgt_rename)
            except (DataRetrievalError, EpisodeNotFound, SeriesNotFound, InvalidFilename,
                    RegxSelectionError, ConfigValueError), msg:
                log.error(msg)
        elif self.type == "Movie":
            if self.args.suppress_movies:
               log.info('Suppression of Movies Requested: Movie Skipped')
            try:
                self.rename_movies.renameMovie(_tgt_rename)
            except:
                raise BaseDaddyVisionException('Unknown Error: {}'.format(sys.exc_info()[1]))


    def _get_type(self, pathname):
        log.trace('_get_type: Pathname: {}'.format(pathname))

        _file_name = os.path.split(pathname.rstrip(os.sep))[1]
        _dest_dir = None
        _type = None
        _fmt = None

        if self.args.content:
            if self.args.content == 'Series':
                _type = "Series"
                _dest_dir = self.settings.NewSeriesDir
            elif self.args.content == "Movie":
                _type = "Movie"
                _dest_dir = self.settings.NewMoviesDir
            else:
                _type = "NonVideo"
                _dest_dir = os.path.join(self.settings.NonVideoDir, os.path.basename(pathname.rstrip(os.sep)))  # Adds the last directory to target name
            if os.path.isfile(pathname):
                _fmt = 'file'
                _dest_dir = os.path.splitext(_dest_dir)[0]
            elif os.path.isdir(pathname):
                _fmt = 'dir'
            return _type, _fmt, _dest_dir

        for cRegEx in self.RegEx:
            _series = cRegEx.search(_file_name)
            if _series:
                _series_name = _series.group(1)
                log.debug("Series: %s" % _series_name)
                _type = "Series"
                _dest_dir = self.settings.NewSeriesDir

                if os.path.isfile(pathname):
                    _fmt = 'file'
                    _dest_dir = os.path.splitext(_dest_dir)[0]
                elif os.path.isdir(pathname):
                    _fmt = 'dir'

                return _type, _fmt, _dest_dir

        if any(pathname.lower().count(key) > 0 for key in self.settings.MovieGlob):
            _type = "Movie"
            _dest_dir = self.settings.NewMoviesDir
        else:
            _type = "NonVideo"
            _dest_dir = os.path.join(self.settings.NonVideoDir, os.path.basename(pathname.rstrip(os.sep)))  # Adds the last directory to target name

        if os.path.isfile(pathname):  # a file
            _fmt = 'file'
            _dest_dir = os.path.splitext(_dest_dir)[0]
        elif os.path.isdir(pathname):  # a folder
            _fmt = 'dir'
        return _type, _fmt, _dest_dir

    @useLibraryLogging
    def _distribute_file(self, srcfile, destdir):
        log.trace('_distribute_file: %s %s' % (srcfile, destdir))
        """ Move or copy a single file.
        """
        # ignored file?
        if self._ignored(os.path.basename(srcfile)) and self.args.ignore:
            log.verbose("Ignoring %r!" % (srcfile,))
            return

        if self.type == "Movie":
            if self.args.suppress_movies:
               log.verbose("Ignoring %r!" % (srcfile,))
               return

        destfile = os.path.join(destdir, os.path.basename(srcfile))
        if os.path.exists(destfile) and filecmp.cmp(destfile, srcfile):
            log.info("Skipped: Already at Destination:")
            log.info("         {}".format(os.path.basename(srcfile)))
            log.info("         {}".format(os.path.basename(destfile)))
            return destfile

        indicator = "<+<"
        action = shutil.copy2

        # make sure target folder exists
        if not os.path.exists(destdir):
            log.debug("Creating %r" % (destdir.rstrip(os.sep) + os.sep,))
            try:
                os.makedirs(destdir)
                os.chmod(destdir, 0775)
            except OSError, exc:
                log.error("Failed to create %r (%s)" % (destdir, exc))

        # copy file, possibly across devices.
        log.verbose("Copying: {}".format(destdir))
        log.verbose("         {}".format(indicator))
        log.verbose("         {}".format(srcfile))
        try:
            action(srcfile, destfile)
        except OSError, exc:
            log.error("Failed to copy %r (%s)" % (os.path.basename(srcfile), exc))
        return destfile

    @useLibraryLogging
    def _distribute_directory(self, src_dir, dest_dir):
        """ Move or copy a folder.
        """
        log.trace('_distribute_directory: %s %s' % (src_dir, dest_dir))

        # initialize stuff
        src_dir = src_dir.rstrip(os.sep)
        _tgt_dir = dest_dir
        _base_dir = os.path.join(dest_dir, os.path.basename(src_dir))
        _files_req_unpack = False

        for _root, _dir_names, _file_names in os.walk(src_dir):
            # don't scan ignored subdirs
            for _dir_name in _dir_names[:]:
                if self._ignored(_dir_name) and self.args.ignore:
                    log.verbose("Ignoring %r" % os.path.join(_root, _dir_name)[len(src_dir):])
                    _dir_names.remove(_dir_name)

            if dest_dir == self.settings.NewMoviesDir:
                if self.args.suppress_movies:
                   log.verbose('Skipping Movie: %s' % src_dir)
                   continue

            # Build Directory Structure
            _sub_dir = _root[len(os.path.split(src_dir)[0]):].lstrip(os.sep)
#            _sub_dir = os.path.split(_root.rstrip(os.sep))[1]
            dest_dir = os.path.join(_tgt_dir, _sub_dir)
            # create destination directory
            if not os.path.exists(dest_dir):
                log.debug("Creating %r" % dest_dir)
                try:
                    os.makedirs(dest_dir)
                    os.chmod(dest_dir, 0775)
                except OSError, exc:
                    log.error("Failed to create %r (%s)" % (dest_dir, exc))

            # find RARed files
            _rar_list = []
            _file_list = []
            for _file in sorted(_file_names):
                if self._ignored(_file) and self.args.ignore:
                    log.verbose("Ignoring %r" % os.path.join(_root, _file))
                    continue
                if self.RAR_RE.search(_file):
                    _rar_list.append(_file)
                else:
                    _file_list.append(_file)

            # handle normal files
            for _file in _file_list:
                _file = os.path.join(_root, _file)
                self._distribute_file(_file, dest_dir)

            # skip RAR parts, except the first one
            for _file in _rar_list:
                if self.RAR_PART_RE.search(_file.lower()) \
                        and not (_file.lower().endswith(".part01.rar") \
                                 or _file.lower().endswith(".part001.rar")):
                    continue

                _file = os.path.join(_root, _file)
                if _file.lower().endswith(".rar"):
                    log.verbose("Unpacking: {}".format(os.path.basename(_file)))
                    self._unpack_requested(_file, dest_dir)
                    _files_req_unpack = True

            if _files_req_unpack:
                if self.args.clean_up_name:
                    self._clean_names(dest_dir)
                _files_req_unpack = False

        return _base_dir

    def _clean_names(self, dest_dir):
        # map ugly scene short names to original directory name
        # get common prefix of unpacked media files
        log.trace('_clean_names:%s' % (dest_dir))

        for _root, _dir_names, _file_names in os.walk(dest_dir):
            _src_name = os.path.basename(_root.rstrip(os.sep))
            for _file in _file_names:
                try:
                    os.utime(os.path.join(_root, _file), None)
                except:
                    continue

            _media = [os.path.splitext(i)[0] for i in _file_names if any(i.lower().endswith(k) for k in self.settings.MediaExt)]
            _prefix = os.path.commonprefix(_media)
            if _prefix.lower().endswith(".cd"):
                _prefix = _prefix[:-3]
            log.debug("Common Prefix: %s" % _prefix)

            # rename all files that have that prefix
            self.group1_re = re.compile("^(\[.+?\][ \._\-][ \._\-]?[ \._\-]?)?(?P<filename>.*)")
            self.group2_re = re.compile("^({.+?}[ \._\-][ \._\-]?[ \._\-]?)?(?P<filename>.*)")
            # @TODO Needs work, Series with only Season in dir name

            if _prefix:
                for _file in _file_names:
                    if _file.startswith(_prefix):
                        # get nice name, omitting any duplicate information
                        _nice_name, ext = os.path.splitext(_file)
                        _nice_name = _nice_name[len(_prefix):]
                        for i, ch in enumerate(reversed(_nice_name.lower())):
                            if _src_name.lower()[-i - 1] == ch:
                                _nice_name = _nice_name[:-1]
                            else:
                                break
                        _nice_name = _src_name + _nice_name + ext.lower()

                        # Strip Group Name
                        if _nice_name[:1] == '[':
                            _match = self.group1_re.match(_nice_name)
                            if _match:
                                _nice_name = _match.group('filename')
                        elif _nice_name[:1] == '{':
                            _match = self.group2_re.match(_nice_name)
                            if _match:
                                _nice_name = _match.group('filename')

                        # now make it pretty
                        log.debug("Cleanup Name %r to %r" % (_file, _nice_name))
                        try:
                            os.rename(os.path.join(dest_dir, _file), os.path.join(dest_dir, _nice_name))
                        except OSError, exc:
                            log.error("Failed to rename %r to %r (%s)" % (_file, _nice_name, exc))
        return

    def _ignored(self, name):
        """ Check for ignored pathnames.
        """
        return any(fnmatch.fnmatch(name.lower(), pattern) for pattern in self.settings.IgnoreGlob)

    def _unpack_requested(self, rar_file, dest_dir):
        """ Unpack an archive.
        """
        log.trace('_unpack_requested: {} Dest: {}'.format(rar_file, dest_dir))

        cmd = ["unrar", "e", "-idq", "-ep", "-o-", "-ts", "-x *.rar", os.path.abspath(rar_file)]
        log.trace("Calling %s" % cmd)
        try:
            process = Popen(cmd, shell=False, stdin=None, stdout=PIPE, stderr=PIPE, cwd=dest_dir)
            process.wait()
            output = process.stdout.read()
            if output:
                log.trace('unrar: %s' % output)
            output = process.stderr.read()
            if output:
                log.trace('unrar: %s' % output)
        except subprocess.CalledProcessError, exc:
            log.error("Command %s returned with RC=%d" % (cmd, exc.returncode))
        return


if __name__ == '__main__':

    logger.initialize()
    library = Distribute()

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

    if len(library.args.library) == 0:
        library.options.parser.error("Missing required Library pathname for File/Directory to be Distributed")
        msg = 'Missing Scan Starting Point (Input Directory), Using Default: {}'.format(library.settings.NewSeriesDir)

    for _lib_path in library.args.library:
        if os.path.exists(_lib_path):
            library.distribute(_lib_path)
        else:
            log.error('Skipping Distribution: Unable to find File/Directory: {}'.format(_lib_path))
