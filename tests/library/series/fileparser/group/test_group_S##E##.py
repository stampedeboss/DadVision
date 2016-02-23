import unittest
from logging import INFO

import logger
from series import FileParser


class KnownValues(unittest.TestCase):
    File_SxxExx = {}
    File_SxxExx['FileName'] = "/mnt/DadVision/Series/Covert Affairs/Season 1/E01 Pilot.mkv"
    File_SxxExx['SeriesName'] = 'Covert Affairs'
    File_SxxExx['SeasonNum'] = 1
    File_SxxExx['EpisodeNums'] = [1]
    File_SxxExx['type'] = 'episode'
    File_SxxExx['Ext'] = 'mkv'
#   File_SxxExx['BaseDir'] = '/mnt/DadVision/Series'

class fileParserGroup_3(unittest.TestCase):

    def setUp(self):

        TRACE = 5
        VERBOSE = 15

        logger.initialize(unit_test=True, level=INFO)
#        logger.start(level=ERROR)

        self.library = FileParser()

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
    def test_fileparser_group_3_011(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name}Covert Affairs S1E01 Case 011.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_012(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name}Covert Affairs S01E01 Case 012.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_013(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name}Covert Affairs S1E001 Case 013.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_014(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name}Covert Affairs S01E001 Case 014.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 02    {Group.Name}Covert.Affairs. ...
    def test_fileparser_group_3_021(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}Covert.Affairs.S1E01 Case 021.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_022(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}Covert.Affairs.S01E01 Case 022.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_023(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}Covert.Affairs.S1E001 Case 023.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_024(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}Covert.Affairs.S01E001 Case 024.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 03    {Group.Name}Covert_Affairs_ ...
    def test_fileparser_group_3_031(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}Covert_Affairs_S1E01 Case 031.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_032(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}Covert_Affairs_S01E01 Case 032.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_033(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}Covert_Affairs_S1E001 Case 033.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_034(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}Covert_Affairs_S01E001 Case 034.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 04    {Group Name} Covert Affairs ...
    def test_fileparser_group_3_041(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name} Covert Affairs S1E01 Case 041.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_042(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name} Covert Affairs S01E01 Case 042.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_043(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name} Covert Affairs S1E001 Case 043.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_044(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name} Covert Affairs S01E001 Case 044.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 05    {Group.Name}.Covert.Affairs. ...
    def test_fileparser_group_3_051(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}.Covert.Affairs.S1E01 Case 051.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_052(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}.Covert.Affairs.S01E01 Case 052.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_053(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}.Covert.Affairs.S1E001 Case 053.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_054(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}.Covert.Affairs.S01E001 Case 054.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 06    {Group.Name}_Covert_Affairs_ ...
    def test_fileparser_group_3_061(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}_Covert_Affairs_S1E01 Case 061.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_062(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}_Covert_Affairs_S01E01 Case 062.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_063(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}_Covert_Affairs_S1E001 Case 063.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_064(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}_Covert_Affairs_S01E001 Case 064.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 07    [Group Name] Covert Affairs ...
    def test_fileparser_group_3_071(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] Covert Affairs S1E01 Case 071.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_072(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] Covert Affairs S01E01 Case 072.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_073(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] Covert Affairs S1E001 Case 073.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_074(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] Covert Affairs S01E001 Case 074.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 08    [Group.Name].Covert.Affairs.
    def test_fileparser_group_3_081(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].Covert.Affairs.S1E01 Case 081.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_082(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].Covert.Affairs.S01E01 Case 082.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_083(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].Covert.Affairs.S1E001 Case 083.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_084(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].Covert.Affairs.S01E001 Case 084.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 09    [Group.Name]_Covert_Affairs.
    def test_fileparser_group_3_091(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_Covert_Affairs_S1E01 Case 091.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_092(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_Covert_Affairs_S01E01 Case 092.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_093(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_Covert_Affairs_S1E001 Case 093.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_094(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_Covert_Affairs_S01E001 Case 094.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 10    [Group Name] - Covert Affairs ...
    def test_fileparser_group_3_101(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] - Covert Affairs S1E01 Case 101.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_102(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] - Covert Affairs S01E01 Case 102.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_103(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] - Covert Affairs S1E001 Case 103.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_104(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] - Covert Affairs S01E001 Case 104.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 11    [Group Name].-.Covert.Affairs ...
    def test_fileparser_group_3_111(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].-.Covert.Affairs.S1E01 Case 111.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_112(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].-.Covert.Affairs.S01E01 Case 112.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_113(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].-.Covert.Affairs.S1E001 Case 113.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_114(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].-.Covert.Affairs.S01E001 Case 114.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 12    [Group Name]_-_Covert_Affairs ...
    def test_fileparser_group_3_121(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_-_Covert_Affairs_S1E01 Case 121.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_122(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_-_Covert_Affairs_S01E01 Case 122.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_123(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_-_Covert_Affairs_S1E001 Case 0123.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_fileparser_group_3_124(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_-_Covert_Affairs_S01E001 Case 124.mkv"
        self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def theSuite(self):
        suite = unittest.TestLoader().loadTestsFromTestCase(self)
        return suite

if __name__ == '__main__':
#    suite = unittest.TestLoader().loadTestsFromTestCase(FileParserSingleEps)
    suite = fileParserGroup_3.theSuite()
    unittest.TextTestRunner(verbosity=2).run(suite)
