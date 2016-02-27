# -*- coding: UTF-8 -*-
'''

Purpose:
	Initialization Routine for Library

	Setup of standard Logging and Command Line Options

'''

import fnmatch
import unicodedata

from dadvision import DadVision

__pgmname__     = 'library'

__author__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"

__maintainer__ = __author__

__copyright__ = "Copyright 2011, AJ Reynolds"
__license__ = "GPL"


class Library(DadVision):

	def __init__(self):
		super(Library, self).__init__()

	def _ignored(self, name):
		""" Check for ignored pathnames.
		"""
		rc = []
		if name == 'New': rc.append(True)
		rc.append(any(fnmatch.fnmatch(name.lower(), pattern) for pattern in Library.settings.ExcludeList))
		rc.append(any(fnmatch.fnmatch(name.lower(), pattern) for pattern in Library.settings.IgnoreGlob))
		return any(rc)

	def decode(self, coded_text):

		if type(coded_text) is unicode:
			decoded_text = unicodedata.normalize('NFKD', coded_text).encode('ascii', 'ignore')
		else:
			decoded_text = coded_text

		decoded_text = decoded_text.replace("&amp;", "&").replace("/", "_")

		return decoded_text


if __name__ == '__main__':

	import sys
	import logging

	log = logging.getLogger(__pgmname__)
	DadVision.args = DadVision.cmdoptions.ParseArgs(sys.argv[1:])

	library = Library()
	log.verbose("*** LOGGING STARTED ***")

	_lib_paths = DadVision.args.filespec

	pass