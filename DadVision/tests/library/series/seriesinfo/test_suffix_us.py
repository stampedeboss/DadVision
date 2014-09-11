import unittest

from library.series.seriesinfo import SeriesInfo
from common import logger


# A level more detailed than DEBUG
TRACE = 5
# A level more detailed than INFO
VERBOSE = 15

class KnownValues(unittest.TestCase):
	SeriesData = {'SeriesName': 'Suits'}
	Suits_Data = {'SeriesName': 'Suits',
				  'tvdb_id': 247808,
				  'status': 'Continuing',
				  'top_show': 'Unknown',
				  'source': 'tvdb',
				  'imdb_id': 'tt1632701'}
	TVDB_ID = {'Suits': 247808,
				'Married at First Sight (US)': 283196,
				'The Office (US)': 73244,
				'The Tomorrow People (US)': 268591,
				'The Voice (US)': 247824,
				'Who Do You Think You Are? (US)': 146651,
				'Battlestar Galactica (2003)': 73545,
				'Castle (2009)': 83462,
				'Doctor Who (2005)': 78804,
				'Last Man Standing (2011)': 248834,
				'Legends (2014)': 265074,
				'Once Upon a Time (2011)': 248835,
				'Parenthood (2010)': 94551,
				'Partners (2012)': 259092,
	            'Pawn Stars': 111051,
				'Rush (2014)': 280939,
				'Scandal (2012)': 248841,
	            'So You Think You Can Dance': 78956,
				'The Americans (2013)': 261690,
				'The Bridge (2013)': 264085,
				'The Newsroom (2012)': 256227,
				'Zero Hour (2013)': 258773,
	}


class SeriesInfoSuffix(unittest.TestCase):

	def setUp(self):

		logger.initialize(unit_test=True, level=VERBOSE)

		self.library = SeriesInfo(rtnDict=True)
		self.library.args = self.library.options.parser.parse_args(["/usr/local/bin/episode.py",
																	"--tvdb",
																	"--so"]
																	)

#	@unittest.expectedFailure
	def test_suffix_us_and_year_100(self):
		self.assertEqual(self.library.getShowInfo({'SeriesName': "Suits"})['tvdb_id'],
						 KnownValues.Suits_Data['tvdb_id'])

#	@unittest.expectedFailure
	def test_suffix_us_and_year_110(self):
		KnownValues.SeriesData = {'SeriesName': "Married at First Sight (US)"}
		KnownValues.SeriesData_alt = {'SeriesName': "Married at First Sight"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 self.library.getShowInfo(KnownValues.SeriesData_alt)['tvdb_id'])

	def test_suffix_us_and_year_111(self):
		KnownValues.SeriesData = {'SeriesName': "Married at First Sight (US)"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["Married at First Sight (US)"])

	def test_suffix_us_and_year_112(self):
		KnownValues.SeriesData = {'SeriesName': "Married at First Sight"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["Married at First Sight (US)"])

	def test_suffix_us_and_year_120(self):
		KnownValues.SeriesData = {'SeriesName': "The Office (US)"}
		KnownValues.SeriesData_alt = {'SeriesName': "The Office"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 self.library.getShowInfo(KnownValues.SeriesData_alt)['tvdb_id'])

	def test_suffix_us_and_year_121(self):
		KnownValues.SeriesData = {'SeriesName': "The Office (US)"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["The Office (US)"])

	def test_suffix_us_and_year_122(self):
		KnownValues.SeriesData = {'SeriesName': "The Office"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["The Office (US)"])

	def test_suffix_us_and_year_130(self):
		KnownValues.SeriesData = {'SeriesName': "The Tomorrow People (US)"}
		KnownValues.SeriesData_alt = {'SeriesName': "The Tomorrow People"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 self.library.getShowInfo(KnownValues.SeriesData_alt)['tvdb_id'])

	def test_suffix_us_and_year_131(self):
		KnownValues.SeriesData = {'SeriesName': "The Tomorrow People (US)"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["The Tomorrow People (US)"])

	def test_suffix_us_and_year_132(self):
		KnownValues.SeriesData = {'SeriesName': "The Tomorrow People"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["The Tomorrow People (US)"])

	def test_suffix_us_and_year_140(self):
		KnownValues.SeriesData = {'SeriesName': "The Voice (US)"}
		KnownValues.SeriesData_alt = {'SeriesName': "The Voice"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 self.library.getShowInfo(KnownValues.SeriesData_alt)['tvdb_id'])

	def test_suffix_us_and_year_141(self):
		KnownValues.SeriesData = {'SeriesName': "The Voice (US)"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["The Voice (US)"])

	def test_suffix_us_and_year_142(self):
		KnownValues.SeriesData = {'SeriesName': "The Voice"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["The Voice (US)"])

	def test_suffix_us_and_year_150(self):
		KnownValues.SeriesData = {'SeriesName': "Who Do You Think You Are? (US)"}
		KnownValues.SeriesData_alt = {'SeriesName': "Who Do You Think You Are?"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 self.library.getShowInfo(KnownValues.SeriesData_alt)['tvdb_id'])

	def test_suffix_us_and_year_151(self):
		KnownValues.SeriesData = {'SeriesName': "Who Do You Think You Are? (US)"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID[ "Who Do You Think You Are? (US)"])

	def test_suffix_us_and_year_152(self):
		KnownValues.SeriesData = {'SeriesName': "Who Do You Think You Are?"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID[ "Who Do You Think You Are? (US)"])

	def test_suffix_us_and_year_153(self):
		KnownValues.SeriesData = {'SeriesName': "Who Do You Think You Are (US)"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID[ "Who Do You Think You Are? (US)"])

	def test_suffix_us_and_year_154(self):
		KnownValues.SeriesData = {'SeriesName': "Who Do You Think You Are"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID[ "Who Do You Think You Are? (US)"])

	def test_suffix_us_and_year_200(self):
		KnownValues.SeriesData = {'SeriesName': "Battlestar Galactica (2003)"}
		KnownValues.SeriesData_alt = {'SeriesName': "Battlestar Galactica"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 self.library.getShowInfo(KnownValues.SeriesData_alt)['tvdb_id'])

	def test_suffix_us_and_year_201(self):
		KnownValues.SeriesData = {'SeriesName': "Battlestar Galactica (2003)"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["Battlestar Galactica (2003)"])

	def test_suffix_us_and_year_202(self):
		KnownValues.SeriesData = {'SeriesName': "Battlestar Galactica"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["Battlestar Galactica (2003)"])

	def test_suffix_us_and_year_210(self):
		KnownValues.SeriesData = {'SeriesName': "Castle (2009)"}
		KnownValues.SeriesData_alt = {'SeriesName': "Castle"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 self.library.getShowInfo(KnownValues.SeriesData_alt)['tvdb_id'])

	def test_suffix_us_and_year_211(self):
		KnownValues.SeriesData = {'SeriesName': "Castle (2009)"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["Castle (2009)"])

	def test_suffix_us_and_year_212(self):
		KnownValues.SeriesData = {'SeriesName': "Castle"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["Castle (2009)"])

	def test_suffix_us_and_year_220(self):
		KnownValues.SeriesData = {'SeriesName': "Doctor Who (2005)"}
		KnownValues.SeriesData_alt = {'SeriesName': "Doctor Who"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 self.library.getShowInfo(KnownValues.SeriesData_alt)['tvdb_id'])

	def test_suffix_us_and_year_221(self):
		KnownValues.SeriesData = {'SeriesName': "Doctor Who (2005)"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["Doctor Who (2005)"])

	def test_suffix_us_and_year_222(self):
		KnownValues.SeriesData = {'SeriesName': "Doctor Who"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["Doctor Who (2005)"])

	def test_suffix_us_and_year_230(self):
		KnownValues.SeriesData = {'SeriesName': "Last Man Standing (2011)"}
		KnownValues.SeriesData_alt = {'SeriesName': "Last Man Standing"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 self.library.getShowInfo(KnownValues.SeriesData_alt)['tvdb_id'])

	def test_suffix_us_and_year_231(self):
		KnownValues.SeriesData = {'SeriesName': "Last Man Standing (2011)"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["Last Man Standing (2011)"])

	def test_suffix_us_and_year_232(self):
		KnownValues.SeriesData = {'SeriesName': "Last Man Standing"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["Last Man Standing (2011)"])

	def test_suffix_us_and_year_240(self):
		KnownValues.SeriesData = {'SeriesName': "Legends (2014)"}
		KnownValues.SeriesData_alt = {'SeriesName': "Legends"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 self.library.getShowInfo(KnownValues.SeriesData_alt)['tvdb_id'])

	def test_suffix_us_and_year_241(self):
		KnownValues.SeriesData = {'SeriesName': "Legends (2014)"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["Legends (2014)"])

	def test_suffix_us_and_year_242(self):
		KnownValues.SeriesData = {'SeriesName': "Legends (US)"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["Legends (2014)"])

	def test_suffix_us_and_year_243(self):
		KnownValues.SeriesData = {'SeriesName': "Legends"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["Legends (2014)"])

	def test_suffix_us_and_year_250(self):
		KnownValues.SeriesData = {'SeriesName': "Once Upon a Time (2011)"}
		KnownValues.SeriesData_alt = {'SeriesName': "Once Upon a Time"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 self.library.getShowInfo(KnownValues.SeriesData_alt)['tvdb_id'])

	def test_suffix_us_and_year_251(self):
		KnownValues.SeriesData = {'SeriesName': "Once Upon a Time (2011)"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["Once Upon a Time (2011)"])

	def test_suffix_us_and_year_252(self):
		KnownValues.SeriesData = {'SeriesName': "Once Upon a Time"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["Once Upon a Time (2011)"])

	def test_suffix_us_and_year_253(self):
		KnownValues.SeriesData = {'SeriesName': "Once Upon a Time"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["Once Upon a Time (2011)"])

	def test_suffix_us_and_year_260(self):
		KnownValues.SeriesData = {'SeriesName': "Parenthood (2010)"}
		KnownValues.SeriesData_alt = {'SeriesName': "Parenthood"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 self.library.getShowInfo(KnownValues.SeriesData_alt)['tvdb_id'])

	def test_suffix_us_and_year_261(self):
		KnownValues.SeriesData = {'SeriesName': "Parenthood (2010)"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["Parenthood (2010)"])

	def test_suffix_us_and_year_262(self):
		KnownValues.SeriesData = {'SeriesName': "Parenthood"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["Parenthood (2010)"])

	def test_suffix_us_and_year_270(self):
		KnownValues.SeriesData = {'SeriesName': "Partners (2012)"}
		KnownValues.SeriesData_alt = {'SeriesName': "Partners"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 self.library.getShowInfo(KnownValues.SeriesData_alt)['tvdb_id'])

	def test_suffix_us_and_year_271(self):
		KnownValues.SeriesData = {'SeriesName': "Partners (2012)"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["Partners (2012)"])

	def test_suffix_us_and_year_272(self):
		KnownValues.SeriesData = {'SeriesName': "Partners"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["Partners (2012)"])

	def test_suffix_us_and_year_280(self):
		KnownValues.SeriesData = {'SeriesName': "Rush (2014)"}
		KnownValues.SeriesData_alt = {'SeriesName': "Rush"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 self.library.getShowInfo(KnownValues.SeriesData_alt)['tvdb_id'])

	def test_suffix_us_and_year_281(self):
		KnownValues.SeriesData = {'SeriesName': "Rush (2014)"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["Rush (2014)"])

	def test_suffix_us_and_year_282(self):
		KnownValues.SeriesData = {'SeriesName': "Rush (US)"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["Rush (2014)"])

	def test_suffix_us_and_year_283(self):
		KnownValues.SeriesData = {'SeriesName': "Rush"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["Rush (2014)"])

	def test_suffix_us_and_year_290(self):
		KnownValues.SeriesData = {'SeriesName': "Scandal (2012)"}
		KnownValues.SeriesData_alt = {'SeriesName': "Scandal (US)"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 self.library.getShowInfo(KnownValues.SeriesData_alt)['tvdb_id'])

	def test_suffix_us_and_year_291(self):
		KnownValues.SeriesData = {'SeriesName': "Scandal (2012)"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["Scandal (2012)"])

	def test_suffix_us_and_year_292(self):
		KnownValues.SeriesData = {'SeriesName': "Scandal (US)"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["Scandal (2012)"])

	def test_suffix_us_and_year_293(self):
		KnownValues.SeriesData = {'SeriesName': "Scandal"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["Scandal (2012)"])

	def test_suffix_us_and_year_300(self):
		KnownValues.SeriesData = {'SeriesName': "The Americans (2013)"}
		KnownValues.SeriesData_alt = {'SeriesName': "The Americans (US)"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 self.library.getShowInfo(KnownValues.SeriesData_alt)['tvdb_id'])

	def test_suffix_us_and_year_301(self):
		KnownValues.SeriesData = {'SeriesName': "The Americans (2013)"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["The Americans (2013)"])

	def test_suffix_us_and_year_302(self):
		KnownValues.SeriesData = {'SeriesName': "The Americans (US)"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["The Americans (2013)"])

	def test_suffix_us_and_year_303(self):
		KnownValues.SeriesData = {'SeriesName': "The Americans"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["The Americans (2013)"])

	def test_suffix_us_and_year_310(self):
		KnownValues.SeriesData = {'SeriesName': "The Bridge (2013)"}
		KnownValues.SeriesData_alt = {'SeriesName': "The Bridge (US)"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 self.library.getShowInfo(KnownValues.SeriesData_alt)['tvdb_id'])

	def test_suffix_us_and_year_311(self):
		KnownValues.SeriesData = {'SeriesName': "The Bridge (2013)"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["The Bridge (2013)"])

	def test_suffix_us_and_year_312(self):
		KnownValues.SeriesData = {'SeriesName': "The Bridge (US)"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["The Bridge (2013)"])

	def test_suffix_us_and_year_313(self):
		KnownValues.SeriesData = {'SeriesName': "The Bridge"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["The Bridge (2013)"])

	def test_suffix_us_and_year_320(self):
		KnownValues.SeriesData = {'SeriesName': "The Newsroom (2012)"}
		KnownValues.SeriesData_alt = {'SeriesName': "The Newsroom (US)"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 self.library.getShowInfo(KnownValues.SeriesData_alt)['tvdb_id'])

	def test_suffix_us_and_year_321(self):
		KnownValues.SeriesData = {'SeriesName': "The Newsroom (2012)"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["The Newsroom (2012)"])

	def test_suffix_us_and_year_322(self):
		KnownValues.SeriesData = {'SeriesName': "The Newsroom (US)"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["The Newsroom (2012)"])

	def test_suffix_us_and_year_323(self):
		KnownValues.SeriesData = {'SeriesName': "The Newsroom"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["The Newsroom (2012)"])

	def test_suffix_us_and_year_330(self):
		KnownValues.SeriesData = {'SeriesName': "Zero Hour (2013)"}
		KnownValues.SeriesData_alt = {'SeriesName': "Zero Hour (US)"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 self.library.getShowInfo(KnownValues.SeriesData_alt)['tvdb_id'])

	def test_suffix_us_and_year_331(self):
		KnownValues.SeriesData = {'SeriesName': "Zero Hour (2013)"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["Zero Hour (2013)"])

	def test_suffix_us_and_year_332(self):
		KnownValues.SeriesData = {'SeriesName': "Zero Hour (US)"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["Zero Hour (2013)"])

	def test_suffix_us_and_year_333(self):
		KnownValues.SeriesData = {'SeriesName': "Zero Hour"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["Zero Hour (2013)"])

	def test_suffix_us_and_year_340(self):
		KnownValues.SeriesData = {'SeriesName': "So You Think You Can Dance"}
		KnownValues.SeriesData_alt = {'SeriesName': "So You Think You Can Dance (US)"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 self.library.getShowInfo(KnownValues.SeriesData_alt)['tvdb_id'])

	def test_suffix_us_and_year_341(self):
		KnownValues.SeriesData = {'SeriesName': "So You Think You Can Dance"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["So You Think You Can Dance"])

	def test_suffix_us_and_year_342(self):
		KnownValues.SeriesData = {'SeriesName': "So You Think You Can Dance (US)"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["So You Think You Can Dance"])

	def test_suffix_us_and_year_343(self):
		KnownValues.SeriesData = {'SeriesName': "SYTYCD"}
		self.assertEqual(self.library.getShowInfo(KnownValues.SeriesData)['tvdb_id'],
						 KnownValues.TVDB_ID["So You Think You Can Dance"])


	def theSuite(self):
		suite = unittest.TestLoader().loadTestsFromTestCase(self)
		return suite

if __name__ == '__main__':

	suite = SeriesInfoSuffix.theSuite()
	unittest.TextTestRunner(verbosity=1).run(suite)
