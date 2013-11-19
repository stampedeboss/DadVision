from daddyvision.series.fileparser import FileParser
from daddyvision.common import exceptions
from daddyvision.common import logger
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

        self.parser = FileParser()
    '''
        Test Cases:
            01    Covert Affairs ...
            02    Covert.Affairs. ...
            03    Covert_Affairs_ ...
    '''


# 01    Covert Affairs ...
    def test_FileParser_single_case_001(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs S1E01 Case 006.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_002(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs S01E01 Case 007.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_003(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs S1E001 Case 008.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_004(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs S01E001 Case 009.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 02    Covert.Affairs. ...
    def test_FileParser_single_case_021(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert.Affairs.S1E01.Title.ext Case 026.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_022(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert.Affairs.S01E01.Title.ext Case 027.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_023(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert.Affairs.S1E001.Title.ext Case 028.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_024(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert.Affairs.S01E001.Title.ext Case 029.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 03    Covert_Affairs_ ...
    def test_FileParser_single_case_031(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert_Affairs_S1E01_Title.ext Case 046.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_032(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert_Affairs_S01E01_Title.ext Case 047.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_033(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert_Affairs_S1E001_Title.ext Case 048.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_034(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert_Affairs_S01E001_Title.ext Case 049.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def theSuite(self):
        suite = unittest.TestLoader().loadTestsFromTestCase(self)
        return suite

if __name__ == '__main__':
#    suite = unittest.TestLoader().loadTestsFromTestCase(FileParserSingleEps)
    suite = FileParserSingleEps.theSuite()
    unittest.TextTestRunner(verbosity=2).run(suite)
