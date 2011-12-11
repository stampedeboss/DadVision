'''
Created on Dec 9, 2011

@author: aj
'''
import __init__
import __main__
from manager import managerclass

__pgmname__ = 'movies.__main__'
__version__ = '$Rev$'

__author__ = "AJ Reynolds"
__copyright__ = "Copyright 2011, AJ Reynolds"
__credits__ = []
__license__ = "GPL"

__maintainer__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"
__status__ = "Development"

print '{}'.format(__pgmname__)

class maintest():
    def __init__(self):
        print '{}.maintest.__init__'.format(__pgmname__)
        print 'movies version: {}'.format(__init__.__version__)
        print '{} version: {}'.format(__pgmname__, __version__)
        self.Module2 = __pgmname__

    def GetModule(self):
        return self.Module2

    def testmain(self):
        print '{}.maintest.testmain'.format(__pgmname__)
        print 'calling manager'
        objhandle = managerclass()
        objhandle.managertest()

if __name__ == '__main__':
    print '{}.__main__'.format(__pgmname__)

    objhandle = maintest()
    objhandle.testmain()