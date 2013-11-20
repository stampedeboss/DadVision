from library import Library
from serieslibrary.fileparser import FileParser
from common import exceptions
from common import logger
from logging import INFO, WARNING, ERROR, DEBUG
import unittest
import os
import sys

class KnownValues(unittest.TestCase):
    File_SxxExx = {}
    File_SxxExx['FileName'] = "/mnt/DadVision/Series/Covert Affairs 2012/S01/E01 Pilot.mkv"
    File_SxxExx['SeriesName'] = 'Covert Affairs (2012)'
    File_SxxExx['SeasonNum'] = 1
    File_SxxExx['EpisodeNums'] = [1]
    File_SxxExx['Ext'] = 'ext'

class FileParserSingleEps(unittest.TestCase):

    def setUp(self):

        TRACE = 5
        VERBOSE = 15

        logger.initialize(unit_test=True, level=INFO)
#        logger.start(level=ERROR)

        self.library = FileParser()

    '''
        Test Cases:
            01    Covert Affairs 2012...
            02    Covert.Affairs.2012 ...
            03    Covert_Affairs_2012 ...
    '''

# 01    Covert Affairs 2012 ...
    def test_FileParser_single_case_001(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 2012 1x01 Case 001.ext"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_002(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 2012 01x01 Case 002.ext"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_003(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 2012 1x001 Case 003.ext"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_004(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 2012 01x001 Case 004.ext"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 02    Covert.Affairs.2012 ...
    def test_FileParser_single_case_011(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert.Affairs.2012.1x01.Case.014.ext"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_012(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert.Affairs.2012.01x01.Case.015.ext"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_013(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert.Affairs.2012.1x001.Case.016.ext"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_014(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert.Affairs.2012.01x001.Case.017.ext"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 03    Covert_Affairs_2012 ...
    def test_FileParser_single_case_021(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert_Affairs_2012_1x01_Case_018.ext"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_022(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert_Affairs_2012_01x01_Case_019.ext"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_023(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert_Affairs_2012_1x001_Case_020.ext"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_024(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert_Affairs_2012_01x001_Case_021.ext"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def theSuite(self):
        suite = unittest.TestLoader().loadTestsFromTestCase(self)
        return suite

if __name__ == '__main__':
#    suite = unittest.TestLoader().loadTestsFromTestCase(FileParserSingleEps)
    suite = FileParserSingleEps.theSuite()
    unittest.TextTestRunner(verbosity=1).run(suite)
