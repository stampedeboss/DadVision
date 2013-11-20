from movielibrary.fileparser import FileParser
from common import exceptions
from common import logger
from logging import INFO, WARNING, ERROR, DEBUG
import logging
import unittest
import os
import sys

# A level more detailed than DEBUG
TRACE = 5
# A level more detailed than INFO
VERBOSE = 15

class KnownValues(unittest.TestCase):
    Movie_Details = {}
    Movie_Details['FileName'] = "/mnt/DadVision/Movies/Every Which Way But Loose (1978)/Every Which Way But Loose (1978).mkv"
    Movie_Details['MovieName'] = 'Every Which Way But Loose'
    Movie_Details['Year'] = '1978'
    Movie_Details['Ext'] = 'mkv'

class FileParserMovies(unittest.TestCase):

    def setUp(self):

        logger.initialize(unit_test=True, level=INFO)
#        logger.initialize()
    #   logger.start(level=ERROR)

        self.library = FileParser()
            
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

    def load_date(self, File_Name):
        KnownValues.Movie_Details = {}
        KnownValues.Movie_Details["FileName"] = "/mnt/Download/Bittorrent/{}/{}.mkv".format(File_Name, File_Name)
        KnownValues.Movie_Details['MovieName'] = 'Every Which Way But Loose'
        KnownValues.Movie_Details['Year'] = '1978'
        KnownValues.Movie_Details['Ext'] = 'mkv'

    def load_no_date(self, File_Name):
        KnownValues.Movie_Details = {}
        KnownValues.Movie_Details["FileName"] = "/mnt/Download/Bittorrent/{}/{}.mkv".format(File_Name, File_Name)
        KnownValues.Movie_Details['MovieName'] = 'Every Which Way But Loose'
        KnownValues.Movie_Details['Ext'] = 'mkv'

    def movie_dir_load_date(self, File_Name):
        KnownValues.Movie_Details = {}
        KnownValues.Movie_Details["FileName"] = "/srv/DadVision/Movies/{}/{}.mkv".format(File_Name, File_Name)
        KnownValues.Movie_Details['MovieName'] = 'Every Which Way But Loose'
        KnownValues.Movie_Details['Year'] = '1978'
        KnownValues.Movie_Details['Ext'] = 'mkv'

    def test_FileParser_case_011(self):
        self.load_no_date('every which way but loose')
        self.assertEqual(self.library.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_012(self):
        self.load_no_date('EVERY.WHICH.WAY.BUT.LOOSE')
        self.assertEqual(self.library.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_013(self):
        self.load_no_date('Every_Which_Way_But_Loose')
        self.assertEqual(self.library.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_021(self):
        self.load_no_date('Every Which Way But Loose 720P BluRay x264-LCHD')
        self.assertEqual(self.library.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_022(self):
        self.load_no_date('Every.Which.Way.But.Loose.720P.BluRay.x264-LCHD')
        self.assertEqual(self.library.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_023(self):
        self.load_no_date('Every_Which_Way_But_Loose_720P_BluRay_x264-LCHD')
        self.assertEqual(self.library.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_031(self):
        self.load_date('Every Which Way But Loose 1978 720P BluRay x264-LCHD')
        self.assertEqual(self.library.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_032(self):
        self.load_date('Every.Which.Way.But.Loose.1978.720P.BluRay.x264-LCHD')
        self.assertEqual(self.library.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_033(self):
        self.load_date('Every_Which_Way_But_Loose_1978_720P_BluRay_x264-LCHD')
        self.assertEqual(self.library.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_041(self):
        self.load_date('Every Which Way But Loose (1978) 720P BluRay x264-LCHD')
        self.assertEqual(self.library.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_042(self):
        self.load_date('Every.Which.Way.But.Loose.(1978).720P.BluRay.x264-LCHD')
        self.assertEqual(self.library.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_043(self):
        self.load_date('Every_Which_Way_But_Loose_(1978)_720P_BluRay_x264-LCHD')
        self.assertEqual(self.library.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_051(self):
        self.load_date('Every Which Way But Loose (BDrip 1080p ENG-ITA-GER-SPA) MultiSub x264 bluray (1978)')
        self.assertEqual(self.library.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_052(self):
        self.load_date('Every.Which.Way.But.Loose.(BDrip.1080p.ENG-ITA-GER-SPA).MultiSub.x264.bluray.(1978)')
        self.assertEqual(self.library.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_061(self):
        self.load_date('Every Which Way But Loose [BDrip 1080p ENG-ITA-GER-SPA] MultiSub x264 bluray (1978)')
        self.assertEqual(self.library.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_062(self):
        self.load_date('Every.Which.Way.But.Loose.[BDrip.1080p.ENG-ITA-GER-SPA].MultiSub.x264.bluray.(1978)')
        self.assertEqual(self.library.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_071(self):
        self.load_date('The Clint Eastwood Collection - Every Which Way But Loose (1978) 720P BluRay x264-LCHD')
        self.assertEqual(self.library.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_081(self):
        self.load_date('The Clint Eastwood Collection 05 - Every Which Way But Loose (1978) 720P BluRay x264-LCHD')
        self.assertEqual(self.library.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_091(self):
        self.load_date('1978 - Every Which Way But Loose 720P BluRay x264-LCHD')
        self.assertEqual(self.library.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_101(self):
        self.load_no_date('Arma Letale 2 - Lethal Weapon 2 [BDRip-1080p-MultiLang-MultiSub-Chapters][RiP By MaX]')
        KnownValues.Movie_Details['MovieName'] = 'Lethal Weapon 2'
        self.assertEqual(self.library.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_111(self):
        self.load_no_date('Miracle on 34th Street (BDrip 1080p ENG-ITA-FRE-GER) Multisub x264 bluray (1994)')
        KnownValues.Movie_Details['MovieName'] = 'Miracle On 34th Street'
        KnownValues.Movie_Details['Year'] = '1994'
        self.assertEqual(self.library.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_121(self):
        self.load_no_date('A Very Harold & Kumar3D Christmas (2011) x264 1080p DTS & DD 5.1 NL Subs DMT')
        KnownValues.Movie_Details['MovieName'] = 'A Very Harold & Kumar3D Christmas'
        KnownValues.Movie_Details['Year'] = '2011'
        self.assertEqual(self.library.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_131(self):
        self.load_no_date('Drive.720p.BluRay.X264-BLOW')
        KnownValues.Movie_Details['MovieName'] = 'Drive'
        self.assertEqual(self.library.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_141(self):
        self.load_no_date('James Bond 05 - You Only Live Twice (Ultimate Edition)')
        KnownValues.Movie_Details['MovieName'] = 'You Only Live Twice (Ultimate Edition)'
        self.assertEqual(self.library.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_151(self):
        self.load_no_date('Casino.Royale.2006.720p.BRRip.XviD-SHiRK')
        KnownValues.Movie_Details['MovieName'] = 'Casino Royale'
        KnownValues.Movie_Details['Year'] = '2006'
        self.assertEqual(self.library.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_161(self):
        self.load_no_date('Star.Trek.V.The.Final.Frontier.1989.720p.BluRay.x264-SiNNERS')
        KnownValues.Movie_Details['MovieName'] = 'Star Trek V The Final Frontier'
        KnownValues.Movie_Details['Year'] = '1989'
        self.assertEqual(self.library.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def test_FileParser_case_171(self):
        self.load_no_date('Caccia a Ottobre Rosso - The Hunt for Red October [BDRip-1080p-MultiLang-MultiSub-Chapters][RiP By MaX]')
        KnownValues.Movie_Details['MovieName'] = 'The Hunt For Red October'
        self.assertEqual(self.library.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    @unittest.expectedFailure
    def test_FileParser_case_201(self):
        self.load_no_date('2001 Odissea nello spazio - 2001 A Space Odyssey [BDRip-1080p-MultiLang-MultiSub-Chapters][RiP By MaX]')
        KnownValues.Movie_Details['MovieName'] = '2001 A Space Odyssey'
        self.assertEqual(self.library.getFileDetails(KnownValues.Movie_Details["FileName"]), KnownValues.Movie_Details)

    def theSuite(self):
        suite = unittest.TestLoader().loadTestsFromTestCase(self)
        return suite

if __name__ == '__main__':

    Library.args = self.library.options.parser.parse_args('--error')
    
    suite = FileParserMovies.theSuite()
    unittest.TextTestRunner(verbosity=2).run(suite)
