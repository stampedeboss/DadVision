#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''

Purpose:
	Scan Video Libraries to check for errors with the video
	structure or conent
'''
import os
import re
import tempfile
import logging

from subprocess import Popen, PIPE

from library import countFiles

from dadvision import DadVision

__pgmname__ = 'chkvideo'

__author__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"

__maintainer__ = __author__

__copyright__ = "Copyright 2016, AJ Reynolds"
__license__ = "GPL"

log = logging.getLogger(__pgmname__)

FilesWithIssues = {}

class ChkVideo(DadVision):
	def __init__(self):

		super(ChkVideo, self).__init__()

		chkvideo_group = self.cmdoptions.parser.add_argument_group("ChkVideo Options", description=None)
		chkvideo_group.add_argument("-d", "--deep", dest="deep",action="store_true",
									default=False, help="Perform Detailed Check of AVI Files")

def chkVideoDir(pathname, deep=False):
	log.trace('Checking Directory: %s' % pathname)
	global FilesWithIssues

	_files_checked = 0
	_file_count = countFiles(pathname)

	if _file_count == 0:
		log.warn('Path contains no video content, Stopping scan. Path: {}'.format(pathname))
		return {}

	log.info('Number of Files in Tree: %s' % _file_count)

	if os.path.isdir(pathname):
		for root, dirs, files in os.walk(os.path.abspath(pathname), followlinks=False):
			dirs = sorted(dirs)
			files = sorted(files)
			for fname in files:
				fq_fname = os.path.join(root, fname)
				rc = chkVideoFile(fq_fname, deep)
				if deep and rc[0] > 0:
					FilesWithIssues[fq_fname] = rc[1]
				elif rc > 0:
					FilesWithIssues[fq_fname] = 'Errors Found'
					log.verbose('File has issues: %s' % fq_fname)
				_files_checked += 1
				quotient, remainder = divmod(_files_checked, 250)
				if remainder == 0:
					log.info('Files Checked: %2.2f%% - %5s of %5s   Number of Errors: %s' % (_files_checked / _file_count, _files_checked, _file_count, len(FilesWithIssues)))
		log.info('Files Checked: %2.2f%% - %5s of %5s   Number of Errors: %s' % (_files_checked / _file_count, _files_checked, _file_count, len(FilesWithIssues)))

	return FilesWithIssues

def chkVideoFile(pathname, deep=False):
	log.trace('Checking File: %s' % pathname)

	ext = os.path.splitext(pathname)[1][1:]
	if ext == 'avi':
		if deep:
			rc = chkAVId(pathname)
			return rc
		rc = chkAVI(pathname)
		if rc == 1:
			rc = chkAVId(pathname)[0]
	elif ext == 'mkv':
		rc = chkMKV(pathname)
	else:
		rc = 0
	return rc

def chkAVId(pathname):
	regex_bracket = re.compile('.*\].*$', re.IGNORECASE)
	regex_text = re.compile('((frame)|(Press)|(PAR))', re.IGNORECASE)
	error_msgs = []
	rc = 0
	_ffmpeg_out = tempfile.NamedTemporaryFile()
	cmd = ['ffmpeg', '-v', '5', '-i', pathname, '-f', 'null', '-']
	process = Popen(cmd, shell=False, stdin=None, stdout=None, stderr=PIPE, cwd=None)
	output = process.stderr.readlines()
	for line in output:
		if not regex_bracket.match(line):
			continue
		else:
			if not regex_text.search(line):
				error_msgs.append(line.strip('\n'))
				print line.strip('\n')
				rc = 1
	return rc, error_msgs

def chkAVI(pathname):
	cmd = ['avinfo', '-q', pathname, '--list']
	process = Popen(cmd, shell=False, stdin=None, stdout=PIPE, stderr=PIPE, cwd=None)
	output = process.stdout.read()
	log.debug('AVINFO: %s' % output)
	if output == '':
		rc = 1
	else:
		rc = 0
	return rc

def chkMKV(pathname):
	NULLF = open('/dev/null', 'w')
	cmd = ['mkvinfo', pathname]
	process = Popen(cmd, shell=False, stdin=None, stdout=NULLF, stderr=NULLF, cwd=None)
	rc = process.returncode
	return rc


if __name__ == '__main__':
	from sys import argv
	from os.path import isdir, walk, exists
	from dadvision import DadVision
	from logging import DEBUG; TRACE = 5; VERBOSE = 15
	DadVision.logger.initialize(level=DEBUG)

	library = ChkVideo()
	DadVision.args = DadVision.cmdoptions.ParseArgs(argv[1:])
#	DadVision.logger.start(DadVision.args.logfile, DEBUG, timed=DadVision.args.timed)

	if len(DadVision.args.pathname) > 0:
		for pathname in DadVision.args.pathname:
			if os.path.exists(pathname):
				if isdir(pathname):
					FilesWithIssues = chkVideoDir(pathname, library.args.deep)
				else:
					rc = chkVideoFile(pathname, library.args.deep)
			else:
				log.error('Skipping: Pathname Not Found: {}'.format(pathname))

	if len(FilesWithIssues) > 0:
		for _entry in sorted(FilesWithIssues):
			log.info(_entry)
		og.info('Number Files Identified: %s' % len(FilesWithIssues))
	else:
		log.info('No errors found')
