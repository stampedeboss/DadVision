#!/usr/local/bin/python2.7
# encoding: utf-8
'''
'''

import sys
import os
import logging

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from daddyvision.common import logger
from daddyvision.common.settings import Settings
from daddyvision.library2.cmd_options import Options

__pgmname__ = os.path.basename(sys.argv[0])
__version__ = '$Rev: 160 $'

__author__ = "@author: AJ Reynolds"
__copyright__ = "@copyright: 2013, AJ Reynolds"
__license__ = "@license: GPL"
__credits__ = []

__maintainer__ = "AJ Reynolds"
__email__ = "@contact: stampedeboss@gmail.com"
__status__ = "Development"
__date__ = '2013-07-25'
__updated__ = '2013-07-25'

__credits__ = []
__license__ = "GPL"

log = logging.getLogger(__pgmname__)

DEBUG = 1
TESTRUN = 0
PROFILE = 0

def useLibraryLogging(func):

    def wrapper(self, *args, **kw):
        # Set the library name in the logger
        logger.set_library(self.type)
        try:
            return func(self, *args, **kw)
        finally:
            logger.set_library('')

    return wrapper

class Library(object):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
#        self.config = Settings()
        self.options = Options(sys.argv)
        self._add_rename_options(self.options.parser)

    def _add_rename_options(self, parser):
        rename_group = parser.add_argument_group("Rename", 'Options Related to Renaming')
        rename_group.add_argument("--no-cleanup", dest="clean_up_name",
             action="store_false", default=True,
             help="Do not clean-up names from unpack")
        rename_group.add_argument("-f", "--force", dest="check",
            action="store_false", default=True,
            help="Bypass Video Check and Force Rename")
        rename_group.add_argument("--no-ignore", dest="ignore",
            action="store_false", default=True,
            help="Bypass Ignore Process and Handle all Files")
        
        
if __name__ == "__main__":

    logger.initialize()
    library = Library()

    args = library.options.parser.parse_args()
    sys.exit(0)

#     if argv is None:
#         argv = sys.argv
#     else:
#         sys.argv.extend(argv)
# 
# 
#         args = parser.parse_args()
#         
    paths = args.paths
