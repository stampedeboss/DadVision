from daddyvision.series.episodeinfo import EpisodeDetails
from daddyvision.common.exceptions import InvalidArgumentType, DictKeyError, DataRetrievalError
from daddyvision.common.exceptions import SeriesNotFound, EpisodeNotFound, EpisodeNameNotFound
from logging import INFO, WARNING, ERROR, DEBUG
import unittest
import logging
import logging.handlers
import os
import sys

class KnownValues(unittest.TestCase):
    SeriesData = {'SeriesName' : 'Suits'}
    Suits_Data = {'TVDBSeriesID': '247808'}
    
class EpisodeDetailsExceptions(unittest.TestCase):

    def setUp(self):
        __version__ = '$Rev$'
        __pgmname__ = 'unittest'

        logging.addLevelName(5, 'TRACE')
        logging.addLevelName(15, 'VERBOSE')
        log = logging.getLogger()
        setattr(log, 'TRACE', lambda *args: log.log(5, *args))
        setattr(log, 'VERBOSE', lambda *args: log.log(15, *args))

        HomeDir = os.path.expanduser('~')
        ConfigDirB = os.path.join(HomeDir, '.config')
        LogDir = os.path.join('/srv', 'log')

        log.setLevel('TRACE')
        _formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)-8s - %(message)s")

        _error_log = logging.handlers.RotatingFileHandler(os.path.join(LogDir, '%s_error.log' % __pgmname__), maxBytes=0, backupCount=7)
        _error_log.setLevel('TRACE')
        _error_log.setFormatter(_formatter)
        log.addHandler(_error_log)

        _console = logging.StreamHandler()
        _console.setLevel(INFO)
        _console.setFormatter(_formatter)
        log.addHandler(_console)

        self.mymodule = EpisodeDetails()
        
 
#    @unittest.expectedFailure
    def test_EpisodeDetails_exception_case_000(self):
        self.assertEqual(self.mymodule.getDetails({'SeriesName' : "Suits"})['TVDBSeriesID'], KnownValues.Suits_Data['TVDBSeriesID'])

    def test_EpisodeDetails_exception_case_001(self):
        self.assertRaises(InvalidArgumentType, self.mymodule.getDetails, 'string')

    def test_EpisodeDetails_exception_case_002(self):
        KnownValues.SeriesData = {'NotSeriesName' : "Suits"}
        self.assertRaises(DictKeyError, self.mymodule.getDetails, KnownValues.SeriesData)

    def test_EpisodeDetails_exception_case_003(self):
        KnownValues.SeriesData = {'SeriesName' : "Not a Real SeriesName"}
        self.assertRaises(SeriesNotFound, self.mymodule.getDetails, KnownValues.SeriesData)

suite = unittest.TestLoader().loadTestsFromTestCase(EpisodeDetailsExceptions)
unittest.TextTestRunner(verbosity=2).run(suite)

#if __name__ == '__main__':
#    unittest.main()
