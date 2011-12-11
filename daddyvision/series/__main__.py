"""
Purpose:
        Configuration and Run-time settings for the XBMC Support Programs

"""

import daddyvision.series
import os
import sys
import logging
from daddyvision.common import logger
from daddyvision.common.options import CoreOptionParser
from daddyvision.series.manager import Manager

__author__ = "AJ Reynolds"
__copyright__ = "Copyright 2011, AJ Reynolds"
__credits__ = []
__license__ = "GPL"

__pgmname__ = 'series'
__version__ = '$Rev$'

__maintainer__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"
__status__ = "Development"

logger.initialize()

parser = CoreOptionParser()
options = parser.parse_args()[0]

try:
    manager = Manager(options)
except IOError, e:
    # failed to load config, TODO: why should it be handled here?
    __init__.log.exception(e)
    logger.flush_logging_to_console()
    sys.exit(1)

log_level = logging.getLevelName(options.loglevel.upper())
log_file = os.path.expanduser(manager.options.logfile)
# If an absolute path is not specified, use the config directory.
if not os.path.isabs(log_file):
    log_file = os.path.join(manager.config_base, log_file)
logger.start(log_file, log_level)

manager.execute()

