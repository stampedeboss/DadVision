#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''

Purpose:
    Scan Video Libraries/Directories and add file information to DownloadMonitor Database.

'''
from __future__ import division
from daddyvision.common import logger
from daddyvision.common.exceptions import UnexpectedErrorOccured, DuplicateRecord
from daddyvision.common.options import OptionParser
from daddyvision.common.settings import Settings
from daddyvision.series.fileparser import FileParser
import logging
import os
import sqlite3
import sys
import time
import datetime

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

config = Settings()
fileparser = FileParser()

db = sqlite3.connect(config.DBFile)
cursor = db.cursor()

def load_entry(file_details):

#    t = os.path.getmtime(file_details['FileName'])
#    timestamp = datetime.datetime.fromtimestamp(t)

    try:
        # SQL #
        cursor.execute('INSERT INTO Files(SeriesName, SeasonNum, EpisodeNum, Filename) \
                 VALUES ("{}", {}, {}, "{}")'.format(file_details['SeriesName'],
                                                     file_details['SeasonNum'],
                                                     file_details['EpisodeNums'][0],
                                                     file_details['FileName']
                                                     )
                       )
        file_id = int(cursor.lastrowid)
    except  sqlite3.IntegrityError, e:
        raise DuplicateRecord
    except sqlite3.Error, e:
        raise UnexpectedErrorOccured("File Information Insert: {} {}".format(e, file_details))

class DownloadDatabase(object):
    def __init__(self):
        pass

    def ScanSeriesLibrary(self):
        log.trace('ScanSeriesLibrary: Start')

        FilesToBeAdded = []

        Files_Loaded = 0
        Files_Processed = 0

        if not os.path.isdir(config.SeriesDir):
            raise UnexpectedErrorOccured('Series Library referenced in setting NOT FOUND: {}'.format(config.SeriesDir))
            sys.exit(1)

        File_Count = self._count_total_files(config.SeriesDir)
        log.info('Number of File to be Checked: %s' % File_Count)

        for _root, _dirs, _files in os.walk(config.SeriesDir):
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
                    _file_details = fileparser.getFileDetails(_fq_name)
                    if _file_details['Ext'] in config.MediaExt:
                        load_entry(_file_details)
                        Files_Loaded += 1
                    else:
                        log.info('Skipping Non-VIdeo File: {}'.format(_fq_name))
#                        Files_Processed += 1
                except DuplicateRecord:
                    Files_Loaded += 1

                quotient, remainder = divmod(Files_Processed, 250)
                if remainder == 0:
                    db.commit()
                    log.info('Files Checked: %2.2f%% - %5s of %5s   Number of Errors: %s' % (Files_Processed/ File_Count,
                                                                                             Files_Processed,
                                                                                             File_Count,
                                                                                             Files_Processed - Files_Loaded
                                                                                             )
                         )
        db.commit()
        log.info('Complete: Files Checked: %5s   Number of Errors: %s' % (Files_Processed,
                                                                          Files_Processed - Files_Loaded
                                                                          )
                             )



    def _count_total_files(self, valid_path):
        File_Count = 0
        for _root, _dirs, _files in os.walk(valid_path):
            _dirs.sort()
            for _exclude_dir in config.ExcludeList:
                try:
                    _index = _dirs.index(_exclude_dir)
                    _dirs.pop(_index)
                    logger.TRACE('Removing Dir From Count: %s' % _exclude_dir)
                except:
                    continue

            for _f in _files:
                File_Count += 1
        return File_Count

if __name__ == '__main__':

    parser = OptionParser()
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
    library.ScanSeriesLibrary()

'''
try:
    # SQL #
    cursor.execute('SELECT f.FileName, patient_id, p.patient_initials, p.patient_diagnosis, p.patient_allergies FROM patient p')
    if cursor.rowcount != 1:
        raise PatientNotFound ('Patient: %s Not Found' % patient_id)
    for row in cursor:
        self.patient_list.append(fetchoneDict(cursor))

    # SQL #
    cursor.execute('INSERT INTO patient(patient_initials, patient_diagnosis, patient_allergies) \
             VALUES (%s, %s, %s)' % (sym,sym,sym), (patient_initials, patient_diagnosis, patient_allergies))
    patient_id = int(cursor.lastrowid)
#    if cursor.warning_count() > 0:
#    raise PatientSaveError("Insert - %s %s" % (db.info(), cursor.messages))
    db.commit()

except  sqlite3.Error, e:
    log.error("METHOD: Patient - List")
    raise PatientListError (e)
return self.patient_list
'''


