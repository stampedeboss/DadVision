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
import os
import json

from requests_oauthlib import OAuth2Session


#: The Trakt.tv OAuth Client ID for your OAuth Application
CLIENT_ID = "54d65f67401b045bc720ef109d4d05a107c0f5e28badf2f413f89f9bee514ae7"
#: The Trakt.tv OAuth Client Secret for your OAuth Application
CLIENT_SECRET = "85f06b5b6d29265a8be4fa113bbaefb0dd58826cbfd4b85da9a709459a0cb9b1"

redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
api_key = None

#: The url for the Trakt API. Can be modified to run against different
#: Trakt.tv environments
BASE_URL = 'https://api.trakt.tv/'
BASE_AUTHORIZATION_URL = '{}oauth/authorize'.format(BASE_URL)
TOKEN_URL = '{}oauth/token'.format(BASE_URL)

#: The OAuth2 Redirect URI for your OAuth Application
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'

#: Default request HEADERS
HEADERS = {'Content-Type': 'application/json', 'trakt-api-version': '2'}

# Get the users TRAKT userid
USERNAME = raw_input('Please enter trakt userid:  ')

#: Default path for where to store your trakt.tv API authentication information
CONFIG_PATH = os.path.join(os.path.expanduser('~'),'{}.pytrakt.json'.format(USERNAME))

# OAuth endpoints given in the API documentation
oauth = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, state=None)

# Redirect user to Trakt for authorization
authorization_url, state = oauth.authorization_url(BASE_AUTHORIZATION_URL, username=USERNAME)
print 'Please go here and authorize:  ', authorization_url
print ' '

# Get the authorization verifier code from the callback url
redirect_response = raw_input('Paste the Code returned here:  ')

# Fetch the access token
oauth.fetch_token(TOKEN_URL,
                  client_secret=CLIENT_SECRET,
                  code=redirect_response)

api_key = oauth.token['access_token']

data = {'CLIENT_ID': CLIENT_ID, 'CLIENT_SECRET': CLIENT_SECRET,
        'api_key': api_key}
with open(CONFIG_PATH, 'w') as config_file:
    json.dump(data, config_file)

print ' '
print oauth.token['access_token']
print ' '
print oauth.token
