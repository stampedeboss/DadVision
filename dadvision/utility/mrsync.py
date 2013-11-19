#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Purpose:
        Invoke rsync with Standard Options

'''
from argparse import ArgumentParser
from daddyvision.common.options import OptionParser, OptionGroup
from subprocess import Popen, call as Call,  check_call, CalledProcessError
import os
import sys

__pgmname__ = 'mrsync'
__version__ = '$Rev$'

__author__ = "AJ Reynolds"
__copyright__ = "Copyright 2011, AJ Reynolds"
__credits__ = []
__license__ = "GPL"

__maintainer__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"
__status__ = "Development"

class rsync_cmd(object):

    def __init__(self, args):
        self.args = args
        return

    def Run_rsync(self):

        cmd = ['rsync', '-auvhL',
               '--progress',
               '--partial-dir=.rsync-partial',
               '--exclude=lost+found'
               ]
#        cmdLineOptions =
        cmd.extend(self._add_runtime_options())

        try:
            print
            print ' '.join(cmd)
            print
            process = check_call(cmd, shell=False, stdin=None, stdout=None, stderr=None)
        except CalledProcessError, exc:
            print "Command %s returned with RC=%d" % (cmd, exc.returncode)
            sys.exit(1)

    def _add_runtime_options(self):

        CmdLineArgs = []

        if self.args.dryrun:
            CmdLineArgs.append('-n')

        if self.args.remove:
            CmdLineArgs.append('--remove-source-files')

        if self.args.stats:
            CmdLineArgs.append('--stats')

        if self.args.ignoreexisting:
            CmdLineArgs.append('--ignore-existing')

        if self.args.chksum:
            CmdLineArgs.append('--checksum')

        if self.args.delete:
            CmdLineArgs.append('--delete')

        if self.args.xclude:
            CmdLineArgs.append('--exclude=*{}*'.format(self.args.xclude))

        if self.args.novideo:
            CmdLineArgs.append('--exclude=*.avi')
            CmdLineArgs.append('--exclude=*.mkv')
            CmdLineArgs.append('--exclude=*.mp4')
            CmdLineArgs.append('--exclude=*.iso')
            CmdLineArgs.append('--exclude=*.mpg')
            CmdLineArgs.append('--exclude=*.vob')
            CmdLineArgs.append('--exclude=*.ifo')
            CmdLineArgs.append('--exclude=*.bup')
            CmdLineArgs.append('--exclude=*.VOB')
            CmdLineArgs.append('--exclude=*.IFO')
            CmdLineArgs.append('--exclude=*.BUP')
            CmdLineArgs.append('--exclude=core')

        CmdLineArgs.append(args.source.replace("\\", ""))
        CmdLineArgs.append(args.target.replace("\\", ""))

        return CmdLineArgs

class ArgParser(ArgumentParser):

    def __init__(self, **kwargs):

        ArgumentParser.__init__(self, **kwargs)

        self.version = __version__

if __name__ == '__main__':

    parser = ArgumentParser(description='Invoke rsync with standard options.')
    #parser = ArgumentParser(prog='mrsync', add_help=False)
    parser.add_argument('-V', '--version', action='version',
        help='Print version and exit.')

    group = parser.add_argument_group("Modifers")
    group.add_argument("--checksum", dest="chksum",
        action="store_true", default=False,
        help="Use Checksum not Date and Time")
    group.add_argument("--delete", dest="delete",
        action="store_true", default=False,
        help="Delete any files on rmt that do not exist on local")
    group.add_argument("--ignore-existing", dest="ignoreexisting",
        action="store_true", default=False,
        help="Ignore Existing files on receiver")
    group.add_argument("--no-video", dest="novideo",
        action="store_true", default=False,
        help="Suppress Video Files, Only Move Support Files/Directories")
    group.add_argument("-n", "--dry-run", dest="dryrun",
        action="store_true", default=False,
        help="Don't Run Link Create Commands")
    group.add_argument("-r", "--remove-source-files", dest="remove",
        action="store_true", default=False,
        help="Delete Source Files once transfered")
    group.add_argument("--stats", dest="stats",
        action="store_true", default=False,
        help="Display additional transfer stats")
    group.add_argument("-x", "--exclude", dest="xclude",
        action="store", default="",
        help="Exclude files/directories")
    parser.add_argument(dest='source')
    parser.add_argument(dest='target')

    args = parser.parse_args()
    sync = rsync_cmd(args)
    sync.Run_rsync()