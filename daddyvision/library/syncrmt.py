#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Purpose:
        Program to Sync Remote Hosts

'''
from daddyvision.common import logger
from daddyvision.common.exceptions import ConfigValueError, SQLError, UnexpectedErrorOccured, InvalidFilename
from daddyvision.common.options import OptionParser, OptionGroup
from daddyvision.common.settings import Settings
from daddyvision.series.fileparser import FileParser
from subprocess import Popen, call as Call,  check_call, CalledProcessError
import logging
import os
import sqlite3
import sys
import time
import psutil
import tempfile
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

class DaddyvisionNetwork(object):

    def __init__(self, options):
        self.options = options
        self._add_runtime_options()
        self.fileparser = FileParser()
        return

    def SyncRMT(self):

        if not self.options.dryrun:
            self.chkStatus(self.options.SymLinks)
            time.sleep(0.2)
            self.chkStatus(self.options.SymLinks)


        if 'Series' in self.options.content:
            if os.path.exists(os.path.join(self.options.SymLinks, 'Incrementals')):
                self.SyncIncrementals(os.path.join(self.options.SymLinks, 'Incrementals'))
            self.SyncSeries()

        if 'Movies' in self.options.content:
            self.SyncMovies()

        if not self.options.dryrun:
            cmd = ['xbmc-send', '--host={}'.format(self.options.HostName), '--action=XBMC.UpdateLibrary(video)']
            try:
                process = check_call(cmd, shell=False, stdin=None, stdout=None, stderr=None, cwd=config.SeriesDir)
            except CalledProcessError, exc:
                log.error("Command %s returned with RC=%d" % (cmd, exc.returncode))

    def SyncSeries(self):
        log.info('Syncing - Series')

        log_file = os.path.join(logger.LogDir, 'syncrmt_{}.log'.format(self.options.HostName))
        cmd = ['rsync', '-rptuvhogL{}'.format(self.options.CmdLineDryRun),
               '--progress',
               '--partial-dir=.rsync-partial',
               '--exclude=lost+found',
               self.options.SeriesDeleteExclusions,
               '{}'.format(self.options.CmdLineArgs),
               '--log-file={}'.format(log_file),
               '{}/Series/'.format(self.options.SymLinks),
               '{}@{}:{}/'.format(self.options.UserId, self.options.HostName, self.options.SeriesRmt)]

        try:
            process = check_call(cmd, shell=False, stdin=None, stdout=None, stderr=None, cwd=os.path.join(self.options.SymLinks, 'Series'))
        except CalledProcessError, exc:
            log.error("Command %s returned with RC=%d" % (cmd, exc.returncode))
            sys.exit(1)

    def SyncMovies(self):
        log.info('Syncing - Movies')

        log_file = os.path.join(logger.LogDir, 'syncrmt_{}.log'.format(self.options.HostName))
        cmd = ['rsync', '-rptuvhogL{}'.format(self.options.CmdLineDryRun),
               '--progress',
               '--partial-dir=.rsync-partial',
               '--exclude=lost+found',
               '{}'.format(self.options.CmdLineArgs),
               '--log-file={}'.format(log_file),
               '{}/Movies/'.format(self.options.SymLinks),
               '{}@{}:{}/'.format(self.options.UserId, self.options.HostName, self.options.MoviesRmt)]
        try:
            process = check_call(cmd, shell=False, stdin=None, stdout=None, stderr=None, cwd=os.path.join(self.options.SymLinks, 'Movies'))
        except CalledProcessError, exc:
            log.error("Command %s returned with RC=%d" % (cmd, exc.returncode))
            sys.exit(1)

    def SyncIncrementals(self, directory):
        log.info('Syncing - Incremental Series')

        printfmt = '%P\n'
        _downloaded_files = []
        _sync_needed = []

        try:
            db = sqlite3.connect(config.DBFile)
            cursor = db.cursor()
            cursor.execute('SELECT FileName FROM Downloads  WHERE Name = "{}"'.format(self.options.user))
            for row in cursor:
                _downloaded_files.append(unicodedata.normalize('NFKD', row[0]).encode('ascii','ignore'))
            db.close()
        except:
            db.close()
            raise

        _available_files_temp = tempfile.NamedTemporaryFile()
        cmd = ['find', '-L','-type', 'f', '-printf', '{}'.format(printfmt)]
        log.trace("Calling %s" % cmd)
        try:
            process = check_call(cmd, shell=False, stdin=None, stdout=_available_files_temp, stderr=_available_files_temp, cwd=directory)
        except CalledProcessError, exc:
            log.error("Initial Find Command returned with RC=%d, Ending" % (exc.returncode))
            sys.exit(1)

        _sync_needed_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        with open(_sync_needed_file.name, "w") as _sync_needed_file_obj:
            with open(_available_files_temp.name, "r") as _available_files_obj:
                for _line in _available_files_obj.readlines():
                    episode = os.path.join(config.SeriesDir, _line.strip('\n'))
                    if episode not in _downloaded_files:
                        _sync_needed_file_obj.write(_line)
                        _sync_needed.append(episode)
            _available_files_obj.close()
            _sync_needed_file_obj.close()

        log_file = os.path.join(logger.LogDir, 'syncrmt_{}.log'.format(self.options.HostName))
        cmd = ['rsync', '-rptuvhogLR'.format(self.options.CmdLineDryRun), '--progress', '--partial-dir=.rsync-partial',
               '--log-file={}'.format(log_file),
               '--files-from={}'.format(_sync_needed_file.name),
               './',
               '{}@{}:{}/'.format(self.options.UserId, self.options.HostName, self.options.SeriesRmt)]
        try:
            process = check_call(cmd, shell=False, stdin=None, stdout=None, stderr=None, cwd=directory)
        except CalledProcessError, exc:
            log.error("Incremental rsync Command returned with RC=%d, Ending" % (exc.returncode))
            os.remove(_sync_needed_file.name)
            sys.exit(1)

        os.remove(_sync_needed_file.name)

        if not self.options.dryrun:
            for episode in _sync_needed:
                self.record_download(episode)

        _series_delete_exclusions = '/tmp/{}_series_exclude_list'.format(self.options.HostName)
        _incremental_file_obj = open(_series_delete_exclusions, 'w')
        cmd = ['find', '.', '-type', 'l', '-printf', printfmt]
        try:
            process = check_call(cmd, shell=False, stdin=None, stdout=_incremental_file_obj, stderr=None, cwd=directory)
        except CalledProcessError, exc:
            log.error("Find Command for Series Exclusions returned with RC=%d" % (exc.returncode))
            sys.exit(1)

        self.options.SeriesDeleteExclusions = '--exclude-from={}'.format(_series_delete_exclusions)
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

        self.options.CmdLineArgs = ''

        if self.options.delete:
            self.options.CmdLineArgs = self.options.CmdLineArgs + '--delete'

        if self.options.xclude:
            self.options.CmdLineArgs = self.options.CmdLineArgs + ' --exclude=*{}*'.format(self.options.xclude)

        return

    def record_download(self, file_name):
        try:
            file_details = self.fileparser.getFileDetails(file_name)
        except InvalidFilename, e:
            return
        except:
            raise UnexpectedErrorOccured("File Information Insert: {} {}".format(e, file_name))
        try:
            db = sqlite3.connect(config.DBFile)
            cursor = db.cursor()
            cursor.execute('INSERT INTO Downloads(Name, SeriesName, Filename) VALUES ("{}", "{}", "{}")'.format(self.options.user,
                                                                                                                file_details['SeriesName'],
                                                                                                                file_name))
            db.commit()
            db.close()
        except  sqlite3.IntegrityError, e:
            db.close()
        except sqlite3.Error, e:
            db.close()
            raise UnexpectedErrorOccured("File Information Insert: {} {}".format(e, file_name))


    def chkStatus(self, directory, recurse=False):
        time.sleep(0.2)
        pidList = psutil.process_iter()
        for p in pidList:
            cmdline = p.cmdline
            if len(cmdline) > 0:
                if p.name == 'rsync':
                    if os.path.split(cmdline[-2].rstrip(os.sep))[0] == directory.rstrip(os.sep):
                        if options.runaction == 'ask':
                            while True:
                                value = raw_input("syncrmt for: %s Already Running, Cancel This Request or Restart? (C/R): " % (directory))
                                if not value:
                                    continue
                                if value.lower()[:1] == 'c':
                                    options.runaction = 'cancel'
                                    break
                                if value.lower()[:1] == 'r':
                                    options.runaction = 'restart'
                                    break
                        if options.runaction == 'cancel':
                            log.warn('rmtsync for : %s is Already Running, Request Canceled' % directory)
                            sys.exit(1)
                        else:
                            os.system('sudo kill -kill %s' % p.pid)
                            log.warn('Previous Session Killed: %s' % p.pid)
                            options.runaction = 'restart'
                            time.sleep(0.1)
                            self.chkStatus(directory)
        return

class localOptions(OptionParser):

    def __init__(self, unit_test=False, **kwargs):
        OptionParser.__init__(self, **kwargs)

        group = OptionGroup(self, "Users")
        group.add_option("-a", "--aly", dest="user", default='',
            action="store_const", const="aly",
            help="Sync Tigger for Aly")
        group.add_option("-k", "--kim", dest="user",
            action="store_const", const="kim",
            help="Sync Goofy for Kim")
        group.add_option("-p", "--peterson", dest="user",
            action="store_const", const="ben",
            help="Sync Tigger for Ben and Mac")
        self.add_option_group(group)

        group = OptionGroup(self, "Media Type")
        group.add_option("-s", "--series", dest="content", default=[],
            action="store_const", const=["Series"],
            help="process TV Series")
        group.add_option("-m", "--movies", dest="content",
            action="store_const", const=["Movies"],
            help="process Movies")
        group.add_option("-b", "--both", dest="content",
            action="store_const", const=["Series", "Movies"],
            help="process both TV Series and Movies")
        self.add_option_group(group)

        group = OptionGroup(self, "Modifers")
        group.add_option("-n", "--dry-run", dest="dryrun",
            action="store_true", default=False,
            help="Don't Run Link Create Commands")
        group.add_option("--delete", dest="delete",
            action="store_true", default=False,
            help="Delete any files on rmt that do not exist on local")
        group.add_option("-x", "--exclude", dest="xclude",
            action="store", type="string", default="",
            help="Exclude files/directories")
        self.add_option_group(group)

        group = OptionGroup(self, "SyncRMT Already Running")
        group.add_option("-c", "--cancel", dest="runaction",
            action="store_const", const='cancel', default='ask',
            help="Cancel this request and let existing run")
        group.add_option("-r", "--restart", dest="runaction",
            action="store_const", const='restart',
            help="Stop existing and Restart with this request")
        self.add_option_group(group)


if __name__ == '__main__':

    parser = localOptions()
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

    syncrmt = DaddyvisionNetwork(options)
    syncrmt = syncrmt.SyncRMT()
