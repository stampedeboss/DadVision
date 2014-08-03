#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Purpose:
     purpose

'''
from library import Library
from common import logger
from common.daemon import Daemon
from library.rmtfunctions import listItems, updateLinks
from rpyc.utils.server import ThreadedServer # or ForkingServer
import logging
import os
import rpyc
import sys

__pgmname__ = 'rpyc_server'
__version__ = '@version: $Rev$'

__author__ = "@author: AJ Reynolds"
__copyright__ = "@copyright: Copyright 2011, AJ Reynolds"
__license__ = "@license: GPL"

__maintainer__ = "@organization: AJ Reynolds"
__status__ = "@status: Development"
__credits__ = []

TRACE = 5
VERBOSE = 15
log = logging.getLogger(__pgmname__)


class MyDaemon(Daemon):

    def run(self):

        server = ThreadedServer(DaddyVisionService, hostname = '192.168.9.201', port = 32489, logger = log)
        server.start()

class DaddyVisionService(rpyc.Service):

    def exposed_ListItems(self, host, content_type, compress=False):
        return listItems(host, content_type, compress)

    def exposed_UpdateLinks(self, host, request):
        return updateLinks(host, request)

if __name__ == '__main__':

    logger.initialize()
    library = Library()
    daemon = MyDaemon('/tmp/daemon-rpyc_server.pid')

    Library.args = library.options.parser.parse_args(sys.argv[1:])
    log.debug("Parsed command line: {!s}".format(library.args))

    log_level = logging.getLevelName(library.args.loglevel.upper())

    if library.args.logfile == 'daddyvision.log':
        log_file = '{}.log'.format(__pgmname__)
    else:
        log_file = os.path.expanduser(library.args.logfile)

    # If an absolute path is not specified, use the default directory.
    if not os.path.isabs(log_file):
        log_file = os.path.join(logger.LogDir, log_file)

    logger.start(log_file, log_level, timed=True)

    if library.args.loglevel != 'DEBUG' and library.args.loglevel != 'TRACE':
        if len(library.args.library) != 1:
            library.options.parser.error('Command Error: Missing keyword - "start", "restart" or "stop" needed')
        if library.args.library[0].lower() not in ['start', 'restart', 'stop']:
            library.options.parser.error('Command Error: Invalid keyword - "start", "restart" or "stop" needed')

    try:
        from subprocess import Popen, PIPE
        _p = Popen(["svnversion", "/usr/local/lib/python2.7/dist-packages/dadvision/"], stdout=PIPE)
        REVISION = _p.communicate()[0]
        REVISION = 'Revision: {}'.format(REVISION.strip('\n').strip())
        _p = None  # otherwise we get a wild exception when Django auto-reloads
    except Exception, e:
        print "Could not get revision number: ", e
        REVISION = 'Version: {}'.format(__version__)

    if library.args.loglevel == 'DEBUG' or library.args.loglevel == 'TRACE':
        log.info('******* DEBUG Selected, Not using Daemon ********')
        log.info("**************  %s    ***************" % REVISION)
        daemon.run()
    elif library.args.library[0].lower() == 'start':
        log.info("*************** STARTING DAEMON ****************")
        log.info("**************  %s    ***************" % REVISION)
        daemon.start()
    elif library.args.library[0].lower() == 'stop':
        log.info("*************** STOPING DAEMON *****************")
        log.info("**************  %s    ***************" % REVISION)
        daemon.stop()
    elif library.args.library[0].lower() == 'restart':
        log.info("************** RESTARTING DAEMON ***************")
        log.info("**************  %s    ***************" % REVISION)
        daemon.restart()
