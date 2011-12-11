'''
Created on Dec 9, 2011

@author: aj
'''

import __init__
import __main__
from testrun import testrunclass

__pgmname__ = 'movies.manager'
__version__ = '$Rev$'

__author__ = "AJ Reynolds"
__copyright__ = "Copyright 2011, AJ Reynolds"
__credits__ = []
__license__ = "GPL"

__maintainer__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"
__status__ = "Development"

print '{}'.format(__pgmname__)

class managerclass():
    def __init__(self):
        print '{}.managerclass.__init__'.format(__pgmname__)
        print 'movies version: {}'.format(__init__.__version__)
        print '{} version: {}'.format(__pgmname__, __version__)
        self.Module3 = __pgmname__


    def GetModule(self):
        return self.Module3

    def managertest(self):
        print '{}.managerclass.managertest'.format(__pgmname__)
        print 'calling testrun'
        objhandle = testrunclass(self)
        objhandle.testrun()

if __name__ == '__main__':
    print '{}.__main__'.format(__pgmname__)
    objhandle = managerclass()
    objhandle.managertest()
