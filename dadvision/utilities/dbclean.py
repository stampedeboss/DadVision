#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''

Purpose:
	Scan Video Libraries/Directories and remove any entries that have been removed from the library.

'''
from __future__ import division

import logging
import os
import re
import sqlite3
import sys

from common.exceptions import UnexpectedErrorOccured
from library import Library

import logger
from series import FileParser

__pgmname__ = 'dbclean'

__author__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"

__maintainer__ = __author__

__copyright__ = "Copyright 2011, AJ Reynolds"
__license__ = "GPL"

TRACE = 5
VERBOSE = 15

log = logging.getLogger(__pgmname__)

TRACE = 5
VERBOSE = 15

configdir = os.path.join(os.sep, "usr", "local", "etc", "daddyvision")
ConfigDir = configdir
ConfigFile = os.path.join(ConfigDir, '{}.cfg'.format(__pgmname__))

class CleanDatabase(Library):
	def __init__(self):
		log.trace('__init__ method: Started')

		super(CleanDatabase, self).__init__()

		self.db = sqlite3.connect(self.settings.DBFile)
		self.cursor = self.db.cursor()

		self.directory_old = '/mnt/DadVision/Series'
		self.re_dir_old = re.compile('^{}.*$'.format(self.directory_old), re.IGNORECASE)
		self.re_dir_current = re.compile('^{}.*$'.format(self.settings.SeriesDir), re.IGNORECASE)

		self.fileparser = FileParser()


	def ScanFileEntries(self):
		log.trace('ScanSeriesLibrary: Start')

		self.cursor.execute('SELECT COUNT(*)e FROM Files')
		Result = self.cursor.fetchall()
		File_Count = Result[0][0]

		Files_Processed = 0
		Files_Deleted = 0
		Files_Updated = 0

		log.info('Number of File to be Checked: %s' % File_Count)

		self.cursor.execute('SELECT f.FileName FROM Files f')
		Result = self.cursor.fetchall()
		for row in Result:
			Files_Processed += 1
			if os.path.exists(row[0]):
				pass
			else:
				_target = re.split(self.directory_old, row[0])
				if len(_target) > 1:
					try:
						Files_Updated += 1
						episode = os.path.join(self.settings.SeriesDir, _target[1].lstrip(os.sep))
						self.cursor.execute('UPDATE Files SET FileName="{}" WHERE FileName="{}"'.format(episode.encode('ascii', 'ignore'), row[0].encode('ascii', 'ignore')))
					except  sqlite3.Error, e:
						if e.message == 'column FileName is not unique':
							self.cursor.execute('DELETE FROM Files WHERE FileName="{}"'.format(row[0]))
							Files_Deleted += 1
						else:
							sys.exc_clear()
#							print 'ERROR: {}'.format(e.message.encode('ascii', 'ignore'))
				else:
					log.info('Entry Removed: {}'.format(row[0].encode('ascii', 'ignore')))
					try:
						self.cursor.execute('DELETE FROM Files WHERE FileName="{}"'.format(row[0].encode('ascii', 'ignore')))
						Files_Deleted += 1
					except sqlite3.Error, e:
						raise UnexpectedErrorOccured("File Information Insert: {} {}".format(e.message, row[0].encode('ascii', 'ignore')))

			quotient, remainder = divmod(Files_Processed, 250)
			if remainder == 0:
				self.db.commit()
				log.info('Files Checked: %2.2f%% - %5s of %5s   Number Deleted: %s   Number Updated: %s' % (Files_Processed/ File_Count,
																											Files_Processed,
																											File_Count,
																											Files_Deleted,
																											Files_Updated
																						 )
						 )
		self.db.commit()
		log.info('Complete: Files Checked: %5s   Number Deleted: %s' % (Files_Processed,
																		  Files_Deleted
																		  ))

	def ScanDownloadEntries(self):
		log.trace('ScanSeriesLibrary: Start')

		self.cursor.execute('SELECT COUNT(*)e FROM Downloads')
		Result = self.cursor.fetchall()
		File_Count = Result[0][0]

		Files_Processed = 0
		Files_Deleted = 0
		Files_Updated = 0

		log.info('Number of File Entries to be Checked: %s' % File_Count)

		self.cursor.execute('SELECT d.Name, d.FileName FROM Downloads d')
		Result = self.cursor.fetchall()
		for row in Result:
			Files_Processed += 1
			if os.path.exists(row[1]):
				pass
			else:
				_target = re.split(self.directory_old, row[1])
				if len(_target) > 1:
					try:
						Files_Updated += 1
						episode = os.path.join(self.settings.SeriesDir, _target[1].lstrip(os.sep))
						self.cursor.execute('UPDATE Downloads SET FileName="{}" WHERE Name="{}" and FileName="{}"'.format(episode, row[0], row[1]))
					except sqlite3.Error, e:
						if e.message == 'columns Name, FileName are not unique':
							self.cursor.execute('DELETE FROM Downloads WHERE Name="{}" and FileName="{}"'.format(row[0], row[1]))
							Files_Deleted += 1
						else:
							print 'ERROR: {}'.format(e)
				else:
					log.info('Entry Removed: {}  {}'.format(row[0], row[1]))
					try:
						self.cursor.execute('DELETE FROM Downloads WHERE Name="{}" and FileName="{}"'.format(row[0], row[1]))
						Files_Deleted += 1
					except sqlite3.Error, e:
						raise UnexpectedErrorOccured("File Information Insert: {} {}".format(e, row[0]))

			quotient, remainder = divmod(Files_Processed, 250)
			if remainder == 0:
				self.db.commit()
				log.info('Files Checked: %2.2f%% - %5s of %5s   Number Deleted: %s   Number Updated: %s' % (Files_Processed/ File_Count,
																											Files_Processed,
																											File_Count,
																											Files_Deleted,
																											Files_Updated
																						 )
						 )
		self.db.commit()
		log.info('Complete: Files Checked: %5s   Number Deleted: %s' % (Files_Processed,
																		  Files_Deleted
																		  ))

if __name__ == '__main__':

	logger.initialize()
	log.trace("MAIN: -------------------------------------------------")

	library = CleanDatabase()

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

	library.ScanFileEntries()
	library.ScanDownloadEntries()
