#!/usr/bin/env python
"""
Author: AJ Reynolds
Date: 11-19-2011
Purpose:
    Program to list recently downloaded shows

"""

from __future__ import division
from library import Library
from common import logger
from subprocess import check_call, CalledProcessError
from datetime import datetime, timedelta
import logging
import os
import re
import operator
import errno
import sys
import tempfile
import time

__pgmname__ = 'library.series.newshows'
__version__ = '@version: $Rev$'

__author__ = "@author: AJ Reynolds"
__copyright__ = "@copyright: Copyright 2011, AJ Reynolds"
__status__ = "@status: Development"
__license__ = "@license: GPL"

__maintainer__ = "@organization: AJ Reynolds"
__credits__ = []

log = logging.getLogger(__pgmname__)

logger.initialize()

TEMP_LOC = "/home/aj/newshows"
MB = 1024 ** 2
GB = 1024 ** 3

class NewShows(Library):

    def __init__(self):

        super(NewShows, self).__init__()

        group1 = self.options.parser.add_argument_group("Users", description=None)
        group1.add_argument("-a", "--aly", dest="user", default='',
             action="store_const", const="tigger",
             help="Display the Newshows for Aly")
        group1.add_argument("-k", "--kim", dest="user",
             action="store_const", const="goofy",
             help="Display the Newshows for Kim")
        group1.add_argument("-m", "--michelle", dest="user",
             action="store_const", const="eeyore",
             help="Display the Newshows for Michelle")
        group1.add_argument("-p", "--peterson", dest="user",
             action="store_const", const="pluto",
             help="Display the Newshows for Ben")

        group2 = self.options.parser.add_argument_group("Directories", description=None)
        group2.add_argument("-i", "--input-directory", dest="InputDir",
             action="store", type=str, default="",
             help="Directory to be checked for new downloads")
        group2.add_argument("-o", "--output-directory", dest="OutputDir",
             action="store", type=str, default="",
             help="Directory to be used to build DVD Image")

        group3 = self.options.parser.add_argument_group("Modifers", description=None)
        group3.add_argument("-d", "--days-back", dest="days_back",
             action="store", type=str, default="-7",
             help="Number of days back for display")
        group3.add_argument("-x", "--exclude-mkv", dest="exclude_mkv",
             action="store_true", default=False,
             help="Exclude all MKV files")

        group4 = self.options.parser.add_argument_group("DVD Options", description=None)
        group4.add_argument("-b", "--build-list", dest="build",
             action="store_true", default=False,
             help="Build input files for DVD Image")
        group4.add_argument("-f", "--format-dvd", dest="format_dvd",
             action="store_true", default=False,
             help="Format DVD prior to writing DVD Image to DVD Drive")
        group4.add_argument("-r", "--remove", dest="remove",
             action="store_true", default=False,
             help="Delete any files created to support DVD image")
        group4.add_argument("-w", "--write-dvd", dest="write_dvd",
             action="store_true", default=False,
             help="Write DVD Image to DVD Drive")

        self.NewFiles = []

    def findShows(self):
        self._build_findcmd_options()
        self.BuildList()
        self.Print()
        if self.args.build:
            self.BuildDVD()
        return

    def BuildList(self):
        PRINT_OPTS = ['-printf', '%p@%Ty%Tm%Td-%TH%TM-%TS@%s\n']
        _tv_parse = re.compile(
            '''
            ^({}/)             			  # Directory
            (?P<series>.*)                        # Series Name
            (/Season.)                            # Season Literal
            (?P<season>[0-9]+)                    # Season Number (##)
            (/E)                                  # Episode Literal
            (?P<epno1>[0-9][0-9]+)                # Starting Episode Number (##)
            [\.\- \/]?                            # Sep 1
            (E)?                                  # Optional Episode Literal
            (?P<epno2>[0-9][0-9]+)?               # Ending Episode Number (##)
            (?P<epname>.*)                        # Title
            \.(?P<ext>....?)$                     # extension
            '''.format(library.settings.SeriesDir), re.X | re.I)

        _links_parse = re.compile(
            '''
            ^(/srv/Links/.*/Series/)              # Directory
            (?P<series>.*)                        # Series Name
            (/Season.)                            # Season Literal
            (?P<season>[0-9]+)                    # Season Number (##)
            (/E)                                  # Episode Literal
            (?P<epno1>[0-9][0-9]+)                # Starting Episode Number (##)
            [\.\- \/]?                            # Sep 1
            (E)?                                  # Optional Episode Literal
            (?P<epno2>[0-9][0-9]+)?               # Ending Episode Number (##)
            (?P<epname>.*)                        # Title
            \.(?P<ext>....?)$                     # extension
            ''', re.X | re.I)

        _find_cmd = ['find',
                     self.args.InputDir,
                     '-ignore_readdir_race',
                     '-maxdepth',
                     '10',
                     '-path',
                     library.settings.NewSeriesDir,
                     '-prune',
                     '-o',
                     '-path',
                     '/mnt/DadVision/Series/lost+found',
                     '-prune',
                     '-o',
                     '-daystart',
                     '-follow',
                     '-type',
                     'f'
                     ]

        _find_cmd.extend(self.args.CmdLineArgs)
        _find_cmd.extend(PRINT_OPTS)

        try:
            _temp = tempfile.NamedTemporaryFile()
            check_call(_find_cmd, shell=False, stdin=None, stdout=_temp, stderr=None, cwd=os.path.join(self.args.InputDir))
        except CalledProcessError, exc:
#             log.error("Find Command for Series Exclusions returned with RC=%d" % (exc.returncode))
#             sys.exit(1)
            pass

        try:
            f = open(_temp.name, 'r')
            for _line in f.readlines():
                _file_name, _date_stamp, _file_size = _line.rstrip("\n").split('@')
                _series = _tv_parse.match(_file_name)
                if not _series:
                    _series = _links_parse.match(_file_name)
                    if not _series:
                        log.error('Unable to Parse: Skipping: %s' % _file_name)
                        continue
                _file_size = int(_file_size)
                _series_name = _series.group('series')
                _season_number = int(_series.group('season'))
                _episode_number = "E" + _series.group('epno1')
                _episode_title = _series.group('epname')
                _ext = _series.group('ext')
                _air_date = _date_stamp[0:6]

                self.NewFiles.append({'FileName' : _file_name,
                                      'SeriesName' : _series_name,
                                      'SeasonNumber' : _season_number,
                                      'EpisodeNumber' : _episode_number,
                                      'EpisodeTitle' : _episode_title,
                                      'AirDate' : _air_date,
                                      'FileSize' : _file_size,
                                      'Ext' : _ext
                                      })

        finally:
            # Automatically cleans up the file
            self.NewFiles.sort(key=operator.itemgetter('FileName'))
            _temp.close()

    def Print(self):
        if self.NewFiles == []:
            log.warning('No Files Found, Possible BuildList was not complete')
            return 1

        _headers = "%-25.25s %s%02.2s %-3.3s %-28.28s %-3.3s %8.8s %4s"
        _details = "%-25.25s %s%02.2d %-3.3s %-28.28s %-3.3s %7.6s%s %4s"
        _totals = "%-67s%05.5sG"
        _total_size = 0

        log.verbose('%s %s - Date: %s' % (self.args.user, self.args.days_back, time.strftime("%a %b %d %Y %H:%M %Z")))
        log.verbose(_headers % ("Show", "S", "EA", "EP", "Title", "EXT", "Filesize", "DayB"))
        log.verbose(_headers % ("-------------------------", "-", "--", "---", "----------------------------", "---", "--------", "----"))
        print '%s %s - Date: %s' % (self.args.user, self.args.days_back, time.strftime("%a %b %d %Y %H:%M %Z"))
        print _headers % ("Show", "S", "EA", "EP", "Title", "EXT", "Filesize", "DayB")
        print _headers % ("-------------------------", "-", "--", "---", "----------------------------", "---", "--------", "----")

        _today = datetime.today()
        _date_format = "%y%m%d"

        for _entry in self.NewFiles:
            _series_name = _entry['SeriesName']
            _season_number = _entry['SeasonNumber']
            _episode_number = _entry['EpisodeNumber']
            _episode_title = _entry['EpisodeTitle']
            _air_date = _entry['AirDate']
            _file_size = _entry['FileSize']
            _ext = _entry['Ext']

            b = datetime.strptime(_air_date, _date_format)
            _delta = _today - b

            _total_size = _total_size + _file_size
            if _file_size > GB:
                _file_size = _file_size / GB
                log.verbose(_details % (_series_name, "S", _season_number, _episode_number, _episode_title, _ext, _file_size, "G", _delta.days))
                print _details % (_series_name, "S", _season_number, _episode_number, _episode_title, _ext, _file_size, "G", _delta.days)
            else:
                _file_size = _file_size / MB
                log.verbose(_details % (_series_name, "S", _season_number, _episode_number, _episode_title, _ext, _file_size, "M", _delta.days))
                print _details % (_series_name, "S", _season_number, _episode_number, _episode_title, _ext, _file_size, "M", _delta.days)

        log.verbose(_headers % ("-------------------------", "-", "--", "---", "----------------------------", "---", "--------", "----"))
        print _headers % ("-------------------------", "-", "--", "---", "----------------------------", "---", "--------", "----")
        if _total_size > GB:
            log.verbose("{:64s} {: >8,.2f}GB".format('TOTAL->', _total_size / GB))
            print "{:64s} {: >8,.2f}GB".format('TOTAL->', _total_size / GB)
        else:
            log.verbose("{:64s} {: >8,.2f}MB".format('TOTAL->', _total_size / MB))
            print "{:64s} {: >8,.2f}MB".format('TOTAL->', _total_size / MB)
            print  " "

    def BuildDVD(self):

        if self.NewFiles == []:
            log.warning('No Files Found, Possible BuildList was not complete')
            return 1

        _target_dir = os.path.join(TEMP_LOC, self.args.user)

        for _entry in self.NewFiles:
            _file_name = _entry['FileName']
            _series_name = _entry['SeriesName']
            _season_number = _entry['SeasonNumber']
            _episode_number = _entry['EpisodeNumber']
            _episode_title = _entry['EpisodeTitle']
            _ext = _entry['Ext']
            _folder = os.path.join(os.path.join(_target_dir, _series_name), 'Season %s' % str(_season_number))
            _symlink = os.path.join(_folder, os.path.basename(_file_name))

            if os.path.exists(_symlink):
                continue

            try:
                if not os.path.exists(_folder):
                    os.makedirs(_folder, 0777)
                os.symlink(os.path.realpath(_file_name), _symlink)
                os.lchown(_symlink, 1000, 100)
                log.debug('Created symlink for: %s' % (_symlink))
            except OSError as exc:  # Python >2.5
                if exc.errno == errno.EEXIST:
                    pass
                else: raise

        if self.args.format_dvd:
            os.system('dvd+rw-format -force /dev/sr0')
        if self.args.write_dvd:
            burn_cmd = 'myback -main_dir -auto -dir_script_adr "" -dir_list_adr "" -content_list_adr "" -split_list_adr "" -info_script off %s' % _target_dir
            os.system(burn_cmd)
        if self.args.remove:
            os.system('rm -r %s' % _target_dir)

    def _build_findcmd_options(self):
        LOW_DEF_SUFFIX = "hdtv"
        AVI_ONLY = ['-iname', '*.avi']
        MKV_AND_AVI = ['-iregex', '^.*[mkv|avi|mp4]']
        XCLUDE_HDTV = ['-not', '-ipath', LOW_DEF_SUFFIX]

        if self.args.InputDir:
            if not os.path.exists(self.args.InputDir):
                log.error('Request Input Directory Does Not Exist: {}'.format(self.args.InputDir))
                sys.exit(1)
            if not self.args.user:
                self.args.user = 'Directory'
        elif self.args.user:
            self.args.InputDir = os.path.join(self.settings.SubscriptionDir, self.args.user, "Series")
        else:
            self.args.user = 'All'
            self.args.InputDir = self.settings.SeriesDir

        if int(self.args.days_back) > 0:
            self.args.days_back = int(self.args.days_back) * -1

        self.args.CmdLineArgs = []

        if self.args.exclude_mkv:
            self.args.CmdLineArgs.extend(AVI_ONLY)
        else:
            self.args.CmdLineArgs.extend(MKV_AND_AVI)
            self.args.CmdLineArgs.extend(XCLUDE_HDTV)

#        self.args.CmdLineArgs.extend(['-iregex', '^(?!.*lost.found)$'])

        self.args.CmdLineArgs.extend(['-mtime', str(self.args.days_back)])

        return


if __name__ == "__main__":

    from library import Library
    from logging import INFO, WARNING, ERROR, DEBUG

    logger.initialize()

    library = NewShows()

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

    library.findShows()

#     if len(library.args.library) == 0:
#         msg = 'Missing Scan Starting Point (Input Directory), Using Default: {}'.format(library.settings.NewSeriesDir)
#         log.info(msg)
#         library.args.library = [library.settings.NewSeriesDir]
#
#     for _lib_path in library.args.library:
#         if os.path.exists(_lib_path):
#             library.renameSeries(_lib_path)
#         else:
#             log.error('Skipping Rename: Unable to find File/Directory: {}'.format(_lib_path))
