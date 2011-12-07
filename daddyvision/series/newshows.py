"""
Author: AJ Reynolds
Date: 11-19-2011
Purpose:
                Program to list recently downloaded shows

"""
from __future__ import division
from configobj import ConfigObj
from optparse import OptionParser, OptionGroup
from exceptions import ConfigValueError
import datetime
import operator
import logging
import logging.handlers
import os
import os.path
import errno
import psutil
import re
import subprocess
import sys
import tempfile
import time

__version__ = '$Rev$'
__pgmname__ = 'newshows'

PgmDir = os.path.dirname(__file__)
HomeDir = os.path.expanduser('~')
ConfigDirB = os.path.join(HomeDir, '.config')
ConfigDir = os.path.join(ConfigDirB, 'xbmcsupt')
LogDir = os.path.join(HomeDir, 'log')
TEMP_LOC = os.path.join(HomeDir, __pgmname__)

if not os.path.exists(LogDir):
        try:
                os.makedirs(LogDir)
        except:
                raise ConfigValueError("Cannot Create Log Directory: %s" % LogDir)

# Set up a specific logger with our desired output level
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
ml = logging.handlers.RotatingFileHandler(os.path.join(LogDir, '%s.log' % __pgmname__), maxBytes=0, backupCount=7)
ch = logging.StreamHandler()
ml.setLevel(logging.INFO)
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s - %(message)s")
ml.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(ml)
logger.addHandler(ch)
ml.doRollover()

TV_SHOW_DIR = "/mnt/TV/Series"
ALY_DIR = "/mnt/Links/aly/Series/"
KIM_DIR = "/mnt/Links/kim/Series/"
MICHELLE_DIR = "/mnt/Links/michelle/Series/"
BEN_DIR = "/mnt/Links/ben/Series/"
TEMP_LOC = "/home/aj/newshows"

ListFile = "/newshows.lst"
LogFile = "log_newshows_"                    #  Filename Has Area Appended Lower in Routine
Default_Sub_Dir = "TV_Shows"
LOW_DEF_SUFFIX = "hdtv"

DRIVE_SPEED = 16
MB = 1024**2
GB = 1024**3
MAX_DVD_SIZE = 4.3 * GB

_tv_parse = re.compile(
            '''
            ^(/mnt/TV/Series/)                    # Directory
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

    def __init__(self):
        self.NewFiles = []

    def BuildList(self, options):

        _avi_only = '-iname *avi'
        _mkv_avi = '\( -iname "*mkv" -o -iname "*avi" \)'

        _new_avi_only = '-iwholename *Season\ 1\/E01\*avi'
        _new_mkv_avi = '\( -iwholename \*Season\ 1\/E01\*mkv -o -iwholename \*Season\ 1\/E01\*avi \)'

        _xclude_hdtv = '-not -ipath %s' % LOW_DEF_SUFFIX
        _print_opts ='-printf "%p"@"%Ty%Tm%Td-%TH%TM-%TS"@"%s\\n"'

        _temp = tempfile.NamedTemporaryFile()


        if not options.new_series_only:
            if options.exclude_mkv:
                _file_types = _avi_only
                _hdtv_dirs = ''
            else:
                _file_types = _mkv_avi
                _hdtv_dirs = _xclude_hdtv
        _find_cmd = ('find %s -ignore_readdir_race -daystart -follow -maxdepth %s -type f -mtime %s %s %s %s > %s' %
                    (options.dir_input, 10, options.days_back, _file_types, _hdtv_dirs, _print_opts,_temp.name))
        os.system(_find_cmd)

        if options.new_series_only or options.new_series:
            if options.exclude_mkv:
                _file_types = _new_avi_only
                _hdtv_dirs = ''
            else:
                _file_types = _new_mkv_avi
                _hdtv_dirs = _xclude_hdtv

            _find_cmd = ('find %s -ignore_readdir_race -daystart -follow -maxdepth %s -type f -mtime %s %s %s %s >> %s' %
                        (options.dir_input, 10, options.days_back, _file_types, _hdtv_dirs, _print_opts,_temp.name))
            os.system(_find_cmd)

        try:
            for _line in _temp.readlines():
                _file_name, _date_stamp, _file_size = _line.rstrip("\n").split('@')
                _series = _tv_parse.match(_file_name)
                if not _series:
                    _series = _links_parse.match(_file_name)
                    if not _series:
                        logger.error('Unable to Parse: Skipping: %s' % _file_name)
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
            logger.warning('No Files Found, Possible BuildList was not complete')
            return 1

        formatter2 = logging.Formatter("%(message)s")
        ch.setFormatter(formatter2)
        if options.log:
            _log_file = os.path.join(TEMP_LOC, '%s_%s.log' % (__pgmname__, options.area))
            try:
                os.remove(_log_file)
            except OSError:
                pass
            lg = logging.FileHandler(os.path.join(_log_file), mode='a', encoding=None, delay=False)
            lg.setLevel(logging.INFO)
            lg.setFormatter(formatter2)
            logger.addHandler(lg)

        _headers = "%-25.25s %s%02.2s %-3.3s %-28.28s %-3.3s %8.8s %-4s"
        _details = "%-25.25s %s%02.2d %-3.3s %-28.28s %-3.3s %7.6s%s %-4s"
        _totals = "%-67s%05.5sG"
        _total_size = 0
        options.dir_input = ALY_DIR

        logger.info('%s %s - Date: %s' % (options.area, options.days_back, time.strftime("%a %b %d %Y %H:%M %Z")))
        logger.info(_headers % ("Show", "S", "EA", "EP", "Title", "EXT", "Filesize", "Day"))
        logger.info(_headers % ("-------------------------", "-", "--", "---", "----------------------------", "---", "--------", "----"))

        for _entry in self.NewFiles:
            _series_name = _entry['SeriesName']
            _season_number = _entry['SeasonNumber']
            _episode_number = _entry['EpisodeNumber']
            _episode_title = _entry['EpisodeTitle']
            _air_date = _entry['AirDate']
            _file_size = _entry['FileSize']
            _ext = _entry['Ext']

            _total_size = _total_size + _file_size
            if _file_size > GB:
                _file_size = _file_size/GB
                logger.info(_details % (_series_name, "S", _season_number, _episode_number, _episode_title, _ext, _file_size, "G", _air_date[4:6]))
            else:
                _file_size = _file_size/MB
                logger.info(_details % (_series_name, "S", _season_number, _episode_number, _episode_title, _ext, _file_size, "M", _air_date[4:6]))

        logger.info(_headers % ("-------------------------", "-", "--", "---", "----------------------------", "---", "--------", "----"))
        if _total_size > GB:
            logger.info("{:64s} {: >8,.2f}GB".format('TOTAL->',_total_size/GB))
        else:
            logger.info("{:64s} {: >8,.2f}MB".format('TOTAL->',_total_size/MB))
            print  " "

        ch.setFormatter(formatter)
        if options.log:
            logger.removeHandler(lg)

        if options.print_log:
            os.system('lpr %s' % _log_file)

    def BuildDVD(self):

        if self.NewFiles == []:
            logger.warning('No Files Found, Possible BuildList was not complete')
            return 1

        _target_dir = os.path.join(TEMP_LOC, options.area)

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
                os.makedirs(_folder, 0777)
                os.symlink(os.path.realpath(_file_name), _symlink)
                os.lchown(_symlink, 1000, 100)
                logger.debug('Created symlink for: %s' % (_symlink))
            except OSError as exc: # Python >2.5
                if exc.errno == errno.EEXIST:
                    pass
                else: raise

        if options.log:
            _log_file = os.path.join(TEMP_LOC, '%s_%s.log' % (__pgmname__, options.area))
            os.system('cp %s %s' % (_log_file, _target_dir))

        if options.format_dvd:
            os.system('dvd+rw-format -force /dev/sr0')
        if options.write_dvd:
            burn_cmd = 'myback -main_dir -auto -dir_script_adr "" -dir_list_adr "" -content_list_adr "" -split_list_adr "" -info_script off %s' % _target_dir
            os.system(burn_cmd)
        if options.remove:
            os.system('rm -r %s' % _target_dir)


if __name__ == "__main__":

    parser = OptionParser(
                          "%prog [options] filename|directory",
                          version="%prog " + __version__
                          )


    parser.add_option("-d", "--days-back", dest="days_back",
                     action="store", type="string", default="-7",
                     help="Number of days back for display")

    group = OptionGroup(parser, "Users")
    group.add_option("-a", "--aly", dest="aly",
                     action="store_true", default=False,
                     help="Display the Newshows for Aly")
    group.add_option("-k", "--kim", dest="kim",
                     action="store_true", default=False,
                     help="Display the Newshows for Kim")
    group.add_option("-m", "--michelle", dest="michelle",
                     action="store_true", default=False,
                     help="Display the Newshows for Michelle")
    group.add_option("-p", "--peterson", dest="ben",
                     action="store_true", default=False,
                     help="Display the Newshows for Ben")

    parser.add_option_group(group)
    group = OptionGroup(parser, "Directories")
    group.add_option("-i", "--input-directory", dest="dir_input",
                     action="store", type="string", default="/mnt/TV/Series",
                     help="Directory to be checked for new downloads")
    group.add_option("-o", "--output-directory", dest="dir_output",
                     action="store", type="string", default="",
                     help="Directory to be used to build DVD Image")
    parser.add_option_group(group)

    group = OptionGroup(parser, "Modifers")

    group.add_option("-x", "--exclude-mkv", dest="exclude_mkv",
                     action="store_true", default=False,
                     help="Exclude all MKV files")
    group.add_option("-n", "--include-new", dest="new_series",
                     action="store_true", default=False,
                     help="Include New Series even if not subscribed")
    group.add_option("-s", "--new-series-only", dest="new_series_only",
                     action="store_true", default=False,
                     help="Only include new series (Season 1, Episode 1) in the list")
    parser.add_option_group(group)

    group = OptionGroup(parser, "DVD Options")
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
    parser.add_option_group(group)

    group = OptionGroup(parser, "Output Controls")
    group.add_option("-l", "--log", dest="log",
                     action="store_true", default=False,
                     help="Create Log of shows")
    group.add_option("--print-log", dest="print_log",
                     action="store_true", default=False,
                     help="Print the created log")
    parser.add_option_group(group)


    group = OptionGroup(parser, "Logging Levels")
    group.add_option("-e", "--errors", dest="error",
                     action="store_true", default=False,
                     help="omit all but error logging")
    group.add_option("-q", "--quiet", dest="quiet",
                     action="store_true", default=False,
                     help="omit informational logging")
    group.add_option("-v", "--verbose", dest="verbose",
                     action="store_true", default=False,
                     help="increase informational logging")
    group.add_option("--debug", dest="debug",
                     action="store_true", default=False,
                     help="increase informational logging to include debug")
    parser.add_option_group(group)

    options, args = parser.parse_args()
    logger.debug("Parsed command line options: %r" % options)
    logger.debug("Parsed arguments: %r" % args)

    opt_sel = 0
    if options.debug:
        logger.setLevel(logging.DEBUG)
        ml.setLevel(logging.DEBUG)
        ch.setLevel(logging.DEBUG)
        opt_sel =+ 1
    if options.error:
        logger.setLevel(logging.ERROR)
        ml.setLevel(logging.ERROR)
        ch.setLevel(logging.ERROR)
        opt_sel =+ 1
    if options.quiet:
        logger.setLevel(logging.WARNING)
        ml.setLevel(logging.WARNING)
        ch.setLevel(logging.WARNING)
        opt_sel =+ 1
    if options.verbose:
        logger.setLevel(logging.DEBUG)
        ml.setLevel(logging.DEBUG)
        ch.setLevel(logging.DEBUG)
        opt_sel =+ 1

    user_opts = 0
    if options.aly:
        user_opts += 1
        options.dir_input = ALY_DIR
        options.area = 'Aly'
    if options.kim:
        user_opts += 1
        options.dir_input = KIM_DIR
        options.area = 'Kim'
    if options.michelle:
        user_opts += 1
        options.dir_input = MICHELLE_DIR
        options.area = 'Michelle'
    if options.ben:
        user_opts += 1
        options.dir_input = BEN_DIR
        options.area = 'Ben'

    if user_opts == 0:
        options.area = 'Series'

    if opt_sel > 1:
        msg = "Mutually Exclusive options selected, Reconsider Parameters"
        logger.error(msg)
        parser.error(msg)
        sys.exit(1)

    if options.print_log:
        options.log = True

    shows = NewShows()
    shows.BuildList(options)
    shows.Print()
    if options.build:
        shows.BuildDVD()
