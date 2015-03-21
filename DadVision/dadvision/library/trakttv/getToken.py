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
from requests_oauthlib import OAuth2Session

client_id = "54d65f67401b045bc720ef109d4d05a107c0f5e28badf2f413f89f9bee514ae7"
client_secret = "85f06b5b6d29265a8be4fa113bbaefb0dd58826cbfd4b85da9a709459a0cb9b1"
redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
#username = 'stampedeboss'
#username = 'Alyr0923'
#username = 'kimr9999'
#username = 'mcreynold82'
#username = 'phsdoc55'

# Get the authorization verifier code from the callback url
username = raw_input('Please enter trakt userid:  ')

authorization_base_url = 'https://api.trakt.tv/oauth/authorize'
token_url = 'https://api.trakt.tv/oauth/token'
headers = {'Content-Type': 'application/json'}

# OAuth endpoints given in the API documentation
oauth = OAuth2Session(client_id, redirect_uri=redirect_uri, state=None)

# Redirect user to Trakt for authorization
authorization_url, state = oauth.authorization_url(authorization_base_url, username=username)
print 'Please go here and authorize:  ', authorization_url
print ' '

# Get the authorization verifier code from the callback url
redirect_response = raw_input('Paste the Code returned here:  ')

# Fetch the access token
oauth.fetch_token(token_url,
                  client_secret=client_secret,
                  code=redirect_response)

print ' '
print oauth.token