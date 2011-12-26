#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Purpose:
     purpose

'''
from daddyvision.common import logger
from daddyvision.common.options import OptionParser, CoreOptionParser
from daddyvision.common.settings import Settings
from datetime import date
import logging
import os
import sys
import fnmatch


__pgmname__ = 'daddyvision.library.testrmt'
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


def listItems(user, content_type):
#return a Dict of Items {Title | [current_status, date, pathname]}

    Return_List = []

    if content_type.lower() == 'series':
        target_level = 0
        content_dir = os.path.join(config.SeriesDir)
        subscription_dir = os.path.join(config.SubscriptionDir, user, 'Series')
        incremental_dir = os.path.join(config.SubscriptionDir, user, 'Incrementals')
    elif content_type.lower() == 'movies':
        target_level = 0
        content_dir = os.path.join(config.MoviesDir)
        subscription_dir = os.path.join(config.SubscriptionDir, user, 'Movies')
        incremental_dir = False

    log.debug('User: {} Content: {}'.format(user, content_type))

    startinglevel = content_dir.count(os.sep)
    for root, dirs, files in os.walk(os.path.abspath(content_dir), followlinks=False):
        log.info('ROOT: %s' % (root))

        dirs.sort()
        #return a Dict of Items {Title | [current_status, date, pathname]}
        for directory in dirs[:]:
            level = root.count(os.sep) - startinglevel
            if ignored(directory):
                log.debug("Skipping: %s" % directory)
                dirs.remove(directory)
                continue
            elif level == target_level:
                log.debug('Directory: %s Level: %s' % (directory, level))

                if incremental_dir and os.path.exists(os.path.join(incremental_dir, directory)):
                    current_status = 'Incremental'
                elif os.path.exists(os.path.join(subscription_dir, directory)):
                    current_status = 'Subscribed'
                else:
                    current_status = ''

                title = directory.split(None, 1)

                if title[0] in config.Predicates:
                    title = '%s, %s' % (title[1], title[0])
                else:
                    title = directory

                statinfo = os.stat(os.path.join(root, directory))
                mod_date = statinfo.st_mtime

                Return_List.append({'Title' : directory,
                                    'Status' : current_status,
                                    'Date' : mod_date,
                                    'Path' : os.path.join(root, directory)
                                    })

    return Return_List

def updateLinks(user, request):

#going to get a list of dict items [Title : Movie title or Series Name (dir name), Type : type, Action : action]  with action being Add, Delete, NewOnly

    for _entry in request:
        symlink = os.path.join(config.SubscriptionDir, user, _entry['Type'], _entry['Title'])
        if _entry['Action'] == 'Add':
            if _entry['Type'] in ['Series', 'Incremental']:
                pathname = os.path.join(config.SeriesDir, _entry['Title'])
            else:
                pathname = os.path.join(config.MoviesDir, _entry['Title'])
            if not os.path.exists(symlink):
                try:
                    os.symlink(pathname, symlink)
                    os.lchown(symlink, 1000, 100)
                    log.info('symlink for %s to: %s' % (symlink, pathname))
                except OSError, message:
                    log.error('Unable to created symlink for %s to: %s - %s' % (symlink, pathname, message))
        elif _entry['Action'] == 'Delete':
            if os.path.exists(symlink):
                try:
                    os.remove(symlink)
                    log.info('Removed Symlink: %s' % symlink)
                except OSError, message:
                    log.error('Unable to remove symlink for %s - %s' % (symlink, message))

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
        log_file = '{}.log'.format(__pgmname__)
    else:
        log_file = os.path.expanduser(options.logfile)

    # If an absolute path is not specified, use the default directory.
    if not os.path.isabs(log_file):
        log_file = os.path.join(logger.LogDir, log_file)

    logger.start(log_file, log_level, timed=True)

    log.debug("Parsed command line options: {!s}".format(options))
    log.debug("Parsed arguments: %r" % args)

    list_returned = listItems('aly', 'Movies')
    print list_returned