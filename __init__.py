# -*- coding: UTF-8 -*-
'''
    Initialization Routine for library

    Routine is call on any import of a module in the library

'''

from common.settings import Settings
from common.cmdoptions import CmdOptions
import sys

__pgmname__     = 'library.__init__'
__version__     = '@version: $Rev$'

__author__      = "@author: AJ Reynolds"
__copyright__   = "@copyright: Copyright 2011, AJ Reynolds"
__license__     = "@license: GPL"

__maintainer__  = "@organization: AJ Reynolds"
__status__      = "@status: Development"
__credits__     = []


class Library(object):
    def __init__(self):
        self.settings = Settings()
        self.options = CmdOptions()