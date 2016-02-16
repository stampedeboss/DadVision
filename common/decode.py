#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Author: AJ Reynolds
Date: 03-19-2015
Purpose:
Routine to decode Unicode Text to String
"""
import sys
import unicodedata

__pgmname__ = 'decode'
__version__ = '$Rev: 497 $'

__author__ = "@author: AJ Reynolds"
__copyright__ = "@copyright: 2014, AJ Reynolds"
__credits__ = []
__license__ = "@license: GPL"

__maintainer__ = "AJ Reynolds"
__email__ = "@contact: stampedeboss@gmail.com"
__status__ = "Development"

__date__ = '2015-03-19'
__updated__ = '2015-03-19'


def decode(coded_text):

	if type(coded_text) is unicode:
		decoded_text = unicodedata.normalize('NFKD', coded_text).encode('ascii', 'ignore')
	else:
		decoded_text = coded_text

	decoded_text = decoded_text.replace("&amp;", "&").replace("/", "_")

	return decoded_text

if __name__ == '__main__':

	if len(sys.argv) > 1:
		coded_text = sys.argv[1]
	else:
		coded_text = u'Test Unicode String'

	print(type(decode(coded_text)), decode(coded_text))
