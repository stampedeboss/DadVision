#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''

Purpose:
    Scan Video Libraries/Directories and remove any entries that have been removed from the library.

'''
from __future__ import division
from daddyvision.common import logger
from daddyvision.common.exceptions import UnexpectedErrorOccured
from daddyvision.common.options import OptionParser, CoreOptionParser
from daddyvision.common.settings import Settings
from daddyvision.series.fileparser import FileParser
import logging
import os
import sqlite3
import sys
import tempfile
import time

__pgmname__ = 'dbclean'
__version__ = '$Rev$'

__author__ = "AJ Reynolds"
__copyright__ = "Copyright 2011, AJ Reynolds"
__credits__ = []
__license__ = "GPL"

__maintainer__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"
__status__ = "Development"

TRACE = 5
VERBOSE = 15

log = logging.getLogger(__pgmname__)

logger.initialize()

TRACE = 5
VERBOSE = 15

config = Settings()
fileparser = FileParser()

db = sqlite3.connect(config.DBFile)
cursor = db.cursor()

class CleanDatabase(object):
    def __init__(self):
        pass

    def ScanDeadEntries(self):
        log.trace('ScanSeriesLibrary: Start')

        cursor.execute('SELECT COUNT(*)e FROM Files')
        Result = cursor.fetchall()
        File_Count = Result[0][0]

        Files_Processed = 0
        Files_Deleted = 0

        log.info('Number of File to be Checked: %s' % File_Count)

        cursor.execute('SELECT f.FileName FROM Files f')

        for row in cursor:
            Files_Processed += 1
            if os.path.exists(row[0]):
                pass
            else:
                log.info('Entry Removed: {}'.format(row[0]))
                try:
                    cursor.execute('DELETE FROM Files WHERE FileName="{}"'.format(row[0]))
                    Files_Deleted += 1
                except sqlite3.Error, e:
                    raise UnexpectedErrorOccured("File Information Insert: {} {}".format(e, row[0]))

                quotient, remainder = divmod(Files_Processed, 250)
                if remainder == 0:
                    db.commit()
                    log.info('Files Checked: %2.2f%% - %5s of %5s   Number Deleted: %s' % (Files_Processed/ File_Count,
                                                                                             Files_Processed,
                                                                                             File_Count,
                                                                                             Files_Deleted
                                                                                             )
                         )
        db.commit()
        log.info('Complete: Files Checked: %5s   Number Deleted: %s' % (Files_Processed,
                                                                          Files_Deleted
                                                                          ))


if __name__ == '__main__':

    parser = CoreOptionParser()
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

    library = CleanDatabase()
    library.ScanDeadEntries()

