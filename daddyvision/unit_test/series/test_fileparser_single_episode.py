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

# Season #/E##
    def test_FileParser_single_case_001(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/DadVision/Series/Covert Affairs/Season 1/E01 Case 001.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_002(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/DadVision/Series/Covert Affairs/Season 01/E01 Case 002.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_003(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/DadVision/Series/Covert Affairs/Season 1/E001 Case 003.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_004(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/DadVision/Series/Covert Affairs/Season 01/E001 Case 004.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_005(self):
        KnownValues.File_SxxExx["FileName"] = "/Series/Covert Affairs/Season 1/E01 Case 005.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# S##E##
    def test_FileParser_single_case_006(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs S1E01 Case 006.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_007(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs S01E01 Case 007.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_008(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs S1E001 Case 008.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_009(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs S01E001 Case 009.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_010(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name}Covert Affairs S1E01 Case 010.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_011(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name}Covert Affairs S01E01 Case 011.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_012(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name}Covert Affairs S1E001 Case 012.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_013(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name}Covert Affairs S01E001 Case 013.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_014(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name} Covert Affairs S1E01 Case 014.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_015(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name} Covert Affairs S01E01 Case 015.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_016(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name} Covert Affairs S1E001 Case 016.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_017(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name} Covert Affairs S01E001 Case 017.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_018(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] Covert Affairs S1E01 Case 018.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_019(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] Covert Affairs S01E01 Case 019.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_020(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] Covert Affairs S1E001 Case 020.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_021(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] Covert Affairs S01E001 Case 021.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_022(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] - Covert Affairs S1E01 Case 022.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_023(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] - Covert Affairs S01E01 Case 023.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_024(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] - Covert Affairs S1E001 Case 024.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_025(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] - Covert Affairs S01E001 Case 025.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_026(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert.Affairs.S1E01.Title.ext Case 026.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_027(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert.Affairs.S01E01.Title.ext Case 027.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_028(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert.Affairs.S1E001.Title.ext Case 028.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_029(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert.Affairs.S01E001.Title.ext Case 029.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_030(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}Covert.Affairs.S1E01 Case 030.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_031(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}Covert.Affairs.S01E01 Case 031.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_032(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}Covert.Affairs.S1E001 Case 032.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_033(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}Covert.Affairs.S01E001 Case 033.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_034(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}.Covert.Affairs.S1E01 Case 034.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_035(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}.Covert.Affairs.S01E01 Case 035.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_036(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}.Covert.Affairs.S1E001 Case 036.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_037(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}.Covert.Affairs.S01E001 Case 037.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_038(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].Covert.Affairs.S1E01 Case 038.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_039(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].Covert.Affairs.S01E01 Case 039.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_040(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].Covert.Affairs.S1E001 Case 040.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_041(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].Covert.Affairs.S01E001 Case 041.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_042(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].-.Covert.Affairs.S1E01 Case 042.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_043(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].-.Covert.Affairs.S01E01 Case 043.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_044(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].-.Covert.Affairs.S1E001 Case 044.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_045(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].-.Covert.Affairs.S01E001 Case 045.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_046(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert_Affairs_S1E01_Title.ext Case 046.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_047(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert_Affairs_S01E01_Title.ext Case 047.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_048(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert_Affairs_S1E001_Title.ext Case 048.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_049(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert_Affairs_S01E001_Title.ext Case 049.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_050(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}Covert_Affairs_S1E01 Case 050.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_051(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}Covert_Affairs_S01E01 Case 051.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_052(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}Covert_Affairs_S1E001 Case 052.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_053(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}Covert_Affairs_S01E001 Case 053.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_054(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}_Covert_Affairs_S1E01 Case 054.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_055(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}_Covert_Affairs_S01E01 Case 055.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_056(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}_Covert_Affairs_S1E001 Case 056.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_057(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}_Covert_Affairs_S01E001 Case 057.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_058(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_Covert_Affairs_S1E01 Case 058.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_059(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_Covert_Affairs_S01E01 Case 059.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_060(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_Covert_Affairs_S1E001 Case 060.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_061(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_Covert_Affairs_S01E001 Case 061.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_062(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_-_Covert_Affairs_S1E01 Case 062.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_063(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_-_Covert_Affairs_S01E01 Case 063.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_064(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_-_Covert_Affairs_S1E001 Case 064.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_065(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_-_Covert_Affairs_S01E001 Case 065.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# #x##
    def test_FileParser_single_case_066(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 1x01 Case 066.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_067(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 01x01 Case 067.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_068(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 1x001 Case 068.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_069(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 01x001 Case 069.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_070(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name}Covert Affairs 1x01 Case 070.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_071(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name}Covert Affairs 01x01 Case 071.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_072(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name}Covert Affairs 1x001 Case 072.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_073(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name}Covert Affairs 01x001 Case 073.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_074(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name} Covert Affairs 1x01 Case 074.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_075(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name} Covert Affairs 01x01 Case 075.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_076(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name} Covert Affairs 1x001 Case 076.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_077(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name} Covert Affairs 01x001 Case 077.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_078(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] Covert Affairs 1x01 Case 078.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_079(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] Covert Affairs 01x01 Case 079.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_080(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] Covert Affairs 1x001 Case 080.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_081(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] Covert Affairs 01x001 Case 081.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_082(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] - Covert Affairs 1x01 Case 082.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_083(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] - Covert Affairs 01x01 Case 083.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_084(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] - Covert Affairs 1x001 Case 084.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_085(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] - Covert Affairs 01x001 Case 085.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_086(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert.Affairs.1x01.Title.ext Case 086.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_087(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert.Affairs.01x01.Title.ext Case 087.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_088(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert.Affairs.1x001.Title.ext Case 088.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_089(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert.Affairs.01x001.Title.ext Case 089.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_090(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}Covert.Affairs.1x01 Case 090.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_091(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}Covert.Affairs.01x01 Case 091.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_092(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}Covert.Affairs.1x001 Case 092.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_093(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}Covert.Affairs.01x001 Case 093.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_094(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}.Covert.Affairs.1x01 Case 094.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_095(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}.Covert.Affairs.01x01 Case 095.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_096(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}.Covert.Affairs.1x001 Case 096.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_097(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}.Covert.Affairs.01x001 Case 097.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_098(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].Covert.Affairs.1x01 Case 098.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_099(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].Covert.Affairs.01x01 Case 099.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_100(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].Covert.Affairs.1x001 Case 100.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_101(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].Covert.Affairs.01x001 Case 101.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_102(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].-.Covert.Affairs.1x01 Case 102.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_103(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].-.Covert.Affairs.01x01 Case 103.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_104(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].-.Covert.Affairs.1x001 Case 104.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_105(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].-.Covert.Affairs.01x001 Case 105.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_106(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert_Affairs_1x01_Title.ext Case 106.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_107(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert_Affairs_01x01_Title.ext Case 107.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_108(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert_Affairs_1x001_Title.ext Case 108.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_109(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert_Affairs_01x001_Title.ext Case 109.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_110(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}Covert_Affairs_1x01 Case 110.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_111(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}Covert_Affairs_01x01 Case 111.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_112(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}Covert_Affairs_1x001 Case 112.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_113(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}Covert_Affairs_01x001 Case 113.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_114(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}_Covert_Affairs_1x01 Case 114.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_115(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}_Covert_Affairs_01x01 Case 115.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_116(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}_Covert_Affairs_1x001 Case 116.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_117(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}_Covert_Affairs_01x001 Case 117.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_118(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_Covert_Affairs_1x01 Case 118.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_119(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_Covert_Affairs_01x01 Case 119.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_120(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_Covert_Affairs_1x001 Case 120.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_121(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_Covert_Affairs_01x001 Case 121.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_122(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_-_Covert_Affairs_1x01 Case 122.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_123(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_-_Covert_Affairs_01x01 Case 123.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_124(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_-_Covert_Affairs_1x001 Case 124.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_125(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_-_Covert_Affairs_01x001 Case 125.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# ###
    def test_FileParser_single_case_126(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 101 Case 126.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_127(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 0101 Case 127.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_128(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 1001 Case 128.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_129(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 01001 Case 129.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_130(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name}Covert Affairs 101 Case 130.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_131(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name}Covert Affairs 0101 Case 131.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_132(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name}Covert Affairs 1001 Case 132.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_133(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name}Covert Affairs 01001 Case 133.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_134(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name} Covert Affairs 101 Case 134.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_135(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name} Covert Affairs 0101 Case 135.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_136(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name} Covert Affairs 1001 Case 136.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_137(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name} Covert Affairs 01001 Case 137.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_138(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] Covert Affairs 101 Case 138.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_139(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] Covert Affairs 0101 Case 139.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_140(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] Covert Affairs 1001 Case 140.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_141(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] Covert Affairs 01001 Case 141.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_142(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] - Covert Affairs 101 Case 142.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_143(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] - Covert Affairs 0101 Case 143.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_144(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] - Covert Affairs 1001 Case 144.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_145(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] - Covert Affairs 01001 Case 145.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_146(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert.Affairs.101.Title.ext Case 146.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_147(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert.Affairs.0101.Title.ext Case 147.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_148(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert.Affairs.1001.Title.ext Case 148.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_149(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert.Affairs.01001.Title.ext Case 149.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_150(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}Covert.Affairs.101 Case 150.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_151(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}Covert.Affairs.0101 Case 151.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_152(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}Covert.Affairs.1001 Case 152.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_153(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}Covert.Affairs.01001 Case 153.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_154(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}.Covert.Affairs.101 Case 154.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_155(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}.Covert.Affairs.0101 Case 155.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_156(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}.Covert.Affairs.1001 Case 156.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_157(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}.Covert.Affairs.01001 Case 157.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_158(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].Covert.Affairs.101 Case 158.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_159(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].Covert.Affairs.0101 Case 159.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_160(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].Covert.Affairs.1001 Case 160.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_161(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].Covert.Affairs.01001 Case 161.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_162(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].-.Covert.Affairs.101 Case 162.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_163(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].-.Covert.Affairs.0101 Case 163.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_164(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].-.Covert.Affairs.1001 Case 164.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_165(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].-.Covert.Affairs.01001 Case 165.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_166(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert_Affairs_101_Title.ext Case 166.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_167(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert_Affairs_0101_Title.ext Case 167.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_168(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert_Affairs_1001_Title.ext Case 168.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_169(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert_Affairs_01001_Title.ext Case 169.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_170(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}Covert_Affairs_101 Case 170.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_171(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}Covert_Affairs_0101 Case 171.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_172(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}Covert_Affairs_1001 Case 172.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_173(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}Covert_Affairs_01001 Case 173.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_174(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}_Covert_Affairs_101 Case 174.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_175(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}_Covert_Affairs_0101 Case 175.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_176(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}_Covert_Affairs_1001 Case 176.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_177(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}_Covert_Affairs_01001 Case 177.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_178(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_Covert_Affairs_101 Case 178.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_179(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_Covert_Affairs_0101 Case 179.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_180(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_Covert_Affairs_1001 Case 180.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_181(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_Covert_Affairs_01001 Case 181.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_182(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_-_Covert_Affairs_101 Case 182.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_single_case_183(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_-_Covert_Affairs_0101 Case 183.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_184(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_-_Covert_Affairs_1001 Case 184.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    @unittest.expectedFailure
    def test_FileParser_single_case_185(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_-_Covert_Affairs_01001 Case 185.ext"
        self.assertEqual(self.parser.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def theSuite(self):
        suite = unittest.TestLoader().loadTestsFromTestCase(self)
        return suite        

if __name__ == '__main__':
#    suite = unittest.TestLoader().loadTestsFromTestCase(FileParserSingleEps)
    suite = FileParserSingleEps.theSuite()
    unittest.TextTestRunner(verbosity=2).run(suite)
