"""
Purpose:
        Configuration and Run-time settings for the XBMC Support Programs

"""

from daddyvision.common.settings import Settings
from daddyvision.common.exceptions import InvalidArgumentType, DictKeyError, DataRetrievalError
from daddyvision.common.exceptions import SeriesNotFound, EpisodeNotFound, EpisodeNameNotFound
from logging import INFO, WARNING, ERROR, DEBUG
import daddyvision
import datetime
import difflib
import errno
import fnmatch
import logging
import logging.handlers
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

__pgmname__ = 'series.info'
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

# A level more detailed than DEBUG
TRACE = 5
# A level more detailed than INFO
VERBOSE = 15

logging.addLevelName(5, 'TRACE')
logging.addLevelName(15, 'VERBOSE')
log = logging.getLogger()
setattr(log, 'TRACE', lambda *args: log.log(5, *args))
setattr(log, 'VERBOSE', lambda *args: log.log(15, *args))

class SeriesInfo(object):

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

    def GetDetails(self, request):
        log.TRACE('SeriesInfo-GetDetails: Input Parm: {}'.format(request))

        if type(request) == dict:
            if 'SeriesName' in request:
                _suffix = self._check_suffix.match(request['SeriesName'].rstrip())
                if _suffix:
                    _series_name = '{} ({})'.format(_suffix.group('SeriesName'), _suffix.group('year').upper())
                    request['SeriesName'] = _series_name.rstrip()
                    log.debug('SeriesInfo-GetDetails: Request: Modified %s' % request)
                SeriesDetails = request
            else:
                error_msg = 'SeriesInfo-GetDetails: Request Missing "SeriesName" Key: {!s}'.format(request)
                log.TRACE(error_msg)
                raise DictKeyError(error_msg)
        else:
            error_msg='SeriesInfo-GetDetails: Invalid object type passed, must be DICT, received: {}'.format(type(request))
            log.TRACE(error_msg)
            raise InvalidArgumentType(error_msg)

        SeriesDetails = self._retrieve_tvdb_info(SeriesDetails)

        log.debug('SeriesInfo-GetDetails: Series Data Returned: {!s}'.format(SeriesDetails))
        return SeriesDetails

    def _retrieve_tvdb_info(self, SeriesDetails):
        log.TRACE('SeriesInfo-_retrieve_tvdb_info: Input Parm: {!s}'.format(SeriesDetails))

        _series_name = None
        _tvdb_show_id = None

        _series_name = SeriesDetails['SeriesName'].rstrip()
        try:
            _series_name = difflib.get_close_matches(_series_name, self._show_list,1,cutoff=0.7)[0].rstrip()
            _tvdb_show_id = self._show_list[_series_name]
            log.debug('SeriesInfo-_retrieve_tvdb_info: Series Found - TVDB ID: {:>8} Name: {}'.format(_tvdb_show_id, _series_name))
        except IndexError, exc:
            try:
                log.debug('SeriesInfo-_retrieve_tvdb_info: Show Not Found: %s - Checking Aliases' % _series_name)
                _alias_name = difflib.get_close_matches(_series_name, self._alias_list,1,cutoff=0.9)
                _series_name = self._alias_list[_alias_name[0]].rstrip()
                _series_name = difflib.get_close_matches(_series_name, self._show_list,1,cutoff=0.9)[0].rstrip()
                _tvdb_show_id = self._show_list[_series_name]
                log.debug('SeriesInfo-_retrieve_tvdb_info: Found Real Name: TVDB ID: {:>8} Name: {}'.format(_tvdb_show_id, _series_name))
            except IndexError, exc:
                log.debug('SeriesInfo-_retrieve_tvdb_info: Show Not Found: %s - Attempting Match Logic' % _series_name)
                try:
                    _matches = tvdb.get_series(_series_name)
                    for _m in _matches:
                        if _series_name == _m['name']:
                            _tvdb_show_id = _m['id']
                            log.debug('SeriesInfo-_retrieve_tvdb_info: Series Found - TVDB ID: {:>8} Name: {}'.format(_tvdb_show_id, _series_name))
                            log.TRACE('SeriesInfo-_retrieve_tvdb_info: start update')
                            self.show_list[_series_name] = _tvdb_show_id
                            with open(self._show_file, "a") as _show_file_obj:
                                _show_file_obj.write('%s\t%s\n' % (_series_name, _tvdb_show_id))
                            _show_file_obj.close()
                            log.TRACE('SeriesInfo-_retrieve_tvdb_info: end update')
                            break
                except exc:
                    error_msg = "SeriesInfo-_retrieve_tvdb_info: Unable to retrieve Series Name Info - %s" % (SeriesDetails['SeriesName'])
                    log.TRACE(error_msg)
                    raise DataRetrievalError(error_msg)

        if _tvdb_show_id == None:
            error_msg="SeriesInfo-_retrieve_tvdb_info: Unable to Locate Series in TVDB: %s" % (_series_name)
            log.TRACE(error_msg)
            raise SeriesNotFound(error_msg)

        log.info('SeriesInfo: Series Found - TVDB ID: {:>8} Name: {}'.format( _tvdb_show_id, _series_name))

        if type(_tvdb_show_id) == list:
            log.debug("SeriesInfo-_retrieve_tvdb_info: Show ID List Found, Using First Entry: %s" % _tvdb_show_id)
            SeriesDetails['SeriesName'] = _tvdb_show_id[1]
            SeriesDetails['TVDBShowID'] = _tvdb_show_id[0]
        else:
            SeriesDetails['SeriesName'] = _series_name
            SeriesDetails['TVDBShowID'] = _tvdb_show_id
        SeriesDetails = self._episode_details(SeriesDetails)
        return SeriesDetails


    def _episode_details(self,SeriesDetails):
        log.TRACE("SeriesInfo-_episode_details: Retrieving Episodes - %s ID: %s" % (SeriesDetails['SeriesName'], SeriesDetails['TVDBShowID']))

        try:
            _series_info = tvdb.get_series_all(SeriesDetails['TVDBShowID'], episodes=True, banners=False, actors=False)
            _episode_list = _series_info['episodes']
        except SeriesNotFound, message:
            log.error("SeriesInfo-_episode_details: Unable to retrieve Series and Episode Info - %s, ID: %s" % (SeriesDetails['seriesname'], SeriesDetails['TVDBShowID']))
            raise SeriesNotFound("SeriesInfo-_episode_details: Unable to retrieve Series and Episode Info - %s, ID: %s" % (SeriesDetails['seriesname'], SeriesDetails['TVDBShowID']))
        except IOError, message:
            log.error("SeriesInfo-_episode_details: Unable to retrieve Series and Episode Info - %s, ID: %s %s" % (SeriesDetails['seriesname'], SeriesDetails['TVDBShowID'], message))
            raise DataRetrievalError("SeriesInfo-_episode_details: Connection Issues - Unable to retrieve Series and Episode Info - %s, ID: %s" % (SeriesDetails['seriesname'], SeriesDetails['TVDBShowID']))
        except:
            log.error("SeriesInfo-_episode_details: Unplanned Error retrieving Series and Episode Info - %s, ID: %s" % (SeriesDetails['seriesname'], SeriesDetails['TVDBShowID']))
            raise DataRetrievalError("SeriesInfo-_episode_details: Connection Issues - Unable to retrieve Series and Episode Info - %s, ID: %s" % (SeriesDetails['seriesname'], SeriesDetails['TVDBShowID']))

        SeriesDetails['episodedata'] = []
                
        for _item in _episode_list:
            if _item['name']:
                _name = _item['name'].rstrip()
                log.TRACE('SeriesInfo-_episode_details: Episode Name: %s' % _name)
            else:
                _name = 'NOT FOUND'

            if 'season' in SeriesDetails:
                if 'epno' in SeriesDetails:
                    for epno in SeriesDetails['epno']:
                        log.debug('SeriesInfo-_episode_details: Checking for Season & epno Match: %s %s' % (_item['season_number'], _item['episode_number']))
                        if _item['season_number'] == SeriesDetails['season'] and _item['episode_number'] == epno:
                            SeriesDetails['episodedata'].append({'season' : _item['season_number'],
                                                          'epno' : epno,
                                                          'episodename' : _name,
                                                          'airdate': _item['first_aired']})
                else:
                    if _item['season_number'] == SeriesDetails['season']:
                        SeriesDetails['episodedata'].append({'season' : _item['season_number'],
                                                      'epno' : [_item['episode_number']],
                                                      'episodename' : _name,
                                                      'airdate': _item['first_aired']})
            elif 'airdate' in SeriesDetails:
                if _item['first_aired'] == SeriesDetails['airdate']:
                    SeriesDetails['season'] = _item['season_number']
                    SeriesDetails['epno'] = [_item['episode_number']]
                    SeriesDetails['episodedata'] = [{'season' : _item['season_number'],
                                'epno' : _item['episode_number'],
                                'episodename' : _name,
                                'airdate': _item['first_aired']}]
            else:
                SeriesDetails['episodedata'].append({'season' : _item['season_number'],
                                'epno' : [_item['episode_number']],
                                'episodename' : _name,
                                'airdate': _item['first_aired']})
        if len(SeriesDetails['episodedata']) > 0:
            return SeriesDetails
        else:
            log.debug("SeriesInfo-_episode_details: No Episode Data Found - %s, ID: %s" % (SeriesDetails['seriesname'], SeriesDetails['TVDBShowID']))
            raise EpisodeNotFound("SeriesInfo-_episode_details: No Data Episode Found - %s, ID: %s" % (SeriesDetails['seriesname'], SeriesDetails['TVDBShowID']))

if __name__ == "__main__":

    from optparse import OptionParser, OptionGroup

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

    if len(args) > 0:
        _my_series_info = SeriesInfo()
        _series_details =  _my_series_info.GetDetails({'SeriesName' : args[0]})
        log.debug('Series Details: %s' % _series_details)
    else:
        log.error('No requested show not found in command line argument')
