#!/usr/bin/python

import unittest as unittest

def TestSuite():

	all_tests = unittest.TestLoader().discover('group', pattern='*.py')
	return all_tests

if __name__ == "__main__":

	unittest.TextTestRunner().run(TestSuite())
