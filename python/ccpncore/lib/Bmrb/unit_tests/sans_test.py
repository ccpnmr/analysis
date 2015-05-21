#!/usr/bin/python -u
#

import os
import sys

sys.path.append( os.path.join(os.path.dirname(os.path.realpath(__file__)), "..") )
import sans

class Test( sans.ContentHandler, sans.ErrorHandler ) :
    def comment( self, line, text ) :
        print("Comment: %s in line %s" % (text, line))
        return False
    def startData( self, line, name ) :
        print("Start data block %s in line %s" % (name, line))
        return False
    def endData( self, line, name ) :
        print("End data block %s in line %s" % (name, line))
    def startSaveframe( self, line, name ) :
        print("Start saveframe %s in line %s" % (name, line))
        return False
    def endSaveframe( self, line, name ) :
        print("End saveframe %s in line %s" % (name, line))
        return False
    def startLoop( self, line ) :
        print("Start loop in line %s" % line)
        return False
    def endLoop( self, line ) :
        print("End loop in line %s" % line)
        return False
    def data( self, tag, tagline, val, valline, delim, inloop ) :
        print("%s tag/value: %s : %s ( %s : %s ) d %s" % ( "Loop" if inloop else "Free", tag, sans.quote( val ), tagline, valline, delim))
        return False
    def fatalError( self, line, msg ) :
        print("parse fatal error in line %s : %s" % (line, msg))
        return True
    def error( self, line, msg ) :
        print("parse error in line %s : %s" % (line, msg))
        return True
    def warning( self, line, msg ) :
        print("parse warning in line %s : %s" % (line, msg))
        return False

#
#
#
if __name__ == "__main__" :
    l = sans.STARLexer( sys.stdin )
#    l.verbose = True
    t = Test()
    p = sans.parser( l, t, t )
    p.parse()
#
#
