#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Purpose:
     Parse a filename that is passed to it and return the movie name and year if available.

'''
from __future__ import division
from logging import INFO, WARNING, ERROR, DEBUG
from daddyvision.common.exceptions import InvalidFilename, RegxSelectionError
from daddyvision.common import logger
import datetime
import logging
import os
import re
import sys
import tempfile
import time
import sqlite3

__pgmname__ = 'movies.fileparser'
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

TRACE = 5
VERBOSE = 15

class FileParser(object):
    """
    Runs path via configured regex, extracting data from groups.
    Returns an Dictionary instance containing extracted data.
    """

    def __init__(self, config):
        log.trace("Entering: __init__")

        self.config = config

        self.FileDetails = {}
        self.regex_repack = re.compile('^.*(repack|proper).*$', re.IGNORECASE)
        self.RegxParse = self.GetRegx()

#        @TODO: Eventually move MovieGlob to settings
        self.MovieGlob = ["1080p", "720p", "bluray", "x264", "x264-refined", "h264", "ac3", "ac-3",
                          "uncut", "director", "directors", "director's", "unrated", "extended", "retail",
                          "repack", "proper", "480p", "dvdr", "dvdrip", "brrip", "bdrip", "hdtv", "ntsc", "pal",
                          "r5", "br-screener", "screener", "tsxvid", "xvid", "divxnl", "divx", "scr", "hq",
                          "pdvd-rip", "pdvd", "pdv", "Predvd", "pre-dvd", "dvd", "ppvrip", "pdtv", "cam",
                          "telesync", "telecine", "WorkPrint", "vhs", "cvcd", "vcd", "webrip", "br-scr",
                          "ts", "ws", "nl", "nlt", "cn ", "tc ", "extratorrent", "2lions", " vostfr", "fxm",
                          "subs", "nl Subs", "french", "english", "spanish", "ita ", "italia",
                          "hindi", "german", "eng","swesub", ]


    def getFileDetails(self, fq_name):
        log.trace("GetFileDetails: File: %s" % (fq_name))

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
            _error_msg = "No Matching Regx - Unable to parse Filename: {}".format(fq_name)
            log.trace(_error_msg)
            raise InvalidFilename('FileParser:' + _error_msg)

        self.LogHeader = 'RegEx {}'.format(self.RegExNumber)
        log.verbose('{}: RegEx Matched'.format(self.LogHeader))

        _parsed_keys = _parse_details.groupdict().keys()
        for _key in _parsed_keys:
            log.debug("{}: {}".format(_key, _parse_details.group(_key)))

        self.File_Details = {}
        self.File_Details['FileName'] = fq_name

        try:
            if 'MovieName' in _parsed_keys:
                self.File_Details['MovieName'] = self._get_movie_name(_parsed_keys, _parse_details)
        except InvalidFilename as errmsg:
            log.trace('{errmsg} Filename: {fq_name}'.format(errmsg, fq_name))
            raise RegxSelectionError('FileParser: {errmsg} Filename: {fq_name}'.format(errmsg, fq_name))

        if 'Year' in _parsed_keys:
            self.File_Details['Year'] = _parse_details.group('Year')
            
        if 'Trailer' in _parsed_keys and _parse_details.group('Trailer') != None:
            self.File_Details['Trailer'] = True

        if 'Ext' in _parsed_keys:
            self.File_Details['Ext'] = _parse_details.group('Ext')
        elif _file_name[-4] == '.':
            self.File_Details['Ext'] = _file_name[-4:]
            log.debug('{}: Parse Failed to Locate Extension Using: {}'.format(self.LogHeader, self.File_Details['Ext']))
        else:
            log.trace('{}: Unable to Identify Extension for Filename: {}'.format(self.LogHeader, fq_name))
            raise RegxSelectionError('FileParser: {}: Unable to Identify Extension for Filename: {}'.format(self.LogHeader, fq_name))

        log.trace('{}: File Details Found: {}'.format(self.LogHeader, self.File_Details))

        return self.File_Details

    def _get_movie_name(self, _parsed_keys, _parse_details):
        log.trace("{}: _get_movie_name: {} {!r}".format(self.LogHeader, _parsed_keys, _parse_details))

        if 'MovieName' in _parsed_keys and _parse_details.group('MovieName') != None:
            _movie_name = _parse_details.group('MovieName')
        else:
            raise InvalidFilename('FileParser: {}: Parse Did Not Find Movie Name: {1}'.format(self.LogHeader, _parsed_keys))

        '''
        Cleans up movie name by removing any . and _
        characters, along with any trailing hyphens.
        '''
        _movie_name = re.sub("(\D)[.](\D)", "\\1 \\2", _movie_name)
        _movie_name = re.sub("(\D)[.]", "\\1 ", _movie_name)
        _movie_name = re.sub("[.](\D)", " \\1", _movie_name)
        _movie_name = _movie_name.replace("_", " ")
        _movie_name = re.sub("-$", "", _movie_name)

        _word_list = _movie_name.split()
        _title = []
        for _word in _word_list:
            if _word.lower() in self.MovieGlob:
                break
            else:
                _title.append(_word.capitalize())

        _movie_name = " ".join(_title)

        log.trace('{}: Movie Name: {}'.format(self.LogHeader, _movie_name.strip()))

        return _movie_name.strip()

    def GetRegx(self):
        log.trace("FileParse: GetRegx")

        RegxParse = []
        RegxParse.append(re.compile(
            '''                                     # RegEx 1
            ^(/.*/)?                                # Optional Directory
            [({.*})?|(\[.*\])]?                     # { GROUP NAME }
            [\._ \-]?[\._ \-]?[\._ \-]?             # Optional Sep 1-3
            (?P<MovieName>.*?)                      # Movie Name
            [/\._ \-][\(]?                          # Sep 1
            (?P<Year>[1-2][09][0-9][0-9])
            [\)]?[/\._ \-]                          # Sep 1
            (?P<Keywords>.+)?                       # Optional Title
            \.(?P<Ext>....?)$                       # extension
            ''',
            re.X|re.I))

        RegxParse.append(re.compile(
            '''                                     # RegEx 2
            ^(/.*/)?                                # Optional Directory
            (?P<MovieName>.*?)                      # Movie Name
            [/\._ \-]?                              # Sep 1
            (?P<Trailer>.trailer)?                  # trailer indicator
            \.(?P<Ext>....?)$                       # extension
            ''',
            re.X|re.I))

        return RegxParse

if __name__ == '__main__':

    from daddyvision.common.options import OptionParser, CoreOptionParser
    from daddyvision.common.settings import Settings

    parser = CoreOptionParser()
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

    config = Settings()

    _my_parser = FileParser(config)

    if len(args) > 0:
        _answer = _my_parser.getFileDetails(args[0])
    else:
        log.error('Missing Filename to be processed')
        sys.exit(1)

    print
    print _answer
