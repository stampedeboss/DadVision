#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Purpose:
MEDS - Nursing assistant, Maintain a Medication List for a Patients
        Upgrade environment to support the latest published version
 """
import os, sys, datetime, time, socket, string
import shlex, subprocess
import logging, logging.handlers
import tempfile

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s %(levelname)s - %(message)s")
#fh = logging.handlers.TimedRotatingFileHandler(update_log, when='midnight', interval=1, backupCount=14, encoding=None, delay=False, utc=False)
#fh.setLevel(logging.DEBUG)
#fh.setFormatter(formatter)
#logger.addHandler(fh)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)
#fh.doRollover()


cmd = ['ps waux | grep auth | grep root | grep -v grep']
temp_log = '/tmp/test.log'

#with open(temp_log, "w+") as tl:
with tempfile.TemporaryFile('w+') as tl:
    subprocess.call(cmd, stdin=None, stdout=tl, stderr=tl, shell=True)
    tl.seek(0)
    rows = tl.readlines()
    for row in rows:
        logger.info(row.rstrip("\n"))
        parms = row.split()
        for i in range(len(parms)):
            if parms[i] == '-auth':
                cmd2 = ['x11vnc', '-display', ':0', '-auth', parms[i+1]]
                subprocess.call(cmd2, stdin=None, stdout=None, stderr=None, shell=False)