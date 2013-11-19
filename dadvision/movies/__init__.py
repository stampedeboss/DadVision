#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from dadvision.common.cmdoptions import CmdOptions
import logging
import sys

__pgmname__     = 'movies.__init__'
__version__     = '$Rev$'

__author__      = "@author: AJ Reynolds"
__copyright__   = "@copyright: 2013, AJ Reynolds"
__license__     = "@license: GPL"

__maintainer__  = "AJ Reynolds"
__email__       = "@contact: stampedeboss@gmail.com"
__status__      = "Development"

__credits__     = []
__date__        = '2013-08-07'
__updated__     = '2013-08-07'

log = logging.getLogger(__pgmname__)

TRACE = 5
VERBOSE = 15

class Movies(object):
    """
    Movie Base Object
    """
    def __init__(self, ):
        log.trace("Entering: movies.__init__")
        options = CmdOptions(sys.argv)
