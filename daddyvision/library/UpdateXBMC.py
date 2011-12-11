#!/usr/bin/env python
"""
Author: AJ Reynolds

Date: 11-27-2010

Purpose:
Program to watch for changes in the TV, Movie, and Links folders and take the
appropriate actions

"""
from configobj import ConfigObj
from daemon import Daemon
from distribute import Distribute
from getconfig import GetConfig
from optparse import OptionParser
import logging
import logging.handlers
import os.path
import pyinotify
import re
import sys
import time

__version__ = '$Rev$'
__pgmname__ = 'UpdateXBMC'
PgmDir		 = os.path.dirname(__file__)
HomeDir	 = os.path.expanduser('~')
ConfigDir	 = os.path.join(HomeDir, '.config')
LogDir		 = os.path.join(HomeDir, 'log')
DataDir	 = os.path.join(HomeDir, __pgmname__)

# Set up a specific logger with our desired output level
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
ml = logging.handlers.TimedRotatingFileHandler(os.path.join(LogDir, '%s.log' % __pgmname__), when='midnight', backupCount=7)
dl = logging.handlers.TimedRotatingFileHandler(os.path.join(LogDir, '%s_debug.log' % __pgmname__), when='midnight', backupCount=7)
ch = logging.StreamHandler()
ml.setLevel(logging.INFO)
dl.setLevel(logging.DEBUG)
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s - %(message)s")
ml.setFormatter(formatter)
dl.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(ml)
logger.addHandler(dl)
logger.addHandler(ch)

class MyDaemon(Daemon):
	def run(self):
		self.parms = GetConfig()
		self.options = options
		while True:
			if not os.path.exists(self.parms.series_dir):
				logger.error("Path Not Found: %s" % self.parms.series_dir)
				logger.error("Invalid Config Entries, Ending")
				sys.exit(1)

			if self.options.debug:
				logger.debug('Found watch directory: %s' % self.parms.series_dir)

			pHandler = PackageHandler()
			watchManager = pyinotify.WatchManager()
			mask	 = pyinotify.IN_CREATE | pyinotify.IN_MOVED_TO
			handler = EventHandler(pHandler)
			notifier = pyinotify.Notifier(watchManager, handler)
			if self.options.debug:
				logger.debug('Notifier Created')
			watchDir1	 = watchManager.add_watch(self.parms.series_dir, mask, rec=True)
			logger.info('Watching Directory: %s' % (self.parms.series_dir))
			watchDir2	 = watchManager.add_watch(self.parms.movies_dir, mask, rec=True)
			logger.info('Watching Directory: %s' % (self.parms.movies_dir))
			watchDir3	 = watchManager.add_watch("/mnt/Links/", mask, rec=True)
			logger.info('Watching Directory: %s' % "/mnt/Links/")
			if not options.debug:
				try:
					notifier.loop()
				except:
					pass
				pass
			else: notifier.loop()

class EventHandler(pyinotify.ProcessEvent):
	''' Handle Events related to new files being moved or added to the watched folder
	'''
	def __init__(self, pHandler):
		self.pHandler = pHandler

	def process_IN_CREATE(self, event):
		logger.info("-----------------------------------")
		logger.info("Create Event: " + event.pathname)
		self.pHandler.SyncRmt(event.pathname)

	def process_IN_MOVED_TO(self, event):
		logger.info("-----------------------------------")
		logger.info("Moved Event: " + event.pathname)
		self.pHandler.SyncRmt(event.pathname)

class PackageHandler(object):
	''' Process the file or directory passed
	'''
	def __init__(self):
		pass
		if daemon.options.debug:
			logger.debug('PackageHandler Initialized')

	def SyncRmt(self, pathname):
		logger.debug(pathname)

		tvshow = re.split('^\/mnt\/TV', pathname)
		movie = re.split('^\/mnt\/Movies/Films', pathname)

		for user in ['aly', 'ben', 'kim']:
			links = re.match('^\/mnt\/Links/%s' % user, pathname)
			if links:
				logger.info('New Link Added: %s' % pathname)
			elif len(tvshow) > 1:
				tgt = '/mnt/Links/%s' % user
				symlink = tgt + tvshow[1]
				logger.debug(symlink)
				if os.path.exists(symlink):
					logger.info('update required: %s' % os.path.basename(os.path.split(pathname)[0]))
				else:
					continue
			elif len(movie) > 1:
				tgt = '/mnt/Links/%s/Movies/' % user
				symlink = tgt + movie[1]
				logger.debug(symlink)
				if os.path.exists(symlink):
					logger.info('update required: %s' % os.path.basename(os.path.split(pathname)[0]))
				else:
					continue
			else:
				continue

			logger.info('update required: %s' % user)
			if user == 'aly':
				cmd = 'syncrmt -abr&'
			elif user == 'ben':
				cmd = 'syncrmt -pbr&'
			else:
				cmd = 'syncrmt -kbr&'
			os.system(cmd)
		return

if __name__ == "__main__":

	parser = OptionParser(
							"%prog [options] start|stop|restart",
							version="%prog " + __version__
							)
	parser.add_option("-e",
						"--errors",
						dest="error",
						action="store_true",
						default=False,
						help="omit all but error logging"
										)
	parser.add_option("-q",
						"--quiet",
						dest="quiet",
						action="store_true",
						default=False,
						help="omit informational logging"
										)
	parser.add_option("-v",
						"--verbose",
						dest="verbose",
						action="store_true",
						default=False,
						help="increase informational logging"
						)
	parser.add_option("-d",
						"--debug",
						dest="debug",
						action="store_true",
						default=False,
						help="increase informational logging to include debug information"
						)

	options, args = parser.parse_args()

	num_options = 0
	if options.error:
		logger.setLevel(logging.ERROR)
		ch.setLevel(logging.ERROR)
		num_options += 1
	if options.quiet:
		logger.setLevel(logging.WARNING)
		ch.setLevel(logging.WARNING)
		num_options += 1
	if options.verbose:
		logger.setLevel(logging.DEBUG)
		ch.setLevel(logging.DEBUG)
		num_options += 1
	if options.debug:
		logger.setLevel(logging.DEBUG)
		ch.setLevel(logging.DEBUG)
		num_options += 1
	if num_options > 1:
		parser.error("Conflicting options requested. Reconsider your options!")

	logger.info('********************************************************************************************')
	logger.info("Parsed command line options: %r" % options)
	logger.debug("Parsed arguments: %r" % args)

	if not options.debug and not options.verbose:
		if len(args) != 1 or (args[0].lower() != 'start' and args[0].lower() != 'stop' and args[0].lower() != 'restart'):
			parser.error('Invalid or missing arguments')

	daemon = MyDaemon('/tmp/daemon-UpdateXBMC.pid')

	if options.debug or options.verbose:
		logger.info('******* DEBUG Selected, Not using Daemon ********')
		daemon.run()
	elif 'start' == args[0]:
		logger.info("*************** STARTING DAEMON ****************")
		daemon.start()
	elif 'stop' == args[0]:
		logger.info("*************** STOPING DAEMON *****************")
		daemon.stop()
	elif 'restart' == args[0]:
		logger.info("************** RESTARTING DAEMON ***************")
		logger.info("**************    %s     ***************" % __version__)
		daemon.restart()
