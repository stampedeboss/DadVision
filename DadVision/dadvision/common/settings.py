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

from configobj import ConfigObj
from common import logger
from common.exceptions import ConfigValueError, ConfigNotFound, InvalidArgumentValue, InvalidArgumentType
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

configdir = os.path.join(os.sep, "usr", "local", "etc", "daddyvision")
ConfigDir = configdir
ConfigFile = os.path.join(ConfigDir, '{}.cfg'.format(__pgmname__))
host = socket.gethostname()

log = logging.getLogger(__pgmname__)

class Settings(object):
	"""
	Returns new Settings object with Library, Common, and Subscriber data.

	settings: List of runtime information being requested. Valid options:
				 Common: Settings common to many routines (DEFAULT)
				RoutineName: Name of the special settings
	"""

	def __init__(self):

		if not os.path.exists(ConfigFile):
			raise ConfigNotFound("Config File Not Found: %s" % ConfigFile)

		self.config = ConfigObj(ConfigFile, unrepr=True, interpolation=False)

		HostName = self.config[host]
		self.UserID = HostName['UserId']
		self.SeriesDir = HostName['SeriesDir']
		self.MoviesDir = HostName['MovieDir']
		self.DownloadDir = HostName['DownloadDir']
		self.UnpackDir = HostName['UnpackDir']
		self.DownloadMovies = HostName['DownloadMovies']
		self.TraktUserID = HostName['TraktUserID']
		self.TraktPassWord = HostName['TraktPassWord']
		self.TraktHashPswd = hashlib.sha1(HostName['TraktPassWord']).hexdigest()
		self.TraktAPIKey = HostName['TraktAPIKey']
		self.TraktBase64Key = base64.encodestring(HostName['TraktUserID']+':'+HostName['TraktUserID'])

		Library = self.config['Library']
		_NewDir = Library['NewDir']
		self.NewMoviesDir = os.path.join(self.MoviesDir, _NewDir)
		self.NewSeriesDir = os.path.join(self.SeriesDir, _NewDir)

		Common = self.config['Common']
		self.MediaExt = Common['MediaExt']
		self.MovieGlob = Common['MovieGlob']
		self.MovieGlob2 = Common['MovieGlob2']
		self.IgnoreGlob = Common['IgnoreGlob']
		self.Predicates = Common['Predicates']

		self.ConversionsPatterns = self.config['Conversions']
		self.TvdbIdFile = os.path.join(ConfigDir, Common['TvdbIdFile'])

		self.SeriesAliasList = {}
		self.SeriesAliasFile = os.path.join(ConfigDir, Common['SeriesAliasFile'])


		self.ExcludeList = []
		self.exclude_file = os.path.join(ConfigDir, Common['ExcludeFile'])

		self.ExcludeScanList = []
		self.exclude_scan_file = os.path.join(ConfigDir, Common['ExcludeScanFile'])

		self.SpecialHandlingList = []
		self.spl_hand_file = os.path.join(ConfigDir, Common['SplHandFile'])

		self.EpisodeAdjList = []
		self.episode_adj_file = os.path.join(ConfigDir, Common['EpisodeAdjFile'])

		self.ReloadFromFiles()

		dbfile = self.config['DBFile']
		self.DBFile = dbfile['DBFile']

		hostnames = self.config['Hostnames']
		self.Hostnames = hostnames['Hostnames']

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

		HostName = self.config[hostname]
		self.UserID = HostName['UserId']
		self.SeriesDir = HostName['SeriesDir']
		self.MoviesDir = HostName['MovieDir']
		self.DownloadDir = HostName['DownloadDir']
		self.UnpackDir = HostName['UnpackDir']
		self.DownloadMovies = HostName['DownloadMovies']
		self.TraktUserID = HostName['TraktUserID']
		self.TraktPassWord = HostName['TraktPassWord']
		self.TraktHashPswd = hashlib.sha1(HostName['TraktPassWord']).hexdigest()
		self.TraktAPIKey = HostName['TraktAPIKey']
		self.TraktBase64Key = base64.encodestring('{}:{}'.format(HostName['TraktUserID'].rstrip(), HostName['TraktUserID'].rstrip()))

		Library = self.config['Library']
		_NewDir = Library['NewDir']
		self.NewMoviesDir = os.path.join(self.MoviesDir, _NewDir)
		self.NewSeriesDir = os.path.join(self.SeriesDir, _NewDir)

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
						  'Identifier': _HOSTNAME['Identifier'],
						  'TraktUserID': _HOSTNAME['TraktUserID'],
						  'TraktPassWord': _HOSTNAME['TraktPassWord'],
						  'TraktHashPswd': hashlib.sha1(_HOSTNAME['TraktPassWord']).hexdigest(),
						  'TraktAPIKey': _HOSTNAME['TraktAPIKey'],
						  'TraktBase64Key': base64.encodestring(_HOSTNAME['TraktUserID']+':'+_HOSTNAME['TraktUserID'])}

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
	log.info('TraktUserID: {}'.format(config.TraktUserID))
	log.info('TraktPassWord: {}'.format(config.TraktPassWord))
	log.info('TraktAPIKey: {}'.format(config.TraktAPIKey))
	log.info('Base64Key: {}'.format(config.TraktBase64Key))

	log.info(config.GetHostConfig(['tigger']))
	log.info(config.GetHostConfig(['all']))
	config.ReloadFromFiles()
	config.ReloadHostConfig('tigger')
	log.info('TraktUserID: {}'.format(config.TraktUserID))

	try:
		log.info(config.GetHostConfig(['mickey']))
	except InvalidArgumentValue, msg:
		log.error('GetHostConfig Failed: {}'.format(msg))
		try:
			config.ReloadHostConfig('mickey')
		except InvalidArgumentValue, msg:
			log.error('ReloadHostConfig Failed: {}'.format(msg))
	sys.exit(0)