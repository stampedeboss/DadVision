#!/usr/bin/env python
# encoding: utf-8
'''
cmd_options -- Command Line Options Handler for DaddyVision

'''
import logging
import sys
import os
from argparse import ArgumentParser, SUPPRESS
from argparse import RawDescriptionHelpFormatter
from common import logger

__pgmname__ = os.path.basename(sys.argv[0])
__version__ = '$Rev$'

__author__ = "@author: AJ Reynolds"
__copyright__ = "@copyright: 2013, AJ Reynolds"
__credits__ = []
__license__ = "@license: GPL"

__maintainer__ = "AJ Reynolds"
__email__ = "@contact: stampedeboss@gmail.com"
__status__ = "Development"

__date__ = '2013-07-25'
__updated__ = '2013-07-25'

program_version_message = '%%(prog)s %s (%s)' % (__version__, __updated__)
program_license = '''

Created by AJ Reynolds on %s.
Copyright 2013 AJ Reynolds. All rights reserved.

Licensed under the GPL License

Distributed on an "AS IS" basis without warranties
or conditions of any kind, either express or implied.

USAGE
''' % (str(__date__))

log = logging.getLogger(__pgmname__)

class CmdOptions(ArgumentParser):
    '''Define Standard Options for All Command lines.'''
    def __init__(self, **kwargs):

        super(CmdOptions, self).__init__(self, **kwargs)

        args = ''

        # Setup argument parser
        self.parser = ArgumentParser(description=program_license,
                         formatter_class=RawDescriptionHelpFormatter,
                         conflict_handler='resolve')
        self.parser.add_argument('-V', '--version',
                         action='version',
                         version=program_version_message)
        self.parser.add_argument('--logfile', action='store',
                         dest='logfile', default='daddyvision.log',
                         help='Specify a custom logfile filename [default: %(default)s]')
        self.parser.add_argument('library', metavar="library", nargs='*',
                         help="paths to folder(s) with file(s) ")

        group_loglvl = self.parser.add_mutually_exclusive_group()
        group_loglvl.add_argument("--verbose", dest="loglevel",
                         action="store_const", const="VERBOSE",
                         default='INFO',
                         help="increase logging to include additional informational information")
        group_loglvl.add_argument("--debug", dest="loglevel",
                         action="store_const", const="DEBUG",
                         help="increase logging to include debugging information")
        group_loglvl.add_argument("--trace", dest="loglevel",
                         action="store_const", const="TRACE",
                         help="increase logging to include trace information")
        group_loglvl.add_argument("--quiet", dest="loglevel",
                         action="store_const", const="WARNING",
                         help="Limit logging to only include Warning, Errors, and Critical information")
        group_loglvl.add_argument("--errors", dest="loglevel",
                         action="store_const", const="ERROR",
                         help="Limit logging to only include Errors and Critical information")

    def ParseArgs(self, arg):

        args = self.parser.parse_args(arg)
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


if __name__ == "__main__":

    logger.initialize()

    opt = CmdOptions()
    args = opt.parser.parse_args(sys.argv[1:])
    print args
    sys.exit()
