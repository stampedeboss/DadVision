#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""

Purpose:
		Score How Well 2 items match.
"""

import logging
import sys

from fuzzywuzzy import fuzz

__pgmname__ = 'matching'

__author__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"

__maintainer__ = __author__

__copyright__ = "Copyright 2011, AJ Reynolds"
__license__ = "GPL"

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


if __name__ == "__main__":

	from dadvision import DadVision
	DadVision.args = DadVision.cmdoptions.ParseArgs(sys.argv[1:])
#	DadVision.logger.start(DadVision.args.logfile, DadVision.args.loglevel, timed=True)

	log.info('Test: With Factor')
	score = matching('text1', 'text2', factor=75)

	log.info('Test: Without Factor')
	score = matching('text1', 'text2')