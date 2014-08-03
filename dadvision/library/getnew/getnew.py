#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Purpose:
    Program to maintain subscriptions to Series and Movies

'''
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from common import Common
from common import logger
from getnew_ui import Ui_MainWindow
import catalog
import logging
import socket
import os
import sys

__pgmname__ = 'getnew'
__version__ = '@version: $Rev: 231 $'

__author__ = "@author: AJ Reynolds"
__copyright__ = "@copyright: Copyright 2011, AJ Reynolds"
__license__ = "@license: GPL"

__maintainer__ = "@organization: AJ Reynolds"
__status__ = "@status: Development"
__credits__ = []

STATUS, FLG_ADD, FLG_DEL, FLG_LOCAL, COLLECTION, TITLE, DATE_ADDED, SERVER, PATHNAME = range(9)
log = logging.getLogger(__pgmname__)


class StartQT4(QtGui.QMainWindow):
    def __init__(self, parent=None):

        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.current_content = 'Series'

        self.ui.available_content.setItemDelegateForColumn(1, catalog.CheckBoxDelegate(self))
        self.ui.available_content.setItemDelegateForColumn(2, catalog.CheckBoxDelegate(self))
        self.ui.available_content.setItemDelegateForColumn(3, catalog.CheckBoxDelegate(self))

        self.ui.series.setChecked(True)

        host = socket.gethostname()
        if host in ['tigger', 'goofy', 'eeyore']:
            self.ui.server_name.addItem(host)
            self.current_server = host
        else:
            self.ui.server_name.addItem('-- Select --')
            for name in common.settings.Hostnames:
                self.ui.server_name.addItem(name)
            self.current_server = '-- Select --'

        self.model = catalog.CatalogModel()
        if self.current_server:
            self.model.load(self.current_server, self.current_content)

        self.proxy = QtGui.QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.ui.available_content.setModel(self.proxy)

        self.ui.user.currentIndexChanged.connect(self.chgServer)
        self.ui.server_name.currentIndexChanged.connect(self.chgServer)
        self.ui.series.clicked.connect(self.loadSeries)
        self.ui.movies.clicked.connect(self.loadMovies)
        self.ui.cancel.clicked.connect(self.loadModel)
        self.proxy.dataChanged.connect(self.dirtyTable)
        self.ui.update.clicked.connect(self.update)
        self.ui.filter.textChanged.connect(self.proxy.setFilterRegExp)

        self.proxy.setFilterKeyColumn(TITLE)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.ui.available_content.setSortingEnabled(True)

        self.resizeColumns()
        self.cleanTable()

    def resizeColumns(self):
        for column in range(self.model.columnCount()):
            if self.current_server == '-- Select --':
                self.ui.available_content.setEnabled(False)
            else: 
                self.ui.available_content.setEnabled(True)

            if column in [FLG_LOCAL, COLLECTION, STATUS, SERVER, PATHNAME]:
                self.ui.available_content.setColumnHidden(column, True)
            else: self.ui.available_content.setColumnHidden(column, False)

        self.ui.available_content.resizeColumnsToContents()

    def loadModel(self):
        self.model.load(self.current_server, self.current_content)
        self.resizeColumns()
        self.cleanTable()

    def chgServer(self):
        server = str(self.ui.server_name.currentText())
        if self.current_server == server: return
        self.current_server = server
        self.loadModel()

    def loadSeries(self):
        if self.current_content == 'Series': return
        self.current_content = 'Series'
        self.loadModel()

    def loadMovies(self):
        if self.current_content == 'Movies': return
        self.current_content = 'Movies'
        self.loadModel()

    def update(self):
        self.model.update(self.current_server, self.current_content)
        self.loadModel()

    def cleanTable(self):
        if not self.model.dirty:
            self.ui.close.setEnabled(True)
            self.ui.cancel.setEnabled(False)
            self.ui.update.setEnabled(False)
            self.ui.close.setVisible(True)
            self.ui.cancel.setVisible(False)
            self.ui.update.setVisible(False)

    def dirtyTable(self):
        if self.model.dirty:
            self.ui.close.setEnabled(False)
            self.ui.cancel.setEnabled(True)
            self.ui.update.setEnabled(True)
            self.ui.close.setVisible(False)
            self.ui.cancel.setVisible(True)
            self.ui.update.setVisible(True)

if __name__ == "__main__":
    logger.initialize()
    common = Common()

    Common.args = common.options.parser.parse_args(sys.argv[1:])
    log.debug("Parsed command line: {!s}".format(common.args))

    log_level = logging.getLevelName(common.args.loglevel.upper())

    if common.args.logfile == 'daddyvision.log':
        log_file = '{}.log'.format(__pgmname__)
    else:
        log_file = os.path.expanduser(common.args.logfile)

    # If an absolute path is not specified, use the default directory.
    if not os.path.isabs(log_file):
        log_file = os.path.join(logger.LogDir, log_file)

    logger.start(log_file, log_level, timed=True)

    app = QtGui.QApplication(sys.argv)
    myapp = StartQT4()
    myapp.show()
    sys.exit(app.exec_())
