#!/usr/bin/python -u
#
# Interfaces for sans parsers.
#
# All callbacks can return True to stop the parser.
# File pointer remains at the start of next token when that happens.
# Callbacks must return False to keep the parser going.
#
# Content handler ones simply raise "Abstract method called"
# exception (this is good enough).
#
import sys

class ErrorHandler :
    def fatalError( self, line, msg ) :
        sys.stderr.write("critical parse error in line %s: %s\n" % (line, msg))
    def error( self, line, msg ) :
        sys.stderr.write("parse error in line %s : %s\n" % (line, msg))
        return True
    def warning( self, line, msg ) :
        sys.stderr.write("parser warning in line %s : %s\n" % (line, msg))
        return True

#
# This content handler returns tag/value pair in one callback
# (for both loop and free tags)
#
class ContentHandler :
    def startData( self, line, name ) :
        raise Exception( "Abstract method called" )
    def endData( self, line, name ) :
        raise Exception( "Abstract method called" )
    def startSaveFrame( self, line, name ) :
        raise Exception( "Abstract method called" )
    def startSaveframe( self, line, name ) :
        return self.startSaveFrame( line, name )
    def endSaveFrame( self, line, name ) :
        raise Exception( "Abstract method called" )
    def endSaveframe( self, line, name ) :
        return self.endSaveFrame( line, name )
    def startLoop( self, line ) :
        raise Exception( "Abstract method called" )
    def endLoop( self, line ) :
        raise Exception( "Abstract method called" )
    def comment( self, line, text ) :
        raise Exception( "Abstract method called" )
    def data( self, tag, tagline, val, valline, delim, inloop ) :
        raise Exception( "Abstract method called" )

#
# This content handler returns tag & value in separate callbacks
#
class ContentHandler2 :
    def startData( self, line, name ) :
        raise Exception( "Abstract method called" )
    def endData( self, line, name ) :
        raise Exception( "Abstract method called" )
    def startSaveFrame( self, line, name ) :
        raise Exception( "Abstract method called" )
    def startSaveframe( self, line, name ) :
        return self.startSaveFrame( line, name )
    def endSaveFrame( self, line, name ) :
        raise Exception( "Abstract method called" )
    def endSaveframe( self, line, name ) :
        return self.endSaveFrame( line, name )
    def startLoop( self, line ) :
        raise Exception( "Abstract method called" )
    def endLoop( self, line ) :
        raise Exception( "Abstract method called" )
    def comment( self, line, text ) :
        raise Exception( "Abstract method called" )
    def tag( self, line, tag ) :
        raise Exception( "Abstract method called" )
    def value( self, line, val, delim ) :
        raise Exception( "Abstract method called" )
