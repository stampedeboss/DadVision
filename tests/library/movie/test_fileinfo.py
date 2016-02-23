import unittest
from logging import INFO
from os.path import splitext

import logger
from movie import FileInfo

# A level more detailed than DEBUG
TRACE = 5
# A level more detailed than INFO
VERBOSE = 15

class FileInfoMovies(unittest.TestCase):

	def setUp(self):

		logger.initialize(unit_test=True, level=INFO)
		self.library = FileInfo()
		self.kv = {}

	def load_date(self, File_Name):
		self.kv = {}
		self.kv["filename"] = "/mnt/Download/Bittorrent/{}/{}.mkv".format(splitext(File_Name)[0],
																		  File_Name)
		self.kv['title'] = 'Every Which Way But Loose'
		self.kv['year'] = 1978
		self.kv['type'] = 'movie'
		self.kv['container'] = 'mkv'

	def load_no_date(self, File_Name):
		self.kv = {}
		self.kv["filename"] = "/mnt/Download/Bittorrent/{}/{}.mkv".format(splitext(File_Name)[0],
																		  File_Name)
		self.kv['title'] = 'Every Which Way But Loose'
		self.kv['type'] = 'movie'
		self.kv['container'] = 'mkv'

	def movie_dir_load_date(self, File_Name):
		self.kv = {}
		self.kv["filename"] = "/srv/DadVision/Movies/{}/{}.mkv".format(splitext(File_Name)[0],
																	   File_Name)
		self.kv['title'] = 'Every Which Way But Loose'
		self.kv['year'] = 1978
		self.kv['type'] = 'movie'
		self.kv['container'] = 'mkv'

	def test_FileInfo_case_011(self):
		self.load_no_date('every which way but loose')
		rc = self.library.get_movie_details(self.kv["filename"])
		self.assertDictContainsSubset(self.kv, rc)

	def test_FileParser_case_012(self):
		self.load_no_date('EVERY.WHICH.WAY.BUT.LOOSE')
		rc = self.library.get_movie_details(self.kv["filename"])
		self.assertDictContainsSubset(self.kv, rc)

	def test_FileParser_case_013(self):
		self.load_no_date('Every_Which_Way_But_Loose')
		rc = self.library.get_movie_details(self.kv["filename"])
		self.assertDictContainsSubset(self.kv, rc)

	def test_FileParser_case_021(self):
		self.load_no_date('Every Which Way But Loose 720P BluRay x264-LCHD')
		rc = self.library.get_movie_details(self.kv["filename"])
		self.assertDictContainsSubset(self.kv, rc)

	def test_FileParser_case_022(self):
		self.load_no_date('Every.Which.Way.But.Loose.720P.BluRay.x264-LCHD')
		rc = self.library.get_movie_details(self.kv["filename"])
		self.assertDictContainsSubset(self.kv, rc)

	def test_FileParser_case_023(self):
		self.load_no_date('Every_Which_Way_But_Loose_720P_BluRay_x264-LCHD')
		rc = self.library.get_movie_details(self.kv["filename"])
		self.assertDictContainsSubset(self.kv, rc)

	def test_FileParser_case_031(self):
		self.load_date('Every Which Way But Loose 1978 720P BluRay x264-LCHD')
		rc = self.library.get_movie_details(self.kv["filename"])
		self.assertDictContainsSubset(self.kv, rc)

	def test_FileParser_case_032(self):
		self.load_date('Every.Which.Way.But.Loose.1978.720P.BluRay.x264-LCHD')
		rc = self.library.get_movie_details(self.kv["filename"])
		self.assertDictContainsSubset(self.kv, rc)

	def test_FileParser_case_033(self):
		self.load_date('Every_Which_Way_But_Loose_1978_720P_BluRay_x264-LCHD')
		rc = self.library.get_movie_details(self.kv["filename"])
		self.assertDictContainsSubset(self.kv, rc)

	def test_FileParser_case_041(self):
		self.load_date('Every Which Way But Loose (1978) 720P BluRay x264-LCHD')
		rc = self.library.get_movie_details(self.kv["filename"])
		self.assertDictContainsSubset(self.kv, rc)

	def test_FileParser_case_042(self):
		self.load_date('Every.Which.Way.But.Loose.(1978).720P.BluRay.x264-LCHD')
		rc = self.library.get_movie_details(self.kv["filename"])
		self.assertDictContainsSubset(self.kv, rc)

	def test_FileParser_case_043(self):
		self.load_date('Every_Which_Way_But_Loose_(1978)_720P_BluRay_x264-LCHD')
		rc = self.library.get_movie_details(self.kv["filename"])
		self.assertDictContainsSubset(self.kv, rc)

	def test_FileParser_case_051(self):
		self.load_date('Every Which Way But Loose (BDrip 1080p ENG-ITA-GER-SPA) MultiSub x264 bluray (1978)')
		rc = self.library.get_movie_details(self.kv["filename"])
		self.assertDictContainsSubset(self.kv, rc)

	def test_FileParser_case_052(self):
		self.load_date('Every.Which.Way.But.Loose.(BDrip.1080p.ENG-ITA-GER-SPA).MultiSub.x264.bluray.(1978)')
		rc = self.library.get_movie_details(self.kv["filename"])
		self.assertDictContainsSubset(self.kv, rc)

	def test_FileParser_case_061(self):
		self.load_date('Every Which Way But Loose [BDrip 1080p ENG-ITA-GER-SPA] MultiSub x264 bluray (1978)')
		rc = self.library.get_movie_details(self.kv["filename"])
		self.assertDictContainsSubset(self.kv, rc)

	def test_FileParser_case_062(self):
		self.load_date('Every.Which.Way.But.Loose.[BDrip.1080p.ENG-ITA-GER-SPA].MultiSub.x264.bluray.(1978)')
		rc = self.library.get_movie_details(self.kv["filename"])
		self.assertDictContainsSubset(self.kv, rc)

	def test_FileParser_case_071(self):
		self.load_date('The Clint Eastwood Collection - Every Which Way But Loose (1978) 720P BluRay x264-LCHD')
		rc = self.library.get_movie_details(self.kv["filename"])
		self.assertDictContainsSubset(self.kv, rc)

	def test_FileParser_case_081(self):
		self.load_date('The Clint Eastwood Collection 05 - Every Which Way But Loose (1978) 720P BluRay x264-LCHD')
		rc = self.library.get_movie_details(self.kv["filename"])
		self.assertDictContainsSubset(self.kv, rc)

	def test_FileParser_case_091(self):
		self.load_date('1978 - Every Which Way But Loose 720P BluRay x264-LCHD')
		rc = self.library.get_movie_details(self.kv["filename"])
		self.assertDictContainsSubset(self.kv, rc)

	def test_FileParser_case_101(self):
		self.load_no_date('Arma Letale 2 - Lethal Weapon 2 [BDRip-1080p-MultiLang-MultiSub-Chapters][RiP By MaX]')
		self.kv['title'] = 'Lethal Weapon 2'
		rc = self.library.get_movie_details(self.kv["filename"])
		self.assertDictContainsSubset(self.kv, rc)

	def test_FileParser_case_111(self):
		self.load_no_date('Miracle on 34th Street (BDrip 1080p ENG-ITA-FRE-GER) Multisub x264 bluray (1994)')
		self.kv['title'] = 'Miracle on 34th Street'
		self.kv['year'] = 1994
		rc = self.library.get_movie_details(self.kv["filename"])
		self.assertDictContainsSubset(self.kv, rc)

	def test_FileParser_case_121(self):
		self.load_no_date('A Very Harold & Kumar3D Christmas (2011) x264 1080p DTS & DD 5.1 NL Subs DMT')
		self.kv['title'] = 'A Very Harold & Kumar3D Christmas'
		self.kv['year'] = 2011
		rc = self.library.get_movie_details(self.kv["filename"])
		self.assertDictContainsSubset(self.kv, rc)

	def test_FileParser_case_131(self):
		self.load_no_date('Drive.720p.BluRay.X264-BLOW')
		self.kv['title'] = 'Drive'
		rc = self.library.get_movie_details(self.kv["filename"])
		self.assertDictContainsSubset(self.kv, rc)

	def test_FileParser_case_141(self):
		self.load_no_date('James Bond - You Only Live Twice (Ultimate Edition).720p.BRRip.XviD-SHiRK')
		self.kv['title'] = 'You Only Live Twice'
		rc = self.library.get_movie_details(self.kv["filename"])
		self.assertDictContainsSubset(self.kv, rc)

	def test_FileParser_case_151(self):
		self.load_no_date('Casino.Royale.2006.720p.BRRip.XviD-SHiRK')
		self.kv['title'] = 'Casino Royale'
		self.kv['year'] = 2006
		rc = self.library.get_movie_details(self.kv["filename"])
		self.assertDictContainsSubset(self.kv, rc)

	def test_FileParser_case_161(self):
		self.load_no_date('Star.Trek.V.The.Final.Frontier.1989.720p.BluRay.x264-SiNNERS')
		self.kv['title'] = 'Star Trek V the Final Frontier'
		self.kv['year'] = 1989
		rc = self.library.get_movie_details(self.kv["filename"])
		self.assertDictContainsSubset(self.kv, rc)

	def test_FileParser_case_171(self):
		self.load_no_date('Caccia a Ottobre Rosso - The Hunt for Red October [BDRip-1080p-MultiLang-MultiSub-Chapters][RiP By MaX]')
		self.kv['title'] = 'The Hunt for Red October'
		rc = self.library.get_movie_details(self.kv["filename"])
		self.assertDictContainsSubset(self.kv, rc)

	@unittest.expectedFailure
	def test_FileParser_case_201(self):
		self.load_no_date('2001 Odissea nello spazio - 2001 A Space Odyssey [BDRip-1080p-MultiLang-MultiSub-Chapters][RiP By MaX]')
		self.kv['title'] = '2001 A Space Odyssey'
		rc = self.library.get_movie_details(self.kv["filename"])
		self.assertDictContainsSubset(self.kv, rc)

	def theSuite(self):
		suite = unittest.TestLoader().loadTestsFromTestCase(self)
		return suite

if __name__ == '__main__':

	FileInfo.args = FileInfo.cmdoptions.ParseArgs('--error')

	suite = FileInfoMovies.theSuite()
	unittest.TextTestRunner(verbosity=2).run(suite)
