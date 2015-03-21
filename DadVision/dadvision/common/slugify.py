#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Author: AJ Reynolds
Date: 03-19-2015
Purpose:
Base API for TRAKT, provides common routines.
"""
import re
import unicodedata

__pgmname__ = 'slugify'
__version__ = '@version: $Rev: 500 $'

__author__ = "@author: AJ Reynolds"
__copyright__ = "@copyright: Copyright 2015, AJ Reynolds"
__status__ = "@status: Development"
__license__ = "@license: GPL"

__maintainer__ = "@organization: AJ Reynolds"
__credits__ = []


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