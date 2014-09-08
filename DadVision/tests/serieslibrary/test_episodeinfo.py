import unittest

from library.series.seriesinfo import SeriesInfo
from common.exceptions import InvalidArgumentType, DictKeyError
from common.exceptions import SeriesNotFound
from common import logger


# A level more detailed than DEBUG
TRACE = 5
# A level more detailed than INFO
VERBOSE = 15

class KnownValues(unittest.TestCase):
    SeriesData = {'SeriesName' : 'Suits'}
    Suits_Data = {'TVDBSeriesID': '247808'}

class EpisodeDetailsExceptions(unittest.TestCase):

    def setUp(self):
        logger.initialize(unit_test=True, level=TRACE)
#         logger.start(level=ERROR)

        self.library = SeriesInfo()
#        args = self.library.options.parser.parse_args(["/usr/local/bin/episode.py", "--tvdb", "--error"])

#    @unittest.expectedFailure
    def test_EpisodeDetails_exception_case_000(self):
        self.assertEqual(self.library.getShowInfo({'SeriesName' : "Suits"}), KnownValues.Suits_Data['tvdb_id'])

    def test_EpisodeDetails_exception_case_001(self):
        self.assertRaises(InvalidArgumentType, self.library.getShowInfo(), 'string')

    def test_EpisodeDetails_exception_case_002(self):
        KnownValues.SeriesData = {'NotSeriesName' : "Suits"}
        self.assertRaises(DictKeyError, self.library.getShowInfo(), KnownValues.SeriesData)

    def test_EpisodeDetails_exception_case_003(self):
        KnownValues.SeriesData = {'SeriesName' : "Not a Real SeriesName"}
        self.assertRaises(SeriesNotFound, self.library.getShowInfo(), KnownValues.SeriesData)

    def theSuite(self):
        suite = unittest.TestLoader().loadTestsFromTestCase(self)
        return suite

if __name__ == '__main__':

    library = SeriesInfo()
    args = library.options.parser.parse_args(["/usr/local/bin/episode.py", "--tvdb", "--error"])

    suite = EpisodeDetailsExceptions.theSuite()
    unittest.TextTestRunner(verbosity=2).run(suite)
