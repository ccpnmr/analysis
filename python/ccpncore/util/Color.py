"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
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
"""Color specification"""

def rgbaToHex(r, g, b, a=255):
  
  return '#' + ''.join([hex(x)[2:] for x in (r, g, b, a)])

def rgbToHex(r, g, b):

  return '#' + ''.join([hex(x)[2:] for x in (r, g, b)])
  
colorNameToHexDict = {
  'red':     '#ff0000',
  'green':   '#00ff00',
  'blue':    '#0000ff',
  'yellow':  '#ffff00',
  'magenta': '#ff00ff',
  'cyan':    '#ffff00',
}

# Note that Color strings are not re-used

class Color(str):
  """ A class to make color manipulation easier and more transparent.
      Assumes that r, g, b values are 8-bit so between 0 and 255 and have optional a.
      
  >>> c = Color('magenta')
  >>> c = Color('#ff00ff')
  >>> c = Color((255, 0, 255))
  """
  
  def __init__(self, value):
    """ value can be name or #rrggbb or #rrggbbaa or (r, g, b) or (r, g, b, a) tuple/list """
    
    if not value:
      raise Exception('not allowed blank color')
    
    if isinstance(value, str):
      value = value.lower()
      name = value
      if value[0] != '#':
        value = colorNameToHexDict[name]
        
      assert len(value) in (7, 9), 'len(value) = %d, should be 7 or 9' % len(value)
      
      r = int(value[1:3], 16)
      g = int(value[3:5], 16)
      b = int(value[5:7], 16)
      a = int(value[7:9], 16) if len(value) == 9 else 255
    else:
      assert isinstance(value, list) or isinstance(value, tuple), 'value must be list or tuple if it is not a string'
      assert len(value) in (3, 4), 'len(value) = %d, should be 3 or 4' % len(value)
      r, g, b = value[:3]
      if len(value) == 4:
        a = value[3]
        name = rgbaToHex(r, g, b, a)
      else:
        a = 255
        name = rgbToHex(r, g, b)
   
    ###str.__init__(self)
    self.r = r
    self.g = g
    self.b = b
    self.a = a
    self.name = name
    
  def rgba(self):

    return (self.r, self.g, self.b, self.a)

  def __repr__(self):

    return self.name

  def __str__(self):

    return self.__repr__()
