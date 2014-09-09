import unittest

from library.series.seriesinfo import SeriesInfo
from common import logger


# A level more detailed than DEBUG
TRACE = 5
# A level more detailed than INFO
VERBOSE = 15

class KnownValues(unittest.TestCase):
	SeriesData = {'SeriesName' : 'Suits'}
	Suits_Data = {'SeriesName': '247808'}

	'''
	Married at First Sight (US)
	The Office (US)
	The Tomorrow People (US)
	The Voice (US)
	Who Do You Think You Are? (US)

	Battlestar Galactica (2003)
	Castle (2009)
	Doctor Who (2005)
	Last Man Standing (2011)
	Legends (2014)
	Once Upon a Time (2011)
	Parenthood (2010)
	Partners (2012)
	Rush (2014)
	Scandal (2012)
	The Americans (2013)
	The Bridge (2013)
	The Newsroom (2012)
	Zero Hour (2013)
	'''

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
		self.assertEqual(self.library.getShowInfo({'SeriesName' : "Suits"}),
		                 KnownValues.Suits_Data['tvdb_id'])

#	@unittest.expectedFailure
	def test_suffix_us_and_year_110(self):
		KnownValues.SeriesData = {'SeriesName': "Married at First Sight (US)"}
		KnownValues.SeriesData_alt = {'SeriesName': "Married at First Sight"}
		self.assertDictEqual(self.library.getShowInfo(KnownValues.SeriesData),
		                 self.library.getShowInfo(KnownValues.SeriesData_alt))

	def test_suffix_us_and_year_120(self):
		KnownValues.SeriesData = {'SeriesName': "The Office (US)"}
		KnownValues.SeriesData_alt = {'SeriesName': "The Office"}
		self.assertDictEqual(self.library.getShowInfo(KnownValues.SeriesData),
		                 self.library.getShowInfo(KnownValues.SeriesData_alt))

	def test_suffix_us_and_year_130(self):
		KnownValues.SeriesData = {'SeriesName': "The Tomorrow People (US)"}
		KnownValues.SeriesData_alt = {'SeriesName': "The Tomorrow People"}
		self.assertDictEqual(self.library.getShowInfo(KnownValues.SeriesData),
		                 self.library.getShowInfo(KnownValues.SeriesData_alt))

	def test_suffix_us_and_year_140(self):
		KnownValues.SeriesData = {'SeriesName': "The Voice (US)"}
		KnownValues.SeriesData_alt = {'SeriesName': "The Voice"}
		self.assertDictEqual(self.library.getShowInfo(KnownValues.SeriesData),
		                 self.library.getShowInfo(KnownValues.SeriesData_alt))

	def test_suffix_us_and_year_150(self):
		KnownValues.SeriesData = {'SeriesName': "Who Do You Think You Are? (US)"}
		KnownValues.SeriesData_alt = {'SeriesName': "Who Do You Think You Are?"}
		self.assertDictEqual(self.library.getShowInfo(KnownValues.SeriesData),
		                 self.library.getShowInfo(KnownValues.SeriesData_alt))


	def test_suffix_us_and_year_200(self):
		KnownValues.SeriesData = {'SeriesName': "Battlestar Galactica (2003)"}
		KnownValues.SeriesData_alt = {'SeriesName': "Battlestar Galactica"}
		self.assertDictEqual(self.library.getShowInfo(KnownValues.SeriesData),
		                 self.library.getShowInfo(KnownValues.SeriesData_alt))

	def test_suffix_us_and_year_210(self):
		KnownValues.SeriesData = {'SeriesName': "Castle (2009)"}
		KnownValues.SeriesData_alt = {'SeriesName': "Castle"}
		self.assertDictEqual(self.library.getShowInfo(KnownValues.SeriesData),
		                 self.library.getShowInfo(KnownValues.SeriesData_alt))

	def test_suffix_us_and_year_220(self):
		KnownValues.SeriesData = {'SeriesName': "Doctor Who (2005)"}
		KnownValues.SeriesData_alt = {'SeriesName': "Doctor Who"}
		self.assertDictEqual(self.library.getShowInfo(KnownValues.SeriesData),
		                 self.library.getShowInfo(KnownValues.SeriesData_alt))

	def test_suffix_us_and_year_230(self):
		KnownValues.SeriesData = {'SeriesName': "Last Man Standing (2011)"}
		KnownValues.SeriesData_alt = {'SeriesName': "Last Man Standing"}
		self.assertDictEqual(self.library.getShowInfo(KnownValues.SeriesData),
		                 self.library.getShowInfo(KnownValues.SeriesData_alt))

	def test_suffix_us_and_year_240(self):
		KnownValues.SeriesData = {'SeriesName': "Legends (2014)"}
		KnownValues.SeriesData_alt = {'SeriesName': "Legends"}
		self.assertDictEqual(self.library.getShowInfo(KnownValues.SeriesData),
		                 self.library.getShowInfo(KnownValues.SeriesData_alt))

	def test_suffix_us_and_year_250(self):
		KnownValues.SeriesData = {'SeriesName': "Once Upon a Time (2011)"}
		KnownValues.SeriesData_alt = {'SeriesName': "Once Upon a Time"}
		self.assertDictEqual(self.library.getShowInfo(KnownValues.SeriesData),
		                 self.library.getShowInfo(KnownValues.SeriesData_alt))

	def test_suffix_us_and_year_260(self):
		KnownValues.SeriesData = {'SeriesName': "Parenthood (2010)"}
		KnownValues.SeriesData_alt = {'SeriesName': "Parenthood"}
		self.assertDictEqual(self.library.getShowInfo(KnownValues.SeriesData),
		                 self.library.getShowInfo(KnownValues.SeriesData_alt))

	def test_suffix_us_and_year_270(self):
		KnownValues.SeriesData = {'SeriesName': "Partners (2012)"}
		KnownValues.SeriesData_alt = {'SeriesName': "Partners"}
		self.assertDictEqual(self.library.getShowInfo(KnownValues.SeriesData),
		                 self.library.getShowInfo(KnownValues.SeriesData_alt))

	def test_suffix_us_and_year_280(self):
		KnownValues.SeriesData = {'SeriesName': "Rush (2014)"}
		KnownValues.SeriesData_alt = {'SeriesName': "Rush"}
		self.assertDictEqual(self.library.getShowInfo(KnownValues.SeriesData),
		                 self.library.getShowInfo(KnownValues.SeriesData_alt))

	def test_suffix_us_and_year_281(self):
		KnownValues.SeriesData = {'SeriesName': "Rush (US)"}
		KnownValues.SeriesData_alt = {'SeriesName': "Rush (2014)"}
		self.assertDictEqual(self.library.getShowInfo(KnownValues.SeriesData),
		                 self.library.getShowInfo(KnownValues.SeriesData_alt))

	def test_suffix_us_and_year_290(self):
		KnownValues.SeriesData = {'SeriesName': "Scandal (2012)"}
		KnownValues.SeriesData_alt = {'SeriesName': "Scandal (US)"}
		self.assertDictEqual(self.library.getShowInfo(KnownValues.SeriesData),
		                 self.library.getShowInfo(KnownValues.SeriesData_alt))

	def test_suffix_us_and_year_291(self):
		KnownValues.SeriesData = {'SeriesName': "Scandal (2012)"}
		KnownValues.SeriesData_alt = {'SeriesName': "Scandal"}
		self.assertDictEqual(self.library.getShowInfo(KnownValues.SeriesData),
		                 self.library.getShowInfo(KnownValues.SeriesData_alt))

	def test_suffix_us_and_year_300(self):
		KnownValues.SeriesData = {'SeriesName': "The Americans (2013)"}
		KnownValues.SeriesData_alt = {'SeriesName': "The Americans (US)"}
		self.assertDictEqual(self.library.getShowInfo(KnownValues.SeriesData),
		                 self.library.getShowInfo(KnownValues.SeriesData_alt))

	def test_suffix_us_and_year_301(self):
		KnownValues.SeriesData = {'SeriesName': "The Americans (2013)"}
		KnownValues.SeriesData_alt = {'SeriesName': "The Americans"}
		self.assertDictEqual(self.library.getShowInfo(KnownValues.SeriesData),
		                 self.library.getShowInfo(KnownValues.SeriesData_alt))

	def test_suffix_us_and_year_310(self):
		KnownValues.SeriesData = {'SeriesName': "The Bridge (2013)"}
		KnownValues.SeriesData_alt = {'SeriesName': "The Bridge (US)"}
		self.assertDictEqual(self.library.getShowInfo(KnownValues.SeriesData),
		                 self.library.getShowInfo(KnownValues.SeriesData_alt))

	def test_suffix_us_and_year_311(self):
		KnownValues.SeriesData = {'SeriesName': "The Bridge (2013)"}
		KnownValues.SeriesData_alt = {'SeriesName': "The Bridge"}
		self.assertDictEqual(self.library.getShowInfo(KnownValues.SeriesData),
		                 self.library.getShowInfo(KnownValues.SeriesData_alt))

	def test_suffix_us_and_year_320(self):
		KnownValues.SeriesData = {'SeriesName': "The Newsroom (2012)"}
		KnownValues.SeriesData_alt = {'SeriesName': "The Newsroom (US)"}
		self.assertDictEqual(self.library.getShowInfo(KnownValues.SeriesData),
		                 self.library.getShowInfo(KnownValues.SeriesData_alt))

	def test_suffix_us_and_year_321(self):
		KnownValues.SeriesData = {'SeriesName': "The Newsroom (2012)"}
		KnownValues.SeriesData_alt = {'SeriesName': "The Newsroom"}
		self.assertDictEqual(self.library.getShowInfo(KnownValues.SeriesData),
		                 self.library.getShowInfo(KnownValues.SeriesData_alt))

	def test_suffix_us_and_year_330(self):
		KnownValues.SeriesData = {'SeriesName': "Zero Hour (2013)"}
		KnownValues.SeriesData_alt = {'SeriesName': "Zero Hour (US)"}
		self.assertDictEqual(self.library.getShowInfo(KnownValues.SeriesData),
		                 self.library.getShowInfo(KnownValues.SeriesData_alt))

	def test_suffix_us_and_year_331(self):
		KnownValues.SeriesData = {'SeriesName': "Zero Hour (2013)"}
		KnownValues.SeriesData_alt = {'SeriesName': "Zero Hour"}
		self.assertDictEqual(self.library.getShowInfo(KnownValues.SeriesData),
		                 self.library.getShowInfo(KnownValues.SeriesData_alt))

	def test_suffix_us_and_year_340(self):
		KnownValues.SeriesData = {'SeriesName': "So You Think You Can Dance"}
		KnownValues.SeriesData_alt = {'SeriesName': "So You Think You Can Dance (US)"}
		self.assertDictEqual(self.library.getShowInfo(KnownValues.SeriesData),
		                 self.library.getShowInfo(KnownValues.SeriesData_alt))

	def test_suffix_us_and_year_341(self):
		KnownValues.SeriesData = {'SeriesName': "SYTYCD"}
		KnownValues.SeriesData_alt = {'SeriesName': "So You Think You Can Dance"}
		self.assertDictEqual(self.library.getShowInfo(KnownValues.SeriesData),
		                 self.library.getShowInfo(KnownValues.SeriesData_alt))


	def theSuite(self):
		suite = unittest.TestLoader().loadTestsFromTestCase(self)
		return suite

if __name__ == '__main__':

	suite = SeriesInfoSuffix.theSuite()
	unittest.TextTestRunner(verbosity=1).run(suite)
