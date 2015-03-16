"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================
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
    l.verbose = True
    t = Test()
    p = sans.parser( l, t, t )
    p.parse()
#
#
