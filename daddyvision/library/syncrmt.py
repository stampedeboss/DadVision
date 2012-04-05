#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Purpose:
        Program to Sync Remote Hosts

'''
from daddyvision.common import logger
from daddyvision.common.exceptions import (ConfigValueError, SQLError,
    UnexpectedErrorOccured, InvalidFilename)
from daddyvision.common.options import OptionParser, OptionGroup
from daddyvision.common.settings import Settings
from daddyvision.series.fileparser import FileParser
from subprocess import Popen, call as Call, check_call, CalledProcessError
import logging
import os
import psutil
import re
import socket
import sqlite3
import sys
import tempfile
import time
import unicodedata

__pgmname__ = 'syncrmt'
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
printfmt = '%P\n'

def use_library_logging(func):

    def wrapper(self, *args, **kw):
        # Set the library name in the logger
        from daddyvision.common import logger
        logger.set_library(self.options.HostName.upper())
        try:
            return func(self, *args, **kw)
        finally:
            logger.set_library('')

    return wrapper

class DaddyvisionNetwork(object):

    def __init__(self, options):
        self.options = options
        self._add_runtime_options()
        self.fileparser = FileParser()
        self.log_file = os.path.join(logger.LogDir, 'rsync_{}.log'.format(self.options.HostName))
        return

    @use_library_logging
    def syncRMT(self, dir_name=''):

        self.dir_name = dir_name.rstrip(os.sep)
        if self.dir_name:
            options.suppress_incremental = True

        s = socket.socket()
        port = 32480 # port number is a number, not string
        try:
            s.connect((self.options.HostName, port))
            s.close()
        except Exception, e:
            ip_address = socket.gethostbyname(self.options.HostName)
            log.warn('%s(%s) appears to be offline - %s' % (self.options.HostName.upper(), ip_address, `e`))
            sys.exit(0)

        if not self.options.dryrun:
            self._chk_status()
 #           time.sleep(0.2)
 #           self._chk_status()

        if not self.options.SeriesRmt and not self.options.MoviesRmt and not self.options.dryrun:
            self._update_xbmc()
            sys.exit(0)

        if 'Series' in self.options.content:
            self.syncSeries()
            if not options.suppress_incremental and os.path.exists(os.path.join(self.options.SymLinks, 'Incrementals')):
                self.syncIncrementals(os.path.join(self.options.SymLinks, 'Incrementals'))

        if 'Movies' in self.options.content:
            self.syncMovies()

    def syncSeries(self):
        log.info('Syncing - Series')

        _series_delete_exclusions = '/tmp/{}_series_exclude_list'.format(self.options.HostName)
        _incremental_file_obj = open(_series_delete_exclusions, 'w')

        cmd = ['find', '.', '-type', 'l', '-printf', printfmt]
        try:
            process = check_call(cmd, shell=False, stdin=None, stdout=_incremental_file_obj, stderr=None, cwd=os.path.join(self.options.SymLinks, 'Incrementals'))
        except CalledProcessError, exc:
            log.error("Find Command for Series Exclusions returned with RC=%d" % (exc.returncode))
            sys.exit(1)

        cmd = ['rsync', '-rptvhogL{}'.format(self.options.CmdLineDryRun),
               '--progress',
               '--partial-dir=.rsync-partial',
               '--log-file={}'.format(self.log_file),
               '--exclude=lost+found']
        try:
            if not options.reverse:
                cmd.append('--exclude-from={}'.format(_series_delete_exclusions))
                cmd.extend(self.options.CmdLineArgs)
                cmd.append('{}/Series/{}'.format(self.options.SymLinks, self.dir_name))
                cmd.append('{}@{}:{}/'.format(self.options.UserId, self.options.HostName, self.options.SeriesRmt))
                log.verbose(' '.join(cmd))
                process = check_call(cmd, shell=False, stdin=None, stdout=None, stderr=None, cwd=os.path.join(self.options.SymLinks, 'Series'))
            else:
                cmd.extend(self.options.CmdLineArgs)
                cmd.append('{}@{}:{}/{}'.format(self.options.UserId, self.options.HostName, self.options.SeriesRmt, self.dir_name))
                cmd.append('{}/'.format(config.SeriesDir))
                log.verbose(' '.join(cmd))
                process = check_call(cmd, shell=False, stdin=None, stdout=None, stderr=None, cwd=config.SeriesDir)

            if not self.options.dryrun:
                self._update_xbmc()
        except CalledProcessError, exc:
            if exc.returncode == 255 or exc.returncode == -9:
                sys.exit(1)
            else:
                log.error("Command %s returned with RC=%d" % (cmd, exc.returncode))
                self._update_xbmc()
                sys.exit(1)


    def syncMovies(self):
        log.info('Syncing - Movies')

        cmd = ['rsync', '-rptvhogL{}'.format(self.options.CmdLineDryRun),
               '--progress',
               '--partial-dir=.rsync-partial',
               '--log-file={}'.format(self.log_file),
               '--exclude=lost+found']
        cmd.extend(self.options.CmdLineArgs)

        try:
            if not options.reverse:
                cmd.append('{}/Movies/{}'.format(self.options.SymLinks, self.dir_name))
                cmd.append('{}@{}:{}/'.format(self.options.UserId, self.options.HostName, self.options.MoviesRmt))
            else:
                cmd.append('{}@{}:{}/{}'.format(self.options.UserId, self.options.HostName, self.options.MoviesRmt, self.dir_name))
                cmd.append('{}/Movies/'.format(self.options.SymLinks))

            log.verbose(' '.join(cmd))
            process = check_call(cmd, shell=False, stdin=None, stdout=None, stderr=None, cwd=os.path.join(self.options.SymLinks, 'Movies'))

            if not self.options.dryrun:
                self._update_xbmc()
        except CalledProcessError, exc:
            if exc.returncode == 255 or exc.returncode == -9:
                sys.exit(1)
            else:
                log.error("Command %s returned with RC=%d" % (cmd, exc.returncode))
                self._update_xbmc()
                sys.exit(1)

    def syncIncrementals(self, directory):
        log.info('Syncing - Incremental Series')

        _sync_needed = self._get_list(directory)
        if self.options.dryrun:
            for _entry in _sync_needed:
                log.info(_entry)
            return

        if len(_sync_needed) > 5:
            _every = 5
        else:
            _every = len(_sync_needed)
        _counter = 0
        _file_list = []
        _file_names = {}

        for episode in _sync_needed:
            _counter += 1
            _file_list.append('./{}'.format(episode))
            _file_name = os.path.join(config.SeriesDir, episode)
            _series = episode.split(os.sep)[0]
            _file_names[_file_name] = _series
            quotient, remainder = divmod(_counter, _every)
            if remainder == 0:
                try:
                    self._process_batch(directory, _file_list, _file_names)
                    _file_list = []
                    _file_names = {}
                except CalledProcessError, msg:
                    _file_list = []
                    break

        if _file_list != []:
            self._process_batch(directory, _file_list, _file_names)

        return

    def _get_list(self, directory):
        log.trace('_get_list: Getting list of Incremental files requiring Sync')

        _downloaded_files = []
        _sync_needed = []

        _reg_ex_dir = re.compile('^{}.*$'.format(directory), re.IGNORECASE)

        try:
            db = sqlite3.connect(config.DBFile)
            cursor = db.cursor()
            cursor.execute('SELECT FileName FROM Downloads  WHERE Name = "{}"'.format(self.options.user))
            for row in cursor:
                _downloaded_files.append(unicodedata.normalize('NFKD', row[0]).encode('ascii','ignore'))
            db.close()

            for _root, _dirs, _files in os.walk(os.path.abspath(directory),followlinks=True):
                if _dirs:
                    _dirs.sort()
                _files.sort()
                for _file in _files:
                    _target = re.split(directory, os.path.join(_root, _file))[1].lstrip(os.sep)
                    episode = os.path.join(config.SeriesDir, _target)
                    if episode not in _downloaded_files:
                        _sync_needed.append(_target)
        except:
            db.close()
            log.error("Incrementals Not Processed: SQLITE3 Error")
            return []

        return _sync_needed

    def _process_batch(self, directory, file_list, file_names):
        log.trace('_process_batch: {}'.format(file_names))

        cmd = ['rsync', '-rptvhogLR'.format(self.options.CmdLineDryRun), '--progress', '--partial-dir=.rsync-partial', '--log-file={}'.format(self.log_file)]
        cmd.extend(file_list)
        cmd.append('{}@{}:{}/'.format(self.options.UserId, self.options.HostName, self.options.SeriesRmt))
        log.verbose(' '.join(cmd))
        try:
            process = check_call(cmd, shell=False, stdin=None, stdout=None, stderr=None, cwd=directory)
            for _file_name in file_names:
                _series = file_names[_file_name]
                self._record_download(_series, _file_name)
            self._update_xbmc()
        except CalledProcessError, exc:
            log.error("Incremental rsync Command returned with RC=%d, Ending" % (exc.returncode))
            if exc.returncode == 255 or exc.returncode == -9:
                sys.exit(1)
            else:
                raise UnexpectedErrorOccured("Incremental rsync Command returned with RC=%d, Ending" % (exc.returncode))

    def _record_download(self, series, file_name):
        try:
            db = sqlite3.connect(config.DBFile)
            cursor = db.cursor()
            cursor.execute('INSERT INTO Downloads(Name, SeriesName, Filename) VALUES ("{}", "{}", "{}")'.format(self.options.user,
                                                                                                                series,
                                                                                                                file_name))
            db.commit()
        except  sqlite3.IntegrityError, e:
            pass
        except sqlite3.Error, e:
            db.close()
            raise UnexpectedErrorOccured("File Information Insert: {} {}".format(e, file_name))

        db.close()
        return

    def _update_xbmc(self):
        if not self.options.dryrun:
            cmd = ['xbmc-send', '--host={}'.format(self.options.HostName), '--action=XBMC.UpdateLibrary(video)']
            try:
                process = check_call(cmd, shell=False, stdin=None, stdout=None, stderr=None, cwd=config.SeriesDir)
            except CalledProcessError, exc:
                log.error("Command %s returned with RC=%d" % (cmd, exc.returncode))

    def _chk_status(self):
        time.sleep(0.2)
        pidList = psutil.process_iter()
        for p in pidList:
            cmdline = p.cmdline
            if len(cmdline) > 0:
                if p.name == 'rsync':
                    _rsync_target = cmdline[-1]
                    _rsync_target = _rsync_target.split(':')
                    if len(_rsync_target) < 2:
                        continue
                    _rsync_user = cmdline[-1].split(':')[0].split('@')[1]
                    if _rsync_user == self.options.HostName:
                        if p.terminal:
                            options.runaction = 'cancel'
                        elif options.runaction == 'ask':
                            while True:
                                value = raw_input("syncrmt for: %s Already Running, Cancel This Request or Restart? (C/R): " % (self.options.HostName))
                                if not value:
                                    continue
                                if value.lower()[:1] == 'c':
                                    options.runaction = 'cancel'
                                    break
                                if value.lower()[:1] == 'r':
                                    options.runaction = 'restart'
                                    break
                        if options.runaction == 'cancel':
#                            log.warn('rmtsync for : %s is Already Running, Request Canceled' % self.options.HostName)
                            sys.exit(1)
                        else:
                            p.kill()
                            log.warn('Previous Session Killed: %s' % p.pid)
                            options.runaction = 'restart'
                            time.sleep(0.1)
#                            self._chk_status()
        return

    def _add_runtime_options(self):
        if self.options.user:
            self.options.SymLinks = os.path.join(config.SubscriptionDir, self.options.user)

            profile = config.GetSubscribers(req_profile=[self.options.user])
            self.options.UserId = profile[self.options.user]['UserId']
            self.options.SeriesRmt = profile[self.options.user]['SeriesDir']
            self.options.MoviesRmt = profile[self.options.user]['MovieDir']
            self.options.HostName = profile[self.options.user]['HostName']
        else:
            parser.error('Missing User Command Line Parameter, Use "syncrmt --help" for details')
            sys.exit(1)

        if not self.options.content:
            parser.error('Missing Media Type Command Line Parameter, Use "syncrmt --help" for details')
            sys.exit(1)

        if self.options.dryrun:
            self.options.CmdLineDryRun = 'n'
        else:
            self.options.CmdLineDryRun = ''

        self.options.CmdLineArgs = []

        if not self.options.no_update:
            self.options.CmdLineArgs.append('-u')

        if self.options.ignore_existing:
            self.options.CmdLineArgs.append('--ignore-existing')

        if self.options.xclude:
            self.options.CmdLineArgs.append('--exclude=*{}*'.format(self.options.xclude))

        if self.options.novideo:
            for entry in config.MediaExt:
                self.options.CmdLineArgs.append('--exclude=*.{}'.format(entry))
                self.options.CmdLineArgs.append('--exclude=*.{}'.format(entry.upper()))

        if self.options.chksum:
            self.options.CmdLineArgs.append('--checksum')

        if self.options.delete:
            self.options.CmdLineArgs.append('--delete')

        if self.options.reverse:
            self.options.suppress_incremental = True

        return

class LocalOptions(OptionParser):

    def __init__(self, unit_test=False, **kwargs):
        OptionParser.__init__(self, **kwargs)

        group = OptionGroup(self, "Users")
        group.add_option("-a", "--aly", dest="user", default='',
            action="store_const", const="aly",
            help="Sync Tigger for Aly")
        group.add_option("-k", "--kim", dest="user",
            action="store_const", const="kim",
            help="Sync Goofy for Kim")
        group.add_option("-d", "--eeyore", dest="user",
            action="store_const", const="michelle",
            help="Sync Eeyore for Michelle")
        group.add_option("-p", "--peterson", dest="user",
            action="store_const", const="ben",
            help="Sync Tigger for Ben and Mac")
        self.add_option_group(group)

        group = OptionGroup(self, "Media Type")
        group.add_option("-s", "--series", dest="content", default=[],
            action="store_const", const=["Series"],
            help="process Series")
        group.add_option("-m", "--movies", dest="content",
            action="store_const", const=["Movies"],
            help="process Movies")
        group.add_option("-b", "--both", dest="content",
            action="store_const", const=["Series", "Movies"],
            help="process both Series and Movies")
        self.add_option_group(group)

        group = OptionGroup(self, "Modifers")
        group.add_option("--checksum", dest="chksum",
            action="store_true", default=False,
            help="Use Checksum not Date and Time")
        group.add_option("--delete", dest="delete",
            action="store_true", default=False,
            help="Delete any files on rmt that do not exist on local")
        group.add_option("-n", "--dry-run", dest="dryrun",
            action="store_true", default=False,
            help="Don't Run Link Create Commands")
        group.add_option("--ignore-existing", dest='ignore_existing',
            action="store_true", default=False,
            help="Use rysnc's --ignore-existing argument")
        group.add_option("--no-video", dest="novideo",
            action="store_true", default=False,
            help="Suppress Video Files, Only Move Support Files/Directories")
        group.add_option("--reverse", dest="reverse",
            action="store_true", default=False,
            help="Reverse flow of Update, RMT --> Local")
        group.add_option("--suppress", dest="suppress_incremental",
            action="store_true", default=False,
            help="Skip Processing of Incremental Subscriptions")
        group.add_option("--no-update", dest="no_update",
            action="store_true", default=False,
            help="Don't Skip files that are newer on the receiver")
        group.add_option("-x", "--exclude", dest="xclude",
            action="store", type="string", default="",
            help="Exclude files/directories")
        self.add_option_group(group)

        group = OptionGroup(self, "syncRMT Already Running")
        group.add_option("-c", "--cancel", dest="runaction",
            action="store_const", const='cancel', default='ask',
            help="Cancel this request and let existing run")
        group.add_option("-r", "--restart", dest="runaction",
            action="store_const", const='restart',
            help="Stop existing and Restart with this request")
        self.add_option_group(group)


if __name__ == '__main__':

    parser = LocalOptions()
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

    if len(args) > 0:
        if len(options.content) > 1:
            log.error("Passed Series/Movie Name can't use BOTH (-b) for content")
            sys.exit(1)
        for entry in args:
            syncrmt = DaddyvisionNetwork(options)
            syncrmt = syncrmt.syncRMT(entry)
    else:
        syncrmt = DaddyvisionNetwork(options)
        syncrmt = syncrmt.syncRMT()