#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Author: AJ Reynolds
Date: 07-19-2014
Purpose:
  Configuration and Run-time settings for the XBMC Support Programs

  Created by AJ Reynolds on %s.
  Copyright 2013 AJ Reynolds. All rights reserved.

  Licensed under the GPL License

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.
"""

import logging
import os
import sys
import time
import socket
import base64
import hashlib

from configobj import ConfigObj

from common import logger
from common.exceptions import ConfigValueError, ConfigNotFound, InvalidArgumentValue, InvalidArgumentType


__pgmname__ = 'settings'
__version__ = '$Rev$'

__author__ = "@author: AJ Reynolds"
__copyright__ = "@copyright: 2013-2014, AJ Reynolds"
__credits__ = []
__license__ = "@license: GPL"

__maintainer__ = "AJ Reynolds"
__email__ = "@contact: stampedeboss@gmail.com"
__status__ = "Development"

__date__ = '2013-06-25'
__updated__ = '2014-07-27'

program_version_message = '%%(prog)s %s (%s)' % (__version__, __updated__)
program_license = '''
Created by AJ Reynolds on %s.
Copyright 2014 AJ Reynolds. All rights reserved.

Licensed under the GPL License

Distributed on an "AS IS" basis without warranties
or conditions of any kind, either express or implied.

USAGE:
''' % (str(__date__))

configdir = os.path.join(os.sep, "usr", "local", "etc", "dadvision")
ConfigDir = configdir
ConfigFile = os.path.join(ConfigDir, '{}.cfg'.format(__pgmname__))
host = socket.gethostname()

log = logging.getLogger(__pgmname__)

class Settings(object):
    """
    Returns new Settings object with Library, Media, and Subscriber data.

    settings: List of runtime information being requested. Valid options:
                 Media: Settings common to many routines (DEFAULT)
                RoutineName: Name of the special settings
    """

    def __init__(self):

        if not os.path.exists(ConfigFile):
            raise ConfigNotFound("Config File Not Found: %s" % ConfigFile)

        self.config = ConfigObj(ConfigFile, unrepr=True, interpolation=False)

        Media = self.config['Media']
        self.MediaExt = Media['MediaExt']
        self.MovieGlob = Media['MovieGlob']
        self.MovieGlob2 = Media['MovieGlob2']
        self.IgnoreGlob = Media['IgnoreGlob']
        self.Predicates = Media['Predicates']
        self.CountryCodes = Media['CountryCodes']

        self.ConversionsPatterns = self.config['Conversions']

        self.SeriesAliasList = {}
        self.SeriesAliasFile = os.path.join(ConfigDir, Media['SeriesAliasFile'])


        self.ExcludeList = []
        self.exclude_file = os.path.join(ConfigDir, Media['ExcludeFile'])

        self.ExcludeScanList = []
        self.exclude_scan_file = os.path.join(ConfigDir, Media['ExcludeScanFile'])

        self.SpecialHandlingList = []
        self.spl_hand_file = os.path.join(ConfigDir, Media['SplHandFile'])

        self.EpisodeAdjList = []
        self.episode_adj_file = os.path.join(ConfigDir, Media['EpisodeAdjFile'])

        hostnames = self.config['Hostnames']
        self.Hostnames = hostnames['Hostnames']

        hostConfig = self.config[host]
        self.UserID = hostConfig['UserId']
        self.SeriesDir = hostConfig['SeriesDir']
        self.MoviesDir = hostConfig['MovieDir']
        self.DownloadDir = hostConfig['DownloadDir']
        self.UnpackDir = hostConfig['UnpackDir']
        self.DownloadMovies = hostConfig['DownloadMovies']
        self.DownloadSeries = hostConfig['DownloadSeries']
        self.TraktUserID = hostConfig['TraktUserID']
        self.TraktAuthorization = hostConfig['TraktToken']['token_type'] + ' ' + hostConfig['TraktToken']['access_token']

        Program = self.config['Program']
        self.DBFile = Program['DBFile']
        self.TraktAPIKey = Program['TraktClientID']
        self.TraktClientID = Program['TraktClientID']
        self.TraktClientSecret = Program['TraktClientSecret']

        self.NewMoviesDir = os.path.join(self.MoviesDir, Program['NewDir'])
        self.NewSeriesDir = os.path.join(self.SeriesDir, Program['NewDir'])

        self.ReloadFromFiles()

        return

    def ReloadFromFiles(self):

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

        if os.path.exists(self.exclude_file):
            with open(self.exclude_file, "r") as _exclude_file_obj:
                for line in _exclude_file_obj.readlines():
                    self.ExcludeList.append(line.rstrip("\n"))
        else:
            touch(self.exclude_file)

        if os.path.exists(self.exclude_scan_file):
            with open(self.exclude_scan_file, "r") as _exclude_file_obj:
                for line in _exclude_file_obj.readlines():
                    self.ExcludeScanList.append(line.rstrip("\n"))
        else:
            touch(self.exclude_scan_file)

        if os.path.exists(self.spl_hand_file):
            with open(self.spl_hand_file, "r") as _splhand_file_obj:
                for show_name in _splhand_file_obj.readlines():
                    self.SpecialHandlingList.append(show_name.rstrip("\n"))
        else:
            touch(self.spl_hand_file)

        if os.path.exists(self.episode_adj_file):
            with open(self.episode_adj_file, "r") as _episode_adj_file_obj:
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
            touch(self.episode_adj_file)

        return

    def ReloadHostConfig(self, hostname):
        log.verbose('Reloading Settings on request for hostname: {}'.format(hostname))
        if hostname not in self.Hostnames:
            raise InvalidArgumentValue('Requested Hostname not found: {}'.format(hostname))

        hostConfig = self.config[hostname]
        self.UserID = hostConfig['UserId']
        self.SeriesDir = hostConfig['SeriesDir']
        self.MoviesDir = hostConfig['MovieDir']
        self.DownloadDir = hostConfig['DownloadDir']
        self.UnpackDir = hostConfig['UnpackDir']
        self.DownloadMovies = hostConfig['DownloadMovies']
        self.TraktUserID = hostConfig['TraktUserID']
        self.TraktAuthorization = hostConfig['TraktToken']['token_type'] + ' ' + hostConfig['TraktToken']['access_token']

        Program = self.config['Program']
        self.NewMoviesDir = os.path.join(self.MoviesDir, Program['NewDir'])
        self.NewSeriesDir = os.path.join(self.SeriesDir, Program['NewDir'])

        return

    def GetHostConfig(self, requested_host=['all']):
        log.trace("Retrieving Host Information: {}".format(requested_host))

        if type(requested_host) != list:
            raise InvalidArgumentType('Invalid Request Must be LIST of hostnames to be returned')
        if tuple(set(requested_host) - set(self.Hostnames + ['all'])):
            raise InvalidArgumentValue('Requested Hostname not found: {}'.format(requested_host))
        if requested_host == ['all']:
            requested_host = self.Hostnames

        _host_profiles = {}

        for _entry in requested_host:
            try:
                _HOSTNAME = self.config[_entry]
            except KeyError:
                raise ConfigValueError("The requested hostname's configuration missing")

            _host_config = {'UserId': _HOSTNAME['UserId'],
                          'MovieDir': _HOSTNAME['MovieDir'],
                          'SeriesDir': _HOSTNAME['SeriesDir'],
                          'DownloadDir': _HOSTNAME['DownloadDir'],
                          'UnpackDir': _HOSTNAME['UnpackDir'],
                          'DownloadMovies': _HOSTNAME['DownloadMovies'],
                          'TraktUserID': _HOSTNAME['TraktUserID']}
            if 'TraktToken' in _HOSTNAME:
                _token = _HOSTNAME['TraktToken']
                if 'token_type' in _token and 'access_token' in _token:
                    _host_config['TraktAuthorization'] = '{} {}'.format(_token['token_type'], _token['access_token'])
                else:
                    _host_config['TraktAuthorization'] = ''

            _host_profiles[_entry] = _host_config

        return _host_profiles


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
    config = Settings()

    log.info('HostNames: {}'.format(config.Hostnames))
    log.info('SeriesDir: {}'.format(config.SeriesDir))
    log.info('MoviesDir: {}'.format(config.MoviesDir))
    log.info('NewSeriesDir: {}'.format(config.NewSeriesDir))
    log.info('NewMoviesDir: {}'.format(config.NewMoviesDir))
    log.info('UnpackDir: {}'.format(config.UnpackDir))
    log.info('DownloadMovies: {}'.format(config.DownloadMovies))
    log.info('EpisodeAdjList: {}'.format(config.EpisodeAdjList))
    log.info('MediaExt: {}'.format(config.MediaExt))
    log.info('MovieGlob: {}'.format(config.MovieGlob))
    log.info('IgnoreGlob: {}'.format(config.IgnoreGlob))
    log.info('Predicates: {}'.format(config.Predicates))
    log.info('DBFile: {}'.format(config.DBFile))
    log.info('SeriesAliasList: {}'.format(config.SeriesAliasList))
    log.info('ExcludeList: {}'.format(config.ExcludeList))
    log.info('ExcludeScanList: {}'.format(config.ExcludeScanList))
    log.info('SpecialHandlingList: {}'.format(config.SpecialHandlingList))
    log.info('EpisodeAdjList: {}'.format(config.EpisodeAdjList))
    log.info('TraktAPIKey: {}'.format(config.TraktAPIKey))
    log.info('TraktUserID: {}'.format(config.TraktUserID))
    log.info('TraktPassWord: {}'.format(config.TraktPassWord))
    log.info('TraktAuthorization: {}'.format(config.TraktAuthorization))

    config.ReloadFromFiles()

    config.ReloadHostConfig('tigger')
    log.info('TraktUserID: {}'.format(config.TraktUserID))
    log.info('TraktPassWord: {}'.format(config.TraktPassWord))
    log.info('TraktAuthorization: {}'.format(config.TraktAuthorization))

    log.info(config.GetHostConfig(['tigger']))
    log.info(config.GetHostConfig(['all']))

    try:
        log.info(config.GetHostConfig(['mickey']))
    except InvalidArgumentValue, msg:
        log.error('GetHostConfig Failed: {}'.format(msg))
        try:
            config.ReloadHostConfig('mickey')
        except InvalidArgumentValue, msg:
            log.error('ReloadHostConfig Failed: {}'.format(msg))
    sys.exit(0)
