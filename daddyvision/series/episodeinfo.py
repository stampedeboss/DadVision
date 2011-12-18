"""
Purpose:
        Configuration and Run-time settings for the XBMC Support Programs

"""

from daddyvision.common.settings import Settings
from daddyvision.common.exceptions import InvalidArgumentType, DictKeyError, DataRetrievalError
from daddyvision.common.exceptions import SeriesNotFound, EpisodeNotFound, EpisodeNameNotFound
from daddyvision.common import logger
from daddyvision.common.options import OptionParser, CoreOptionParser
from logging import INFO, WARNING, ERROR, DEBUG
from tvrage.api import Show
import datetime
import difflib
import errno
import fnmatch
import logging
import os
import os.path
import re
import subprocess
import sys
import time
import tvdb
import unicodedata


__author__ = "AJ Reynolds"
__copyright__ = "Copyright 2011, AJ Reynolds"
__credits__ = []
__license__ = "GPL"

__pgmname__ = 'episodeinfo'
__version__ = '$Rev$'

__maintainer__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"
__status__ = "Development"

FlexGetConfig = os.path.join(os.path.expanduser('~'),'.flexget', 'config.series')

log = logging.getLogger(__pgmname__)

class EpisodeDetails(object):

    def __init__(self):

        tvdb.API_KEY     = "959D8E76B796A1FB"
        self._check_suffix = re.compile('^(?P<SeriesName>.+?)[ \._\-](?P<year>[0-9][0-9][0-9][0-9]|US|us|Us)$', re.VERBOSE)

        self.config = Settings()

    def getDetails(self, request):
        log.trace('getDetailsAll: Input Parm: {}'.format(request))

        if type(request) == dict:
            if 'SeriesName' in request:
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
            error_msg='getDetails: Invalid object type passed, must be DICT, received: {}'.format(type(request))
            log.trace(error_msg)
            raise InvalidArgumentType(error_msg)

        SeriesDetails = self._adj_episode(SeriesDetails)
        try:
            SeriesDetails = self._retrieve_tvdb_info(SeriesDetails)
        except:
            SeriesDetails = self._retrieve_tvrage_info(SeriesDetails)

        log.debug('getDetails: Series Data Returned: {!s}'.format(SeriesDetails))
        return SeriesDetails

    def _adj_episode(self, SeriesDetails):
        for _entry in self.config.EpisodeAdjList:
            if _entry['SeriesName'] == SeriesDetails['SeriesName']:
                if _entry['SeasonNum'] == SeriesDetails['SeasonNum']:
                    if _entry['Begin'] < SeriesDetails['EpisodeNums'][0] and _entry['End'] > SeriesDetails['EpisodeNums'][0]:
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

        if _tvdb_id == None:
            x = Show(_series_name)
            _series_name = x.name
            _series_name, _tvdb_id = self._find_series_id(_series_name)

        if _tvdb_id == None:
            error_msg="_retrieve_tvdb_info: Unable to Locate Series in TVDB: %s" % (_series_name)
            log.trace(error_msg)
            raise SeriesNotFound(error_msg)

        log.verbose('Series Found - TVDB ID: {:>8} Name: {}'.format( _tvdb_id, _series_name))

        if type(_tvdb_id) == list:
            log.debug("_retrieve_tvdb_info: Series ID List Found, Using First Entry: %s" % _tvdb_id)
            SeriesDetails['SeriesName'] = _tvdb_id[1]
            SeriesDetails['TVDBSeriesID'] = _tvdb_id[0]
        else:
            SeriesDetails['SeriesName'] = _series_name
            SeriesDetails['TVDBSeriesID'] = _tvdb_id
        SeriesDetails = self._episode_details(SeriesDetails)
        return SeriesDetails

    def _find_series_id(self,_series_name):

        _tvdb_id = None

        try:
            _series_name = difflib.get_close_matches(_series_name, self.config.TvdbIdList,1,cutoff=0.8)[0].rstrip()
            _tvdb_id = self.config.TvdbIdList[_series_name]
            log.debug('_find_series_id: Series Found - TVDB ID: {:>8} Name: {}'.format(_tvdb_id, _series_name))
        except IndexError, exc:
            try:
                log.debug('_find_series_id: Series Not Found: %s - Checking Aliases' % _series_name)
                _alias_name = difflib.get_close_matches(_series_name, self.config.SeriesAliasList,1,cutoff=0.9)
                _series_name = self.config.SeriesAliasList[_alias_name[0]].rstrip()
                _series_name = difflib.get_close_matches(_series_name, self.config.TvdbIdList,1,cutoff=0.9)[0].rstrip()
                _tvdb_id = self.config.TvdbIdList[_series_name]
                log.debug('_find_series_id: Found Real Name: TVDB ID: {:>8} Name: {}'.format(_tvdb_id, _series_name))
            except IndexError, exc:
                log.debug('_find_series_id: Series Not Found: %s - Attempting Match Logic' % _series_name)
                try:
                    _matches = tvdb.get_series(_series_name)
                    for _m in _matches:
                        _new_name = _m['name']
                        _new_name = unicodedata.normalize('NFKD', _new_name).encode('ascii','ignore')
                        _new_name = _new_name.replace("&amp;", "&").replace("/", "_")
                        if _series_name == _new_name or _series_name.lower() == _new_name.lower():
                            _tvdb_id = _m['id']
                            log.debug('_find_series_id: Series Found - TVDB ID: {:>8} Name: {}'.format(_tvdb_id, _series_name))
                            log.trace('_find_series_id: start update')
                            self.config.TvdbIdList[_series_name] = _tvdb_id
                            with open(self.config.TvdbIdFile, "a") as _sf_obj:
                                _sf_obj.write('%s\t%s\n' % (_series_name, _tvdb_id))
                            _sf_obj.close()
                            with open(FlexGetConfig, "a") as _sf_obj:
                                _sf_obj.write('    - %s\n' % (_series_name))
                            _sf_obj.close()
                            log.trace('_find_series_id: end update')
                            self.config.ReloadTVDBList()
                            break
                except exc:
                    error_msg = "_find_series_id: Unable to retrieve Series Name Info - %s" % (_series_name)
                    log.trace(error_msg)
                    raise DataRetrievalError(error_msg)
        return _series_name, _tvdb_id

    def _episode_details(self,SeriesDetails):
        log.trace("_episode_details: Retrieving Episodes - %s ID: %s" % (SeriesDetails['SeriesName'], SeriesDetails['TVDBSeriesID']))

        try:
            _series_info = tvdb.get_series_all(SeriesDetails['TVDBSeriesID'], episodes=True, banners=False, actors=False)
            _episode_list = _series_info['episodes']
        except SeriesNotFound, message:
            log.error("_episode_details: Unable to retrieve Series and Episode Info - %s, ID: %s" % (SeriesDetails['SeriesName'], SeriesDetails['TVDBSeriesID']))
            raise SeriesNotFound("_episode_details: Unable to retrieve Series and Episode Info - %s, ID: %s" % (SeriesDetails['SeriesName'], SeriesDetails['TVDBSeriesID']))
        except IOError, message:
            log.error("_episode_details: Unable to retrieve Series and Episode Info - %s, ID: %s %s" % (SeriesDetails['SeriesName'], SeriesDetails['TVDBSeriesID'], message))
            raise DataRetrievalError("_episode_details: Connection Issues - Unable to retrieve Series and Episode Info - %s, ID: %s" % (SeriesDetails['SeriesName'], SeriesDetails['TVDBSeriesID']))
        except:
            log.error("_episode_details: Unplanned Error retrieving Series and Episode Info - %s, ID: %s" % (SeriesDetails['SeriesName'], SeriesDetails['TVDBSeriesID']))
            raise DataRetrievalError("_episode_details: Connection Issues - Unable to retrieve Series and Episode Info - %s, ID: %s" % (SeriesDetails['SeriesName'], SeriesDetails['TVDBSeriesID']))

        SeriesDetails['EpisodeData'] = []

        for _item in _episode_list:
            if _item['name']:
                _name = _item['name'].rstrip()
                log.trace('_episode_details: Episode Name: %s' % _name)
            else:
                _name = 'NOT FOUND'

            if 'SeasonNum' in SeriesDetails:
                if 'EpisodeNums' in SeriesDetails:
                    for epno in SeriesDetails['EpisodeNums']:
                        log.trace('_episode_details: Checking for SeasonNum & EpisodeNum Match: %s %s' % (_item['season_number'], _item['episode_number']))
                        if _item['season_number'] == SeriesDetails['SeasonNum'] and _item['episode_number'] == epno:
                            SeriesDetails['EpisodeData'].append({'SeasonNum' : _item['season_number'],
                                                          'EpisodeNum' : epno,
                                                          'EpisodeTitle' : _name,
                                                          'DateAired': _item['first_aired']})
                else:
                    if _item['season_number'] == SeriesDetails['SeasonNum']:
                        SeriesDetails['EpisodeData'].append({'SeasonNum' : _item['season_number'],
                                                      'EpisodeNum' : [_item['episode_number']],
                                                      'EpisodeTitle' : _name,
                                                      'DateAired': _item['first_aired']})
            elif 'DateAired' in SeriesDetails:
                if _item['first_aired'] == SeriesDetails['DateAired']:
                    SeriesDetails['SeasonNum'] = _item['season_number']
                    SeriesDetails['EpisodeNum'] = [_item['episode_number']]
                    SeriesDetails['EpisodeData'] = [{'SeasonNum' : _item['season_number'],
                                'EpisodeNum' : _item['episode_number'],
                                'EpisodeTitle' : _name,
                                'DateAired': _item['first_aired']}]
            else:
                SeriesDetails['EpisodeData'].append({'SeasonNum' : _item['season_number'],
                                'EpisodeNum' : [_item['episode_number']],
                                'EpisodeTitle' : _name,
                                'DateAired': _item['first_aired']})
        if len(SeriesDetails['EpisodeData']) > 0:
            return SeriesDetails
        else:
            log.debug("_episode_details: No Episode Data Found - %s, ID: %s" % (SeriesDetails['SeriesName'], SeriesDetails['TVDBSeriesID']))
            raise EpisodeNotFound("_episode_details: No Data Episode Found - %s, ID: %s" % (SeriesDetails['SeriesName'], SeriesDetails['TVDBSeriesID']))

    def _retrieve_tvrage_info(self, SeriesDetails):
        log.warn('_retrieve_tvrage_info: Input Parm: {!s}'.format(SeriesDetails))

        _series_name = SeriesDetails['SeriesName'].rstrip()
        _series = Show(_series_name)
        SeriesDetails['EpisodeData'] = []
        for epno in SeriesDetails['EpisodeNums']:
            try:
                episode = _series.season(SeriesDetails['SeasonNum']).episode(epno)
            except KeyError:
                log.debug("_episode_details: TVDB & TVRAGE No Episode Data Found - %s" % (SeriesDetails['SeriesName']))
                raise EpisodeNotFound("_episode_details: TVDB & TVRAGE No Data Episode Found - %s" % (SeriesDetails['SeriesName']))

            SeriesDetails['EpisodeData'].append({'SeasonNum' : SeriesDetails['SeasonNum'],
                                                 'EpisodeNum' : SeriesDetails['EpisodeNums'][0],
                                                 'EpisodeTitle' : episode.title,
                                                 'DateAired': episode.airdate})
        return SeriesDetails


if __name__ == "__main__":

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


    if len(args) > 0:
        _series_details = {args[0] : args[1], args[2] : int(args[3]), args[4] : [int(args[5])]}
        _my_episode_info = EpisodeDetails()
        _episode_details =  _my_episode_info.getDetails(_series_details)
        log.debug('Episode Details: %s' % _episode_details)
    else:
        log.error('Series Name Not Found in Command Line Argument')
