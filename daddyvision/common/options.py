import os
import sys
from optparse import OptionParser as OptParser, OptionGroup
import daddyvision

__pgmname__ = 'common.options'
__version__ = '$Rev$'

__author__ = "@author: AJ Reynolds"
__copyright__ = "Copyright 2011, AJ Reynolds"
__credits__ = []
__license__ = "GPL"

__maintainer__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"
__status__ = "Development"

class OptionParser(OptParser):

    def __init__(self, **kwargs):
        OptParser.__init__(self, **kwargs)

        self.version = __version__

        self.add_option('-V', '--version', action='version',
                        help='Print DaddyVision version and exit.')

        self.add_option('--logfile', action='store', dest='logfile', default='daddyvision.log',
                        help='Specify a custom logfile name/location. Default is daddyvision.log in the /srv/log directory.')

        group = OptionGroup(self, "Logging Levels:")
        group.add_option("--loglevel", dest="loglevel",
            action="store", type="choice", default="INFO",
            choices=['CRITICAL' ,'ERROR', 'WARNING', 'INFO', 'VERBOSE', 'DEBUG', 'TRACE'],
            help="Specify by name the Level of logging desired, [CRITICAL|ERROR|WARNING|INFO|VERBOSE|DEBUG|TRACE]")
        group.add_option("-e", "--errors", dest="loglevel",
            action="store_const", const="ERROR",
            help="Limit logging to only include Errors and Critical information")
        group.add_option("-q", "--quiet", dest="loglevel",
            action="store_const", const="WARNING",
            help="Limit logging to only include Warning, Errors, and Critical information")
        group.add_option("-v", "--verbose", dest="loglevel",
            action="store_const", const="VERBOSE",
            help="increase logging to include informational information")
        group.add_option("--debug", dest="loglevel",
            action="store_const", const="DEBUG",
            help="increase logging to include debug information")
        group.add_option("--trace", dest="loglevel",
            action="store_const", const="TRACE",
            help="increase logging to include program trace information")
        self.add_option_group(group)

class CoreOptionParser(OptionParser):
    """Contains all the options that should only be used when running without a ui"""

    def __init__(self, unit_test=False, **kwargs):
        OptionParser.__init__(self, **kwargs)

        self._unit_test = unit_test

'''
    def parse_args(self, args=None):
        result = OptParser.parse_args(self, args or self._unit_test and ['flexget', '--reset'] or None)
        options = result[0]

        if options.test and (options.learn or options.reset):
            self.error('--test and %s are mutually exclusive' % ('--learn' if options.learn else '--reset'))

        # reset and migrate should be executed with learn
        if (options.reset and not self._unit_test) or options.migrate:
            options.learn = True

        # Lower the log level when executed with --cron
        if options.quiet:
            options.loglevel = 'info'

        return options, args
'''