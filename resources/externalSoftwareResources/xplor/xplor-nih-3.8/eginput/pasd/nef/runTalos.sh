#!/bin/sh

nefFilename=$1
TALOSN=/Users/Eliza/Projects/talosn/talosn
numProcessors=1 # I found that a value > 1 causes crashes, irreproducibility

if [ ! -f "$1" ]; then
    echo "usage: $0 <file.nef>"
    echo "  creates file_new.nef"
    exit 1
fi

if [ -z "`which $TALOSN 2>/dev/null`" ]; then
    echo "Error: Could not find program named $TALOSN"
    exit 1
fi

#Q: H or HN for amide proteins? - doesn't seem to matter

./genTalosNInput.py $nefFilename

#talos spits messages to stderr - redirect to stdout
$TALOSN -in ${nefFilename}.tab -np $numProcessors 2>&1

./talosToNEF.py $nefFilename pred.tab predAll.tab         
