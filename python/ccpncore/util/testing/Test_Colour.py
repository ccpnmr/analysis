"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
from ccpncore.util.Color import Color

from nose.tools import raises

@raises(TypeError)
def test_color_create_blank():
  c = Color()

def test_color_create_known_name():
  c = Color('red')

@raises(KeyError)
def test_color_create_unknown_name():
  c = Color('really-red')

def test_color_create_hex():
  c = Color('#ff00ff')
  print(c.name)
  c = Color('#FF00FFFF')
  print(c.name)

def test_color_create_rgb():
  c = Color((255, 0, 255))
  print(c.name)
  c = Color((255, 0, 255, 127))
  print(c.name)


