import unittest
from logging import INFO

import logger
from series import FileParser


class KnownValues(unittest.TestCase):
	File_SxxExx = {}
	File_SxxExx['FileName'] = "/mnt/DadVision/Series/Covert Affairs 2012/Season 1/E01 Pilot.mkv"
	File_SxxExx['SeriesName'] = 'Covert Affairs (2012)'
	File_SxxExx['SeasonNum'] = 1
	File_SxxExx['EpisodeNums'] = [1]
	File_SxxExx['type'] = 'episode'
	File_SxxExx['Ext'] = 'ext'
#   File_SxxExx['BaseDir'] = '/mnt/DadVision/Series'

class fileParserGroup_5(unittest.TestCase):

	def setUp(self):

		TRACE = 5
		VERBOSE = 15

		logger.initialize(unit_test=True, level=INFO)
#        logger.start(level=ERROR)

		self.library = FileParser()

	'''
		Test Cases:
			01    {Group Name}Covert Affairs 2012 ...
			02    {Group.Name}Covert.Affairs.2012. ...
			03    {Group.Name}Covert_Affairs_2012_ ...
			04    {Group Name} Covert Affairs 2012 ...
			05    {Group.Name}.Covert.Affairs.2012. ...
			06    {Group.Name}_Covert_Affairs_2012_ ...
			07    [Group Name] Covert Affairs 2012 ...
			08    [Group.Name].Covert.Affairs.2012.
			09    [Group.Name]_Covert_Affairs_2012.
			10    [Group Name] - Covert Affairs 2012 ...
			11    [Group Name].-.Covert.Affairs.2012 ...
			12    [Group Name]_-_Covert_Affairs_2012 ...
	'''

# 01    {Group Name}Covert Affairs 2012 ...
	def test_fileparser_group_5_011(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name}Covert Affairs 2012 S1E01 Case 011.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_012(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name}Covert Affairs 2012 S01E01 Case 012.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_013(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name}Covert Affairs 2012 S1E001 Case 013.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_014(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name}Covert Affairs 2012 S01E001 Case 014.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 02    {Group.Name}Covert.Affairs.2012. ...
	def test_fileparser_group_5_021(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}Covert.Affairs.2012.S1E01 Case 021.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_022(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}Covert.Affairs.2012.S01E01 Case 022.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_023(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}Covert.Affairs.2012.S1E001 Case 023.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_024(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}Covert.Affairs.2012.S01E001 Case 024.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 03    {Group.Name}Covert_Affairs_2012_ ...
	def test_fileparser_group_5_031(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}Covert_Affairs_2012_S1E01 Case 031.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_032(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}Covert_Affairs_2012_S01E01 Case 032.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_033(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}Covert_Affairs_2012_S1E001 Case 033.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_034(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}Covert_Affairs_2012_S01E001 Case 034.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 04    {Group Name} Covert Affairs 2012 ...
	def test_fileparser_group_5_041(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name} Covert Affairs 2012 S1E01 Case 041.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_042(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name} Covert Affairs 2012 S01E01 Case 042.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_043(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name} Covert Affairs 2012 S1E001 Case 043.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_044(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group Name} Covert Affairs 2012 S01E001 Case 044.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 05    {Group.Name}.Covert.Affairs.2012. ...
	def test_fileparser_group_5_051(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}.Covert.Affairs.2012.S1E01 Case 051.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_052(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}.Covert.Affairs.2012.S01E01 Case 052.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_053(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}.Covert.Affairs.2012.S1E001 Case 053.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_054(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group.Name}.Covert.Affairs.2012.S01E001 Case 054.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 06    {Group.Name}_Covert_Affairs_2012_ ...
	def test_fileparser_group_5_061(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}_Covert_Affairs_2012_S1E01 Case 061.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_062(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}_Covert_Affairs_2012_S01E01 Case 062.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_063(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}_Covert_Affairs_2012_S1E001 Case 063.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_064(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/{Group_Name}_Covert_Affairs_2012_S01E001 Case 064.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 07    [Group Name] Covert Affairs 2012 ...
	def test_fileparser_group_5_071(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] Covert Affairs 2012 S1E01 Case 071.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_072(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] Covert Affairs 2012 S01E01 Case 072.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_073(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] Covert Affairs 2012 S1E001 Case 073.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_074(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] Covert Affairs 2012 S01E001 Case 074.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 08    [Group.Name].Covert.Affairs.2012.
	def test_fileparser_group_5_081(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].Covert.Affairs.2012.S1E01 Case 081.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_082(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].Covert.Affairs.2012.S01E01 Case 082.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_083(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].Covert.Affairs.2012.S1E001 Case 083.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_084(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].Covert.Affairs.2012.S01E001 Case 084.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 09    [Group.Name]_Covert_Affairs_2012.
	def test_fileparser_group_5_091(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_Covert_Affairs_2012_S1E01 Case 091.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_092(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_Covert_Affairs_2012_S01E01 Case 092.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_093(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_Covert_Affairs_2012_S1E001 Case 093.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_094(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_Covert_Affairs_2012_S01E001 Case 094.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 10    [Group Name] - Covert Affairs 2012 ...
	def test_fileparser_group_5_101(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] - Covert Affairs 2012 S1E01 Case 101.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_102(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] - Covert Affairs 2012 S01E01 Case 102.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_103(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] - Covert Affairs 2012 S1E001 Case 103.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_104(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group Name] - Covert Affairs 2012 S01E001 Case 104.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 11    [Group Name].-.Covert.Affairs.2012 ...
	def test_fileparser_group_5_111(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].-.Covert.Affairs.2012.S1E01 Case 111.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_112(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].-.Covert.Affairs.2012.S01E01 Case 112.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_113(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].-.Covert.Affairs.2012.S1E001 Case 113.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_114(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group.Name].-.Covert.Affairs.2012.S01E001 Case 114.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# 12    [Group Name]_-_Covert_Affairs_2012 ...
	def test_fileparser_group_5_121(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_-_Covert_Affairs_2012_S1E01 Case 121.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_122(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_-_Covert_Affairs_2012_S01E01 Case 122.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_123(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_-_Covert_Affairs_2012_S1E001 Case 0123.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def test_fileparser_group_5_124(self):
		KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/[Group_Name]_-_Covert_Affairs_2012_S01E001 Case 124.ext"
		self.assertEqual(self.library.getFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

	def theSuite(self):
		suite = unittest.TestLoader().loadTestsFromTestCase(self)
		return suite

if __name__ == '__main__':
#    suite = unittest.TestLoader().loadTestsFromTestCase(FileParserSingleEps)
	suite = fileParserGroup_5.theSuite()
	unittest.TextTestRunner(verbosity=2).run(suite)
