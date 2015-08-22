#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Purpose:
    Program to distribute the files from a source to a target library. If needed,
    the files will be unzipped and renamed to meet the library standard.
"""
from subprocess import check_call, Popen, PIPE, CalledProcessError
import fnmatch
import logging
import os
import re
import sys
import traceback

from guessit import guess_file_info

from library import Library
from common import logger
from common.exceptions import UnexpectedErrorOccured, InvalidFilename
from library.movie.rename import RenameMovie
from library.series.rename import RenameSeries


__pgmname__ = 'library.distribute'
__version__ = '@version: $Rev$'

__author__ = "@author: AJ Reynolds"
__copyright__ = "@copyright: Copyright 2011, AJ Reynolds"
__status__ = "@status: Development"
__license__ = "@license: GPL"

__maintainer__ = "@organization: AJ Reynolds"
__credits__ = []

log = logging.getLogger(__pgmname__)

# def useLibraryLogging(func):
# 	def wrapper(self, *args, **kw):
# 		# Set the library name in the logger
# 		logger.set_library(self.contentType)
# 		try:
# 			return func(self, *args, **kw)
# 		finally:
# 			logger.set_library('')
# 	return wrapper

class Distribute(Library):

    def __init__(self):
        log.trace('__init__')

        super(Distribute, self).__init__()

        dist1 = self.options.parser.add_argument_group("Media Type Options", description=None)
        dist1.add_argument("-s", "--series", dest="content", default="",
            action="store_const", const="Series",
            help="Process as Series")
        dist1.add_argument("-m", "--movies", dest="content",
            action="store_const", const="Movies",
            help="Process as Movies")
        dist1.add_argument("-n", "--non-video", dest="content",
            action="store_const", const="NonVideo",
            help="Process as Non-Video")

        dist2 = self.options.parser.add_argument_group("Distribute Options", description=None)
        dist2.add_argument("--no-cleanup", "--nc", dest="clean_up_name",
            action="store_false", default=True,
            help="Do not clean-up names from unpack")
        dist2.add_argument("--no-ignore", "--ni", dest="ignore",
            action="store_false", default=True,
            help="Process all files, Ignore nothing")
        dist2.add_argument("--no-movies", dest="suppress_movies",
            action="store_true", default=False,
            help="Do Not Process Movie files")
        dist2.add_argument("--no-rename", "--nr", dest="rename",
            action="store_false", default=True,
            help="Do Not Rename the File from NEW")

        self.rename_series = RenameSeries()
        self.rename_movies = RenameMovie()

        self.contentType = None
        self.RegEx = []

        try:
            self.RegEx.append(re.compile('(.*)[\._ \-][s|season]([0-9]+)[e|x]?[0-9]?([^\\/]*)', re.IGNORECASE))
            self.RegEx.append(re.compile('(.*)[\._ \-][s]?([0-9]+)[e|x][0-9]?([^\\/]*)', re.IGNORECASE))
            self.RegEx.append(re.compile('(.*)[\._ \-]([0-9]+\.[0-9]+\.[0-9]+)([^\\/]*)', re.IGNORECASE))
            self.RegEx.append(re.compile('(.*)[\._ \-]season[\._ \-]([0-9]+)([^\\/]*)', re.IGNORECASE))
        except re.error, errormsg:
            log.error("Distribute.__init__: Invalid Series RegEx pattern: %s" % (errormsg))
            raise UnexpectedErrorOccured("Distribute.__init__: Invalid Series RegEx: %s" % (errormsg))

        self.RAR_RE = re.compile(r"\.([rR][aA][rR]|[rR]\d{2,3})$")
        self.RAR_PART_RE = re.compile(r"\.part\d{2,3}\.rar$")

#	@useLibraryLogging
    def distribute(self, pathname):
        log.trace('ProcessFile: %s' % pathname)

        pathname = os.path.abspath(pathname)

        #TODO: Check to ensure request within DadVision Scope
        if os.path.isfile(pathname):
            log.trace("file - %r..." % (pathname))
            self.distributeFile(pathname)
        elif os.path.isdir(pathname):
            log.trace("directory ...%r" % (os.path.basename(pathname)))
            try:
                self.distributeDirectory(pathname)
            except KeyboardInterrupt:
                sys.exit(8)
            except:
                an_error = traceback.format_exc()
                log.error(traceback.format_exception_only(type(an_error), an_error)[-1])
                log.error('Distribute skipped for: {}'.format(os.path.basename(pathname)))
                return
        else:
            raise InvalidFilename('Content Type can not be determined due to naming convention: Skipped')

#	@useLibraryLogging
    def distributeFile(self, sourceFile):
        log.trace('distributeFile: %s %s' % (self.contentType, sourceFile))
        """ Move or copy a single file.
        """
        # ignored file?
        if self._ignored(os.path.basename(sourceFile)) and self.args.ignore:
            log.verbose("Ignoring %r!" % (sourceFile))
            return

        if os.path.splitext(sourceFile)[1][1:].lower() not in self.settings.MediaExt:
            log.verbose("Ignoring %r!" % (sourceFile))
            return

        self._setContentType(sourceFile)
        if self.contentType == 'Movies' and self.args.suppress_movies:
            log.verbose('Skipping Movie: %s' % sourceFile)
            return

        if self.contentType == "Series":
            _destinationDir = self.settings.NewSeriesDir
        elif self.contentType == "Movies":
            _destinationDir = self.settings.NewMoviesDir
        else:
            _destinationDir = self.settings.UnpackDir

        # Adds the last directory to target name
        _destinationDir = os.path.join(_destinationDir, os.path.basename(os.path.dirname(sourceFile)))
        _distributedFile = os.path.join(_destinationDir, os.path.basename(sourceFile))
        if os.path.exists(_distributedFile) and os.path.getsize(_distributedFile) == os.path.getsize(sourceFile):
            log.verbose("Skipped Copy: Already at Destination:")
            log.verbose("         {}".format(os.path.basename(sourceFile)))
            log.verbose("         {}".format(os.path.basename(_distributedFile)))
        else:
            # make sure target folder exists
            if not os.path.exists(_destinationDir):
                log.debug("Creating %r" % _destinationDir.rstrip(os.sep) + os.sep,)
                os.makedirs(_destinationDir)
                os.chmod(_destinationDir, 0775)

            # copy file, possibly across devices.
            log.verbose("Copying: {}".format(_destinationDir))
            log.verbose("         {}".format("<+<"))
            log.verbose("         {}".format(sourceFile))

#			indicator = "<+<"
#			action = shutil.copy2
#				action(sourceFile, _distributedFile)

            try:
                cmd = ['rsync', '-rptvhogLR', '--progress',
                       '--partial-dir=.rsync-partial', os.path.basename(sourceFile), _destinationDir]
                log.verbose(' '.join(cmd))
                check_call(cmd, shell=False, stdin=None, stdout=None,
                           stderr=None, cwd=os.path.dirname(sourceFile))
            except CalledProcessError, exc:
                log.error("Incremental rsync Command returned with RC=%d, Ending" % (exc.returncode))
                raise UnexpectedErrorOccured(exc)

        try:
            if self.args.rename:
                if self.contentType == "Series":
                    self.rename_series.renameFile(_distributedFile)
                elif self.contentType == "Movies":
                    self.rename_movies.renameMovie(_distributedFile)
        except:
            an_error = traceback.format_exc()
            log.error(traceback.format_exception_only(type(an_error), an_error)[-1])
            log.error('Rename skipped for: {}'.format(os.path.basename(_distributedFile)))

        return

#	@useLibraryLogging
    def distributeDirectory(self, sourceDirectory):
        """ Move or copy a folder.
        """
        log.trace('distributeDirectory: %s %s' % (self.contentType, sourceDirectory))

        for _root, _dir_names, _file_names in os.walk(sourceDirectory):
            # don't scan ignored subdirs
            for _dir_name in _dir_names:
                if self._ignored(_dir_name) and self.args.ignore:
                    log.verbose("Ignoring %r" % os.path.join(_root, _dir_name)[len(sourceDirectory):])
                    _dir_names.remove(_dir_name)

            # sort file types contained in directory
            _requiresUnpack = []
            _simpleCopyOK = []
            for _file in sorted(_file_names):
                if self._ignored(_file) and self.args.ignore:
                    log.verbose("Ignoring %r" % os.path.join(_root, _file))
                    continue
                if self.RAR_RE.search(_file):
                    _requiresUnpack.append(os.path.join(_root, _file))
                else:
                    _simpleCopyOK.append(os.path.join(_root, _file))

            # handle normal files
            for _file in _simpleCopyOK:
                try:
                    self.distributeFile(_file)
                except:
                    an_error = traceback.format_exc()
                    log.verbose(traceback.format_exception_only(type(an_error), an_error)[-1])
                    log.warning('Distribute skipped for: {}'.format(os.path.basename(_file)))

            # handle unpacking files
            if len(_requiresUnpack) > 0:
                self._unpackDirectory(_requiresUnpack)

        return

    def _setContentType(self, pathname):
        log.trace('_setContentType: Pathname: {}'.format(pathname))

        if self.args.content:
            if self.args.content == 'Series':
                self.contentType = "Series"
            elif self.args.content == "Movies":
                self.contentType = "Movies"
            else:
                self.contentType = "NonVideo"
            return

        if pathname[:len(self.settings.DownloadMovies)] == self.settings.DownloadMovies:
            self.contentType = 'Movies'
            return
        elif pathname[0][:len(self.settings.DownloadSeries)] == self.settings.DownloadSeries:
            self.contentType = 'Series'
            return

        _guessit_info = guess_file_info(pathname)
        print '-'*60
        print _guessit_info['type']
        print '-'*60

        if _guessit_info['type'] == 'episode':
            self.contentType = "Series"
            return
        elif _guessit_info['type'] == 'movie':
            self.contentType = 'Movies'
            return

        _file_name = os.path.basename(pathname)

        for cRegEx in self.RegEx:
            _series = cRegEx.search(_file_name)
            if _series:
                _series_name = _series.group(1)
                log.debug("Series: %s" % _series_name)
                self.contentType = "Series"
                return

        if any(pathname.lower().count(key) > 0 for key in self.settings.MovieGlob):
            self.contentType = "Movies"
            return
        else:
            self.contentType = "NonVideo"
            return

    def _unpackDirectory(self, unpackFileList):

        self._setContentType(unpackFileList[0])

        if self.contentType == 'Series':
            _destinationDir = os.path.join(self.settings.SeriesDir,
                                           self.settings.NewSeriesDir,
                                           os.path.basename(os.path.dirname(unpackFileList[0]))
                                            )
        elif self.contentType == 'Movies':
            _destinationDir = os.path.join(self.settings.MoviesDir,
                                           self.settings.NewMoviesDir,
                                           os.path.basename(os.path.dirname(unpackFileList[0]))
                                            )
        else: _destinationDir = os.path.join(self.settings.UnpackDir,
                                             'UNKNOWN',
                                             os.path.basename(os.path.dirname(unpackFileList[0]))
                                            )

#        if unpackFileList[0][:len(self.settings.DownloadDir)] == self.settings.DownloadDir:
#            _destinationDir = os.path.dirname(unpackFileList[0][len(self.settings.DownloadDir)+1:])
#        elif unpackFileList[0][:len(self.settings.DownloadMovies)] == self.settings.DownloadMovies:
#            _destinationDir = os.path.dirname(unpackFileList[0][len(self.settings.DownloadMovies)+1:])
#        elif unpackFileList[0][:len(self.settings.DownloadSeries)] == self.settings.DownloadSeries:
#            _destinationDir = os.path.dirname(unpackFileList[0][len(self.settings.DownloadMovies)+1:])
#        else:
#            _destinationDir = 'UNKNOWN'

        if self.contentType == 'Series': _destinationDir = os.path.join(self.settings.NewSeriesDir, _destinationDir)
        elif self.contentType == 'Movies': _destinationDir = os.path.join(self.settings.NewMoviesDir, _destinationDir)
        else: _destinationDir = os.path.join(self.settings.UnpackDir, _destinationDir)

        # create destination directory
        if not os.path.exists(_destinationDir):
            log.debug("Creating %r" % _destinationDir)
            os.makedirs(_destinationDir)
            os.chmod(_destinationDir, 0775)

        # skip RAR parts, except the first one
        _cleanupfilesCreated = False
        for _file in unpackFileList:
            if self.RAR_PART_RE.search(_file.lower()) \
                    and not (_file.lower().endswith(".part01.rar")
                             or _file.lower().endswith(".part001.rar")):
                continue

            if _file.lower().endswith(".rar"):
                log.verbose("Unpacking: {}".format(os.path.basename(_file)))
                self._unpackFiles(_file, _destinationDir)
                _cleanupfilesCreated = True

        if _cleanupfilesCreated:
            if self.args.clean_up_name:
                self._clean_names(_destinationDir)
            _cleanupfilesCreated = False

        try:
            if self.args.rename:
                if self.contentType == "Series":
                    self.rename_series.renameSeries(_destinationDir)
                elif self.contentType == "Movies":
                    self.rename_movies.renameMovie(_destinationDir)
        except:
            an_error = traceback.format_exc()
            log.error(traceback.format_exception_only(type(an_error), an_error)[-1])
            log.error('Rename skipped for: {}'.format(os.path.basename(_destinationDir)))

        return

    def _unpackFiles(self, rar_file, destinationDir):
        """ Unpack an archive.
        """
        log.trace('_unpackFiles: {} Dest: {}'.format(rar_file, destinationDir))

        cmd = ["unrar", "e", "-idq", "-ep", "-o-", "-ts", "-x *.rar", os.path.abspath(rar_file)]

        log.trace("Calling %s" % cmd)
        process = Popen(cmd, shell=False, stdin=None, stdout=PIPE, stderr=PIPE, cwd=destinationDir)
        process.wait()

        output = process.stdout.read()
        if output:
            log.verbose('unrar: %s' % output)

        output = process.stderr.read()
        if output:
            log.error('unrar: %s' % output)

        return

#	@useLibraryLogging
    def _clean_names(self, destinationDir):
        # map ugly scene short names to original directory name
        # get common prefix of unpacked media files
        log.trace('_clean_names:%s' % (destinationDir))

        for _root, _dirs, _files in os.walk(destinationDir):
            _src_name = os.path.basename(_root)
            for _file in _files:
                try:
                    os.utime(os.path.join(_root, _file), None)
                except:
                    continue

            _media = [os.path.splitext(i)[0] for i in _files if any(i.lower().endswith(k) for k in self.settings.MediaExt)]
            _prefix = os.path.commonprefix(_media)
            if _prefix.lower().endswith(".cd"):
                _prefix = _prefix[:-3]
            log.debug("Common Prefix: %s" % _prefix)

            # rename all files that have that prefix
            self.group1_re = re.compile("^(\[.+?\][ \._\-][ \._\-]?[ \._\-]?)?(?P<filename>.*)")
            self.group2_re = re.compile("^({.+?}[ \._\-][ \._\-]?[ \._\-]?)?(?P<filename>.*)")
            # @TODO Needs work, Series with only Season in dir name

            if _prefix:
                for _file in _files:
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
                            os.rename(os.path.join(destinationDir, _file),
                                      os.path.join(destinationDir, _nice_name))
                        except OSError, exc:
                            log.error("Failed to clean up %r to %r (%s)" % (_file, _nice_name, exc))
                            an_error = traceback.format_exc()
                            log.error(traceback.format_exception_only(type(an_error), an_error)[-1])

        return

    def _ignored(self, name):
        """ Check for ignored pathnames.
        """
        return any(fnmatch.fnmatch(name.lower(), pattern) for pattern in self.settings.IgnoreGlob)


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
