#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Purpose:
   Program to perform various tasks (check for missing episodes, locate duplication files, etc).
   Assist with maintaining a Library of Series and Episode files.

"""
from __future__ import division
from library import Library
from common.countfiles import countFiles
from common.cmdoptions import CmdOptions
from common.exceptions import (RegxSelectionError,
    InvalidArgumentType, InvalidPath, InvalidFilename, ConfigNotFound,
    ConfigValueError, DataRetrievalError, SeriesNotFound,
    SeasonNotFound, EpisodeNotFound)
from common import logger
from library.series.episodeinfo import EpisodeDetails
from library.series.fileparser import FileParser
from datetime import datetime, date, timedelta
from logging import INFO, WARNING, ERROR, DEBUG
from pytvdbapi import api
from pytvdbapi.error import TVDBAttributeError, TVDBIndexError, TVDBValueError, TVDBIdError, BadData
import difflib
import fnmatch
import logging
import os
import re
import sys
import unicodedata

__pgmname__ = 'library.series.check'
__version__ = '$Rev$'

__author__ = "@author: AJ Reynolds"
__email__ = "@contact: stampedeboss@gmail.com"
__copyright__ = "@copyright: Copyright 2011, AJ Reynolds"
__license__ = "@license: GPL"

__maintainer__ = "@organization: AJ Reynolds"
__status__ = "@status: Development"
__credits__ = []

log = logging.getLogger(__pgmname__)

class CheckSeries(Library):

    def __init__(self):
        log.trace('__init__ method: Started')

        super(CheckSeries, self).__init__()

        check_group1= self.options.parser.add_argument_group("Series Unique Options", description=None)
        check_group1.add_argument("-x", "--no-excludes", dest="no_excludes",
            action="store_true", default=False,
            help="Ignore Exclude File")
        check_group1.add_argument("-s", "--include-specials", dest="specials",
            action="store_true", default=False,
            help="remove files (keep MKV over AVI, delete non-video files)")
        check_group1.add_argument("-r", "--remove", dest="remove",
            action="store_true", default=False,
            help="remove files (keep MKV over AVI, delete non-video files)")
        check_group1.add_argument("-d", "--days", dest="age_limit",
            action="store", type=int, default=90,
            help="Limit check back x number of days, default 30")
        check_group1.add_argument("-f", "--no-age-limit-requested", dest="age_limit",
            action="store_const", const=99999,
            help="Full Check")

        self.episodeinfo = EpisodeDetails()
        self.parser = FileParser()
        self.db = api.TVDB("959D8E76B796A1FB")

        self.regex_season = re.compile('^(?:Season).(?P<SeasonNum>[0-9]+)$', re.I)
        self.regex_episode = re.compile('^(?:E)(?P<EpisodeNum>[0-9][0-9]+)[\.\- ]*(?:E)?(?P<EpisodeNum2>[0-9][0-9]+)?(?P<EpisodeName>.+)?\.(?P<Ext>.+?)$', re.I)
        
        return

    def check(self, pathname):
        log.trace('check: Pathname Requested: {}'.format(pathname))

        pathname = os.path.abspath(pathname)
        _series_details = []

        self.write_log_entry("==== Begin Scan: {} ====".format(pathname), INFO)

        _series = self.getListSeries(pathname)
        for _show in _series:
            _episode_list = []
	    _seasons = []
            try:
                _series_details = self.getSeriesInfo(_show)
            except (TVDBIdError, BadData), message:
                log.error('Invalid Entry in TVDBID File: {} {}'.format(_show, message))
                raise ConfigValueError('Invalid Entry in TVDBID File: {} {}'.format(_show, message))

            if not _series_details:
                continue

            _seasons = os.listdir(os.path.join(self.settings.SeriesDir,_show))
            for _season in _seasons:
                _parsed_details = self.regex_season.match(_season)
                if not _parsed_details:
                   continue

                self.Show_Details = {}
                self.Show_Details['SeasonNum'] = int(_parsed_details.group('SeasonNum'))
                _epno_list = []

                _episodes = os.listdir(os.path.join(self.settings.SeriesDir,_show, _season))
                for _episode in _episodes:
                    if not os.path.splitext(_episode)[1][1:] in self.settings.MediaExt:
                        continue

                    _parsed_details = self.regex_episode.match(_episode)
                    if not _parsed_details:
                        continue

                    _epno = [int(_parsed_details.group('EpisodeNum'))]
                    _epno_list.append(int(_parsed_details.group('EpisodeNum')))

                    if _parsed_details.group('EpisodeNum2'):
                        _epno.append(int(_parsed_details.group('EpisodeNum2')))
                        _epno_list.append(int(_parsed_details.group('EpisodeNum2')))

                self.Show_Details['EpisodeNums'] = _epno_list
                _episode_list.append(self.Show_Details)

            log.debug(_episode_list)
            self.checkMissing(_series_details, _episode_list)

	sys.exit()

    def getListSeries(self, pathname):

	_prefix = os.path.commonprefix([pathname, self.settings.SeriesDir])
        if not _prefix == self.settings.SeriesDir:
            raise
        elif not os.path.abspath(pathname) == self.settings.SeriesDir:
            return [os.path.basename(pathname)]

        _series = os.listdir(os.path.abspath(pathname))
        _series.sort()
        _series_temp = sorted(_series)
        for _show in _series_temp:
            if self.ignored(_show) or _show == "New":
                _series.remove(_show)
                log.trace('Removing Series: %s' % _show)

        for _show in _series:
            _matches = difflib.get_close_matches(_show, _series, 2, cutoff=0.9)
            if len(_matches) > 1:
            	log.error('Possible Duplicate Directories: {} - {}'.format(_matches[0], _matches[1]))

        return _series


    def getSeriesInfo(self, seriesname):
        log.trace('getSeries: Series Name: %s' % (seriesname))

        try:
            _series_details = {'SeriesName': seriesname}
            _series_details = self.episodeinfo.getDetails(_series_details)
        except (SeriesNotFound, InvalidArgumentType, InvalidPath, InvalidFilename,
            ConfigNotFound, ConfigValueError, DataRetrievalError) as errormsg:
            log.warn(errormsg)
            log.warn("Skipping series: %s" % (seriesname))
            return None

        log.debug(_series_details)
        return _series_details

    def checkMissing(self, series_details, episode_list):
        log.debug('checkMissing - series_details: {} episode_list: {}'.format(series_details, episode_list))
        #{'SeasonNum': 10, 'DateAired': datetime.date(2013, 12, 5), 'EpisodeTitle': u'Man on the Moon', 'EpisodeNum': 11}

        missing = []
        _seasons_found = {}
        date_boundry = date.today() - timedelta(days=self.args.age_limit)

        for series_entry in series_details['EpisodeData']:
            if series_entry['DateAired']:
                if series_entry['DateAired'] < date_boundry or series_entry['DateAired'] >= datetime.today().date():
                    continue
            else:
                continue
            if not self.args.specials and series_entry['SeasonNum'] == 0:
                continue

            found_episode = False
            try:
                for episode_entry in episode_list:
                    if series_entry['SeasonNum'] == episode_entry['SeasonNum'] and series_entry['EpisodeNum'] in episode_entry['EpisodeNums']:
                        found_episode = True

                        if not series_details['SeriesName'] in _seasons_found:
                            _seasons_found[series_details['SeriesName']] = [series_entry['SeasonNum']]
                        elif series_details['SeriesName'] in _seasons_found:
                            if not series_entry['SeasonNum'] in _seasons_found[series_details['SeriesName']]:
                                _seasons_found[series_details['SeriesName']].append(series_entry['SeasonNum'])

                        if len(episode_entry['EpisodeNums']) > 1:
                            log.debug('Matched: Season {} Episode {}'.format(series_entry['SeasonNum'], series_entry['EpisodeNum']))
                            episode_entry['EpisodeNums'].remove(series_entry['EpisodeNum'])
                        else:
                            episode_list.remove(episode_entry)
                        raise GetOutOfLoop
            except GetOutOfLoop:
                continue

            if not found_episode:
                missing.append(series_entry)

        if len(missing) > 0:
            message = "Missing %i episode(s) - SERIES: %-35.35s" % (len(missing), series_details['SeriesName'])
            self.write_log_entry(message, ERROR)

        season_message = "         Season: {}  Episode: ALL"
        message = "         Season: {}  Episode: {}  Aired: {} Title: {}"

        _last_season = None
        for _entry in missing:

            if (series_details['SeriesName'] in _seasons_found and _entry['SeasonNum'] in _seasons_found[series_details['SeriesName']]) or self.args.age_limit < 99999:
                _season_num = "S%2.2d" % int(_entry['SeasonNum'])
                _ep_no = "E%2.2d" % int(_entry['EpisodeNum'])
                if _entry['DateAired']:
                    _date_aired = _entry['DateAired']
                else:
                    _date_aired = "Unknown"
                log.error(message.format(_season_num, 
                                         _ep_no,
                                         _date_aired,
                                         _entry['EpisodeTitle'].encode('utf8', 'replace').replace("&amp;", "&")))
            else:
                _season_num = "S%2.2d" % int(_entry['SeasonNum'])
                if not _season_num == _last_season:
                    log.error(season_message.format(_season_num))
                    _last_season = _season_num

        return

    def processDups(self, dups):
        pass

    def handle_dup(self, DUPS, last_dups, seriesdata, series_dir, seriesname, season, fmt_epno, epno, epname, ext, lastext, fqname, lastfqname, fname, lastfname):
        global dups_series, dups_episode

        log.debug('handle_dup - seriesname: %s season: %s fmt_epno: %s ext: %s' % (seriesname, season, fmt_epno, ext))

        fmt_dups = '%-8.8s %-8.8s SERIES: %-25.25s SEA: %2.2s KEEPING: %-35.35s REMOVING: %-35.35s %s'

        if last_dups != seriesname:
            if not self.args.nogui:
                dups_series = mw.insert_row(mw.treest_series_model, DUPS,
                                        " ",
                                        " ",
                                        seriesname, "SEASON", "KEEPING", "REMOVING", "NEW NAME")
            last_dups = seriesname

        action = 'DRY RUN'
        # Check for multiple resolutions and non-video files
        if ext != lastext:
            message = 'Two Files Found: %s and %s - \t File: %s' % (lastext, ext, os.path.splitext(fqname)[0])
            log.info(message)
            if ext not in media_ext:
                if self.args.remove:
                    action = 'REMOVED '
                    os.remove(fqname)
            log.warn(fmt_dups % ("DUPS-",
                                action,
                                seriesname,
                                season,
                                lastext,
                                ext,
                                " "))
            return last_dups

        elif lastext not in media_ext:
            if self.args.remove:
                action = 'REMOVED '
                os.remove(lastfqname)
            log.warn(fmt_dups % ("DUPS-",
                     action,
                     seriesname,
                     season,
                     ext,
                     lastext,
                     " "))
            return last_dups

        elif lastext == 'avi' and ext == 'mkv':
            if self.args.remove:
                action = 'REMOVED '
                os.remove(lastfqname)
            log.warn(fmt_dups % ("DUPS-",
                                 action,
                                 seriesname,
                                 season,
                                 ext,
                                 lastext,
                                 " "))
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
            epdata['epname'] = formatEpisodeName(epdata['episodedata'], join_with=FileNames['multiep_join_name_with'])
            if epdata['epname'] == epname:
                message = "%-15s Season %-2s  Keeping: %-40s Removing: %s" % (seriesname, season, fname, lastfname)
                log.info(message)
                if self.args.remove:
                    try:
                        os.remove(lastfqname)
                        action = 'REMOVED '
                    except OSError, exc:
                        log.warning('Delete Failed: %s' % exc)
        elif epdata['epname'] == lastepname:
            message = "%-15s Season %-2s  Keeping: %-40s Removing: %s" % (seriesname, season, lastfname, fname)
            log.info(message)
            if self.args.remove:
                try:
                    os.remove(fqname)
                    action = 'REMOVED '
                except OSError, exc:
                    log.warning('Delete Failed: %s' % exc)
            else:
                new_name = FileNames['std_epname'] % epdata
                message = "%-15s Season %-2s Renaming: %-40s Removing %-40s New Name: %-40s" % (seriesname, season, lastfname, fname, new_name)
                log.info(message)
                if self.args.remove:
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
        else:
            message = "Possible Dup: UNKNOWN\t%s\t%s" % (lastfqname, fqname)
            log.info(message)
            message = 'NO ACTION: Unable to determine proper name:'
            log.info(message)

    def write_log_entry(self, msg, level=INFO):
        log.trace('write_log_entry: Level: {}  Message: {}'.format(level, msg))
        if level == WARNING:
            log.warn(msg)
        elif level == ERROR:
            log.error(msg)
        else:
            log.info(msg)
        return

    def ignored(self, name):
        """ Check for ignored pathnames.
        """
        exclude = self.settings.ExcludeList + self.settings.ExcludeScanList
        return any(fnmatch.fnmatch(name.lower(), pattern) for pattern in (self.settings.ExcludeList + self.settings.ExcludeScanList))


class GetOutOfLoop(Exception):
    pass


if __name__ == "__main__":

    from library import Library
    from logging import INFO, WARNING, ERROR, DEBUG

    logger.initialize()

    library = CheckSeries()

    Library.args = library.options.parser.parse_args(sys.argv[1:])
    log.debug("Parsed command line: {!s}".format(library.args))

    log_level = logging.getLevelName(library.args.loglevel.upper())

    if library.args.logfile == 'daddyvision.log':
        log_file = '{}.log'.format(__pgmname__)
    else:
        log_file = os.path.expanduser(library.args.logfile)

    # If an absolute path is not specified, use the default directory.
    if not os.path.isabs(log_file):
        log_file = os.path.join(logger.LogDir, log_file)

    logger.start(log_file, log_level, timed=True)

    if library.args.no_excludes:
        library.settings.ExcludeScanList = []

    if len(library.args.library) == 0:
        msg = 'Missing Scan Starting Point (Input Directory), Using Default: {}'.format(library.settings.SeriesDir)
        log.info(msg)
        library.args.library = [library.settings.SeriesDir]

    for _lib_path in library.args.library:
        if os.path.exists(_lib_path):
            library.check(_lib_path)
        else:
            log.warn('Skipping Rename: Unable to find File/Directory: {}'.format(_lib_path))



