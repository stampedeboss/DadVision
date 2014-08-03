#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Purpose:
    Program to maintain subscriptions to Series and Movies

'''
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from common import Settings
from datetime import date
import logging
import operator
import os
import sys
import socket
import pickle
import zlib

__pgmname__ = 'catalog'
__version__ = '@version: $Rev: 231 $'

__author__ = "@author: AJ Reynolds"
__copyright__ = "@copyright: Copyright 2011, AJ Reynolds"
__license__ = "@license: GPL"

__maintainer__ = "@organization: AJ Reynolds"
__status__ = "@status: Development"
__credits__ = []

log = logging.getLogger(__pgmname__)

host = socket.gethostname()
if host in ['grumpy', 'tigger', 'goofy', 'eeyore', 'happy']:
    import rpyc
    conn = rpyc.connect("192.168.9.201", 32489)

STATUS, FLG_ADD, FLG_DEL, FLG_LOCAL, COLLECTION, TITLE, DATE_ADDED, SERVER, PATHNAME = range(9)
booleanSet = [STATUS, FLG_ADD, FLG_DEL, FLG_LOCAL]
readOnlySet = [COLLECTION, TITLE, DATE_ADDED, SERVER, PATHNAME]

class CatalogModel(QAbstractTableModel):

    def __init__(self, parent=None, *args):
        """ content: a list of lists
        """
        super(QAbstractTableModel, self).__init__()
        self.settings = Settings()
        self.catalogItems = []
        self.servers = set()
        self.dirty = False
        self.available_servers = self.settings.Hostnames

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.catalogItems)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 9  # len(self.catalogItems[0])

    def load(self, server, content='Series'):
        _table_entries = []
        if host in ['grumpy', 'tigger', 'goofy', 'eeyore', 'happy']:
            _table_entries = conn.root.ListItems(server, content, True)
            _table_entries = zlib.decompress(_table_entries)
            _table_entries = pickle.loads(_table_entries)
        else:
            _table_entries = generateFake(content)

        self.catalogItems = []
        for item in _table_entries:

            if item['Title'] == 'New':
                continue

            if item['Status'] == 'Incrementals':
                item ['Status'] = True
                item['Incrementals'] = True
            elif item['Status'] == 'Subscribed':
                item ['Status'] = True
                item['Incrementals'] = False
            else:
                item ['Status'] = False
                item['Incrementals'] = False

            self.catalogItems.append([item ['Status'],
                                      item ['Status'],
                                      False,
                                      item['Incrementals'],
                                      '',
                                      item['Title'],
                                      str(date.fromtimestamp(item['Date'])),
                                      '192.168.9.201',
                                      item['Path']]
                                     )

        if content == 'Series' :
            self.sort(TITLE, Qt.AscendingOrder)
        else:
            self.sort(DATE_ADDED, Qt.DescendingOrder)

        self.dirty = False
        return

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.TextAlignmentRole:
            if orientation == Qt.Horizontal:
                if section in [STATUS, FLG_ADD, FLG_DEL, FLG_LOCAL]:
                    return QVariant(int(Qt.AlignCenter | Qt.AlignVCenter))
            return QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
        if role != Qt.DisplayRole:
            return QVariant()
        if orientation == Qt.Horizontal:
            if section == STATUS:
                return QVariant("S")
            if section == FLG_ADD:
                return QVariant("A")
            if section == FLG_DEL:
                return QVariant("D")
            if section == FLG_LOCAL:
                return QVariant("L")
            if section == COLLECTION:
                return QVariant("Collection")
            if section == TITLE:
                return QVariant("Title")
            elif section == DATE_ADDED:
                return QVariant("Date")
            elif section == SERVER:
                return QVariant("Server")
            elif section == PATHNAME:
                return QVariant("Pathname")
        return QVariant(int(section + 1))

    def data(self, index, role=Qt.DisplayRole):
        if (not index.isValid() or
            not (0 <= index.row() < len(self.catalogItems))):
            return QVariant()
        item = self.catalogItems[index.row()]
        column = index.column()

        if index.column() in booleanSet and role in (Qt.CheckStateRole, Qt.DisplayRole):  # Roles: 0 Display, 10 CheckState, 2 EditRole
            if role == Qt.CheckStateRole:
                    return  QVariant(item[column])
            else:  # if role == Qt.DisplayRole:
                return QVariant(item[column])
        if index.column() in readOnlySet and role == Qt.DisplayRole:
                return QVariant(item[column])
        return QVariant()

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid(): return False

        item = self.catalogItems[index.row()]
        column = index.column()

        if role == Qt.EditRole:
            if column in [COLLECTION, DATE_ADDED, TITLE, SERVER, PATHNAME]:
                item[column] = value.toString()
                self.dirty = True
                self.dataChanged.emit(index, index)
                return True
            if column in booleanSet:
                if column == FLG_ADD:
                    if item[STATUS]:  # Already added, must use delete to remove
                        return False
                    if item[FLG_DEL]:  # Can't mark add for item marked to delete
                        return False
                    item[FLG_ADD] = not item[FLG_ADD]
                    self.dirty = True
                    self.dataChanged.emit(index, index)
                    return True
                if column == FLG_LOCAL:
                    if item[FLG_DEL]:  # Can't mark add local for item marked to delete
                        return False
                    item[FLG_LOCAL] = not item[FLG_LOCAL]
                    if item[FLG_LOCAL] and not item[FLG_ADD]:  # Must also have Add Flag
                        self.setData((self.index(index.row(), FLG_ADD)), False, 2)
                    self.dirty = True
                    self.dataChanged.emit(index, index)
                    return True
                if column == FLG_DEL:
                    if item[STATUS] and item[FLG_ADD]:
                        item[FLG_DEL] = not item[FLG_DEL]
                        self.dirty = True
                        self.dataChanged.emit(index, index)
                        return True
                    if item[FLG_ADD]:  # Can't delete requested entry, just uncheck add
                        self.setData((self.index(index.row(), FLG_ADD)), False, 2)
                        if item[FLG_LOCAL]: self.setData((self.index(index.row(), FLG_LOCAL)), False, 2)
                        return True
                    return False
                return False
        else: return False
        '''
        Constant                Value    Description
        Qt.DisplayRole           0 The key data to be rendered in the form of text. (QString)
        Qt.DecorationRole        1 The data to be rendered as a decoration in the form of an icon. (QColor, QIcon or QPixmap)
        Qt.EditRole              2 The data in a form suitable for editing in an editor. (QString)
        Qt.ToolTipRole           3 The data displayed in the item's tooltip. (QString)
        Qt.StatusTipRole         4 The data displayed in the status bar. (QString)
        Qt.WhatsThisRole         5 The data displayed for the item in "What's This?" mode. (QString)
        Qt.SizeHintRole         13 The size hint for the item that will be supplied to views. (QSize)

        Roles describing appearance and meta data (with associated types):
        Constant                Value    Description
        Qt.FontRole              6 The font used for items rendered with the default delegate. (QFont)
        Qt.TextAlignmentRole     7 The alignment of the text for items rendered with the default delegate. (Qt.AlignmentFlag)
        Qt.BackgroundRole        8 The background brush used for items rendered with the default delegate. (QBrush)
        Qt.BackgroundColorRole   8 This role is obsolete. Use BackgroundRole instead.
        Qt.ForegroundRole        9 The foreground brush (text color, typically) used for items rendered with the default delegate. (QBrush)
        Qt.TextColorRole         9 This role is obsolete. Use ForegroundRole instead.
        Qt.CheckStateRole       10 This role is used to obtain the checked state of an item. (Qt.CheckState)
        Qt.InitialSortOrderRole 14 This role is used to obtain the initial sort order of a header view section. (Qt.SortOrder). This role was introduced in Qt 4.8.
        '''

    def flags(self, index):
        if not index.isValid(): return
        if index.column() in booleanSet:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable  # Qt.ItemIsUserCheckable |
        elif index.column() in readOnlySet:
            return Qt.ItemIsEnabled
        return Qt.ItemIsEnabled
        '''
        Qt.ItemFlag
        Qt.NoItemFlags           0 It does not have any properties set.
        Qt.ItemIsSelectable      1 It can be selected.
        Qt.ItemIsEditable        2 It can be edited.
        Qt.ItemIsDragEnabled     4 It can be dragged.
        Qt.ItemIsDropEnabled     8 It can be used as a drop target.
        Qt.ItemIsUserCheckable  16 It can be checked or unchecked by the user.
        Qt.ItemIsEnabled        32 The user can interact with the item.
        Qt.ItemIsTristate       64 The item is checkable with three separate states.
        '''

    def update(self, server, content):
        _update_request = []
        for item in self.catalogItems:
            _subscribed, _add, _del, _local, _collection, _title, _date, _server, _path = item
            _title = os.path.basename(_path)

            if _subscribed and not _del: continue
            if not _add: continue

            if  _local: _type = 'Incrementals'
            else: _type = content

            if _del:
                _action = 'Delete'
            elif _add or _local:
                _action = 'Add'
            _update_request.append({'Action' : _action,
                                   'Type' : _type,
                                   'Title' : _title,
                                   'Path' : _path
                                   })

        conn.root.UpdateLinks(server, _update_request)
        return

    def sort(self, Ncol, order):
        """Sort table by given column number.
        """
        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        self.catalogItems = sorted(self.catalogItems, key=operator.itemgetter(Ncol))
        if order == Qt.DescendingOrder:
            self.catalogItems.reverse()
        self.emit(SIGNAL("layoutChanged()"))

    def loadYAML(self):
        from yaml import load, dump

        self.catalogItems = []
        _series = file(os.path.expanduser('~/.flexget/config.series'), 'r')
        _data = load(_series)

        for _quality in _data['series']:
            for _show in _data['series'][_quality]:
                if  isinstance(_show, dict):
                    _name = _show.keys()[0]
                    _settings = _show.values()[0]
                else:
                    _name = _show
                    _settings = {}
                self.catalogItems.append([True,
                                          True,
                                          False,
                                          True,
                                          _quality,
                                          _name,
                                          _quality,
                                          'localhost',
                                          _settings]
                                         )
        self.sort(TITLE, Qt.AscendingOrder)


class CheckBoxDelegate(QStyledItemDelegate):
    """
    A delegate that places a fully functioning QCheckBox in every
    cell of the column to which it's applied
    """
    def __init__(self, parent):
        QItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        '''
        Important, otherwise an editor is created if the user clicks in this cell.
        ** Need to hook up a signal to the model
        '''
        return None

    def paint(self, painter, option, index):
        '''
        Paint a checkbox without the label.
        '''
        row = index.row()
        column = index.column()

        checked = index.data().toBool()
        check_box_style_option = QStyleOptionButton()

        check_box_style_option.state |= QStyle.State_Enabled
#         if (index.flags() & Qt.ItemIsEditable) > 0:
#             check_box_style_option.state |= QStyle.State_Enabled
#         else:
#             check_box_style_option.state |= QStyle.State_ReadOnly

        if checked:
            check_box_style_option.state |= QStyle.State_On
        else:
            check_box_style_option.state |= QStyle.State_Off

        check_box_style_option.rect = self.getCheckBoxRect(option)

        check_box_style_option.state |= QStyle.State_Enabled

        QApplication.style().drawControl(QStyle.CE_CheckBox, check_box_style_option, painter)

    def sizeHint(self, view, index):
        check_box_style_option = view
        check_box_rect = QApplication.style().subElementRect(QStyle.SE_CheckBoxIndicator, check_box_style_option, None)

        height = check_box_rect.width()
        width = check_box_rect.height()

        return QSize(width, height)

    def editorEvent(self, event, model, option, index):
        '''
        Change the data in the model and the state of the checkbox
        if the user presses the left mousebutton or presses
        Key_Space or Key_Select and this cell is editable. Otherwise do nothing.
        '''
#         if not (index.flags() & Qt.ItemIsEditable) > 0:
#             return False

        # Do not change the checkbox-state
        if event.type() == QEvent.MouseButtonPress:
            return False
        if event.type() == QEvent.MouseButtonRelease or event.type() == QEvent.MouseButtonDblClick:
            if event.button() != Qt.LeftButton or not self.getCheckBoxRect(option).contains(event.pos()):
                return False
            if event.type() == QEvent.MouseButtonDblClick:
                return True
        elif event.type() == QEvent.KeyPress:
            if event.key() != Qt.Key_Space and event.key() != Qt.Key_Select:
                return False
            else:
                return False

        # Change the checkbox-state
        self.setModelData(None, model, index)
        return True

    def setModelData (self, editor, model, index):
        '''
        The user wanted to change the old state in the opposite.
        '''
        newValue = not index.data().toBool()
        model.setData(index, newValue, Qt.EditRole)

    def getCheckBoxRect(self, option):
        check_box_style_option = QStyleOptionButton()
        check_box_rect = QApplication.style().subElementRect(QStyle.SE_CheckBoxIndicator, check_box_style_option, None)
        check_box_point = QPoint (option.rect.x() +
                            option.rect.width() / 2 -
                            check_box_rect.width() / 2,
                            option.rect.y() +
                            option.rect.height() / 2 -
                            check_box_rect.height() / 2)
        return QRect(check_box_point, check_box_rect.size())

def generateFake(content):
    import random
    import time
    import datetime

    table_entries = []
    shows = []
    if content == 'Series':
        shows.append('Alphas')
        shows.append('Covert Affairs')
        shows.append('Burn Notice')
        shows.append('Royal Pains')
        shows.append('Rookie Blues')
        shows.append('Blue Bloods')
        shows.append('This is a very long Title of a TV Series')
        shows.append('MASH')
        shows.append('Gunsmoke')
        shows.append('I love Lucy')
        shows.append('Human Target')
        shows.append('Star Trek')
        shows.append('Star Trek: The Next Generation')
        shows.append('Star Trek: Deep Space Nine')
        shows.append("Grey's Anatomy")
        shows.append('Chuck')
        shows.append('Brain Games')
        shows.append('The Last Show in the List')
    else:
        shows.append('MASH')
        shows.append('Big Green, The')
        shows.append('Transformers')
        shows.append('Transformers: The Dark Side of the Moon')
        shows.append('Top Gun')
        shows.append('Risky Business')
        shows.append('Days of Thunder')

    today = datetime.date.today()
    for i in range(len(shows)):
        table_item = {}
        random_int = random.randint(0, 365)
        show_date = today - datetime.timedelta(random_int)
        show_epoch = time.mktime(show_date.timetuple())
        if i % 2 == 0: table_item['Status'] = 'Subscribed'
        else: table_item['Status'] = ''
        table_item['Title'] = shows[i]
        table_item['Date'] = show_epoch
        table_item['Path'] = '/srv/DadVision/{}/{}'.format(content, shows[i])
        table_entries.append(table_item)
    return table_entries
