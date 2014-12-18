#!/usr/bin/python -u
#
import os
import sys

sys.path.append( os.path.join(os.path.dirname(os.path.realpath(__file__)), "..") )

from sans import STARLexer
from sans import ErrorHandler, ContentHandler
from sans import cifparser
from sans import quote

class Test( ContentHandler, ErrorHandler ) :
    def comment( self, line, text ) :
        print("Comment: %s in line %s" % (text, line))
        return False
    def startData( self, line, name ) :
        print("Start data block %s in line %s" % (name, line))
        return False
    def endData( self, line, name ) :
        print("End data block %s in line %s" % (name, line))
    def startSaveFrame( self, line, name ) :
        print("Start saveframe %s in line %s" % (name, line))
        return False
    def endSaveFrame( self, line, name ) :
        print("End saveframe %s in line %s" % (name, line))
        return False
    def startLoop( self, line ) :
        print("Start loop in line %s" % line)
        return False
    def endLoop( self, line ) :
        print("End loop in line %s" % line)
        return False
    def data( self, tag, tagline, val, valline, delim, inloop ) :
        print("%s tag/value: %s : %s ( %s : %s ) d %s" % ( "Loop" if inloop else "Free", tag, quote( val ), tagline, valline, delim))
        return False
    def error( self, line, msg ) :
        print("parse error in line %s : %s" % (line, msg))
        return True
#
#
#
if __name__ == "__main__" :
    l = STARLexer( sys.stdin )
    t = Test()
    p = cifparser( l, t, t )
    p.parse()
#
#
