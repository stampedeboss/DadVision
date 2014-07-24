#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Purpose:
  Configuration and Run-time settings for the XBMC Support Programs

  Created by AJ Reynolds on %s.
  Copyright 2013 AJ Reynolds. All rights reserved.

  Licensed under the GPL License

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.
"""

from configobj import ConfigObj
from common import logger
from common.exceptions import (ConfigValueError, ConfigNotFound, UserAbort,
    UnexpectedErrorOccured, InvalidArgumentType)
import logging
import os
import sys
import time
import socket
import base64
import hashlib

__pgmname__ = 'settings'
__version__ = '$Rev$'

__author__ = "@author: AJ Reynolds"
__copyright__ = "@copyright: 2013, AJ Reynolds"
__license__ = "@license: GPL"
__credits__ = []

__maintainer__ = "AJ Reynolds"
__email__ = "@contact: stampedeboss@gmail.com"
__status__ = "Development"

myplatform = sys.platform

configdir = os.path.join(os.sep, "usr", "local", "etc", "daddyvision")
if myplatform != 'linux2':
    ConfigDir = '{}{}'.format("c:\Users\car16284\Documents\DadVision", configdir)
else:
    ConfigDir = configdir

ConfigFile = os.path.join(ConfigDir, '{}.cfg'.format(__pgmname__))

log = logging.getLogger(__pgmname__)
host = socket.gethostname()


class Settings(object):
    """
    Returns new Settings object with Library, Common, and Subscriber data.

    settings: List of runtime information being requested. Valid options:
                 Common: Settings common to many routines (DEFAULT)
                RoutineName: Name of the special settings

    update_existing: Indicator to request updating an existing config.
    """

    def __init__(self, subject=['common'], update=False):

        if not os.path.exists(ConfigFile):
            raise ConfigNotFound("Config File Not Found: %s" % ConfigFile)

        self.config = ConfigObj(ConfigFile, unrepr=True, interpolation=False)

        HostName = self.config[host]
        self.SeriesDir = HostName['SeriesDir']
        self.MoviesDir = HostName['MovieDir']
        self.DownloadDir = HostName['DownloadDir']
        self.NonVideoDir = HostName['NonVideoDir']
        self.TraktUserID = HostName['TraktUserID']
        self.TraktPassWord = HostName['TraktPassWord']
        self.TraktHashPswd = hashlib.sha1(HostName['TraktPassWord']).hexdigest()
        self.TraktAPIKey = HostName['TraktAPIKey']
        self.TraktBase64Key = base64.encodestring(HostName['TraktUserID']+':'+HostName['TraktUserID'])

        Library = self.config['Library']
        self.NewDir = Library['NewDir']
        self.IncrementalsDir = Library['IncrementalsDir']
        self.SubscriptionDir = os.path.join(ConfigDir , Library['SubscriptionDir'])
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
        else:
            touch(self.SeriesAliasFile)


        self.ExcludeList = []
        _exclude_file = os.path.join(ConfigDir, Common['ExcludeFile'])
        if os.path.exists(_exclude_file):
            with open(_exclude_file, "r") as _exclude_file_obj:
                for line in _exclude_file_obj.readlines():
                    self.ExcludeList.append(line.rstrip("\n"))
        else:
            touch(_exclude_file)

        self.ExcludeScanList = []
        _exclude_scan_file = os.path.join(ConfigDir, Common['ExcludeScanFile'])
        if os.path.exists(_exclude_scan_file):
            with open(_exclude_scan_file, "r") as _exclude_file_obj:
                for line in _exclude_file_obj.readlines():
                    self.ExcludeScanList.append(line.rstrip("\n"))
        else:
            touch(_exclude_scan_file)

        self.SpecialHandlingList = []
        _spl_hand_file = os.path.join(ConfigDir, Common['SplHandFile'])
        if os.path.exists(_spl_hand_file):
            with open(_spl_hand_file, "r") as _splhand_file_obj:
                for show_name in _splhand_file_obj.readlines():
                    self.SpecialHandlingList.append(show_name.rstrip("\n"))
        else:
            touch(_spl_hand_file)

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
        else:
            touch(_episode_adj_file)
#                log.debug('Episode Adjustment: LOADED')

        self.ConversionsPatterns = self.config['Conversions']

        dbfile = self.config['DBFile']
        self.DBFile = dbfile['DBFile']

        hostnames = self.config['Hostnames']
        self.Hostnames = hostnames['Hostnames']

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
            touch(self.TvdbIdFile)
            log.warn("TVDB Series IDs File Missing, New One Created: %s" % self.TvdbIdFile)
        return 0

    def GetSubscribers(self, req_profile=None):
        log.trace("Retrieving Host Information: {}".format(req_profile))

        _user_profiles = {}

        if req_profile is not None:
            if type(req_profile) != list:
                if req_profile.lower() != 'all':
                    raise InvalidArgumentType('Invalid Request Must be LIST with list of hostnames names to be returned')

        if req_profile == 'all' or req_profile is None:
            req_profile = self.Users

        for _entry in req_profile:

            try:
                _user_profile = self.config[_entry]
            except KeyError:
                continue

            if _user_profile:
                _user_dict = {'Name': _entry, 'HostName': _user_profile['HostName'],
                              'UserId': _user_profile['UserId'],
                              'MovieDir': _user_profile['MovieDir'],
                              'SeriesDir': _user_profile['SeriesDir'],
                              'DownloadDir': _user_profile['DownloadDir'],
                              'NonVideoDir': _user_profile['NonVideoDir'],
                              'Identifier': _user_profile['Identifier']
                             }

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
    log.info('HostNames: {}'.format(config.Hostnames))

    log.info('TraktUserID: {}'.format(config.TraktUserID))
    log.info('TraktPassWord: {}'.format(config.TraktPassWord))
    log.info('TraktAPIKey: {}'.format(config.TraktAPIKey))
    log.info('Base64Key: {}'.format(config.TraktBase64Key))
