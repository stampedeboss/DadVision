#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Purpose:
     Remove entries from database where file no longer exists

'''
from __future__ import division

import logging
import os
import re
import sqlite3
import sys
import unicodedata

from common.exceptions import UnexpectedErrorOccured

import logger
from dadvision.library import Library

__pgmname__ = 'library.dbclean_dnld'

__author__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"

__maintainer__ = __author__

__copyright__ = "Copyright 2011, AJ Reynolds"
__license__ = "GPL"

log = logging.getLogger(__pgmname__)

class CleanDatabase(Library):
    def __init__(self):

        super(CleanDatabase, self).__init__()
        self.db = sqlite3.connect(self.settings.DBFile)

        group = self.options.parser.add_argument_group("Media Type", description=None)
        group.add_argument("-i", "--incremental", dest="scan_type", default='Series',
            action="store_const", const="Incrementals",
            help="Process Incrementals instead of Series")

    def cleanDatabase(self):
        log.trace('ScanSeriesLibrary: Start')

        for user in self.settings.Hostnames:
            _table_entries = []
            try:
                cursor = self.db.cursor()
                cursor.execute('SELECT FileName FROM Downloads WHERE Name = "{}"'.format(user))
                for row in cursor:
                    _table_entries.append(unicodedata.normalize('NFKD', row[0]).encode('ascii', 'ignore'))
            except:
                self.db.close()
                log.error("Processing Stopped: SQLITE3 Error")
                return []

            cursor = self.db.cursor()
            for _file_name in _table_entries:
                _target = os.path.join('/mnt/Links', user, self.settings.IncrementalsDir, re.split(self.settings.SeriesDir, _file_name)[1].lstrip(os.sep))

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


if __name__ == '__main__':

    logger.initialize()
    library = CleanDatabase()

    args = library.options.parser.parse_args(sys.argv[1:])
    log.debug("Parsed command line: {!s}".format(args))

    log_level = logging.getLevelName(args.loglevel.upper())

    if args.logfile == 'daddyvision.log':
        log_file = '{}.log'.format(__pgmname__)
    else:
        log_file = os.path.expanduser(args.logfile)

    # If an absolute path is not specified, use the default directory.
    if not os.path.isabs(log_file):
        log_file = os.path.join(logger.LogDir, log_file)

    logger.start(log_file, log_level, timed=True)

    if len(args.library) < 1:
        log.warn('No pathname supplied for rename: Using default: {}'.format(library.settings.NewMoviesDir))
        args.library = library.settings.NewMoviesDir

    library.cleanDatabase()
