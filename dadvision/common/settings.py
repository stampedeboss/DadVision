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

import logging
import os
import socket
import sys
import time

from configobj import ConfigObj

from common.exceptions import ConfigValueError, ConfigNotFound

__pgmname__ = 'settings'

__author__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"

__maintainer__ = __author__

__copyright__ = "Copyright 2016, AJ Reynolds"
__license__ = "GPL"

ConfigDir = os.path.join(os.sep, "usr", "local", "etc", "dadvision")
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
		self.AdditionalGlob = Media['AdditionalGlob']
		self.Predicates = Media['Predicates']
		self.CountryCodes = Media['CountryCodes']

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

		self.ConversionsPatterns = self.config['Conversions']

		self.Hostnames = self.config['Hostnames']['Hostnames']

		hostConfig = self.config[host]
		self.UserID = hostConfig['UserId']
		self.SeriesDir = hostConfig['SeriesDir']
		self.MoviesDir = hostConfig['MovieDir']
		self.DownloadDir = hostConfig['DownloadDir']
		self.UnpackDir = hostConfig['UnpackDir']
		self.DownloadMovies = hostConfig['DownloadMovies']
		self.DownloadSeries = hostConfig['DownloadSeries']
		self.TraktUserID = hostConfig['TraktUserID']
		self.TraktAuthorization = " ".join([hostConfig['TraktToken']['token_type'],
											hostConfig['TraktToken']['access_token']])

		Program = self.config['Program']
		self.DBFile = Program['DBFile']
		self.TraktAPIKey = Program['TraktClientID']
		self.TraktClientID = Program['TraktClientID']
		self.TraktClientSecret = Program['TraktClientSecret']
		self.TraktFollowed = Program['TraktFollowed']
		self.TraktFollowed720 = Program['TraktFollowed720']

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
			_alias_file_obj.close()
			log.debug('Series Alias: LOADED')
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
		log.debug('Reloading Settings on request for hostname: {}'.format(hostname))
		if hostname not in self.Hostnames:
			raise ConfigValueError('Requested Hostname not found: {}'.format(hostname))

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
		log.debug("Retrieving Host Information: {}".format(requested_host))

		if type(requested_host) != list:
			raise ConfigValueError('Invalid Request Must be LIST of hostnames to be returned')
		if tuple(set(requested_host) - set(self.Hostnames + ['all'])):
			raise ConfigValueError('Requested Hostname not found: {}'.format(requested_host))
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
					_host_config['TraktAuthorization'] = '{} {}'.format(_token['token_type'],
					                                                    _token['access_token'])
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

	from logging import INFO, DEBUG, ERROR; TRACE = 5; VERBOSE = 15
	from common import logger
	logger.initialize(level=DEBUG)

	settings = Settings()
	log.info('HostNames: {}'.format(settings.Hostnames))
	log.info('SeriesDir: {}'.format(settings.SeriesDir))
	log.info('MoviesDir: {}'.format(settings.MoviesDir))
	log.info('NewSeriesDir: {}'.format(settings.NewSeriesDir))
	log.info('NewMoviesDir: {}'.format(settings.NewMoviesDir))
	log.info('UnpackDir: {}'.format(settings.UnpackDir))
	log.info('DownloadMovies: {}'.format(settings.DownloadMovies))
	log.info('EpisodeAdjList: {}'.format(settings.EpisodeAdjList))
	log.info('MediaExt: {}'.format(settings.MediaExt))
	log.info('MovieGlob: {}'.format(settings.MovieGlob))
	log.info('IgnoreGlob: {}'.format(settings.IgnoreGlob))
	log.info('Predicates: {}'.format(settings.Predicates))
	log.info('DBFile: {}'.format(settings.DBFile))
	log.info('SeriesAliasList: {}'.format(settings.SeriesAliasList))
	log.info('ExcludeList: {}'.format(settings.ExcludeList))
	log.info('ExcludeScanList: {}'.format(settings.ExcludeScanList))
	log.info('SpecialHandlingList: {}'.format(settings.SpecialHandlingList))
	log.info('EpisodeAdjList: {}'.format(settings.EpisodeAdjList))
	log.info('TraktAPIKey: {}'.format(settings.TraktAPIKey))
	log.info('TraktUserID: {}'.format(settings.TraktUserID))
	log.info('TraktAuthorization: {}'.format(settings.TraktAuthorization))

	settings.ReloadFromFiles()

	settings.ReloadHostConfig('tigger')
	log.info('TraktUserID: {}'.format(settings.TraktUserID))
	log.info('TraktAuthorization: {}'.format(settings.TraktAuthorization))

	log.info(settings.GetHostConfig(['tigger']))
	log.info(settings.GetHostConfig(['all']))

	try:
		log.info(settings.GetHostConfig(['mickey']))
	except ConfigValueError, msg:
		log.error('GetHostConfig Failed: {}'.format(msg))
		try:
			settings.ReloadHostConfig('mickey')
		except ConfigValueError, msg:
			log.error('ReloadHostConfig Failed: {}'.format(msg))

	sys.exit(0)
