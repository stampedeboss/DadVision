#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Purpose:
     Load current file information into Download Table for all users

'''
from __future__ import division
from daddyvision.common import logger
from daddyvision.common.exceptions import UnexpectedErrorOccured, DuplicateRecord, InvalidFilename
from daddyvision.common.options import OptionParser, CoreOptionParser
from daddyvision.common.settings import Settings
from daddyvision.common.countfiles import countFiles
from daddyvision.series.fileparser import FileParser
import logging
import os
import sqlite3
import sqlite3 as MySQLdb
import sys
import tempfile
import time
import datetime

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

config = Settings()
fileparser = FileParser()

db = sqlite3.connect(config.DBFile)
cursor = db.cursor()

def load_entry(user, file_name):

    t = os.path.getmtime(file_name)
    timestamp = datetime.datetime.fromtimestamp(t)

    try:
        file_details = fileparser.getFileDetails(file_name)
        # SQL #
        cursor.execute('INSERT INTO Downloads(Name, SeriesName, Filename, DownloadTimeStamp) VALUES ("{}", "{}", "{}", "{}")'.format(user,
                                                                                                                                     file_details['SeriesName'],
                                                                                                                                     file_name,
                                                                                                                                     timestamp))
    except  sqlite3.IntegrityError, e:
        raise DuplicateRecord
    except sqlite3.Error, e:
        raise UnexpectedErrorOccured("File Information Insert: {} {}".format(e, file_name))
    except InvalidFilename:
        pass

class DownloadDatabase(object):
    def __init__(self):
        pass

    def ScanSeriesLibrary(self, type_scan):
        log.trace('ScanSeriesLibrary: Start')

        user_profiles = config.GetSubscribers()
        for user in config.Users:
            user_profile = user_profiles[user]

            Files_Loaded = 0
            Files_Processed = 0

            source_directory = os.path.join(config.SubscriptionDir, user, type_scan)

            File_Count = countFiles(source_directory, exclude_list=config.ExcludeList)
            log.info('{:5s} - Number of File to be Checked: {}'.format(user, File_Count))

            for _symlink_dir in os.listdir(source_directory):
                target_dir = os.path.join(config.SeriesDir, _symlink_dir)

                if not os.path.isdir(target_dir):
                    raise UnexpectedErrorOccured('Series Library referenced in setting NOT FOUND: {}'.format(target_dir))
                    sys.exit(1)

                for _root, _dirs, _files in os.walk(target_dir):
                    if _dirs != None:
                        _dirs.sort()
                        for _exclude_dir in config.ExcludeList:
                            try:
                                _index = _dirs.index(_exclude_dir)
                                _dirs.pop(_index)
                                logger.TRACE('Removing Dir: %s' % _exclude_dir)
                            except:
                                continue

                    for _file_name in _files:

                        Files_Processed += 1
                        _fq_name = os.path.join(_root, _file_name)
                        log.trace('Processing File: %s' % _fq_name)

                        try:
                            _file_ext = os.path.splitext(_fq_name)[1][1:].lower()
                            if _file_ext in config.MediaExt:
                                load_entry(user, _fq_name)
                                Files_Loaded += 1
                            else:
                                continue
                                log.info('Skipping Non-VIdeo File: {}'.format(_fq_name))
                        except DuplicateRecord:
                            Files_Loaded += 1

                        quotient, remainder = divmod(Files_Processed, 250)
                        if remainder == 0:
                            db.commit()
                            log.info('%-5s - Files Checked: %2.2f%%   %5s of %5s   Number of Errors: %s' % (user,
                                                                                                           Files_Processed/ File_Count,
                                                                                                           Files_Processed,
                                                                                                           File_Count,
                                                                                                           Files_Processed - Files_Loaded
                                                                                                           )
                                 )
            db.commit()
            log.info('{:5s} - Complete: Files Checked: {:5n}   Number of Errors: {}'.format(user,
                                                                                        Files_Processed,
                                                                                        Files_Processed - Files_Loaded
                                                                                        )
                )


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

    library = DownloadDatabase()
    if len(args) > 0:
        if args[0].lower()[0:4] == 'incr':
            library.ScanSeriesLibrary('Incrementals')
    else:
        library.ScanSeriesLibrary('Series')


