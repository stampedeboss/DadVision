#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Purpose:
     purpose

'''
from daddyvision.common import logger
from daddyvision.common.daemon import Daemon
from daddyvision.common.options import OptionParser
from rpyc.utils.server import ThreadedServer # or ForkingServer
from daddyvision.library.rmtfunctions import listItems, updateLinks
import logging
import os
import rpyc
import sys

__pgmname__ = 'rpyc_server'
__version__ = '$Rev$'

__author__ = "AJ Reynolds"
__copyright__ = "Copyright 2011, AJ Reynolds"
__credits__ = []
__license__ = "GPL"

__maintainer__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"
__status__ = "Development"

TRACE = 5
VERBOSE = 15

log = logging.getLogger(__pgmname__)

logger.initialize()

TRACE = 5
VERBOSE = 15

class MyDaemon(Daemon):

    def run(self):

        server = ThreadedServer(DaddyVisionService, hostname = '192.168.9.201', port = 32489, logger = log)
        server.start()

class DaddyVisionService(rpyc.Service):

    def exposed_ListItems(self, user, content_type, compress=False):
        return listItems(user, content_type, compress)

    def exposed_UpdateLinks(self, user, request):
        return updateLinks(user, request)

if __name__ == '__main__':
    parser = OptionParser()
    options, args = parser.parse_args()

    log_level = logging.getLevelName(options.loglevel.upper())

    if options.logfile == 'daddyvision.log':
        log_file = '{}.log'.format(__pgmname__)
    else:
        log_file = os.path.expanduser(options.logfile)

    # If an absolute path is not specified, use the default directory.
    if not os.path.isabs(log_file):
        log_file = os.path.join(logger.LogDir, log_file)

    logger.start(log_file, log_level, timed=True)

    log.debug("Parsed command line options: {!s}".format(options))
    log.debug("Parsed arguments: %r" % args)


    daemon = MyDaemon('/tmp/daemon-rpyc_server.pid')

    try:
        from subprocess import Popen, PIPE
        _p = Popen(["svnversion",  "/usr/local/lib/python2.7/dist-packages/daddyvision/"], stdout=PIPE)
        REVISION= _p.communicate()[0]
        REVISION='Revision: {}'.format(REVISION.strip('\n').strip())
        _p = None # otherwise we get a wild exception when Django auto-reloads
    except Exception, e:
        print "Could not get revision number: ", e
        REVISION='Version: {}'.format(__version__)

    if options.loglevel == 'DEBUG' or options.loglevel == 'TRACE':
        log.info('******* DEBUG Selected, Not using Daemon ********')
        log.info("**************  %s    ***************" % REVISION)
        daemon.run()
    elif 'start' == args[0]:
        log.info("*************** STARTING DAEMON ****************" )
        log.info("**************  %s    ***************" % REVISION)
        daemon.start()
    elif 'stop' == args[0]:
        log.info("*************** STOPING DAEMON *****************" )
        log.info("**************  %s    ***************" % REVISION)
        daemon.stop()
    elif 'restart' == args[0]:
        log.info("************** RESTARTING DAEMON ***************" )
        log.info("**************  %s    ***************" % REVISION)
        daemon.restart()