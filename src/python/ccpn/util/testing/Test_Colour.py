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
from ccpn.util.Colour import Colour

from nose.tools import raises

@raises(TypeError)
def test_color_create_blank():
  c = Colour()

def test_color_create_known_name():
  c = Colour('red')

@raises(KeyError)
def test_color_create_unknown_name():
  c = Colour('really-red')

def test_color_create_hex():
  c = Colour('#ff00ff')
  print(c.name)
  c = Colour('#FF00FFFF')
  print(c.name)

def test_color_create_rgb():
  c = Colour((255, 0, 255))
  print(c.name)
  c = Colour((255, 0, 255, 127))
  print(c.name)


