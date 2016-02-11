#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Purpose:
		Score How Well 2 items match.
"""

import sys
import logging

from fuzzywuzzy import fuzz

from common import logger


__pgmname__ = 'matching'
__version__ = '@version: $Rev: 488 $'

__author__ = "@author: AJ Reynolds"
__email__ = "@contact: stampedeboss@gmail.com"
__copyright__ = "@copyright: Copyright 2015, AJ Reynolds"
__license__ = "@license: GPL"

__maintainer__ = "@organization: AJ Reynolds"
__status__ = "@status: Development"
__credits__ = []

log = logging.getLogger(__pgmname__)


def matching(value1, value2, factor=None):
	"""

	:rtype : object
	"""

	fuzzy = []
	fuzzy.append(fuzz.ratio(value1.lower(), value2.lower()))
	fuzzy.append(fuzz.partial_ratio(value1.lower(), value2.lower()))
	fuzzy.append(fuzz.token_set_ratio(value1.lower(), value2.lower()))
	fuzzy.append(fuzz.token_sort_ratio(value1.lower(), value2.lower()))

	log.trace("=" * 50)
	log.trace('Fuzzy Compare: {} - {}'.format(value1.lower(), value2.lower()))
	log.trace("-" * 50)
	log.trace('{}: Simple Ratio'.format(fuzzy[0]))
	log.trace('{}: Partial Ratio'.format(fuzzy[1]))
	log.trace('{}: Token Set Ratio'.format(fuzzy[2]))
	log.trace('{}: Token Sort Ratio'.format(fuzzy[3]))

	if factor:      # Will return True or False
		log.trace('Return with Factor - {}: {}'.format(factor, any([fr > factor for fr in fuzzy])))
		return any([fr >= factor for fr in fuzzy])

	score = 0
	entries = 0
	for fr in fuzzy:
		score += fr
		if fr > 0: entries += 1

	if entries > 0: score = score/entries
	else: score = 0

	log.trace('Return without Factor - Score: {}'.format(score))

	return score


if __name__ == "__main__":

	from library import Library
	import os.path

	logger.initialize()

	log.trace("MAIN: -------------------------------------------------")

	library = Library()

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

	logger.start(log_file, 5)

	log.info('Test: With Factor')
	score = matching('text1', 'text2', factor=75)

	log.info('Test: Without Factor')
	score = matching('text1', 'text2')