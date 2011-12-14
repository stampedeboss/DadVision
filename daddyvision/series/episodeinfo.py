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

__author__ = "AJ Reynolds"
__copyright__ = "Copyright 2011, AJ Reynolds"
__credits__ = []
__license__ = "GPL"

__pgmname__ = 'episodeinfo'
__version__ = '$Rev$'

__maintainer__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"
__status__ = "Development"

PgmDir      = os.path.dirname(__file__)
HomeDir     = os.path.expanduser('~')
ConfigDirB  = os.path.join(HomeDir, '.config')
ConfigDir   = os.path.join(ConfigDirB, 'xbmcsupt')
LogDir = os.path.join(HomeDir, 'log')
TEMP_LOC = os.path.join(HomeDir, __pgmname__)
RunDir      = sys.path[0]

log = logging.getLogger(__pgmname__)

class EpisodeDetails(object):

    def __init__(self):

        tvdb.API_KEY     = "959D8E76B796A1FB"
        self._check_suffix = re.compile('^(?P<SeriesName>.+?)[ \._\-](?P<year>[0-9][0-9][0-9][0-9]|US|us|Us)$', re.VERBOSE)

        self._config_settings = Settings()

        self._show_list = {}
        self._alias_list = {}

        self._show_file = self._config_settings.TvdbIdFile
        if os.path.exists(self._show_file):
            with open(self._show_file, "r") as _show_file_obj:
                for _line in _show_file_obj.readlines():
                    _show_details = _line.rstrip("\n").split("\t")
                    if len(_show_details) == 2:
                        self._show_list[_show_details[0]] = _show_details[1]
            _show_file_obj.close()
        else:
            log.warn("TVDB ShowIDs File Missing: " % self._show_file)
            log.warn("TVDB ShowIDs File to be Created: " % self._show_file)

        _alias_file = self._config_settings.ShowAliasFile
        if os.path.exists(_alias_file):
            with open(_alias_file, "r") as _alias_file_obj:
                for _line in _alias_file_obj.readlines():
                    _show_details = _line.rstrip("\n").split("\t")
                    if len(_show_details) == 2:
                        self._alias_list[_show_details[0]] = _show_details[1]
            _alias_file_obj.close()

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

        SeriesDetails = self._retrieve_tvdb_info(SeriesDetails)

        log.debug('getDetailsAll: Series Data Returned: {!s}'.format(SeriesDetails))
        return SeriesDetails

    def _retrieve_tvdb_info(self, SeriesDetails):
        log.trace('_retrieve_tvdb_info: Input Parm: {!s}'.format(SeriesDetails))

        _series_name = None
        _tvdb_show_id = None

        _series_name = SeriesDetails['SeriesName'].rstrip()
        try:
            _series_name = difflib.get_close_matches(_series_name, self._show_list,1,cutoff=0.7)[0].rstrip()
            _tvdb_show_id = self._show_list[_series_name]
            log.debug('_retrieve_tvdb_info: Series Found - TVDB ID: {:>8} Name: {}'.format(_tvdb_show_id, _series_name))
        except IndexError, exc:
            try:
                log.debug('_retrieve_tvdb_info: Series Not Found: %s - Checking Aliases' % _series_name)
                _alias_name = difflib.get_close_matches(_series_name, self._alias_list,1,cutoff=0.9)
                _series_name = self._alias_list[_alias_name[0]].rstrip()
                _series_name = difflib.get_close_matches(_series_name, self._show_list,1,cutoff=0.9)[0].rstrip()
                _tvdb_show_id = self._show_list[_series_name]
                log.debug('_retrieve_tvdb_info: Found Real Name: TVDB ID: {:>8} Name: {}'.format(_tvdb_show_id, _series_name))
            except IndexError, exc:
                log.debug('_retrieve_tvdb_info: Show Not Found: %s - Attempting Match Logic' % _series_name)
                try:
                    _matches = tvdb.get_series(_series_name)
                    for _m in _matches:
                        if _series_name == _m['name']:
                            _tvdb_show_id = _m['id']
                            log.debug('_retrieve_tvdb_info: Series Found - TVDB ID: {:>8} Name: {}'.format(_tvdb_show_id, _series_name))
                            log.trace('_retrieve_tvdb_info: start update')
                            self._show_list[_series_name] = _tvdb_show_id
                            with open(self._show_file, "a") as _show_file_obj:
                                _show_file_obj.write('%s\t%s\n' % (_series_name, _tvdb_show_id))
                            _show_file_obj.close()
                            log.trace('_retrieve_tvdb_info: end update')
                            break
                except exc:
                    error_msg = "_retrieve_tvdb_info: Unable to retrieve Series Name Info - %s" % (SeriesDetails['SeriesName'])
                    log.trace(error_msg)
                    raise DataRetrievalError(error_msg)

        if _tvdb_show_id == None:
            error_msg="_retrieve_tvdb_info: Unable to Locate Series in TVDB: %s" % (_series_name)
            log.trace(error_msg)
            raise SeriesNotFound(error_msg)

        log.verbose('Series Found - TVDB ID: {:>8} Name: {}'.format( _tvdb_show_id, _series_name))

        if type(_tvdb_show_id) == list:
            log.debug("_retrieve_tvdb_info: Show ID List Found, Using First Entry: %s" % _tvdb_show_id)
            SeriesDetails['SeriesName'] = _tvdb_show_id[1]
            SeriesDetails['TVDBShowID'] = _tvdb_show_id[0]
        else:
            SeriesDetails['SeriesName'] = _series_name
            SeriesDetails['TVDBShowID'] = _tvdb_show_id
        SeriesDetails = self._episode_details(SeriesDetails)
        return SeriesDetails


    def _episode_details(self,SeriesDetails):
        log.trace("_episode_details: Retrieving Episodes - %s ID: %s" % (SeriesDetails['SeriesName'], SeriesDetails['TVDBShowID']))

        try:
            _series_info = tvdb.get_series_all(SeriesDetails['TVDBShowID'], episodes=True, banners=False, actors=False)
            _episode_list = _series_info['episodes']
        except SeriesNotFound, message:
            log.error("_episode_details: Unable to retrieve Series and Episode Info - %s, ID: %s" % (SeriesDetails['SeriesName'], SeriesDetails['TVDBShowID']))
            raise SeriesNotFound("_episode_details: Unable to retrieve Series and Episode Info - %s, ID: %s" % (SeriesDetails['SeriesName'], SeriesDetails['TVDBShowID']))
        except IOError, message:
            log.error("_episode_details: Unable to retrieve Series and Episode Info - %s, ID: %s %s" % (SeriesDetails['SeriesName'], SeriesDetails['TVDBShowID'], message))
            raise DataRetrievalError("_episode_details: Connection Issues - Unable to retrieve Series and Episode Info - %s, ID: %s" % (SeriesDetails['SeriesName'], SeriesDetails['TVDBShowID']))
        except:
            log.error("_episode_details: Unplanned Error retrieving Series and Episode Info - %s, ID: %s" % (SeriesDetails['SeriesName'], SeriesDetails['TVDBShowID']))
            raise DataRetrievalError("_episode_details: Connection Issues - Unable to retrieve Series and Episode Info - %s, ID: %s" % (SeriesDetails['SeriesName'], SeriesDetails['TVDBShowID']))

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
            log.debug("_episode_details: No Episode Data Found - %s, ID: %s" % (SeriesDetails['SeriesName'], SeriesDetails['TVDBShowID']))
            raise EpisodeNotFound("_episode_details: No Data Episode Found - %s, ID: %s" % (SeriesDetails['SeriesName'], SeriesDetails['TVDBShowID']))

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
        _my_episode_info = EpisodeDetails()
        _episode_details =  _my_episode_info.getDetailsAll({'SeriesName' : args[0]})
        log.debug('Episode Details: %s' % _episode_details)
    else:
        log.error('Series Name Not Found in Command Line Argument')
