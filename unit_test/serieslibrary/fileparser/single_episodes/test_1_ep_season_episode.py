
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
    '''
        Test Cases:
            01    Covert Affairs ...
            02    Covert.Affairs. ...
            03    Covert_Affairs_ ...
    '''


# 01    Covert Affairs ...
    def test_FileParser_single_case_011(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs Season 1 Episode 01 Case 011.ext"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_012(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs Season 01 Episode 01 Case 012.ext"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_013(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs Season 1 Episode 001 Case 013.ext"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_014(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs Season 01 Episode 001 Case 014.ext"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 02    Covert.Affairs. ...
    def test_FileParser_single_case_021(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert.Affairs.Season.1.Episode.01.Case.021.ext"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_022(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert.Affairs.Season.01.Episode.01.Case.022.ext"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_023(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert.Affairs.Season.1.Episode.001.Case.023.ext"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_024(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert.Affairs.Season.01.Episode.001.Case.024.ext"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 03    Covert_Affairs_ ...
    def test_FileParser_single_case_031(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert_Affairs_Season_1_Episode_01_Case_031.ext"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_032(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert_Affairs_Season_01_Episode_01_Case_032.ext"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_033(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert_Affairs_Season_1_Episode_001_Case_033.ext"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_034(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert_Affairs_Season_01_Episode_001_Case_034.ext"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def theSuite(self):
        suite = unittest.TestLoader().loadTestsFromTestCase(self)
        return suite

if __name__ == '__main__':
#    suite = unittest.TestLoader().loadTestsFromTestCase(FileParserSingleEps)
    suite = FileParserSingleEps.theSuite()
    unittest.TextTestRunner(verbosity=2).run(suite)
