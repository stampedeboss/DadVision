#!/usr/bin/env python
"""
Author: AJ Reynolds
Date: 12-11-2010
Purpose:
Program to rename and update Modification Time to Air Date

"""
from seriesExceptions import *
from seriesinfo import SeriesInfo
from getconfig import GetConfig
import re
import os
import sys
import filecmp
import fnmatch
import logging
from logging import INFO, WARNING, ERROR, DEBUG
import datetime
import time
import unicodedata

__version__ = '$Rev$'
__pgmname__ = 'DownloadMonitor'

#Level     Numeric value
#CRITICAL    50
#ERROR       40
#WARNING     30
#INFO        20
#DEBUG       10
#NOTSET       0

# A level more detailed than DEBUG
TRACE = 5
# A level more detailed than INFO
VERBOSE = 15

logging.addLevelName(5, 'TRACE')
logging.addLevelName(15, 'VERBOSE')
logger = logging.getLogger()
setattr(logger, 'TRACE', lambda *args: logger.log(5, *args))
setattr(logger, 'VERBOSE', lambda *args: logger.log(15, *args))

class RenameShows(object):
    def __init__(self, parms, options):
        logger.TRACE('RenameShows.__init__')
        logger.debug(options)

        self.parms = parms
        self.options = options

        self.regex_repack = re.compile('^.*(repack|proper).*$', re.IGNORECASE)
        self.check_suffix = re.compile('^(?P<seriesname>.+?)[ \._\-](?P<year>[0-9][0-9][0-9][0-9]|US|us|Us)$', re.VERBOSE)
#        self.check_year = re.compile('^(?P<seriesname>.+?)[ \._\-](?P<year>[0-9][0-9][0-9][0-9])$', re.VERBOSE)
#        self.check_US = re.compile('^(?P<seriesname>.+?)[ \._\-](?P<country>US)$', re.VERBOSE)

        self.lastseries = None
        self.showdata = {}
        self.showinfo = SeriesInfo()
        return

    def ProcessFile(self, pathname):
        if os.path.isfile(pathname):
            logger.debug("-----------------------------------------------")
            logger.debug("Directory: %s" % os.path.split(pathname)[0])
            logger.debug("Filename:  %s" % os.path.split(pathname)[1])
            series, epdata = self.FileParser(pathname)
            if epdata : epdata = self.GetEpisodeDetails(epdata)
            if epdata : self.RenameFile(pathname, epdata)
        elif os.path.isdir(pathname):
            for root, dirs, files in os.walk(os.path.abspath(pathname),followlinks=False):
                for dir in dirs[:]:
                    if self.ignored(dir):
                        logger.debug("Ignoring %r" % os.path.join(root, dir))
                        dirs.remove(dir)
                files.sort()
                for fname in files:
                    pathname = os.path.join(root, fname)
                    logger.debug("-----------------------------------------------")
                    logger.debug("Filename: %s" % pathname)
                    try:
                        series, epdata = self.FileParser(pathname)
                        if epdata:
                            epdata = self.GetEpisodeDetails(epdata)
                        if epdata:
                            self.RenameFile(pathname, epdata)
                    except InvalidFilename, msg:
                        logger.warning('File Name Invalid for Automatic Handling, Requires Manual Intervention')
                        continue
        else:
            logger.error('Invalid Parm, Neither File or Directory: %s' % pathname)
        try:
            cmd='xbmc-send --host=happy --action="XBMC.UpdateLibrary(video)"'
            os.system(cmd)
            logger.TRACE("TV Show Rename Trigger Successful")
        except OSError, exc:
            logger.error("TV Show Rename Trigger Failed: %s" % exc)


    def FileParser(self, pathname):
        """Runs path via configured regex, extracting data from groups.
        Returns an Dictionary instance containing extracted data.
        """
        path, fname    = os.path.split(pathname)

        seriesname      = ''
        seasonnumber    = ''
        episodenumbers  = ''
        epno            = ''
        airdate         = ''

        logger.debug("FileParser - File Name: %s" % (fname))

        EPScheme = re.compile('^E[0-9][0-9].*', re.X|re.I)
        EPParse = re.compile(            '''                                     # RegEx 1
            ^(/.*/)*                                # Directory
            (?P<seriesname>.*)                      # Series Name
            (/Season)                               # Season
            [/\._ \-]                               # Sep 1
            (?P<seasonnumber>[0-9]+)                # Season Number (##)
            (/)                                     # Directory Seperator
            [E|e]                                   # Episode Number (##)
            (?P<episodenumber>[0-9][0-9]+)          # e
            [/\._ \-]?                              # Optional Sep 1
            (?P<epname>.+)?                         # Optional Title
            \.(?P<ext>....?)$                       # extension
            ''',
             re.X|re.I)
        series = EPScheme.match(fname)
        if series:
            series = EPParse.match(pathname)
            if not series:
                sys.exit(1)
        else:
            for cmatcher in self.compiled_regexs:
                series = cmatcher.match(fname)
                if series:
                    break

        if series:
            namedgroups = series.groupdict().keys()
            namedgroups = series.groupdict().keys()
            for key in namedgroups:
                logger.TRACE("%s: %s" % ( key, series.group(key)))

            if 'seriesname' in namedgroups and series.group('seriesname') != None:
                seriesname = series.group('seriesname')
                logger.debug('FileParser - SeriesName: %s' % seriesname)
                seriesname = self.cleanRegexedSeriesName(seriesname)
                logger.debug('FileParser - Post Clean SeriesName: %s' % seriesname)
            else:
                msg = 'FileParser: Missing Show Name: %s' % fname
                raise InvalidFilename(msg)
                logger.warning(msg)

            if 'ext' in namedgroups:
                ext = series.group('ext')
            elif fname[-4] == '.':
                    ext = fname[-4:]
                    logger.TRACE['ext: %s' % ext]
            else:
                logger.debug('FileParser - Missing Extension - Named Groups: %s' % (namedgroups))
                raise InvalidFilename(fname)


            if 'episodenumber1' in namedgroups:
                # Multiple episodes, have episodenumber1 or 2 etc
                epnos = []
                for cur in namedgroups:
                    epnomatch = re.match('episodenumber(\d+)', cur)
                    if epnomatch:
                        epnos.append(int(series.group(cur)))
                epnos.sort()
                episodenumbers = epnos
            elif 'episodenumberstart' in namedgroups:
                # Multiple episodes, regex specifies start and end number
                start = int(series.group('episodenumberstart'))
                end = int(series.group('episodenumberend'))
                if start > end:
                    # Swap start and end
                    start, end = end, start
                episodenumbers = range(start, end + 1)
            elif 'episodenumber' in namedgroups:
                episodenumbers = [int(series.group('episodenumber')), ]
                logger.debug('FileParser - Episode Number: %s' % episodenumbers)
            elif 'year' in namedgroups or 'month' in namedgroups or 'day' in namedgroups:
                if not all(['year' in namedgroups, 'month' in namedgroups, 'day' in namedgroups]):
                    raise ConfigValueError("Date-based regex must contain groups 'year', 'month' and 'day'")
                series.group('year')

                airdate = datetime.datetime(int(series.group('year')),
                                         int(series.group('month')),
                                         int(series.group('day')))
            else:
                raise ConfigValueError(
                    "Regex does not contain episode number group, should"
                    "contain episodenumber, episodenumber1-9, or"
                    "episodenumberstart and episodenumberend\n\nPattern"
                    "was:\n" + cmatcher.pattern)

            if 'seasonnumber' in namedgroups:
                seasonnumber = int(series.group('seasonnumber'))
                epdata = {
                          'base_dir' : self.parms.series_dir,
                          'seriesname': seriesname,
                          'seasonnumber': seasonnumber,
                          'epno': episodenumbers,
                          'ext' : ext
                          }
            elif 'year' in namedgroups and 'month' in namedgroups and 'day' in namedgroups:
                epdata = {
                          'base_dir' : self.parms.series_dir,
                          'seriesname': seriesname,
                          'airdate': airdate,
                          'ext' : ext
                          }
            else:
                logger.debug('FileParser - No Season Number, Named Groups: %s' % (namedgroups))
                raise InvalidFilename(fname)
#                    # No season number specified, usually for Anime
#                    epdata = NoSeasonEpisodeInfo(
#                    seriesname = seriesname,
#                    episodenumbers = episodenumbers,
#                    filename = self.path)
            return series, epdata
        else:
            raise InvalidFilename(fname)

    def GetEpisodeDetails(self, epdata):
        if not epdata:
            logger.warn("No Match: %s" % epdata)
            return None
        seriesname = epdata['seriesname']
        if 'episodedata' in self.showdata and self.lastseries == seriesname:
            pass
        else:
            logger.debug('Last Series: %s  Current Series: %s' % (self.lastseries, seriesname))
            self.lastseries = seriesname
            self.showdata = {'seriesname': seriesname}
            try:
                self.showdata  = self.showinfo.ShowDetails(self.showdata)
            except (ShowNotFound, EpisodeNotFound), message:
                logger.warn("%s" % (message))
                return None

        seriesname     = self.showdata['seriesname']
        try:
            for item in self.showdata['episodedata']:
                if 'epno' in epdata:
                    if item['season'] >= epdata['seasonnumber']:
                        if item['epno'][-1] > epdata['epno'][-1]:
                            raise GetOutOfLoop
                    for single_epno in epdata['epno']:
                        single_epno = [single_epno]
                        if item['season'] == epdata['seasonnumber'] and item['epno'] == single_epno:
                            if 'episodedata' in epdata:
                                epdata['episodedata'].append({'seasonnumber' : item['season'],
                                                              'epno'        : single_epno[0],
                                                              'episodename' : item['episodename'],
                                                              'airdate'     : item['airdate']})
                            else:
                                epdata['airdate'] = item['airdate']
                                epdata['episodedata'] = [{'seasonnumber' : item['season'],
                                                          'epno'            : single_epno[0],
                                                          'episodename'     : item['episodename'],
                                                          'airdate'         : item['airdate']}]
                            logger.debug("epdata: %s" % item)
                            if len(epdata['epno']) == 1:
                                raise GetOutOfLoop
                            else:
                                break
                else:
                    if item['airdate'] == epdata['airdate']:
                        if 'episodedata' in epdata:
                            epdata['seasonnumber'] = item['season']
                            epdata['epno'] = item['epno']
                            epdata['episodedata'].append({'seasonnumber' : item['season'],
                                                          'epno'        : item['epno'],
                                                          'episodename' : item['episodename'],
                                                          'airdate'     : item['airdate']})
                        else:
                            epdata['seasonnumber'] = item['season']
                            epdata['epno'] = item['epno']
                            epdata['episodedata'] = [{'seasonnumber' : item['season'],
                                                      'epno'            : item['epno'],
                                                      'episodename'     : item['episodename'],
                                                      'airdate'         : item['airdate']}]
                        logger.debug("epdata: %s" % item)
                        raise GetOutOfLoop
        except GetOutOfLoop:
            pass

        if not 'episodedata' in epdata:
            raise EpisodeNotFound('Episode Not Found: %s' % epdata)
        epdata['seriesname'] = seriesname
        epdata['epname'] = self.formatEpisodeName(epdata['episodedata'], join_with = self.parms.FileNames['multiep_join_name_with'])
        if len(epdata['epno']) == 1:
            epdata['epno'] = self.parms.FileNames['episode_single'] % epdata['epno'][0]
        else:
            epdata['epno'] = self.parms.FileNames['episode_separator'].join(
                self.parms.FileNames['episode_single'] % x for x in epdata['epno'])
        return epdata

    def RenameFile(self, pathname, epdata):
        if not 'episodedata' in epdata:
            logger.info('rename_message' % (epdata['seriesname'], epdata['seasonnumber'], "TVDB Data Not Found", os.path.basename(pathname)))
            return None

        repack  = self.regex_repack.search(pathname)
        if repack:
            new_name = self.parms.FileNames['std_fqn'] % epdata
            try:
                os.remove(new_name)
            except:
                logger.info('Unable to delete: %s' % new_name)
            new_name = self.parms.FileNames['proper_fqn'] % epdata
        else:
            new_name = self.parms.FileNames['std_fqn'] % epdata

        if os.path.exists(new_name) and filecmp.cmp(new_name, pathname):
            if os.path.split(new_name)[0] == os.path.split(pathname)[0]:
                logger.info('Updating Inplace: %s ==> %s' % (pathname, new_name))
                self.UpdateDate(epdata, new_name)
            else:
                logger.info("Deleting %r, already at destination!" % (os.path.split(pathname)[1],))
                os.remove(pathname)
                self.delDir(pathname)
            return

        logger.info(self.parms.FileNames['rename_message'] % (epdata['seriesname'], epdata['seasonnumber'], os.path.basename(new_name), os.path.basename(pathname)))
        try:
            if not os.path.exists(os.path.split(new_name)[0]):
                os.makedirs(os.path.split(new_name)[0])
                if os.getgid() == 0:
                    os.chown(os.path.split(new_name)[0], 1000, 100)
            os.rename(pathname, new_name)
            logger.info("Successfully Renamed: %s" % new_name)
        except OSError, exc:
            logger.error("Skipping, Unable to Rename File: %s" % pathname)
            logger.error("Unexpected error: %s" % exc)

        self.delDir(pathname)

        self.UpdateDate(epdata, new_name)

    def UpdateDate(self,epdata, new_name):
        air_date = epdata['airdate']
        cur_date = time.localtime(os.path.getmtime(new_name))
        if air_date:
            tt = air_date.timetuple()
            logger.debug('Current File Date: %s  Air Date: %s' % (time.asctime(cur_date), time.asctime(tt)))
            tup_cur = [cur_date[0], cur_date[1], cur_date[2], cur_date[3], cur_date[4], cur_date[5], cur_date[6], cur_date[7], -1]
            tup = [tt[0], tt[1], tt[2], 20, 0, 0, tt[6], tt[7], tt[8]]
            if tup != tup_cur:
                time_epoc = time.mktime(tup)
                try:
                    logger.info("Updating First Aired: %s %s" % (new_name, air_date))
                    os.utime(new_name, (time_epoc, time_epoc))
                except (OSError, IOError), exc:
                    logger.error("Skipping, Unable to update time: %s" % new_name)
                    logger.error("Unexpected error: %s" % exc)

    def delDir(self, pathname):
        if len(os.listdir(os.path.split(pathname)[0])) < 1:
            dirList = [pathname, self.parms.series_new_dir]
            commonPrefix = os.path.commonprefix(dirList)
            if not commonPrefix != self.parms.series_new_dir:
                os.rmdir(os.path.split(pathname)[0])

    def ignored(self, name):
        """ Check for ignored pathnames.
        """
        return any(fnmatch.fnmatch(name.lower(), pattern) for pattern in self.parms.exclude_list)

    def formatEpisodeNumbers(self, series):
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
            fmt_epno = self.parms.FileNames['episode_single'] % epno[0]
        else:
            fmt_epno = self.parms.FileNames['episode_separator'].join(
                self.parms.FileNames['episode_single'] % x for x in epno)

        return fmt_epno, epno

    def cleanRegexedSeriesName(self, seriesname):
        """Cleans up series name by removing any . and _
        characters, along with any trailing hyphens.

        Is basically equivalent to replacing all _ and . with a
        space, but handles decimal numbers in string, for example:

        >>> cleanRegexedSeriesName("an.example.1.0.test")
        'an example 1.0 test'
        >>> cleanRegexedSeriesName("an_example_1.0_test")
        'an example 1.0 test'
        """
        seriesname = re.sub("(\D)[.](\D)", "\\1 \\2", seriesname)
        seriesname = re.sub("(\D)[.]", "\\1 ", seriesname)
        seriesname = re.sub("[.](\D)", " \\1", seriesname)
        seriesname = seriesname.replace("_", " ")
        seriesname = re.sub("-$", "", seriesname)
        suffix = self.check_suffix.match(seriesname.rstrip())
        if suffix:
            seriesname = '%s (%s)' % (suffix.group('seriesname'), suffix.group('year').upper())
        return seriesname.strip()

    def formatEpisodeName(self, epdata, join_with):
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

        if len(names) == 0:
            return "NOT FOUND IN TVDB"

        if len(names) == 1:
            logger.debug("Episode Name: %s" % (names[0]))
            return names[0]

        found_names = []
        numbers = []

        for cname in names:
            number = re.match("(.*) \(([0-9]+)\)$", cname)
            if number:
                epname, epno = number.group(1), number.group(2)
                if len(found_names) > 0 and epname not in found_names:
                    logger.debug("Episode Name: %s" % (join_with.join(names)))
                    return join_with.join(names)
                found_names.append(epname)
                numbers.append(int(epno))
            else:
                # An episode didn't match
                logger.debug("Episode Name: %s" % (join_with.join(names)))
                return join_with.join(names)

        names = []
        start, end = min(numbers), max(numbers)
        names.append("%s (%d-%d)" % (found_names[0], start, end))
        logger.debug("Episode Name: %s" % (join_with.join(names)))
        return join_with.join(names)

class GetOutOfLoop( Exception ):
    pass

class RenameMovies(object):
    def __init__(self, parms, pathname):
        self.regex_repack = re.compile('^.*(repack|proper).*$', re.IGNORECASE)
        self.regexMovie = re.compile('^(?P<moviename>.+?)[ \._\-](?P<year>[0-9][0-9][0-9][0-9]).*$', re.VERBOSE)
        self.parms = parms
        self.pathname = pathname
        self.processMovie()

    def processMovie(self):
        if os.path.isfile(self.pathname):
            logger.debug("-----------------------------------------------")
            logger.debug("Movie Directory: %s" % os.path.split(self.pathname)[0])
            logger.debug("Movie Filename:  %s" % os.path.split(self.pathname)[1])
            self.RenameMovie(self.pathname)
        elif os.path.isdir(self.pathname):
            for root, dirs, files in os.walk(os.path.abspath(self.pathname),followlinks=False):
                for dir in dirs[:]:
                    if self.ignored(dir):
                        logger.debug("Ignoring %r" % os.path.join(root, dir))
                        dirs.remove(dir)
                files.sort()
                for fname in files:
                    pathname = os.path.join(root, fname)
                    logger.debug("-----------------------------------------------")
                    logger.debug("Filename: %s" % pathname)
                    self.RenameMovie(pathname)

    def RenameMovie(self, pathname):
        match  = self.regexMovie.search(os.path.split(pathname)[1])
        if match:
            moviename = self.cleanRegexedMovieName(match.group('moviename'))
            year = match.group('year')
            ext = os.path.splitext(pathname)[1]
            NewDir = '%s (%s)' % (moviename, year)
            NewName = '%s (%s)%s' % (moviename, year, ext)
            fqNewName = os.path.join(os.path.split(self.parms.movies_dir)[0], os.path.join(NewDir, NewName))
            repack  = self.regex_repack.search(pathname)
            if os.path.exists(fqNewName):
                if repack:
                    os.remove(fqNewName)
                elif filecmp.cmp(fqNewName, pathname):
                    logger.info("Deleting %r, already at destination!" % (os.path.split(pathname)[1],))
                    os.remove(pathname)
                    if os.path.split(pathname)[0] != self.parms.movies_new_dir:
                        if len(os.listdir(os.path.split(pathname)[0])) < 1:
                            os.rmdir(os.path.split(pathname)[0])
                    return

            logger.info('Renaming Movie: %s to %s' % (os.path.basename(pathname), NewName))
            try:
                if not os.path.exists(os.path.split(fqNewName)[0]):
                    os.makedirs(os.path.split(fqNewName)[0])
                    if os.getgid() == 0:
                        os.chown(os.path.split(fqNewName)[0], 1000, 100)
                os.rename(pathname, fqNewName)
                logger.info("Successfully Renamed: %s" % fqNewName)
            except OSError, exc:
                logger.error("Skipping, Unable to Rename File: %s" % pathname)
                logger.error("Unexpected error: %s" % exc)

            if os.path.split(pathname)[0] != self.parms.movies_new_dir:
                if len(os.listdir(os.path.split(pathname)[0])) < 1:
                    os.rmdir(os.path.split(pathname)[0])

    def ignored(self, name):
        """ Check for ignored pathnames.
        """
        return any(fnmatch.fnmatch(name.lower(), pattern) for pattern in self.parms.exclude_list)

    def cleanRegexedMovieName(self, moviename):
        """Cleans up name by removing any . and _
        characters, along with any trailing hyphens.
        """
        moviename = re.sub("(\D)[.](\D)", "\\1 \\2", moviename)
        moviename = re.sub("(\D)[.]", "\\1 ", moviename)
        moviename = re.sub("[.](\D)", " \\1", moviename)
        moviename = moviename.replace("_", " ")
        moviename = re.sub("-$", "", moviename)
        return moviename.strip()

if __name__ == "__main__":
    import logging.handlers
    from optparse import OptionParser, OptionGroup

    PgmDir        = os.path.dirname(__file__)
    HomeDir     = os.path.expanduser('~')
    ConfigDir    = os.path.join(HomeDir, '.config')
    LogDir        = os.path.join(HomeDir, 'log')
    DataDir     = os.path.join(HomeDir, __pgmname__)

    # Set up a specific logger with our desired output level
    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s - %(message)s")
    logger.setLevel(0)
    _console = logging.StreamHandler()
    _console.setLevel(INFO)
    _console.setFormatter(formatter)
    logger.addHandler(_console)
    _main_log = logging.handlers.TimedRotatingFileHandler(os.path.join(LogDir, '%s.log' % __pgmname__), when='midnight', backupCount=7)
    _main_log.setLevel(VERBOSE)
    _main_log.setFormatter(formatter)
    logger.addHandler(_main_log)

    parms = GetConfig()

    parser = OptionParser(
        "%prog [options] [<pathname>]",
        version="%prog " + __version__)

    group = OptionGroup(parser, "Logging Levels:")
    group.add_option("--loglevel", dest="loglevel",
        action="store", type="choice", default="INFO",
        choices=['CRITICAL' ,'ERROR', 'WARNING', 'INFO', 'VERBOSE', 'DEBUG', 'TRACE'],
        help="Specify by name the Level of logging desired, [CRITICAL|ERROR|WARNING|INFO|VERBOSE|DEBUG|TRACE]")
    group.add_option("-e", "--errors", dest="loglevel",
        action="store_const", const="ERROR",
        help="Limit logging to only include Errors and Critical information")
    group.add_option("-q", "--quiet", dest="loglevel",
        action="store_const", const="WARNING",
        help="Increase logging to add Warning and above information")
    group.add_option("-v", "--verbose", dest="loglevel",
        action="store_const", const="VERBOSE",
        help="Increase logging to add above informational information")
    group.add_option("--debug", dest="loglevel",
        action="store_const", const="DEBUG",
        help="Increase logging to include debug information")
    group.add_option("--trace", dest="loglevel",
        action="store_const", const="TRACE",
        help="Increase logging to include program trace information")
    parser.add_option_group(group)

    options, args = parser.parse_args()
    _console.setLevel(options.loglevel)
    logger.debug("Parsed command line options: %r" % options)
    logger.debug("Parsed arguments: %r" % args)

    reqname = ''
    for i in range(len(args)):
        reqname = '%s %s'% (reqname, args[i])
    reqname = reqname.lstrip().rstrip()
    if len(reqname) == 0:
        logger.info('Missing Scan Starting Point (Input Directory), Using Default: %s' % parms.series_new_dir)
        reqname = parms.series_new_dir

    if not os.path.exists(reqname):
        logger.error('Invalid arguments file or path name not found: %s' % reqname)
        sys.exit(1)

    renameshows = RenameShows(parms, options)
    renameshows.ProcessFile(reqname)

#    dirs = os.listdir(reqname)
#    logger.debug(dirs)
#    for dir in dirs:
#        try:
#            renameshows.ProcessFile(os.path.join(reqname, dir))
#        except (InvalidFilename, EpisodeNotFound), msg:
#            logger.warning(msg)
#        pass

#    RenameMovies(parms, reqname)
