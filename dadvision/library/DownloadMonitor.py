#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Purpose:
	Program to watch for changes in the download folders and invoke the
	appropriate actions based on subject matter.

	Subject matter is arranged in the following categories:
		Series, Movies, or Other/Unknown
"""
import logging
import os
import sys
import traceback

import pyinotify
from common import logger
from common.exceptions import ConfigValueError
from library import Library
from pyinotify import IN_CREATE, IN_MOVED_TO

from daemon import Daemon
from distribute import Distribute

TRACE = 5
VERBOSE = 15

__pgmname__ = 'DownloadMonitor'

__author__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"

__maintainer__ = __author__

__copyright__ = "Copyright 2011, AJ Reynolds"
__license__ = "GPL"

log = logging.getLogger(__pgmname__)

class MyDaemon(Daemon):

	def __init__(self, pidfile, distribute, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):

		self.stdin = stdin
		self.stdout = stdout
		self.stderr = stderr
		self.pidfile = pidfile
		self.distribute = distribute
		self.pHandler = PackageHandler(self.distribute)
		self.handler = EventHandler(self.pHandler)

		try:
			from subprocess import Popen, PIPE
			_p = Popen(["git", "describe", "HEAD", "--long", "--tags"],
					   cwd=os.path.dirname(os.path.dirname(__file__)),
					   stdout=PIPE)
			__version__ = _p.communicate()[0]
			__version__ = '{}'.format(__version__.strip('\n').strip())
			_p = None  # otherwise we get a wild exception when Django auto-reloads
		except Exception, e:
			print "Could not get version number: ", e
			__version__ = 'UNKNOWN'

	def run(self):

		if not os.path.exists(library.settings.DownloadDir):
			log.error("Path Not Found: %s" % library.settings.DownloadDir)
			raise ConfigValueError("Configuration Issue Watch Directory Not Found: %s" % library.settings.DownloadDir)

		log.debug('Found watch directory: %s' % library.settings.DownloadDir)

		while True:
			self.watchManager = pyinotify.WatchManager()
			self.notifier = pyinotify.Notifier(self.watchManager, self.handler)
			log.debug('Notifier Created')

			self.mask = IN_CREATE | IN_MOVED_TO

			DownloadDir1 = self.watchManager.add_watch(library.settings.DownloadDir, self.mask, rec=True)
			log.info('Watching Directory: %s' % library.settings.DownloadDir)
			DownloadDir2 = self.watchManager.add_watch(library.settings.DownloadMovies, self.mask, rec=True)
			log.info('Watching Directory: %s' % library.settings.DownloadMovies)
			DownloadDir3 = self.watchManager.add_watch(library.settings.DownloadSeries, self.mask, rec=True)
			log.info('Watching Directory: %s' % library.settings.DownloadSeries)

			if library.args.loglevel not in ['DEBUG', 'TRACE']:
				try:
					self.notifier.loop()
				except:
					an_error = traceback.format_exc(1)
					log.error(traceback.format_exception_only(type(an_error), an_error)[-1])
			else:
				try:
					self.notifier.loop()
				except KeyboardInterrupt:
					sys.exit(8)
				except:
					an_error = traceback.format_exc(1)
					log.error(traceback.format_exception_only(type(an_error), an_error)[-1])

class EventHandler(pyinotify.ProcessEvent):
	''' Handle Events related to new files being moved or added to the watched folder
	'''
	def __init__(self, pHandler):
		self.pHandler = pHandler

	def process_IN_CREATE(self, event):
		log.info("-----------------------------------")
		log.info("Create Event: {}".format(os.path.dirname(event.pathname)))
		log.info("        File: {}".format(os.path.basename(event.pathname)))
		self.pHandler.NewDownload(event.pathname)

	def process_IN_MOVED_TO(self, event):
		log.info("-----------------------------------")
		log.info("Moved Event: {}".format(os.path.dirname(event.pathname)))
		log.info("       File: {}".format(os.path.basename(event.pathname)))
		self.pHandler.NewDownload(event.pathname)

class PackageHandler(object):
	''' Process the file or directory passed
	'''
	def __init__(self, distribute):
		self.distribute = distribute
		log.debug('PackageHandler Initialized')

	def NewDownload(self, pathname):
		try:
			self.distribute.distribute(pathname)
		except:
			an_error = traceback.format_exc(1)
			log.error(traceback.format_exception_only(type(an_error), an_error)[-1])
			log.error('Rename skipped for: {}'.format(os.path.basename(pathname)))


if __name__ == "__main__":

	logger.initialize()

	library = Distribute()
	daemon = MyDaemon('/tmp/daemon-DownloadMonitor2.pid', library)

	Library.args = library.options.parser.parse_args(sys.argv[1:])
	log.debug("Parsed command line: {!s}".format(library.args))

	log_level = logging.getLevelName(library.args.loglevel.upper())

	if library.args.logfile == 'daddyvision.log':
		log_file = '{}.log'.format(__pgmname__)
	else:
		log_file = os.path.expanduser(library.args.logfile)

	# If an absolute path is not specified, use the default directory.
	if not os.path.isabs(log_file):
		log_file = os.path.join(logger.LogDir, __pgmname__, log_file)

	logger.start(log_file, log_level, timed=True)

	if library.args.loglevel != 'DEBUG' and library.args.loglevel != 'TRACE':
		if len(library.args.library) != 1:
			library.options.parser.error('Command Error: Missing keyword - "start", "restart" or "stop" needed')
		if library.args.library[0].lower() not in ['start', 'restart', 'stop']:
			library.options.parser.error('Command Error: Invalid keyword - "start", "restart" or "stop" needed')

	try:
		from subprocess import Popen, PIPE
		_p = Popen(["git", "describe", "HEAD", "--long", "--tags"],
				   cwd=os.path.dirname(os.path.dirname(__file__)),
				   stdout=PIPE)
		#_p = Popen(["svnversion", "/usr/local/lib/python2.7/dist-packages/dadvision/"], stdout=PIPE)
		REVISION = _p.communicate()[0]
		REVISION = '{}'.format(REVISION.strip('\n').strip())
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
