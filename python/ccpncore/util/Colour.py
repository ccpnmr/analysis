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
"""Color specification"""

from collections import OrderedDict

def rgbaToHex(r, g, b, a=255):
  
  return '#' + ''.join([hex(x)[2:] for x in (r, g, b, a)])

def rgbToHex(r, g, b):

  return '#' + ''.join([hex(x)[2:] for x in (r, g, b)])

def hexToRgb(hex):
  hex = hex.lstrip('#')
  lv = len(hex)
  return tuple(int(hex[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

  

colourNameToHexDict = {
  'red':     '#ff0000',
  'green':   '#00ff00',
  'blue':    '#0000ff',
  'yellow':  '#ffff00',
  'magenta': '#ff00ff',
  'cyan':    '#ffff00',
}

spectrumColours = OrderedDict([('#cb1400','red'),
                                ('#318290','pastel blue'),
                                ('#fe6c11','orange'),
                                ('#3a4e5c','dark grey'),
                                ('#ecfc00','yellow'),
                                ('#933355','midnight blue'),
                                ('#80ff00','seashell'),
                                ('#5846d6','purple'),
                                ('#df2950','pastel pink'),
                                ('#097a27','pastel green'),
                                ('#d231cb','pink'),
                                ('#d24c23','dark orange'),
                                ('#4f9caa','light pastel blue'),
                                ('#ff932e','light pastel orange'),
                                ('#ffff5a','light yellow'),
                                ('#2d5175','mid blue'),
                                ('#d8e1cf','light seashell'),
                                ('#95eff','lilac'),
                                ('#f9609c','mid pink'),
                                ('#50ae56','mid green'),
                                ('#ff8eff','light pink'),
                                ('#3fe945','light green')])

spectrumHexColours = tuple(spectrumColours.keys())

# Note that Colour strings are not re-used

class Colour(str):
  """ A class to make colour manipulation easier and more transparent.
      Assumes that r, g, b values are 8-bit so between 0 and 255 and have optional a.
      
  >>> c = Colour('magenta')
  >>> c = Colour('#ff00ff')
  >>> c = Colour((255, 0, 255))
  """
  
  def __init__(self, value):
    """ value can be name or #rrggbb or #rrggbbaa or (r, g, b) or (r, g, b, a) tuple/list """
    
    if not value:
      raise Exception('not allowed blank colour')
    
    if isinstance(value, str):
      value = value.lower()
      name = value
      if value[0] != '#':
        value = colourNameToHexDict[name]
        
      assert len(value) in (7, 9), 'len(value) = %d, should be 7 or 9' % len(value)
      
      r = int(value[1:3], 16)
      g = int(value[3:5], 16)
      b = int(value[5:7], 16)
      a = int(value[7:9], 16) if len(value) == 9 else 255
    else:
      assert isinstance(value, list) or isinstance(value, tuple), 'value must be list or tuple if it is not a string, was %s' % (value,)
      assert len(value) in (3, 4), 'value=%s, len(value) = %d, should be 3 or 4' % (value,len(value))
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
    """Returns 4-tuple of (r, g, b, a) where each one is in range 0 to 255"""

    return (self.r, self.g, self.b, self.a)
    
  def scaledRgba(self):
    """Returns 4-tuple of (r, g, b, a) where each one is in range 0.0 to 1.0"""

    return (self.r / 255.0, self.g / 255.0, self.b / 255.0, self.a / 255.0)

  def hex(self):

    return '#' + ''.join([hex(x)[2:] for x in (self.r, self.g, self.b)])

  def __repr__(self):

    return self.name

  def __str__(self):

    return self.__repr__()

def rgba(value):
  
  return Colour(value).rgba()
  
def scaledRgba(value):

  return Colour(value).scaledRgba()

def hex(value):

  return Colour(value).hex()
