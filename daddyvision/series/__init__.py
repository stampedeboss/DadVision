#!/usr/bin/python /home/aj/workspace/VideoLibrary/daddyvision

import os
import sys
import logging
from daddyvision.common import logger
from daddyvision.common.options import CoreOptionParser
from daddyvision.series.manager import Manager

__pgmname__ = 'series.__init__'
__version__ = '$Rev$'

__author__ = "AJ Reynolds"
__copyright__ = "Copyright 2011, AJ Reynolds"
__credits__ = []
__license__ = "GPL"

__maintainer__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"
__status__ = "Development"

PgmDir = os.path.dirname(__file__)
HomeDir = os.path.expanduser('~')
ConfigDirB = os.path.join(HomeDir, '.config')
ConfigDir = os.path.join(ConfigDirB, 'xbmcsupt')
LogDir = os.path.join(HomeDir, 'log')
TEMP_LOC = os.path.join(HomeDir, __pgmname__)
RunDir = sys.path[0]

log = logging.getLogger('main')
