from daddyvision.common.fileparser import FileParser
from daddyvision.common import exceptions
from daddyvision.common import logger
from logging import INFO, WARNING, ERROR, DEBUG
import unittest
import os
import sys

import test_fileparser_exceptions
#import test_fileparser_single_episode
#import test_fileparser_multi_episode

module1 = test_fileparser_exceptions.FileParserExceptions()
#module2 = test_fileparser_single_episode.FileParserSingleEps()
#module3 = test_fileparser_multi_episode.FileParserMultiEps()

suite1 = module1.theSuite()
print suite1
#suite2 = module2.theSuite()
#suite3 = module3.theSuite()
alltests = unittest.TestSuite([suite1])
#alltests = unittest.TestSuite([suite1, suite2, suite3])