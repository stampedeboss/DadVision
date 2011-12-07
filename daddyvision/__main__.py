"""
    Main entry point for Command Line Interface

"""

import os
import sys
import logging
from daddyvision import logger
#from daddyvision.options import CoreOptionParser
#from daddyvision import settings

__version__ = '$Rev$'
__pgmname__ = '__init__'

PGM_DIR      = os.path.dirname(__file__)
HOME_DIR     = os.path.expanduser('~')
CONFIG_DIR_B = os.path.join(HOME_DIR, '.config')
CONFIG_DIR   = os.path.join(CONFIG_DIR_B, 'VideoLibrary')
LOG_DIR      = os.path.join(HOME_DIR, 'log')

log = logging.getLogger('main')

logger.initialize()

log.warn('WARNING Message')
log.error('ERROR Message')
log.info('INFO Message')
log.verbose('VERBOSE Message')
log.debug('DEBUG Message')
log.trace('TRACE Message')


#parser = CoreOptionParser()
#options = parser.parse_args()[0]
#settings = settings()

#try:
#    manager = Manager(options)
#except IOError, e:
#    # failed to load config, TODO: why should it be handled here?
#    log.exception(e)
#    logger.flush_logging_to_console()
#    sys.exit(1)

#log_level = logging.getLevelName(options.loglevel.upper())
#logger.start(os.path.join(manager.config_base, 'VideoLibrary.log'), log_level)

#manager.execute()

