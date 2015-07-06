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

from library.trakt.__init__ import *

__pgmname__ = 'user'
__version__ = '@version: $Rev: 462 $'

__author__ = "@author: AJ Reynolds"
__copyright__ = "@copyright: Copyright 2015, AJ Reynolds"
__status__ = "@status: Development"
__license__ = "@license: GPL"

__maintainer__ = "@organization: AJ Reynolds"
__credits__ = []

log = logging.getLogger(__pgmname__)


def addCollection(userid=userid, authorization=authorization, entries=None):

    _url = 'https://api-v2launch.trakt.tv/sync/collection'
    data = postBase(_url, userid=userid, authorization=authorization, entries=entries)

    return data



def getCollection(userid=userid, authorization=authorization, entrytype='shows', rtn=dict):

#	_url = 'https://api-v2launch.trakt.tv/users/{}/collection/{}?extended=full'.format(userid, entrytype)
    _url = 'https://api-v2launch.trakt.tv/sync/collection/{}?extended=full'.format(entrytype)

    _list = getBase(_url, userid, authorization, rtn)

    return _list

def getList(userid=userid, authorization=authorization, list='stdshows', rtn=dict):

    _url = 'https://api-v2launch.trakt.tv/users/{}/lists/{}/items?extended=full'.format(userid, list)
    _list = getBase(_url, userid, authorization, rtn)

    return _list

def getWatchList(userid=userid, authorization=authorization, entrytype='shows', rtn=dict):

    _url = 'https://api-v2launch.trakt.tv/users/{}/watchlist/{}?extended=full'.format(userid, entrytype)
    _list = getBase(_url, userid, authorization, rtn)

    return _list

def getWatched(userid=userid, authorization=authorization, entrytype='shows', rtn=dict):

    _url = 'https://api-v2launch.trakt.tv/users/{}/watched/{}?extended=full'.format(userid, entrytype)
    _list = getBase(_url, userid, authorization, rtn)

    return _list

def removeFromWatchlist(userid=userid, authorization=authorization, entries=None):

    _url = 'https://api-v2launch.trakt.tv/sync/watchlist/remove'
    data = postBase(_url, userid=userid, authorization=authorization, entries=entries)

    return data

def addToList(userid=userid, authorization=authorization, list='stdshows', entries=None):

    _url = 'https://api-v2launch.trakt.tv/users/{}/lists/{}/items'.format(userid, list)
    data = postBase(_url, userid=userid, authorization=authorization, entries=entries)

    return data

def removeFromList(userid=userid, authorization=authorization, list='stdshows', entries=None):

    _url = 'https://api-v2launch.trakt.tv/users/{}/lists/{}/items/remove'.format(userid, list)
    data = postBase(_url, userid=userid, authorization=authorization, entries=entries)

    return data

def removeFromHistory(userid=userid, authorization=authorization, entries=None, entrytype=None):

    _url = 'https://api-v2launch.trakt.tv/sync/history/remove'
    data = postBase(_url, userid=userid, authorization=authorization, entries=entries)

    return data

def removeFromCollection(self, userid=userid, authorization=authorization, entries=None, entrytype=None):

    _url = 'https://api-v2launch.trakt.tv/sync/collection/remove'
    data = postBase(_url, userid=userid, authorization=authorization, entries=entries)

    return data
