#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Purpose:
        Program to Sync Remote Hosts

'''
from library import Library
from common import logger
from common.exceptions import (ConfigValueError, SQLError,
    UnexpectedErrorOccured, InvalidFilename)
from library.series.fileparser import FileParser
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
__version__ = '@version: $Rev$'

__author__ = "@author: AJ Reynolds"
__copyright__ = "@copyright: Copyright 2011, AJ Reynolds"
__status__ = "@status: Development"
__license__ = "@license: GPL"

__maintainer__ = "@organization: AJ Reynolds"
__credits__ = []

log = logging.getLogger(__pgmname__)


def use_library_logging(func):

    def wrapper(self, *args, **kw):
        # Set the library name in the logger
        logger.set_library(self.args.hostname.upper())
        try:
            return func(self, *args, **kw)
        finally:
            logger.set_library('')

    return wrapper


class SyncLibrary(Library):

    def __init__(self):
        super(SyncLibrary, self).__init__()

        sync1 = self.options.parser.add_argument_group("HostsNames",
                                                       description=None
                                                       )
        sync1.add_argument("-t", "--tigger", dest="hostname", default='',
            action="store_const", const="tigger",
            help="Sync Tigger for Aly")
        sync1.add_argument("-g", "--goofy", dest="hostname",
            action="store_const", const="goofy",
            help="Sync Goofy for Kim")
        sync1.add_argument("-e", "--eeyore", dest="hostname",
            action="store_const", const="eeyore",
            help="Sync Eeyore for Daniel")
        sync1.add_argument("-p", "--pluto", dest="hostname",
            action="store_const", const="pluto",
            help="Sync Pluto for Ben and Mac")
        sync1.add_argument("-l", "--local", dest="hostname",
            action="store_const", const="localhost",
            help="Sync Local Michelle on portable drive")

        sync2 = self.options.parser.add_argument_group("Media Type",
                                                       description=None
                                                       )
        sync2.add_argument("-s", "--series", dest="content",
                           action="append_const", const="Series",
                           help="Process Series")
        sync2.add_argument("-m", "--movies", dest="content",
                           action="append_const", const="Movies",
                           help="Process Movies")

        sync3 = self.options.parser.add_argument_group("Modifiers",
                                                       description=None
                                                       )
        sync3.add_argument("--build-drive", dest="bld_drive",
                           action="store_true", default=False,
                           help="Build a portable drive for remote syncing")
        sync3.add_argument("--build-dest", dest="bld_dest",
                           action="store", default='/media/28E264B5E26488C0',
                           help="Destination for Build Drive")
        sync3.add_argument("--checksum", dest="chksum",
                           action="store_true", default=False,
                           help="Use Checksum not Date and Time")
        sync3.add_argument("--delete", dest="delete",
                           action="store_true", default=False,
                           help="Delete any files on rmt that do not exist on local")
        sync3.add_argument("-n", "--dry-run", dest="dryrun",
                           action="store_true", default=False,
                           help="Don't Run Link Create Commands")
        sync3.add_argument("--ignore-existing", dest='ignore_existing',
                           action="store_true", default=False,
                           help="Skip updating files that exist on receiver")
        sync3.add_argument("--no-update", dest="no_update",
                           action="store_true", default=False,
                           help="Don't update database info on downloads")
        sync3.add_argument("--no-video", dest="novideo",
                           action="store_true", default=False,
                           help="Suppress Video Files, Only Move Support Files/Directories")
        sync3.add_argument("--reverse", dest="reverse",
                           action="store_true", default=False,
                           help="Reverse flow of Update, RMT --> Local")
        sync3.add_argument("-u", "--update", dest="update",
                           action="store_true", default=False,
                           help="Skip files that are newer on the receiver")
        sync3.add_argument("-x", "--exclude", dest="xclude",
                           action="append", default=[],
                           help="Exclude files/directories")
        sync3.add_argument("--rsync", dest="rsync",
                           action="store_true", default=False,
                           help='Bypass database and run full download')

        sync4 = self.options.parser.add_argument_group("syncRMT Already Running",
                                                       description=None
                                                       )
        sync4.add_argument("-c", "--cancel", dest="runaction",
                           action="store_const", const='cancel', default='ask',
                           help="Cancel this request and let existing run")
        sync4.add_argument("-r", "--restart", dest="runaction",
                           action="store_const", const='restart',
                           help="Stop existing and Restart with this request")

        self.fileparser = FileParser()
        self._printfmt = '%P\n'
        return

    @use_library_logging
    def sync(self, dir_name=''):

        self.dir_name = dir_name.rstrip(os.sep)
        self._update_args()

        if not self.args.bld_drive and self._rmt_offline(self.args.hostname):
            sys.exit(1)

        if not self.args.dryrun:
            self._chk_already_running()

        if self.args.bld_drive:
            self._series_src = self.args.SeriesLoc
            self._movies_src = self.args.MoviesLoc
            self._series_dst = '{}/{}/Series/'.format(self.args.bld_dest, self.args.hostname)
            self._movies_dst = '{}@{}:{}/'.format(self.args.UserId, self.args.hostname, self.args.MoviesRmt)
            self._build_dst = '{}load_movies'.format(self.args.bld_dest)
            if os.path.exists(self._build_dst):
                while True:
                    _answer = raw_input("Continue (Y or N), Movie Build File Already Exists: {}".format(self._build_dst))
                    if _answer.lower()[0] not in ['y', 'n']:
                        continue
                    elif _answer.lower()[0] == 'n':
                        sys.exit(1)
                    else:
                        break
        elif self.args.reverse:
            self._series_src = '{}@{}:{}/'.format(self.args.UserId, self.args.hostname, self.args.SeriesRmt)
            self._movies_src = '{}@{}:{}/'.format(self.args.UserId, self.args.hostname, self.args.MoviesRmt)
            self._series_dst = self.args.SeriesLoc
            self._movies_dst = self.args.MoviesLoc
        elif self.args.hostname == 'localhost':
            self._series_src = self.args.SeriesLoc
            self._movies_src = self.args.MoviesLoc
            self._series_dst = '{}/'.format(self.args.SeriesRmt)
            self._movies_dst = '{}/'.format(self.args.MoviesRmt)
        else:
            self._series_src = '{}/{}'.format(self.args.SeriesLoc, self.dir_name)
            self._movies_src = '{}/{}'.format(self.args.MoviesLoc, self.dir_name)
            self._series_dst = '{}@{}:{}/'.format(self.args.UserId, self.args.hostname, self.args.SeriesRmt)
            self._movies_dst = '{}@{}:{}/'.format(self.args.UserId, self.args.hostname, self.args.MoviesRmt)

        if self.args.rsync:
            if 'Series' in self.args.content:
                self._syncSeries()
            if 'Movies' in self.args.content:
                self._syncMovies()
            return

        if 'Series' in self.args.content:
            _sync_needed = self._get_list_series(self._series_src)
            if self.args.dryrun:
                for _entry in _sync_needed:
                    log.info(_entry)
            else:
                self._syncList(_sync_needed, self._series_src, self._series_dst)

        if 'Movies' in self.args.content:
            self._syncMovies()

        if not self.args.dryrun:
            self._update_xbmc()
        return

    def _syncSeries(self):
        log.info('Syncing - Series')

        cmd = ['rsync', '-rptvhogL{}'.format(self.args.CmdLineDryRun),
               '--progress',
               '--partial-dir=.rsync-partial',
               '--log-file={}'.format(log_file),
               '--exclude=lost+found']
        try:
            cmd.extend(self.args.CmdLineArgs)
            cmd.append(self._series_src)
            cmd.append(self._series_dst)
            log.verbose(' '.join(cmd))
            process = check_call(cmd, shell=False, stdin=None, stdout=None, stderr=None, cwd=os.path.join(self.args.SeriesLoc))
        except CalledProcessError, exc:
            if exc.returncode == 255 or exc.returncode == -9:
                sys.exit(1)
            else:
                log.error("Command %s returned with RC=%d" % (cmd, exc.returncode))
                self._update_xbmc()
                sys.exit(1)
        return

    def _syncMovies(self):
        log.info('Syncing - Movies')

        cmd = ['rsync', '-rptvhogL{}'.format(self.args.CmdLineDryRun),
               '--progress',
               '--partial-dir=.rsync-partial',
               '--log-file={}'.format(log_file),
               '--exclude=lost+found']
        cmd.extend(self.args.CmdLineArgs)
        cmd.append('{}/{}'.format(self._movies_src, self.dir_name))
        if self.args.bld_drive:
            cmd.append('--only-write-batch={}/load_movies'.format(self.args.bld_dest))
        cmd.append('{}'.format(self._movies_dst))
        log.verbose(' '.join(cmd))

        try:
            process = check_call(cmd, shell=False, stdin=None, stdout=None, stderr=None, cwd=os.path.join(self.args.MoviesLoc))
        except CalledProcessError, exc:
            if exc.returncode == 255 or exc.returncode == -9:
                sys.exit(1)
            else:
                log.error("Command %s returned with RC=%d" % (cmd, exc.returncode))
                self._update_xbmc()
                sys.exit(1)
        return

    def _get_list_series(self, directory):
        log.trace('_get_list_series: Getting list of files requiring Sync')

        _downloaded_files = []
        _sync_needed = []
        _reg_ex_dir = re.compile('^{}.*$'.format(directory), re.IGNORECASE)
        try:
            db = sqlite3.connect(self.settings.DBFile)
            cursor = db.cursor()
            cursor.execute('SELECT FileName FROM Downloads  WHERE Name = "{}"'.format(self.args.hostname))
            for row in cursor:
                _downloaded_files.append(unicodedata.normalize('NFKD', row[0]).encode('ascii', 'ignore'))
            db.close()
            for _root, _dirs, _files in os.walk(os.path.abspath(directory), followlinks=True):
                if _dirs:
                    _dirs.sort()
                _files.sort()
                for _file in _files:
                    _target = re.split(directory, os.path.join(_root, _file))[1].lstrip(os.sep)
                    episode = os.path.join(self.settings.SeriesDir, _target)
                    _no_skip = True
                    if episode not in _downloaded_files:
                        for item in self.args.xclude:
                            if re.search(item, episode): _no_skip = False
                        if _no_skip: _sync_needed.append(_target)
        except:
            db.close()
            log.error("Incrementals Not Processed: SQLITE3 Error")
            return []
        return _sync_needed

    def _syncList(self, sync_needed, directory, target):
        log.info('Syncing - List')
        if len(sync_needed) > 7 and not self.args.no_update:
            _every = 5
        else:
            _every = len(sync_needed)
        _counter = 0
        _file_list = []
        _file_names = {}

        for episode in sync_needed:
            _counter += 1
            _file_list.append('./{}'.format(episode))
            _file_name = os.path.join(self.settings.SeriesDir, episode)
            _series = episode.split(os.sep)[0]
            _file_names[_file_name] = _series
            quotient, remainder = divmod(_counter, _every)
            if remainder == 0:
                try:
                    self._process_batch(directory,
                                        target,
                                        _file_list,
                                        _file_names
                                        )
                    _file_list = []
                    _file_names = {}
                except CalledProcessError:
                    _file_list = []
                    break

        if _file_list != []:
            self._process_batch(directory, target, _file_list, _file_names)
        return

    def _process_batch(self, directory, target, file_list, file_names):
        log.trace('_process_batch: {}'.format(file_names))

        cmd = ['rsync', '-rptvhogLR'.format(self.args.CmdLineDryRun),
               '--progress', '--partial-dir=.rsync-partial',
               '--log-file={}'.format(log_file)]
        cmd.extend(file_list)
        cmd.append(target)
        log.verbose(' '.join(cmd))
        try:
            check_call(cmd, shell=False, stdin=None, stdout=None,
                       stderr=None, cwd=directory)
            if not self.args.no_update:
                for _file_name in file_names:
                    _series = file_names[_file_name]
                    self._record_download(_series, _file_name)
#            self._update_xbmc()
        except CalledProcessError, exc:
            log.error("Incremental rsync Command returned with RC=%d, Ending" % (exc.returncode))
            if exc.returncode == 255 or exc.returncode == -9:
                sys.exit(1)
            else:
#                self._update_xbmc()
                raise UnexpectedErrorOccured("Incremental rsync Command returned with RC=%d, Ending" % (exc.returncode))
        return

    def _record_download(self, series, file_name):
        try:
            db = sqlite3.connect(self.settings.DBFile)
            cursor = db.cursor()
            cursor.execute('INSERT INTO Downloads(Name, SeriesName, Filename) VALUES ("{}", "{}", "{}")'.format(self.args.hostname,
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

    def _rmt_offline(self, hostname):
        s = socket.socket()
        port = 32480  # port number is a number, not string
        try:
            s.connect((hostname, port))
            s.close()
        except Exception, e:
            ip_address = socket.gethostbyname(hostname)
            log.warn('%s(%s) appears to be offline - %s' % (self.args.hostname.upper(), ip_address, `e`))
            return True
        return False

    def _update_xbmc(self):
        if self.args.dryrun:
            return
        cmd = ['xbmc-send',
               '--host={}'.format(self.args.hostname),
               '--action=XBMC.UpdateLibrary(video)']
        try:
            check_call(cmd, shell=False, stdin=None, stdout=None,
                       stderr=None, cwd=self.settings.SeriesDir)
        except CalledProcessError, exc:
            log.error("Command %s returned with RC=%d" % (cmd, exc.returncode))
        return

    def _chk_already_running(self):
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
                    _rsync_hostname = cmdline[-1].split(':')[0].split('@')[1]
                    if _rsync_hostname == self.args.hostname:
                        if p.terminal:
                            self.args.runaction = 'cancel'
                        elif self.args.runaction == 'ask':
                            while True:
                                value = raw_input("syncrmt for: %s Already Running, Cancel This Request or Restart? (C/R): " % (self.args.hostname))
                                if not value:
                                    continue
                                if value.lower()[:1] == 'c':
                                    self.args.runaction = 'cancel'
                                    break
                                if value.lower()[:1] == 'r':
                                    self.args.runaction = 'restart'
                                    break
                        if self.args.runaction == 'cancel':
                            sys.exit(1)
                        else:
                            p.kill()
                            log.warn('Previous Session Killed: %s' % p.pid)
                            self.args.runaction = 'restart'
                            time.sleep(0.1)
#                            self._chk_already_running()
        return

    def _update_args(self):
        if self.args.hostname:
            profile = self.settings.GetSubscribers(req_profile=[self.args.hostname])
            self.args.UserId = profile[self.args.hostname]['UserId']
            self.args.SeriesRmt = profile[self.args.hostname]['SeriesDir']
            self.args.MoviesRmt = profile[self.args.hostname]['MovieDir']
            self.args.SeriesLoc = os.path.join(self.settings.SubscriptionDir, self.args.hostname, 'Series')
            self.args.MoviesLoc = os.path.join(self.settings.SubscriptionDir, self.args.hostname, 'Movies')
        else:
            self.options.parser.error('Missing Hostname Command Line Parameter')
            sys.exit(1)

        if self.args.content == None:
            self.args.content = ["Series", "Movies"]

        if self.args.dryrun:
            self.args.CmdLineDryRun = 'n'
        else:
            self.args.CmdLineDryRun = ''

        if self.args.reverse:
            self.args.rsync = True
            profile_loc = self.settings.GetSubscribers(req_profile=[socket.gethostname()])
            self.args.SeriesLoc = '{}/'.format(profile[self.args.hostname]['SeriesDir'])
            self.args.MoviesLoc = '{}/'.format(profile[self.args.hostname]['MovieDir'])

        if self.args.bld_drive:
            self.args.no_update = True
            if self.args.reverse:
                self.options.parser.error('--reverse and --build-drive can not be used together')
                sys.exit(1)
            if not self.args.bld_dest:
                self.options.parser.error('--build-dest required with --build-drive')
                sys.exit(1)
            if not os.path.exists(self.args.bld_dest) and not self.args.dryrun:
                self.options.parser.error('--build-dest does not exist: {}'.format(self.args.bld_dest))
                sys.exit(1)

        self.args.CmdLineArgs = ['-i']

        if self.args.update or self.args.bld_drive:
            self.args.CmdLineArgs.append('-u')

        if self.args.ignore_existing or self.args.bld_drive:
            self.args.CmdLineArgs.append('--ignore-existing')

        if self.args.chksum:
            self.args.CmdLineArgs.append('--checksum')

        if self.args.delete:
            self.args.CmdLineArgs.append('--delete-before')

        if self.args.xclude:
            for item in self.args.xclude:
                self.args.CmdLineArgs.append('--exclude=*{}*'.format(item))

        if self.args.novideo:
            for entry in self.settings.MediaExt:
                self.args.CmdLineArgs.append('--exclude=*.{}'.format(entry))
                self.args.CmdLineArgs.append('--exclude=*.{}'.format(entry.upper()))

        return


if __name__ == '__main__':

    logger.initialize()
    library = SyncLibrary()

    Library.args = library.options.parser.parse_args(sys.argv[1:])
    log.debug("Parsed command line: {!s}".format(library.args))

    log_level = logging.getLevelName(library.args.loglevel.upper())

    if library.args.logfile == 'daddyvision.log':
        log_file = 'syncrmt_{}.log'.format(library.args.hostname)
    else:
        log_file = os.path.expanduser(library.args.logfile)

    # If an absolute path is not specified, use the default directory.
    if not os.path.isabs(log_file):
        log_file = os.path.join(logger.LogDir, log_file)

    logger.start(log_file, log_level, timed=True)

    if len(library.args.library) > 0:
        for entry in library.args.library:
            library.sync(entry)
    else:
            library.sync()
