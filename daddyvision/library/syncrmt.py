#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Purpose:
        Program to Sync Remote Hosts

'''
from daddyvision.common import logger
from daddyvision.common.exceptions import ConfigValueError, SQLError, UnexpectedErrorOccured
from daddyvision.common.options import OptionParser, OptionGroup
from daddyvision.common.settings import Settings
from daddyvision.series.fileparser import FileParser
from subprocess import Popen, CalledProcessError
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

db = sqlite3.connect(config.DBFile)
cursor = db.cursor()

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

        if os.path.exists(os.path.join(self.options.SymLinks, 'Incrementals')):
            self.SyncIncrementals(os.path.join(self.options.SymLinks, 'Incrementals'))

        if 'Series' in self.options.content:
            self.SyncSeries()
        
        if 'Movies' in self.options.content:
            self.SyncMovies

        if not self.options.dryrun:
            cmd = ['xbmc-send', '--host={}'.format(self.options.HostName), '--action="XBMC.UpdateLibrary(video)"']
            try:
                process = Popen(cmd, shell=False, stdin=None, stdout=None, stderr=None, cwd=self.options.SeriesDir)
                process.wait()
            except CalledProcessError, exc:
                log.error("Command %s returned with RC=%d" % (cmd, exc.returncode))

    def SyncSeries(self):
        log_file = os.path.join(logger.LogDir, 'syncrmt_{}.log'.format(self.options.HostName))
        cmd = ['rsync', '-rptuvhogLR'.format(self.options.CmdLineDryRun), 
               '--progress',
              '{}'.format(self.options.CmdLineArgs), 
               '--partial-dir=.rsync-partial', 
               '--log-file={}'.format(log_file),
               ' --exclude="lost+found"',
               '{}/Series/'.format(self.options.SymLinks), 
               '{}@{}:{}/'.format(self.options.user, self.options.HostName, self.options.SeriesRmt)]
        try:
            process = Popen(cmd, shell=False, stdin=None, stdout=None, stderr=None, cwd=os.path.join(self.options.SymLinks, 'Series'))
            process.wait()
        except CalledProcessError, exc:
            log.error("Command %s returned with RC=%d" % (cmd, exc.returncode))
            sys.exit(1)
    
    def SyncMovies(self):
        log_file = os.path.join(logger.LogDir, 'syncrmt_{}.log'.format(self.options.HostName))
        cmd = ['rsync', '-rptuvhogLR'.format(self.options.CmdLineDryRun), 
               '--progress {}'.format(self.options.CmdLineArgs), 
               '--partial-dir=.rsync-partial', 
               '--log-file={}'.format(log_file),
               ' --exclude="lost+found"',
               '{dir}/{user}/Movies/'.format(dir=self.options.SymLinks, user=self.options.user), 
               '{}@{}:{}/'.format(self.options.user, self.options.HostName, self.options.MoviesRmt)]
        try:
            process = Popen(cmd, shell=False, stdin=None, stdout=None, stderr=None, cwd=os.path.join(self.options.SymLinks, 'Movies'))
            process.wait()
        except CalledProcessError, exc:
            log.error("Command %s returned with RC=%d" % (cmd, exc.returncode))
            sys.exit(1)
    
    def SyncIncrementals(self, directory):
        
        printfmt = '%P\n'
        _downloaded_files = []
        _downloads_needed = []

        try:
            cursor.execute('SELECT FileName FROM Downloads  WHERE Name = "{}"'.format(self.options.user))
            for row in cursor:
                _downloaded_files.append(unicodedata.normalize('NFKD', row[0]).encode('ascii','ignore'))
        except:
            raise

        _available_files_temp = tempfile.NamedTemporaryFile()
        cmd = ['find', '-L','-type', 'f', '-printf', '{}'.format(printfmt)] 
        log.trace("Calling %s" % cmd)
        try:
            process = Popen(cmd, shell=False, stdin=None, stdout=_available_files_temp, stderr=_available_files_temp, cwd=directory)
            process.wait()
        except CalledProcessError, exc:
            log.error("Command %s returned with RC=%d" % (cmd, exc.returncode))

        _files_to_download_temp = tempfile.NamedTemporaryFile(mode='w')
        with open(_available_files_temp.name, "r") as _available_files_obj:
            for _line in _available_files_obj.readlines():
                episode = os.path.join(config.SeriesDir, _line.strip('\n'))
                if episode not in _downloaded_files:
                    _files_to_download_temp.write(_line)
                    _downloads_needed.append(episode)
            _available_files_obj.close()
        
        log_file = os.path.join(logger.LogDir, 'syncrmt_{}.log'.format(self.options.HostName))
        cmd = ['rsync', '-rptuvhogLR'.format(self.options.CmdLineDryRun), '--progress', '--partial-dir=.rsync-partial', 
               '--log-file={}'.format(log_file), 
               '--files-from={}'.format(_files_to_download_temp.name),
               './', 
               '{}@{}:{}/'.format(self.options.user, self.options.HostName, self.options.SeriesRmt)]
        try:
            process = Popen(cmd, shell=False, stdin=None, stdout=None, stderr=None, cwd=directory)
            process.wait()
        except CalledProcessError, exc:
            log.error("Command %s returned with RC=%d" % (cmd, exc.returncode))
            sys.exit(1)

        if not self.options.dryrun:
            for episode in _downloads_needed:
                self.record_download(episode)

        _incremental_files = '/tmp/{}_incrementals_list'.format(self.options.HostName)
        _incremental_file_obj = open(_incremental_files, 'w')
        cmd = ['find', '.', '-type', 'l', '-printf', printfmt]
        try:
            process = Popen(cmd, shell=False, stdin=None, stdout=_incremental_file_obj, stderr=None, cwd=directory)
            process.wait()
        except CalledProcessError, exc:
            log.error("Command %s returned with RC=%d" % (cmd, exc.returncode))
            sys.exit(1)

        self.options.CmdLineArgs = self.options.CmdLineArgs + ' --exclude-from="{}"'.format(_incremental_files) 
        return
    
    def _add_runtime_options(self):
        if self.options.user:
            self.options.SymLinks = os.path.join(config.SubscriptionDir, self.options.user)
            
            profile = config.GetSubscribers(req_profile=[self.options.user])
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
            self.options.CmdLineArgs = self.options.CmdLineArgs + ' --delete-before'

        if self.options.xclude:
            self.options.CmdLineArgs = self.options.CmdLineArgs + ' --exclude="*%s*"' % options.xclude
        
        return
    
    def record_download(self, file_name):
        try:
            file_details = self.fileparser.getFileDetails(file_name)
            cursor.execute('INSERT INTO Downloads(Name, SeriesName, Filename) VALUES ("{}", "{}", "{}")'.format(self.options.user, 
                                                                                                                file_details['SeriesName'], 
                                                                                                                file_name))
            db.commit()
        except  sqlite3.IntegrityError, e:
            pass
        except sqlite3.Error, e:
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
