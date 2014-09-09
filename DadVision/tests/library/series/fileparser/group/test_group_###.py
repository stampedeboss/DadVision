import unittest
from logging import INFO, WARNING, ERROR, DEBUG

from library.series.fileparser import FileParser
from common import logger


class KnownValues(unittest.TestCase):
    File_SxxExx = {}
    File_SxxExx['FileName'] = "/srv/DadVision/Series/Covert Affiars/Season 1/E01 Pilot.mkv"
    File_SxxExx['SeriesName'] = 'Covert Affairs'
    File_SxxExx['SeasonNum'] = 1
    File_SxxExx['EpisodeNums'] = [1]
#    File_SxxExx['type'] = 'episode'
    File_SxxExx['Ext'] = 'mkv'

class fileParserGroup_1(unittest.TestCase):

    def setUp(self):

        TRACE = 5
        VERBOSE = 15

        logger.initialize(unit_test=True, level=INFO)
        self.library = FileParser()
        args = self.library.options.parser.parse_args('--error')

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
    def test_fileparser_group_1_011(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/{Group Name}Covert Affairs 101 Case 011.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_1_012(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/{Group Name}Covert Affairs 0101 Case 012.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_fileparser_group_1_013(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/{Group Name}Covert Affairs 1001 Case 013.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_fileparser_group_1_014(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/{Group Name}Covert Affairs 01001 Case 014.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 02    {Group.Name}Covert.Affairs. ...
    def test_fileparser_group_1_021(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/{Group.Name}Covert.Affairs.101 Case 021.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_1_022(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/{Group.Name}Covert.Affairs.0101 Case 022.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_fileparser_group_1_023(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/{Group.Name}Covert.Affairs.1001 Case 023.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_fileparser_group_1_024(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/{Group.Name}Covert.Affairs.01001 Case 024.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 03    {Group.Name}Covert_Affairs_ ...
    def test_fileparser_group_1_031(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/{Group_Name}Covert_Affairs_101 Case 031.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_1_032(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/{Group_Name}Covert_Affairs_0101 Case 032.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_fileparser_group_1_033(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/{Group_Name}Covert_Affairs_1001 Case 033.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_fileparser_group_1_034(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/{Group_Name}Covert_Affairs_01001 Case 034.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 04    {Group Name} Covert Affairs ...
    def test_fileparser_group_1_041(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/{Group Name} Covert Affairs 101 Case 041.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_1_042(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/{Group Name} Covert Affairs 0101 Case 042.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_fileparser_group_1_043(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/{Group Name} Covert Affairs 1001 Case 043.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_fileparser_group_1_044(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/{Group Name} Covert Affairs 01001 Case 044.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 05    {Group.Name}.Covert.Affairs. ...
    def test_fileparser_group_1_051(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/{Group.Name}.Covert.Affairs.101 Case 051.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_1_052(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/{Group.Name}.Covert.Affairs.0101 Case 052.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_fileparser_group_1_053(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/{Group.Name}.Covert.Affairs.1001 Case 053.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_fileparser_group_1_054(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/{Group.Name}.Covert.Affairs.01001 Case 054.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 06    {Group.Name}_Covert_Affairs_ ...
    def test_fileparser_group_1_061(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/{Group_Name}_Covert_Affairs_101 Case 061.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_1_062(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/{Group_Name}_Covert_Affairs_0101 Case 062.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_fileparser_group_1_063(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/{Group_Name}_Covert_Affairs_1001 Case 063.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_fileparser_group_1_064(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/{Group_Name}_Covert_Affairs_01001 Case 064.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 07    [Group Name] Covert Affairs ...
    def test_fileparser_group_1_071(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/[Group Name] Covert Affairs 101 Case 071.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_1_072(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/[Group Name] Covert Affairs 0101 Case 072.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_fileparser_group_1_073(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/[Group Name] Covert Affairs 1001 Case 073.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_fileparser_group_1_074(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/[Group Name] Covert Affairs 01001 Case 074.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 08    [Group.Name].Covert.Affairs.
    def test_fileparser_group_1_081(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/[Group.Name].Covert.Affairs.101 Case 081.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_1_082(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/[Group.Name].Covert.Affairs.0101 Case 082.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_fileparser_group_1_083(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/[Group.Name].Covert.Affairs.1001 Case 083.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_fileparser_group_1_084(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/[Group.Name].Covert.Affairs.01001 Case 084.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 09    [Group.Name]_Covert_Affairs.
    def test_fileparser_group_1_091(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/[Group_Name]_Covert_Affairs_101 Case 091.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_1_092(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/[Group_Name]_Covert_Affairs_0101 Case 092.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_fileparser_group_1_093(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/[Group_Name]_Covert_Affairs_1001 Case 093.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_fileparser_group_1_094(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/[Group_Name]_Covert_Affairs_01001 Case 094.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 10    [Group Name] - Covert Affairs ...
    def test_fileparser_group_1_101(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/[Group Name] - Covert Affairs 101 Case 101.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_1_102(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/[Group Name] - Covert Affairs 0101 Case 102.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_fileparser_group_1_103(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/[Group Name] - Covert Affairs 1001 Case 103.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_fileparser_group_1_104(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/[Group Name] - Covert Affairs 01001 Case 104.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 11    [Group Name].-.Covert.Affairs ...
    def test_fileparser_group_1_111(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/[Group.Name].-.Covert.Affairs.101 Case 111.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_1_112(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/[Group.Name].-.Covert.Affairs.0101 Case 112.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_fileparser_group_1_113(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/[Group.Name].-.Covert.Affairs.1001 Case 113.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_fileparser_group_1_114(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/[Group.Name].-.Covert.Affairs.01001 Case 114.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 12    [Group Name]_-_Covert_Affairs ...
    def test_fileparser_group_1_121(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/[Group_Name]_-_Covert_Affairs_101 Case 121.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_1_122(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/[Group_Name]_-_Covert_Affairs_0101 Case 122.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_fileparser_group_1_123(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/[Group_Name]_-_Covert_Affairs_1001 Case 0123.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_fileparser_group_1_124(self):
        KnownValues.File_SxxExx["FileName"] = "/srv/Download/Bittorrent/[Group_Name]_-_Covert_Affairs_01001 Case 124.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def theSuite(self):
        suite = unittest.TestLoader().loadTestsFromTestCase(self)
        return suite

if __name__ == '__main__':
    suite = fileParserGroup_1.theSuite()
    unittest.TextTestRunner(verbosity=2).run(suite)
