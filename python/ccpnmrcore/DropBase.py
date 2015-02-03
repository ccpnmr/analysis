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

    else:
      data = (event.mimeData().retrieveData('application/x-qabstractitemmodeldatalist', str))
      print('RECEIVED mimeData: "%s"' % data)
      pidData = str(data.data(),encoding='utf-8')
      WHITESPACE_AND_NULL = ['\x01', '\x00', '\n','\x1e','\x02','\x03','\x04','\x0e','\x12', '\x0c', '\x05', '\x10', '\x14', '\x1c', '\x08']
      pidData2 = [s for s in pidData if s not in WHITESPACE_AND_NULL]
      actualPid = ''.join(map(str, pidData2))
      wrapperObject = self.getObject(actualPid)
      self.dropCallback(wrapperObject)
