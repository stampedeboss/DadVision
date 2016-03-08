#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Author: AJ Reynolds
Date: 07-19-2014
Purpose:
Program to cleanup the various lists and entries used from the TRAKT
website to support syncrmt and other DadVision modules.

ABOUT
Current functions:
 Remove entries from the watchlist that have been delivered.
 Repopulate the std-shows list
"""
from __future__ import division

import json
import logging
import os
import sys
from urllib2 import Request, urlopen, HTTPError

from configobj import ConfigObj

import logger
from dadvision.library import Library

__pgmname__ = 'getToken'

__author__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"

__maintainer__ = __author__

__copyright__ = "Copyright 2011, AJ Reynolds"
__license__ = "GPL"

log = logging.getLogger(__pgmname__)

class getToken(Library):

    def __init__(self):
        log.trace('__init__ method: Started')

        super(getToken, self).__init__()
        trakt_auth_group = self.options.parser.add_argument_group("Profiles", description=None)
        trakt_auth_group.add_argument("-y", "--grumpy", dest="HostName",
            action="append_const", const="grumpy",
            help="Entires for Grumpy")
        trakt_auth_group.add_argument("-t", "--tigger", dest="HostName",
            action="append_const", const="tigger",
            help="Entires for Tigger")
        trakt_auth_group.add_argument("-g", "--goofy", dest="HostName",
            action="append_const", const="goofy",
            help="Entries for Goofy")
        trakt_auth_group.add_argument("-p", "--pooh", dest="HostName",
            action="append_const", const="pooh",
            help="Entries for Eeore")
        trakt_auth_group.add_argument("-l", "--pluto", dest="HostName",
            action="append_const", const="pluto",
            help="Entries for Pluto")

        trakt_options_group = self.options.parser.add_argument_group("Options", description=None)
        trakt_auth_group.add_argument("-r", "--rt", "--refresh-token", dest="use_refresh_key",
            action="store_const", const=True, default=False,
            help="Use Refresh Key if available, if not start New")

        #PIN Based
        self.PIN_URL = 'https://MyTrakt.tv/pin/1617'
        self.GET_TOKEN_URL = 'https://api-v2launch.MyTrakt.tv/oauth/token'
        self.config_file = os.path.join(os.sep,
                                       "usr",
                                       "local",
                                       "etc",
                                       "dadvision",
                                       'settings.cfg')


    def ProcessRequest(self):

        log.trace('ProcessRequest: Started')

        if not self.args.HostName:
            log.error('No Token Requested, Stopping')
            sys.exit(99)

        self.client_id = self.settings.TraktAPIKey
        self.client_secret = self.settings.TraktClientSecret

        for hostname in self.args.HostName:
            config = ConfigObj(self.config_file, unrepr=True, interpolation=False)
            hostConfig = config[hostname]
            TraktUserID = hostConfig['TraktUserID']
            try:
                if not self.args.use_refresh_key:
                    raise
                else:
                    TraktToken = hostConfig['TraktToken']
                    redirect_response = TraktToken['refresh_token']
            except:
                print 'Please go here and authorize:  ', self.PIN_URL
                redirect_response = raw_input('Paste the Code returned here:  ')

            _getToken = {"code": redirect_response,
                       "client_id": self.client_id,
                       "client_secret": self.client_secret,
                       "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
                       "grant_type": "authorization_code"}

            json_data = json.dumps(_getToken)
            clen = len(json_data)

            headers = {
                'Content-Type': 'application/json',
                'MyTrakt-api-version': '2',
                'Content-Length': clen
            }

            request = Request(self.GET_TOKEN_URL, data=json_data, headers=headers)
            try:
                response_body = urlopen(request).read()
            except HTTPError, e:
                log.error(e)
                return e

            data = json.loads(response_body.decode('UTF-8', 'ignore'))
            hostConfig['TraktToken'] = data
            config.write()



if __name__ == "__main__":

    logger.initialize()
    library = getToken()

    library.args = library.options.parser.parse_args(sys.argv[1:])
    log.debug("Parsed command line: {!s}".format(library.args))

    log_level = logging.getLevelName(library.args.loglevel.upper())

    if library.args.logfile == 'daddyvision.log':
        log_file = '{}.log'.format(__pgmname__)
    else:
        log_file = os.path.expanduser(library.args.logfile)

    # If an absolute path is not specified, use the default directory.
    if not os.path.isabs(log_file):
        logger.LogDir = os.path.join(logger.LogDir, 'MyTrakt')
        log_file = os.path.join(logger.LogDir, log_file)

    library.args.logfile = log_file

    logger.start(log_file, log_level, timed=False)

    library.ProcessRequest()
