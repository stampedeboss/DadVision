#!/usr/bin/env python
"""
#Author: AJ Reynolds
#Date: 12-02-2010
#Purpose:
#########################################################################
#									#
#   Program to perform various tasks (check, rename, etc) to maintain	#
#   a Video Library of TV Shows						#
#									#
#########################################################################
#   Changelog:								#
#	12-06-2010 1.0 Initial Release, combined various tools into a 	#
#			Single Routine					#
#									#
#########################################################################

"""
import sys, os, os.path, stat, time, re
from datetime import datetime, date, timedelta
import logging
import logging.handlers
import gtk
import gtk.glade
import tvdb
import seriesinfo
import unicodedata
from optparse import OptionParser
from configobj import ConfigObj
from seriesinfo import SeriesInfo
from seriesExceptions import (InvalidType, InvalidPath, InvalidFilename,
ConfigNotFound, ConfigValueError, DictKeyError, DataRetrievalError,
ShowNotFound, SeasonNotFound, EpisodeNotFound, EpisodeNameNotFound
)

VERSION = '$Rev$'

ConfigFile = os.path.expanduser('~/.config/videotools/series.cfg')

if not os.path.exists(ConfigFile):
	cmd = 'series_defaults.py'
	os.system(cmd)

if not os.path.exists(ConfigFile):
	print "ERROR NO CONFIG FILE"
	sys.exit(1)
else:
	config = ConfigObj(ConfigFile, unrepr=True, interpolation=False)

Defaults 	= config['Defaults']
series_dir 	= os.path.expanduser(Defaults['series_dir'])
exclude_extras 	= os.path.expanduser(Defaults['exclude_extras'])
exclude_series 	= os.path.expanduser(Defaults['exclude_series'])
glade_file 	= os.path.expanduser(Defaults['glade_file'])
splhand_file	= os.path.expanduser(Defaults['splhand_file'])
media_ext	= Defaults['media_ext']

Logging 	= config['Logging']
log_file 	= os.path.expanduser(Logging['log_file'])
backupcount 	= int(Logging['BackupCount'])

FileNames 	= config['FileNames']		# Used in reformt logic below

RegEx		= config['RegEx']
patterns	= RegEx['Std']

Check		= config['Check']
default_age 	= int(Check['age'])

compiled_regexs = []
for cpattern in patterns:
	try:
		cregex = re.compile(cpattern, re.X|re.I)
	except re.error, errormsg:
		logger.warn("WARNING: Invalid RegEx pattern, %s. %s" % (errormsg, cregex.pattern))
		sys.exit(1)
	else:
		compiled_regexs.append(cregex)

options = []
args 	= []
exclude_list = []

parser = OptionParser(
	"%prog [options] check|rename|dup <pathnames>...",
	version="%prog " + VERSION)

parser.add_option("-q", "--quiet", dest="quiet",
	action="store_true", default=False,
	help="omit informational logging")
parser.add_option("-e", "--errors", dest="error",
	action="store_true", default=False,
	help="omit all but error logging")
parser.add_option("-v", "--verbose", dest="verbose",
	action="store_true", default=False,
	help="debug - verbose output in log")
parser.add_option("--debug", dest="debug",
	action="store_true", default=False,
	help="debug - verbose output in log")
parser.add_option("--no-gui", dest="nogui",
	action="store_true", default=False,
	help="command line only, no window")

parser.add_option("-i", "--input-directory",
	dest="requested_dir",
	default="None",
	help="directory to be scanned")

parser.add_option("-x", "--no-excludes", dest="no_excludes",
	action="store_true", default=False,
	help="Ignore Exclude File")
parser.add_option("-s", "--specials", dest="show_specials",
	action="store_true", default=False,
	help="Include Specials")

parser.add_option("-r", "--remove", dest="remove",
	action="store_true", default=False,
	help="remove files (keep MKV over AVI, delete non-video files)")

parser.add_option("-d", "--days", dest="age_limit",
	action="store", type=int, default=30,
	help="check back x number of days")
parser.add_option("-f", "--no-age-limit-requested", dest="age_limit_requested",
	action="store_false", default=True,
	help="Full Check, Do not limit check to # days back")

options, args = parser.parse_args()

# Set up a specific logger with our desired output level
logger = logging.getLogger("cseries")
logger.setLevel(logging.DEBUG)
# create log message file and console handler and set level to debug
fh = logging.handlers.RotatingFileHandler(log_file, maxBytes=0, backupCount=backupcount)
ch = logging.StreamHandler()
fh.setLevel(logging.DEBUG)
ch.setLevel(logging.INFO)
# create formatter
formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s - %(message)s")
# add formatter to logger
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add handlers to logger
logger.addHandler(fh)
logger.addHandler(ch)

fh.doRollover()

class SeriesMain():
	def __init__(self):
		builder = gtk.Builder()
		builder.add_from_file(glade_file)
		events = { "on_main_window_destroy" : self.quit,
					"on_bt_ok_clicked" : self.bt_ok_clicked,
					"on_bt_close_clicked" : self.bt_close_clicked
					}
		builder.connect_signals(events)

		self.wMain = builder.get_object("main_window")

		self.wMain.set_size_request(800, 600)
		self.wMain.set_position(gtk.WIN_POS_CENTER)

		#Initialize Log TextView
		self.logwindowview=builder.get_object("txtvw_log")
		self.logwindow=gtk.TextBuffer (None)
		self.logwindowview.set_buffer(self.logwindow)

		#Initialize our Show Tree (Treeview)
		self.treevw_show=builder.get_object("treevw_show")
		self.treest_show_model=gtk.TreeStore(str, str, str, str, str, str, str, str)
		self.treevw_show.set_model(self.treest_show_model)
		#create rendered column 1
		renderer=gtk.CellRendererText()
		column=gtk.TreeViewColumn("STATUS", renderer, text=0)
		column.set_resizable(True)
		self.treevw_show.append_column(column)
		#create rendered column 2
		renderer=gtk.CellRendererText()
		column=gtk.TreeViewColumn("TVDB", renderer, text=1)
		column.set_resizable(True)
		self.treevw_show.append_column(column)
		#create rendered column 3
		renderer=gtk.CellRendererText()
		column=gtk.TreeViewColumn("SERIES", renderer, text=2)
		column.set_resizable(True)
		self.treevw_show.append_column(column)
		#create rendered column 4
		renderer=gtk.CellRendererText()
		column=gtk.TreeViewColumn(" ", renderer, text=3)
		column.set_resizable(True)
		self.treevw_show.append_column(column)
		#create rendered column 5
		renderer=gtk.CellRendererText()
		column=gtk.TreeViewColumn(" ", renderer, text=4)
		column.set_resizable(True)
		self.treevw_show.append_column(column)
		#create rendered column 6
		renderer=gtk.CellRendererText()
		column=gtk.TreeViewColumn(" ", renderer, text=5)
		column.set_resizable(True)
		self.treevw_show.append_column(column)
		#create rendered column 7
		renderer=gtk.CellRendererText()
		column=gtk.TreeViewColumn(" ", renderer, text=6)
		column.set_resizable(True)
		self.treevw_show.append_column(column)
		#create rendered column 8
		renderer=gtk.CellRendererText()
		column=gtk.TreeViewColumn(" ", renderer, text=7)
		column.set_resizable(True)
		self.treevw_show.append_column(column)

		self.treevw_show.set_hover_expand(False)

		self.wMain.show()

		return

	def insert_row(self, model, parent, status, tvdb_id=' ', show=' ', season=' ', episode=' ', title=' ', air_date=' ', item7=' '):
		myiter=model.append(parent, None)
		model.set_value(myiter, 0, status)
		model.set_value(myiter, 1, tvdb_id)
		model.set_value(myiter, 2, show)
		model.set_value(myiter, 3, season)
		model.set_value(myiter, 4, episode)
		model.set_value(myiter, 5, title)
		model.set_value(myiter, 6, air_date)
		model.set_value(myiter, 7, item7)
		return myiter

	def quit(self,obj):
		gtk.main_quit()

	def bt_ok_clicked(self,obj):
		message = "====Begin Scan===="
		logger.debug(message)
		self.check_dir(requested_dir)

	def bt_close_clicked(self,obj):
		gtk.main_quit()

	def log(self, message, color="black", enter="\n"):
		message = message + enter
		buffer = self.logwindow
		iter = buffer.get_end_iter()
		if color != "black":
			tag = buffer.create_tag()
			tag.set_property("foreground", color)
			self.logwindow.insert_with_tags(buffer.get_end_iter(), message, tag)
		else:
			self.logwindow.insert(iter, message)
			mark = buffer.create_mark("end", buffer.get_end_iter(), False)
			self.logwindowview.scroll_to_mark(mark, 0.05, True, 0.0,1.0)

def check_dir(requested_dir):
	logger.debug('check_dir - Dir Requested: %s' % (requested_dir))
	dir_list 	= []
	tvdb_list 	= []
	showdata 	= []
	lastseries 	= 'START'
	lastseason 	= None
	lastepno 	= None
	lastepname	= None
	lastext 	= None
	lastfname	= None
	lastfqname	= None
	scanned	= 0
	last_dups	= ' '

	if options.nogui:
		MISSING = " "
		DUPS	= " "
	else:
		MISSING	= mw.insert_row(mw.treest_show_model, None,"Missing")
		DUPS	= mw.insert_row(mw.treest_show_model, None,"Dup")

	logger.info("====Begin Scan====")

	for root, dirs, files in os.walk(os.path.abspath(requested_dir),followlinks=True):
		if dirs != None:
			dirs.sort()
			for exclude_dir in exclude_list:
				try:
					index = dirs.index(exclude_dir)
					dirs.pop(index)
					if options.debug:
						logger.debug('Removing Dir: %s' % exclude_dir)
				except:
					pass
				pass
			files.sort()
			for fname in files:
				scanned = scanned + 1
				quotient, remainder = divmod(scanned, 250)
				if remainder == 0:
					logger.info('Files Processed: %s - On Series: %s' % (scanned, lastseries))
				fqname = os.path.join(root, fname)
				if options.debug:
					logger.debug('Processing File: %s' % (fqname))
				for cmatcher in compiled_regexs:
					series = cmatcher.search(fqname)
					if series:
						if options.debug:
							logger.debug("RegEx Matched: %s" % cmatcher.pattern)
							namedgroups = series.groupdict().keys()
							for key in namedgroups:
								logger.debug("%s: %s" % ( key, series.group(key)))
						break
				if not series:
					logger.error("Unable to Parse: %s" % os.path.join(root, fname))
					continue
				if series:
					seriesname 	= series.group('seriesname').rsplit('/',1)[-1].replace("&amp;", "&")
					season 		= int(series.group('season'))
					epname		= series.group('epname')
					ext 		= series.group('ext')
					fmt_epno, epno = formatEpisodeNumbers(series)
					if lastseries != seriesname:
						logger.debug('Processing Series: %s' % seriesname)
						if args[0].lower() == 'check' or args[0].lower() == 'missing':
							missing = checkMissing(MISSING, dir_list, tvdb_list)
						showdata, tvdb_list = getSeries(seriesname)
						dir_list = []
					elif season == lastseason and epno == lastepno:
						if args[0].lower() == 'check' or args[0].lower() == 'dups':
							logger.debug('Possible Dups: %s - %s' % (lastfname, fname))
							last_dups = handle_dup(DUPS, last_dups, showdata, os.path.abspath(requested_dir), seriesname, season, fmt_epno, epno, epname, ext, lastext, fqname, lastfqname, fname, lastfname)

				for ep_num in epno:
					dir_entry = "%s\t%d\t%d" % (seriesname, season, ep_num)
					dir_list.append(dir_entry)

				lastseries 	= seriesname
				lastfqname 	= fqname
				lastfname 	= fname
				lastseason 	= season
				lastepno 	= epno
				lastepname 	= epname
				lastext 	= ext

	if args[0].lower() == 'check' or args[0].lower() == 'missing':
		missing = checkMissing(MISSING, dir_list, tvdb_list)

def getSeries(seriesname):
	if options.debug:
		logger.debug('getSeries - seriesname: %s' % (seriesname))
	try:
		showdata = {'seriesname': seriesname}
		showdata = showinfo.ShowDetails(showdata)
	except (ShowNotFound, InvalidType, InvalidPath, InvalidFilename,
		ConfigNotFound, ConfigValueError, DataRetrievalError) as errormsg:
		logger.warn(errormsg)
		logger.error("Skipping series: %s" % (seriesname))
		return None, None
	tvdb_list = []
	for item in showdata['episodedata']:
		if item['airdate'] is not None:
			if item['airdate'] < (datetime.today() - timedelta(days=1)):
				showid 		= showdata['showid']
				seriesname 	= showdata['seriesname']
				season 		= item['season']
				epnum 		= item['epno'][0]
				eptitle 	= item['episodename']
				airdate 	= item['airdate']
				tvdb_entry = "%s\t%d\t%d\t%s\t%s\t%s" % (seriesname, season, epnum, eptitle, airdate, showid)
				tvdb_list.append(tvdb_entry)
	tvdb_list.sort()
	return showdata, tvdb_list

def checkMissing(MISSING, dir_list, tvdb_list):
	if options.debug:
		logger.debug('checkMissing - dir_list: tvdb_list:' % ())
	if tvdb_list == None:
		return
	missing = []
	tvdb_entry = ''
	dir_entry = ''
	date_boundry = date.today() - timedelta(days=options.age_limit)
	for tvdb_entry in tvdb_list:
		found_show = False
		tvdb_seriesname, tvdb_season, tvdb_epno, tvdb_eptitle, tvdb_airdate, tvdb_showid = tvdb_entry.split("\t")
		if not options.show_specials:
			if int(tvdb_season) == 0:
				continue
		if options.age_limit_requested:
			year, month, day = time.strptime(tvdb_airdate, "%Y-%m-%d %H:%M:%S")[:3]
			if date(year, month, day) < date_boundry:
				continue
		for dir_entry in dir_list:
			dir_seriesname, dir_season, dir_epno = dir_entry.split("\t")
			if tvdb_season == dir_season and tvdb_epno == dir_epno:
				found_show = True
				continue
		if not found_show:
			missing.append(tvdb_entry)
			if options.debug:
				logger.warn(tvdb_entry)

	if len(missing) > 0:
		tvdb_seriesname, tvdb_season, tvdb_epno, tvdb_eptitle, tvdb_airdate, tvdb_showid = missing[0].split("\t")
		message = "Missing %i episode(s) - TVDB ID: %8.8s SERIES: %-25.25s" % (len(missing), tvdb_showid, tvdb_seriesname)
		logger.warn(message)
		if not options.nogui:
			mw.log(message, "red")
			missing_series = mw.insert_row(mw.treest_show_model, MISSING,
										" ",
										tvdb_showid,
										tvdb_seriesname,
										"SEA/EP",
										"TITLE",
										"AIR DATE")
	last_season = ''
	for tvdb_entry in missing:
		tvdb_seriesname, tvdb_season, tvdb_epno, tvdb_eptitle, tvdb_airdate, tvdb_showid = tvdb_entry.split("\t")
		tvdb_season = "S%2.2d" % int(tvdb_season)
		tvdb_epno = "E%2.2d" % int(tvdb_epno)
		tvdb_airdate = datetime.strptime(tvdb_airdate, "%Y-%m-%d %H:%M:%S")
		if options.nogui:
			logger.warn('%8.8s SEA: %3.3s EPNO: %3.3s TITLE: %-25.25s AIRDATE: %s' % (
																					"Missing-",
																					tvdb_season,
																					tvdb_epno,
																					tvdb_eptitle,
																					tvdb_airdate.strftime("%Y-%m-%d")))
		else:
			if last_season != tvdb_season:
				missing_season = mw.insert_row(mw.treest_show_model, missing_series, " ", " ", " ", tvdb_season)
				missing_episode = mw.insert_row(mw.treest_show_model, missing_season,
											" ",
											" ",
											" ",
											tvdb_epno,
											tvdb_eptitle,
											tvdb_airdate.strftime("%Y-%m-%d"))

		last_season = tvdb_season

def handle_dup(DUPS, last_dups, showdata, series_dir, seriesname, season, fmt_epno, epno, epname, ext, lastext, fqname, lastfqname, fname, lastfname):
	global dups_series, dups_episode

	if options.debug:
		logger.debug('handle_dup - seriesname: %s season: %s fmt_epno: %s ext: %s' % (seriesname, season, fmt_epno, ext))

	fmt_dups = '%-8.8s %-8.8s SERIES: %-25.25s SEA: %2.2s KEEPING: %-35.35s REMOVING: %-35.35s %s'

	if last_dups != seriesname:
		if not options.nogui:
			dups_series = mw.insert_row(mw.treest_show_model, DUPS,
									" ",
									" ",
									seriesname,"SEASON", "KEEPING", "REMOVING", "NEW NAME")
		last_dups = seriesname

	action = 'DRY RUN'
	# Check for multiple resolutions and non-video files
	if ext != lastext:
		message = 'Two Files Found: %s and %s - \t File: %s' % (lastext, ext, os.path.splitext(fqname)[0])
		logger.info(message)
		if not options.nogui:
			mw.log(message)
		if ext not in media_ext:
			if options.remove:
				action = 'REMOVED '
				os.remove(fqname)
		if options.nogui:
			logger.warn(fmt_dups % ("DUPS-",
								action,
								seriesname,
								season,
								lastext,
								ext,
								" "))
		else:
			dups_episode = mw.insert_row(mw.treest_show_model, dups_series,
										action,
										" ",
										" ",
										season,
										lastfname,
										fname)
		return last_dups
	elif lastext not in media_ext:
		if options.remove:
			action = 'REMOVED '
			os.remove(lastfqname)
		if options.nogui:
			logger.warn(fmt_dups % ("DUPS-",
					action,
					seriesname,
					season,
					ext,
					lastext,
					" "))
		else:
			message = 'Auto Removing: %s' % lastfqname
			logger.info(message)
			mw.log(message)
			dups_episode = mw.insert_row(mw.treest_show_model, dups_series,
								action,
								" ",
								" ",
								season,
								fname,
								lastfname)
		return last_dups
	elif lastext == 'avi' and ext == 'mkv':
		if options.remove:
			action = 'REMOVED '
			os.remove(lastfqname)
		if options.nogui:
			logger.warn(fmt_dups % ("DUPS-",
								action,
								seriesname,
								season,
								ext,
								lastext,
								" "))
		else:
			dups_episode = mw.insert_row(mw.treest_show_model, dups_series,
										action,
										" ",
										" ",
										season,
										fname,
										lastfname)
			return last_dups
		return last_dups
	# Possible Dup found
	epdata = {
			'base_dir' : series_dir,
			'seriesname': seriesname,
			'season': season,
			'epno' : fmt_epno,
			'ext' : ext
			}
	for item in showdata['episodedata']:
		for single_epno in epno:
			single_epno = [single_epno]
			if item['season'] == season and item['epno'] == single_epno:
				if 'episodedata' in epdata:
					epdata['episodedata'].append({'season' 	: item['season'],
												'epno' 		: single_epno[0],
												'episodename' 	: item['episodename'],
												'airdate'	: item['airdate']})
				else:
					epdata['episodedata'] = [{'season' 		: item['season'],
											'epno' 		: single_epno[0],
											'episodename' 	: item['episodename'],
											'airdate'		: item['airdate']}]
	if options.debug:
		logger.debug("epdata: %s" % epdata)
	if 'episodedata' in epdata:
		epdata['epname'] = formatEpisodeName(epdata['episodedata'], join_with = FileNames['multiep_join_name_with'])
		if epdata['epname'] == epname:
			message = "%-15s Season %-2s  Keeping: %-40s Removing: %s" % (seriesname, season, fname, lastfname)
			logger.info(message)
			if not options.nogui:
				mw.log(message)
			if options.remove:
				try:
					os.remove(lastfqname)
					action = 'REMOVED '
				except OSError, exc:
					logger.warning('Delete Failed: %s' % exc)
			if not options.nogui:
				dups_episode = mw.insert_row(mw.treest_show_model, dups_series,
											action,
											" ",
											" ",
											season,
											fname,
											lastfname)
	elif epdata['epname'] == lastepname:
		message = "%-15s Season %-2s  Keeping: %-40s Removing: %s" % (seriesname, season, lastfname, fname)
		logger.info(message)
		if not options.nogui:
			mw.log(message)
		if options.remove:
			try:
				os.remove(fqname)
				action = 'REMOVED '
			except OSError, exc:
				logger.warning('Delete Failed: %s' % exc)
		if not options.nogui:
			dups_episode = mw.insert_row(mw.treest_show_model, dups_series,
										action,
										" ",
										" ",
										season,
										lastfname,
										fname)
		else:
			new_name = FileNames['std_epname'] % epdata
			message = "%-15s Season %-2s Renaming: %-40s Removing %-40s New Name: %-40s" % (seriesname, season, lastfname, fname, new_name)
			logger.info(message)
			if not options.nogui:
				mw.log(message)
			if options.remove:
				new_name = FileNames['std_fqn'] % epdata
				try:
					os.rename(lastfqname, new_name)
				except OSError, exc:
					logger.warning('Rename Failed: %s' % exc)
				try:
					os.remove(fqname)
					action = 'REMOVED '
				except OSError, exc:
					logger.warning('Rename Failed: %s' % exc)
			if not options.nogui:
				dups_episode = mw.insert_row(mw.treest_show_model, dups_series,
										action,
										" ",
										" ",
										season,
										lastfname,
										fname,
										new_name)
	else:
		message = "Possible Dup: UNKNOWN\t%s\t%s" % (lastfqname, fqname)
		logger.info(message)
		if not options.nogui:
			mw.log(message)
		message = 'NO ACTION: Unable to determine proper name:'
		logger.info(message)
		if not options.nogui:
			mw.log(message)

def formatEpisodeNumbers(series):
	if options.debug:
		logger.debug('formatEpisodeNumbers - series: %s' % (series))
	"""Format episode number(s) into string, using configured values
	"""
	namedgroups = series.groupdict().keys()
	if 'episodenumber1' in namedgroups:
		# Multiple episodes, have episodenumber1 or 2 etc
		epno = []
		for cur in namedgroups:
			epnomatch = re.match('episodenumber(\d+)', cur)
			if epnomatch:
				epno.append(int(series.group(cur)))
			epno.sort()
	elif 'episodenumberstart' in namedgroups:
		# Multiple episodes, regex specifies start and end number
		start = int(series.group('episodenumberstart'))
		end = int(series.group('episodenumberend'))
		if start > end:
			# Swap start and end
			start, end = end, start
		epno = range(start, end + 1)

	elif 'episodenumber' in namedgroups:
		epno = [int(series.group('episodenumber')), ]

	if len(epno) == 1:
		fmt_epno = FileNames['episode_single'] % epno[0]
	else:
		fmt_epno = FileNames['episode_separator'].join(
													FileNames['episode_single'] % x for x in epno)

	return fmt_epno, epno

def formatEpisodeName(epdata, join_with):
	if options.debug:
		logger.debug('formatEpisodeName - epdata: %s' % (epdata))
	"""Takes a list of episode names, formats them into a string.
	If two names are supplied, such as "Pilot (1)" and "Pilot (2)", the
	returned string will be "Pilot (1-2)"

	If two different episode names are found, such as "The first", and
	"Something else" it will return "The first, Something else"
	"""

	names = []
	for nameentry in epdata:
		newname = nameentry['episodename']
		newname = unicodedata.normalize('NFKD', newname).encode('ascii','ignore')
		newname = newname.replace("&amp;", "&").replace("/", "_")
		names.append(newname)
		if options.debug:
			logger.debug('EP Name: %s' % nameentry['episodename'])

	if len(names) == 0:
		return "NOT FOUND IN TVDB"

	if len(names) == 1:
		return names[0]

	found_names = []
	numbers = []

	for cname in names:
		number = re.match("(.*) \(([0-9]+)\)$", cname)
		if number:
			epname, epno = number.group(1), number.group(2)
			if len(found_names) > 0 and epname not in found_names:
				return join_with.join(names)
			found_names.append(epname)
			numbers.append(int(epno))
		else:
			# An episode didn't match
			return join_with.join(names)

	names = []
	start, end = min(numbers), max(numbers)
	names.append("%s (%d-%d)" % (found_names[0], start, end))
	return join_with.join(names)

if __name__ == "__main__":

	opt_sel = 0
	if options.debug:
		logger.setLevel(logging.DEBUG)
		fh.setLevel(logging.DEBUG)
		ch.setLevel(logging.DEBUG)
		opt_sel = opt_sel + 1
	if options.error:
		logger.setLevel(logging.ERROR)
		fh.setLevel(logging.ERROR)
		ch.setLevel(logging.ERROR)
		opt_sel = opt_sel + 1
	if options.quiet:
		logger.setLevel(logging.WARNING)
		fh.setLevel(logging.WARNING)
		ch.setLevel(logging.WARNING)
		opt_sel = opt_sel + 1
	if options.verbose:
		logger.setLevel(logging.DEBUG)
		fh.setLevel(logging.DEBUG)
		ch.setLevel(logging.DEBUG)
		opt_sel = opt_sel + 1

	logger.debug("Parsed command line options: %r" % options)
	logger.debug("Parsed arguments: %r" % args)
	if options.debug:
		logger.debug('Number of output options selected: %s' % (opt_sel))

	if opt_sel > 1:
		parser.error("Confliting Reporting Options Requested? Reconsider your options!")
		sys.exit(1)

	series_functions= ['check', 'missing', 'rename', 'dups']

	if len(args) == 0:
		args = ['check']

	if args[0] not in series_functions:
		logger.error('Invalid Option Requested: %r' % args)
		sys.exit(1)

	if options.requested_dir == "None":
		if len(args) > 1:
			options.requested_dir = args[1]
		else:
			logger.info('Missing Scan Starting Point (Input Directory), Using Default: %r' % series_dir)
			options.requested_dir = series_dir

	if os.path.exists(exclude_extras):
		with open(exclude_extras, "r") as excludes:
			for line in excludes.readlines():
				exclude_list.append(line[0:(len(line)-1)])
	else:
		logger.warn("Extras Exclude File Missing: %r" % exclude_extras)

	if not options.no_excludes:
		if os.path.exists(exclude_series):
			with open(exclude_series, "r") as excludes:
				for line in excludes.readlines():
					exclude_list.append(line[0:(len(line)-1)])
	else:
		logger.warn("Series Exclude File Missing: %r" % exclude_series)

	showinfo 	= SeriesInfo()

	if not options.nogui:
		mw = SeriesMain()

	check_dir(options.requested_dir)

	if not options.nogui:
		gtk.main()
