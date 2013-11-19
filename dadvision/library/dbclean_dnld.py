#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Purpose:
     Load current file information into Download Table for all users

'''
from __future__ import division
from daddyvision.common import logger
from daddyvision.common.exceptions import UnexpectedErrorOccured, DuplicateRecord, InvalidFilename
from daddyvision.common.options import OptionParser, OptionGroup
from daddyvision.common.settings import Settings
from daddyvision.common.countfiles import countFiles
from daddyvision.series.fileparser import FileParser
import logging
import os
import re
import sqlite3
import sys
import tempfile
import time
import datetime
import unicodedata

__pgmname__ = 'dbload_download'
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

class Library(object):
    def __init__(self):
        self.config = Settings()
        self.db = sqlite3.connect(self.config.DBFile)

    def CleanDatabase(self, user_list):
        log.trace('ScanSeriesLibrary: Start')

        for user in self.config.Users:
            if user_list and user not in user_list:
                continue
            
            _table_entries = []
            
            try:
                cursor = self.db.cursor()
                cursor.execute('SELECT FileName FROM Downloads WHERE Name = "{}"'.format(user))
                for row in cursor:
                    _table_entries.append(unicodedata.normalize('NFKD', row[0]).encode('ascii','ignore'))
            except:
                self.db.close()
                log.error("Processing Stopped: SQLITE3 Error")
                return []
    
            cursor = self.db.cursor()
            for _file_name in _table_entries:
                _target = os.path.join('/mnt/Links', user, self.config.IncrementalsDir, re.split(self.config.SeriesDir, _file_name)[1].lstrip(os.sep))
                
                if os.path.lexists(_target):
                    continue
                else:
                    try:
                        # SQL #
                        cursor.execute('DELETE FROM Downloads WHERE Name = "{}" AND Filename = "{}"'.format(user, _file_name))
                    except sqlite3.Error, e:
                        raise UnexpectedErrorOccured("File Information Deletion: {} {}".format(e, _file_name))

            self.db.commit()
        self.db.close()
           

class localOptions(OptionParser):

    def __init__(self, unit_test=False, **kwargs):
        OptionParser.__init__(self, **kwargs)

        group = OptionGroup(self, "Users")
        group.add_option("-a", "--aly", dest="users",
            action="append_const", const="aly",
            help="Sync Tigger for Aly")
        group.add_option("-k", "--kim", dest="users",
            action="append_const", const="kim",
            help="Sync Goofy for Kim")
        group.add_option("-p", "--peterson", dest="users",
            action="append_const", const="ben",
            help="Sync Tigger for Ben and Mac")
        self.add_option_group(group)

        group = OptionGroup(self, "Media Type")
        group.add_option("-i", "--incremental", dest="scan_type", default='Series',
            action="store_const", const="Incrementals",
            help="Process Incrementals instead of Series")
        self.add_option_group(group)


if __name__ == '__main__':
    parser = localOptions()
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

    library = Library()
    library.CleanDatabase(options.users)