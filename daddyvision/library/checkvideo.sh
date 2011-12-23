#!/bin/bash

FFMPEG="/bin/ffmpeg"
LIST=`find | grep \.avi$`

for i in $LIST; do
	echo $i
    OUTP="$i.txt"
    OUTP_OK="$i.txt.ok"
    TMP_OUTP="$i.tmp"
    if [ -f "$OUTP" -o -f "$OUTP_OK" ] ; then
	echo Skipping "$i"
    else
	echo Checking "$i"...
	RESULT="bad"
	"$FFMPEG" -v 5 -i "$i" -f null - 2> "$TMP_OUTP" && \
	    mv "$TMP_OUTP" "$OUTP" && \
	    RESULT=`grep -v "\(frame\)\|\(Press\)" "$OUTP" | grep "\["`
	if [ -z "$RESULT" ] ; then
	    mv "$OUTP" "$OUTP_OK"
	fi
    fi
done
