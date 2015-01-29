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
from urllib2 import Request, urlopen
import logging
import json
import os
import sys

from library import Library
from common import logger
from library.series import Series


__pgmname__ = 'getCollection'
__version__ = '@version: $Rev: 462 $'

__author__ = "@author: AJ Reynolds"
__copyright__ = "@copyright: Copyright 2015, AJ Reynolds"
__status__ = "@status: Development"
__license__ = "@license: GPL"

__maintainer__ = "@organization: AJ Reynolds"
__credits__ = []

log = logging.getLogger(__pgmname__)


def use_library_logging(func):

    def wrapper(self, *args, **kw):
        # Set the library name in the logger
        logger.set_library(self.args.hostname.upper())
        try:
            return func(self, *args, **kw)
        finally:
            logger.set_library('')

    return wrapper

client_id = '54d65f67401b045bc720ef109d4d05a107c0f5e28badf2f413f89f9bee514ae7'
client_secret = '85f06b5b6d29265a8be4fa113bbaefb0dd58826cbfd4b85da9a709459a0cb9b1'


class Shows(Library):

    def __init__(self):
        super(Shows, self).__init__()


    def getCollection(self, userid, authorization):

        self._collected = []

        headers = {
          'Content-Type': 'application/json',
          'trakt-api-version': '2',
          'trakt-api-key': client_id,
          'Authorization': authorization
        }

        request = Request('https://api.trakt.tv/users/{}/collection/shows'.format(userid), headers=headers)
        response_body = urlopen(request).read()
        data = json.loads(response_body.decode('UTF-8', 'ignore'))

        for show in data:
            self._collected.append(Series(**show))

        return self._collected


if __name__ == '__main__':

    logger.initialize()
    library = Shows()

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

    logger.start(log_file, log_level, timed=True)

    for entry in library.settings.Hostnames:
        print entry
        library.settings.ReloadHostConfig(entry)
        print library.settings.TraktUserID, library.settings.TraktAuthorization
        collection = library.getCollection(library.settings.TraktUserID, library.settings.TraktAuthorization)
        print collection
