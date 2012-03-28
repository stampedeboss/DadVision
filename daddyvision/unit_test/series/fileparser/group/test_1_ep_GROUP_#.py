from daddyvision.series.fileparser import FileParser
from daddyvision.common import exceptions
from daddyvision.common import logger
from logging import INFO, WARNING, ERROR, DEBUG
import unittest
import os
import sys

class KnownValues(unittest.TestCase):
    File_SxxExx = {}
    File_SxxExx['FileName'] = "/mnt/DadVision/Series/Covert Affiars/Season 1/E01 Pilot.mkv"
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
            01    {Group Name}Covert Affairs ...
            02    {Group.Name}Covert.Affairs. ...
            03    {Group.Name}Covert_Affairs_ ...
            04    {Group Name} Covert Affairs ...
            05    {Group.Name}.Covert.Affairs. ...
            06    {Group.Name}_Covert_Affairs_ ...
            07    [Group Name] Covert Affairs ...
            08    [Group.Name].Covert.Affairs.
            09    [Group.Name]_Covert_Affairs.
            10    [Group Name] - Covert Affairs ...
            11    [Group Name].-.Covert.Affairs ...
            12    [Group Name]_-_Covert_Affairs ...
    '''

# 01    {Group Name}Covert Affairs ...
    def test_FileParser_single_case_011(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name}Covert Affairs 101 Case 011.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_012(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name}Covert Affairs 0101 Case 012.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_013(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name}Covert Affairs 1001 Case 013.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_014(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name}Covert Affairs 01001 Case 014.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 02    {Group.Name}Covert.Affairs. ...
    def test_FileParser_single_case_021(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}Covert.Affairs.101 Case 021.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_022(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}Covert.Affairs.0101 Case 022.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_023(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}Covert.Affairs.1001 Case 023.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_024(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}Covert.Affairs.01001 Case 024.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 03    {Group.Name}Covert_Affairs_ ...
    def test_FileParser_single_case_031(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}Covert_Affairs_101 Case 031.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_032(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}Covert_Affairs_0101 Case 032.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_033(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}Covert_Affairs_1001 Case 033.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_034(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}Covert_Affairs_01001 Case 034.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 04    {Group Name} Covert Affairs ...
    def test_FileParser_single_case_041(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name} Covert Affairs 101 Case 041.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_042(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name} Covert Affairs 0101 Case 042.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_043(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name} Covert Affairs 1001 Case 043.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_044(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name} Covert Affairs 01001 Case 044.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 05    {Group.Name}.Covert.Affairs. ...
    def test_FileParser_single_case_051(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}.Covert.Affairs.101 Case 051.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_052(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}.Covert.Affairs.0101 Case 052.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_053(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}.Covert.Affairs.1001 Case 053.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_054(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}.Covert.Affairs.01001 Case 054.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 06    {Group.Name}_Covert_Affairs_ ...
    def test_FileParser_single_case_061(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}_Covert_Affairs_101 Case 061.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_062(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}_Covert_Affairs_0101 Case 062.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_063(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}_Covert_Affairs_1001 Case 063.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_064(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}_Covert_Affairs_01001 Case 064.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 07    [Group Name] Covert Affairs ...
    def test_FileParser_single_case_071(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] Covert Affairs 101 Case 071.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_072(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] Covert Affairs 0101 Case 072.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_073(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] Covert Affairs 1001 Case 073.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_074(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] Covert Affairs 01001 Case 074.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 08    [Group.Name].Covert.Affairs.
    def test_FileParser_single_case_081(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].Covert.Affairs.101 Case 081.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_082(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].Covert.Affairs.0101 Case 082.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_083(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].Covert.Affairs.1001 Case 083.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_084(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].Covert.Affairs.01001 Case 084.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 09    [Group.Name]_Covert_Affairs.
    def test_FileParser_single_case_091(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_Covert_Affairs_101 Case 091.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_092(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_Covert_Affairs_0101 Case 092.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_093(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_Covert_Affairs_1001 Case 093.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_094(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_Covert_Affairs_01001 Case 094.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 10    [Group Name] - Covert Affairs ...
    def test_FileParser_single_case_101(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] - Covert Affairs 101 Case 101.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_102(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] - Covert Affairs 0101 Case 102.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_103(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] - Covert Affairs 1001 Case 103.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_104(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] - Covert Affairs 01001 Case 104.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 11    [Group Name].-.Covert.Affairs ...
    def test_FileParser_single_case_111(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].-.Covert.Affairs.101 Case 111.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_112(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].-.Covert.Affairs.0101 Case 112.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_113(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].-.Covert.Affairs.1001 Case 113.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_114(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].-.Covert.Affairs.01001 Case 114.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 12    [Group Name]_-_Covert_Affairs ...
    def test_FileParser_single_case_121(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_-_Covert_Affairs_101 Case 121.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_122(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_-_Covert_Affairs_0101 Case 122.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_123(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_-_Covert_Affairs_1001 Case 0123.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_124(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_-_Covert_Affairs_01001 Case 124.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def theSuite(self):
        suite = unittest.TestLoader().loadTestsFromTestCase(self)
        return suite

if __name__ == '__main__':
#    suite = unittest.TestLoader().loadTestsFromTestCase(FileParserSingleEps)
    suite = FileParserSingleEps.theSuite()
    unittest.TextTestRunner(verbosity=1).run(suite)
