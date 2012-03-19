#!/usr/bin/env python
"""
Author: AJ Reynolds
Date: 11-19-2011
Purpose:
    Program to list recently downloaded shows

"""

from __future__ import division
from daddyvision.common.options import OptionParser, OptionGroup
from daddyvision.common.settings import Settings
from daddyvision.common import logger
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

__author__ = "AJ Reynolds"
__copyright__ = "Copyright 2011, 2012, AJ Reynolds"
__credits__ = []
__license__ = "GPL"

__pgmname__ = 'newshows'
__version__ = '$Rev$'

__maintainer__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"
__status__ = "Development"

log = logging.getLogger(__pgmname__)

logger.initialize()
config = Settings()

TRACE = 5
VERBOSE = 15

TEMP_LOC = "/home/aj/newshows"
MB = 1024**2
GB = 1024**3

_tv_parse = re.compile(
            '''
            ^(/mnt/DadVision/Series/)             # Directory
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
_links_parse = re.compile(
            '''
            ^(/mnt/Links/.*/Series/)              # Directory
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

class NewShows(list):


    def __init__(self, options):
        self.NewFiles = []
        self.options = options
        self._build_findcmd_options()
        self.BuildList()

        return

    def BuildList(self):
        PRINT_OPTS =['-printf', '%p@%Ty%Tm%Td-%TH%TM-%TS@%s\n']

        _find_cmd = ['find',
                     self.options.InputDir,
                     '-ignore_readdir_race',
                     '-daystart',
                     '-follow',
                     '-maxdepth',
                     '10',
                     '-type',
                     'f'
                     ]

        _find_cmd.extend(self.options.CmdLineArgs)
#        _find_cmd.extend(['-path', os.path.join(self.options.InputDir,'Sherlock'), '-prune'])
        _find_cmd.extend(PRINT_OPTS)

        try:
            _temp = tempfile.NamedTemporaryFile()
            check_call(_find_cmd, shell=False, stdin=None, stdout=_temp, stderr=None, cwd=os.path.join(self.options.InputDir))
        except CalledProcessError, exc:
            log.error("Find Command for Series Exclusions returned with RC=%d" % (exc.returncode))
            sys.exit(1)

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

        log.verbose('%s %s - Date: %s' % (self.options.user, self.options.days_back, time.strftime("%a %b %d %Y %H:%M %Z")))
        log.verbose(_headers % ("Show", "S", "EA", "EP", "Title", "EXT", "Filesize", "DayB"))
        log.verbose(_headers % ("-------------------------", "-", "--", "---", "----------------------------", "---", "--------", "----"))
        print '%s %s - Date: %s' % (self.options.user, self.options.days_back, time.strftime("%a %b %d %Y %H:%M %Z"))
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
                _file_size = _file_size/GB
                log.verbose(_details % (_series_name, "S", _season_number, _episode_number, _episode_title, _ext, _file_size, "G", _delta.days))
                print _details % (_series_name, "S", _season_number, _episode_number, _episode_title, _ext, _file_size, "G", _delta.days)
            else:
                _file_size = _file_size/MB
                log.verbose(_details % (_series_name, "S", _season_number, _episode_number, _episode_title, _ext, _file_size, "M", _delta.days))
                print _details % (_series_name, "S", _season_number, _episode_number, _episode_title, _ext, _file_size, "M", _delta.days)

        log.verbose(_headers % ("-------------------------", "-", "--", "---", "----------------------------", "---", "--------", "----"))
        print _headers % ("-------------------------", "-", "--", "---", "----------------------------", "---", "--------", "----")
        if _total_size > GB:
            log.verbose("{:64s} {: >8,.2f}GB".format('TOTAL->',_total_size/GB))
            print "{:64s} {: >8,.2f}GB".format('TOTAL->',_total_size/GB)
        else:
            log.verbose("{:64s} {: >8,.2f}MB".format('TOTAL->',_total_size/MB))
            print "{:64s} {: >8,.2f}MB".format('TOTAL->',_total_size/MB)
            print  " "

    def BuildDVD(self):

        if self.NewFiles == []:
            log.warning('No Files Found, Possible BuildList was not complete')
            return 1

        _target_dir = os.path.join(TEMP_LOC, self.options.user)

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
            except OSError as exc: # Python >2.5
                if exc.errno == errno.EEXIST:
                    pass
                else: raise

        if options.format_dvd:
            os.system('dvd+rw-format -force /dev/sr0')
        if options.write_dvd:
            burn_cmd = 'myback -main_dir -auto -dir_script_adr "" -dir_list_adr "" -content_list_adr "" -split_list_adr "" -info_script off %s' % _target_dir
            os.system(burn_cmd)
        if options.remove:
            os.system('rm -r %s' % _target_dir)

    def _build_findcmd_options(self):
        LOW_DEF_SUFFIX = "hdtv"
        AVI_ONLY = ['-iname', '*.avi']
        MKV_AND_AVI = ['-iregex', '^.*[mkv|avi|mp4]']
        XCLUDE_HDTV = ['-not', '-ipath', LOW_DEF_SUFFIX]

        if self.options.InputDir:
            if not os.path.exists(self.options.InputDir):
                log.error('Request Input Directory Does Not Exist: {}'.format(self.options.InputDir))
                sys.exit(1)
            if not self.options.user:
                self.options.user = 'Directory'
        elif self.options.user:
            self.options.InputDir = os.path.join(config.SubscriptionDir, self.options.user, "Series")
        else:
            self.options.user = 'All'
            self.options.InputDir = config.SeriesDir

        if int(self.options.days_back) > 0:
            self.options.days_back = int(self.options.days_back) * -1

        self.options.CmdLineArgs = []

        if self.options.exclude_mkv:
            self.options.CmdLineArgs.extend(AVI_ONLY)
        else:
            self.options.CmdLineArgs.extend(MKV_AND_AVI)
            self.options.CmdLineArgs.extend(XCLUDE_HDTV)

        self.options.CmdLineArgs.extend(['-mtime', str(self.options.days_back)])

        return

class localOptions(OptionParser):

    def __init__(self, unit_test=False, **kwargs):
        OptionParser.__init__(self, **kwargs)

        group = OptionGroup(self, "Users")
        group.add_option("-a", "--aly", dest="user", default='',
             action="store_const", const="aly",
             help="Display the Newshows for Aly")
        group.add_option("-k", "--kim", dest="user",
             action="store_const", const="kim",
             help="Display the Newshows for Kim")
        group.add_option("-m", "--michelle", dest="user",
             action="store_const", const="michelle",
             help="Display the Newshows for Michelle")
        group.add_option("-p", "--peterson", dest="user",
             action="store_const", const="ben",
             help="Display the Newshows for Ben")
        self.add_option_group(group)

        group = OptionGroup(self, "Directories")
        group.add_option("-i", "--input-directory", dest="InputDir",
             action="store", type="string", default="",
             help="Directory to be checked for new downloads")
        group.add_option("-o", "--output-directory", dest="OutputDir",
             action="store", type="string", default="",
             help="Directory to be used to build DVD Image")
        self.add_option_group(group)

        group = OptionGroup(self, "Modifers")
        group.add_option("-d", "--days-back", dest="days_back",
             action="store", type="string", default="-7",
             help="Number of days back for display")
        group.add_option("-x", "--exclude-mkv", dest="exclude_mkv",
             action="store_true", default=False,
             help="Exclude all MKV files")
        self.add_option_group(group)

        group = OptionGroup(self, "DVD Options")
        group.add_option("-b", "--build-list", dest="build",
             action="store_true", default=False,
             help="Build input files for DVD Image")
        group.add_option("-f", "--format-dvd", dest="format_dvd",
             action="store_true", default=False,
             help="Format DVD prior to writing DVD Image to DVD Drive")
        group.add_option("-r", "--remove", dest="remove",
             action="store_true", default=False,
             help="Delete any files created to support DVD image")
        group.add_option("-w", "--write-dvd", dest="write_dvd",
             action="store_true", default=False,
             help="Write DVD Image to DVD Drive")
        self.add_option_group(group)

if __name__ == "__main__":

    parser = localOptions()
    options, args = parser.parse_args()

    log_level = logging.getLevelName(options.loglevel.upper())

    if options.logfile == 'daddyvision.log':
        log_file = '{}.log'.format(__pgmname__)
    else:
        log_file = os.path.expanduser(options.logfile)

    # If an absolute path is not specified, use the default directory.
    if not os.path.isabs(log_file):
        log_file = os.path.join(logger.LogDir, log_file)

    logger.start(log_file, log_level, timed=True)

    log.debug("Parsed command line options: {!s}".format(options))
    log.debug("Parsed arguments: %r" % args)

    shows = NewShows(options)
    shows.Print()
    if options.build:
        shows.BuildDVD()
