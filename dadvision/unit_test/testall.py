 """Regression testing framework
   This module will search for scripts in the same directory named
   XYZTest.py.  Each such script should be a test suite that tests a
   module through PyUnit.  (As of Python 2.1, PyUnit is included in
   the standard library as "unittest".)  This script will aggregate all
   found test suites into one big test suite and run them all at once.
   """

   import unittest

   import sys, os, re, unittest

   def regressionTest():
   path = os.path.split(sys.argv[0])[0] or os.getcwd()
   files = os.listdir(path)
   test = re.compile("test.py$", re.IGNORECASE)
   files = filter(test.search, files)
   filenameToModuleName = lambda f: os.path.splitext(f)[0]
   moduleNames = map(filenameToModuleName, files)
   modules = map(__import__, moduleNames)
   load = unittest.defaultTestLoader.loadTestsFromModule
   return unittest.TestSuite(map(load, modules))

   if __name__ == "__main__":
      unittest.main(defaultTest="regressionTest")