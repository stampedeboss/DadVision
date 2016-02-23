import unittest

from common.exceptions import InvalidArgumentType, DictKeyError
from common.exceptions import SeriesNotFound

import logger
from series import SeriesInfo


# A level more detailed than DEBUG
TRACE = 5
# A level more detailed than INFO
VERBOSE = 15

class KnownValues(unittest.TestCase):
	SeriesData = {'SeriesName' : 'Suits'}
	Suits_Data = {'SeriesName': '247808'}


class SeriesInfoExceptions(unittest.TestCase):

	def setUp(self):

		logger.initialize(unit_test=True, level=VERBOSE)
		self.library = SeriesInfo(rtnDict=True)
		self.library.args = self.library.options.parser.parse_args(["/usr/local/bin/episode.py"])

#	@unittest.expectedFailure
	def test_SeriesInfo_exception_case_901(self):
		self.assertRaises(InvalidArgumentType, self.library.getShowInfo('string'), 'string')

#	@unittest.expectedFailure
	def test_SeriesInfo_exception_case_902(self):
		KnownValues.SeriesData = {'NotSeriesName' : "Suits"}
		self.assertRaises(DictKeyError, self.library.getShowInfo(KnownValues.SeriesData), KnownValues.SeriesData)

#	@unittest.expectedFailure
	def test_SeriesInfo_exception_case_903(self):
		KnownValues.SeriesData = {'SeriesName' : "Not a Real SeriesName"}
		self.assertRaises(SeriesNotFound, self.library.getShowInfo(self, KnownValues.SeriesData))

	def theSuite(self):
		suite = unittest.TestLoader().loadTestsFromTestCase(self)
		return suite

if __name__ == '__main__':

	suite = SeriesInfoExceptions.theSuite()
	unittest.TextTestRunner(verbosity=1).run(suite)
