#!/usr/bin/python

import unittest as unittest

def TestSuite():

	all_tests = unittest.TestLoader().discover('multiEpisode', pattern='*.py')
	return all_tests

if __name__ == "__main__":
	unittest.TextTestRunner().run(TestSuite())
