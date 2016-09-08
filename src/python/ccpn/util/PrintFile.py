"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2015-03-16 16:57:10 +0000 (Mon, 16 Mar 2015) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: skinnersp $"
__date__ = "$Date: 2015-03-16 16:57:10 +0000 (Mon, 16 Mar 2015) $"
__version__ = "$Revision: 8180 $"

#=========================================================================================
# Start of code
#=========================================================================================

from abc import ABC, abstractmethod

class PrintFile(ABC):
  
  def __init__(self, path, xCount=1, yCount=1, width=800, height=800):
    
    self.path = path
    self.xCount = xCount
    self.yCount = yCount
    self.width = width
    self.height = height

  def __enter__(self):
    self.fp = open(self.path, 'wt')

    return self

  def __exit__(self, *args):
    self.fp.close()

  @abstractmethod
  def startRegion(self, xOutputRegion, yOutputRegion, xNumber=0, yNumber=0):
    pass

  @abstractmethod
  def writeLine(self, x1, y1, x2, y2, colour='#000000'):
    pass

  @abstractmethod
  def writePolyline(self, polyline, colour='#000000'):
    pass

  @abstractmethod
  def writeText(self, text, x, y, colour='#000000', fontsize=10, fontfamily='Verdana'):
    pass
