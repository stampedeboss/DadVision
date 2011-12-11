"""
Purpose:
        Configuration and Run-time settings for the XBMC Support Programs

"""

import os
import sys

__pgmname__ = 'movies.__init__'
__version__ = '$Rev$'

__author__ = "AJ Reynolds"
__copyright__ = "Copyright 2011, AJ Reynolds"
__credits__ = []
__license__ = "GPL"

__maintainer__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"
__status__ = "Development"

print '{}'.format(__pgmname__)

class moviesclass():

    def __init__(self):
        print '{}.moviesclass.__init__'.format(__pgmname__)
        print 'movies version: {}'.format(__version__)
        print '{} version: {}'.format(__pgmname__, __version__)
        self.Module1 = __pgmname__

    def GetModule(self):
        return self.Module1

    def moviestest(self):
        print '{}.moviesclass.moviestest'.format(__pgmname__)

objhandle = moviesclass()
objhandle.moviestest()