#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Purpose:
    Program to maintain subscriptions to Series and Movies

'''
from daddyvision.common import logger
from daddyvision.common.exceptions import ConfigValueError
from daddyvision.common.options import OptionParser, OptionGroup
from datetime import date
import rpyc
import logging
import gtk
import os
import sys
import socket
import pickle
import zlib

__pgmname__ = 'getnew'
__version__ = '$Rev$'

__author__ = "AJ Reynolds"
__copyright__ = "Copyright 2011, AJ Reynolds"
__credits__ = []
__license__ = "GPL"

__maintainer__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"
__status__ = "Development"

TRACE = 5
VERBOSE = 15

log = logging.getLogger(__pgmname__)
logger.initialize()

host        = socket.gethostname()

conn = rpyc.connect("192.168.9.201", 32489)

class Main_Window():
    def __init__(self):

        self.PgmDir = os.path.dirname(__file__)
        self.Incremental = 'Incrementals'

        self.user = ''
        self.content = ''
        self.table_entries = []
        self.msg_id = []

        builder = gtk.Builder()
        builder.add_from_file(os.path.join(self.PgmDir, '%s.glade' % (__pgmname__)))
        events = {"on_main_window_destroy" : self.bt_quit_clicked,
                  "on_cb_all_toggle_toggled" : self.on_cb_all_toggle_toggled,
                  "on_cb_new_toggle_toggled" : self.on_cb_new_toggle_toggled,
                  "delete_toggle_toggled" : self.on_cb_delete_toggle_toggled,
                  "on_rb_aly_toggled" : self.on_rb_aly_toggled,
                  "on_rb_ben_toggled" : self.on_rb_ben_toggled,
                  "on_rb_kim_toggled" : self.on_rb_kim_toggled,
                  "on_rb_michelle_toggled" : self.on_rb_michelle_toggled,
                  "on_rb_daniel_toggled" : self.on_rb_daniel_toggled,
                  "on_rb_series_toggled" : self.on_rb_series_toggled,
                  "on_rb_movies_toggled" : self.on_rb_movies_toggled,
                  "on_bt_save_clicked" : self.bt_save_clicked,
                  "on_bt_quit_clicked" : self.bt_quit_clicked,
                  "on_bt_cancel_clicked" : self.bt_cancel_clicked,
                  "on_treeview_start_interactive_search" : self.on_treeview_start_interactive_search
                  }

        builder.connect_signals(events)

        self.wMain = builder.get_object("main_window")
        self.rb_aly = builder.get_object("rb_aly")
        self.rb_ben = builder.get_object("rb_ben")
        self.rb_kim = builder.get_object("rb_kim")
        self.rb_michelle = builder.get_object("rb_michelle")
        self.rb_daniel = builder.get_object("rb_michelle")
        self.rb_default_user = builder.get_object("rb_default_user")
        self.rb_series = builder.get_object("rb_series")
        self.rb_movies = builder.get_object("rb_movies")
        self.rb_default_content = builder.get_object("rb_default_content")
        self.bt_quit = builder.get_object("bt_quit")
        self.bt_cancel = builder.get_object("bt_cancel")
        self.bt_save = builder.get_object("bt_save")
        self.newcell = builder.get_object("newcell")
        self.status_bar = builder.get_object("statusbar")

        #Initialize our Treeview
        self.treeview=builder.get_object("treeview")
        self.treeview_model=builder.get_object("datastore")
        self.treeselection = self.treeview.get_selection()
        self.treeselection.set_mode(gtk.SELECTION_MULTIPLE)
        mode = self.treeselection.get_mode()

        self.rb_default_content.set_active(True)
        self.unlock_user_controls()

        self.treeview.set_search_column(4)
        self.wMain.show()
        gtk.main()

    def unlock_user_controls(self):

        if host == 'tigger':
            self.user = 'aly'
            self.rb_aly.set_active(True)
            self.rb_aly.set_sensitive(True)
            self.rb_ben.set_sensitive(False)
            self.rb_kim.set_sensitive(False)
            self.rb_michelle.set_sensitive(False)
            self.rb_daniel.set_sensitive(False)
        elif host == 'pluto':
            self.user = 'ben'
            self.rb_ben.set_active(True)
            self.rb_aly.set_sensitive(False)
            self.rb_ben.set_sensitive(True)
            self.rb_kim.set_sensitive(False)
            self.rb_michelle.set_sensitive(False)
            self.rb_daniel.set_sensitive(False)
        elif host == 'goofy':
            self.user = 'kim'
            self.rb_kim.set_active(True)
            self.rb_aly.set_sensitive(False)
            self.rb_ben.set_sensitive(False)
            self.rb_kim.set_sensitive(True)
            self.rb_michelle.set_sensitive(False)
            self.rb_daniel.set_sensitive(False)
        elif host == 'eeyore':
            self.user = 'daniel'
            self.rb_michelle.set_active(True)
            self.rb_aly.set_sensitive(False)
            self.rb_ben.set_sensitive(False)
            self.rb_kim.set_sensitive(False)
            self.rb_michelle.set_sensitive(True)
            self.rb_daniel.set_sensitive(True)
        else:
            if self.user == 'aly':
                self.rb_aly.set_active(True)
            elif self.user == 'ben':
                self.rb_ben.set_active(True)
            elif self.user == 'kim':
                self.rb_kim.set_active(True)
            elif self.user == 'michelle':
                self.rb_michelle.set_active(True)
            elif self.user == 'daniel':
                self.rb_daniel.set_active(True)
            else:
                self.rb_default_user.set_active(True)

            self.rb_aly.set_sensitive(True)
            self.rb_ben.set_sensitive(True)
            self.rb_kim.set_sensitive(True)
            self.rb_michelle.set_sensitive(True)
            self.rb_daniel.set_sensitive(True)

        self.rb_series.set_sensitive(True)
        self.rb_movies.set_sensitive(True)

        self.bt_quit.set_sensitive(True)
        self.bt_quit.set_visible(True)
        self.bt_cancel.set_sensitive(False)
        self.bt_cancel.set_visible(False)
        self.bt_save.set_sensitive(False)
        self.bt_save.set_visible(False)

        return

    def lock_user_controls(self):

        self.bt_quit.set_sensitive(False)
        self.bt_quit.set_visible(False)
        self.bt_cancel.set_sensitive(True)
        self.bt_cancel.set_visible(True)
        self.bt_save.set_sensitive(True)
        self.bt_save.set_visible(True)

        self.rb_aly.set_sensitive(False)
        self.rb_ben.set_sensitive(False)
        self.rb_kim.set_sensitive(False)
        self.rb_michelle.set_sensitive(False)
        self.rb_daniel.set_sensitive(False)
        self.rb_series.set_sensitive(False)
        self.rb_movies.set_sensitive(False)

        return

    def load_window(self):

        if self.content == 'Series':
            self.newcell.set_visible(True)
        elif self.content == 'Movies':
            self.newcell.set_visible(False)
        else:
            return

        if not self.user:
            return

        self.unlock_user_controls()

        self.treeview_model.clear()

        for entry in self.table_entries:
            self.insert_row(self.treeview_model,
                            entry['Status'] == 'Subscribed',
                            entry['Status'] == self.Incremental,
                            entry['Title'],
                            date.fromtimestamp(entry['Date']),
                            entry['Path']
                            )

        if self.content == 'Series':
            self.treeview_model.set_sort_column_id(4,gtk.SORT_ASCENDING)
        else:
            self.treeview_model.set_sort_column_id(5,gtk.SORT_DESCENDING)
        self.treeview.grab_focus()
        return

    def insert_row(self, model, allepisodes, incremental, title, date, path):
        myiter=model.append(None)

        if allepisodes:
            exists = True
            subscribed = True
        elif incremental:
            exists = True
            subscribed = False
        else:
            exists = False
            subscribed = False

        model.set_value(myiter, 0, allepisodes)
        model.set_value(myiter, 1, incremental)
        model.set_value(myiter, 2, False)           # Delete Should always be false at load
        model.set_value(myiter, 3, exists)
        model.set_value(myiter, 4, title)
        model.set_value(myiter, 5, date)
        model.set_value(myiter, 6, path)
        model.set_value(myiter, 7, subscribed)
        return myiter

    def on_cb_all_toggle_toggled(self, cell, path):
        treeiter = self.treeview_model.get_iter(path)
        allepisodes = self.treeview_model.get_value(treeiter, 0)
        incremental = self.treeview_model.get_value(treeiter, 1)
        delete_req = self.treeview_model.get_value(treeiter, 2)
        existing = self.treeview_model.get_value(treeiter, 3)
        subscribed = self.treeview_model.get_value(treeiter, 7)

        if existing:
            if allepisodes and subscribed and not delete_req:
                self.treeview_model.set_value(treeiter, 0, True)
            elif incremental and not delete_req:
                self.treeview_model.set_value(treeiter, 0, True)
                self.treeview_model.set_value(treeiter, 1, False)
                self.lock_user_controls()
        else:
            self.treeview_model.set_value(treeiter, 0, not self.treeview_model.get_value(treeiter, 0))
            if self.treeview_model.get_value(treeiter, 0):
                self.treeview_model.set_value(treeiter, 1, False)
            self.lock_user_controls()

        return

    def on_cb_new_toggle_toggled(self, cell, path):
        treeiter = self.treeview_model.get_iter(path)
        allshows = self.treeview_model.get_value(treeiter, 0)
        incremental = self.treeview_model.get_value(treeiter, 1)
        delete_req = self.treeview_model.get_value(treeiter, 2)
        existing = self.treeview_model.get_value(treeiter, 3)
        subscribed = self.treeview_model.get_value(treeiter, 7)

        if existing:
            if incremental and not subscribed and not delete_req:
                self.treeview_model.set_value(treeiter, 1, True)
            elif allshows and not delete_req:
                self.treeview_model.set_value(treeiter, 0, False)
                self.treeview_model.set_value(treeiter, 1, True)
                self.lock_user_controls()
        else:
            self.treeview_model.set_value(treeiter, 1, not self.treeview_model.get_value(treeiter, 1))
            if self.treeview_model.get_value(treeiter, 1):
                self.treeview_model.set_value(treeiter, 0, False)
            self.lock_user_controls()

        return

    def on_cb_delete_toggle_toggled(self, cell, path):
        treeiter = self.treeview_model.get_iter(path)
        existing = self.treeview_model.get_value(treeiter, 3)
        subscribed = self.treeview_model.get_value(treeiter, 7)
        if existing:
            self.treeview_model.set_value(treeiter, 2, not self.treeview_model.get_value(treeiter, 2))
            if subscribed:
                self.treeview_model.set_value(treeiter, 0, True)
                self.treeview_model.set_value(treeiter, 1, False)
            else:
                self.treeview_model.set_value(treeiter, 0, False)
                self.treeview_model.set_value(treeiter, 1, True)

            self.lock_user_controls()
        else:
            self.treeview_model.set_value(treeiter, 0, False)
            self.treeview_model.set_value(treeiter, 1, False)
            self.treeview_model.set_value(treeiter, 2, False)
        return

    def on_treeview_start_interactive_search(self, obj):
        obj.set_search_column(4)
        return

    def on_rb_aly_toggled(self, widget, data=None):
        rb_aly_status = ("OFF", "ON")[widget.get_active()]
        if rb_aly_status == "ON":
            self.user = 'aly'
            if self.content:
                self._get_items()
        return

    def on_rb_ben_toggled(self, widget, data=None):
        rb_ben_status = ("OFF", "ON")[widget.get_active()]
        if rb_ben_status == "ON":
            self.user = 'ben'
            if self.content:
                self._get_items()
        return

    def on_rb_kim_toggled(self, widget, data=None):
        rb_kim_status = ("OFF", "ON")[widget.get_active()]
        if rb_kim_status == "ON":
            self.user = 'kim'
            if self.content:
                self._get_items()
        return

    def on_rb_michelle_toggled(self, widget, data=None):
        rb_michelle_status = ("OFF", "ON")[widget.get_active()]
        if rb_michelle_status == "ON":
            self.user = 'michelle'
            if self.content:
                self._get_items()
        return

    def on_rb_daniel_toggled(self, widget, data=None):
        rb_daniel_status = ("OFF", "ON")[widget.get_active()]
        if rb_daniel_status == "ON":
            self.user = 'daniel'
            if self.content:
                self._get_items()
        return

    def on_rb_series_toggled(self, widget, data=None):
        rb_series_status = ("OFF", "ON")[widget.get_active()]
        if rb_series_status == "ON":
            self.content = 'Series'
            if self.user:
                self._get_items()
        return

    def on_rb_movies_toggled(self, widget, data=None):
        rb_movies_status = ("OFF", "ON")[widget.get_active()]
        if rb_movies_status == "ON":
            self.content = 'Movies'
            if self.user:
                self._get_items()
        return

    def bt_quit_clicked(self,obj):
        gtk.main_quit()
        return

    def bt_cancel_clicked(self,obj):
        self.bt_cancel.set_sensitive(False)
        self.bt_save.set_sensitive(False)
        self.pull_item()
        self.push_item('Reloading Window, Please Wait')
        while gtk.events_pending():
            gtk.main_iteration_do(False)
        self.load_window()
        self.push_item('Please Make Your Selections and Press Save or Cancel')
        while gtk.events_pending():
            gtk.main_iteration_do(False)
        return

    def bt_save_clicked(self, obj):

        self.bt_cancel.set_sensitive(False)
        self.bt_save.set_sensitive(False)
        self.push_item('Please Wait for Updates to Complete')
        while gtk.events_pending():
            gtk.main_iteration_do(False)

        treeiter = self.treeview_model.get_iter_first()
        Update_Request = []

        while treeiter:
            all_episodes = self.treeview_model.get_value(treeiter, 0)
            incrementals = self.treeview_model.get_value(treeiter, 1)
            delete_req = self.treeview_model.get_value(treeiter, 2)
            exists = self.treeview_model.get_value(treeiter, 3)
            title = self.treeview_model.get_value(treeiter, 4)
            date = self.treeview_model.get_value(treeiter, 5)
            path = self.treeview_model.get_value(treeiter, 6)
            subscribed = self.treeview_model.get_value(treeiter, 7)
            treeiter = self.treeview_model.iter_next(treeiter)

            title = os.path.basename(path)

            if delete_req:
                if  not subscribed:
                    type_delete = self.Incremental
                else:
                    type_delete = self.content

                Update_Request.append({'Action' : 'Delete',
                                       'Type' : type_delete,
                                       'Title' : title,
                                       'Path' : path
                                       })
            elif all_episodes:
                if exists and subscribed:
                    continue
                else:
                    Update_Request.append({'Action' : 'Add',
                                           'Type' : self.content,
                                           'Title' : title,
                                           'Path' : path
                                           })
                    if exists and not subscribed:
                        Update_Request.append({'Action' : 'Delete',
                                               'Type' : self.Incremental,
                                               'Title' : title,
                                               'Path' : path
                                               })
            elif incrementals:
                if exists and not subscribed:
                    continue
                else:
                    Update_Request.append({'Action' : 'Add',
                                           'Type' : self.Incremental,
                                           'Title' : title,
                                           'Path' : path
                                           })
                    if exists and subscribed:
                        Update_Request.append({'Action' : 'Delete',
                                               'Type' : self.content,
                                               'Title' : title,
                                               'Path' : path
                                               })

        conn.root.UpdateLinks(self.user, Update_Request)
        self._get_items()
        self.pull_item()
        self.push_item('Updates Complete')
        return

    def push_item(self, msg):
        self.msg_id.append(self.status_bar.push(0, msg))
        while gtk.events_pending():
            gtk.main_iteration_do(False)
        return

    def pull_item(self):
        while len(self.msg_id) > 0:
            self.msg_id.pop()
            self.status_bar.pop(0)
        return

    def _get_items(self):
        self.push_item('Please Wait for Window to Load')
        self.bt_quit.set_sensitive(False)
        while gtk.events_pending():
            gtk.main_iteration_do(False)
        self.table_entries = conn.root.ListItems(self.user, self.content, True)
        self.table_entries = zlib.decompress(self.table_entries)
        self.table_entries = pickle.loads(self.table_entries)
        self.bt_quit.set_sensitive(True)
        self.load_window()
        self.pull_item()
        self.push_item('Please Make Your Selections and Press Save or Cancel')
        while gtk.events_pending():
            gtk.main_iteration_do(False)

if __name__ == "__main__":

    parser = OptionParser()
    options, args = parser.parse_args()

    log_level = logging.getLevelName(options.loglevel.upper())

    if options.logfile == 'daddyvision.log':
        log_file = '%s.log' % (__pgmname__)
    else:
        log_file = os.path.expanduser(options.logfile)

    # If an absolute path is not specified, use the default directory.
    if not os.path.isabs(log_file):
        log_file = os.path.join(logger.LogDir, log_file)

    logger.start(log_file, log_level, timed=True)

    log.debug("Parsed command line options: %s" % (options))
    log.debug("Parsed arguments: %r" % args)

    mw     = Main_Window()
