#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Author: AJ Reynolds
Date: 01-24-2011
Purpose:
        Program to Sync Remote Hosts

"""

import os
import re
import sys
import time
import psutil
import logging
import datetime
import subprocess
import logging.handlers
import sqlite3

from configobj import ConfigObj
from seriesExceptions import ConfigValueError
from optparse import OptionParser, OptionGroup

__version__ = '$Rev$'
__pgmname__ = 'syncrmt'
# $Source$

PgmDir      = os.path.dirname(__file__)
HomeDir     = os.path.expanduser('~')
ConfigDirB  = os.path.join(HomeDir, '.config')
ConfigDir   = os.path.join(ConfigDirB, 'xbmcsupt')
LogDir      = os.path.join(HomeDir, 'log')

db = sqlite3.connect(os.path.join(HomeDir, 'DownloadMonitor.db3'))
cursor = db.cursor()
'''
try:
    # SQL #
    cursor.execute('SELECT f.FileName, patient_id, p.patient_initials, p.patient_diagnosis, p.patient_allergies FROM patient p')
    if cursor.rowcount != 1:
        raise PatientNotFound ('Patient: %s Not Found' % patient_id)
    for row in cursor:
        self.patient_list.append(fetchoneDict(cursor))
    cursor.execute('INSERT INTO patient(patient_initials, patient_diagnosis, patient_allergies) \
             VALUES (%s, %s, %s)' % (sym,sym,sym), (patient_initials, patient_diagnosis, patient_allergies))
    patient_id = int(cursor.lastrowid)
#    if cursor.warning_count() > 0:
#    raise PatientSaveError("Insert - %s %s" % (db.info(), cursor.messages))
    db.commit()

except  sqlite3.Error, e:
    log.error("METHOD: Patient - List")
    raise PatientListError (e)
return self.patient_list
'''

if not os.path.exists(LogDir):
    try:
        os.makedirs(LogDir)
    except:
        raise ConfigValueError("Cannot Create Log Directory: %s" % LogDir)

# Set up a specific logger with our desired output level
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
ml = logging.handlers.TimedRotatingFileHandler(os.path.join(LogDir, '%s.log' % __pgmname__), when='midnight', backupCount=7)
dl = logging.handlers.TimedRotatingFileHandler(os.path.join(LogDir, '%s_debug.log' % __pgmname__), when='midnight', backupCount=7)
ch = logging.StreamHandler()
ml.setLevel(logging.INFO)
dl.setLevel(logging.DEBUG)
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s - %(message)s")
ml.setFormatter(formatter)
dl.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(ml)
logger.addHandler(dl)
logger.addHandler(ch)

class chkStatus(object):
    def __init__(self, directory, recurse=False):
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
                            logger.warn('rmtsync for : %s is Already Running, Request Canceled' % directory)
                            sys.exit(1)
                        else:
                            os.system('sudo kill -kill %s' % p.pid)
                            logger.warn('Previous Session Killed: %s' % p.pid)
                            options.runaction = 'restart'
                            time.sleep(0.1)
                            chkStatus(directory)
        return

class GetConfig(object):
    def __init__(self, update_existing=False, pgmname=__pgmname__):

        self.cfgfile = os.path.expanduser(os.path.join(ConfigDir, '%s.cfg' % pgmname))
        if update_existing or not os.path.exists(self.cfgfile):
            self.BuildConfig()

        config = ConfigObj(self.cfgfile, unrepr=True, interpolation=False)

        Defaults     = config['Defaults']
        self.movies_dir     = Defaults['movies_dir']
        self.series_dir     = Defaults['series_dir']

        self.aly_host    = Defaults['aly_host']
        self.aly_symlinks    = os.path.expanduser(Defaults['aly_symlinks'])
        self.aly_rmt_movies    = os.path.expanduser(Defaults['aly_rmt_movies'])
        self.aly_rmt_series    = os.path.expanduser(Defaults['aly_rmt_series'])

        self.kim_host    = Defaults['kim_host']
        self.kim_symlinks    = os.path.expanduser(Defaults['kim_symlinks'])
        self.kim_rmt_movies    = os.path.expanduser(Defaults['kim_rmt_movies'])
        self.kim_rmt_series    = os.path.expanduser(Defaults['kim_rmt_series'])

        self.ben_host    = Defaults['ben_host']
        self.ben_symlinks    = os.path.expanduser(Defaults['ben_symlinks'])
        self.ben_rmt_movies    = os.path.expanduser(Defaults['ben_rmt_movies'])
        self.ben_rmt_series    = os.path.expanduser(Defaults['ben_rmt_series'])

        if not os.path.exists(self.movies_dir):
            logger.error("Path Not Found: %s" % self.movies_dir)
            logger.error("Invalid Config Entries, Ending")
            raise ConfigValueError("Path Not Found: %s" % self.movies_dir)

        if not os.path.exists(self.series_dir):
            logger.error("Path Not Found: %s" % self.series_dir)
            logger.error("Invalid Config Entries, Ending")
            raise ConfigValueError("Path Not Found: %s" % self.series_dir)
        return

    def BuildConfig(self):
        if not os.path.exists(ConfigDir):
            try:
                os.makedirs(ConfigDir)
            except:
                logger.error("Cannot Create Config Directory: %s" % ConfigDir)
                raise ConfigValueError("Cannot Create Config Directory: %s" % ConfigDir)

        config = ConfigObj(unrepr = True, interpolation = False)
        config.filename = self.cfgfile
        config['Defaults'] = {}
        config['Defaults']['movies_dir']        = self.get_dir('/mnt/Movies', 'Movies')
        config['Defaults']['series_dir']        = self.get_dir('/mnt/TV/Series', 'Series')

        config['Defaults']['aly_host']          = self.get_value("Enter Tigger's IP Address", '192.168.9.21')
        config['Defaults']['aly_symlinks']      = self.get_dir('/mnt/Links/aly/', 'Aly\'s Symlinks')
        config['Defaults']['aly_rmt_movies']    = self.get_value("Enter %s Directory: " % 'Aly\'s Remote Movies', '/mnt/Movies/')
        config['Defaults']['aly_rmt_series']    = self.get_value("Enter %s Directory" % 'Aly\'s Remote Series', '/mnt/Series/')

        config['Defaults']['kim_host']          = self.get_value("Enter Goofy's IP Address", '192.168.9.20')
        config['Defaults']['kim_symlinks']      = self.get_dir('/mnt/Links/kim/', 'Kim\'s Symlinks')
        config['Defaults']['kim_rmt_movies']    = self.get_value("Enter %s Directory: " % 'Kim\'s Remote Movies', '/mnt/Movies/')
        config['Defaults']['kim_rmt_series']    = self.get_value("Enter %s Directory" % 'Kim\'s Remote Series', '/mnt/Series/')

        config['Defaults']['ben_host']          = self.get_value("Enter Pluto's IP Address", '')
        config['Defaults']['ben_symlinks']      = self.get_dir('/mnt/Links/ben/', 'Ben\'s Symlinks')
        config['Defaults']['ben_rmt_movies']    = self.get_value("Enter %s Directory: " % 'Ben\'s Remote Movies', '/mnt/Videos/Movies/')
        config['Defaults']['ben_rmt_series']    = self.get_value("Enter %s Directory" % 'Ben\'s Remote Series', '/mnt/Videos/Series/')
        # GETNEW Options
        config['Defaults']['glade_file']        = self.get_value("Enter Glade File Name", '%s.glade' % __pgmname__)
        config['Defaults']['media_ext']         = ['avi', 'mkv', 'mp4', 'mpeg']
        config['Defaults']['predicates']        = ['The', 'A', 'An']

        config.write()

    def get_dir(self, dir_name_d, message):
        while True:
            dir_name = raw_input("Enter %s Directory (%s): " % (message, dir_name_d)).rstrip(os.sep)
            if not dir_name:
                dir_name = dir_name_d
            if os.path.exists(dir_name):
                return dir_name

            while not os.path.exists(os.path.expanduser(dir_name)):
                action = raw_input("%s Directory: %s - Not Found,  Ignore/Re-Enter/Create/Abort? (I/R/C/A): " % (message, dir_name)).lower()[0]
                if len(action) < 1:
                    continue
                elif action[0] == 'a':
                    sys.exit(1)
                elif action[0] == 'i':
                    return dir_name
                elif action[0] == 'c':
                    try:
                        os.makedirs(dir_name)
                    except OSError, exc:
                        print "ERROR - Unable to Create Config Directory: %s, %s: " % (dir_name, exc)
                        continue
                elif action[0] == 'r':
                    dir_name = self.get_dir(dir_name_d, message)
                return dir_name

    def get_value(self, message, default):
        while True:
            value = raw_input("%s (%s): " % (message, default))
            if not value:
                value = default
            return value

if __name__ == '__main__':

    parser = OptionParser(
        "%prog [options]",
        version="%prog " + __version__)

    group = OptionGroup(parser, "Users")
    group.add_option("-a", "--aly", dest="aly",
        action="store_true", default=False,
        help="Sync Tigger for Aly")
    group.add_option("-k", "--kim", dest="kim",
        action="store_true", default=False,
        help="Sync Goofy for Kim")
    group.add_option("-p", "--peterson", dest="ben",
        action="store_true", default=False,
        help="Sync Tigger for Ben and Mac")
    parser.add_option_group(group)

    group = OptionGroup(parser, "Media Type")
    group.add_option("-s", "--series", dest="series",
        action="store_true", default=False,
        help="process TV Series")
    group.add_option("-m", "--movies", dest="movies",
        action="store_true", default=False,
        help="process Movies")
    group.add_option("-b", "--both", dest="both",
        action="store_true", default=False,
        help="process both TV Series and Movies")
    parser.add_option_group(group)

    group = OptionGroup(parser, "Modifers")
    group.add_option("-n", "--dry-run", dest="dryrun",
        action="store_true", default=False,
        help="Don't Run Link Create Commands")
    group.add_option("--delete", dest="delete",
        action="store_true", default=False,
        help="Delete any files on rmt that do not exist on local")
    group.add_option("-x", "--exclude", dest="xclude",
        action="store", type="string", default="",
        help="Exclude files/directories")
    group.add_option("-t", "--timeframe", dest="timeframe",
        action="store", type="string", default="-3",
        help="Number of Days back for Incrementals")
    parser.add_option_group(group)

    group = OptionGroup(parser, "Status Check")
    group.add_option("-c", "--cancel", dest="runaction",
        action="store_const", const='cancel', default='ask',
        help="Cancel this request and let existing run")
    group.add_option("-r", "--restart", dest="runaction",
        action="store_const", const='restart',
        help="Stop existing and Restart with this request")
    parser.add_option_group(group)

    group = OptionGroup(parser, "Logging Levels")
    group.add_option("-e", "--errors", dest="error",
        action="store_true", default=False,
        help="omit all but error logging")
    group.add_option("-q", "--quiet", dest="quiet",
        action="store_true", default=False,
        help="omit informational logging")
    group.add_option("-v", "--verbose", dest="verbose",
        action="store_true", default=False,
        help="increase informational logging")
    group.add_option("-d", "--debug", dest="debug",
        action="store_true", default=False,
        help="increase informational logging to include debug")
    parser.add_option_group(group)

    options, args = parser.parse_args()

    opt_sel = 0
    if options.debug:
        logger.setLevel(logging.DEBUG)
        ml.setLevel(logging.DEBUG)
        ch.setLevel(logging.DEBUG)
        opt_sel = opt_sel + 1
    if options.error:
        logger.setLevel(logging.ERROR)
        ml.setLevel(logging.ERROR)
        ch.setLevel(logging.ERROR)
        opt_sel = opt_sel + 1
    if options.quiet:
        logger.setLevel(logging.WARNING)
        ml.setLevel(logging.WARNING)
        ch.setLevel(logging.WARNING)
        opt_sel = opt_sel + 1
    if options.verbose:
        logger.setLevel(logging.DEBUG)
        ml.setLevel(logging.DEBUG)
        ch.setLevel(logging.DEBUG)
        opt_sel = opt_sel + 1

    logger.debug("Parsed command line options: %r" % options)
    logger.debug("Parsed arguments: %r" % args)

    if opt_sel > 1:
        logger.error('Conflicting options selected, Reconsider Parameters.')
        sys.exit(1)

    parms = GetConfig()

    logger.debug('Options: %s' % options)

    symlinks   = ''
    rmt_movies = ''
    rmt_series = ''

    req_content= ''
    req_dir    = ''
    req_host   = ''
    req_user   = ''

    if options.xclude == '':
        exclude       = '--exclude="*hdtv/"'
    else:
        exclude       = '--exclude="*hdtv/" --exclude="*%s*"' % options.xclude

    if options.dryrun:
        n = 'n'
    else:
        n = ''

    if options.delete:
        delete = '--delete-before'
    else:
        delete = ''

    if options.aly:
        symlinks=parms.aly_symlinks
        rmt_movies=parms.aly_rmt_movies
        rmt_series=parms.aly_rmt_series
        req_host=parms.aly_host
    elif options.kim:
        symlinks=parms.kim_symlinks
        rmt_movies=parms.kim_rmt_movies
        rmt_series=parms.kim_rmt_series
        req_host=parms.kim_host
    elif options.ben:
        symlinks=parms.ben_symlinks
        rmt_movies=parms.ben_rmt_movies
        rmt_series=parms.ben_rmt_series
        req_host=parms.ben_host
    else:
        n = 'n'
        options.dryrun = True
        symlinks=parms.aly_symlinks
        rmt_movies=parms.aly_rmt_movies
        rmt_series=parms.aly_rmt_series
        req_host=parms.aly_host

    if options.series:
        req_content='Series'
        req_dir=rmt_series
    elif options.movies:
        req_content='Movies'
        req_dir=rmt_movies
        exclude = ''
    else:
        req_content='Series'
        req_dir=rmt_series

    if  n == '':
        rc = chkStatus(symlinks)
        time.sleep(0.2)
        rc = chkStatus(symlinks)

    printfmt = '"%P\n"'

    if os.path.exists(os.path.join(symlinks, 'Incrementals')):
        os.chdir(os.path.join(symlinks, 'Incrementals'))
        cmd = 'find -L . -type f -mtime %s -printf %s > ../filelist' % (options.timeframe, printfmt)
        os.system(cmd)
        cmd = 'sudo rsync -rptuvhogLR%s --progress --partial-dir=.rsync-partial --log-file=/home/aj/log/syncrmt_%s.log --files-from=../filelist ./ %s:%s' % (n, req_host, req_host, rmt_series)
        os.system(cmd)
        cmd = 'find . -type l -printf %s > ../incrementallist' % (printfmt)
        os.system(cmd)
        exclude = '%s --exclude-from=../incrementallist' % exclude

    if options.both:
        cmd = 'sudo rsync -rptuvhogL%s --progress %s "--partial-dir=.rsync-partial" --log-file=/home/aj/log/syncrmt_%s.log --exclude="*hdtv/" --exclude="lost+found" %s %sSeries/ %s:%s' % (n, delete, req_host, exclude, symlinks, req_host, rmt_series)
        logger.info(cmd)
        os.system(cmd)
        cmd = 'sudo rsync -rptuvhogL%s --progress %s "--partial-dir=.rsync-partial" --log-file=/home/aj/log/syncrmt_%s.log --exclude="lost+found" %s %sMovies/ %s:%s' % (n, delete, req_host, exclude, symlinks, req_host, rmt_movies)
        logger.info(cmd)
        os.system(cmd)
    else:
        cmd = 'sudo rsync -rptuvhogL%s --progress %s "--partial-dir=.rsync-partial" --log-file=/home/aj/log/syncrmt_%s.log --exclude="lost+found" %s %s%s/ %s:%s' % (n, delete, req_host, exclude, symlinks, req_content, req_host, req_dir)
        logger.info(cmd)
        os.system(cmd)

    if not options.dryrun:
        cmd = 'xbmc-send --host=%s --action="XBMC.UpdateLibrary(video)"' % (req_host)
        logger.info(cmd)
        os.system(cmd)
