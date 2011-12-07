#!/usr/bin/env python
'''
Purpose:
    Runs path via configured regex, extracting data from groups.
    Returns an Dictionary instance containing extracted data.

Created on Dec 4, 2011
@author: AJ Reynolds

'''

from __future__ import division
from subprocess import Popen, call as Call, PIPE
from logging import INFO, WARNING, ERROR, DEBUG
from daddyvision.common.exceptions import InvalidFilename, RegxSelectionError
import datetime
import logging
import logging.handlers
import os
import re
import tempfile
import time
import sqlite3

__version__ = '$Rev$'
__pgmname__ = 'fileparser'

logging.addLevelName(5, 'TRACE')
logging.addLevelName(15, 'VERBOSE')
log = logging.getLogger()
setattr(log, 'TRACE', lambda *args: log.log(5, *args))
setattr(log, 'VERBOSE', lambda *args: log.log(15, *args))

class FileParser(dict):
    """
    Runs path via configured regex, extracting data from groups.
    Returns an Dictionary instance containing extracted data.
    """
    def __init__(self):
        log.TRACE("FileParser: __init__")

        self.FileDetails = {}
        self.RegxParse = self.GetRegx()
        self.check_suffix = re.compile('^(?P<SeriesName>.+?)[ \._\-](?P<Year>[0-9][0-9][0-9][0-9]|US|us|Us)$', re.VERBOSE)

    def GetFileDetails(self, fq_name):
        log.TRACE("FileParser: GetFileDetails- File: %s" % (fq_name))

        #tODO: Implement logging mod to track module reporting error

        _path, _file_name = os.path.split(fq_name)

        self.RegExNumber = 0
        for _pattern in self.RegxParse:
            self.RegExNumber += 1
            _parse_details = _pattern.match(fq_name)
            if not _parse_details:
                continue
            else:
                break

        if not _parse_details:
            _error_msg = "FileParser: No Matching Regx - Unable to parse Filename: {}".format(fq_name)
            log.TRACE(_error_msg)
            raise InvalidFilename(_error_msg)

        self.LogHeader = 'FileParser-RegEx {}'.format(self.RegExNumber)
        log.VERBOSE('{}: RegEx Matched'.format(self.LogHeader))

        with open('/home/aj/log/fileparse_regx.log', 'a') as tracker:
            tracker.write('RegEx: {} - {}: \n'.format(self.RegExNumber, fq_name))
        tracker.close()

        _parsed_keys = _parse_details.groupdict().keys()

        for _key in _parsed_keys:
            log.VERBOSE("{}: {}".format(_key, _parse_details.group(_key)))

        _air_date = ''

        try:
            errmsg = '{}: Missing Series Name {}'.format(self.LogHeader,_parse_details)
            _series_name = self._get_series_name(_parsed_keys, _parse_details)
            try:
                _season_num = self._get_season_number(_parsed_keys, _parse_details)
                _episode_nums = self._get_episode_numbers(_parsed_keys, _parse_details)
            except InvalidFilename as errmsg:
                _air_date = self._get_date_aired(_parsed_keys, _parse_details)
        except InvalidFilename as errmsg:
            log.TRACE('{errmsg} Filename: {fq_name}'.format(errmsg, fq_name))
            raise RegxSelectionError('{errmsg} Filename: {fq_name}'.format(errmsg, fq_name))

        if 'Ext' in _parsed_keys:
            _ext = _parse_details.group('Ext')
        elif _file_name[-4] == '.':
            _ext = _file_name[-4:]
            log.debug('{}: Parse Failed to Locate Extension Using: {}'.format(self.LogHeader, _ext))
        else:
            log.TRACE('{}: Unable to Identify Extension for Filename: {}'.format(self.LogHeader, fq_name))
            raise RegxSelectionError('{}: Unable to Identify Extension for Filename: {}'.format(self.LogHeader, fq_name))

        self.File_Details = {}
        self.File_Details['FileName'] = fq_name
        self.File_Details['SeriesName'] = _series_name
        self.File_Details['Ext'] = _ext
#        self.File_Details['BaseDir'] = '/mnt/TV/Series'

        if _air_date:
            self.File_Details['AirDate'] = _air_date
        else:
            self.File_Details['SeasonNum'] = _season_num
            self.File_Details['EpisodeNums'] = _episode_nums

        log.TRACE('{}: File Details Found: {}'.format(self.LogHeader, self.File_Details))

        return self.File_Details

    def _get_series_name(self, _parsed_keys, _parse_details):
        log.TRACE("{}: _get_series_name: {} {}".format(self.LogHeader, _parsed_keys, _parse_details))

        if 'SeriesName' in _parsed_keys and _parse_details.group('SeriesName') != None:
            _series_name = _parse_details.group('SeriesName')
        else:
            raise InvalidFilename('{}: Parse Did Not Find Series Name: {1}'.format(self.LogHeader, _parsed_keys))

        '''
        Cleans up series name by removing any . and _
        characters, along with any trailing hyphens.
        '''
        _series_name = re.sub("(\D)[.](\D)", "\\1 \\2", _series_name)
        _series_name = re.sub("(\D)[.]", "\\1 ", _series_name)
        _series_name = re.sub("[.](\D)", " \\1", _series_name)
        _series_name = _series_name.replace("_", " ")
        _series_name = re.sub("-$", "", _series_name)
        _suffix = self.check_suffix.match(_series_name.rstrip())

        if _suffix:
            _series_name = '%s (%s)' % (_suffix.group('SeriesName'), _suffix.group('Year').upper())

        log.TRACE('{}: Series Name: {}'.format(self.LogHeader, _series_name.strip()))

        return _series_name.strip()

    def _get_season_number(self, _parsed_keys, _parse_details):
        log.TRACE("{}: _get_season_number: {} {}".format(self.LogHeader, _parsed_keys, _parse_details))

        if 'SeasonNum' in _parsed_keys:
            _season_num = int(_parse_details.group('SeasonNum'))
        else:
            log.TRACE('{}: No Season / Episode Numbers or Air Date in File Name, Named Groups: {}'.format(self.LogHeader, _parsed_keys))
            raise RegxSelectionError('{}: No Season / Episode Numbers or Air Date in File Name, Named Groups: {}'.format(self.LogHeader, _parsed_keys))

        log.TRACE('{}: Season Number: {}'.format(self.LogHeader, _season_num))

        return _season_num

    def _get_episode_numbers(self, _parsed_keys, _parse_details):
        log.TRACE("{}: _get_episode_numbers: {} {}".format(self.LogHeader, _parsed_keys, _parse_details))

        _episode_list = []
        if 'EpisodeNum1' in _parsed_keys:
            # Multiple episodes, have EpisodeNum1
            for _entry in _parsed_keys:
                _ep_no_match = re.match('EpisodeNum(\d+)', _entry)
                if _ep_no_match:
                    _episode_list.append(int(_parse_details.group(_entry)))
            _episode_numbers = sorted(_episode_list)
        elif 'EpisodeNumStart' in _parsed_keys:
            # Range of episodes, regex specifies start and end number
            _start = int(_parse_details.group('EpisodeNumStart'))
            _end = int(_parse_details.group('EpisodeNumEnd'))
            if _start > _end:
                _start, _end = _end, _start
            _episode_numbers = range(_start, _end + 1)
        elif 'EpisodeNum' in _parsed_keys:
            _episode_numbers = [int(_parse_details.group('EpisodeNum')), ]
        else:
            raise RegxSelectionError(("{}:"
                                   "Regex does not contain episode number group, should "
                                   "contain EpisodeNum, EpisodeNum1-9, or "
                                   "EpisodeNumStart and EpisodeNumEnd\n {}"
                                   ).format(self.LogHeader, _parsed_keys))

        return _episode_numbers

    def _get_date_aired(self, _parsed_keys, _parse_details):
        log.TRACE("{}: _get_date_aired: {} {}".format(self.LogHeader, _parsed_keys, _parse_details))

        if 'year' in _parsed_keys or 'month' in _parsed_keys or 'day' in _parsed_keys:
            if not all(['year' in _parsed_keys, 'month' in _parsed_keys, 'day' in _parsed_keys]):
                    raise RegxSelectionError("{}: Date-based regex must contain groups 'year', 'month' and 'day', Keys Found {}".format(self.LogHeader, _parsed_keys))

            _air_date = datetime.datetime(int(_parse_details.group('year')),
                                          int(_parse_details.group('month')),
                                          int(_parse_details.group('day')))
            self.FileDetails.append({'AirDate': _air_date})
        else:
            log.debug()
            raise RegxSelectionError('{}: No Season / Episode Numbers or Air Date in File Name, Named Groups: {}'.format(self.LogHeader, _parsed_keys))

    def GetRegx(self):
        log.TRACE("FileParse: GetRegx")

#----------------------------------------------------------------------------------------
        # My Library Standard
        self.RegxParse = []
        self.RegxParse.append(re.compile(
            '''                                     # #1  /xxx/xxx/xxx/series/Season #/E##-E## Title.ext
            ^(/.*/)*                                # Directory
            (?P<SeriesName>.*)                      # Series Name
            (/Season)                               # Season
            [/\._ \-]                               # Sep 1
            (?P<SeasonNum>[0-9]+)                   # Season Number (##)
            (/)                                     # Directory Seperator
            [E|e]                                   # Episode Number (##)
            (?P<EpisodeNum1>[0-9][0-9]+)            # e
            (\-E)                                   # Sep between Episode Numbers1
            (?P<EpisodeNum2>[0-9][0-9]+)            # e
            [/\._ \-]                               # Optional Sep 1
            (?P<EpisodeName>.+)                     # Optional Title
            \.(?P<Ext>....?)$                       # extension
            ''',
             re.X|re.I))

        self.RegxParse.append(re.compile(
            '''                                     # #2 /xxx/xxx/xxx/series/Season #/E## Title.ext
            ^(/.*/)*                                # Directory
            (?P<SeriesName>.*)                      # Series Name
            (/Season)                               # Season
            [/\._ \-]                               # Sep 1
            (?P<SeasonNum>[0-9]+)                   # Season Number (##)
            (/)                                     # Directory Seperator
            [E|e]                                   # Episode Number (##)
            (?P<EpisodeNum>[0-9][0-9]+)             # e
            [/\._ \-]?                              # Optional Sep 1
            (?P<EpisodeName>.+)?                    # Optional Title
            \.(?P<Ext>....?)$                       # extension
            ''',
             re.X|re.I))

#----------------------------------------------------------------------------------------
#        # Multiepisode
#        self.RegxParse.append(re.compile(
#            '''                                     # RegEx 3
#            ^(/.*/)?                                # Optional Directory
#            (?P<SeriesName>.*)                      # Series Name
#            [/\._ \-]                               # Sep 1
#            [s|season]                              # s|season
#            [/\._ \-]?                              # Optional Sep 1
#            (?P<SeasonNum>[0-9]+)                   # Season Number (##)
#            [/\._ \-]?                              # Sep 1
#            [E|e]                                   # e
#            (?P<EpisodeNumStart>[0-9][0-9]+)        # Starting Episode Number (##)
#            [\.\- ]?                                # Sep 1
#            [e]?                                    # Optional e
#            (?P<EpisodeNumEnd>[0-9][0-9]+)          # Ending Episode Number (##)
#            [\.\- ]                                 # Sep 1
#            (?P<EpisodeName>.*)                     # Optional Title
#            \.(?P<Ext>....?)$                       # Extension
#            ''',
#            re.X|re.I))
#
#        self.RegxParse.append(re.compile(
#            '''                                     # RegEx 4
#            ^(/.*/)?                                # Optional Directory
#            (?P<SeriesName>.*)                      # Series Name
#            [/\._ \-]                               # Sep 1
#            [s|season]                              # s|season
#            [/\._ \-]?                              # Optional Sep 1
#            (?P<SeasonNum>[0-9]+)                   # Season Number (##)
#            [/\._ \-]?                              # Optional Sep 1
#            [E|e]                                   # e
#            (?P<EpisodeNum>[0-9][0-9]+)             # Episode Number (##)
#            [/\._ \-]?                              # Optional Sep 1
#            (?P<EpisodeName>.*)                     # Optional Title
#            \.(?P<Ext>....?)$                       # Extension
#            ''',
#            re.X|re.I))
#
#        self.RegxParse.append(re.compile(
#            '''                                    # foo s01e23 s01e24 s01e25 *
#            ^((?P<SeriesName>.+?)[ \._\-])?        # show name
#            [Ss](?P<SeasonNum>[0-9][0-9]+)         # s01
#            [\.\- ]?                               # separator
#            [Ee](?P<EpisodeNumStart>[0-9][0-9]+)   # first e23
#            ([\.\- ]+                              # separator
#            [Ss](?P<SeasonNum>[0-9][0-9]+)         # s01
#            [\.\- ]?                               # separator
#            [Ee][0-9][0-9]+)*                      # e24 etc (middle groups)
#            ([\.\- ]+                              # separator
#            [Ss](?P<SeasonNum>[0-9][0-9]+)         # s01
#            [\.\- ]?                               # separator
#            [Ee](?P<EpisodeNumEnd>[0-9][0-9]+))    # final episode number
#            [^\/]*$
#            ''',
#            re.X|re.I))
#
#        self.RegxParse.append(re.compile(
#            '''                                      # foo.s01e23e24*
#            ^((?P<SeriesName>.+?)[ \._\-])?          # show name
#            [Ss](?P<SeasonNum>[0-9][0-9]+)           # s01
#            [\.\- ]?                                 # separator
#            [Ee](?P<EpisodeNumStart>[0-9][0-9]+)     # first e23
#            ([\.\- ]?                                # separator
#            [Ee][0-9][0-9]+)*                        # e24e25 etc
#            [\.\- ]?[Ee](?P<EpisodeNumEnd>[0-9][0-9]+) # final episode num
#            [^\/]*$
#            ''',
#            re.X|re.I))
#
#        self.RegxParse.append(re.compile(
#            '''                                      # foo.1x23 1x24 1x25
#            ^((?P<SeriesName>.+?)[ \._\-])?          # show name
#            (?P<SeasonNum>[0-9]+)                    # first season number (1)
#            [xX](?P<EpisodeNumStart>[0-9][0-9]+)     # first episode (x23)
#            ([ \._\-]+                               # separator
#            (?P=SeasonNum)                           # more season numbers (1)
#            [xX][0-9][0-9]+)*                        # more episode numbers (x24)
#            ([ \._\-]+                               # separator
#            (?P=SeasonNum)                           # last season number (1)
#            [xX](?P<EpisodeNumEnd>[0-9][0-9]+))      # last episode number (x25)
#            [^\/]*$
#            ''',
#            re.X|re.I))
#
#        self.RegxParse.append(re.compile(
#            '''                                      # foo.1x23x24*
#            ^((?P<SeriesName>.+?)[ \._\-])?          # show name
#            (?P<SeasonNum>[0-9]+)                    # 1
#            [xX](?P<EpisodeNumStart>[0-9][0-9]+)     # first x23
#            ([xX][0-9][0-9]+)*                       # x24x25 etc
#            [xX](?P<EpisodeNumEnd>[0-9][0-9]+)       # final episode num
#            [^\/]*$
#            ''',
#            re.X|re.I))
#
#        self.RegxParse.append(re.compile(
#            '''                                      # foo.s01e23-24*
#            ^((?P<SeriesName>.+?)[ \._\-])?          # show name
#            [Ss](?P<SeasonNum>[0-9][0-9]+)           # s01
#            [\.\- ]?                                 # separator
#            [Ee](?P<EpisodeNumStart>[0-9][0-9]+)     # first e23
#            (                                        # -24 etc
#                    [\-]
#                    [Ee]?[0-9][0-9]+
#            )*
#                    [\-]                                # separator
#                    [Ee]?(?P<EpisodeNumEnd>[0-9][0-9]+) # final episode num
#            [\.\- ]                                  # must have a separator (prevents s01e01-720p from being 720 episodes)
#            [^\/]*$
#            ''',
#            re.X|re.I))
#
#        self.RegxParse.append(re.compile(
#            '''                                      # foo.1x23-24*
#            ^((?P<SeriesName>.+?)[ \._\-])?          # show name
#            (?P<SeasonNum>[0-9]+)                    # 1
#            [xX](?P<EpisodeNumStart>[0-9][0-9]+)     # first x23
#            (                                        # -24 etc
#                    [\-][0-9][0-9]+
#            )*
#                    [\-]                             # separator
#                    (?P<EpisodeNumEnd>[0-9][0-9]+)   # final episode num
#            ([\.\- ].*                               # must have a separator (prevents 1x01-720p from being 720 episodes)
#            |
#            $)
#            ''',
#            re.X|re.I))
#
#        self.RegxParse.append(re.compile(
#            '''                                      # foo.[1x09-11]*
#            ^(?P<SeriesName>.+?)[ \._\-]             # show name and padding
#            \[                                       # [
#                    ?(?P<SeasonNum>[0-9]+)           # season
#            [xX]                                     # x
#                    (?P<EpisodeNumStart>[0-9][0-9]+) # episode
#                    (- [0-9][0-9]+)*
#            -                                        # -
#                    (?P<EpisodeNumEnd>[0-9][0-9]+)   # episode
#            \]                                       # \]
#            [^\\/]*$
#            ''',
#            re.X|re.I))
#
#        self.RegxParse.append(re.compile(
#            '''                                      # foo.s0101, foo.0201
#            ^(?P<SeriesName>.+?)[ \._\-]
#            [Ss](?P<SeasonNum>[0-9]{2})
#            [\.\- ]?
#            (?P<EpisodeNum>[0-9]{2})
#            [^0-9]*$
#            ''',
#            re.X|re.I))
#
#        self.RegxParse.append(re.compile(
#            '''                                      # foo.s01.e01, foo.s01_e01
#            ^((?P<SeriesName>.+?)[ \._\-])?
#            \[?
#            [Ss](?P<SeasonNum>[0-9][0-9]+)[\.\- ]?
#            [Ee]?(?P<EpisodeNum>[0-9][0-9]+)
#            \]?
#            [^\\/]*$
#            ''',
#            re.X|re.I))
#
#        self.RegxParse.append(re.compile(
#            '''                                      # Foo - S2 E 02 - etc
#            ^(?P<SeriesName>.+?)[ ]?[ \._\-][ ]?
#            [Ss](?P<SeasonNum>[0-9]+)[\.\- ]?
#            [Ee]?[ ]?(?P<EpisodeNum>[0-9][0-9]+)
#            [^\\/]*$
#            ''',
#            re.X|re.I))

#----------------------------------------------------------------------------------------
        #Groups
        self.RegxParse.append(re.compile(
            '''                                     # # 3  RegEx 1
            ^(/.*/)?                                # Optional Directory
            ({.*})                                  # { GROUP NAME }
            [\._ \-]?[\._ \-]?[\._ \-]?             # Optional Sep 1-3
            (?P<SeriesName>.*)                      # Series Name
            [/\._ \-]                               # Sep 1
            [S|s]                                   # s|S
            [/\._ \-]?                              # Optional Sep 1
            (?P<SeasonNum>[0-9]+)                   # Season Number (##)
            [/\._ \-]?                              # Optional Sep 1
            [E|e]                                   # Episode Number (##)
            (?P<EpisodeNum>[0-9][0-9]+)             # e
            [/\._ \-]?                              # Optional Sep 1
            (?P<EpisodeName>.+)?                    # Optional Title
            \.(?P<Ext>....?)$                       # extension
            ''',
            re.X|re.I))

        self.RegxParse.append(re.compile(
            '''                                     # RegEx 4
            ^(/.*/)?                                # Optional Directory
            (\[.*\])                                # { GROUP NAME }
            [\._ \-]?[\._ \-]?[\._ \-]?             # Optional Sep 1-3
            (?P<SeriesName>.*)                      # Series Name
            [/\._ \-]                               # Sep 1
            [S|s]                                   # s|S
            [/\._ \-]?                              # Optional Sep 1
            (?P<SeasonNum>[0-9]+)                   # Season Number (##)
            [/\._ \-]?                              # Optional Sep 1
            [E|e]                                   # e
            (?P<EpisodeNum>[0-9][0-9]+)             # Episode Number (##)
            [/\._ \-]?                              # Optional Sep 1
            (?P<EpisodeName>.+)?                    # Optional Title
            \.(?P<Ext>....?)$                       # Extension
            ''',
            re.X|re.I))

        self.RegxParse.append(re.compile(
            '''                                     # # 5  RegEx 1
            ^(/.*/)?                                # Optional Directory
            ({.*})                                  # { GROUP NAME }
            [\._ \-]?[\._ \-]?[\._ \-]?             # Optional Sep 0-3
            (?P<SeriesName>.*)                      # Series Name
            [/\._ \-]+                              # Sep 1
            [/\._ \-]?                              # Optional Sep 1
            (?P<SeasonNum>[0-9]+)                   # Season Number (##)
            [/\._ \-]?                              # Optional Sep 1
            [E|e|x|X]?                               #
            (?P<EpisodeNum>[0-9][0-9]+)             # Episode Number (##)
            [/\._ \-]                               # Sep 1
            (?P<EpisodeName>.+)?                    # Optional Title
            \.(?P<Ext>....?)$                       # extension
            ''',
            re.X|re.I))

        self.RegxParse.append(re.compile(
            '''                                     # RegEx 6
            ^(/.*/)?                                # Optional Directory
            (\[.*\])                                # { GROUP NAME }
            [\._ \-]?[\._ \-]?[\._ \-]?             # Optional Sep 0-3
            (?P<SeriesName>.*)                      # Series Name
            [/\._ \-]                               # Sep 1
            (?P<SeasonNum>[0-9]+)                   # Season Number (##)
            [/\._ \-]?                              # Optional Sep 1
            [E|e|x|X]?                               # e
            (?P<EpisodeNum>[0-9][0-9]+)             # Episode Number (##)
            [/\._ \-]+                              # Optional Sep 1
            (?P<EpisodeName>.+)?                    # Optional Title
            \.(?P<Ext>....?)$                       # Extension
            ''',
            re.X|re.I))

#----------------------------------------------------------------------------------------
        #Single Episode with S or Season
        self.RegxParse.append(re.compile(
            '''                                     # RegEx 7
            ^(/.*/)?                                # Optional Directory
            (?P<SeriesName>.*)                      # Series Name
            [/\._ \-]                               # Sep 1
            [s|season]                              # s|season
            [/\._ \-]?                              # Optional Sep 1
            (?P<SeasonNum>[0-9]+)                   # Season Number (##)
            [/\._ \-]?                              # Optional Sep 1
            (hdtv)?                                 # Optional "hdtv"
            [/\._ \-]?                              # Optional Sep 1
            [E|e]                                   # e
            (?P<EpisodeNum>[0-9][0-9]+)             # Episode Number (##)
            [/\._ \-]?                              # Optional Sep 1
            (?P<EpisodeName>.*)                     # Optional Title
            \.(?P<Ext>....?)$                       # Extension
            ''',
            re.X|re.I))

#----------------------------------------------------------------------------------------
        #Single Episode No S or Season
        self.RegxParse.append(re.compile(
            '''                                    # #8  foo ##e|x##
            ^(/.*/)?                               # Optional Directory
            (?P<SeriesName>.*?)                    # Series Name
            [/\._ \-]+                             # Sep 1 or More
            (?P<SeasonNum>[0-9][0-9])              # Season Number (##)
            [e|x]?                                  # e|x
            (?P<EpisodeNum>[0-9][0-9]+)            # Episode Number(##)
            [/\._ \-]*                             # Optional Sep 1 or more
            (?P<EpisodeName>.+)?                   # Optional Title
            \.(?P<Ext>....?)$                      # Extension
            ''',
            re.X|re.I))

        self.RegxParse.append(re.compile(
            '''                                    # #9  foo #e|x##
            ^(/.*/)?                               # Optional Directory
            (?P<SeriesName>.*?)                    # Series Name
            [/\._ \-]+                             # Sep
            (?P<SeasonNum>[0-9])                   # Season Number (#)
            [e|x]?                                  # Optional e|x
            (?P<EpisodeNum>[0-9][0-9]+)            # Episode Number(##)
            [/\._ \-]?                             # Optional Sep 1
            (?P<EpisodeName>.+)?                   # Optional Title
            \.(?P<Ext>....?)$                      # Extension
            ''',
            re.X|re.I))

#        self.RegxParse.append(re.compile(
#            '''                                      # foo.1x09*
#            ^((?P<SeriesName>.+?)[ \._\-])?          # show name and padding
#            \[?                                      # [ optional
#            (?P<SeasonNum>[0-9]+)                    # season
#            [xX]                                     # x
#            (?P<EpisodeNum>[0-9][0-9]+)              # episode
#            \]?                                      # ] optional
#            [^\\/]*$
#            ''',
#            re.X|re.I))

#        self.RegxParse.append(re.compile(
#            '''                                      # foo.103*
#            ^(?P<SeriesName>.+)[ \._\-]
#            (?P<SeasonNum>[0-9]{1})
#            (?P<EpisodeNum>[0-9]{2})
#            [\._ -][^\\/]*$
#            ''',
#            re.X|re.I))
#
#        self.RegxParse.append(re.compile(
#            '''                                      # foo.0103*
#            ^(?P<SeriesName>.+)[ \._\-]
#            (?P<SeasonNum>[0-9]{2})
#            (?P<EpisodeNum>[0-9]{2,3})
#            [\._ -][^\\/]*$
#            ''',
#            re.X|re.I))
#
#----------------------------------------------------------------------------------------
        # DATE AIRED
        self.RegxParse.append(re.compile(
            '''                                    # RegEx 10
            ^(/.*/)?                               # Optional Directory
            (?P<SeriesName>.+?)                    # Series name
            [/\._ \-]                              # Sep 1
            (?P<year>\d{4})                        # year (####)
            [ \._\-]                               # Separator .|1
            (?P<month>\d{2})                       # Month (##)
            [ \._\-]                               # separator .|-
            (?P<day>\d{2})                         # Day (##)
            [/\._ \-]?                             # Optional Sep 1
            (?P<EpisodeName>.*)                    # Optional Title
            \.(?P<Ext>....?)$                      # Extension
            ''',
            re.X|re.I))

#------------------------------------------------------------------------------------------
#        # Special Cases
#        self.RegxParse.append(re.compile(
#            '''                                      # Show - Episode 9999 [S 12 - Ep 131] - etc
#            (?P<SeriesName>.+)                       # Showname
#            [ ]-[ ]                                  # -
#            [Ee]pisode[ ]\d+                         # Episode 1234 (ignored)
#            [ ]
#            \[                                       # [
#            [sS][ ]?(?P<SeasonNum>\d+)               # s 12
#            ([ ]|[ ]-[ ]|-)                          # space, or -
#            ([eE]|[eE]p)[ ]?(?P<EpisodeNum>\d+)      # e or ep 12
#            \]                                       # ]
#            .*$                                      # rest of file
#            ''',
#            re.X|re.I))
#
#        self.RegxParse.append(re.compile(
#            '''                                      # show.name.e123.abc
#            ^(?P<SeriesName>.+?)                     # Show name
#            [ \._\-]                                 # Padding
#            (?P<EpisodeNum>[0-9]+)                   # 2
#            of                                       # of
#            [ \._\-]?                                # Padding
#            \d+                                      # 6
#            ([\._ -]|$|[^\\/]*$)                     # More padding, then anything
#            ''',
#            re.X|re.I))
#
#        self.RegxParse.append(re.compile(
#            '''                                      # show.name.e123.abc
#            ^(?P<SeriesName>.+?)                     # Show name
#            [ \._\-]                                 # Padding
#            [Ee](?P<EpisodeNum>[0-9]+)               # E123
#            [\._ -][^\\/]*$                          # More padding, then anything
#            ''',
#            re.X|re.I))

        return self.RegxParse

if __name__ == '__main__':

    from optparse import OptionParser, OptionGroup

    PgmDir = os.path.dirname(__file__)
    HomeDir = os.path.expanduser('~')
    ConfigDirB = os.path.join(HomeDir, '.config')
    ConfigDir = os.path.join(ConfigDirB, 'xbmcsupt')
    LogDir = os.path.join(HomeDir, 'log')
    TEMP_LOC = os.path.join(HomeDir, __pgmname__)

    log.setLevel('TRACE')
    _formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)-8s - %(message)s")

    _mem_log = logging.handlers.MemoryHandler(1000 * 1000, 100)
    _mem_log.setLevel(DEBUG)
    _mem_log.setFormatter(_formatter)
    log.addHandler(_mem_log)

    _console = logging.StreamHandler()
    _console.setLevel(INFO)
    _console.setFormatter(_formatter)
    log.addHandler(_console)

#    _main_log = logging.handlers.RotatingFileHandler(os.path.join(LogDir, '%s.log' % __pgmname__), maxBytes=0, backupCount=7)
#    _main_log.setLevel(DEBUG)
#    _main_log.setFormatter(_formatter)
#    log.addHandler(_main_log)
#    _main_log.doRollover()
#
#    _error_log = logging.handlers.RotatingFileHandler(os.path.join(LogDir, '%s_error.log' % __pgmname__), maxBytes=0, backupCount=7)
#    _error_log.setLevel(ERROR)
#    _error_log.setFormatter(_formatter2)
#    log.addHandler(_error_log)
#    _error_log.doRollover()

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
        help="Limit logging to only include Warning, Errors, and Critical information")
    group.add_option("-v", "--verbose", dest="loglevel",
        action="store_const", const="VERBOSE",
        help="increase logging to include informational information")
    group.add_option("--debug", dest="loglevel",
        action="store_const", const="DEBUG",
        help="increase logging to include debug information")
    group.add_option("--trace", dest="loglevel",
        action="store_const", const="TRACE",
        help="increase logging to include program trace information")
    parser.add_option_group(group)

    options, args = parser.parse_args()
    _console.setLevel(options.loglevel)

    log.debug("Parsed command line options: %r" % options)
    log.debug("Parsed arguments: %r" % args)

    _my_parser = FileParser()
    if len(args) > 0:
        _answer = _my_parser.GetFileDetails(args[0])
    else:
        _answer = _my_parser.GetFileDetails()

    print
    print _answer