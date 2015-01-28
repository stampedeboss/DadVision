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

token = {'stampedeboss': {'client_id': '54d65f67401b045bc720ef109d4d05a107c0f5e28badf2f413f89f9bee514ae7',
                     'client_secret': '85f06b5b6d29265a8be4fa113bbaefb0dd58826cbfd4b85da9a709459a0cb9b1',
                     'authorization': 'Bearer 23ce6843ef4296053b117ec9e37f4dc9b124cc4ed05c50556812014cc17effa6',
                     'access_token': ''
					},
          'Alyr0923': {'client_id': '722fb8b6d3467672d4fab1aa168e523b39f6d6dc7eecd72e82f352701bb42995',
                     'client_secret': "9bf8dd42e0cf9590cdd59594b6a5401165fa383448228866a1b529b5ebd9aa66",
                     'access_token': {u'access_token': u'd8a0380a9b22f149df941b23de0915ce9272a453fd346cc702f2d9c663d6e830', u'token_type': u'bearer', u'expires_in': 7776000, u'expires_at': 1429898517.891456, u'scope': [u'public']},
                     'authorization': 'Bearer d8a0380a9b22f149df941b23de0915ce9272a453fd346cc702f2d9c663d6e830',
                     'authorization_1': 'Bearer 5bccca9768a0339959f91c7b8de96e094eac6ccadd5abb7ee5838b60cddc841a'
                    },
          'kimr9999': {'client_id': '25b1a279c9792ea1a257ba6d7f5017c245ba32de8c4e6bc7c0efbbb514e2432d',
                    'client_secret': "2fe68f2c8a796bab6bfe8cf226063d9960b9df1f6631d678d8aabfea05ce1bbe",
                    'access_token': {u'access_token': u'd69d6db6d86dcfe7bf66cd81db3b16f66efa7177b7be3871031153d6018e7605', u'token_type': u'bearer', u'expires_in': 7776000, u'expires_at': 1429898835.355948, u'scope': [u'public']},
                    'authorization': 'Bearer d69d6db6d86dcfe7bf66cd81db3b16f66efa7177b7be3871031153d6018e7605',
                    'authorization_1': 'Bearer 7fd0103aa14fe3cba2767f7fcacea7099a4b07ce65fed573fcf3344943592c8f'
                    },
          'pluto': {'client_id': "",
                    'client_secret': "",
                    'access_token': "",
                    'authorization': 'Bearer '
                    },
          'mcreynolds82': {'client_id': "409c57db13df88844a45c5072f7e5594917e8b54406f30b7dca4346053e7162c",
                    'client_secret': "c32c748bb3bd54c880950e64996bd5f7a5123fb89f071ad2467c50630896b8f6",
                    'access_token': {u'access_token': u'fb7c69bf8387638a59f3c525625062d247c330fd11e4a432ad3746691422e46f', u'token_type': u'bearer', u'expires_in': 7776000, u'expires_at': 1430189243.868178, u'scope': [u'public']},
                    'authorization': 'Bearer fb7c69bf8387638a59f3c525625062d247c330fd11e4a432ad3746691422e46f'
                    }
        }


class Shows(Library):

    def __init__(self):
        super(Shows, self).__init__()

        self._collected = []

    def getCollection(self, userid):

        headers = {
          'Content-Type': 'application/json',
          'trakt-api-version': '2',
          'trakt-api-key': token[userid]['client_id'],
          'Authorization': token[userid]['authorization']
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

    library.getCollection('Alyr0923')
