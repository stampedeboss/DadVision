#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Purpose:
        Program to Sync Remote Hosts

'''
import os
import re
import shutil
import socket
import sqlite3
import tempfile
import time
import unicodedata
from subprocess import check_call, CalledProcessError

import psutil
from common.exceptions import ConfigValueError
from library import Library
from library.MyTrakt.user import *
from pytvdbapi import api
from tqdm import tqdm

import logger
from movie import TMDBInfo

__pgmname__ = 'syncrmt'

__author__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"

__maintainer__ = __author__

__copyright__ = "Copyright 2011, AJ Reynolds"
__license__ = "GPL"

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
        sync1.add_argument("-p", "--pooh", dest="hostname",
            action="store_const", const="pooh",
            help="Sync Pooh for Michelle")
        sync1.add_argument("-l", "--pluto", dest="hostname",
            action="store_const", const="pluto",
            help="Sync Pluto for Ben and Mac")

        sync2 = self.options.parser.add_argument_group("Media Type", description=None)
        sync2.add_argument("-s", "--series", dest="content",
            action="append_const", const="Series",
            help="Process Series")
        sync2.add_argument("-m", "--movies", dest="content",
            action="append_const", const="Movies",
            help="Process Movies")

        sync3 = self.options.parser.add_argument_group("Modifiers", description=None)
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
        sync3.add_argument("--refresh", dest="refresh_limit",
            action="store", type=int, default=14400,
            help='Refresh existing links if older x seconds, Default: 14400 (4 hours)')
        sync3.add_argument("--no-reuse", dest="no_reuse",
            action="store_true", default=False,
            help='Do not reuse existing links, even if possible')
        sync3.add_argument("--reverse", dest="reverse",
            action="store_true", default=False,
            help="Reverse flow of Update, RMT --> Local, --ignore-existing, --rsync, --update implied")
        sync3.add_argument("--rsync", dest="rsync",
            action="store_true", default=False,
            help='Bypass database and run full download')
        sync3.add_argument("-u", "--update", dest="update",
            action="store_true", default=False,
            help="Skip files that are newer on the receiver")
        sync3.add_argument("-x", "--exclude", dest="xclude",
            action="append", default=[],
            help="Exclude files/directories")

        sync4 = self.options.parser.add_argument_group("syncRMT Already Running")
        sync4.add_argument("-c", "--cancel", dest="runaction",
            action="store_const", const='cancel', default='ask',
            help="Cancel this request and let existing run")
        sync4.add_argument("-r", "--restart", dest="runaction",
            action="store_const", const='restart',
            help="Stop existing and Restart with this request")

        self.db = api.TVDB("959D8E76B796A1FB")

        self.tmdb_info = TMDBInfo()
        self._printfmt = '%P\n'
        return

    @use_library_logging
    def sync(self, dir_name=''):

        self.dir_name = dir_name.rstrip(os.sep)
        self._update_args()

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
                self._syncList(_sync_needed, self._series_src, self._series_tgt)

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
            cmd.append(self._series_tgt)
            log.verbose(' '.join(cmd))
            check_call(cmd, shell=False, stdin=None, stdout=None, stderr=None, cwd=self._series_wd)
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
        cmd.append('{}'.format(self._movies_src))
        cmd.append('{}'.format(self._movies_tgt))
        log.verbose(' '.join(cmd))

        try:
            check_call(cmd, shell=False, stdin=None, stdout=None, stderr=None, cwd=self._movies_wd)
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

    def _already_running(self):
        time.sleep(0.2)
        pidList = psutil.process_iter()
        _directory_in_use = False
        for p in pidList:
            cmdline = p.cmdline()
            if len(cmdline) > 0:
                if p.name() == 'rsync':
                    _rsync_target = cmdline[-1]
                    _rsync_target = _rsync_target.split(':')
                    if len(_rsync_target) < 2:
                        continue
                    _rsync_hostname = cmdline[-1].split(':')[0].split('@')[1]
                    if _rsync_hostname == self.args.hostname:
                        _directory_in_use = True
                        if not self.args.dryrun:
                            if p.terminal():
                                log.info('syncrmt running in terminal window, unable to cancel')
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
                                _directory_in_use = False
        return _directory_in_use

    def _update_args(self):
        """
        :type self: object
        """
        if not self.args.hostname:
            self.options.parser.error('Missing Hostname Command Line Parameter')
            sys.exit(1)

        profiles = self.settings.GetHostConfig(requested_host=[socket.gethostname(), self.args.hostname])
        if self.args.reverse:
            self.args.rsync = True
            self.args.update = True
            self.args.ignore_existing = True

            host_src = self.args.hostname
            host_tgt = socket.gethostname()

            self._series_src = '{}@{}:{}/'.format(profiles[host_src]['UserId'],
                                                  host_src,
                                                  profiles[host_src]['SeriesDir'])
            self._movies_src = '{}@{}:{}/'.format(profiles[host_src]['UserId'],
                                                  host_src,
                                                  profiles[host_src]['MovieDir'])
            self._series_tgt = profiles[host_tgt]['SeriesDir']
            self._movies_tgt = profiles[host_tgt]['MovieDir']
            self._series_wd = profiles[host_tgt]['SeriesDir']
            self._movies_wd = profiles[host_tgt]['MovieDir']
        else:
            host_src = socket.gethostname()
            host_tgt = self.args.hostname

            self.args.TraktUserID = profiles[host_tgt]['TraktUserID']
            self.args.TraktAuthorization = profiles[host_tgt]['TraktAuthorization']

            if not self.args.TraktUserID:
                msg = 'Missing: MyTrakt.tv account and the userid/authorization entered in the config file'
                log.error(msg)
                raise ConfigValueError(msg)

            if not self._already_running():
                if self._checkTempDir(host_tgt, False):
                    _library_list = []
                    log.info('Rebuilding Series List')
                    _library_list = self._build_list('shows')
                    self._build_symbolics(_library_list, area='Series')
                    log.info('Rebuilding Movies List')
                    _library_list = self._build_list('movies')
                    self._build_symbolics(_library_list, area='Movies')
            else:
                self._checkTempDir(host_tgt, True)

            self._series_src = '{}/{}'.format(os.path.join(self._temp_dir,
                                                           'Series'),
                                              self.dir_name)
            self._movies_src = '{}/{}'.format(os.path.join(self._temp_dir,
                                                           'Movies'),
                                              self.dir_name)
            self._series_tgt = '{}@{}:{}/'.format(profiles[host_tgt]['UserId'],
                                                  host_tgt,
                                                  profiles[host_tgt]['SeriesDir'])
            self._movies_tgt = '{}@{}:{}/'.format(profiles[host_tgt]['UserId'],
                                                  host_tgt,
                                                  profiles[host_tgt]['MovieDir'])
            self._series_wd = self._series_src
            self._movies_wd = self._movies_src

        if self.args.content is None:
            self.args.content = ["Series", "Movies"]

        if self.args.dryrun:
            self.args.CmdLineDryRun = 'n'
        else:
            self.args.CmdLineDryRun = ''

        self.args.CmdLineArgs = ['-i']

        if self.args.update:
            self.args.CmdLineArgs.append('-u')

        if self.args.ignore_existing:
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

    def _checkTempDir(self, host_tgt, dryrun=False):

        _syncrmt_dir = re.compile('^syncrmt_{}.*$'.format(self.args.hostname), re.IGNORECASE)

        _dir_list = {}
        for pathname in filter(_syncrmt_dir.match, os.listdir(tempfile.gettempdir())):
            st = os.stat(os.path.join(tempfile.gettempdir(), pathname))
            _age = (time.time() - st.st_mtime)

            if dryrun and not self.args.no_reuse:
                _dir_list[pathname] = _age
                continue

            if _age > self.args.refresh_limit or self.args.no_reuse:
                shutil.rmtree(os.path.join(tempfile.gettempdir(), pathname))
                continue

            if len(os.listdir(os.path.join(tempfile.gettempdir(), pathname, 'Movies'))) == 0:
                shutil.rmtree(os.path.join(tempfile.gettempdir(), pathname))
                continue
            if len(os.listdir(os.path.join(tempfile.gettempdir(), pathname, 'Series'))) == 0:
                shutil.rmtree(os.path.join(tempfile.gettempdir(), pathname))
                continue

            _dir_list[pathname] = _age

        if _dir_list:
            _last_dir = min(_dir_list, key=lambda k: _dir_list[k])
            self._temp_dir = os.path.join(tempfile.gettempdir(), _last_dir)
            del _dir_list[_last_dir]
            if _dir_list:
                for pathname, age in _dir_list.iteritems():
                    shutil.rmtree(os.path.join(tempfile.gettempdir(), pathname))
            return False

        self._temp_dir = tempfile.mkdtemp(suffix='', prefix='syncrmt_'+host_tgt+'_', dir=None)
        os.makedirs(os.path.join(self._temp_dir, 'Series'))
        os.chmod(os.path.join(self._temp_dir, 'Series'), 0775)
        os.makedirs(os.path.join(self._temp_dir, 'Movies'))
        os.chmod(os.path.join(self._temp_dir, 'Movies'), 0775)
        os.makedirs(os.path.join(self._temp_dir, 'Invalid'))
        os.chmod(os.path.join(self._temp_dir, 'Invalid'), 0775)

        return True

    def _build_list(self, entrytype):

        trakt_list = getCollection(self.args.TraktUserID, self.args.TraktAuthorization, entrytype, rtn=list)
        if type(trakt_list) == HTTPError:
            log.error('Collection: Invalid Return Code - {}'.format(trakt_list))
            sys.exit(99)

        trakt_watchlist = getWatchList(self.args.TraktUserID, self.args.TraktAuthorization, entrytype, rtn=list)
        if type(trakt_watchlist) == HTTPError:
            log.error('WatchList: Invalid Return Code - {}'.format(trakt_watchlist))
        else:
            trakt_list = trakt_list + trakt_watchlist

        _library_list = []
        _warn_msgs = []
        _error_msgs = []

        if trakt_list:
            for _entry in tqdm(trakt_list, leave=True):
                if entrytype == 'shows':
                    if os.path.exists(os.path.join(self.settings.SeriesDir, _entry.title)):
                        _title = _entry.title
                    else:
                        _show = self.db.get_series(_entry.tvdb_id, 'en')
                        _title = self.decode(_show.SeriesName)
                        if not os.path.exists('{}'.format(os.path.join(self.settings.SeriesDir, _title))):
                            _warn_msgs.append('Series Not Available: MyTrakt - {}  tvdb - {}'.format(_entry.title, _title))
                            continue
                else:
                    _title = "{} ({})".format(self.decode(_entry.title),_entry.year)

                if _title in _library_list:
                    _rc = removeFromWatchlist(self.args.TraktUserID, self.args.TraktAuthorization, entries=[_entry])
                    if type(_rc) == HTTPError:
                        _error_msgs.append('Collection: Invalid Return Code - {}'.format(trakt_list))
                    else:
                        _warn_msgs.append('Remove from Watchlist: {} - {}  Not Found: {}'.format(_title,
                                                                                        _rc['deleted']['shows'],
                                                                                        _rc['not_found']['shows']))
                    continue
                _library_list.append(_title)

        print('')
        for _msgs in _warn_msgs:
            log.warning(_msgs)
        for _msgs in _error_msgs:
            log.error(_msgs)


        return _library_list

    def _build_symbolics(self, _symbolics_requested, area=None):

        if area == "Series":
            _target_dir = self.settings.SeriesDir
            _temp_dir = os.path.join(self._temp_dir, 'Series')
        elif area == "Movies":
            _target_dir = self.settings.MoviesDir
            _temp_dir = os.path.join(self._temp_dir, 'Movies')
        else:
            log.error('Invalid Parameter Passed to _build_symbolics')
            sys.exit(99)

        for _entry in tqdm(_symbolics_requested, desc='Build Links', leave=True):
            cmd = [ 'ln', '-s',
                    '{}'.format(os.path.join(_target_dir, _entry)),
                    '{}'.format(_entry)
                    ]
            run_command(cmd, cwd=_temp_dir)

        # Remove any broken links
        try:
            cmd = 'find -L {} -type l -exec mv {} ../Invalid/ \;'.format(_temp_dir, "'{}'")
            log.verbose('{}'.format(cmd))
            run_command(cmd, True, _temp_dir)
        except:
            pass
        return


def run_command(cmd, Shell=False, cwd=None):
    try:
        log.verbose('{}'.format(cmd))
        check_call(cmd, shell=Shell, stdin=None, stdout=None, stderr=None, cwd=cwd)
        return
    except CalledProcessError, exc:
        if exc.returncode == 255 or exc.returncode == -9:
            sys.exit(1)
        else:
            pass
#			log.error("Command %s returned with RC=%d" % (cmd, exc.returncode))
    return True


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
