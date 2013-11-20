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
    File_SxxExx['FileName'] = "/mnt/DadVision/Series/Covert Affairs/Season 1/E01 Pilot.mkv"
    File_SxxExx['SeriesName'] = 'Covert Affairs'
    File_SxxExx['SeasonNum'] = 1
    File_SxxExx['EpisodeNums'] = [1]
    File_SxxExx['Ext'] = 'ext'
#   File_SxxExx['BaseDir'] = '/mnt/DadVision/Series'

class FileParserSingleEps(unittest.TestCase):

    def setUp(self):

        TRACE = 5
        VERBOSE = 15

        logger.initialize(unit_test=True, level=INFO)
#        logger.start(level=ERROR)

        self.library = FileParser()

# Season #/E##
    def test_FileParser_single_case_001(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/DadVision/Series/Covert Affairs/Season 1/E01 Case 001.ext"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_002(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/DadVision/Series/Covert Affairs/Season 01/E01 Case 002.ext"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_003(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/DadVision/Series/Covert Affairs/Season 1/E001 Case 003.ext"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_004(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/DadVision/Series/Covert Affairs/Season 01/E001 Case 004.ext"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_005(self):
        KnownValues.File_SxxExx["FileName"] = "/Series/Covert Affairs/Season 1/E01 Case 005.ext"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def theSuite(self):
        suite = unittest.TestLoader().loadTestsFromTestCase(self)
        return suite

if __name__ == '__main__':
#    suite = unittest.TestLoader().loadTestsFromTestCase(FileParserSingleEps)
    suite = FileParserSingleEps.theSuite()
    unittest.TextTestRunner(verbosity=2).run(suite)
