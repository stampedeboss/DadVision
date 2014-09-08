import unittest

from library.series.fileparser import FileParser
from common import exceptions
from common import logger


class KnownValues(unittest.TestCase):
    File_SxxExx = {}
    File_SxxExx['FileName'] = ""
    File_SxxExx['SeriesName'] = 'Covert Affairs'
    File_SxxExx['SeasonNum'] = 1
    File_SxxExx['EpisodeNums'] = [1]
    File_SxxExx['Ext'] = 'ext'
#   File_SxxExx['BaseDir'] = '/mnt/DadVision/Series'

class FileParserExceptions(unittest.TestCase):

    def setUp(self):

        TRACE = 5
        VERBOSE = 15

        logger.initialize(unit_test=True, level=VERBOSE)
#        logger.start(level=ERROR)

        self.library = FileParser()

    def test_FileParser_exception_case_001(self):
        # should raise an exception for missing or invalid patient_id
        KnownValues.File_SxxExx['FileName'] = '/mnt/Download/Bittorrent/the.big.bang.theory.season.1.avi'
        self.assertRaises(exceptions.InvalidFilename, self.library.getFileDetails, KnownValues.File_SxxExx['FileName'])

    def theSuite(self):
        suite = unittest.TestLoader().loadTestsFromTestCase(self)
        return suite

if __name__ == '__main__':
#    suite = unittest.TestLoader().loadTestsFromTestCase(FileParserExceptions)
    suite = FileParserExceptions.theSuite()
    unittest.TextTestRunner(verbosity=2).run(suite)

