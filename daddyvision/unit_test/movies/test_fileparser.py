from daddyvision.movies.fileparser import FileParser
from daddyvision.common import exceptions
from daddyvision.common import logger
from daddyvision.common.settings import Settings
from logging import INFO, WARNING, ERROR, DEBUG
import unittest
import os
import sys

class KnownValues(unittest.TestCase):
    Movie_Details = {}
    Movie_Details['FileName'] = "/mnt/DadVision/Movies/Every Which Way But Loose (1978)/Every Which Way But Loose (1978).mkv"
    Movie_Details['MovieName'] = 'Every Which Way But Loose'
    Movie_Details['Year'] = '1978'
    Movie_Details['Ext'] = 'mkv'
    Movie_Details_No_Date = {}
    Movie_Details_No_Date['FileName'] = "/mnt/DadVision/Movies/Every Which Way But Loose (1978)/Every Which Way But Loose (1978).mkv"
    Movie_Details_No_Date['MovieName'] = 'Every Which Way But Loose'
    Movie_Details_No_Date['Ext'] = 'mkv'

class FileParserMovies(unittest.TestCase):

    def setUp(self):

        TRACE = 5
        VERBOSE = 15

        logger.initialize(level=INFO)
#        logger.start(level=ERROR)

        self.config = Settings()
        self.parser = FileParser(self.config)
    '''
        Test Cases:
            Movie Title ...
            Movie Title year ...
            Movie Title (year) ...
            Colletion Name - Movie Title ...
            Colletion Name - Movie Title year...
            Colletion Name - Movie Title (year)...
            year - Movie Title ...
            {Group Name} Movie Title
            {Group Name} Movie Title year
            {Group Name} Movie Title (year)
    '''

#    @unittest.expectedFailure
    def test_FileParser_case_011(self):
        File_Name = 'Every Which Way But Loose 720P BluRay x264-LCHD'
        KnownValues.Movie_Details_No_Date["FileName"] = "/mnt/Download/Bittorrent/{}/{}.mkv".format(File_Name, File_Name)
        self.assertEqual(self.parser.getFileDetails(KnownValues.Movie_Details_No_Date["FileName"]), KnownValues.Movie_Details_No_Date)

    def test_FileParser_case_012(self):
        File_Name = 'Every Which Way But Loose 1978 720P BluRay x264-LCHD'
        KnownValues.Movie_Details["FileName"] = "/mnt/Download/Bittorrent/{}/{}.mkv".format(File_Name, File_Name)
        self.assertEqual(self.parser.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_013(self):
        File_Name = 'Every Which Way But Loose (1978) 720P BluRay x264-LCHD'
        KnownValues.Movie_Details["FileName"] = "/mnt/Download/Bittorrent/{}/{}.mkv".format(File_Name, File_Name)
        self.assertEqual(self.parser.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_014(self):
        File_Name = 'Every Which Way But Loose (BDrip 1080p ENG-ITA-GER-SPA) MultiSub x264 bluray (1978)'
        KnownValues.Movie_Details["FileName"] = "/mnt/Download/Bittorrent/{}/{}.mkv".format(File_Name, File_Name)
        self.assertEqual(self.parser.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_015(self):
        File_Name = 'Every Which Way But Loose [BDrip 1080p ENG-ITA-GER-SPA] MultiSub x264 bluray (1978)'
        KnownValues.Movie_Details["FileName"] = "/mnt/Download/Bittorrent/{}/{}.mkv".format(File_Name, File_Name)
        self.assertEqual(self.parser.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_016(self):
        File_Name = 'The Clint Eastwood Collection - Every Which Way But Loose (1978) 720P BluRay x264-LCHD'
        KnownValues.Movie_Details["FileName"] = "/mnt/Download/Bittorrent/{}/{}.mkv".format(File_Name, File_Name)
        self.assertEqual(self.parser.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_017(self):
        File_Name = 'The Clint Eastwood Collection 05 - Every Which Way But Loose (1978) 720P BluRay x264-LCHD'
        KnownValues.Movie_Details["FileName"] = "/mnt/Download/Bittorrent/{}/{}.mkv".format(File_Name, File_Name)
        self.assertEqual(self.parser.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_018(self):
        File_Name = '1978 - Every Which Way But Loose 720P BluRay x264-LCHD'
        KnownValues.Movie_Details["FileName"] = "/mnt/Download/Bittorrent/{}/{}.mkv".format(File_Name, File_Name)
        self.assertEqual(self.parser.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_019(self):
        File_Name = 'EVERY_WHICH_WAY_BUT_LOOSE'
        KnownValues.Movie_Details_No_Date["FileName"] = "/mnt/Download/Bittorrent/{}/{}.mkv".format(File_Name, File_Name)
        self.assertEqual(self.parser.getFileDetails(KnownValues.Movie_Details_No_Date["FileName"]), KnownValues.Movie_Details_No_Date)

    def test_FileParser_case_021(self):
        File_Name = 'Every.Which.Way.But.Loose.720P.BluRay.x264-LCHD'
        KnownValues.Movie_Details_No_Date["FileName"] = "/mnt/Download/Bittorrent/{}/{}.mkv".format(File_Name, File_Name)
        self.assertEqual(self.parser.getFileDetails(KnownValues.Movie_Details_No_Date["FileName"]), KnownValues.Movie_Details_No_Date)

    def test_FileParser_case_022(self):
        File_Name = 'Every.Which.Way.But.Loose.1978.720P.BluRay.x264-LCHD'
        KnownValues.Movie_Details["FileName"] = "/mnt/Download/Bittorrent/{}/{}.mkv".format(File_Name, File_Name)
        self.assertEqual(self.parser.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_023(self):
        File_Name = 'Every.Which.Way.But.Loose.(1978).720P.BluRay.x264-LCHD'
        KnownValues.Movie_Details["FileName"] = "/mnt/Download/Bittorrent/{}/{}.mkv".format(File_Name, File_Name)
        self.assertEqual(self.parser.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_024(self):
        File_Name = 'Every.Which.Way.But.Loose.(BDrip.1080p.ENG-ITA-GER-SPA).MultiSub.x264.bluray.(1978)'
        KnownValues.Movie_Details["FileName"] = "/mnt/Download/Bittorrent/{}/{}.mkv".format(File_Name, File_Name)
        self.assertEqual(self.parser.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_025(self):
        File_Name = 'Every.Which.Way.But.Loose.[BDrip.1080p.ENG-ITA-GER-SPA].MultiSub.x264.bluray.(1978)'
        KnownValues.Movie_Details["FileName"] = "/mnt/Download/Bittorrent/{}/{}.mkv".format(File_Name, File_Name)
        self.assertEqual(self.parser.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_031(self):
        File_Name = 'Every_Which_Way_But_Loose_720P_BluRay_x264-LCHD'
        KnownValues.Movie_Details_No_Date["FileName"] = "/mnt/Download/Bittorrent/{}/{}.mkv".format(File_Name, File_Name)
        self.assertEqual(self.parser.getFileDetails(KnownValues.Movie_Details_No_Date["FileName"]), KnownValues.Movie_Details_No_Date)

    def test_FileParser_case_032(self):
        File_Name = 'Every_Which_Way_But_Loose_1978_720P_BluRay_x264-LCHD'
        KnownValues.Movie_Details["FileName"] = "/mnt/Download/Bittorrent/{}/{}.mkv".format(File_Name, File_Name)
        self.assertEqual(self.parser.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_033(self):
        File_Name = 'Every_Which_Way_But_Loose_(1978)_720P_BluRay_x264-LCHD'
        KnownValues.Movie_Details["FileName"] = "/mnt/Download/Bittorrent/{}/{}.mkv".format(File_Name, File_Name)
        self.assertEqual(self.parser.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def theSuite(self):
        suite = unittest.TestLoader().loadTestsFromTestCase(self)
        return suite

if __name__ == '__main__':
    suite = FileParserMovies.theSuite()
    unittest.TextTestRunner(verbosity=1).run(suite)
