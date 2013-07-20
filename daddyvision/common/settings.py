#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Purpose:
        Configuration and Run-time settings for the XBMC Support Programs

"""

from configobj import ConfigObj
from daddyvision.common import logger
from daddyvision.common.exceptions import (ConfigValueError, UserAbort,
    UnexpectedErrorOccured, InvalidArgumentType)
import logging
import os
import re
import sys
import time

__pgmname__ = 'settings'
__version__ = '$Rev$'

__author__ = "AJ Reynolds"
__copyright__ = "Copyright 2011, AJ Reynolds"
__credits__ = []
__license__ = "GPL"

__maintainer__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"
__status__ = "Development"

ConfigDir   = os.path.join("/usr/local/etc", "daddyvision")
ConfigFile  = os.path.join(ConfigDir, '{}.cfg'.format(__pgmname__))

log = logging.getLogger('settings')

class Settings(object):
    '''
    Returns new Settings object with Library, Common, and Subscriber data.

    settings: List of runtime information being requested. Valid options:
                 Common: Settings common to many routines (DEFAULT)
                RoutineName: Name of the special settings

    update_existing: Indicator to request updating an existing config.
    '''

    def __init__(self, subject=['common'], update=False):

        if update or not os.path.exists(ConfigFile):
            self.BuildConfig(update)

        self.config = ConfigObj(ConfigFile, unrepr=True, interpolation=False)

        Library = self.config['Library']
        self.SeriesDir = Library['SeriesDir']
        self.MoviesDir = Library['MoviesDir']
        self.NewDir = Library['NewDir']
        self.DownloadDir = Library['DownloadDir']
        self.NonVideoDir = Library['NonVideoDir']
        self.IncrementalsDir = Library['IncrementalsDir']

        self.SubscriptionDir = os.path.join(ConfigDir ,Library['SubscriptionDir'])
        self.NewMoviesDir = os.path.join(self.MoviesDir, self.NewDir)
        self.NewSeriesDir = os.path.join(self.SeriesDir, self.NewDir)

        if not os.path.exists(self.SeriesDir):
            log.error("Path Not Found: %s" % self.SeriesDir)
            log.error("Invalid Config Entries, Ending")
            raise ConfigValueError("Path Not Found: %s" % self.SeriesDir)

        if not os.path.exists(self.MoviesDir):
            log.error("Path Not Found: %s" % self.MoviesDir)
            log.error("Invalid Config Entries, Ending")
            raise ConfigValueError("Path Not Found: %s" % self.MoviesDir)

        if not os.path.exists(self.NewSeriesDir):
            log.error("Path Not Found: %s" % self.NewSeriesDir)
            log.error("Invalid Config Entries, Ending")
            raise ConfigValueError("Path Not Found: %s" % self.NewSeriesDir)

        if not os.path.exists(self.NewMoviesDir):
            log.error("Path Not Found: %s" % self.NewMoviesDir)
            log.error("Invalid Config Entries, Ending")
            raise ConfigValueError("Path Not Found: %s" % self.NewMoviesDir)

        if not os.path.exists(self.NonVideoDir):
            log.error("Path Not Found: %s" % self.NonVideoDir)
            log.error("Invalid Config Entries, Ending")
            raise ConfigValueError("Path Not Found: %s" % self.NonVideoDir)

        Common = self.config['Common']
        self.MediaExt = Common['MediaExt']
        self.MovieGlob = Common['MovieGlob']
        self.MovieGlob2 = Common['MovieGlob2']
        self.IgnoreGlob = Common['IgnoreGlob']
        self.Predicates = Common['Predicates']

        self.TvdbIdList = {}
        self.TvdbIdFile = os.path.join(ConfigDir, Common['TvdbIdFile'])
        touch(os.path.join(os.path.join(ConfigDir), 'Series_Aliases'))
        self.ReloadTVDBList()

        self.SeriesAliasList = {}
        self.SeriesAliasFile = os.path.join(ConfigDir, Common['SeriesAliasFile'])
        if os.path.exists(self.SeriesAliasFile):
            with open(self.SeriesAliasFile, "r") as _alias_file_obj:
                for _line in _alias_file_obj.readlines():
                    _series_alias_entry = _line.rstrip("\n").split("\t")
                    if len(_series_alias_entry) == 2:
                        self.SeriesAliasList[_series_alias_entry[0]] = _series_alias_entry[1]
#                log.debug('Series Alias: LOADED')
            _alias_file_obj.close()

        self.ExcludeList = []
        exclude_file = os.path.join(ConfigDir, Common['ExcludeFile'])
        if os.path.exists(exclude_file):
            with open(exclude_file, "r") as exclude_file_obj:
                for line in exclude_file_obj.readlines():
                    self.ExcludeList.append(line.rstrip("\n"))

        self.ExcludeScanList = []
        ExcludeScanFile = os.path.join(ConfigDir, Common['ExcludeScanFile'])
        if os.path.exists(ExcludeScanFile):
            with open(ExcludeScanFile, "r") as exclude_file_obj:
                for line in exclude_file_obj.readlines():
                    self.ExcludeScanList.append(line.rstrip("\n"))

#        log.debug('Exclude List: LOADED')

        self.SpecialHandlingList = []
        spl_hand_file = os.path.join(ConfigDir, Common['SplHandFile'])
        if os.path.exists(spl_hand_file):
            with open(spl_hand_file, "r") as splhand_file_obj:
                for show_name in splhand_file_obj.readlines():
                    self.SpecialHandlingList.append(show_name.rstrip("\n"))
#                log.debug('Special Handling: LOADED')

        self.EpisodeAdjList = []
        _episode_adj_file = os.path.join(ConfigDir, Common['EpisodeAdjFile'])
        if os.path.exists(_episode_adj_file):
            with open(_episode_adj_file, "r") as _episode_adj_file_obj:
                for _line in _episode_adj_file_obj.readlines():
                    _adjustment = _line.rstrip("\n").split("\t")
                    if len(_adjustment) == 6 and _adjustment[:0] != '#':
                        _adjustment_entry = {'SeriesName' : _adjustment[0],
                                             'SeasonNum' : int(_adjustment[1]),
                                             'Begin' : int(_adjustment[2]),
                                             'End' : int(_adjustment[3]),
                                             'AdjSeason' : int(_adjustment[4]),
                                             'AdjEpisode' : int(_adjustment[5])}
                        self.EpisodeAdjList.append(_adjustment_entry)
#                log.debug('Episode Adjustment: LOADED')

        self.ConversionsPatterns = self.config['Conversions']

        dbfile = self.config['DBFile']
        self.DBFile = dbfile['DBFile']

        users = self.config['Users']
        self.Users = users['Users']

        return

    def ReloadTVDBList(self):
        if os.path.exists(self.TvdbIdFile):
            with open(self.TvdbIdFile, "r") as TvdbIdFile_obj:
                for _line in TvdbIdFile_obj.readlines():
                    _tvdb_id_details = _line.rstrip("\n").split("\t")
                    if len(_tvdb_id_details) == 2 and _tvdb_id_details[:0] != '#':
                        self.TvdbIdList[_tvdb_id_details[0]] = _tvdb_id_details[1]
            TvdbIdFile_obj.close()
#            log.debug('TVDB IDs: LOADED')
        else:
            log.warn("TVDB Series IDs File Missing: " % self.TvdbIdFile)
        return 0

    def GetSubscribers(self, req_profile=None):
        log.trace("Retrieving User Information: {}".format(req_profile))

        _user_profiles = {}

        if req_profile != None:
            if type(req_profile) != list:
                if req_profile.lower() != 'all':
                    raise InvalidArgumentType('Invalid Request Must be LIST with list of user names to be returned')

        if req_profile == 'all' or req_profile == None:
            req_profile = self.Users

        for _entry in req_profile:

            try:
                _user_profile = self.config[_entry]
            except KeyError:
                continue

            if _user_profile:
                _user_dict = {}
                _user_dict['Name'] = _entry
                _user_dict['HostName'] = _user_profile['HostName']
                _user_dict['UserId'] = _user_profile['UserId']
                _user_dict['MovieDir'] = _user_profile['MovieDir']
                _user_dict['SeriesDir'] = _user_profile['SeriesDir']
                _user_dict['Identifier'] = _user_profile['Identifier']

                _user_profiles[_entry] = _user_dict

#                _user_profiles.append(_user_dict)

        return _user_profiles

    def AddSubscriber(self, req_profile=None):
        log.trace("Adding/Updating User Information: {}".format(req_profile))

        if type(req_profile) != dict:
            raise InvalidArgumentType('Invalid Request Must be DICT with profile information to be added')

        self.config[req_profile['Name']] = {}
        self.config[req_profile['Name']]['HostName'] = req_profile['HostName']
        self.config[req_profile['Name']]['UserId'] = req_profile['UserId']
        self.config[req_profile['Name']]['MovieDir'] = req_profile['MovieDir']
        self.config[req_profile['Name']]['SeriesDir'] = req_profile['SeriesDir']
        self.config[req_profile['Name']]['Identifier'] = req_profile['Identifier']

        if req_profile['Name'] not in self.Users:
            self.Users.append(req_profile['Name'])
            users = self.config['Users']
            users['Users'] = self.Users

        with open(ConfigFile, "w") as _cf:
            self.config.write(_cf)

        self.config.reload()

        _user_dict = self.GetSubscribers([req_profile['Name']])
        if _user_dict[req_profile['Name']] != req_profile:
            raise UnexpectedErrorOccured("The profile does not match with what was just added, programming error")
#        _user_dict = {}
#        _user = self.config[req_profile['Name']]
#        _user_dict['Name'] = req_profile['Name']
#        _user_dict['HostName'] = _user['HostName']
#        _user_dict['UserId'] = _user['UserId']
#        _user_dict['MovieDir'] = _user['MovieDir']
#        _user_dict['SeriesDir'] = _user['SeriesDir']
#        _user_dict['Identifier'] = _user['Identifier']

        return _user_dict

    def BuildConfig(self, update=False):

        if not os.path.exists(ConfigDir):
            try:
                os.makedirs(ConfigDir)
            except:
                log.error("Cannot Create Config Directory: %s" % ConfigDir)
                raise ConfigValueError("Cannot Create Config Directory: %s" % ConfigDir)

        config = ConfigObj(unrepr = True, interpolation = False)
        config.filename = ConfigFile

        _base_dir = get_dir('/mnt', "Base Directory for Libraries")

        config['Library'] = {}
        config['Library']['SeriesDir'] = get_dir(os.path.join(_base_dir, "DadVision/Series"), "Series")
        config['Library']['MoviesDir'] = get_dir(os.path.join(_base_dir, "DadVision/Movies"), "Movies")
        config['Library']['DownloadDir'] = get_dir(os.path.join(_base_dir, "Downloads/Bittorrent"), "Downloads")
        config['Library']['NonVideoDir'] = get_dir(os.path.join(_base_dir, "Downloads/Unpacked"), "Unknown Unpack")
        config['Library']['NewDir'] = "New"
        config['Library']['SubscriptionDir'] = "Links"
        config['Library']['IncrementalsDir'] = "Incrementals"

        config['Common'] = {}
        config['Common']['MediaExt'] = ['avi', 'bup', 'core', 'divx', 'ifo', 'img', 'iso',
                                        'm2ts', "m4v",'mp4', 'mkv', 'mpeg', 'mpg', 'vob'
                                        ]

        config['Common']['MovieGlob'] = ["1080p", "720p", "bluray", "x264", "x264-refined", "h264",
                                         "ac3", "ac-3", "uncut", "director", "directors", "director's",
                                         "unrated", "extended", "retail", "repack", "proper", "480p",
                                         "dvdr", "dvdrip", "brrip", "bdrip", "hdtv", "ntsc", "pal", "r5",
                                         "br-screener", "screener", "tsxvid", "xvid", "divxnl", "divx",
                                         "scr", "hq", "pdvd-rip", "pdvd", "pdv", "Predvd", "pre-dvd", "dvd",
                                         "ppvrip", "pdtv", "cam", "telesync", "telecine", "WorkPrint", "vhs",
                                         "cvcd", "vcd", "webrip", "br-scr", "ts", "ws", "nl", "nlt", "cn ",
                                         "tc ", "extratorrent", "2lions", " vostfr", "fxm", "subs", "nl Subs",
                                         "french", "english", "spanish", "ita ", "italia", "hindi", "german",
                                         "eng","swesub", 'blu-ray', 'dvd-r', 'fulldvd', 'multi', 'dts',
                                          ]
        config['Common']['IgnoreGlob'] = ['*subs*', '*subpack*', '*sample*', '*.sfv', '*.srt',
                                                  '*.idx', '*.swp', '*.tmp', '*.bak', '*.nfo', '*.txt',
                                                  '*.doc', '*.docx', '*.jpg', '*.png', '*.com', '*.mds',
                                                  'thumbs.db', 'desktop.ini', 'ehthumbs_vista.db', '*.url',
                                                  '.*', '*~*'
                                                  ]
        config['Common']['Predicates'] = ['The', 'A', 'An']

        config['Common']['TvdbIdFile']      = 'Series_TvdbId'
        config['Common']['SeriesAliasFile'] = 'Series_Aliases'
        config['Common']['SplHandFile']     = 'Series_Special_Handling'
        config['Common']['ExcludeFile']     = 'Series_Excludes'
        config['Common']['ExcludeScanFile'] = 'Series_Excluded_From_Scans'
        config['Common']['EpisodeAdjFile']  = 'Series_Episode_Adjustments'

        config['Conversions'] = {}
        # Formats for renaming files
        config['Conversions']['std_fqn']  = '%(BaseDir)s/%(SeriesName)s/Season %(SeasonNum)s/%(EpisodeNumFmt)s %(EpisodeTitle)s.%(Ext)s'
        config['Conversions']['proper_fqn']  = '%(BaseDir)s/%(SeriesName)s/Season %(SeasonNum)s/%(EpisodeNumFmt)s %(EpisodeTitle)s (PROPER).%(Ext)s'
        config['Conversions']['fullname'] = '%(SeriesName)s/Season %(SeasonNum)/[%(SeriesName)s S0%(SeasonNum)%(EpisodeNumFmt)s] %(EpisodeTitle)s%(Ext)s'
        config['Conversions']['std_show'] = '%(SeriesName)s/Season %(SeasonNumber)s/%(EpisodeNumFmt)s %(EpisodeTitle)s.%(Ext)s'
        config['Conversions']['hdtv_fqn'] = '%(SeriesName)s/Season %(SeasonNum) hdtv/[%(EpisodeNumFmt)s] %(EpisodeTitle)s%(Ext)s'
        config['Conversions']['std_epname']= '%(EpisodeNumFmt)s %(EpisodeTitle)s.%(Ext)s'

        # Used to join multiple episode names together
        config['Conversions']['multiep_join_name_with'] = ', '

        # Format for numbers (python string format), %02d does 2-digit
        # padding, %d will cause no padding
        config['Conversions']['episode_single'] = 'E%02d'

        # String to join multiple number
        config['Conversions']['episode_separator'] = '-'

        config['Conversions']['rename_message'] = '%-15.15s Season %2.2s NEW NAME: %-40.40s CUR NAME: %s'

        file_name = raw_input("Enter File Name for DaddyVision Tracking Database (%s): " % 'daddyvision.db3').lstrip(os.sep)
        if not file_name:
            file_name = 'daddyvision.db3'
        config['DBFile'] = {}
        config['DBFile']['DBFile'] = os.path.join(ConfigDir, file_name)

        config['Users'] = {}
        config['Users']['Users'] = []

        config.write()
        log.info('New Config File Created: %s' % ConfigFile)
        return

def get_dir(dir_name_d, message):
    while True:
        log.debug("ROUTINE: get_dir %s %s" % (message, dir_name_d))
        dir_name = raw_input("Enter %s Directory (%s): " % (message, dir_name_d)).rstrip(os.sep)
        if not dir_name:
            dir_name = dir_name_d
        if os.path.exists(os.path.expanduser(dir_name)):
            return dir_name
        while not os.path.exists(os.path.expanduser(dir_name)):
            action = raw_input("%s Directory: %s - Not Found,  Ignore/Re-Enter/Create/Abort? (I/R/C/A): " % (message, dir_name)).lower()[0]
            log.debug("ROUTINE: get_dir loop %s %s %s" % (action, message, dir_name_d))
            if len(action) < 1:
                continue
            elif action[0].lower() == 'a':
                raise UserAbort
            elif action[0].lower() == 'i':
                return dir_name
            elif action[0].lower() == 'c':
                try:
                    os.makedirs(os.path.expanduser(dir_name))
                    return dir_name
                except OSError, exc:
                    log.error("Unable to Create Directory: %s, %s: " % (dir_name, exc))
                    continue
            elif action[0] == 'r':
                dir_name = get_dir(dir_name_d, message)
                return dir_name

def touch(path):
    now = time.time()
    try:
        # assume it's there
        os.utime(path, (now, now))
    except os.error:
        # if it isn't, try creating the directory,
        # a file with that name
        open(path, "w").close()
        os.utime(path, (now, now))

if __name__ == '__main__':

    logger.initialize()

    update_existing = False
    if len(sys.argv) > 1:
        if sys.argv[1] == 'update':
            update_existing = True

    config = Settings(update=update_existing)

    log.info('SeriesDir: {}'.format(config.SeriesDir))
    log.info('MoviesDir: {}'.format(config.MoviesDir))
    log.info('NewDir: {}'.format(config.NewDir))
    log.info('NewSeriesDir: {}'.format(config.NewSeriesDir))
    log.info('NewMoviesDir: {}'.format(config.NewMoviesDir))
    log.info('NonVideoDir: {}'.format(config.NonVideoDir))
    log.info('SubscriptionDir: {}'.format(config.SubscriptionDir))
    log.info('TvdbIdList: {}'.format(config.TvdbIdList))
    log.info('EpisodeAdjList: {}'.format(config.EpisodeAdjList))
    log.info('MediaExt: {}'.format(config.MediaExt))
    log.info('MovieGlob: {}'.format(config.MovieGlob))
    log.info('IgnoreGlob: {}'.format(config.IgnoreGlob))
    log.info('Predicates: {}'.format(config.Predicates))
    log.info('DBFile: {}'.format(config.DBFile))
    log.info('Users: {}'.format(config.Users))
