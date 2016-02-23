#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Purpose:
     Scan MKV Files and identify those that may need remuxed

'''
import logging
import os
import sys
from subprocess import Popen, CalledProcessError, PIPE

import logger
from dadvision.library import Library

__pgmname__ = 'library.scanmkv'

__author__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"

__maintainer__ = __author__

__copyright__ = "Copyright 2011, AJ Reynolds"
__license__ = "GPL"

log = logging.getLogger(__pgmname__)

class scanLibrary(Library):
    '''
    classdocs
    '''

    def scanMKV(self, _path_name):

        _need_researched = {}

        for _root, _dirs, _files in os.walk(os.path.abspath(_path_name), followlinks=False):
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
                    if _line_parts[0] == 'Track':
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


if __name__ == '__main__':

    logger.initialize()

    library = scanLibrary()

    args = library.options.parser.parse_args(sys.argv[1:])
    log.debug("Parsed command line: {!s}".format(args))

    log_level = logging.getLevelName(args.loglevel.upper())

    if args.logfile == 'daddyvision.log':
        log_file = '{}.log'.format(__pgmname__)
    else:
        log_file = os.path.expanduser(args.logfile)

    # If an absolute path is not specified, use the default directory.
    if not os.path.isabs(log_file):
        log_file = os.path.join(logger.LogDir, log_file)

    logger.start(log_file, log_level, timed=True)

    if len(args.library) == 0:
        msg = 'Missing Scan Starting Point (Input Directory), Using Default: {}'.format(library.settings.NewSeriesDir)
        log.info(msg)
        args.library = [library.settings.MoviesDir]

    for _lib_path in args.library:
        if os.path.exists(_lib_path):
            library.scanMKV(_lib_path)
        else:
            log.error('Skipping Scan: Unable to find File/Directory: {}'.format(_lib_path))
