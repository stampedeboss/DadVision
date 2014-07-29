#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Purpose:
        Configuration and Run-time settings for the XBMC Support Programs
"""
from library import Library
from pytvdbapi.error import TVDBAttributeError, TVDBIndexError, TVDBValueError
from common.exceptions import InvalidArgumentType, DictKeyError, DataRetrievalError
from common.exceptions import SeriesNotFound, EpisodeNotFound, EpisodeNameNotFound
from common import logger
from fuzzywuzzy import fuzz
import datetime
import difflib
import errno
import logging
import os.path
import re
import sys
import time
import unicodedata

import tvdb
from pytvdbapi import api
from tvrage.api import Show, ShowNotFound

__pgmname__ = 'episodeinfo'
__version__ = '@version: $Rev$'

__author__ = "@author: AJ Reynolds"
__email__ = "@contact: stampedeboss@gmail.com"
__copyright__ = "@copyright: Copyright 2011, AJ Reynolds"
__license__ = "@license: GPL"

__maintainer__ = "@organization: AJ Reynolds"
__status__ = "@status: Development"
__credits__ = []

FlexGetConfig = os.path.join(os.path.expanduser('~'), '.flexget', 'config.series')
log = logging.getLogger(__pgmname__)

class EpisodeDetails(Library):

    def __init__(self):
        log.trace('EpisodeDetails.__init__')

        super(EpisodeDetails, self).__init__()

        ep_group = self.options.parser.add_argument_group("Episode Detail Options", description=None)
        ep_group.add_argument("--series-name", type=str, dest='series_name')
        ep_group.add_argument("--season", type=int, dest='season')
        ep_group.add_argument("--epno", type=int, action='append', dest='epno')
        ep_group.add_argument("--tvrage", dest="tvrage",
            action="store_true", default=False,
            help="Force information to come from TVRage")
        ep_group.add_argument("--tvdb", dest="tvdb",
            action="store_true", default=False,
            help="Force information to come from TVDB")

        self.db = api.TVDB("959D8E76B796A1FB")
        self._check_suffix = re.compile('^(?P<SeriesName>.+?)[ \._\-](?P<year>[0-9][0-9][0-9][0-9]|US|us|Us)$', re.VERBOSE)
	self.confidenceFactor = 90

    def getDetails(self, request):
        log.trace('getDetailsAll: Input Parm: {}'.format(request))

        if type(request) == dict:
            if 'SeriesName' in request and request['SeriesName'] is not None:
                _suffix = self._check_suffix.match(request['SeriesName'].rstrip())
                if _suffix:
                    _series_name = '{} ({})'.format(_suffix.group('SeriesName'), _suffix.group('year').upper())
                    request['SeriesName'] = _series_name.rstrip()
                    log.debug('getDetailsAll: Request: Modified %s' % request)
                SeriesDetails = request
            else:
                error_msg = 'getDetails: Request Missing "SeriesName" Key: {!s}'.format(request)
                log.trace(error_msg)
                raise DictKeyError(error_msg)
        else:
            error_msg = 'getDetails: Invalid object type passed, must be DICT, received: {}'.format(type(request))
            log.trace(error_msg)
            raise InvalidArgumentType(error_msg)

        SeriesDetails = self._adj_episode(SeriesDetails)

        if self.args.tvdb:
            SeriesDetails = self._retrieve_tvdb_info(SeriesDetails)
        elif self.args.tvrage:
            SeriesDetails = self._retrieve_tvrage_info(SeriesDetails)
        else:
            try:
                SeriesDetails = self._retrieve_tvdb_info(SeriesDetails)
            except (SeriesNotFound, EpisodeNotFound), msg:
                SeriesDetails = self._retrieve_tvrage_info(SeriesDetails)

#        log.debug('getDetails: Series Data Returned: {!s}'.format(SeriesDetails))
        return SeriesDetails

    def _adj_episode(self, SeriesDetails):
        for _entry in self.settings.EpisodeAdjList:
            if _entry['SeriesName'] == SeriesDetails['SeriesName'] and 'SeasonNum' in SeriesDetails:
                if _entry['SeasonNum'] == SeriesDetails['SeasonNum']:
                    if _entry['Begin'] <= SeriesDetails['EpisodeNums'][0] and _entry['End'] >= SeriesDetails['EpisodeNums'][0]:
                        SeriesDetails['SeasonNum'] = SeriesDetails['SeasonNum'] + _entry['AdjSeason']
                        SeriesDetails['EpisodeNums'][0] = SeriesDetails['EpisodeNums'][0] + _entry['AdjEpisode']
                        return SeriesDetails
        return SeriesDetails

    def _retrieve_tvdb_info(self, SeriesDetails):
        log.trace('_retrieve_tvdb_info: Input Parm: {!s}'.format(SeriesDetails))

        _series_name = None
        _tvdb_id = None

        _series_name = SeriesDetails['SeriesName'].rstrip()
        _series_name, _tvdb_id = self._find_series_id(_series_name)

        log.verbose('Series Found - TVDB ID: {:>8} Name: {}'.format(_tvdb_id, _series_name))

        if type(_tvdb_id) == list:
            log.debug("_retrieve_tvdb_info: Series ID List Found, Using First Entry: %s" % _tvdb_id)
            SeriesDetails['SeriesName'] = _tvdb_id[1]
            SeriesDetails['TVDBSeriesID'] = _tvdb_id[0]
        else:
            SeriesDetails['SeriesName'] = _series_name
            SeriesDetails['TVDBSeriesID'] = _tvdb_id
        try:
            SeriesDetails = self._episode_details(SeriesDetails)
        except EpisodeNotFound, msg:
            log.error(msg)
            raise EpisodeNotFound(msg)
        return SeriesDetails

    def _find_series_id(self, _series_name):

        _tvdb_id = None
        # Check for Alias
        try:
            _alias_name = difflib.get_close_matches(_series_name, self.settings.SeriesAliasList, 1, cutoff=0.9)
            _series_name = self.settings.SeriesAliasList[_alias_name[0]].rstrip()
        except IndexError, exc:
            pass

        try:
            _series_name = difflib.get_close_matches(_series_name, self.settings.TvdbIdList, 1, cutoff=0.9)[0].rstrip()
            _tvdb_id = self.settings.TvdbIdList[_series_name]
            log.debug('_find_series_id: Series Found - TVDB ID: {:>8} Name: {}'.format(_tvdb_id, _series_name))
        except IndexError, exc:
            log.debug('_find_series_id: Series Not Found: %s - Attempting Match Logic' % _series_name)
            try:
                _matches = self.db.search(_series_name, "en")
                for _m in _matches:
		    if self._correct_show(_series_name, _m):
                        _series_name = _m.SeriesName
                        _series_name = unicodedata.normalize('NFKD', _series_name).encode('ascii', 'ignore')
                        _series_name = _series_name.replace("&amp;", "&").replace("/", "_")
                        _tvdb_id = _m.seriesid
                        log.debug('_find_series_id: Series Found - TVDB ID: {:>8} Name: {}'.format(_tvdb_id, _series_name))
                        log.trace('_find_series_id: start update')
                        self.settings.TvdbIdList[_series_name] = _tvdb_id
                        with open(self.settings.TvdbIdFile, "a") as _sf_obj:
                            _sf_obj.write('%s\t%s\n' % (_series_name, _tvdb_id))
                        _sf_obj.close()
                        with open(FlexGetConfig, "a") as _sf_obj:
                            _sf_obj.write('    - %s\n' % (_series_name.replace(':', '')))
                        _sf_obj.close()
                        log.trace('_find_series_id: end update')
                        self.settings.ReloadTVDBList()
                        break
            except exc:
                error_msg = "_find_series_id: Unable to retrieve Series Name Info - %s" % (_series_name)
                log.trace(error_msg)
                raise DataRetrievalError(error_msg)

        if _tvdb_id == None:
            error_msg = "_find_series_id: Series Not Found in TVDB: %s" % (_series_name)
            log.trace(error_msg)
            raise SeriesNotFound(error_msg)

        return _series_name, _tvdb_id

    def _correct_show(self, _series_name, _m):

        _new_name = _m.SeriesName
        _new_name = unicodedata.normalize('NFKD', _new_name).encode('ascii', 'ignore')
        _new_name = _new_name.replace("&amp;", "&").replace("/", "_")

        log.debug('Checking: {}'.format(_new_name))
        if _series_name == _new_name or _series_name.lower() == _new_name.lower():
            return True

        if not "AliasNames" in _m:
            return False 

	if not type(_m.AliasNames) == list:
	    _m.AliasNames = [_m.AliasNames]

	for _new_name in _m.AliasNames:
            _new_name = unicodedata.normalize('NFKD', _new_name).encode('ascii', 'ignore')
            _new_name = _new_name.replace("&amp;", "&").replace("/", "_")
            log.debug('Alias: {}'.format(_new_name))


            if self.matching(_series_name, _new_name):
                _series_name = _m.SeriesName
                _series_name = unicodedata.normalize('NFKD', _series_name).encode('ascii', 'ignore')
                _series_name = _series_name.replace("&amp;", "&").replace("/", "_")
                self.settings.SeriesAliasList[_new_name] = _series_name
                with open(self.settings.SeriesAliasFile, "a") as _sf_obj:
                    _sf_obj.write('%s\t%s\n' % (_new_name, _series_name))
                    _sf_obj.close()

                return True

        return False

    def _episode_details(self, SeriesDetails):
        log.trace("_episode_details: Retrieving Episodes - %s ID: %s" % (SeriesDetails['SeriesName'], SeriesDetails['TVDBSeriesID']))

        _err_msg_1 = "_episode_details: Season/Episode Not Found - {}  ID: {}"
        _err_msg_2 = "_episode_details: Connection Issues Retrieving Series and Episode Info - {}, ID: {}"
        _err_msg_3 = "_episode_details: Unknown Error Retrieving Series and Episode Info - {}, ID: {}"
        _err_msg_4 = "_episode_details: No Episode Data Found - {}, ID: {}"
        _trace_msg_1 = '_episode_details: Checking for SeasonNum & EpisodeNum Match: {} {}'

        SeriesDetails['EpisodeData'] = []

        try:
            _series = self.db.get_series( SeriesDetails['TVDBSeriesID'], "en" )
            if 'SeasonNum' in SeriesDetails:
                _season = _series[SeriesDetails['SeasonNum']]
                log.debug('Season: {}'.format(_season))
                if 'EpisodeNums' in SeriesDetails:
                    for epno in SeriesDetails['EpisodeNums']:
                        _episode = _season[epno]
                        self._load_data(_season, _episode, SeriesDetails)
                else:
                    for _episode in _season:
                        self._load_data(_season, _episode, SeriesDetails)
            else:
                for _season in _series:
                    log.debug('Season: {}'.format(_season.season_number))
                    for _episode in _season:
                        self._load_data(_season, _episode, SeriesDetails)
        except TVDBIndexError, message:
            log.error(_err_msg_1.format(SeriesDetails['SeriesName'], SeriesDetails['TVDBSeriesID']))
            log.error(message)
            raise EpisodeNotFound(_err_msg_1.format(SeriesDetails['SeriesName'], SeriesDetails['TVDBSeriesID']))
        except IOError, message:
            log.error(_err_msg_2.format(SeriesDetails['SeriesName'], SeriesDetails['TVDBSeriesID']))
            log.error(message)
            raise DataRetrievalError(_err_msg_2.format(SeriesDetails['SeriesName'], SeriesDetails['TVDBSeriesID']))
#        except:
#            log.error(_err_msg_3.format(SeriesDetails['SeriesName'], SeriesDetails['TVDBSeriesID']))
#            raise DataRetrievalError(_err_msg_3.format(SeriesDetails['SeriesName'], SeriesDetails['TVDBSeriesID']))
            raise
 
        if len(SeriesDetails['EpisodeData']) > 0:
            return SeriesDetails
        else:
            log.debug(_err_msg_4.format(SeriesDetails['SeriesName'], SeriesDetails['TVDBSeriesID']))
            raise EpisodeNotFound(_err_msg_4.format(SeriesDetails['SeriesName'], SeriesDetails['TVDBSeriesID']))

    def _load_data(self, _season, _episode, SeriesDetails):
        if type(_episode.EpisodeName) == unicode:
            _episode_name = unicodedata.normalize('NFKD', _episode.EpisodeName).encode('ascii', 'ignore')
            _episode_name = _episode_name.replace("&amp;", "&").replace("/", "_")
        else:
            _episode_name = str(_episode.EpisodeName)

        SeriesDetails['EpisodeData'].append({'SeasonNum'    : _season.season_number,
                                             'EpisodeNum'   : _episode.EpisodeNumber,
                                             'EpisodeTitle' : _episode_name,
                                             'DateAired'    :  _episode.FirstAired})
        log.debug('{} {} {} {}'.format(_season.season_number, _episode.EpisodeNumber, _episode_name, _episode.FirstAired))


    def _retrieve_tvrage_info(self, SeriesDetails):
        log.debug('_retrieve_tvrage_info: Input Parm: {!s}'.format(SeriesDetails))

        _series_name = SeriesDetails['SeriesName'].rstrip()

        try:
            _series = Show(_series_name)
        except:
            error_msg = "Series Not Found: _retrieve_tvrage_info: Unable to Locate Series in TVDB or TVRAGE: %s" % (_series_name)
            raise SeriesNotFound(error_msg)

        _tvrage_series_name = _series.name
        if self._matching(_series_name, _tvrage_series_name)
            error_msg = "_retrieve_tvrage_info: Unable to Locate Series in TVDB or TVRAGE: %s" % (_series_name)
            raise SeriesNotFound(error_msg)

        log.warn('_retrieve_tvrage_info: Using TVRage for Episode Data: %s' % _tvrage_series_name)
        SeriesDetails['EpisodeData'] = []
        if 'EpisodeNums' in SeriesDetails:
            for epno in SeriesDetails['EpisodeNums']:
                try:
                    _episode = _series.season(SeriesDetails['SeasonNum']).episode(epno)
                except KeyError:
                    log.debug("_retrieve_tvrage_info: TVDB & TVRAGE No Episode Data Found - %s" % (SeriesDetails['SeriesName']))
                    raise EpisodeNotFound("_retrieve_tvrage_info: TVDB & TVRAGE No Data Episode Found - %s" % (SeriesDetails['SeriesName']))

                try:
                    _date_aired = _episode.airdate
                    SeriesDetails['EpisodeData'].append({'SeasonNum' : SeriesDetails['SeasonNum'],
                                                         'EpisodeNum' : epno,
                                                         'EpisodeTitle' : _episode.title,
                                                         'DateAired': _date_aired})
                except KeyError, msg:
                    raise EpisodeNotFound(msg)
        else:
            _episodes = _series.episodes
            for _season_num in _series.episodes:
                for _episode_num in _series.episodes[_season_num]:
                    try:
                        _episode = _series.season(_season_num).episode(_episode_num)
                        _date_aired = _episode.airdate
                        SeriesDetails['EpisodeData'].append({'SeasonNum' : _season_num,
                                                             'EpisodeNum' : _episode_num,
                                                             'EpisodeTitle' : _episode.title,
                                                             'DateAired': _date_aired})
                    except KeyError, msg:
                        raise EpisodeNotFound(msg)
        return SeriesDetails

    def _matching(self, value1, value2):
        log.trace("_matching: Compare: {} --> {}".format(value1, value2))

        Fuzzy[0] = fuzz.ratio(value1, value2)
        Fuzzy[1] = fuzz.token_set_ratio(value1, value2)
        Fuzzy[2] = fuzz.token_sort_ratio(value1, value2)
        Fuzzy[3] = fuzz.token_set_ratio(value1, value2)

        log.debug('Fuzzy Ratio" {} for {} - {}'.format(Fuzzy[0], value1, value2))
        log.debug('Fuzzy Partial Ratio" {} for {} - {}'.format(Fuzzy[1], value1, value2))
        log.debug('Fuzzy Token Sort Ratio" {} for {} - {}'.format(Fuzzy[2], value1, value2))
        log.debug('Fuzzy Token Set Ratio" {} for {} - {}'.format(Fuzzy[3], value1, value2))

        return any([fr > self.confidenceFactor for fr in Fuzzy])


if __name__ == "__main__":

    logger.initialize()
    library = EpisodeDetails()
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

    _series_details = {'SeriesName' : library.args.series_name}
    if library.args.season:
        _series_details['SeasonNum'] = library.args.season
    if library.args.epno:
        _series_details['EpisodeNums'] = library.args.epno

    _answer = library.getDetails(_series_details)

    print
    print _answer
#         log.debug('Episode Details: %s' % _episode_details)
#     else:
#         log.error('Series Name Not Found in Command Line Argument')


