#!/usr/bin/python /home/aj/workspace/VideoLibrary/daddyvision/movies
'''
Created on Dec 9, 2011

@author: aj
'''
import __init__
import __main__
import manager


__pgmname__ = 'movies.testrun'
__version__ = '$Rev$'

__author__ = "AJ Reynolds"
__copyright__ = "Copyright 2011, AJ Reynolds"
__credits__ = []
__license__ = "GPL"

__maintainer__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"
__status__ = "Development"

print '{}'.format(__pgmname__)

class testrunclass(object):
    def __init__(self, parent):

        print '{}.testrunclass.__init__'.format(__pgmname__)
        print 'movies version: {}'.format(__init__.__version__)
        print '{} version: {}'.format(__pgmname__, __version__)

        print vars(parent)
        print vars()

        print parent.GetModule()

    def testrun(self):
        print '{}.testrunclass.testrun'.format(__pgmname__)
        print 'DONE'

def printVars(object):
    for i in [v for v in dir(object) if not callable(getattr(object,v))]:
        print '\n%s:' % i
        exec('print object.%s\n\n') % i

if __name__ == '__main__':
    print '{}.__main__'.format(__pgmname__)
    objhandle = testrunclass()
    objhandle.testrun()
