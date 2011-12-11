#!/usr/bin/env python
"""
Author: AJ Reynolds
Date: 11-27-2010
Purpose:
Program to maintain subscriptions to Series and Movies

"""
import os
import re
import sys
import gtk
import time
import errno
import pickle
import shutil
import socket
import difflib
import fnmatch
import logging
import commands
import datetime
import subprocess
import logging.handlers
from seriesExceptions import *
from datetime import date
from optparse import OptionParser, OptionGroup
from configobj import ConfigObj

__version__ = '$Rev$'
__pgmname__ = 'getnew'
__cfgname__ = 'syncrmt'

host        = socket.gethostname()
PgmDir      = os.path.dirname(__file__)
HomeDir     = os.path.expanduser('~')
ConfigDirB  = os.path.join(HomeDir, '.config')
ConfigDir   = os.path.join(ConfigDirB, 'xbmcsupt')
LogDir      = os.path.join(HomeDir, 'log')

if not os.path.exists(LogDir):
    try:
        os.makedirs(LogDir)
    except:
        raise ConfigValueError("Cannot Create Log Directory: %s" % LogDir)

# Set up a specific logger with our desired output level
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
ml = logging.handlers.TimedRotatingFileHandler(os.path.join(LogDir, '%s.log' % __pgmname__), when='midnight', backupCount=7)
dl = logging.handlers.TimedRotatingFileHandler(os.path.join(LogDir, '%s_debug.log' % __pgmname__), when='midnight', backupCount=7)
_console = logging.StreamHandler()
ml.setLevel(logging.INFO)
dl.setLevel(logging.DEBUG)
_console.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s - %(message)s")
ml.setFormatter(formatter)
dl.setFormatter(formatter)
_console.setFormatter(formatter)
logger.addHandler(ml)
logger.addHandler(dl)
logger.addHandler(_console)

ml.doRollover()
dl.doRollover()

cmd = 'sudo mount -a'
os.system(cmd)

class Main_Window():
    def __init__(self, user, content):

        self.content = content
        self.user = user

        builder = gtk.Builder()
        builder.add_from_file(parms.glade_file)
        events = {"on_main_window_destroy" : self.bt_quit_clicked,
                  "on_cb_all_toggle_toggled" : self.on_cb_all_toggle_toggled,
                  "on_cb_new_toggle_toggled" : self.on_cb_new_toggle_toggled,
                  "delete_toggle_toggled" : self.on_cb_delete_toggle_toggled,
                  "on_rb_aly_toggled" : self.on_rb_aly_toggled,
                  "on_rb_kim_toggled" : self.on_rb_kim_toggled,
                  "on_rb_ben_toggled" : self.on_rb_ben_toggled,
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
        self.rb_kim = builder.get_object("rb_kim")
        self.rb_ben = builder.get_object("rb_ben")
        self.rb_series = builder.get_object("rb_series")
        self.rb_movies = builder.get_object("rb_movies")
        self.bt_quit = builder.get_object("bt_quit")
        self.bt_cancel = builder.get_object("bt_cancel")
        self.bt_save = builder.get_object("bt_save")
        self.newcell = builder.get_object("newcell")

        #Initialize our Treeview
        self.treeview=builder.get_object("treeview")
        self.treeview_model=builder.get_object("datastore")
        self.treeselection = self.treeview.get_selection()
        self.treeselection.set_mode(gtk.SELECTION_MULTIPLE)
        mode = self.treeselection.get_mode()

        self.setup_controls()
        if self.content == 'series':
            self.rb_series.set_active(True)
        else:
            self.rb_movies.set_active(True)

        self.treeview.set_search_column(1)
        self.wMain.show()
        gtk.main()

    def setup_controls(self):
        # Load Window Based on Command Line Parm or Defaults
        if host == 'tigger':
            self.rb_aly.set_active(True)
            self.rb_aly.set_sensitive(True)
            self.rb_ben.set_sensitive(False)
            self.rb_kim.set_sensitive(False)
        elif host == 'goofy':
            self.rb_kim.set_active(True)
            self.rb_kim.set_sensitive(True)
            self.rb_aly.set_sensitive(False)
            self.rb_ben.set_sensitive(False)
        elif host == 'pluto':
            self.rb_ben.set_active(True)
            self.rb_ben.set_sensitive(True)
            self.rb_aly.set_sensitive(False)
            self.rb_kim.set_sensitive(False)
        else:
            self.rb_aly.set_sensitive(True)
            self.rb_ben.set_sensitive(True)
            self.rb_kim.set_sensitive(True)
            if self.user == 'aly':
                self.rb_aly.set_active(True)
            elif self.user == 'kim':
                self.rb_kim.set_active(True)
            else:
                self.rb_ben.set_active(True)

        self.rb_series.set_sensitive(True)
        self.rb_movies.set_sensitive(True)

        return

    def load_window(self, user, content):
        self.content = content
        self.user = user

        if host == 'grumpy':
            symdir = os.path.join('/mnt/Links', self.user)
            self.OnlyNewShowsFile = os.path.join(symdir, 'OnlyNewShowsList')
        elif self.user =='aly':
            self.OnlyNewShowsFile = '/home/aly/.config/xbmcsupt/OnlyNewShowsList'
        elif self.user =='ben':
            self.OnlyNewShowsFile = '/home/xbmc/.config/xbmcsupt/OnlyNewShowsList'
        elif self.user =='kim':
            self.OnlyNewShowsFile = '/home/kimr/.config/xbmcsupt/OnlyNewShowsList'

        if os.path.exists(self.OnlyNewShowsFile):
            with open(self.OnlyNewShowsFile, "r") as f:
                self.OnlyNewShowsList = pickle.load(f)
        else:
                self.OnlyNewShowsList = []


        self.bt_quit.set_sensitive(True)
        self.bt_quit.set_visible(True)
        self.bt_cancel.set_sensitive(False)
        self.bt_cancel.set_visible(False)
        self.bt_save.set_sensitive(False)
        self.bt_save.set_visible(False)

        if self.content == 'series':
            target_level = 0
            self.content_dir = parms.series_dir
            self.newcell.set_visible(True)
#            self.newcell.set_sensitive(True)
        elif self.content == 'movies':
            target_level = 1
            self.content_dir = parms.movies_dir
            self.newcell.set_visible(False)
 #           self.newcell.set_sensitive(False)
        else:
            self.content = 'series'
            target_level = 0
            self.content_dir = parms.series_dir
            self.cellnew.set_visible(True)

        if self.user == 'aly':
            self.symlinks_dir = os.path.join(parms.aly_dir, self.content.title())
        elif self.user == 'kim':
            self.symlinks_dir = os.path.join(parms.kim_dir, self.content.title())
        elif self.user == 'ben':
            self.symlinks_dir = os.path.join(parms.ben_dir, self.content.title())
        else:
            return

        logger.debug('Content: %s  User: %s' % (content, user))
        logger.debug('Directory: %s  Symlinks: %s' % (self.content_dir, self.symlinks_dir))

        self.treeview_model.clear()

        exclude_list = ["lost+found", ".Trash-1000", "CinemaExperience", "New", ".Done"]
        startinglevel = self.content_dir.count(os.sep)
        for root, dirs, files in os.walk(os.path.abspath(self.content_dir),followlinks=False):
            logger.info('ROOT: %s' % (root))

            dirs.sort()
            for directory in dirs[:]:
                level = root.count(os.sep) - startinglevel
                if directory in exclude_list:
                    logger.debug("Skipping: %s" % directory)
                    dirs.remove(directory)
                    continue
                elif level == target_level:
                    logger.debug('Directory: %s Level: %s' % (directory, level))

                    if directory in self.OnlyNewShowsList:
                        OnlyNewShows = True
                    else:
                        OnlyNewShows = False

                    title = directory.split(None, 1)
                    if title[0] in parms.predicates:
                        title = '%s, %s' % (title[1], title[0])
                    else:
                        title = directory

                    if OnlyNewShows:
                        status = False
                    elif os.path.exists(os.path.join(self.symlinks_dir,directory)):
                        status = True
                    else:
                        status = False

                    if options.debug:
                        logger.debug("%s %s - %s" % (status, title, os.path.join(self.symlinks_dir,directory)))

                    statinfo = os.stat(os.path.join(root,directory))
                    movie_itr = self.insert_row(self.treeview_model,
                                                status,
                                                title,
                                                date.fromtimestamp(statinfo.st_mtime),
                                                os.path.join(root,directory),
                                                False,
                                                OnlyNewShows
                                                )
                else:
                    logger.debug('Ignored Directory: %s Level: %s' % (directory, level))

            if level < target_level:
                pass
            else:
                while len(dirs) > 0:
                    del dirs[0]

        if self.content == 'series':
            self.treeview_model.set_sort_column_id(1,gtk.SORT_ASCENDING)
        else:
            self.treeview_model.set_sort_column_id(2,gtk.SORT_DESCENDING)
        return

    def insert_row(self, model, status, title=' ', date=' ', path=' ', delete=False, OnlyNewShows=False):
        myiter=model.append(None)
        model.set_value(myiter, 0, status)
        model.set_value(myiter, 1, title)
        model.set_value(myiter, 2, date)
        model.set_value(myiter, 3, path)
        model.set_value(myiter, 4, status)
        model.set_value(myiter, 5, delete)
        model.set_value(myiter, 6, OnlyNewShows)
        return myiter

    def on_cb_new_toggle_toggled(self, cell, path):
        treeiter = self.treeview_model.get_iter(path)
        existing = self.treeview_model.get_value(treeiter, 4)
        show = os.path.basename(self.treeview_model.get_value(treeiter, 3))
        if show in self.OnlyNewShowsList:
            self.treeview_model.set_value(treeiter, 0, False)
            self.treeview_model.set_value(treeiter, 6, True)
        elif existing:
            self.treeview_model.set_value(treeiter, 0, True)
            self.treeview_model.set_value(treeiter, 6, False)
        else:
            self.treeview_model.set_value(treeiter, 6, not self.treeview_model.get_value(treeiter, 6))
            if self.treeview_model.get_value(treeiter, 6):
                self.treeview_model.set_value(treeiter, 0, False)

            self.bt_quit.set_sensitive(False)
            self.bt_quit.set_visible(False)
            self.bt_cancel.set_sensitive(True)
            self.bt_cancel.set_visible(True)
            self.bt_save.set_sensitive(True)
            self.bt_save.set_visible(True)

            self.rb_aly.set_sensitive(False)
            self.rb_ben.set_sensitive(False)
            self.rb_kim.set_sensitive(False)
            self.rb_series.set_sensitive(False)
            self.rb_movies.set_sensitive(False)

        return

    def on_cb_all_toggle_toggled(self, cell, path):
        treeiter = self.treeview_model.get_iter(path)
        existing = self.treeview_model.get_value(treeiter, 4)
        show = os.path.basename(self.treeview_model.get_value(treeiter, 3))
        if show in self.OnlyNewShowsList:
            self.treeview_model.set_value(treeiter, 6, True)
            self.treeview_model.set_value(treeiter, 0, False)
        elif existing:
            self.treeview_model.set_value(treeiter, 0, True)
        else:
            self.treeview_model.set_value(treeiter, 0, not self.treeview_model.get_value(treeiter, 0))
            if self.treeview_model.get_value(treeiter, 0):
                self.treeview_model.set_value(treeiter, 6, False)

            self.bt_quit.set_sensitive(False)
            self.bt_quit.set_visible(False)
            self.bt_cancel.set_sensitive(True)
            self.bt_cancel.set_visible(True)
            self.bt_save.set_sensitive(True)
            self.bt_save.set_visible(True)

            self.rb_aly.set_sensitive(False)
            self.rb_ben.set_sensitive(False)
            self.rb_kim.set_sensitive(False)
            self.rb_series.set_sensitive(False)
            self.rb_movies.set_sensitive(False)

        return

    def on_cb_delete_toggle_toggled(self, cell, path):
        treeiter = self.treeview_model.get_iter(path)
        existing = self.treeview_model.get_value(treeiter, 4)
        show = os.path.basename(self.treeview_model.get_value(treeiter, 3))
        if show in self.OnlyNewShowsList or existing:
            self.treeview_model.set_value(treeiter, 5, not self.treeview_model.get_value(treeiter, 5))

            self.bt_quit.set_sensitive(False)
            self.bt_quit.set_visible(False)
            self.bt_cancel.set_sensitive(True)
            self.bt_cancel.set_visible(True)
            self.bt_save.set_sensitive(True)
            self.bt_save.set_visible(True)

            self.rb_aly.set_sensitive(False)
            self.rb_ben.set_sensitive(False)
            self.rb_kim.set_sensitive(False)
            self.rb_series.set_sensitive(False)
            self.rb_movies.set_sensitive(False)
        else:
            self.treeview_model.set_value(treeiter, 5, False)
        return

    def on_treeview_start_interactive_search(self, obj):
        obj.set_search_column(1)
        return

    def on_rb_aly_toggled(self, widget, data=None):
        rb_aly_status = ("OFF", "ON")[widget.get_active()]
        if rb_aly_status == "ON":
            self.user = 'aly'
            self.load_window(self.user, self.content)
        return

    def on_rb_kim_toggled(self, widget, data=None):
        rb_kim_status = ("OFF", "ON")[widget.get_active()]
        if rb_kim_status == "ON":
            self.user = 'kim'
            self.load_window(self.user, self.content)
        return

    def on_rb_ben_toggled(self, widget, data=None):
        rb_ben_status = ("OFF", "ON")[widget.get_active()]
        if rb_ben_status == "ON":
            self.user = 'ben'
            self.load_window(self.user, self.content)
        return

    def on_rb_series_toggled(self, widget, data=None):
        rb_series_status = ("OFF", "ON")[widget.get_active()]
        if rb_series_status == "ON":
            self.load_window(self.user, "series")
        return

    def on_rb_movies_toggled(self, widget, data=None):
        rb_movies_status = ("OFF", "ON")[widget.get_active()]
        if rb_movies_status == "ON":
            self.load_window(self.user, "movies")
        return

    def bt_quit_clicked(self,obj):
        gtk.main_quit()
        return

    def bt_cancel_clicked(self,obj):
        self.setup_controls()
        rb_series_status = ("OFF", "ON")[self.rb_series.get_active()]
        if rb_series_status == "ON":
            self.load_window(self.user, "series")
        else:
            self.load_window(self.user, "movies")

        return

    def bt_save_clicked(self,obj):
        self.links_file = os.path.join(parms.output_dir, '%s_symlinks_%s' % (host, self.content))
        treeiter = self.treeview_model.get_iter_first()
        with open(self.links_file, "w") as updates:
            while treeiter:
                selected = self.treeview_model.get_value(treeiter, 0)
                title = self.treeview_model.get_value(treeiter, 1)
                date = self.treeview_model.get_value(treeiter, 2)
                path = self.treeview_model.get_value(treeiter, 3)
                link_exists = self.treeview_model.get_value(treeiter, 4)
                delete_requested = self.treeview_model.get_value(treeiter, 5)
                OnlyNewShows_requested = self.treeview_model.get_value(treeiter, 6)
                treeiter = self.treeview_model.iter_next(treeiter)
                show = os.path.basename(path)
                if selected or OnlyNewShows_requested:
                    if host == "grumpy" and not options.remote:
                        if OnlyNewShows_requested:
                            OnlyNewSHowsLink = os.path.split(self.symlinks_dir)[0]
                            symlink = os.path.join(os.path.join(OnlyNewSHowsLink, 'Incrementals'), show)
                        else:
                            symlink = os.path.join(self.symlinks_dir, show)

                        if delete_requested:
                            self.delete_link(show, path, symlink)
                        else:
                            self.add_link(OnlyNewShows_requested, selected, show, path, symlink)
                    elif host in ['goofy', 'tigger', 'pluto'] or options.remote:
                        if (link_exists or show in self.OnlyNewShowsList) and not delete_requested and not options.full:
                            continue
                        path = self.build_path(path)
                        symdir = os.path.join('/mnt/Links', self.user)
                        if OnlyNewShows_requested:
                            symdir = os.path.join(symdir, 'Incrementals')
                        else:
                            symdir = os.path.join(symdir, self.content.title())

                        if delete_requested:
                            cmd = 'rm %s' % (os.path.join(symdir, os.path.basename(path)))
                            logger.info('%s' % (cmd))
                            updates.write('%s\n' % cmd)
                            if show in self.OnlyNewShowsList:
                                self.OnlyNewShowsList.remove(show)
                        else:
                            cmd = 'ln -s %s %s' % (path, os.path.join(symdir, os.path.basename(path)))
                            logger.info('%s' % (cmd))
                            updates.write('%s\n' % cmd)
                            if not show in self.OnlyNewShowsList:
                                self.OnlyNewShowsList.append(show)

        with open(self.OnlyNewShowsFile, "w") as f:
            pickle.dump(self.OnlyNewShowsList, f)

        self.update_grumpy()
        self.setup_controls()

        rb_series_status = ("OFF", "ON")[self.rb_series.get_active()]
        if rb_series_status == "ON":
            self.rb_movies.set_active(True)
        else:
            self.rb_series.set_active(True)
        return

    def delete_link(self, show, path, symlink):
        if show in self.OnlyNewShowsList:
            self.OnlyNewShowsList.remove(show)
        if os.path.exists(symlink):
            try:
                os.remove(symlink)
                logger.info('Removed Symlink: %s' % symlink)
            except OSError, message:
                logger.error('Unable to remove symlink for %s to: %s - %s' % (self.user.title(), path, message))
        return

    def add_link(self, OnlyNewShows_requested, selected, show, path, symlink):
        if OnlyNewShows_requested and not show in self.OnlyNewShowsList:
            self.OnlyNewShowsList.append(show)
        if not os.path.exists(symlink) and (selected or OnlyNewShows_requested):
            try:
                os.symlink(path, symlink)
                os.lchown(symlink, 1000, 100)
                logger.info('Created Only New Shows symlink for %s to: %s' % (self.user.title(), path))
            except OSError, message:
                logger.error('Unable to created symlink for %s to: %s - %s' % (self.user.title(), path, message))
        return

    def update_grumpy(self):
        if host == "grumpy":
            if self.user =='aly':
                rmtconfig = '/home/aly/.config/xbmcsupt/'
                rmthost = 'tigger'
            elif self.user =='ben':
                rmtconfig = '/home/xbmc/.config/xbmcsupt/'
                rmthost = 'pluto'
            elif self.user =='kim':
                rmtconfig = '/home/kimr/.config/xbmcsupt/'
                rmthost = 'goofy'
            if not options.remote:
                cmd = 'sudo scp -p %s %s:%s' % (self.OnlyNewShowsFile, rmthost, rmtconfig)
                os.system(cmd)
                cmd = 'sudo ssh %s chown 1000:100 %s' % (rmthost, os.path.join(rmtconfig, 'OnlyNewShowsList'))
                os.system(cmd)
                cmd = 'sudo ssh %s chmod 664 %s' % (rmthost, os.path.join(rmtconfig, 'OnlyNewShowsList'))
                os.system(cmd)
        else:
            cmd = 'sudo scp -p %s 192.168.9.201:/home/aj/.config/xbmcsupt/' % (os.path.join(ConfigDir, 'OnlyNewShowsList'))
            os.system(cmd)
            if os.path.exists(self.links_file):
                os.chmod(self.links_file, 0777)
                cmd = 'sudo scp -p %s 192.168.9.201:/mnt/Links/%s_links_%s' % (self.links_file, host, self.content)
                os.system(cmd)
                cmd = 'sudo ssh 192.168.9.201 /mnt/Links/%s_links_%s' % (host, self.content)
                os.system(cmd)
            elif not options.remote:
                os.remove(self.links_file)

        return

    def build_path(self, path):

        if self.content == 'series':
            path = os.path.join('/mnt/TV/Series', os.path.basename(path))
        else:
            subfolder = os.path.basename(os.path.dirname(path))
            path = os.path.join(os.path.join('/mnt/Movies', subfolder), os.path.basename(path))

        path = path.replace ( '"', '\\"' )
        path = path.replace ( "'", "\\'" )
        path = path.replace ( "`", "\\'" )
        path = path.replace ( ' ', '\\ ' )
        path = path.replace ( '&', '\\&' )
        path = path.replace ( '(', '\\(' )
        path = path.replace ( ')', '\\)' )
        path = path.replace ( '[', '\\[' )
        path = path.replace ( ']', '\\]' )
        return path

    def cb_select_toggle_toggled(self, cell, path):
        treeiter = self.treeview_model.get_iter(path)
        downloaded = self.treeview_model.get_value(treeiter, 3)
        if downloaded:
            self.treeview_model.set_value(treeiter, 0, True)
        else:
            self.treeview_model.set_value(treeiter, 0, not self.treeview_model.get_value(treeiter, 0))
        return

class GetConfig(object):
    def __init__(self, update_existing=False, pgmname=__cfgname__):


        self.cfgfile = os.path.expanduser(os.path.join(ConfigDir, '%s.cfg' % pgmname))
        if update_existing or not os.path.exists(self.cfgfile):
            self.BuildConfig()

        config = ConfigObj(self.cfgfile, unrepr=True, interpolation=False)

        Defaults     = config['Defaults']
        self.movies_dir = Defaults['movies_dir']
        self.series_dir = Defaults['series_dir']
        self.output_dir = os.path.expanduser(Defaults['output_dir'])
        self.aly_dir    = os.path.expanduser(Defaults['aly_symlinks'])
        self.kim_dir    = os.path.expanduser(Defaults['kim_symlinks'])
        self.ben_dir    = os.path.expanduser(Defaults['ben_symlinks'])
        self.glade_file = os.path.join(PgmDir, Defaults['glade_file'])
        self.predicates    = Defaults['predicates']

        if not os.path.exists(self.movies_dir):
            logger.error("Path Not Found: %s" % self.movies_dir)
            logger.error("Invalid Config Entries, Ending")
            raise ConfigValueError("Path Not Found: %s" % self.movies_dir)

        if not os.path.exists(self.series_dir):
            logger.error("Path Not Found: %s" % self.series_dir)
            logger.error("Invalid Config Entries, Ending")
            raise ConfigValueError("Path Not Found: %s" % self.series_dir)
        return

    def BuildConfig(self):
        if not os.path.exists(ConfigDir):
            try:
                os.makedirs(ConfigDir)
            except:
                logger.error("Cannot Create Config Directory: %s" % ConfigDir)
                raise ConfigValueError("Cannot Create Config Directory: %s" % ConfigDir)

        config = ConfigObj(unrepr = True, interpolation = False)
        config.filename = self.cfgfile
        config['Defaults'] = {}
        config['Defaults']['movies_dir']        = self.get_dir('/mnt/Movies', 'Movies')
        config['Defaults']['series_dir']        = self.get_dir('/mnt/TV/Series', 'Series')

        config['Defaults']['aly_host']          = self.get_value("Enter Tigger's IP Address", '192.168.9.21')
        config['Defaults']['aly_symlinks']      = self.get_dir('/mnt/Links/aly/', 'Aly\'s Symlinks')
        config['Defaults']['aly_rmt_movies']    = self.get_value("Enter %s Directory: " % 'Aly\'s Remote Movies', '/mnt/Movies/')
        config['Defaults']['aly_rmt_series']    = self.get_value("Enter %s Directory" % 'Aly\'s Remote Series', '/mnt/Series/')

        config['Defaults']['kim_host']          = self.get_value("Enter Goofy's IP Address", '192.168.9.20')
        config['Defaults']['kim_symlinks']      = self.get_dir('/mnt/Links/kim/', 'Kim\'s Symlinks')
        config['Defaults']['kim_rmt_movies']    = self.get_value("Enter %s Directory: " % 'Kim\'s Remote Movies', '/mnt/Movies/')
        config['Defaults']['kim_rmt_series']    = self.get_value("Enter %s Directory" % 'Kim\'s Remote Series', '/mnt/Series/')

        config['Defaults']['ben_host']          = self.get_value("Enter Pluto's IP Address", '')
        config['Defaults']['ben_symlinks']      = self.get_dir('/mnt/Links/ben/', 'Ben\'s Symlinks')
        config['Defaults']['ben_rmt_movies']    = self.get_value("Enter %s Directory: " % 'Ben\'s Remote Movies', '/mnt/Videos/Movies/')
        config['Defaults']['ben_rmt_series']    = self.get_value("Enter %s Directory" % 'Ben\'s Remote Series', '/mnt/Videos/Series/')

        config['Defaults']['output_dir']        = self.get_dir("Enter %s Directory:" % '/mnt/Links', 'Output')
        config['Defaults']['glade_file']        = self.get_value("Enter Glade File Name", '%s.glade' % __pgmname__)
        config['Defaults']['media_ext']         = ['avi', 'mkv', 'mp4', 'mpeg']
        config['Defaults']['predicates']        = ['The', 'A', 'An']

        config.write()

    def get_dir(self, dir_name_d, message):
        while True:
            dir_name = raw_input("Enter %s Directory (%s): " % (message, dir_name_d)).rstrip(os.sep)
            if not dir_name:
                dir_name = dir_name_d
            if os.path.exists(dir_name):
                return dir_name

            while not os.path.exists(os.path.expanduser(dir_name)):
                action = raw_input("%s Directory: %s - Not Found,  Ignore/Re-Enter/Create/Abort? (I/R/C/A): " % (message, dir_name)).lower()[0]
                if len(action) < 1:
                    continue
                elif action[0] == 'a':
                    sys.exit(1)
                elif action[0] == 'i':
                    return dir_name
                elif action[0] == 'c':
                    try:
                        os.makedirs(dir_name)
                    except OSError, exc:
                        print "ERROR - Unable to Create Config Directory: %s, %s: " % (dir_name, exc)
                        continue
                elif action[0] == 'r':
                    dir_name = self.get_dir(dir_name_d, message)
                return dir_name

    def get_value(self, message, default):
        while True:
            value = raw_input("%s (%s): " % (message, default))
            if not value:
                value = default
            return value

if __name__ == "__main__":

    parser = OptionParser(
        "%prog [options]",
        version="%prog " + __version__)
    parser.add_option("-f", "--full", dest="full",
        action="store_true", default=False,
        help="Include FULL list of selected alias including existing")
    parser.add_option("-r", "--remote", dest="remote",
        action="store_true", default=False,
        help="Treat as if running remote regardless of host")

    group = OptionGroup(parser, "Users:")
    group.add_option("-a", "--aly", dest="user",
        action="store_const", const='aly', default='aly',
        help="Build Links for Aly")
    group.add_option("-k", "--kim", dest="user",
        action="store_const", const='kim',
        help="Build Links for Kim")
    group.add_option("-p", "--peterson", dest="user",
        action="store_const", const='ben',
        help="Build Links for Ben & Mac Peterson")
    parser.add_option_group(group)

    group = OptionGroup(parser, "Category:")
    group.add_option("-s", "--series", dest="type",
        action="store_const", const='series', default='series',
        help="process TV Series")
    group.add_option("-m", "--movies", dest="type",
        action="store_const", const='movies',
        help="process Movies")
    parser.add_option_group(group)

    group = OptionGroup(parser, "Logging Levels:")
    group.add_option("-e", "--errors", dest="error",
        action="store_true", default=False,
        help="omit all but error logging")
    group.add_option("-q", "--quiet", dest="quiet",
        action="store_true", default=False,
        help="omit informational logging")
    group.add_option("-v", "--verbose", dest="verbose",
        action="store_true", default=False,
        help="increase informational logging")
    group.add_option("-d", "--debug", dest="debug",
        action="store_true", default=False,
        help="increase informational logging to include debug")
    parser.add_option_group(group)

    options, args = parser.parse_args()

    opt_sel = 0
    if options.debug:
        logger.setLevel(logging.DEBUG)
        ml.setLevel(logging.DEBUG)
        _console.setLevel(logging.DEBUG)
        opt_sel = opt_sel + 1
    if options.error:
        logger.setLevel(logging.ERROR)
        ml.setLevel(logging.ERROR)
        _console.setLevel(logging.ERROR)
        opt_sel = opt_sel + 1
    if options.quiet:
        logger.setLevel(logging.WARNING)
        ml.setLevel(logging.WARNING)
        _console.setLevel(logging.WARNING)
        opt_sel = opt_sel + 1
    if options.verbose:
        logger.setLevel(logging.DEBUG)
        ml.setLevel(logging.DEBUG)
        _console.setLevel(logging.DEBUG)
        opt_sel = opt_sel + 1

    logger.debug("Parsed command line options: %r" % options)
    logger.debug("Parsed arguments: %r" % args)

    if host == 'tigger':
        options.user = 'aly'
    elif host == 'goofy':
        options.user = 'kim'
    elif host == 'pluto':
        options.user = 'ben'

    parms = GetConfig()

    mw     = Main_Window(options.user, options.type)
