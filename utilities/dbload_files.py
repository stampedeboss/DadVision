#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''

Purpose:
	Scan Video Libraries/Directories and add file information to DownloadMonitor Database.

'''
from __future__ import division
from library import Library
from common import logger
from common.exceptions import UnexpectedErrorOccured, DuplicateRecord, InvalidFilename
from common.countfiles import countFiles
from library.series.fileparser import FileParser
import logging
import os
import sqlite3
import sys
import time
import datetime
import fnmatch

__pgmname__ = 'dbload_files'
__version__ = '$Rev$'

__author__ = "AJ Reynolds"
__copyright__ = "Copyright 2011, AJ Reynolds"
__credits__ = []
__license__ = "GPL"

__maintainer__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"
__status__ = "Development"

log = logging.getLogger(__pgmname__)

logger.initialize()
TRACE = 5
VERBOSE = 15


def _ignored(name):
	""" Check for ignored pathnames.
	"""
	rc = []
	if name == 'New': rc.append(True)
	rc.append(any(fnmatch.fnmatch(name.lower(), pattern) for pattern in library.settings.ExcludeList))
	rc.append(any(fnmatch.fnmatch(name.lower(), pattern) for pattern in library.settings.IgnoreGlob))
	return any(rc)


class DownloadDatabase(Library):
	def __init__(self):
		log.trace('__init__ method: Started')

		super(DownloadDatabase, self).__init__()

		self.db = sqlite3.connect(self.settings.DBFile)
		self.cursor = self.db.cursor()
		self.fileparser = FileParser()


	def ScanSeriesLibrary(self):
		log.trace('ScanSeriesLibrary: Start')

		FilesToBeAdded = []

		Files_Loaded = 0
		Files_Processed = 0
		Files_Already_Processed = 0
		Files_Non_Video = 0
		Files_with_Errors = 0

		File_Count = countFiles(self.settings.SeriesDir, exclude_list=self.settings.ExcludeList)

		log.info('Number of File to be Checked: %s' % File_Count)

		for _root, _dirs, _files in os.walk(self.settings.SeriesDir):
			if _dirs is not None:
				_dirs.sort()
				for _dir in _dirs[:]:
					# Process Enbedded Directories
					if _ignored(_dir):
						_dirs.remove(_dir)

			for _file_name in _files:

				quotient, remainder = divmod(Files_Processed, 250)
				if remainder == 0:
					self.db.commit()
					log.info('Checked: %2.2f%% - %5s of %5s  Errors: %s  Present: %s  Non-Video:  %s ' \
					         % ((Files_Processed/ File_Count)*100,
								Files_Processed,
								File_Count,
								Files_with_Errors,
								Files_Already_Processed,
								Files_Non_Video
							 )
						 )

				Files_Processed += 1
				_fq_name = os.path.join(_root, _file_name)
				log.trace('Processing File: %s' % _fq_name)

				try:
					_ext = os.path.splitext(_file_name)[1][1:]
					if _ext not in self.settings.MediaExt:
						Files_Non_Video += 1
						continue
					_file_details = self.fileparser.getFileDetails(_fq_name)
					self.load_entry(_file_details)
					Files_Loaded += 1
				except InvalidFilename:
					log.info('Skipping Series Not Found: {}'.format(_fq_name))
					Files_with_Errors += 1
					continue
				except DuplicateRecord:
					Files_Already_Processed += 1
					continue

		self.db.commit()
		log.info('Complete: Files Checked: %5s   Number of Errors: %s' % (Files_Processed,
																		  Files_with_Errors
																		  )
							 )

	def load_entry(self, file_details):

	#    t = os.path.getmtime(file_details['FileName'])
	#    timestamp = datetime.datetime.fromtimestamp(t)

		try:
			# SQL #
			self.cursor.execute('INSERT INTO Files(SeriesName, SeasonNum, EpisodeNum, Filename) \
					 VALUES ("{}", {}, {}, "{}")'.format(file_details['SeriesName'],
														 file_details['SeasonNum'],
														 file_details['EpisodeNums'][0],
														 file_details['FileName']
														 )
						   )
			file_id = int(self.cursor.lastrowid)
		except  sqlite3.IntegrityError, e:
			raise DuplicateRecord
		except sqlite3.Error, e:
			raise UnexpectedErrorOccured("File Information Insert: {} {}".format(e, file_details))
		return file_id

if __name__ == '__main__':

	logger.initialize()
	log.trace("MAIN: -------------------------------------------------")

	library = DownloadDatabase()

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

	logger.start(log_file, log_level, timed=False)

	library.ScanSeriesLibrary()
