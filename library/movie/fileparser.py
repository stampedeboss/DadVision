#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Purpose:
     Parse a filename that is passed to it and return the movie name and year if available.
'''
from __future__ import division
from library import Library
from common.exceptions import InvalidFilename, RegxSelectionError
from common import logger
import logging
import fnmatch
import os
import re

__pgmname__ = 'library.movie.fileparser'
__version__ = '@version: $Rev$'

__author__ = "@author: AJ Reynolds"
__email__ = "@contact: stampedeboss@gmail.com"
__copyright__ = "@copyright: Copyright 2011, AJ Reynolds"
__license__ = "@license: GPL"

__maintainer__ = "@organization: AJ Reynolds"
__status__ = "@status: Development"
__credits__ = []

log = logging.getLogger(__pgmname__)

class FileParser(Library):
    """
    Runs path via configured regex, extracting data from groups.
    Returns an Dictionary instance containing extracted data.
    """

    def __init__(self):
        log.trace("Entering: FileParser.__init__")

        super(FileParser, self).__init__()

        self.library = super(FileParser, self)

        self.regex_repack = re.compile('^.*(repack|proper).*$', re.IGNORECASE)
        self.RegxParse = self.GetRegx()

    def getFileDetails(self, fq_name):
        log.trace("GetFileDetails: File: %s" % (fq_name))

        _path, _file_name = os.path.split(fq_name)

        self.RegExNumber = 0
        for _pattern in self.RegxParse:
            self.RegExNumber += 1
            _parse_details = _pattern.match(_file_name)
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
            log.verbose("{}: {}".format(_key, _parse_details.group(_key)))

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
            self.File_Details['Ext'] = _parse_details.group('Ext').lower()
        elif _file_name[-4] == '.':
            self.File_Details['Ext'] = _file_name[-4:].lower()
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
#        _movie_name = _movie_name.replace("(", "")
#        _movie_name = _movie_name.replace("[", "")
#        _movie_name = _movie_name.replace(")", "")
#        _movie_name = _movie_name.replace("]", "")
        _movie_name = re.sub("-$", "", _movie_name)

        _word_list = _movie_name.split()
        _title = []
        for _word in _word_list:
            if self._ignored(_word):
                break
            else:
                if _word[0:1] in ['(', '[', '{']:
                    _word = '(' + _word[1:].capitalize()
                    _title.append(_word)
                else:
                    _title.append(_word.capitalize())

        _movie_name = " ".join(_title)
        _movie_name = _movie_name.replace("3d", "3D")

        _movie_name = re.sub("(^|\s)(\S)", self._repl_func, _movie_name)

        log.trace('{}: Movie Name: {}'.format(self.LogHeader, _movie_name.strip()))

        return _movie_name.strip()

    def _repl_func(self, m):
        """process regular expression match groups for word upper-casing problem"""
        return m.group(1) + m.group(2).upper()

    def GetRegx(self):
        log.trace("FileParse: GetRegx")

        RegxParse = []
        RegxParse.append(re.compile(
            '''                                     # RegEx 1  YEAR First
            ^(?P<Year>(19|20)[0-9][0-9])
            [\._ \-][\._ \-]?[\._ \-]?
            (?P<MovieName>.*)
            [\._ \-]?
            (?P<Keywords>.+)?
            \.(?P<Ext>....?)$
            ''',
            re.X | re.I))

        RegxParse.append(re.compile(
            '''                                     # RegEx 2  COLLECTION NAME
            ^(.*?[\._ ]\-[\._ ])
            (?P<MovieName>.*)
            [/\._ \-]
            [\(\[]?
            (?P<Year>(19|20|21)[0-9][0-9])
            [\)\]]?
            [/\._ \-]?
            (?P<Keywords>.+)?
            \.(?P<Ext>....?)$
            ''',
            re.X | re.I))

        RegxParse.append(re.compile(
            '''                                     # RegEx 2  COLLECTION NAME
            ^(.*?[\._ ]\-[\._ ])
            (?P<MovieName>.*)
            [/\._ \-]?
            (?P<Keywords>.+)?
            \.(?P<Ext>....?)$
            ''',
            re.X | re.I))

        RegxParse.append(re.compile(
            '''                                     # RegEx 3  GROUP NAME
            ^[({.*})?|(\[.*\])]
            [\._ \-]?[\._ \-][\._ \-]?              # Optional Sep 1-3
            (?P<MovieName>.*?)
            [\._ \-][\(\[]?
            (?P<Year>(19|20)[0-9][0-9])
            [\)\]]?[\._ \-]?
            (?P<Keywords>.+)?
            \.(?P<Ext>....?)$
            ''',
            re.X | re.I))

        RegxParse.append(re.compile(
            '''                                      # RegEx 4  YEAR
            (?P<MovieName>.*?)
            [\._ \-][\(\[]?
            (?P<Year>(19|20)[0-9][0-9])
            [\)\]]?[\._ \-]?
            (?P<Keywords>.+)?
            \.(?P<Ext>....?)$
            ''',
            re.X | re.I))

        RegxParse.append(re.compile(
            '''                                     # RegEx 5  TRAILER
            ^(?P<MovieName>.*?)                      # Movie Name
            [/\._ \-]?                              # Sep 1
            (?P<Trailer>.trailer)                  # trailer indicator
            \.(?P<Ext>....?)$                       # extension
            ''',
            re.X | re.I))

        RegxParse.append(re.compile(
            '''                                     # RegEx 6  ALL OTHERS
            ^(?P<MovieName>.*?)                      # Movie Name
            \.(?P<Ext>....?)$                       # extension
            ''',
            re.X | re.I))

        return RegxParse

    def _ignored(self, name):
        """ Check for ignored pathnames.
        """
        return any(fnmatch.fnmatch(name.lower(), pattern) for pattern in self.settings.MovieGlob2)

if __name__ == '__main__':

    import sys

    logger.initialize()

    library = FileParser()
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

    _lib_paths = library.args.library

    _lib_path = _lib_paths[0]
    _answer = library.getFileDetails(_lib_path)

    print
    print _answer
