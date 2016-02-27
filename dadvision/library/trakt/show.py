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

from urllib import urlencode

import unidecode

from trakt import *

__pgmname__ = 'show'

__author__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"

__maintainer__ = __author__

__copyright__ = "Copyright 2011, AJ Reynolds"
__license__ = "GPL"

client_id = '54d65f67401b045bc720ef109d4d05a107c0f5e28badf2f413f89f9bee514ae7'

log = logging.getLogger(__pgmname__)

from slugify import Slugify

myslug = Slugify(pretranslate={"'": '_'}, translate=unidecode.unidecode, to_lower=True)


def getShow(show, rtn=dict, userid='', authorization=''):

	if type(show) in [str, unicode, dict]:
		show = myslug(show)

	_url = 'https://api-v2launch.trakt.tv/shows/{}?extended=full'.format(show)
	_list = getBase(_url, userid, authorization, rtn)

	return _list

def searchShow(show, year=None, rtn=dict, userid='', authorization=''):

	show = { 'query' : show, 'type': 'show'}
	if year: show['year'] = year

	show = urlencode(show)

	_url = 'https://api-v2launch.trakt.tv/search?{}'.format(show)
	_list = getBase(_url, userid, authorization, rtn)

	return _list


def getSeasons(trakt_id, rtn=dict, userid='', authorization=''):

	_url = 'https://api-v2launch.trakt.tv/shows/{}/seasons?extended=episodes,full'.format(trakt_id)
	_list = getBase(_url, userid, authorization, rtn)

	return _list


def getEpisode(trakt_id, season, episode,rtn=str, userid='', authorization=''):

	_url = 'https://api-v2launch.trakt.tv/shows/{}/seasons/{}/episodes/{}?extended=full'.format(trakt_id, season, episode)
	_list = getBase(_url, userid, authorization, rtn)

	return _list


