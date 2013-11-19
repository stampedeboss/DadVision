#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Purpose:
     Scan MKV Files and identify those that may need remuxed    

'''
from daddyvision.common import logger
from daddyvision.common.options import OptionParser, CoreOptionParser
from daddyvision.common.settings import Settings
from subprocess import Popen, call as Call,  check_call, CalledProcessError, PIPE
import fnmatch
import logging
import os
import sys

__pgmname__ = 'daddyvision.library.scanmkv'
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
config = Settings()

TRACE = 5
VERBOSE = 15

class MovieLibrary(object):
    '''
    classdocs
    '''

    def __init__(self, params, config):
        '''
        Constructor
        '''
        log.trace('__init__ method: Started')
        self.config = config
        self.params = params

    def scanMKV(self, _path_name):

        _need_researched = {}

        for _root, _dirs, _files in os.walk(os.path.abspath(_path_name),followlinks=False):
            _dirs.sort()
            _dirs_temp = sorted(_dirs)
            for _dir in _dirs_temp:
                if self._ignored(_dir):
                    _dirs.remove(_dir)
                    log.trace('Removing Dir: %s' % _dir)
                    continue

            for _file_name in _files:
                _ext = os.path.splitext(_file_name)[1][1:].lower()
                if _ext != 'mkv':
                    continue
                    
                cmd = ['mkvmerge', '--identify-verbose', _file_name]
                try:
                    process = Popen(cmd, shell=False, stdin=None, stdout=PIPE, stderr=None, cwd=_root)
                except CalledProcessError, exc:
                    log.error("mkvmerge Command returned with RC=%d" % (exc.returncode))
                    sys.exit(1)
                
                _track_count = 0
                output = process.stdout.readlines()
                for _line in output:
                    _lang = ''
                    _line_parts = _line.split()
                    if _line_parts[0]  == 'Track':
                        _track_count += 1
                        for _item in _line_parts:
                            if _item[0:9] == '[language':
                                _lang = _item.split(':')[1]
                                break
                        if _lang and _lang not in ['eng', 'und']:
                            _track_count += 999
                    
                if _track_count > 3:
                    _need_researched[_file_name] = [os.path.join(_root, _file_name), _track_count]
        _list = []
        for _entry in _need_researched:
            _list.append('{:0>5d} {}'.format(_need_researched[_entry][1], _entry))
        
        _list.sort(reverse=True)
        for _entry in _list:
            print _entry
#        print _need_researched

    def _ignored(self, name):
        """ Check for ignored pathnames.
        """
        return any(fnmatch.fnmatch(name.lower(), pattern) for pattern in self.config.ExcludeList)

        

if __name__ == '__main__':
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
    
    movielibrary = MovieLibrary(options, config)
    movielibrary.scanMKV('/mnt/DadVision/Movies')
   