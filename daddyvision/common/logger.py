#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
"""
import logging
import logging.handlers
from logging import INFO, DEBUG, WARNING, ERROR, CRITICAL
import re
import sys
import threading

# A level more detailed than DEBUG
TRACE = 5
# A level more detailed than INFO
VERBOSE = 15

LogDir = '/srv/log'


class DaddyVisionLogger(logging.Logger):
    """Custom logger that adds library and execution info to log records."""
    local = threading.local()

    def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None):
        extra = {'library': getattr(DaddyVisionLogger.local, 'library', u''),
                 'execution': getattr(DaddyVisionLogger.local, 'execution', '')}
        return logging.Logger.makeRecord(self, name, level, fn, lno, msg, args, exc_info, func, extra)

    def trace(self, msg, *args, **kwargs):
        """Log at TRACE level (more detailed than DEBUG)."""
        self.log(TRACE, msg, *args, **kwargs)

    def verbose(self, msg, *args, **kwargs):
        """Log at VERBOSE level (displayed when FlexGet is run interactively.)"""
        self.log(VERBOSE, msg, *args, **kwargs)

    # backwards compatibility
    debugall = trace


class DaddyVisionFormatter(logging.Formatter):
    """Custom formatter that can handle both regular log records and those created by DaddyVisionLogger"""
    plain_fmt = '%(asctime)-15s %(levelname)-8s %(name)-22s %(message)s'
    daddyvision_fmt = '%(asctime)-15s %(levelname)-8s %(name)-12s %(library)-9s %(message)s'

    def __init__(self):
        logging.Formatter.__init__(self, self.plain_fmt, '%Y-%m-%d %H:%M')

    def format(self, record):
        extra_list = ['rename', 'distribute']
#        print getattr(record, 'name')
#        if hasattr(record, 'name'):
        if getattr(record, 'name') in extra_list:
            self._fmt = self.daddyvision_fmt
        else:
            self._fmt = self.plain_fmt
        return logging.Formatter.format(self, record)


def set_execution(execution):
    DaddyVisionLogger.local.execution = execution


def set_library(library):
    DaddyVisionLogger.local.library = library


class PrivacyFilter(logging.Filter):
    """Edits log messages and <hides> obviously private information."""

    def __init__(self):
        self.replaces = []

        def hide(name):
            s = '([?&]%s=)\w+' % name
            p = re.compile(s)
            self.replaces.append(p)

        for param in ['passwd', 'password', 'pw', 'pass', 'passkey',
            'key', 'apikey', 'user', 'username', 'uname', 'login', 'id']:
            hide(param)

    def filter(self, record):
        if not isinstance(record.msg, basestring):
            return False
        for p in self.replaces:
            record.msg = p.sub(r'\g<1><hidden>', record.msg)
            record.msg = record.msg
        return False

_logging_configured = False
_mem_handler = None
_logging_started = False


def initialize(unit_test=False, level=TRACE):
    """Prepare logging.
    """
    global _logging_configured, _mem_handler

    if _logging_configured:
        return

    logging.addLevelName(TRACE, 'TRACE')
    logging.addLevelName(VERBOSE, 'VERBOSE')
    _logging_configured = True

    # root logger
    log = logging.getLogger()
    formatter = DaddyVisionFormatter()

    _mem_handler = logging.handlers.MemoryHandler(1000 * 1000, 100)
    _mem_handler.setFormatter(formatter)
    log.addHandler(_mem_handler)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    log.addHandler(console)

    if unit_test:
        log.setLevel(level)
        return
    #
    # Process commandline options, unfortunately we need to do it before optparse is available
    #

    # turn on debug level
    if '--trace' or TRACE in sys.argv:
        log.setLevel(TRACE)
    elif '--debug-trace' in sys.argv:
        log.setLevel(TRACE)
    elif '--debug' or 'DEBUG' in sys.argv:
        log.setLevel(logging.DEBUG)
    elif '--verbose' or '-v' or VERBOSE in sys.argv:
        log.setLevel(VERBOSE)
    elif '--quiet' or '-q' or 'WARNING' in sys.argv:
        log.setLevel(logging.WARNING)
    elif '--errors' or '-e' or 'ERROR' in sys.argv:
        log.setLevel(logging.ERROR)
    elif '--critical' or 'CRITICAL' in sys.argv:
        log.setLevel(logging.CRITICAL)
    else:
        log.setLevel(logging.INFO)


def start(filename='daddyvision.log', level=logging.INFO, timed=False):
    """After initialization, start file logging.
    """
    global _logging_started

    assert _logging_configured
    if _logging_started:
        return

    if timed:
        handler = logging.handlers.TimedRotatingFileHandler(filename, when='midnight', backupCount=9)
    else:
        handler = logging.handlers.RotatingFileHandler(filename, maxBytes=1000 * 1024, backupCount=9)
        handler.doRollover()

    handler.setFormatter(_mem_handler.formatter)

    _mem_handler.setTarget(handler)

    # root logger
    log = logging.getLogger()
    log.removeHandler(_mem_handler)
    log.addHandler(handler)
    log.addFilter(PrivacyFilter())
    log.setLevel(level)

    # flush what we have stored from the plugin initialization
    _mem_handler.flush()
    _logging_started = True

def flush_logging_to_console():
    """Flushes memory logger to console"""
    console = logging.StreamHandler()
    console.setFormatter(_mem_handler.formatter)
    log = logging.getLogger()
    log.addHandler(console)
    if len(_mem_handler.buffer) > 0:
        for record in _mem_handler.buffer:
            console.handle(record)
    _mem_handler.flush()

# Set our custom logger class as default
logging.setLoggerClass(DaddyVisionLogger)
