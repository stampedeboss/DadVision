#!/usr/bin/env python
# encoding: utf-8
'''

Purpose:
	cmd_options -- general Command Line Options Handler

'''
import logging
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from os.path import dirname, expanduser, join, split, splitext, isabs
from subprocess import Popen, PIPE
from sys import argv

__pgmname__ = 'cmdoptions'

__author__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"

__maintainer__ = __author__

__copyright__ = "Copyright 2016, AJ Reynolds"
__license__ = "GPL"

log = logging.getLogger(__pgmname__)

try:
	_p = Popen(["git", "describe", "HEAD", "--long", "--tags"],
			   cwd=dirname(dirname(__file__)),
			   stdout=PIPE)
	__version__ = _p.communicate()[0].strip('\n').strip()
except Exception, e:
	log.error("Could not get revision number: {}".format(e))
	__version__ = 'Unknown'

try:
	_p = Popen(["git", "log", "-1", "--format=%cd", "--date=local"],
			   cwd=dirname(dirname(__file__)),
			   stdout=PIPE)
	__commit_date__ = _p.communicate()[0].strip('\n').strip()
except Exception, e:
	log.error("Could not get commit date: {}".format(e))
	__commit_date__ = 'Unknown'

_p = None

program_version_message = '%%(prog)s %s (%s)' % (__version__, __commit_date__)
program_license = '''

Created by AJ Reynolds.
Copyright 2013 AJ Reynolds. All rights reserved.

Licensed under the GPL License

Distributed on an "AS IS" basis without warranties
or conditions of any kind, either express or implied.

USAGE
'''

class CmdOptions(ArgumentParser):
	'''Define Standard Options for All Command lines.'''

	def __init__(self, **kwargs):

		super(CmdOptions, self).__init__(self, **kwargs)

		# Setup argument parser
		self.parser = ArgumentParser(description=program_license,
						 formatter_class=RawDescriptionHelpFormatter,
						 conflict_handler='resolve')
		self.parser.add_argument('-V', '--version',
						 action='version',
						 version=program_version_message)
		self.parser.add_argument('--logdir', action='store',
						 dest='logdir', default='/srv/log',
						 help='Specify a log directory [default: %(default)s]')
		self.parser.add_argument('--logfile', action='store',
						 dest='logfile', default=None,
						 help='Specify a custom logfile filename [default: %(default)s]')
		self.parser.add_argument("--Error-Log", dest="errorlog", action="store_true", default=False,
								help="Create Seperate Log for Errors")
		self.parser.add_argument("--timed", "--timed-roll-over", dest="timed",
		                         action="store_true", default=False,
								help="Logs will start new daily at midnight")
		self.parser.add_argument('pathname', metavar="pathname", nargs='*',
						 help="paths to folder(s)/file(s) ")

		group_loglvl = self.parser.add_mutually_exclusive_group()
		group_loglvl.add_argument("--trace", dest="loglevel",
						 default='INFO',
						 action="store_const", const="TRACE",
						 help="increase logging to include trace information")
		group_loglvl.add_argument("--debug", dest="loglevel",
						 action="store_const", const="DEBUG",
						 help="increase logging to include debugging information")
		group_loglvl.add_argument("--verbose", dest="loglevel",
						 action="store_const", const="VERBOSE",
						 default='INFO',
						 help="increase logging to include additional informational information")
		group_loglvl.add_argument("--info", dest="loglevel",
						 action="store_const", const="INFO",
						 help="Standard logging to include informational information")
		group_loglvl.add_argument("--quiet", dest="loglevel",
						 action="store_const", const="WARNING",
						 help="Limit logging to only include Warning, Errors, and Critical information")
		group_loglvl.add_argument("--errors", dest="loglevel",
						 action="store_const", const="ERROR",
						 help="Limit logging to only include Errors and Critical information")
		group_loglvl.add_argument("--critical", dest="loglevel",
						 action="store_const", const="CRITICAL",
						 help="Limit logging to only include Critical information")

		#TMDB_group = self.parser.add_argument_group("Get TMDB Information Options"),
		#TMDB_group.add_argument("--movie", type=str, dest='MovieName', nargs='?')
		#TMDB_group.add_argument("--year", type=int, dest='Year', nargs='?')

	def ParseArgs(self, sys_argv):

		args = self.parser.parse_args(sys_argv)
		log.debug("Parsed command line: {!s}".format(args))

		if not args.logfile:
			args.logfile = '{}.log'.format(splitext(split(argv[0])[1])[0])

		args.logfile = expanduser(args.logfile)
		if not isabs(args.logfile):
			args.logfile = join(args.logdir, args.logfile)

		return args


if __name__ == "__main__":

	from logging import INFO, DEBUG, ERROR; TRACE = 5; VERBOSE = 15
	from common import logger
	logger.initialize(level=DEBUG)

	opt = CmdOptions()
	args = opt.ParseArgs(argv[1:])
