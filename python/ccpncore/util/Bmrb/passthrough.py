#!/usr/bin/python -u
#
#

from __future__ import absolute_import

import sys
import os

# SANS_PATH = os.path.realpath( os.path.join( os.path.split( __file__ )[0], "../" ) )
# sys.path.append( SANS_PATH )
# import sans

from ccpncore.util.Bmrb import sans

class Handler( sans.ContentHandler ) :
    def startData( self, line, name ) :
        return False
    def endData( self, line, name ) :
        pass
    def startSaveframe( self, line, name ) :
        return False
    def endSaveframe( self, line, name ) :
        return False
    def startLoop( self, line ) :
        return False
    def endLoop( self, line ) :
        return False
    def comment( self, line, text ) :
        return False
    def data( self, tag, tagline, val, valline, delim, inloop ) :
        return False


if __name__ == "__main__" :
    if len( sys.argv ) > 1 : 
        infile = open( sys.argv[1], "rb" )
    else : infile = sys.stdin
    l = sans.STARLexer( infile )
    e = sans.ErrorHandler()
    c = Handler()
    p = sans.parser( l, c, e )
    p.parse()
    if len( sys.argv ) > 1 : infile.close()
