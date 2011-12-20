#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import sys
import logging
import atexit
from daddyvision.common.settings import Settings
from datetime import datetime, timedelta
log = logging.getLogger('manager')

def useExecLogging(func):

    def wrapper(self, *args, **kw):
        # Set the feed name in the logger
        from daddyvision.common import logger
        import time
        logger.set_execution(str(time.time()))
        try:
            return func(self, *args, **kw)
        finally:
            logger.set_execution('')

    return wrapper


class Manager(object):

    """Manager class for daddyvision.series
    """

    unit_test = False
    options = None

    def __init__(self, options):
        global manager
        assert not manager, 'Only one instance of Manager should be created at a time!'
        manager = self
        self.options = options
        self.config = Settings()
        self.acquire_lock()
        atexit.register(self.shutdown)

    def __del__(self):
        global manager
        manager = None

    def check_lock(self):
        """Checks if there is already a lock, returns True if there is."""
        if os.path.exists(self.lockfile):
            # check the lock age
            lock_time = datetime.fromtimestamp(os.path.getmtime(self.lockfile))
            if (datetime.now() - lock_time).seconds > 36000:
                log.warning('Lock file over 10 hour in age, ignoring it ...')
            else:
                return True
        return False

    def acquire_lock(self):
        if self.options.log_start:
            log.info('FlexGet started (PID: %s)' % os.getpid())

        # Exit if there is an existing lock.
        if self.check_lock():
            if not self.options.quiet:
                f = file(self.lockfile)
                pid = f.read()
                f.close()
                print >> sys.stderr, 'Another process (%s) is running, will exit.' % pid.strip()
                print >> sys.stderr, 'If you\'re sure there is no other instance running, delete %s' % self.lockfile
            sys.exit(1)

        f = file(self.lockfile, 'w')
        f.write('PID: %s\n' % os.getpid())
        f.close()
        atexit.register(self.release_lock)

    def release_lock(self):
        if self.options.log_start:
            log.info('FlexGet stopped (PID: %s)' % os.getpid())
        if os.path.exists(self.lockfile):
            os.remove(self.lockfile)
            log.debug('Removed %s' % self.lockfile)
        else:
            log.debug('Lockfile %s not found' % self.lockfile)

    @useExecLogging
    def execute(self, options):

        from daddyvision.unit_test.fileparseCheckNew import ScanDownload

        dir_scan = ScanDownload()
        file_count = dir_scan.ScanDir('/mnt?TV/New')


    def shutdown(self):
        """ Application is being exited
        """
        if not self.unit_test: # don't scroll "nosetests" summary results when logging is enabled
            log.debug('Shutting down')
        self.engine.dispose()
        # remove temporary database used in test mode
        if self.options.test:
            if not 'test' in self.db_filename:
                raise Exception('trying to delete non test database?')
            os.remove(self.db_filename)
            log.info('Removed test database')
        if not self.unit_test: # don't scroll "nosetests" summary results when logging is enabled
            log.debug('Shutdown completed')
