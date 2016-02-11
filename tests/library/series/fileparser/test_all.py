#!/usr/bin/python

import unittest as unittest

import test_exceptions


#import test_group
import test_multiEpisodes
import test_singleEpisodes


suite1 = test_exceptions.TestSuite()
#suite2 = test_group.TestSuite()
suite3 = test_multiEpisodes.TestSuite()
suite4 = test_singleEpisodes.TestSuite()
alltests = unittest.TestSuite([suite1, suite3, suite4])