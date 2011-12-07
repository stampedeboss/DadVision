#!/usr/bin/env python
"""
Purpose:
		Configuration and Run-time settings for the XBMC Support Programs

"""

from configobj import ConfigObj
import os
import re
import sys
import time
import logging
from seriesExceptions import ConfigValueError

__author__ = "AJ Reynolds"
__copyright__ = "Copyright 2011, AJ Reynolds"
__credits__ = []
__license__ = "GPL"

__pgmname__ = 'settings'
__version__ = '$Rev$'

__maintainer__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"
__status__ = "Development"

PgmDir      = os.path.dirname(__file__)
HomeDir     = os.path.expanduser('~')
ConfigDirB  = os.path.join(HomeDir, '.config')
ConfigDir   = os.path.join(ConfigDirB, 'xbmcsupt')
RunDir      = sys.path[0]

# A level more detailed than DEBUG
TRACE = 5
# A level more detailed than INFO
VERBOSE = 15

logging.addLevelName(5, 'TRACE')
logging.addLevelName(15, 'VERBOSE')
log = logging.getLogger()
setattr(log, 'TRACE', lambda *args: log.log(5, *args))
setattr(log, 'VERBOSE', lambda *args: log.log(15, *args))

class Settings(object):
		"""Returns new Settings object with Library, RunTime, and Subscriber data.

		settings_requested: List of runtime information being requested. Valid options:
				Library: List of Directories of Video/Non-Video Libraries
				Common: Settings common to many routines
				RoutineName: Name of the special settings

		update_existing: Indicator to request updating an existing config.
		"""

		def __init__(self, settings=['directories'], update=False, pgmname='__pgmname__':

				self._config_file = os.path.expanduser(os.path.join(ConfigDir, '%s.cfg' % pgmname))

				if update or not os.path.exists(self._config_file):
						self.BuildConfig(update)

				self.config = ConfigObj(self.configfile, unrepr=True, interpolation=False)
				if "directories" in settings:
						Library = self.config['Library']
						SeriesDir = Library['SeriesDir']
						MoviesDir = Library['MoviesDir']
						NonVideoDir = Library['NonVideoDir']
						SubscriptionDir = Library['SubscriptionDir']
						NewDir = Library['NewDir']

						if not os.path.exists(self.SeriesDir):
								logger.error("Path Not Found: %s" % self.SeriesDir)
								logger.error("Invalid Config Entries, Ending")
								raise ConfigValueError("Path Not Found: %s" % self.SeriesDir)

						if not os.path.exists(self.MoviesDir):
								logger.error("Path Not Found: %s" % self.MoviesDir)
								logger.error("Invalid Config Entries, Ending")
								raise ConfigValueError("Path Not Found: %s" % self.MoviesDir)

						if not os.path.exists(self.NonVIdeoDir):
								logger.error("Path Not Found: %s" % self.NonVIdeoDir)
								logger.error("Invalid Config Entries, Ending")
								raise ConfigValueError("Path Not Found: %s" % self.NonVideoDir)

				if "common" in settings_requested:
						RunTime    = self.config['RunTime-Common']
						MediaExt = RunTime['MediaExt']
						MovieGlob = RunTime['MovieGlob']
						IgnoreGlob = RunTime['IgnoreGlob']
						Predicates = RunTime['Predicates']

						TvdbIdFile = os.path.expanduser(RunTime['TvdbIdFile'])
						ShowAliasFile = os.path.expanduser(RunTime['ShowAliasFile'])

						SpecialHandlingList = []
						spl_hand_file = os.path.expanduser(RunTime['SplHandFile'])
						if os.path.exists(spl_hand_file):
							with open(spl_hand_file, "r") as splhand_file_obj:
								for show_name in splhand_file_obj.readlines():
									SpecialHandlingList.append(show_name.rstrip("\n"))
						logger.debug('Special Handling for: %s' % self.special_handling)

						ExcludeList = []
						exclude_file = os.path.expanduser(RunTime['ExcludeFile'])
						if os.path.exists(exclude_file):
							with open(exclude_file, "r") as exclude_file_obj:
								for line in exclude_file_obj.readlines():
									ExcludeList.append(line.rstrip("\n"))

						exclude_extras = os.path.expanduser(RunTime['ExcludeExtrasFile'])
						if os.path.exists(exclude_extras):
							with open(exclude_extras, "r") as exclude_file_obj:
								for line in exclude_file_obj.readlines():
									ExcludeList.append(line.rstrip("\n"))

						logger.debug('Exclude List: %s' % self.ExcludeList)

						FileNamePatterns = config['FileNames']

				if "DownloadMonitor" in settings_requested:
						RunTime    = self.config['RunTime-DownloadMonitor']
						WatchDir = os.path.expanduser(RunTime['WatchDir'])

				if "UpdateMonitor" in settings_requested:
						RunTime    = self.config['RunTime-UpdateMonitor']

	def GetSubscribers(self, subscriber=[None]):
				SubscriptionDetails = {}
				if subscriber == 'all' or len(subscriber > 1):
					_subscriber_list = self.config['SubscriberList']
					Subscribers = _subscriber_list['All']
					for _entry in Subscribeers:
						_subscription_info = config[_entry]
						_host_name = _subscription_info['HostName']
						_user_id = _subscription_info['UserId']
						_movie_dir = _subscription_info['MovieDir']
						_series_dir = _subscription_info['SeriesDir']
						_links_dir = _subscription_info['LinksDir']
						SubscriptionDetails.append(_entry: {'HostName' : _host_name,
															'UserId' : _user_id,
															'MovieDir' : _movie_dir.
															'SeriesDir' : _series_dir,
															'LinksDir' : _links_dir
															})
				elif subscriber != None:
					_subscription_info = config[subscriber]
					_host_name = _subscription_info['HostName']
					_user_id = _subscription_info['UserId']
					_movie_dir = _subscription_info['MovieDir']
					_series_dir = _subscription_info['SeriesDir']
					_links_dir = _subscription_info['LinksDir']
					SubscriptionDetails.append(_entry: {'HostName' : _host_name,
														'UserId' : _user_id,
														'MovieDir' : _movie_dir.
														'SeriesDir' : _series_dir,
														'LinksDir' : _links_dir
														})
		return SubscriptionDetails

		def BuildConfig(self):
				if not os.path.exists(ConfigDir):
						try:
								os.makedirs(ConfigDir)
						except:
								logger.error("Cannot Create Config Directory: %s" % ConfigDir)
								raise ConfigValueError("Cannot Create Config Directory: %s" % ConfigDir)

				config = ConfigObj(unrepr = True, interpolation = False)
				config.filename = self._config_file
				config['Library'] = {}

				_base_dir = get_dir('/mnt', "Base Directory for Libraries")

				config['Library']['SeriesDir'] = get_dir(os.path.join(_base_dir, "Series"), "Series")
				config['Library']['MoviesDir'] = get_dir(os.path.join(_base_dir, "Movies"), "Movies")
				config['Library']['NonVideoDir'] = get_dir(os.path.join(_base_dir, "Non Video Files"), "Downloads")
				config['Library']['SubscriptionDir'] = get_dir(os.path.join(_base_dir, "Links"), "Subscription Files")
				config['Library']['NewDir'] = get_dir(os.path.join(_base_dir, "New"), "Subdirectory for New Files")

				config['RunTime-Common']['MediaExt'] = ['avi', 'mkv', 'mp4', 'mpeg']
				config['RunTime-Common']['MovieGlob'] = [ "720", "1080", "bluray", "bdrip", "brrip", "pal",
															"ntsc", "dvd-r", "fulldvd", "multi", "dts",
															"hdtv", "pdtv", "webrip", "dvdrip", "2lions"
														]
				config['RunTime-Common']['IgnoreGlob'] = ["*sample*", "samples", "sample.avi", "sample-*.avi",
															"*.sfv", ".srt", ".*", "*~", "*.swp", "*.tmp", "*.bak",
																													"*.nfo","*.txt", "thumbs.db", "desktop.ini",
				predicates = ['The', 'A', 'An']
																													"ehthumbs_vista.db", "*.url", "*.doc", "*.docx", "*.jpg",
																													"*.srt", "*.png",	"sample*", "*.com", "*.mds"
																													]

								show_file = raw_input("Enter File Name TVDB Show IDs (%s): " % 'series_tvdb_ids').lstrip(os.sep)
								if not show_file:
										show_file = 'series_tvdb_ids'
								config['RunTime-Common']['TvdbIdFile'] = '%s/%s' % (ConfigDir, show_file)
								touch(os.path.join(os.path.expanduser(ConfigDir), show_file))

								alias_file = raw_input("Enter File Name Show Aliases (%s): " % 'series_aliases').lstrip(os.sep)
								if not alias_file:
					alias_file = 'series_aliases'
								config['RunTime-Common']['ShowAliasFile'] = '%s/%s' % (ConfigDir, alias_file)
								touch(os.path.join(os.path.expanduser(ConfigDir), alias_file))

								config['RunTime-Common']['SplHandFile']   = '%s/special_handling' % ConfigDir
								config['RunTime-Common']['ExcludeExtras'] = '%s/exclude_extras' % ConfigDir
								config['RunTime-Common']['ExcludeFile']   = '%s/exclude_rename' % ConfigDir

								config['RunTime-DownloadMonitor']['WatchDir'] = get_dir(os.path.join('/mnt', 'Downloads/Bittorrent'), "DownloadMonitor Watch Folder")

								config['FileNames'] = {}
				# Formats for renaming files
				config['FileNames']['std_fqn']  = '%(base_dir)s/%(seriesname)s/Season %(seasonnumber)s/%(epno)s %(epname)s.%(ext)s'
				config['FileNames']['proper_fqn']  = '%(base_dir)s/%(seriesname)s/Season %(seasonnumber)s/%(epno)s %(epname)s (PROPER).%(ext)s'
				config['FileNames']['fullname'] = '%(seriesname)s/Season %(seasonnumber)/[%(seriesname)s S0%(seasonnumber)%(epno)s] %(episodename)s%(ext)s'
				config['FileNames']['std_show'] = '%(seriesname)s/Season %(seasonnumber)s/%(epno)s %(epname)s.%(ext)s'
				config['FileNames']['hdtv_fqn'] = '%(seriesname)s/Season %(seasonnumber) hdtv/[%(epno)s] %(episodename)s%(ext)s'
				config['FileNames']['std_epname']= '%(epno)s %(epname)s.%(ext)s'

				# Used to join multiple episode names together
				config['FileNames']['multiep_join_name_with'] = ', '

				# Format for numbers (python string format), %02d does 2-digit
				# padding, %d will cause no padding
				config['FileNames']['episode_single'] = 'E%02d'

				# String to join multiple number
				config['FileNames']['episode_separator'] = '-'

				config['FileNames']['rename_message'] = '%-15.15s Season %2.2s NEW NAME: %-40.40s CUR NAME: %s'

				'''
				Series.py uses the following:
				[RegEx]
				Std = ['\n\t(/.*/)?\n\t(?P<seriesname>.*)\n\t[/\\._ \\-]\n\t(s|season)[/\\._ \\-]?(?P<season>[0-9]+)\n\t[/\\._ \\-]\n\t[e](?P<episodenumberstart>[0-9]+)\n\t[\\-]\n\t[Ee]?(?P<episodenumberend>[0-9]+)\n\t[\\.\\- ]\n\t(?P<epname>.*)\n\t\\.\n\t(?P<ext>....?)\n\t$\n\t', '\n\t(/.*/)?\n\t(?P<seriesname>.*)\n\t[/\\._ \\-]\n\t(s|Season)[/\\._ \\-]?(?P<season>[0-9]+)\n\t[/\\._ \\-]?\n\t[e|E](?P<episodenumber>[0-9]+)\n\t[/\\._ \\-]?\n\t(?P<epname>.+)?\n\t\\.\n\t(?P<ext>....?)\n\t$\n\t', '\n\t(/.*/)?\n\t(?P<seriesname>.*)\n\t[/\\._ \\-]\n\t(s|Season)[/\\._ \\-]?(?P<season>[0-9]+)\n\t[/\\._ \\-]?\n\t(hdtv)?\n\t[/\\._ \\-]?\n\t[e|E](?P<episodenumber>[0-9]+)\n\t[/\\._ \\-]?\n\t(?P<epname>.+)?\n\t\\.\n\t(?P<ext>....?)\n\t$\n\t']
				[Check]
				age = '30'
				
				rename:
				rename_message = '%-15.15s Season %2.2s NEW NAME: %-40.40s CUR NAME: %s'

				'''
				

				config.write()
				logger.info('New Config File Created: %s' % self._config_file)
				return

def get_dir(self, dir_name_d, message):
	while True:
		logger.debug("ROUTINE: get_dir %s %s" % (message, dir_name_d))
		dir_name = raw_input("Enter %s Directory (%s): " % (message, dir_name_d)).rstrip(os.sep)
		if not dir_name:
			dir_name = dir_name_d
		if os.path.exists(os.path.expanduser(dir_name)):
			return dir_name
		while not os.path.exists(os.path.expanduser(dir_name)):
			action = raw_input("%s Directory: %s - Not Found,  Ignore/Re-Enter/Create/Abort? (I/R/C/A): " % (message, dir_name)).lower()[0]
			logger.debug("ROUTINE: get_dir loop %s %s %s" % (action, message, dir_name_d))
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
						logger.error("Unable to Create Directory: %s, %s: " % (dir_name, exc))
						continue
			elif action[0] == 'r':
				dir_name = self.get_dir(dir_name_d, message)
				return dir_name

def touch(self, path):
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

		update_existing = False
		if len(sys.argv) > 0:
				if sys.argv[1] == 'update':
						update_existing = True

		parms = GetConfig(update_existing, 'GetConfig')

		print parms.watch_dir
		print parms.series_dir
		print parms.series_new_dir
		print parms.movies_dir
		print parms.movies_new_dir
		print parms.other_dir
		print parms.media_ext
		print parms.movie_glob
		print parms.ignore_glob
		print parms.special_handling
		print parms.exclude_list
		print parms.show_file
		print parms.alias_file

		print parms.patterns
