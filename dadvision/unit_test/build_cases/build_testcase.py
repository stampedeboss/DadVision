#!/usr/bin/env python
'''
Purpose:
    Read list of test case parameters and output a UnitTest module

Created on Dec 4, 2011
@author: AJ Reynolds

'''

import os
import sys
import tempfile

__version__ = '$Rev$'
__pgmname__ = 'build_testcase'

Line1 = '    def test_FileParser_single_case_{:0>3}(self):\n'
Line2 = '        KnownValues.File_SxxExx["FileName"] ='
Line3 = '        self.assertEqual(self.parser.GetFileDetails(KnownValues.File_SxxExx["FileName"]), KnownValues.File_SxxExx)\n\n'

Part2 = ''

EndLine1='suite = unittest.TestLoader().loadTestsFromTestCase(TestSequenceFunctions)\n'
EndLine2='unittest.TextTestRunner(verbosity=2).run(suite)\n'


test_case_num = 0

if (len(sys.argv) > 1):
    with open('/home/aj/workspace/VideoLibrary/daddyvision/unit_test/test_built.py', 'w') as w:
        if os.path.exists(sys.argv[1]):
            with open(sys.argv[1], "r") as f:
                for line in f.readlines():
                    if line[0:1] == '#':
                        w.write(line)
                    else:
                        test_case_num += 1
                        w.write(Line1.format(test_case_num))
                        w.write('{} "{} Case {:03}.ext"\n'.format(Line2, line.strip('\n'), test_case_num))
                        w.write(Line3)
                        w.write('')
                w.write(EndLine1)
                w.write(EndLine2)
        else:
            print "File Not Found: %s" % sys.argv
            sys.exit(1)

    f.close()
    w.close()