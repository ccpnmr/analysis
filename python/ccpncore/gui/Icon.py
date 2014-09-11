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
from PySide import QtGui, QtCore

import os

ICON_DIR = os.path.dirname(__file__) 

class Icon(QtGui.QIcon):

  def __init__(self, image=None, color=None):
    
    assert image or color
    
    if color:
      image = QtGui.QPixmap(10, 10)
      painter = QtGui.QPainter(image)
      
      if isinstance(color, str):
        color = QtGui.QColor(color[:7])
        image.fill(color)
      
      elif isinstance(color, (tuple, list)):
        image.fill(color[0][:7])
        dx = 22.0/float(len(color))
        
        x = dx
        for i, c in enumerate(color[1:]):
          col = QtGui.QColor(c[:7])
          painter.setPen(col)
          painter.setBrush(col)
          painter.drawRect(x,0,x+dx,21)
          x += dx
        
      else:  
        image.fill(color)
      
      painter.setPen(QtGui.QColor('#000000'))
      painter.setBrush(QtGui.QBrush())
      painter.drawRect(0,0,21,21)
      painter.end()
    
    elif not isinstance(image, QtGui.QIcon):
      if not os.path.exists(image):
        image = os.path.join(ICON_DIR, image)
      
    QtGui.QIcon.__init__(self, image)

if __name__ == '__main__':

  from ccpncore.gui.Button import Button
  from ccpncore.gui.Application import TestApplication

  app = TestApplication()

  window = QtGui.QWidget()
  
  def click():
    print("Clicked")

  button = Button(window, icon='icons/system-help.png', callback=click,
                  tipText='An icon button', grid=(0, 3))

  window.show()
  
  app.start()
