#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Purpose:
     purpose

'''
from library import Library
from common import logger
from common.exceptions import UnexpectedErrorOccured
from datetime import date
import logging
import os
import pickle
import zlib
import re
import sys
import fnmatch


__pgmname__ = 'rmtfunctions'
__version__ = '@version: $Rev$'

__author__ = "@author: AJ Reynolds"
__copyright__ = "@copyright: Copyright 2011, AJ Reynolds"
__license__ = "@license: GPL"

__maintainer__ = "@organization: AJ Reynolds"
__status__ = "@status: Development"
__credits__ = []

log = logging.getLogger(__pgmname__)
library = Library()

regex_collection = re.compile('^.*Collection:.*$', re.IGNORECASE)

def listItems(host, content_type, compress=False):
    '''
    return a dict of Items {Title | [current_status, date, pathname]}
    '''
    log.trace('listItems: HOST: %s  TYPE: %s' % (host, content_type))

    Return_List = []
    if content_type.lower() == 'series':
        content_dir = library.settings.SeriesDir
        subscription_dir = os.path.join(library.settings.SubscriptionDir, host, 'Series')
        incremental_dir = os.path.join(library.settings.SubscriptionDir, host, library.settings.IncrementalsDir)
    elif content_type.lower() == 'movies':
        content_dir = library.settings.MoviesDir
        subscription_dir = os.path.join(library.settings.SubscriptionDir, host, 'Movies')
        incremental_dir = False
    else:
        raise UnexpectedErrorOccured('Invalid Content Type Requested: %s' % (content_type))

    for directory in os.listdir(os.path.abspath(content_dir)):
        if ignored(directory) or os.path.isfile(os.path.join(content_dir, directory)):
            log.trace("Skipping: %s" % directory)
            continue
        if regex_collection.search(directory):
            _prefix = directory.split(':', 1)[1].lstrip()
            for collection_directory in os.listdir(os.path.abspath(os.path.join(content_dir, directory))):
                if ignored(collection_directory):
                    log.trace("Skipping: %s" % collection_directory)
                    continue
                #  No Prefix for Collection on Movies Title
                _add_entry(Return_List, os.path.join(content_dir, directory), subscription_dir, incremental_dir, collection_directory)
                #  Use Prefix for Collection on Movies Title
#                _add_entry(Return_List, os.path.join(content_dir, directory), subscription_dir, incremental_dir, collection_directory, prefix='{}: '.format(_prefix))
        else:
            _add_entry(Return_List, content_dir, subscription_dir, incremental_dir, directory)

    log.trace('Return: %s' % (Return_List))

    if compress:
        _pickled_list = pickle.dumps(Return_List)
        Return_List = zlib.compress(_pickled_list, 9)

    return Return_List

def _add_entry(Return_List, content_dir, subscription_dir, incremental_dir, directory, prefix=''):
    if incremental_dir and os.path.exists(os.path.join(incremental_dir, directory)):
        current_status = library.settings.IncrementalsDir
    elif os.path.exists(os.path.join(subscription_dir, directory)):
        current_status = 'Subscribed'
    else:
        current_status = ''
    title = directory.split(None, 1)
    if title[0] in library.settings.Predicates:
        title = '{}{}, {}'.format(prefix, title[1], title[0])
    else:
        title = '{}{}'.format(prefix, directory)
    statinfo = os.stat(os.path.join(content_dir, directory))
    mod_date = statinfo.st_mtime
    _entry = {'Title':title, 'Status':current_status, 'Date':mod_date, 'Path':os.path.join(content_dir, directory)}
    Return_List.append(_entry)

def updateLinks(host, request):
    log.trace('updateLinks: USER: %s  REQUST: %s' % (host, request))

    rc = 0

    for _entry in request:

        symlink = os.path.join(library.settings.SubscriptionDir, host, _entry['Type'], _entry['Title'])

        if _entry['Action'] == 'Add':
            try:
                if os.path.lexists(symlink):
                    os.remove(symlink)
                os.symlink(_entry['Path'], symlink)
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

    logger.initialize()

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

    list_returned = listItems('goofy', 'Series', True)
    list_returned = listItems('goofy', 'Series', False)
    print list_returned
    list_returned = listItems('goofy', 'Series')
    print list_returned

#    req_add = [{'Action': 'Add', 'Path': '/mnt/DadVision/Movies/Collection: Disney/101 Dalmatians (1961)', 'Type': 'Movies', 'Title': '101 Dalmatians (1961)'}]
#    updateLinks('kim', req_add)
