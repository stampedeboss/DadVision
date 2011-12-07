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
    File_SxxExx['EpisodeNums'] = [1, 2]
    File_SxxExx['Ext'] = 'ext'
#   File_SxxExx['BaseDir'] = '/mnt/TV/Series'

class FileParserMultiEps(unittest.TestCase):

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

# Multi-Episode S##E##E##
    def test_FileParser_multi_case_000(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Series/TV/Covert Affairs/Season 1/E01-E02 Case 000.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_001(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs S1E01e02 Case 001.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_002(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs S01E01e02 Case 002.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_003(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs S1E001e002 Case 003.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_004(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs S01E001e002 Case 004.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# Multi-Episode S##E##-E##
    def test_FileParser_multi_case_005(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs S1E01-e02 Case 005.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_006(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs S01E01-e02 Case 006.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_007(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs S1E001-e002 Case 007.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_008(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs S01E001-e002 Case 008.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# Multi-Episode S##E##-##
    def test_FileParser_multi_case_009(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs S1E01-02 Case 009.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_010(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs S01E01-02 Case 010.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_011(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs S1E001-002 Case 011.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_012(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs S01E001-002 Case 012.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# Multi-Episode S##E## S##E##
    def test_FileParser_multi_case_013(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs S1E01 s1e02 Case 013.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_014(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs S01E01 s01e02 Case 014.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_015(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs S1E001 s1e002 Case 015.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_016(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs S01E001 s01e002 Case 016.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# Multi-Episode ##x##x##
    def test_FileParser_multi_case_017(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 1x01x02 Case 017.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_018(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 01x01x02 Case 018.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_019(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 1x001x002 Case 019.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_020(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 01x001x002 Case 020.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# Multi-Episode ##x##-x##
    def test_FileParser_multi_case_021(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 1x01-x02 Case 021.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_022(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 01x01-x02 Case 022.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_023(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 1x001-x002 Case 023.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_024(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 01x001-x002 Case 024.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# Multi-Episode ##x##-##
    def test_FileParser_multi_case_025(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 1x01-02 Case 025.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_026(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 01x01-02 Case 026.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_027(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 1x001-002 Case 027.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_028(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 01x001-002 Case 028.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# Multi-Episode ##x## ##x##
    def test_FileParser_multi_case_029(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 1x01 1x02 Case 029.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_030(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 01x01 01x02 Case 030.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_031(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 1x001 1x002 Case 031.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_032(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 01x001 01x002 Case 032.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# Multi-Episode ####-##
    def test_FileParser_multi_case_033(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 101-02 Case 033.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_034(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 0101-02 Case 034.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_035(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 1001-002 Case 035.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_036(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 01001-002 Case 036.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# Multi-Episode #### ####
    def test_FileParser_multi_case_037(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 101 102 Case 037.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_038(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 0101 0102 Case 038.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_039(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 1001 1002 Case 039.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_040(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs 01001 01002 Case 040.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# Multi-Episode [####-##]
    def test_FileParser_multi_case_041(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs [101-02] Case 041.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_042(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs [0101-02] Case 042.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_043(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs [1001-002] Case 043.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_044(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs [01001-002] Case 044.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

# Multi-Episode [#### ####]
    def test_FileParser_multi_case_045(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs [101] [102] Case 045.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_046(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs [0101] [0102] Case 046.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_047(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs [1001] [1002] Case 047.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

    def test_FileParser_multi_case_048(self):
        KnownValues.File_SxxExx["FileName"] = "/mnt/Download/Bittorrent/Covert Affairs [01001] [01002] Case 048.ext"
        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)

suite = unittest.TestLoader().loadTestsFromTestCase(FileParserMultiEps)
unittest.TextTestRunner(verbosity=2).run(suite)
