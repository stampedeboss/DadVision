#!/usr/bin/env python
"""
Purpose:
    Program to watch for changes in the download folders and invoke the
    appropriate actions based on subject matter.

    Subject matter is arranged in the following categories:
        Series, Movies, or Other/Unknown
"""
from daddyvision.common.exceptions import ConfigValueError
from daddyvision.common import logger
from daddyvision.common.settings import Settings
from daddyvision.common.daemon import Daemon
from daddyvision.library.distribute import Distribute
from pyinotify import IN_CREATE, IN_MOVED_TO
import os
import sys
import logging
import pyinotify

__author__ = "AJ Reynolds"
__copyright__ = "Copyright 2011, AJ Reynolds"
__credits__ = []
__license__ = "GPL"

__pgmname__ = 'DownloadMonitor'
__version__ = '$Rev$'

__maintainer__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"
__status__ = "Development"

log = logging.getLogger(__pgmname__)

class MyDaemon(Daemon):
    def run(self):

        self.config = Settings()

        while True:
            if not os.path.exists(self.config.WatchDir):
                log.error("Path Not Found: %s" % self.config.WatchDir)
                raise ConfigValueError("Configuration Issue Watch Directory Not Found: %s" % self.config.WatchDir)

            log.debug('Found watch directory: %s' % self.config.watch_dir)

            pHandler = PackageHandler()
            watchManager  = pyinotify.WatchManager()
            mask    = IN_CREATE | IN_MOVED_TO
            handler = EventHandler(pHandler)
            notifier= pyinotify.Notifier(watchManager, handler)
            log.trace('Notifier Created')
            watchDir1 = watchManager.add_watch(self.config.WatchDir, mask, rec=True)
            log.info('Watching Directory: %s' % self.config.WatchDir)
            if not options.debug:
                try:
                    notifier.loop()
                except:
                    pass
                pass
            else: notifier.loop()

class EventHandler(pyinotify.ProcessEvent):
    ''' Handle Events related to new files being moved or added to the watched folder
    '''
    def __init__(self, pHandler):
        self.pHandler = pHandler

    def process_IN_CREATE(self, event):
        log.info("-----------------------------------")
        log.info("Create Event: " + event.pathname)
        self.pHandler.NewDownload(event.pathname)

    def process_IN_MOVED_TO(self, event):
        log.info("-----------------------------------")
        log.info("Moved Event: " + event.pathname)
        self.pHandler.NewDownload(event.pathname)

class PackageHandler(object):
    ''' Process the file or directory passed
    '''
    def __init__(self):
        self.distribute = Distribute()
        log.debug('PackageHandler Initialized')

    def NewDownload(self, pathname):
        self.distribute.ProcessFile(pathname)

if __name__ == "__main__":

    from daddyvision.common.options import OptionParser, CoreOptionParser

    logger.initialize()

    parser = CoreOptionParser()
    options, args = parser.parse_args()

    log_level = logging.getLevelName(options.loglevel.upper())
    log_file = os.path.expanduser(options.logfile)

    # If an absolute path is not specified, use the default directory.
    if not os.path.isabs(log_file):
        log_file = os.path.join(logger.LogDir, log_file)

    logger.start(log_file, log_level)

    log.debug("Parsed command line options: {!s}".format(options))
    log.debug("Parsed arguments: %r" % args)


    log.info('********************************************************************************************')
    log.info("Parsed command line options: %r" % options)
    log.debug("Parsed arguments: %r" % args)

    if options.loglevel != 'DEBUG' and options.loglevel != 'VERBOSE':
        if len(args) != 1 or (args[0].lower() != 'start' and args[0].lower() != 'stop' and args[0].lower() != 'restart'):
            parser.error('Invalid or missing arguments')

    daemon = MyDaemon('/tmp/daemon-example.pid')

    if options.debug or options.verbose:
        log.info('******* DEBUG Selected, Not using Daemon ********')
        log.info("**************    %s     ***************" % __version__)
        daemon.run()
    elif 'start' == args[0]:
        log.info("*************** STARTING DAEMON ****************" )
        log.info("**************    %s     ***************" % __version__)
        daemon.start()
    elif 'stop' == args[0]:
        log.info("*************** STOPING DAEMON *****************" )
        log.info("**************    %s     ***************" % __version__)
        daemon.stop()
    elif 'restart' == args[0]:
        log.info("************** RESTARTING DAEMON ***************" )
        log.info("**************    %s     ***************" % __version__)
        daemon.restart()
