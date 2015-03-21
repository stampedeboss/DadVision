#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Author: AJ Reynolds
Date: 01-24-2015
Purpose:
Program to cleanup the various lists and entries used from the TRAKT
website to support syncrmt and other DadVision modules.

ABOUT
Current functions:
 Remove entries from the watchlist that have been delivered.
 Repopulate the std-shows list
"""
from __future__ import division
from urllib2 import Request, urlopen, HTTPError
import logging
import re
import os
import sys
import traceback
import unicodedata

from library.trakttv.__init__ import *


__pgmname__ = 'show'
__version__ = '@version: $Rev: 462 $'

__author__ = "@author: AJ Reynolds"
__copyright__ = "@copyright: Copyright 2015, AJ Reynolds"
__status__ = "@status: Development"
__license__ = "@license: GPL"

__maintainer__ = "@organization: AJ Reynolds"
__credits__ = []

log = logging.getLogger(__pgmname__)


def slugify(value):
	"""Converts to lowercase, removes non-word characters (alphanumerics and
	underscores) and converts spaces to hyphens. Also strips leading and
	trailing whitespace.

	Borrowed from django.utils.text.slugify with some slight modifications
	"""
	if type(value) == unicode:
		value = unicodedata.normalize('NFKD',
									  value).encode('ascii',
													'ignore').decode('ascii')
	value = re.sub('[^\w\s-]', '', value).strip().lower()
	value = re.sub(r"//", '', value)
	return re.sub('[-\s]+', '-', value)


def getShow(userid=userid, authorization=authorization, show=None, rtn=dict):

	_url = 'https://api-v2launch.trakt.tv/shows/{}'.format(slugify(show))
	_list = getBase(_url, userid, authorization, rtn)

	return _list