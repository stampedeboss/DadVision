#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Purpose:
   Program to perform various tasks (check for missing episodes, locate duplication files, etc).
   Assist with maintaining a Library of TV Series and Episode files.

"""
from daddyvision.common import logger
from daddyvision.common.exceptions import (DataRetrievalError, EpisodeNotFound,
    SeriesNotFound, DuplicateFilesFound, InvalidFilename, RegxSelectionError,
    ConfigValueError)
from daddyvision.common.exceptions import (InvalidArgumentType, InvalidPath,
    InvalidFilename, ConfigNotFound, ConfigValueError, DictKeyError,
    DataRetrievalError, SeriesNotFound, SeasonNotFound, EpisodeNotFound,
    EpisodeNameNotFound)
from daddyvision.series.fileparser import FileParser
from daddyvision.series.episodeinfo import EpisodeDetails
from logging import INFO, WARNING, ERROR, DEBUG
import datetime
import filecmp
import fnmatch
import gtk
import gtk.glade
import logging
import os
import re
import sys
import time
import unicodedata

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

class SeriesMain():

    def __init__(self):

        builder = gtk.Builder()
        builder.add_from_file(glade_file)
        events = { "on_main_window_destroy" : self.quit,
                    "on_bt_ok_clicked" : self.bt_ok_clicked,
                    "on_bt_close_clicked" : self.bt_close_clicked
                    }
        builder.connect_signals(events)

        self.wMain = builder.get_object("main_window")

        self.wMain.set_size_request(800, 600)
        self.wMain.set_position(gtk.WIN_POS_CENTER)

        #Initialize Log TextView
        self.logwindowview=builder.get_object("txtvw_log")
        self.logwindow=gtk.TextBuffer (None)
        self.logwindowview.set_buffer(self.logwindow)

        #Initialize our Show Tree (Treeview)
        self.treevw_show=builder.get_object("treevw_show")
        self.treest_show_model=gtk.TreeStore(str, str, str, str, str, str, str, str)
        self.treevw_show.set_model(self.treest_show_model)
        #create rendered column 1
        renderer=gtk.CellRendererText()
        column=gtk.TreeViewColumn("STATUS", renderer, text=0)
        column.set_resizable(True)
        self.treevw_show.append_column(column)
        #create rendered column 2
        renderer=gtk.CellRendererText()
        column=gtk.TreeViewColumn("TVDB", renderer, text=1)
        column.set_resizable(True)
        self.treevw_show.append_column(column)
        #create rendered column 3
        renderer=gtk.CellRendererText()
        column=gtk.TreeViewColumn("SERIES", renderer, text=2)
        column.set_resizable(True)
        self.treevw_show.append_column(column)
        #create rendered column 4
        renderer=gtk.CellRendererText()
        column=gtk.TreeViewColumn(" ", renderer, text=3)
        column.set_resizable(True)
        self.treevw_show.append_column(column)
        #create rendered column 5
        renderer=gtk.CellRendererText()
        column=gtk.TreeViewColumn(" ", renderer, text=4)
        column.set_resizable(True)
        self.treevw_show.append_column(column)
        #create rendered column 6
        renderer=gtk.CellRendererText()
        column=gtk.TreeViewColumn(" ", renderer, text=5)
        column.set_resizable(True)
        self.treevw_show.append_column(column)
        #create rendered column 7
        renderer=gtk.CellRendererText()
        column=gtk.TreeViewColumn(" ", renderer, text=6)
        column.set_resizable(True)
        self.treevw_show.append_column(column)
        #create rendered column 8
        renderer=gtk.CellRendererText()
        column=gtk.TreeViewColumn(" ", renderer, text=7)
        column.set_resizable(True)
        self.treevw_show.append_column(column)

        self.treevw_show.set_hover_expand(False)

        self.wMain.show()

        gtk.main()

        return

    def insert_row(self, model, parent, status, tvdb_id=' ', show=' ', season=' ', episode=' ', title=' ', air_date=' ', item7=' '):
        myiter=model.append(parent, None)
        model.set_value(myiter, 0, status)
        model.set_value(myiter, 1, tvdb_id)
        model.set_value(myiter, 2, show)
        model.set_value(myiter, 3, season)
        model.set_value(myiter, 4, episode)
        model.set_value(myiter, 5, title)
        model.set_value(myiter, 6, air_date)
        model.set_value(myiter, 7, item7)
        return myiter

    def quit(self,obj):
        gtk.main_quit()

    def bt_ok_clicked(self,obj):
        message = "====Begin Scan===="
        log.debug(message)
        self.check_dir(requested_dir)

    def bt_close_clicked(self,obj):
        gtk.main_quit()

    def log(self, message, color="black", enter="\n"):
        message = message + enter
        buffer = self.logwindow
        iter = buffer.get_end_iter()
        if color != "black":
            tag = buffer.create_tag()
            tag.set_property("foreground", color)
            self.logwindow.insert_with_tags(buffer.get_end_iter(), message, tag)
        else:
            self.logwindow.insert(iter, message)
            mark = buffer.create_mark("end", buffer.get_end_iter(), False)
            self.logwindowview.scroll_to_mark(mark, 0.05, True, 0.0,1.0)

class Library(object):

    def __init__(self):

        episodeinfo = EpisodeDetails()

        if options.use_gui:
            mw = SeriesMain()

        if not options.nogui:

    def check(self, pathname):

        log.trace('check: Pathname Requested: {}'.format(pathname))

        dir_list = []
        tvdb_list = []
        showdata = []
        lastseries = 'START'
        lastseason = None
        lastepno = None
        lastepname = None
        lastext = None
        lastfname = None
        lastfqname = None
        scanned = 0
        last_dups = ' '

        if options.nogui:
            MISSING = " "
            DUPS    = " "
        else:
            MISSING    = mw.insert_row(mw.treest_show_model, None,"Missing")
            DUPS    = mw.insert_row(mw.treest_show_model, None,"Dup")

        log.info("====Begin Scan====")

        for root, dirs, files in os.walk(os.path.abspath(requested_dir),followlinks=True):
            if dirs != None:
                dirs.sort()
                for exclude_dir in exclude_list:
                    try:
                        index = dirs.index(exclude_dir)
                        dirs.pop(index)
                        if options.debug:
                            log.debug('Removing Dir: %s' % exclude_dir)
                    except:
                        pass
                    pass
                files.sort()
                for fname in files:
                    scanned = scanned + 1
                    quotient, remainder = divmod(scanned, 250)
                    if remainder == 0:
                        log.info('Files Processed: %s - On Series: %s' % (scanned, lastseries))
                    fqname = os.path.join(root, fname)
                    if options.debug:
                        log.debug('Processing File: %s' % (fqname))
                    for cmatcher in compiled_regexs:
                        series = cmatcher.search(fqname)
                        if series:
                            if options.debug:
                                log.debug("RegEx Matched: %s" % cmatcher.pattern)
                                namedgroups = series.groupdict().keys()
                                for key in namedgroups:
                                    log.debug("%s: %s" % ( key, series.group(key)))
                            break
                    if not series:
                        log.error("Unable to Parse: %s" % os.path.join(root, fname))
                        continue
                    if series:
                        seriesname     = series.group('seriesname').rsplit('/',1)[-1].replace("&amp;", "&")
                        season         = int(series.group('season'))
                        epname        = series.group('epname')
                        ext         = series.group('ext')
                        fmt_epno, epno = formatEpisodeNumbers(series)
                        if lastseries != seriesname:
                            log.debug('Processing Series: %s' % seriesname)
                            if args[0].lower() == 'check' or args[0].lower() == 'missing':
                                missing = checkMissing(MISSING, dir_list, tvdb_list)
                            showdata, tvdb_list = getSeries(seriesname)
                            dir_list = []
                        elif season == lastseason and epno == lastepno:
                            if args[0].lower() == 'check' or args[0].lower() == 'dups':
                                log.debug('Possible Dups: %s - %s' % (lastfname, fname))
                                last_dups = handle_dup(DUPS, last_dups, showdata, os.path.abspath(requested_dir), seriesname, season, fmt_epno, epno, epname, ext, lastext, fqname, lastfqname, fname, lastfname)

                    for ep_num in epno:
                        dir_entry = "%s\t%d\t%d" % (seriesname, season, ep_num)
                        dir_list.append(dir_entry)

                    lastseries     = seriesname
                    lastfqname     = fqname
                    lastfname     = fname
                    lastseason     = season
                    lastepno     = epno
                    lastepname     = epname
                    lastext     = ext

        if args[0].lower() == 'check' or args[0].lower() == 'missing':
            missing = checkMissing(MISSING, dir_list, tvdb_list)

        def processDups(self, dups):
            pass




    def getSeries(seriesname):
        if options.debug:
            log.debug('getSeries - seriesname: %s' % (seriesname))
        try:
            showdata = {'seriesname': seriesname}
            showdata = episodeinfo.ShowDetails(showdata)
        except (SeriesNotFound, InvalidArgumentType, InvalidPath, InvalidFilename,
            ConfigNotFound, ConfigValueError, DataRetrievalError) as errormsg:
            log.warn(errormsg)
            log.error("Skipping series: %s" % (seriesname))
            return None, None
        tvdb_list = []
        for item in showdata['episodedata']:
            if item['airdate'] is not None:
                if item['airdate'] < (datetime.today() - timedelta(days=1)):
                    showid         = showdata['showid']
                    seriesname     = showdata['seriesname']
                    season         = item['season']
                    epnum         = item['epno'][0]
                    eptitle     = item['episodename']
                    airdate     = item['airdate']
                    tvdb_entry = "%s\t%d\t%d\t%s\t%s\t%s" % (seriesname, season, epnum, eptitle, airdate, showid)
                    tvdb_list.append(tvdb_entry)
        tvdb_list.sort()
        return showdata, tvdb_list

    def checkMissing(MISSING, dir_list, tvdb_list):
        if options.debug:
            log.debug('checkMissing - dir_list: tvdb_list:' % ())
        if tvdb_list == None:
            return
        missing = []
        tvdb_entry = ''
        dir_entry = ''
        date_boundry = date.today() - timedelta(days=options.age_limit)
        for tvdb_entry in tvdb_list:
            found_show = False
            tvdb_seriesname, tvdb_season, tvdb_epno, tvdb_eptitle, tvdb_airdate, tvdb_showid = tvdb_entry.split("\t")
            if not options.show_specials:
                if int(tvdb_season) == 0:
                    continue
            if options.age_limit_requested:
                year, month, day = time.strptime(tvdb_airdate, "%Y-%m-%d %H:%M:%S")[:3]
                if date(year, month, day) < date_boundry:
                    continue
            for dir_entry in dir_list:
                dir_seriesname, dir_season, dir_epno = dir_entry.split("\t")
                if tvdb_season == dir_season and tvdb_epno == dir_epno:
                    found_show = True
                    continue
            if not found_show:
                missing.append(tvdb_entry)
                if options.debug:
                    log.warn(tvdb_entry)

        if len(missing) > 0:
            tvdb_seriesname, tvdb_season, tvdb_epno, tvdb_eptitle, tvdb_airdate, tvdb_showid = missing[0].split("\t")
            message = "Missing %i episode(s) - TVDB ID: %8.8s SERIES: %-25.25s" % (len(missing), tvdb_showid, tvdb_seriesname)
            log.warn(message)
            if not options.nogui:
                mw.log(message, "red")
                missing_series = mw.insert_row(mw.treest_show_model, MISSING,
                                            " ",
                                            tvdb_showid,
                                            tvdb_seriesname,
                                            "SEA/EP",
                                            "TITLE",
                                            "AIR DATE")
        last_season = ''
        for tvdb_entry in missing:
            tvdb_seriesname, tvdb_season, tvdb_epno, tvdb_eptitle, tvdb_airdate, tvdb_showid = tvdb_entry.split("\t")
            tvdb_season = "S%2.2d" % int(tvdb_season)
            tvdb_epno = "E%2.2d" % int(tvdb_epno)
            tvdb_airdate = datetime.strptime(tvdb_airdate, "%Y-%m-%d %H:%M:%S")
            if options.nogui:
                log.warn('%8.8s SEA: %3.3s EPNO: %3.3s TITLE: %-25.25s AIRDATE: %s' % (
                                                                                        "Missing-",
                                                                                        tvdb_season,
                                                                                        tvdb_epno,
                                                                                        tvdb_eptitle,
                                                                                        tvdb_airdate.strftime("%Y-%m-%d")))
            else:
                if last_season != tvdb_season:
                    missing_season = mw.insert_row(mw.treest_show_model, missing_series, " ", " ", " ", tvdb_season)
                    missing_episode = mw.insert_row(mw.treest_show_model, missing_season,
                                                " ",
                                                " ",
                                                " ",
                                                tvdb_epno,
                                                tvdb_eptitle,
                                                tvdb_airdate.strftime("%Y-%m-%d"))

            last_season = tvdb_season

    def handle_dup(DUPS, last_dups, showdata, series_dir, seriesname, season, fmt_epno, epno, epname, ext, lastext, fqname, lastfqname, fname, lastfname):
        global dups_series, dups_episode

        if options.debug:
            log.debug('handle_dup - seriesname: %s season: %s fmt_epno: %s ext: %s' % (seriesname, season, fmt_epno, ext))

        fmt_dups = '%-8.8s %-8.8s SERIES: %-25.25s SEA: %2.2s KEEPING: %-35.35s REMOVING: %-35.35s %s'

        if last_dups != seriesname:
            if not options.nogui:
                dups_series = mw.insert_row(mw.treest_show_model, DUPS,
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
                dups_episode = mw.insert_row(mw.treest_show_model, dups_series,
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
                dups_episode = mw.insert_row(mw.treest_show_model, dups_series,
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
                dups_episode = mw.insert_row(mw.treest_show_model, dups_series,
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
        for item in showdata['episodedata']:
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
        if options.debug:
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
                    dups_episode = mw.insert_row(mw.treest_show_model, dups_series,
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
                dups_episode = mw.insert_row(mw.treest_show_model, dups_series,
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
                    dups_episode = mw.insert_row(mw.treest_show_model, dups_series,
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

    def formatEpisodeNumbers(series):
        if options.debug:
            log.debug('formatEpisodeNumbers - series: %s' % (series))
        """Format episode number(s) into string, using configured values
        """
        namedgroups = series.groupdict().keys()
        if 'episodenumber1' in namedgroups:
            # Multiple episodes, have episodenumber1 or 2 etc
            epno = []
            for cur in namedgroups:
                epnomatch = re.match('episodenumber(\d+)', cur)
                if epnomatch:
                    epno.append(int(series.group(cur)))
                epno.sort()
        elif 'episodenumberstart' in namedgroups:
            # Multiple episodes, regex specifies start and end number
            start = int(series.group('episodenumberstart'))
            end = int(series.group('episodenumberend'))
            if start > end:
                # Swap start and end
                start, end = end, start
            epno = range(start, end + 1)

        elif 'episodenumber' in namedgroups:
            epno = [int(series.group('episodenumber')), ]

        if len(epno) == 1:
            fmt_epno = FileNames['episode_single'] % epno[0]
        else:
            fmt_epno = FileNames['episode_separator'].join(
                                                        FileNames['episode_single'] % x for x in epno)

        return fmt_epno, epno

    def formatEpisodeName(epdata, join_with):
        if options.debug:
            log.debug('formatEpisodeName - epdata: %s' % (epdata))
        """Takes a list of episode names, formats them into a string.
        If two names are supplied, such as "Pilot (1)" and "Pilot (2)", the
        returned string will be "Pilot (1-2)"

        If two different episode names are found, such as "The first", and
        "Something else" it will return "The first, Something else"
        """

        names = []
        for nameentry in epdata:
            newname = nameentry['episodename']
            newname = unicodedata.normalize('NFKD', newname).encode('ascii','ignore')
            newname = newname.replace("&amp;", "&").replace("/", "_")
            names.append(newname)
            if options.debug:
                log.debug('EP Name: %s' % nameentry['episodename'])

        if len(names) == 0:
            return "NOT FOUND IN TVDB"

        if len(names) == 1:
            return names[0]

        found_names = []
        numbers = []

        for cname in names:
            number = re.match("(.*) \(([0-9]+)\)$", cname)
            if number:
                epname, epno = number.group(1), number.group(2)
                if len(found_names) > 0 and epname not in found_names:
                    return join_with.join(names)
                found_names.append(epname)
                numbers.append(int(epno))
            else:
                # An episode didn't match
                return join_with.join(names)

        names = []
        start, end = min(numbers), max(numbers)
        names.append("%s (%d-%d)" % (found_names[0], start, end))
        return join_with.join(names)

if __name__ == "__main__":

    from daddyvision.common.settings import Settings
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

    _config_settings = Settings()

    _path_name = ''
    for i in range(len(args)):
        _path_name = '%s %s'% (_path_name, args[i])
    _path_name = _path_name.lstrip().rstrip()
    if len(_path_name) == 0:
        _new_series_dir = os.path.join ( os.path.split(_config_settings.SeriesDir)[0], _config_settings.NewDir )
        msg = 'Missing Scan Starting Point (Input Directory), Using Default: {}'.format(_new_series_dir)
        log.info(msg)
        _path_name = _new_series_dir

    if not os.path.exists(_path_name):
        log.error('Invalid arguments file or path name not found: %s' % _path_name)
        sys.exit(1)

    if options.requested_dir == "None":
        if len(args) > 1:
            options.requested_dir = args[1]
        else:
            log.info('Missing Scan Starting Point (Input Directory), Using Default: %r' % series_dir)
            options.requested_dir = series_dir

    library = Library()

    library.Check(options.requested_dir)
