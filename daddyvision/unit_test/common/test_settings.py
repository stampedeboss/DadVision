from daddyvision.common import logger
from daddyvision.common.settings import Settings
from logging import INFO, WARNING, ERROR, DEBUG
from fnmatch import fnmatch
import unittest
import os
import sys

TRACE = 5
VERBOSE = 15

class KnownValues(unittest.TestCase):
    SeriesDir = '/mnt/TV/Series'
    MoviesDir = '/mnt/Movies/Films'
    NonVideoDir = '/mnt/Downloads/Unpacked'
    SubscriptionDir = '/mnt/Links'
    NewDir = 'New'
    WatchDir = '/mnt/Downloads/Bittorrent'

    DBFile = '/home/aj/.config/xbmcsupt/daddyvision.db3'
    TvdbIdFile = '/home/aj/.config/xbmcsupt/series_tvdb_ids'
    SeriesAliasFile = '/home/aj/.config/xbmcsupt/series_aliases'

    MediaExt = ['avi', 'mkv', 'mp4', 'mpeg']
    MovieGlob = ['720', '1080', 'bluray', 'bdrip', 'brrip', 'pal', 'ntsc', 'dvd-r', 'fulldvd', 'multi', 'dts', 'hdtv', 'pdtv', 'webrip', 'dvdrip', '2lions']
    IgnoreGlob = ['*subs*', '*subpack*', '*sample*', '*.sfv', '*.srt', '*.idx', '*.swp', '*.tmp', '*.bak', '*.nfo', '*.txt', 'thumbs.db', 'desktop.ini', 'ehthumbs_vista.db', '*.url', '*.doc', '*.docx', '*.jpg', '*.png', '*.com', '*.mds', '.*', '*~*',]
    Predicates = ['The', 'A', 'An']

    std_fqn = '%(BaseDir)s/%(SeriesName)s/Season %(SeasonNum)s/%(EpisodeNumFmt)s %(EpisodeTitle)s.%(Ext)s'
    proper_fqn = '%(BaseDir)s/%(SeriesName)s/Season %(SeasonNum)s/%(EpisodeNumFmt)s %(EpisodeTitle)s (PROPER).%(Ext)s'
    fullname = '%(SeriesName)s/Season %(SeasonNum)/[%(SeriesName)s S0%(SeasonNum)%(EpisodeNumFmt)s] %(EpisodeTitle)s%(Ext)s'
    std_show = '%(SeriesName)s/Season %(SeasonNumber)s/%(EpisodeNumFmt)s %(EpisodeTitle)s.%(Ext)s'
    hdtv_fqn = '%(SeriesName)s/Season %(SeasonNum) hdtv/[%(EpisodeNumFmt)s] %(EpisodeTitle)s%(Ext)s'
    std_epname = '%(EpisodeNumFmt)s %(EpisodeTitle)s.%(Ext)s'
    multiep_join_name_with = ', '
    episode_single = 'E%02d'
    episode_separator = '-'
    rename_message = '%-15.15s Season %2.2s NEW NAME: %-40.40s CUR NAME: %s'

    EpisodeAdjList =  [{'SeasonNum': 4, 'Begin': 0, 'AdjEpisode': 59, 'SeriesName': 'Pawn Stars', 'AdjSeason': -2, 'End': 9999}]

    File_Details = {'BaseDir' : '/mnt/TV/Series',
                    'SeriesName' : "Sample",
                    'SeasonNum' : 1,
                    'EpisodeNums' : [1,2],
                    'EpisodeNumFmt' : 'E01-E02',
                    'EpisodeTitle' : 'Dummy Title',
                    'Ext' : 'avi',
                    'FileName' : '/mnt/Downloads/Bittorrent/Sample S01E01-02 Not now sucker.avi'
                    }

    Series_Season = '/Sample/Season 1/'
    New_Name = 'E01-E02 Dummy Title.avi'
    New_NameP = 'E01-E02 Dummy Title (PROPER).avi'

    Rename_Messsage = 'Sample          Season  1 NEW NAME: E01-E02 Dummy Title.avi                  CUR NAME: Sample S01E01-02 Not now sucker.avi'

class Test000(unittest.TestCase):

    def setUp(self):
        logger.initialize(unit_test=True, level=ERROR)

        self.settings = Settings()

    def test_settings_case_010(self):
        self.assertEqual(self.settings.SeriesDir, KnownValues.SeriesDir)
    def test_settings_case_011(self):
        self.assertEqual(self.settings.MoviesDir, KnownValues.MoviesDir)
    def test_settings_case_012(self):
        self.assertEqual(self.settings.NonVideoDir, KnownValues.NonVideoDir)
    def test_settings_case_013(self):
        self.assertEqual(self.settings.SubscriptionDir, KnownValues.SubscriptionDir)
    def test_settings_case_014(self):
        self.assertEqual(self.settings.NewDir, KnownValues.NewDir)
    def test_settings_case_015(self):
        self.assertEqual(self.settings.WatchDir, KnownValues.WatchDir)
    def test_settings_case_016(self):
        self.assertEqual(self.settings.WatchDir, KnownValues.WatchDir)

    def test_settings_case_020(self):
        self.assertEqual(self.settings.SeriesAliasFile, KnownValues.SeriesAliasFile)

    def test_settings_case_030(self):
        self.assertEqual(self.settings.MediaExt, KnownValues.MediaExt)
    def test_settings_case_031(self):
        self.assertEqual(self.settings.MovieGlob, KnownValues.MovieGlob)
    def test_settings_case_032(self):
        self.assertEqual(self.settings.IgnoreGlob, KnownValues.IgnoreGlob)
    def test_settings_case_033(self):
        self.assertEqual(self.settings.Predicates, KnownValues.Predicates)

    def test_settings_case_040(self):
        self.assertEqual(self.settings.ConversionsPatterns['std_fqn'], KnownValues.std_fqn)
    def test_settings_case_041(self):
        self.assertEqual(self.settings.ConversionsPatterns['proper_fqn'], KnownValues.proper_fqn)
    def test_settings_case_042(self):
        self.assertEqual(self.settings.ConversionsPatterns['rename_message'], KnownValues.rename_message)
    def test_settings_case_043(self):
        self.assertEqual(self.settings.ConversionsPatterns['fullname'], KnownValues.fullname)
    def test_settings_case_044(self):
        self.assertEqual(self.settings.ConversionsPatterns['std_show'], KnownValues.std_show)
    def test_settings_case_045(self):
        self.assertEqual(self.settings.ConversionsPatterns['hdtv_fqn'], KnownValues.hdtv_fqn)
    def test_settings_case_046(self):
        self.assertEqual(self.settings.ConversionsPatterns['std_epname'], KnownValues.std_epname)
    def test_settings_case_047(self):
        self.assertEqual(self.settings.ConversionsPatterns['multiep_join_name_with'], KnownValues.multiep_join_name_with)
    def test_settings_case_048(self):
        self.assertEqual(self.settings.ConversionsPatterns['episode_single'], KnownValues.episode_single)
    def test_settings_case_049(self):
        self.assertEqual(self.settings.ConversionsPatterns['episode_separator'], KnownValues.episode_separator)

    def test_settings_case_050(self):
        self.assertEqual(self.settings.ConversionsPatterns['std_fqn'] % KnownValues.File_Details, KnownValues.SeriesDir +
                                                                                                  KnownValues.Series_Season +
                                                                                                  KnownValues.New_Name)
    def test_settings_case_051(self):
        self.assertEqual(self.settings.ConversionsPatterns['proper_fqn'] % KnownValues.File_Details, KnownValues.SeriesDir +
                                                                                                  KnownValues.Series_Season +
                                                                                                  KnownValues.New_NameP)
    def test_settings_case_052(self):
        self.assertEqual(self.settings.ConversionsPatterns['rename_message'] % (KnownValues.File_Details['SeriesName'],
                                                                                KnownValues.File_Details['SeasonNum'],
                                                                                KnownValues.New_Name,
                                                                                os.path.basename(KnownValues.File_Details['FileName'])
                                                                               ),
                                                                                KnownValues.Rename_Messsage)

    def test_settings_case_060(self):
        self.assertEqual(self.settings.ReloadTVDBList(), 0)
    def test_settings_case_061(self):
        self.assertEqual(self.settings.TvdbIdFile, KnownValues.TvdbIdFile)
    def test_settings_case_062(self):
        self.assertEqual(self.settings.TvdbIdList['90210'], '82716')
    def test_settings_case_063(self):
        self.assertEqual(self.settings.TvdbIdList['Firefly'], '78874')
    def test_settings_case_064(self):
        self.assertEqual(self.settings.TvdbIdList['V (2009)'], '94971')

    def test_settings_case_100a(self):
        self.assertTrue('Leverage' in self.settings.SpecialHandlingList)
    def test_settings_case_100b(self):
        self.assertFalse('Missing Entry' in self.settings.SpecialHandlingList)

    def test_settings_case_101a(self):
        self.assertTrue('The New Yankee Workshop' in self.settings.ExcludeList)
    def test_settings_case_101b(self):
        self.assertFalse('Missing Entry' in self.settings.ExcludeList)
    def test_settings_case_101c(self):
        self.assertTrue('Special Features' in self.settings.ExcludeList)
    def test_settings_case_102c(self):
        self.assertTrue('mkv' in self.settings.MediaExt)
    def test_settings_case_103c(self):
        self.assertTrue('bluray' in self.settings.MovieGlob)
    def test_settings_case_104c(self):
        self.assertTrue('*subs*' in self.settings.IgnoreGlob)
    def test_settings_case_105c(self):
        self.assertTrue('The' in self.settings.Predicates)

    @unittest.expectedFailure
    def test_settings_case_110a(self):
         self.assertTrue(any(fnmatch('anyfile bluray.mkv'.lower(), pattern) for pattern in self.settings.MovieGlob))
#        self.assertTrue(any(fnmatch.fnmatch('anyfile.mkv', pattern) for pattern in self.settings.MediaExt))


 #   def test_settings_case_900(self):
 #       self.assertRaises(exceptions.InvalidFilename, self.parser.getFileDetails, KnownValues.File_SxxExx['FileName'])

    def theSuite(self):
        suite = unittest.TestLoader().loadTestsFromTestCase(self)
        return suite

if __name__ == '__main__':
#    suite = unittest.TestLoader().loadTestsFromTestCase(FileParserExceptions)
    suite = Test000.theSuite()
    unittest.TextTestRunner(verbosity=2).run(suite)

