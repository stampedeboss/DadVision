#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Purpose:
   Program to perform various tasks (check for missing episodes, locate duplication files, etc).
   Assist with maintaining a Library of TV Series and Episode files.

"""
from __future__ import division
from daddyvision.common import logger
from daddyvision.common.exceptions import (RegxSelectionError, 
    InvalidArgumentType, InvalidPath, InvalidFilename, ConfigNotFound, 
    ConfigValueError, DictKeyError, DataRetrievalError, SeriesNotFound, 
    SeasonNotFound, EpisodeNotFound)
from daddyvision.common.options import OptionParser, OptionGroup
from daddyvision.common.settings import Settings
from daddyvision.common.countfiles import countFiles
from daddyvision.series.episodeinfo import EpisodeDetails
from daddyvision.series.fileparser import FileParser
from datetime import datetime, date, timedelta
from logging import INFO, WARNING, ERROR, DEBUG
import filecmp
import fnmatch
import gtk
import logging
import os
import re
import sys
import time
import unicodedata
#import gtk.glade

__author__ = "AJ Reynolds"
__copyright__ = "Copyright 2011, AJ Reynolds"
__credits__ = []
__license__ = "GPL"

__pgmname__ = 'series'
__version__ = '$Rev$'

__maintainer__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"
__status__ = "Development"

log = logging.getLogger(__pgmname__)

class MainWindow():

    def __init__(self, config, options):
        log.trace('MainWindow - __init__')

        _pgm_dir = os.path.dirname(__file__)
        builder = gtk.Builder()
        builder.add_from_file(os.path.join(_pgm_dir, '%s.glade' % (__pgmname__)))
        events = { "on_main_window_destroy" : self.quit,
                   "on_bt_close_clicked" : self.quit,
                   "on_fc_dir_file_set" : self.on_fc_dir_file_set,
                   "on_bt_ok_clicked" : self.bt_ok_clicked
                  }
        builder.connect_signals(events)

        self.wMain = builder.get_object("main_window")
        self.fc_dir = builder.get_object("fc_dir")
        self.bt_execute = builder.get_object("bt_execute")
        self.bt_quit = builder.get_object("bt_quit")

        #Initialize Log TextView
        self.txtview_log=builder.get_object("txtview_log")
        self.txtbuf_log=builder.get_object('txtbuf_log')

        #Initialize our Treeview
        self.tview_series=builder.get_object("tview_series")
        self.tview_series_model=builder.get_object("tstore_series")
        self.tselection_series = self.tview_series.get_selection()
        self.tselection_series.set_mode(gtk.SELECTION_MULTIPLE)
        mode = self.tselection_series.get_mode()
        self.tview_series.set_hover_expand(False)

        self.library = SeriesLibrary(self, config, options)
        self.requested_dir = options.requested_dir
        self.fc_dir.set_current_folder(self.requested_dir)
        
        self.wMain.show()
        gtk.main()
        return

    def insert_row(self, parent, series, issue=' ', season=' ', episode=' ', title=' ', air_date=' '):
        log.trace('insert_row: Series: {} Status: {} '.format(series, issue))
        myiter=self.tview_series_model.append(parent, None)
        self.tview_series_model.set_value(myiter, 0, series)
        self.tview_series_model.set_value(myiter, 1, issue)
        self.tview_series_model.set_value(myiter, 2, season)
        self.tview_series_model.set_value(myiter, 3, episode)
        self.tview_series_model.set_value(myiter, 4, title)
        self.tview_series_model.set_value(myiter, 5, air_date)
        self.tview_series.expand_all()
        path = self.tview_series_model.get_path(myiter)
        self.tview_series.scroll_to_cell(path)
        while gtk.events_pending():
            gtk.main_iteration_do(False)
        return myiter

    def on_fc_dir_file_set(self, obj):
        self.requested_dir = self.fc_dir.get_current_folder()
        return
        
    def quit(self,obj):
        log.trace('quit: ending')
        gtk.main_quit()

    def bt_ok_clicked(self, obj):
        log.trace('bt_ok_clicked: obj: {}'.format(obj))
        self.bt_execute.set_sensitive(False)
#        self.bt_quit.set_sensitive(False)
        while gtk.events_pending():
            gtk.main_iteration_do(False)
        self.library.check(self.requested_dir)

    def write_log_entry(self, msg, level=INFO, enter="\n"):
        log.trace('write_log_entry: Level: {}  Message: {}'.format(level, msg))
        message = msg + enter
        buffer = self.txtbuf_log
        iter = buffer.get_end_iter()
        if level == WARNING:
            log.warn(msg)
            tag = buffer.create_tag()
            tag.set_property("foreground", 'red')
            self.txtbuf_log.insert_with_tags(buffer.get_end_iter(), message, tag)
        elif level == ERROR:
            log.error(msg)
            tag = buffer.create_tag()
            tag.set_property("foreground", 'red')
            self.txtbuf_log.insert_with_tags(buffer.get_end_iter(), message, tag)
        else:
            log.info(msg)
            self.txtbuf_log.insert(iter, message)
            mark = buffer.create_mark("end", buffer.get_end_iter(), False)
            self.txtview_log.scroll_to_mark(mark, 0.05, True, 0.0,1.0)
        while gtk.events_pending():
            gtk.main_iteration_do(False)
        return


class SeriesLibrary(object):

    def __init__(self, mw, config, options):
        log.trace('SeriesLibrary - __init__')

        self.config = config
        self.options = options
        self.mw = mw
        self.episodeinfo = EpisodeDetails()
        self.fileparser = FileParser()

    def check(self, pathname):
        log.trace('check: Pathname Requested: {}'.format(pathname))

        _series_details = []
        _episode_list = []
        _last_file = None
        _last_fq_name = None
        _last_series = ' '
        _last_season = None
        _last_ep_no = None
        _last_ext = None
        _files_checked = 0
        _last_dups = ' '
        
        _total_files = countFiles(pathname, exclude=config.ExcludeList, types=config.MediaExt)
        
        self.mw.write_log_entry("==== Begin Scan: {} ====".format(pathname), INFO)

        for _root, _dirs, _files in os.walk(os.path.abspath(pathname),followlinks=True):
            if _dirs != None:
                _dirs.sort()
                for _dir in _dirs:
                    if self.ignored(_dir):
                        _dirs.remove(_dir)
                        log.trace('Removing Dir: %s' % _dir)
                _files.sort()
                for _file in _files:
                    if os.path.splitext(_file)[1][1:] in self.config.MediaExt:
                        _files_checked += 1
                        _fq_name = os.path.join(_root, _file)
                        try:
                            FileDetails = self.fileparser.getFileDetails(_fq_name)
                        except (InvalidFilename, RegxSelectionError, SeasonNotFound), msg:
                            self.mw.write_log_entry('Skipping - Unable to Parse: {}'.format(msg), ERROR)
                            continue
                    else:
                        continue

                    if FileDetails['SeriesName'] != _last_series:
                        message = 'Files Checked: %2.2f%% - %-5s of %5s   Current Series: %s' % ((_files_checked-1)/_total_files, (_files_checked-1), _total_files, _last_series)
                        self.mw.write_log_entry(message)
                        if _series_details:
                            self.checkMissing(_episode_list, _series_details)
                        _series_details = self.getSeries(FileDetails['SeriesName'])
                        _episode_list = []
#                    elif FileDetails['SeasonNum'] == _last_season and FileDetails['EpisodeNums'] == _last_ep_no:
#                        log.trace('Possible Dups: %s - %s' % (_last_file, _file))
#                        _last_dups = self.handle_dup(None, _last_dups, _series_details, FileDetails, _last_ext, _fq_name, _last_fq_name, _file, _last_file)

                    _episode_list.append(FileDetails)
                    _last_file = _file
                    _last_fq_name = _fq_name
                    _last_series = FileDetails['SeriesName']
                    _last_season = FileDetails['SeasonNum']
                    _last_ep_no = FileDetails['EpisodeNums']
                    _last_ext = FileDetails['Ext']

        message = 'Files Checked: %2.2f%%   %05d of %5d   Current Series: %s' % ((_files_checked)/_total_files, (_files_checked), _total_files, _last_series)
        self.mw.write_log_entry(message)
        self.checkMissing(_episode_list, _series_details)
        self.mw.tview_series.collapse_all()
        self.mw.tview_series.scroll_to_point(0,0)
        while gtk.events_pending():
            gtk.main_iteration_do(False)

    def processDups(self, dups):
        pass

    def getSeries(self, seriesname):
        log.trace('getSeries: Series Name: %s' % (seriesname))
        try:
            _series_details = {'SeriesName': seriesname}
            _series_details = self.episodeinfo.getDetails(_series_details)
        except (SeriesNotFound, InvalidArgumentType, InvalidPath, InvalidFilename,
            ConfigNotFound, ConfigValueError, DataRetrievalError) as errormsg:
            log.warn(errormsg)
            log.error("Skipping series: %s" % (seriesname))
            return None
        return _series_details

    def checkMissing(self, episode_list, series_details):
        log.debug('checkMissing - episode_list: {} series_details: {}'.format(episode_list, series_details))

        missing = []
        date_boundry = date.today() - timedelta(days=self.options.age_limit)

        for series_entry in series_details['EpisodeData']:
            found_series = False
            if series_entry['SeasonNum'] == 0:
                continue
#            year, month, day = time.strptime(series_entry['DateAired'], "%Y-%m-%d %H:%M:%S")[:3]
            if series_entry['DateAired']:
                if series_entry['DateAired'].date() < date_boundry or series_entry['DateAired'].date() > datetime.today().date():
                    continue
            else:
                continue
            try:
                for episode_entry in episode_list:
                    if series_entry['SeasonNum'] == episode_entry['SeasonNum'] and series_entry['EpisodeNum'][0] in episode_entry['EpisodeNums']:
                        found_series = True
                        if len(episode_entry['EpisodeNums']) > 1:
                            episode_entry['EpisodeNums'].remove(series_entry['EpisodeNum'][0])
                        else:
                            episode_list.remove(episode_entry)
                        raise GetOutOfLoop
            except GetOutOfLoop:
                continue
            if not found_series:
                missing.append(series_entry)

        if len(missing) > 0:
            message = "Missing %i episode(s) - SERIES: %-25.25s" % (len(missing), series_details['SeriesName'])
            self.mw.write_log_entry(message, WARNING)
            missing_series = self.mw.insert_row(None, series_details['SeriesName'])
            
        last_season = ''
        for _entry in missing:
            _season_num = "S%2.2d" % int(_entry['SeasonNum'])
            _ep_no = "E%2.2d" % int(_entry['EpisodeNum'][0])
            if _entry['DateAired']:
                _date_aired = _entry['DateAired'].date()
            else:
                _date_aired = "Unknown"  
            if len(missing) > 5:
                if last_season != _entry['SeasonNum']:
                    missing_season = self.mw.insert_row(missing_series, " ", "Missing", _season_num)
                missing_episode = self.mw.insert_row(missing_season, " ", "Missing", _season_num, _ep_no,
                                                                                    _entry['EpisodeTitle'].replace("&amp;", "&"),
                                                                                    _date_aired)
            else:
                missing_season = self.mw.insert_row(missing_series, " ", "Missing", _season_num, _ep_no,
                                                                                                     _entry['EpisodeTitle'].replace("&amp;", "&"),
                                                                                                     _date_aired)
            last_season = _entry['SeasonNum']

    def handle_dup(self, DUPS, last_dups, seriesdata, series_dir, seriesname, season, fmt_epno, epno, epname, ext, lastext, fqname, lastfqname, fname, lastfname):
        global dups_series, dups_episode

        log.debug('handle_dup - seriesname: %s season: %s fmt_epno: %s ext: %s' % (seriesname, season, fmt_epno, ext))

        fmt_dups = '%-8.8s %-8.8s SERIES: %-25.25s SEA: %2.2s KEEPING: %-35.35s REMOVING: %-35.35s %s'

        if last_dups != seriesname:
            if not options.nogui:
                dups_series = mw.insert_row(mw.treest_series_model, DUPS,
                                        " ",
                                        " ",
                                        seriesname,"SEASON", "KEEPING", "REMOVING", "NEW NAME")
            last_dups = seriesname

        action = 'DRY RUN'
        # Check for multiple resolutions and non-video files
        if ext != lastext:
            message = 'Two Files Found: %s and %s - \t File: %s' % (lastext, ext, os.path.splitext(fqname)[0])
            log.info(message)
            if not options.nogui:
                mw.log(message)
            if ext not in media_ext:
                if options.remove:
                    action = 'REMOVED '
                    os.remove(fqname)
            if options.nogui:
                log.warn(fmt_dups % ("DUPS-",
                                    action,
                                    seriesname,
                                    season,
                                    lastext,
                                    ext,
                                    " "))
            else:
                dups_episode = mw.insert_row(mw.treest_series_model, dups_series,
                                            action,
                                            " ",
                                            " ",
                                            season,
                                            lastfname,
                                            fname)
            return last_dups
        elif lastext not in media_ext:
            if options.remove:
                action = 'REMOVED '
                os.remove(lastfqname)
            if options.nogui:
                log.warn(fmt_dups % ("DUPS-",
                        action,
                        seriesname,
                        season,
                        ext,
                        lastext,
                        " "))
            else:
                message = 'Auto Removing: %s' % lastfqname
                log.info(message)
                mw.log(message)
                dups_episode = mw.insert_row(mw.treest_series_model, dups_series,
                                    action,
                                    " ",
                                    " ",
                                    season,
                                    fname,
                                    lastfname)
            return last_dups
        elif lastext == 'avi' and ext == 'mkv':
            if options.remove:
                action = 'REMOVED '
                os.remove(lastfqname)
            if options.nogui:
                log.warn(fmt_dups % ("DUPS-",
                                    action,
                                    seriesname,
                                    season,
                                    ext,
                                    lastext,
                                    " "))
            else:
                dups_episode = mw.insert_row(mw.treest_series_model, dups_series,
                                            action,
                                            " ",
                                            " ",
                                            season,
                                            fname,
                                            lastfname)
                return last_dups
            return last_dups
        # Possible Dup found
        epdata = {
                'base_dir' : series_dir,
                'seriesname': seriesname,
                'season': season,
                'epno' : fmt_epno,
                'ext' : ext
                }
        for item in seriesdata['episodedata']:
            for single_epno in epno:
                single_epno = [single_epno]
                if item['season'] == season and item['epno'] == single_epno:
                    if 'episodedata' in epdata:
                        epdata['episodedata'].append({'season'     : item['season'],
                                                    'epno'         : single_epno[0],
                                                    'episodename'     : item['episodename'],
                                                    'airdate'    : item['airdate']})
                    else:
                        epdata['episodedata'] = [{'season'         : item['season'],
                                                'epno'         : single_epno[0],
                                                'episodename'     : item['episodename'],
                                                'airdate'        : item['airdate']}]
        log.debug("epdata: %s" % epdata)
        if 'episodedata' in epdata:
            epdata['epname'] = formatEpisodeName(epdata['episodedata'], join_with = FileNames['multiep_join_name_with'])
            if epdata['epname'] == epname:
                message = "%-15s Season %-2s  Keeping: %-40s Removing: %s" % (seriesname, season, fname, lastfname)
                log.info(message)
                if not options.nogui:
                    mw.log(message)
                if options.remove:
                    try:
                        os.remove(lastfqname)
                        action = 'REMOVED '
                    except OSError, exc:
                        log.warning('Delete Failed: %s' % exc)
                if not options.nogui:
                    dups_episode = mw.insert_row(mw.treest_series_model, dups_series,
                                                action,
                                                " ",
                                                " ",
                                                season,
                                                fname,
                                                lastfname)
        elif epdata['epname'] == lastepname:
            message = "%-15s Season %-2s  Keeping: %-40s Removing: %s" % (seriesname, season, lastfname, fname)
            log.info(message)
            if not options.nogui:
                mw.log(message)
            if options.remove:
                try:
                    os.remove(fqname)
                    action = 'REMOVED '
                except OSError, exc:
                    log.warning('Delete Failed: %s' % exc)
            if not options.nogui:
                dups_episode = mw.insert_row(mw.treest_series_model, dups_series,
                                            action,
                                            " ",
                                            " ",
                                            season,
                                            lastfname,
                                            fname)
            else:
                new_name = FileNames['std_epname'] % epdata
                message = "%-15s Season %-2s Renaming: %-40s Removing %-40s New Name: %-40s" % (seriesname, season, lastfname, fname, new_name)
                log.info(message)
                if not options.nogui:
                    mw.log(message)
                if options.remove:
                    new_name = FileNames['std_fqn'] % epdata
                    try:
                        os.rename(lastfqname, new_name)
                    except OSError, exc:
                        log.warning('Rename Failed: %s' % exc)
                    try:
                        os.remove(fqname)
                        action = 'REMOVED '
                    except OSError, exc:
                        log.warning('Rename Failed: %s' % exc)
                if not options.nogui:
                    dups_episode = mw.insert_row(mw.treest_series_model, dups_series,
                                            action,
                                            " ",
                                            " ",
                                            season,
                                            lastfname,
                                            fname,
                                            new_name)
        else:
            message = "Possible Dup: UNKNOWN\t%s\t%s" % (lastfqname, fqname)
            log.info(message)
            if not options.nogui:
                mw.log(message)
            message = 'NO ACTION: Unable to determine proper name:'
            log.info(message)
            if not options.nogui:
                mw.log(message)


    def ignored(self, name):
        """ Check for ignored pathnames.
        """
        return any(fnmatch.fnmatch(name.lower(), pattern) for pattern in self.config.ExcludeList)

class GetOutOfLoop(Exception):
    pass
    
class localOptions(OptionParser):

    def __init__(self, unit_test=False, **kwargs):
        OptionParser.__init__(self, **kwargs)

        group = OptionGroup(self, "Series Unique Options:")
        group.add_option("-i", "--input-directory",
            dest="requested_dir",
            default="None",
            help="directory to be scanned")

        group.add_option("-x", "--no-excludes", dest="no_excludes",
            action="store_true", default=False,
            help="Ignore Exclude File")

        group.add_option("-r", "--remove", dest="remove",
            action="store_true", default=False,
            help="remove files (keep MKV over AVI, delete non-video files)")

        group.add_option("-d", "--days", dest="age_limit",
            action="store", type=int, default=90,
            help="Limit check back x number of days, default 30")
        
        group.add_option("-f", "--no-age-limit-requested", dest="age_limit",
            action="store_const", const=99999,
            help="Full Check")
        self.add_option_group(group)


if __name__ == "__main__":

    config = Settings()
    logger.initialize()
    parser = localOptions()
    options, args = parser.parse_args()

    log_level = logging.getLevelName(options.loglevel.upper())
    log_file = os.path.expanduser(options.logfile)

    # If an absolute path is not specified, use the default directory.
    if not os.path.isabs(log_file):
        log_file = os.path.join(logger.LogDir, log_file)

    logger.start(log_file, log_level)

    log.debug("Parsed command line options: {!s}".format(options))
    log.debug("Parsed arguments: %r" % args)

    _path_name = ''
    for i in range(len(args)):
        _path_name = '%s %s'% (_path_name, args[i])

    if options.requested_dir == "None":
        if len(args) > 1:
            options.requested_dir = _path_name
        else:
            log.info('Missing Scan Starting Point (Input Directory), Using Default: %r' % config.SeriesDir)
            options.requested_dir = config.SeriesDir

    if not os.path.exists(options.requested_dir):
        log.error('Invalid arguments file or path name not found: %s' % options.requested_dir)
        sys.exit(1)

    mw = MainWindow(config, options)
