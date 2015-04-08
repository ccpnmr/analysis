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
from PyQt4 import QtGui, QtCore

from ccpnmrcore.Base import Base as GuiBase

class DropBase(GuiBase):
  
  def __init__(self, appBase, dropCallback, *args, **kw):
    
    GuiBase.__init__(self, appBase, *args, **kw)
    self.dropCallback = dropCallback
    
  def dragEnterEvent(self, event):
    event.accept()

  def dropEvent(self, event):
    event.accept()
    if isinstance(self.parent, QtGui.QGraphicsScene):
      event.ignore()
      return

    if event.mimeData().urls():
      filePaths = [url.path() for url in event.mimeData().urls()]
      self.dropCallback(filePaths)

    if event.mimeData().hasFormat('application/x-strip'):
      data = event.mimeData().data('application/x-strip')
      pidData = str(data.data(),encoding='utf-8')
      pidData = [ch for ch in pidData if 32 < ord(ch) < 127]  # strip out junk
      actualPid = ''.join(pidData)
      print('actualPid',actualPid)
      wrapperObject = self.getById(actualPid)
      print(wrapperObject, 'wrapper obj')
      self.dropCallback(wrapperObject)
    else:
      data = event.mimeData().data('application/x-qabstractitemmodeldatalist')
      pidData = str(data.data(),encoding='utf-8')
      pidData = [ch for ch in pidData if 32 < ord(ch) < 127]  # strip out junk
      actualPid = ''.join(pidData)
      wrapperObject = self.getObject(actualPid)
      print(wrapperObject, 'wrapper obj')
      self.dropCallback(wrapperObject)
      print(wrapperObject, 'wrapper obj')
