#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Purpose:
     purpose

'''
from daddyvision.common import logger
from daddyvision.common.options import OptionParser, CoreOptionParser
from daddyvision.common.settings import Settings
from daddyvision.common.exceptions import UnexpectedErrorOccured
from datetime import date
import logging
import os
import re
import sys
import fnmatch


__pgmname__ = 'rmtfunctions'
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

TRACE = 5
VERBOSE = 15

regex_collection = re.compile('^.*Collection:.*$', re.IGNORECASE)

def listItems(user, content_type):
    '''
    return a Dict of Items {Title | [current_status, date, pathname]}
    '''

    log.trace('listItems: USER: %s  TYPE: %s' % (user, content_type))

    Return_List = []

    if content_type.lower() == 'series':
        content_dir = os.path.join(config.SeriesDir)
        subscription_dir = os.path.join(config.SubscriptionDir, user, 'Series')
        incremental_dir = os.path.join(config.SubscriptionDir, user, config.IncrementalsDir)
    elif content_type.lower() == 'movies':
        content_dir = os.path.join(config.MoviesDir)
        subscription_dir = os.path.join(config.SubscriptionDir, user, 'Movies')
        incremental_dir = False
    else:
        raise UnexpectedErrorOccured('Invalid Content Type Requested: %s' % (content_type))

    for directory in os.listdir(os.path.abspath(content_dir)):
        if ignored(directory):
            log.trace("Skipping: %s" % directory)
            continue
        if regex_collection.search(directory):
            for collection_directory in os.listdir(os.path.abspath(os.path.join(content_dir, directory))):
                if ignored(collection_directory):
                    log.trace("Skipping: %s" % collection_directory)
                    continue
                _add_entry(Return_List, os.path.join(content_dir, directory), os.path.join(subscription_dir, directory), incremental_dir, collection_directory)
        else:
            _add_entry(Return_List, content_dir, subscription_dir, incremental_dir, directory)

    log.trace('Return: %s' % (Return_List))

    return Return_List

def _add_entry(Return_List, content_dir, subscription_dir, incremental_dir, directory):
    if incremental_dir and os.path.exists(os.path.join(incremental_dir, directory)):
        current_status = config.IncrementalsDir
    elif os.path.exists(os.path.join(subscription_dir, directory)):
        current_status = 'Subscribed'
    else:
        current_status = ''
    title = directory.split(None, 1)
    if title[0] in config.Predicates:
        title = '%s, %s' % (title[1], title[0])
    else:
        title = directory
    statinfo = os.stat(os.path.join(content_dir, directory))
    mod_date = statinfo.st_mtime
    _entry = {'Title':title, 'Status':current_status, 'Date':mod_date, 'Path':os.path.join(content_dir, directory)}
    Return_List.append(_entry)

def updateLinks(user, request):
    log.trace('updateLinks: USER: %s  REQUST: %s' % (user, request))

    rc = 0

    for _entry in request:

        if regex_collection.search(_entry['Path']):
            _directories = _entry['Path'].split(os.sep)
            symlink = os.path.join(config.SubscriptionDir, user, _entry['Type'], _directories[-2], _entry['Title'])
        else:
            symlink = os.path.join(config.SubscriptionDir, user, _entry['Type'], _entry['Title'])

        if _entry['Action'] == 'Add':
            if not os.path.exists(symlink):
                try:
                    os.symlink(_entry['Path'], symlink)
                    os.lchown(symlink, 1000, 100)
                    log.info('symlink for %s to: %s' % (symlink, _entry['Path']))
                except OSError, message:
                    log.error('Unable to created symlink for %s to: %s - %s' % (symlink, _entry['Path'], message))
                    rc = 1
        elif _entry['Action'] == 'Delete':
            if os.path.exists(symlink):
                try:
                    os.remove(symlink)
                    log.info('Removed Symlink: %s' % symlink)
                except OSError, message:
                    log.error('Unable to remove symlink for %s - %s' % (symlink, message))
                    rc = 1
    return rc

def ignored(name):
    """ Check for ignored pathnames.
    """
    ExcludeList = ["lost+found", ".Trash-1000", "New", "Extra*"]
    return any(fnmatch.fnmatch(name.lower(), pattern) for pattern in ExcludeList)


if __name__ == '__main__':
    parser = OptionParser()
    options, args = parser.parse_args()

    log_level = logging.getLevelName(options.loglevel.upper())

    if options.logfile == 'daddyvision.log':
        log_file = '%s.log' % (__pgmname__)
    else:
        log_file = os.path.expanduser(options.logfile)

    # If an absolute path is not specified, use the default directory.
    if not os.path.isabs(log_file):
        log_file = os.path.join(logger.LogDir, log_file)

    logger.start(log_file, log_level, timed=True)

    log.debug("Parsed command line options: %s" % (options))
    log.debug("Parsed arguments: %r" % args)

    list_returned = listItems('aly', 'Movies')
    print list_returned