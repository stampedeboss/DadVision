#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Purpose:
        Program to Sync Remote Hosts

'''
from daddyvision.common import logger
from daddyvision.common.exceptions import ConfigValueError, SQLError, UserAbort
from daddyvision.common.options import OptionParser, OptionGroup, SUPPRESS_HELP
from daddyvision.common.settings import Settings
from daddyvision.series.fileparser import FileParser
from subprocess import Popen, PIPE, STDOUT, CalledProcessError
import subprocess
import logging
import os
import sqlite3
import sys
import time
import psutil
import sqlite3
import tempfile


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
            rc = self.chkStatus(self.options.SymLinks)
            time.sleep(0.2)
            rc = self.chkStatus(self.options.SymLinks)

        if os.path.exists(os.path.join(self.options.SymLinks, 'Incrementals')):
            self.SyncIncrementals(os.path.join(self.options.SymLinks, 'Incrementals'))
        
        if not self.options.dryrun:
            cmd = 'xbmc-send --host=%s --action="XBMC.UpdateLibrary(video)"' % (req_host)
            log.info(cmd)
            os.system(cmd)

    def SyncSeries(self):
        cmd = 'sudo rsync -rptuvhogL%s --progress %s "--partial-dir=.rsync-partial" --log-file=/home/aj/log/syncrmt_%s.log --exclude="*hdtv/" --exclude="lost+found" %s %sSeries/ %s:%s' % (n, delete, req_host, exclude, symlinks, req_host, rmt_series)
        log.info(cmd)
        os.system(cmd)
        cmd = 'sudo rsync -rptuvhogL%s --progress %s "--partial-dir=.rsync-partial" --log-file=/home/aj/log/syncrmt_%s.log --exclude="lost+found" %s %s%s/ %s:%s' % (n, delete, req_host, exclude, symlinks, req_content, req_host, req_dir)
        log.info(cmd)
        os.system(cmd)
    
    def SyncMovies(self):
        cmd = 'sudo rsync -rptuvhogL%s --progress %s "--partial-dir=.rsync-partial" --log-file=/home/aj/log/syncrmt_%s.log --exclude="lost+found" %s %sMovies/ %s:%s' % (n, delete, req_host, exclude, symlinks, req_host, rmt_movies)
        log.info(cmd)
        os.system(cmd)
    
    def SyncIncrementals(self, directory):
        printfmt = '"%P\n"'
        _possible_files = []
        _temp = tempfile.NamedTemporaryFile()

        cmd = ['find', '-L','-type f', '-printf ()'.format(printfmt)] 
        log.trace("Calling %s" % cmd)
        try:
            process = Popen(cmd, shell=False, stdin=None, stdout=STDOUT, stderr=_temp, cwd=directory)
            process.wait()

            with open(_temp.name, "r") as _tf:
                for _line in _tf.readlines():
                    _possible_files = _possible_files.append(_line.strip('\n'))
            _temp.close()

                
            cursor.execute('SELECT d.FileName FROM Downloads d \
                            WHERE d.Name = "{}" \
                             and  d.FileName in {}'.format(self.options.user,
                                                           _possible_files)
                       )
            for row in cursor:
                print row
        except CalledProcessError, exc:
            log.error("Command %s returned with RC=%d" % (cmd, exc.returncode))
        
        
#        cmd = 'sudo rsync -rptuvhogLR%s --progress --partial-dir=.rsync-partial --log-file=/home/aj/log/syncrmt_%s.log --files-from=../filelist ./ %s:%s' % (n, req_host, req_host, rmt_series)
#        os.system(cmd)
#        cmd = 'find . -type l -printf %s > ../incrementallist' % (printfmt)
#        os.system(cmd)
#        exclude = '%s --exclude-from=../incrementallist' % exclude
    
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
    
        if self.options.dryrun:
            self.options.CmdLineArgs = self.options.CmdLineArgs + ' -n'
        
        if self.options.delete:
            self.options.CmdLineArgs = self.options.CmdLineArgs + ' --delete-before'

        if self.options.xclude:
            self.options.CmdLineArgs = self.options.CmdLineArgs + ' --exclude="*hdtv/" --exclude="*%s*"' % options.xclude
        
        return
    
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
        group.add_option("-s", "--series", dest="content",
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
