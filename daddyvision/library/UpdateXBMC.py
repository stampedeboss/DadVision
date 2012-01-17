#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Purpose:
Program to watch for changes in the TV, Movie, and Links folders and take the
appropriate actions based on new subject matter.

"""
from daddyvision.common import logger
from daddyvision.common.daemon import Daemon
from daddyvision.common.exceptions import ConfigValueError
from daddyvision.common.options import OptionParser, CoreOptionParser
from daddyvision.common.settings import Settings
from daddyvision.library.distribute import Distribute
from logging import INFO, WARNING, ERROR, DEBUG
from pyinotify import IN_CREATE, IN_MOVED_TO
import logging
import os
import pyinotify
import re
import subprocess
import sys
import time

__pgmname__ = 'UpdateXBMC'
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

parser = CoreOptionParser()
options, args = parser.parse_args()

log_level = logging.getLevelName(options.loglevel.upper())

if options.logfile == 'daddyvision.log':
    log_file = 'UpdateXBMC.log'
else:
    log_file = os.path.expanduser(options.logfile)

# If an absolute path is not specified, use the default directory.
if not os.path.isabs(log_file):
    log_file = os.path.join(logger.LogDir, log_file)

logger.start(log_file, log_level, timed=True)

log.debug("Parsed command line options: {!s}".format(options))
log.debug("Parsed arguments: %r" % args)

if options.loglevel != 'DEBUG' and options.loglevel != 'TRACE':
    if len(args) != 1 or (args[0].lower() != 'start' and args[0].lower() != 'stop' and args[0].lower() != 'restart'):
        parser.error('Invalid or missing arguments')

class MyDaemon(Daemon):

    def run(self):

        while True:
            if not os.path.exists(config.SeriesDir):
                log.error("Path Not Found: %s" % config.SeriesDir)
                log.error("Invalid Config Entries, Ending")
                sys.exit(1)
            if not os.path.exists(config.MoviesDir):
                log.error("Path Not Found: %s" % config.MoviesDir)
                log.error("Invalid Config Entries, Ending")
                sys.exit(1)
            if not os.path.exists(config.SubscriptionDir):
                log.error("Path Not Found: %s" % config.SubscriptionDir)
                log.error("Invalid Config Entries, Ending")
                sys.exit(1)

            log.debug('Found watch directories')

            pHandler = PackageHandler()
            watchManager = pyinotify.WatchManager()
            mask	 = IN_CREATE | IN_MOVED_TO
            handler = EventHandler(pHandler)
            notifier = pyinotify.Notifier(watchManager, handler)
            log.debug('Notifier Created')
            watchManager.add_watch(config.SeriesDir, mask, rec=True)
            log.info('Watching Directory: %s' % (config.SeriesDir))
            watchManager.add_watch(config.MoviesDir, mask, rec=True)
            log.info('Watching Directory: %s' % (config.MoviesDir))
            watchManager.add_watch(config.SubscriptionDir, mask, rec=True)
            log.info('Watching Directory: %s' % config.SubscriptionDir)
            if options.loglevel not in ['DEBUG', 'TRACE']:
                try:
                    notifier.loop()
                except:
                    log.error('{}'.format(sys.exc_info()[1]))
                    pass
                pass
            else:
                notifier.loop()

class EventHandler(pyinotify.ProcessEvent):
    ''' Handle Events related to new files being moved or added to the watched folder
    '''
    def __init__(self, pHandler):
        self.pHandler = pHandler

    def process_IN_CREATE(self, event):
        log.info("-----------------------------------")
        log.info("Create Event: " + event.pathname)
        self.pHandler.SyncRmt(event.pathname)

    def process_IN_MOVED_TO(self, event):
        log.info("-----------------------------------")
        log.info("Moved Event: " + event.pathname)
        self.pHandler.SyncRmt(event.pathname)

class PackageHandler(object):
    ''' Process the file or directory passed
    '''
    def __init__(self):
        log.debug('PackageHandler Initialized')
        self.user_profiles = config.GetSubscribers()

    def SyncRmt(self, pathname):
        log.debug('SyncRmt: Start - {}'.format(pathname))
        _episode = re.split('^{}'.format(config.SeriesDir), pathname)
        _movie = re.split('^{}'.format(config.MoviesDir), pathname)

        for user in config.Users:
            print os.path.join('^{}'.format(config.SubscriptionDir),user)
            links = re.match(os.path.join('^{}'.format(config.SubscriptionDir),user), pathname)
            if links:
                log.info('New Link Added: %s' % pathname)
                self._run_update(user)
            elif len(_episode) > 1:
                _symlink = os.path.join(config.SubscriptionDir, user, 'Series')
                _symlink = _symlink + _episode[1]
                _symlink_inc = os.path.join(config.SubscriptionDir, user, 'Incrementals')
                _symlink_inc = _symlink_inc + _episode[1]
                if os.path.exists(_symlink) or os.path.exists(_symlink_inc):
                    log.info('update required: {} - {}'.format(user, pathname))
                    self._run_update(user)
                else:
                    continue
            elif len(_movie) > 1:
                tgt = '/mnt/Links/%s/Movies/' % user
                symlink = tgt + _movie[1]
                log.debug(symlink)
                if os.path.exists(symlink):
                    log.info('Update Required:{} - {}'.format(user, os.path.basename(pathname)))
                    self._run_update(user)
                else:
                    continue
            else:
                continue

    def _run_update(self, user):
        log.debug('_run_update: {}'.format(user))
        if user in self.user_profiles:
            cmd = ['syncrmt', '-{}br'.format(self.user_profiles[user]['Identifier'])]
            subprocess.Popen(cmd, stdin=None, stdout=None, stderr=None)
        else:
            raise ConfigValueError('Configuration File Error, User not fully configured ')
        return

if __name__ == "__main__":

    daemon = MyDaemon('/tmp/daemon-UpdateXBMC.pid')

    try:
        from subprocess import Popen, PIPE
        _p = Popen(["svnversion", "."], stdout=PIPE)
        REVISION= _p.communicate()[0]
        REVISION='Revision: {}'.format(REVISION.strip('\n').strip())
        _p = None # otherwise we get a wild exception when Django auto-reloads
    except Exception, e:
        print "Could not get revision number: ", e
        REVISION='Version: {}'.format(__version__)

    if options.loglevel == 'DEBUG' or options.loglevel == 'TRACE':
        log.info('******* DEBUG Selected, Not using Daemon ********')
        log.info("**************  %s    ***************" % REVISION)
        daemon.run()
    elif 'start' == args[0]:
        log.info("*************** STARTING DAEMON ****************" )
        log.info("**************  %s    ***************" % REVISION)
        daemon.start()
    elif 'stop' == args[0]:
        log.info("*************** STOPING DAEMON *****************" )
        log.info("**************  %s    ***************" % REVISION)
        daemon.stop()
    elif 'restart' == args[0]:
        log.info("************** RESTARTING DAEMON ***************" )
        log.info("**************  %s    ***************" % REVISION)
        daemon.restart()
