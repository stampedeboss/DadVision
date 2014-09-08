#!/usr/bin/python

import unittest as unittest

if __name__ == "__main__":
#	all_tests1 = unittest.TestLoader().discover('group', pattern='*.py')
#	all_tests2 = unittest.TestLoader().discover('misc', pattern='*.py')
	all_tests = unittest.TestLoader().discover('single_episodes', pattern='*.py')

#	all_tests = all_tests1
#	all_tests._tests.extend(all_tests2._tests)
#	all_tests._tests.extend(all_tests3._tests)
	unittest.TextTestRunner().run(all_tests)
