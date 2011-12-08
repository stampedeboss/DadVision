from daddyvision.common.fileparser import FileParser
from daddyvision.common import exceptions
from logging import INFO, WARNING, ERROR, DEBUG
import unittest
import logging
import logging.handlers
import os
import sys

class KnownValues(unittest.TestCase):
    File_SxxExx = {}
    File_SxxExx['FileName'] = ""
    File_SxxExx['SeriesName'] = 'Covert Affairs'
    File_SxxExx['SeasonNum'] = 1
    File_SxxExx['EpisodeNums'] = [1]
    File_SxxExx['Ext'] = 'ext'
#   File_SxxExx['BaseDir'] = '/mnt/TV/Series'

class FileParseExceptions(unittest.TestCase):

    def setUp(self):
        __version__ = '$Rev$'
        __pgmname__ = 'fileparser'

        logging.addLevelName(5, 'TRACE')
        logging.addLevelName(15, 'VERBOSE')
        log = logging.getLogger()
        setattr(log, 'TRACE', lambda *args: log.log(5, *args))
        setattr(log, 'VERBOSE', lambda *args: log.log(15, *args))

        HomeDir = os.path.expanduser('~')
        ConfigDirB = os.path.join(HomeDir, '.config')
        LogDir = os.path.join(HomeDir, 'log')

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

        self.parser = FileParser()


    def test_FileParser_exception_case_001(self):
        # should raise an exception for missing or invalid patient_id
        KnownValues.File_SxxExx['FileName'] = '/mnt/Download/Bittorrent/the.big.bang.theory.season.1.avi'
        self.assertRaises(exceptions.InvalidFilename, self.parser.GetFileDetails, KnownValues.File_SxxExx['FileName'])

suite = unittest.TestLoader().loadTestsFromTestCase(FileParseExceptions)
unittest.TextTestRunner(verbosity=2).run(suite)

#if __name__ == '__main__':
#    unittest.main()
