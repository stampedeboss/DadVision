# -*- coding: UTF-8 -*-
'''

Purpose:
	Initialization Routine for Library

	Setup of standard Logging and Command Line Options

'''

import fnmatch
import logging
import unicodedata
import re
import filecmp
import shutil
import sys

from subprocess import check_call, Popen, PIPE, CalledProcessError
from os import remove, rmdir, makedirs, chmod, rename, walk, listdir
from os.path import dirname, exists, getsize, isdir, isfile, splitext

from fuzzywuzzy import fuzz

from dadvision import DadVision
from common.exceptions import InvalidPath, UnexpectedErrorOccured

__pgmname__     = 'Library'

__author__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"

__maintainer__ = __author__

__copyright__ = "Copyright 2011, AJ Reynolds"
__license__ = "GPL"

log = logging.getLogger(__pgmname__)

class Library(object):

	regex_repack = re.compile('^.*(repack|proper).*$', re.IGNORECASE)

	def __init__(self):
		super(Library, self).__init__()


def countFiles(pathname, types=[], exclude_list=[]):

	if not exists(pathname) or not isdir(pathname):
		raise InvalidPath("Requested pathname does not exist or isn't a directory : {}".format(pathname))

	_file_count = 0
	dir_count = 0
	dir_skipped = 0

	for _root, _dirs, _files in walk(pathname, followlinks=True):

		dir_count += 1
		_dirs.sort()
		_dirs_temp = sorted(_dirs)
		if exclude_list != []:
			for _dir in _dirs_temp:
				if ignored(_dir):
					dir_skipped += 1
					_dirs.remove(_dir)

		for _file in _files:
			ext = os.path.splitext(_file)[1][1:]
			if types != []:
				if ext.lower() in types:
					_file_count += 1
			else:
				_file_count += 1

	return _file_count

def decode(coded_text):

	if type(coded_text) is list and not type(coded_text[0]) in [str, unicode]:
		return coded_text
	elif not type(coded_text) in [unicode, list]:
		return coded_text

	if type(coded_text) is unicode:
		coded_text = unicodedata.normalize('NFKD', coded_text).encode('ascii', 'ignore')
		return coded_text.replace("&amp;", "&").replace("/", "_")

	decoded_text = []
	for item in coded_text:
		if type(item) is unicode:
			item = unicodedata.normalize('NFKD', item).encode('ascii', 'ignore')
			decoded_text.append(item.replace("&amp;", "&").replace("/", "_"))
		elif type(item) is str:
			decoded_text.append(item.replace("&amp;", "&").replace("/", "_"))
		else:
			decoded_text.append(item)

	if len(decoded_text) < 2:
		decoded_text = decoded_text[0]
	return decoded_text

def del_dir(pathname, Tree=False):

	if not isdir(pathname):
		raise InvalidPath('Invalid Path was requested for deletion: {}'.format(pathname))
	try:
		log.trace('Deleting Directory: {}'.format(pathname))
		if Tree:
			shutil.rmtree(pathname)
		else:
			rmdir(pathname)
	except:
		log.warn('Delete Directory: Unable to Delete requested directory: %s' % (sys.exc_info()[1]))
		raise

def del_file(pathname):

	if isdir(pathname):
		raise InvalidPath('Path was requested for deletion: {}'.format(pathname))
	try:
		log.trace('Deleting File as Requested: {}'.format(pathname))
		remove(pathname)
	except:
		log.warn('Delete File: Unable to Delete requested file: %s' % (sys.exc_info()[1]))
		raise

def duplicate(original, new, other):

	if not exists(new):
		return False

	if new == original:
		del_file(original)
		return True

	try:
		if DadVision.args.force_rename or (other and other.lower() in ["proper"]):
			log.warn("Replacing Existing with repack or Force Rename Requested: {}".format(original))
			del_file(new)
			return False

		if getsize(original) > getsize(new):
			log.info("Replacing Existing with Larger Version: {}".format(new))
			del_file(new)
			return False

		log.trace("Comparing existing file to new, may run for some time.")
		if filecmp.cmp(original, new):
			log.info("Deleting New File, Same File already at destination!: {}".format(new))
			del_file(original)
			return True
		del_file(new)
		return False
	except (InvalidPath, OSError), e:
		log.error("Unable to remove File: {}".format(e))
		return True

def ignored(name):
	""" Check for ignored pathnames.
	"""
	rc = []
	if name == 'New': rc.append(True)
	rc.append(any(fnmatch.fnmatch(name.lower(), pattern) for pattern in DadVision.settings.ExcludeList))
	rc.append(any(fnmatch.fnmatch(name.lower(), pattern) for pattern in DadVision.settings.IgnoreGlob))
	return any(rc)

def media(name):
	""" Check for desired pathnames.
	"""
	rc = []
	rc.append(any(fnmatch.fnmatch(name.lower(), '*.{}'.format(pattern))
	              for pattern in DadVision.settings.MediaExt))
	return any(rc)

def make_dir(pathname):
	try:
		if not exists(pathname):
			makedirs(pathname)
			chmod(pathname, 0775)
			log.info("Successfully Created: %s" % pathname)
	except OSError, e:
		log.error("Unexpected error: %s" % e)
		raise UnexpectedErrorOccured("Unexpected error: %s" % e)
	return

def matching(value1, value2, factor=None):
	"""

	:rtype : object
	"""

	fuzzy = []
	fuzzy.append(fuzz.ratio(value1.lower(), value2.lower()))
	fuzzy.append(fuzz.partial_ratio(value1.lower(), value2.lower()))
	fuzzy.append(fuzz.token_set_ratio(value1.lower(), value2.lower()))
	fuzzy.append(fuzz.token_sort_ratio(value1.lower(), value2.lower()))

	log.debug("=" * 50)
	log.debug('Fuzzy Compare: {} - {}'.format(value1.lower(), value2.lower()))
	log.debug("-" * 50)
	log.debug('{}: Simple Ratio'.format(fuzzy[0]))
	log.debug('{}: Partial Ratio'.format(fuzzy[1]))
	log.debug('{}: Token Set Ratio'.format(fuzzy[2]))
	log.debug('{}: Token Sort Ratio'.format(fuzzy[3]))

	if factor:      # Will return True or False
		log.debug('Return with Factor - {}: {}'.format(factor, any([fr > factor for fr in fuzzy])))
		return any([fr >= factor for fr in fuzzy])

	score = 0
	entries = 0
	for fr in fuzzy:
		score += fr
		if fr > 0: entries += 1

	if entries > 0: score = score/entries
	else: score = 0

	log.debug('Return without Factor - Score: {}'.format(score))

	return score

def move_files(old, new):

	files_to_move = listdir(dirname(old))
	file_list = []

	for entry in files_to_move:
		entry = join(dirname(old), entry)
		if any(fnmatch.fnmatch(entry.lower(), pattern) for pattern in DadVision.settings.AdditionalGlob):
			file_list.append(entry)
		else:
			if ignored(entry):
				if isfile(entry): del_file(entry)
				if isdir(entry):  del_dir(entry, Tree=True)

	if file_list:
		try:
			cmd = ['rsync', '-rptvhogLR', '--progress', '--remove-source-files',
				   '--partial-dir=.rsync-partial']
			cmd.extend(file_list)
			cmd.append(dirname(old))
			log.verbose(' '.join(cmd))
			check_call(cmd, shell=False, stdin=None, stdout=None, stderr=None, cwd=dirname(old))
		except CalledProcessError, exc:
			log.error("Incremental rsync Command returned with RC=%d, Ending" % (exc.returncode))
			raise UnexpectedErrorOccured(exc)

def rename_file(old, new):

	if isdir(old): raise InvalidPath('Directory was Requested for File Rename: {}'.format(old))
	try:
		if not exists(dirname(new)): make_dir(dirname(new))
		rename(old, new)
		chmod(new, 0664)
		log.info("Successfully Renamed: %s" % new)
		if len(listdir(dirname(old))) > 1:
			move_files(old, new)
		if len(listdir(dirname(old))) == 0:
			del_dir(dirname(old))
	except OSError, e:
		log.error("Unable to Rename File: {} - {}".format(old, e))
		raise UnexpectedErrorOccured("Unable to Rename File: {} - {}".format(old, e))


if __name__ == '__main__':

	from sys import argv
	from logging import DEBUG; TRACE = 5; VERBOSE = 15
	from common import logger
	logger.initialize(level=DEBUG)
	DadVision.args = DadVision.cmdoptions.ParseArgs(argv[1:])

	library = Library()

	log.info(" ")