#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Purpose:
	Runs path via configured regex, extracting data from groups.
	Returns an Dictionary instance containing extracted data.

Created on Dec 4, 2011
@author: AJ Reynolds

'''

from __future__ import division
from library import Library
from common.exceptions import InvalidFilename, RegxSelectionError, SeasonNotFound, EpisodeNotFound
from common import logger
import datetime
import logging
import os
import re

__pgmname__ = 'library.series.fileparser'
__version__ = '$Rev$'

__author__ = "@author: AJ Reynolds"
__email__ = "@contact: stampedeboss@gmail.com"
__copyright__ = "@copyright: Copyright 2011, AJ Reynolds"
__license__ = "@license: GPL"

__maintainer__ = "@organization: AJ Reynolds"
__status__ = "@status: Development"
__credits__ = []

log = logging.getLogger(__pgmname__)

class FileParser(Library, dict):
	"""
	Runs path via configured regex, extracting data from groups.
	Returns an Dictionary instance containing extracted data.
	"""
	def __init__(self):

		super(FileParser, self).__init__()

		self.RegxParse = self.GetRegx()
		self.check_suffix = re.compile('^(?P<SeriesName>.+?)[ \._\-](?P<Year>[0-9][0-9][0-9][0-9]|US|us|Us)$', re.VERBOSE)
		self.regex_SeriesDir = re.compile('^{}$'.format(self.settings.SeriesDir), re.IGNORECASE)

	def getFileDetails(self, fq_name):
		log.trace("GetFileDetails: File: %s" % (fq_name))

		_path, _file_name = os.path.split(os.path.abspath(fq_name))
		_check_path = _path
		_check_name = _file_name
		_parse_details = None
		while _check_path != os.path.sep:
			_parse_details = self._parse_file_name(_check_name)
			if _parse_details:
				break
			_check_path, _new_subname = os.path.split(_check_path)
			_check_name = os.path.join(_new_subname, _check_name)

		if not _parse_details:
			_error_msg = "No Matching Regx - Unable to parse Filename: {}".format(fq_name)
			log.trace(_error_msg)
			raise InvalidFilename('FileParser:' + _error_msg)

		_parsed_keys = _parse_details.groupdict().keys()
		for _key in _parsed_keys:
			log.debug("{}: {}".format(_key, _parse_details.group(_key)))

		_air_date = ''

		try:
			errmsg = '{}: Missing Series Name {}'.format(self.LogHeader, _parse_details)
			_series_name = self._get_series_name(_parsed_keys, _parse_details)
			try:
				_season_num = self._get_season_number(_parsed_keys, _parse_details)
				errmsg = '{}: Missing Episode Number {}'.format(self.LogHeader, _parse_details)
				_episode_nums = self._get_episode_numbers(_parsed_keys, _parse_details)
			except (SeasonNotFound, EpisodeNotFound) as errmsg:
				errmsg = '{}: Missing Season Number and/or Episode Numbers {}'.format(self.LogHeader, _parse_details)
				_air_date = self._get_date_aired(_parsed_keys, _parse_details)
		except InvalidFilename as errmsg:
			log.trace('{errmsg} Filename: {fq_name}'.format(errmsg, fq_name))
			raise RegxSelectionError('FileParser: {errmsg} Filename: {fq_name}'.format(errmsg, fq_name))

		if 'Ext' in _parsed_keys:
			_ext = _parse_details.group('Ext').lower()
		elif _file_name[-4] == '.':
			_ext = _file_name[-4:]
			log.debug('{}: Parse Failed to Locate Extension Using: {}'.format(self.LogHeader, _ext))
		else:
			log.trace('{}: Unable to Identify Extension for Filename: {}'.format(self.LogHeader, fq_name))
			raise RegxSelectionError('FileParser: {}: Unable to Identify Extension for Filename: {}'.format(self.LogHeader, fq_name))

		if self.regex_SeriesDir.match(_check_path):
			_series_name = _new_subname

		self.File_Details = {}
		self.File_Details['FileName'] = fq_name
		self.File_Details['SeriesName'] = _series_name
		self.File_Details['Ext'] = _ext
#        self.File_Details['BaseDir'] = '/srv/DadVision/Series'

		if _air_date:
			self.File_Details['DateAired'] = _air_date
		else:
			self.File_Details['SeasonNum'] = _season_num
			self.File_Details['EpisodeNums'] = _episode_nums

		log.trace('{}: File Details Found: {}'.format(self.LogHeader, self.File_Details))

		return self.File_Details

	def _parse_file_name(self, pathname):
		RegExNumber = 0
		for _pattern in self.RegxParse:
			RegExNumber += 1
			_parse_details = _pattern.match(pathname)
			if not _parse_details:
				continue
			else:
				self.LogHeader = 'RegEx {}'.format(RegExNumber)
				log.verbose('{}: RegEx Matched'.format(self.LogHeader))
				return _parse_details
		return None

	def _get_series_name(self, _parsed_keys, _parse_details):
		log.trace("{}: _get_series_name: {} {}".format(self.LogHeader, _parsed_keys, _parse_details))

		if 'SeriesName' in _parsed_keys and _parse_details.group('SeriesName') != None:
			_series_name = _parse_details.group('SeriesName')
		else:
			raise InvalidFilename('FileParser: {}: Parse Did Not Find Series Name: {1}'.format(self.LogHeader, _parsed_keys))

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

		_series_name = re.sub("(^|\s)(\S)", self._repl_func, _series_name)

		log.trace('{}: Series Name: {}'.format(self.LogHeader, _series_name.strip()))

		return _series_name.strip()

	def _get_season_number(self, _parsed_keys, _parse_details):
		log.trace("{}: _get_season_number: {} {}".format(self.LogHeader, _parsed_keys, _parse_details))

		if 'SeasonNum' in _parsed_keys:
			_season_num = int(_parse_details.group('SeasonNum'))
		else:
			log.trace('{}: No Season Number in File Name, Named Groups: {}'.format(self.LogHeader, _parsed_keys))
			raise SeasonNotFound('FileParser: {}: No Season Number in File Name, Named Groups: {}'.format(self.LogHeader, _parsed_keys))

		log.trace('{}: Season Number: {}'.format(self.LogHeader, _season_num))

		return _season_num

	def _get_episode_numbers(self, _parsed_keys, _parse_details):
		log.trace("{}: _get_episode_numbers: {} {}".format(self.LogHeader, _parsed_keys, _parse_details))

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
			raise RegxSelectionError(("FileParser: {}:"
								   "Regex does not contain episode number group, should "
								   "contain EpisodeNum, EpisodeNum1-9, or "
								   "EpisodeNumStart and EpisodeNumEnd\n {}"
								   ).format(self.LogHeader, _parsed_keys))

		return _episode_numbers

	def _get_date_aired(self, _parsed_keys, _parse_details):
		log.trace("{}: _get_date_aired: {} {}".format(self.LogHeader, _parsed_keys, _parse_details))

		if 'year' in _parsed_keys or 'month' in _parsed_keys or 'day' in _parsed_keys:
			if not all(['year' in _parsed_keys, 'month' in _parsed_keys, 'day' in _parsed_keys]):
					raise RegxSelectionError("FileParser: {}: Date-based regex must contain groups 'year', 'month' and 'day', Keys Found {}".format(self.LogHeader, _parsed_keys))

			_date_aired = datetime.datetime(int(_parse_details.group('year')),
											int(_parse_details.group('month')),
											int(_parse_details.group('day')))
			return _date_aired
		else:
			log.debug()
			raise InvalidFilename('FileParser: {}: No Season / Episode Numbers or Date Aired in File Name, Named Groups: {}'.format(self.LogHeader, _parsed_keys))

	def _repl_func(self, m):
		"""process regular expression match groups for word upper-casing problem"""
		return m.group(1) + m.group(2).upper()


	def GetRegx(self):

		# My Library Standard
		self.RegxParse = []
		self.RegxParse.append(re.compile(
			'''                                     # #1  /xxx/xxx/xxx/series/Season #/E##-E## Title.ext
			^(/.*/)*                                # Directory
			(?P<SeriesName>.*)                      # Series Name
			(/Season)                               # Season
			[/\._\ \-]                               # Sep 1
			(?P<SeasonNum>[0-9]+)                   # Season Number (##)
			(/)                                     # Directory Seperator
			[E|e]                                   # Episode Number (##)
			(?P<EpisodeNum1>[0-9][0-9]+)            # e
			(\-E)                                   # Sep between Episode Numbers1
			(?P<EpisodeNum2>[0-9][0-9]+)            # e
			[/\._\ \-]                               # Optional Sep 1
			(?P<EpisodeName>.+)                     # Optional Title
			\.(?P<Ext>....?)$                       # extension
			''',re.X|re.I))

		self.RegxParse.append(re.compile(
			'''                                     # #2 /xxx/xxx/xxx/series/Season #/E## Title.ext
			^(/.*/)*                                # Directory
			(?P<SeriesName>.*)                      # Series Name
			(/Season)                               # Season
			[/\._\ \-]                               # Sep 1
			(?P<SeasonNum>[0-9]+)                   # Season Number (##)
			(/)                                     # Directory Seperator
			[E|e]                                   # Episode Number (##)
			(?P<EpisodeNum>[0-9][0-9]+)             # e
			[/\._\ \-]?                              # Optional Sep 1
			(?P<EpisodeName>.+)?                    # Optional Title
			\.(?P<Ext>....?)$                       # extension
			''',re.X|re.I))

#----------------------------------------------------------------------------------------
		# DATE AIRED
		self.RegxParse.append(re.compile(
			'''                                    # RegEx #3
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
			re.X | re.I))

#----------------------------------------------------------------------------------------
		# Multiepisode
		self.RegxParse.append(re.compile(
			'''                                     # RegEx 4 foo.s01e23e24* foo.s01e23-24*
			^(/.*/)?                                # Optional Directory
			(?P<SeriesName>.*)                      # Series Name
			[/\._ \-]                               # Sep 1
			[s|season]                              # s|season
			[/\._ \-]?                              # Optional Sep 1
			(?P<SeasonNum>[0-9]+)                   # Season Number (##)
			[/\._ \-]?                              # Sep 1
			[E|e|x|X]                               # e
			(?P<EpisodeNumStart>[0-9][0-9]+)        # Starting Episode Number (##)
			[\.\- ]?                                # Sep 1
			[e]?                                    # Optional e
			(?P<EpisodeNumEnd>[0-9][0-9]+)          # Ending Episode Number (##)
			[\.\- ]                                 # Sep 1
			(?P<EpisodeName>.*)                     # Optional Title
			\.(?P<Ext>....?)$                       # Extension
			''',
			re.X | re.I))

		self.RegxParse.append(re.compile(
			'''                                     # RegEx 5 foo s01e23 s01e24 s01e25 *
			^(/.*/)?                                # Optional Directory
			(?P<SeriesName>.*)                      # Series Name
			[/\._ \-]                               # Sep 1
			[s|season]                              # s|season
			(?P<SeasonNum>[0-9]+)                   # Season Number (##)
			[E|e|x|X]                               # e
			(?P<EpisodeNumStart>[0-9][0-9]+)        # Starting Episode Number (##)
			[\.\- ]?                                # Sep 1
			[S|s]([0-9]+)                           # s01
			[e|E|x|X]?                              # Optional e
			(?P<EpisodeNumEnd>[0-9][0-9]+)          # Ending Episode Number (##)
			[\.\- ]                                 # Sep 1
			(?P<EpisodeName>.*)                     # Optional Title
			\.(?P<Ext>....?)$                       # Extension
			''',
			re.X | re.I))

		self.RegxParse.append(re.compile(
			'''                                     # Regex #6 foo.1x23x24*
			^(/.*/)?                                # Optional Directory
			((?P<SeriesName>.+?)[ \._\-])?          # show name
			(?P<SeasonNum>[0-9]+)                   # 1
			[xX](?P<EpisodeNumStart>[0-9][0-9]+)    # first x23
			[ \._\-]?                               # separator
			([xX][0-9][0-9]+)*                      # x24x25 etc
			[ \._\-]?                               # separator
			[xX](?P<EpisodeNumEnd>[0-9][0-9]+)      # final episode num
			[/\._ \-]?                              # Optional Sep 1
			(?P<EpisodeName>.+)                     # Optional Title
			\.(?P<Ext>....?)$                       # extension
			''',
			re.X | re.I))

		self.RegxParse.append(re.compile(
			'''                                      # Regex #7 foo.1x23-24*
			^(/.*/)?                                # Optional Directory
			((?P<SeriesName>.+?)[ \._\-])?          # show name
			(?P<SeasonNum>[0-9]+)                    # 1
			[xX](?P<EpisodeNumStart>[0-9][0-9]+)     # first x23
			(                                        # -24 etc
					[\-][0-9][0-9]+
			)*
					[\-]                             # separator
					(?P<EpisodeNumEnd>[0-9][0-9]+)   # final episode num
			([\.\- ].*                               # must have a separator (prevents 1x01-720p from being 720 episodes)
			\.(?P<Ext>....?)$                       # Extension
			$)
			''',
			re.X | re.I))

		self.RegxParse.append(re.compile(
			'''                                     # Regex #8 foo.1x23 1x24 1x25
			^(/.*/)?                                # Optional Directory
			((?P<SeriesName>.+?)[ \._\-])?          # show name
			(?P<SeasonNum>[0-9]+)                   # 1
			[x|X]                                   # X
			(?P<EpisodeNumStart>[0-9][0-9]+)        # first episode (x23)
			[ \._\-]                                # separator
			([0-9]+)                                # more season numbers (1)
			[x|X]                                   # X
			(?P<EpisodeNumEnd>[0-9][0-9]+)*         # last episode number (x25)
			[ \._\-]                                # separator
			(?P<EpisodeName>.+)                     # Optional Title
			\.(?P<Ext>....?)$                       # Extension
			[^\/]*$
			''',
			re.X | re.I))

		self.RegxParse.append(re.compile(
			'''                                      # Regex #9 foo.123-24*
			^(/.*/)?                                # Optional Directory
			((?P<SeriesName>.+?)[ \._\-])?          # show name
			(?P<SeasonNum>[0-9]+)                    # 1
			(?P<EpisodeNumStart>[0-9][0-9]+)     # first x23
			(                                        # -24 etc
					[\-][0-9][0-9]+
			)*
					[\-]                             # separator
					(?P<EpisodeNumEnd>[0-9][0-9]+)   # final episode num
			([\.\- ].*                               # must have a separator (prevents 1x01-720p from being 720 episodes)
			\.(?P<Ext>....?)$                       # Extension
			$)
			''',
			re.X | re.I))

#        self.RegxParse.append(re.compile(
#            '''                                     # Regex #10 foo.123 124 125
#            ^(/.*/)*                                # Directory
#            (?P<SeriesName>.*)                      # Series Name
#            [ \._\-]                                # Sep
#            (?P<SeasonNum>[0-9]+)                   # first season number (1)
#            (?P<EpisodeNumStart>[0-9][0-9]+)        # first episode (x23)
#            [ \._\-]                                # separator
#            (?P<SeasonNumEnd>[0-9]+)                # more season numbers (1)
#            (?P<EpisodeNumEnd>[0-9][0-9]+)          # last episode number (25)
#            (?P<EpisodeName>.+)                     # Optional Title
#            \.(?P<Ext>....?)$                       # Extension
#            [^\/]*$
#            ''',
#            re.X|re.I))

#----------------------------------------------------------------------------------------
		# Groups
		self.RegxParse.append(re.compile(
			'''                                     # Regex 11
			^(/.*/)?                                # Optional Directory
			([\[|{].*[\]}])                         # { GROUP NAME }
			[\._ \-]?[\._ \-]?[\._ \-]?             # Optional Sep 1-3
			(?P<SeriesName>.*?[0-9][0-9][0-9][0-9])  # Series Name
			[ \._\-]                                # Separator .|1
			[S|s]?                                   # s|S
			[/\._ \-]?                              # Optional Sep 1
			(?P<SeasonNum>[0-9]+)                   # Season Number (##)
			[/\._ \-]?                              # Optional Sep 1
			[x|e] ?                                  # Episode Number (##)
			(?P<EpisodeNum>[0-9][0-9]+)             # e
			[/\._ \-]?                              # Optional Sep 1
			(?P<EpisodeName>.+)?                    # Optional Title
			\.(?P<Ext>....?)$                       # extension
			''',
			re.X | re.I))

		self.RegxParse.append(re.compile(
			'''                                     # Regex 11
			^(/.*/)?                                # Optional Directory
			([\[|{].*[\]}])                         # { GROUP NAME }
			[\._ \-]?[\._ \-]?[\._ \-]?             # Optional Sep 1-3
			(?P<SeriesName>.*?)                     # Series Name
			[ \._\-]                                # Separator .|1
			[S|s]?                                   # s|S
			[/\._ \-]?                              # Optional Sep 1
			(?P<SeasonNum>[0-9]+)                   # Season Number (##)
			[/\._ \-]?                              # Optional Sep 1
			[x|e] ?                                  # Episode Number (##)
			(?P<EpisodeNum>[0-9][0-9]+)             # e
			[/\._ \-]?                              # Optional Sep 1
			(?P<EpisodeName>.+)?                    # Optional Title
			\.(?P<Ext>....?)$                       # extension
			''',
			re.X | re.I))

#----------------------------------------------------------------------------------------
		# Single Episode with S or Season
		self.RegxParse.append(re.compile(
			'''                                     # RegEx 15
			^(/.*/)?                                # Optional Directory
			(?P<SeriesName>.*?)                     # Series Name
			[/\._ \-]                               # Sep 1
			[s]                                     # s
			[/\._ \-]?                              # Optional Sep 1
			(?P<SeasonNum>[0-9]+)                   # Season Number (##)
			[/\._ \-]?                              # Optional Sep 1
			[e|episode]                             # e
			(?P<EpisodeNum>[0-9][0-9]+)             # Episode Number (##)
			[/\._ \-]?                              # Optional Sep 1
			(?P<EpisodeName>.*)                     # Optional Title
			\.(?P<Ext>....?)$                       # Extension
			''',
			re.X | re.I))

		self.RegxParse.append(re.compile(
			'''                                    # RegEx 16
			^(/.*/)?
			(?P<SeriesName>.*?)
			[/\._ \-]
			(Season)
			[/\._ \-]
			(?P<SeasonNum>[0-9]+)
			[/\._ \-]
			(Episode)
			[/\._ \-]
			(?P<EpisodeNum>[0-9][0-9]+)
			[/\._ \-]?
			(?P<EpisodeName>.*)
			\.(?P<Ext>....?)$
			''',
			re.X | re.I))

#----------------------------------------------------------------------------------------
		# Single Episode No S or Season
		self.RegxParse.append(re.compile(
			'''                                    # #17  foo ##e|x##
			^(/.*/)?                               # Optional Directory
			(?P<SeriesName>.*[0-9][0-9][0-9][0-9]) # Series Name with Year
			[/\._ \-]+                             # Sep 1 or More
			(?P<SeasonNum>[0-9]+)                  # Season Number (##)
			[e|x]?                                  # e|x
			(?P<EpisodeNum>[0-9][0-9]+)            # Episode Number(##)
			[/\._ \-]*                             # Optional Sep 1 or more
			(?P<EpisodeName>.+)?                   # Optional Title
			\.(?P<Ext>....?)$                      # Extension
			''',
			re.X | re.I))

		self.RegxParse.append(re.compile(
			'''                                    # #18  foo ##e|x##
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
			re.X | re.I))

		self.RegxParse.append(re.compile(
			'''                                    # #18  foo #e|x##
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
			re.X | re.I))

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
#------------------------------------------------------------------------------------------
#        # Special Cases
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

	import sys

	logger.initialize()

	library = FileParser()
	Library.args = library.options.parser.parse_args(sys.argv[1:])
	log.debug("Parsed command line: {!s}".format(library.args))

	log_level = logging.getLevelName(library.args.loglevel)

	if library.args.logfile == 'daddyvision.log':
		log_file = '{}.log'.format(__pgmname__)
	else:
		log_file = os.path.expanduser(library.args.logfile)

	# If an absolute path is not specified, use the default directory.
	if not os.path.isabs(log_file):
		log_file = os.path.join(logger.LogDir, log_file)

	logger.start(log_file, log_level, timed=True)

	_lib_paths = library.args.library

	if _lib_paths == []:
		library.options.parser.error('Pathname for Library is required')

	_lib_path = _lib_paths[0]
	_answer = library.getFileDetails(_lib_path)

	print
	print _answer
