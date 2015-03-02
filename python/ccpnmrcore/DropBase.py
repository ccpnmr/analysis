from PySide import QtGui, QtCore

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
      data = (event.mimeData().retrieveData('application/x-strip', str))
      pidData = str(data.data(),encoding='utf-8')
      pidData = [ch for ch in pidData if 32 < ord(ch) < 127]  # strip out junk
      actualPid = ''.join(pidData)
      print('actualPid',actualPid)
      wrapperObject = self.getById(actualPid)
      print(wrapperObject, 'wrapper obj')
      # print('probablyStrip')
      self.dropCallback(wrapperObject)
    else:
      data = (event.mimeData().retrieveData('application/x-qabstractitemmodeldatalist', str))
      pidData = str(data.data(),encoding='utf-8')
      pidData = [ch for ch in pidData if 32 < ord(ch) < 127]  # strip out junk
      actualPid = ''.join(pidData)
      wrapperObject = self.getObject(actualPid)
      print(wrapperObject, 'wrapper obj')
      self.dropCallback(wrapperObject)
      print(wrapperObject, 'wrapper obj')
