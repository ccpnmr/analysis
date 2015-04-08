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
Qt = QtCore.Qt

from ccpncore.gui.Base import Base

class Label(QtGui.QLabel, Base):

  def __init__(self, parent, text='', pid = None, textColor=None, dragDrop=False, **kw):

    QtGui.QLabel.__init__(self, text, parent)
    Base.__init__(self, **kw)
    self.dragDrop = dragDrop
    self.pid = pid
    self.setAcceptDrops(True)

    if textColor:
      self.setStyleSheet('QLabel {color: %s;}' % textColor)
    
  def get(self):

    return self.text()

  def set(self, text=''):

    self.setText(self.translate(text))
  #   if event.mimeData().hasUrls():
  #     event.accept()
  #   else:
  #     super(Label, self).dragEnterEvent(event)
  #

  def mousePressEvent(self, event):
    if self.dragDrop == True:
      itemData = QtCore.QByteArray(self.pid)
      # dataStream = QtCore.QDataStream(itemData, QtCore.QIODevice.WriteOnly)
      # dataStream << QtCore.QByteArray(self.labelText) << QtCore.QPoint(event.pos() - self.rect().topLeft())

      mimeData = QtCore.QMimeData()
      mimeData.setData('application/x-strip', itemData)
      # mimeData.setText(self.labelText)

      drag = QtGui.QDrag(self)
      drag.setMimeData(mimeData)
      # drag.setHotSpot(event.pos() - self.rect().topLeft())
      # drag.setPixmap(self.pixmap())]
    else:
      event.ignore()


    if drag.exec_(QtCore.Qt.MoveAction | QtCore.Qt.CopyAction, QtCore.Qt.CopyAction) == QtCore.Qt.MoveAction:
        self.close()
    else:
        self.show()

  def dragEnterEvent(self, event):
    event.accept()
  #   itemData = QtCore.QByteArray(self.pid)
  #   mimeData = QtCore.QMimeData()
  #   mimeData.setData('application/x-strip', itemData)
  #
  def dragLeaveEvent(self, event):
    event.accept()

  def dropEvent(self, event):
    if event.mimeData().hasFormat('application/x-strip'):
      data = event.mimeData().data('application/x-strip')
      pidData = str(data.data(),encoding='utf-8')
      pidData = [ch for ch in pidData if 32 < ord(ch) < 127]  # strip out junk
      actualPid = ''.join(pidData)
      wrapperObject = self.parent().getById(actualPid)

      print(wrapperObject.pid.id)
      print(self.pid.id)

      if event.keyboardModifiers() & QtCore.Qt.ShiftModifier:

        sinkIndex = self.parent().getById(self.pid)._wrappedData.index

      else:

        sinkIndex = self.parent().getById(self.pid)._wrappedData.index + 1

      if wrapperObject.pid.id == self.pid.id:
        wrapperObject.moveTo(sinkIndex)
      else:
        self.parent().guiSpectrumDisplay.copyStrip(wrapperObject, sinkIndex)
        # wrapperObject.moveTo(sinkIndex, newSpectrumDisplay=self.parent())



if __name__ == '__main__':

  from ccpncore.gui.Application import TestApplication
  from ccpncore.gui.Button import Button

  msg = 'Hello world'
  count = 0

  def func():

    global count

    count += 1
    label.set(msg + ' ' + str(count))
    print(label.get())

  app = TestApplication()
  
  window = QtGui.QWidget()
 
  label = Label(window, text=msg, textColor='red', grid=(0,0))
  button = Button(window, text='Click me', callback=func, grid=(0,1))

  window.show()

  app.start()
