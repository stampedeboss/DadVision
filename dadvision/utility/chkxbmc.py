#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#####################
### Description   ###
#####################
# This script is intended for people using XBMC library function.
# There are two modes to this script to assist you in organizing your library.
# 	1)  Checks all files located in specified location.  Then returns message
#	    if this file does not exist in database.
#	2)  Checks each record in the database then looks to see if the file exists.
#
# Output could come in the following forms:
#	1) ORPHANFS ENTRY FOUND: /home/soukenka/tvshows/CSI/Season 10/CSI.S10E02.720p.HDTV.X264-DIMENSION.mkv
#	This means that there was a file located in the filesystem that was not found in the database.  This could
#	be resolved by a simple update library.  However if the file is still displayed in output with an up to date
#	library then you need to resolve whatever naming issue you are experiencing.  Many articles exists to assist
#	you in getting this into your library for example: http://wiki.xbmc.org/?title=TV_Shows
#
#	2) ORPHANDB ENTRY FOUND: /home/soukenka/downloads/torrents/tvshows/Medium/Season 4/Medium_S04E01.avi
#	This means that you probly deleted the file however it still exists in the library.  Running a clean library
#	from the settings menu usually resolves this.
#
#	3) RAR ENTRY FOUND: /home/soukenka/movies/Open.Graves.2009.DVDRip.XViD-ReenCoTRiN/rar://%2fhome%2fasoukenka%2fmovies%2fOpen%2eGraves%2e2009%2eDVDRip%2eXViD%2dReenCoTRiN%2freencitrin%2dgravecitrin%2erar/reencitrin-gravecitrin.avi
#	Was not sure how to put this problem exists that because it is a rar file there are usually several parts which cause
#	this script to have orphans.  I usually just confirm movie is in library then add it to ignore list.
#
#	4) STACKEDDB ENTRY FOUND: /home/soukenka/movies/The Lord of the Rings: The Two Towers (2002)/stack:///home/soukenka/movies/The Lord of the Rings: The Two Towers (2002)/The.Lord.Of.The.Rings.The.Two.Towers.Extended.Edition.720p.HDTV.DTS.x264-THOR.disc1.mkv , /home/soukenka/movies/The Lord of the Rings: The Two Towers (2002)/The.Lord.Of.The.Rings.The.Two.Towers.Extended.Edition.720p.HDTV.DTS.x264-THOR.disc2.mkv
#	Sometimes 2 files are stacked in the database so output is put here usually not a big deal


########################
### Author & Credits ###
########################
# written by Eric Soukenka
# any questions contact at easoukenka@gmail.com
# Some code and logic were used from
# 	http://wiki.xbmc.org/?title=Linux-Script_To_Find_Not_Scraped_Movies
# This is open source use it however you like!

#####################
### Requirements  ###
#####################
# python-pysql2  (For me I just did sudo apt-get install python-pysqlite2)
# python
# Have not tested on windows machine but should run fine.  If you have any
# issues with this or it runs successfully please let me know.

#####################
### Instructions  ###
#####################
# Setup the variables in the settings section following instructions for entries.
# Accepts 2 parameters
#       dbonly and fsonly.  They each perform what one would consider the logical choice :)


import re,sys,os
from pysqlite2 import dbapi2 as sqlite

################
### Settings ###
################
#usually just change your username here
DBLITE = "/home/xbmc/.xbmc/userdata/Database/MyVideos34.db"

#files home location
FILESHOME="/mnt/DadVision/Series/"

#this is NOT case sensitive sample will ignore all variants of sample will block sAmPLE
#sorry you need to be careful here if you put in just for instance e it will ignore all files and directories with an e so make unique!
EXECPTIONLIST=['documentaries','upcoming.movies','sample','/musicvideos','mummy','2lions-Team','DVDr-sailo','narnia','THE_DARK_KNIGHT','incomplete/']

#during our file system search we will search for all files with these extensions and see if file exists in database
VALIDEXTENSIONS= ["MKV", "AVI", "FLV", "WMV", "AAF", "3GP", "ASF", "CAM", "M2V", "SWF", "FLA", "M4V", "MOV", "MPEG", "OGG", "RM", "MP4","MPG","IFO","VOB","IMG","ISO"]

####################
### functions    ###
####################
def fileFinder(dir_name, subdir, extArray=""): #directory name to start, true/false if you want recursive, pass an array of extension if you wish to filter
    fileList = []
    try:
        for file in os.listdir(dir_name):
            try:
                dirfile = os.path.join(dir_name, file)
                if os.path.isfile(dirfile):
                    if (extArray==""):
                        fileList.append(dirfile)
                        #print "1:"+dirfile
                    else:
                        if os.path.splitext(dirfile)[1][1:].upper() in extArray:
                            fileList.append(dirfile)
                            #print "2:"+dirfile
                elif os.path.isdir(dirfile) and subdir:
                    fileList.extend(fileFinder(dirfile, subdir, extArray))
                    #print "3:"+dirfile
            except UnicodeDecodeError:
                #need to figure out how to resolve this encoding error!
                print "Internal Error!  Unicode error found with: "+file;
                pass;
        return fileList
    except OSError:
        return "0"

####################
### working code ###
####################
connection1 = sqlite.connect(DBLITE)
cursor1 = connection1.cursor()

connection2 = sqlite.connect(DBLITE)
cursor2 = connection2.cursor()

try:
    if(sys.argv[1]=="fsonly"):
        show="fsonly";
    elif(sys.argv[1]=="dbonly"):
        show="dbonly";
    else:
        show="all";
except IndexError:
    show="all"
if(show=="fsonly" or show=="all"):

    files=fileFinder(FILESHOME,True,VALIDEXTENSIONS)
    for file in files:
        label=""
        skipIt=False;
        i=0;
        trimPath,trimFilename = os.path.split(file)
        query='select strPath,strFilename from path, files where path.idPath = files.idPath and strPath="'+trimPath+'/" and strFilename="'+trimFilename+'" order by strPath, strFilename'
        cursor1.execute(query);
        for row in cursor1:
            i=i+1
            for exc in EXECPTIONLIST:
                if(re.match('.*'+exc.upper()+'.*',file.upper())):
                    skipIt=True;
                else:
                    if(skipIt!=True):
                        skipIt=False;
                    pass;
        if(i==0):
            skipIt=False;
            for exc in EXECPTIONLIST:
                if(re.match('.*'+exc.upper()+'.*',file.upper())):
                    skipIt=True;
                else:
                    if(skipIt!=True):
                        skipIt=False;
                    pass;
            if(skipIt):
                #label="SKIPPING FILE: "
                pass;
            else:
                label="ORPHANFS ENTRY FOUND: ";
                pass;
        elif(i>1):
            label="ERROR DUPLICATE DATABASE ENTRIES: "
        if(label!=""):
            print label+file

if(show=="dbonly" or show=="all"):
    query='select strPath,strFilename from path, files where path.idPath = files.idPath order by strPath, strFilename'
    cursor1.execute(query)
    for row in cursor1:
        label=""
        found=False;
        dbFile=row[0]+row[1];
        if(len(row[0]) > 3):
            files=fileFinder(row[0],False);
            for file in files:
                if(file==dbFile):
                    found=True;
            if(found):
                pass;
            else:
                skipIt=False;
                for exc in EXECPTIONLIST:
                    if(re.match('.*'+exc.upper()+'.*',dbFile.upper())):
                        skipIt=True;
                    else:
                        if(skipIt!=True):
                            skipIt=False;
                if(skipIt):
                    pass;
                else:
                    if(re.match('.*stack:\/\/.*',dbFile)):
                        print "STACKEDDB ENTRY FOUND: " +dbFile
                    elif(re.match('.*rar:\/\/.*',dbFile)):
                        print "RAR ENTRY FOUND: " +dbFile
                    else:
                        print "ORPHANDB ENTRY FOUND: "+dbFile
                pass;

print "Complete...";
