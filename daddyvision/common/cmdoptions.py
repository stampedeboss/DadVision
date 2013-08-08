#!/usr/local/bin/python2.7
# encoding: utf-8
'''
cmd_options -- Command Line Options Handler for DaddyVision

'''

import sys
import os
from argparse import ArgumentParser, SUPPRESS
from argparse import RawDescriptionHelpFormatter

__pgmname__     = os.path.basename(sys.argv[0])
__version__     = '$Rev: 160 $'

__author__      = "@author: AJ Reynolds"
__copyright__   = "@copyright: 2013, AJ Reynolds"
__license__     = "@license: GPL"

__maintainer__  = "AJ Reynolds"
__email__       = "@contact: stampedeboss@gmail.com"
__status__      = "Development"
__credits__     = []

__date__        = '2013-07-25'
__updated__     = '2013-07-25'

program_version_message = '%%(prog)s %s (%s)' % (__version__, __updated__)
program_license = '''

  Created by AJ Reynolds on %s.
  Copyright 2013 AJ Reynolds. All rights reserved.

  Licensed under the GPL License

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (str(__date__))

class CmdOptions(object):
    '''Define Standard Options for All Command lines.'''
    def __init__(self, argv=None):

#         if argv is None:
#             argv = sys.argv
#         else:
#             sys.argv.extend(argv)

        # Setup argument parser
        self.parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter, conflict_handler='resolve')
        self.parser.add_argument('-V', '--version', action='version', version=program_version_message)
        self.parser.add_argument('--logfile', action='store', dest='logfile', default='daddyvision.log',
                            help='Specify a custom logfile filename [default: %(default)s]')
        self.parser.add_argument('prog', help=SUPPRESS)
        self.parser.add_argument('library', help="paths to folder(s) with file(s) [default: %(default)s]", metavar="library", nargs='+')

        group_loglvl = self.parser.add_mutually_exclusive_group()
        group_loglvl.add_argument("-v", "--verbose", dest="loglevel", action="store_const", const="VERBOSE", default='INFO',
                         help="increase logging to include additional informational information")
        group_loglvl.add_argument("--debug", dest="loglevel", action="store_const", const="DEBUG",
                         help="increase logging to include debugging information")
        group_loglvl.add_argument("--trace", dest="loglevel", action="store_const", const="TRACE",
                         help="increase logging to include trace information")
        group_loglvl.add_argument("--quiet", dest="loglevel", action="store_const", const="WARNING",
                         help="Limit logging to only include Warning, Errors, and Critical information")
        group_loglvl.add_argument("--errors", dest="loglevel", action="store_const", const="ERROR",
                         help="Limit logging to only include Errors and Critical information")



if __name__ == "__main__":

    opt = CmdOptions(sys.argv)
    print opt
    #sys.exit(main())