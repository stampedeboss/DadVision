#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Purpose:
     Solict input for the user to add a user to the DaddyVision Environment

'''
from daddyvision.common import logger
from daddyvision.common.exceptions import SQLError, UserAbort
from daddyvision.common.options import OptionParser, CoreOptionParser
from daddyvision.common.settings import Settings
import logging
import os
import sqlite3
import sys

__pgmname__ = 'addusers'
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
config = Settings()

db = sqlite3.connect(config.DBFile)
cursor = db.cursor()

TRACE = 5
VERBOSE = 15

def get_value(message, defaults):
    while True:
        if defaults == None or message not in defaults:
            _response = raw_input("Enter %s (%s): " % (message, None)).rstrip()
        else:
            _response = raw_input("Enter %s (%s): " % (message, defaults[message])).rstrip()
        if len(_response) < 1:
            if defaults == None:
                _action = raw_input("Nothing Entered, R for Retry or Any Key to End\n")
                if len(_action) < 1 or _action[0].lower() != 'r':
                    raise UserAbort
                else:
                    continue
            else:
                return defaults[message]
        else:
            return _response


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


    while True:
        try:
            _user_dict = {}
            old_profile = {}

            _user_dict['Name'] = get_value('Name', None)
            name = _user_dict['Name']
            log.trace('***REQUESTING SUBSCRIBER LIST***')
            req_profile = config.GetSubscribers([name])
            log.trace('Subscriber Profile: {}'.format(req_profile))
            if name in req_profile:
                old_profile = req_profile[name]
            _user_dict['HostName'] = get_value('HostName', old_profile)
            _user_dict['UserId'] = get_value('UserId', old_profile)
            _user_dict['SeriesDir'] = get_value('SeriesDir', old_profile)
            _user_dict['MovieDir'] = get_value('MovieDir', old_profile)
            _user_dict['Identifier'] = get_value('Identifier', old_profile)
            _new_dict = config.AddSubscriber(_user_dict)
            try:
                cursor.execute('INSERT INTO Subscribers(Name, Identifier, UserId, HostName, SeriesDir, MovieDir) \
                         VALUES ("{}", "{}", "{}", "{}", "{}", "{}")'.format(name,
                                                                             _user_dict['Identifier'],
                                                                             _user_dict['UserId'],
                                                                             _user_dict['HostName'],
                                                                             _user_dict['SeriesDir'],
                                                                             _user_dict['MovieDir']
                                                             )
                               )
                if cursor.rowcount == 1:
                    db.commit()
            except  sqlite3.IntegrityError, e:
                try:
                    cursor.execute('UPDATE Subscribers SET Identifier="{}", UserId="{}", HostName="{}", SeriesDir="{}", MovieDir="{}" \
                                         WHERE Name="{}" '.format(_user_dict['Identifier'],
                                                                _user_dict['UserId'],
                                                                _user_dict['HostName'],
                                                                _user_dict['SeriesDir'],
                                                                _user_dict['MovieDir'],
                                                                _user_dict['Name']))
                    db.commit()
                except sqlite3.Error, e:
                    raise SQLError("File Information Insert: {} {}".format(e, _user_dict))
            except sqlite3.Error, e:
                raise SQLError("File Information Insert: {} {}".format(e, _user_dict))



        except UserAbort:
            sys.exit(0)
