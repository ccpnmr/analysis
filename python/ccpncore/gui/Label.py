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

  def __init__(self, parent, text='', pid = None, textColor=None, dragDrop=False, textSize=None, **kw):

    QtGui.QLabel.__init__(self, text, parent)
    Base.__init__(self, **kw)
    self.dragDrop = dragDrop
    self.pid = pid
    self.setAcceptDrops(True)

    if textColor:
      self.setStyleSheet('QLabel {color: %s; font-size: 30pt; font-weight: bold}' % textColor)
    if textSize and textColor:
      self.setStyleSheet('QLabel {font-size: %s;}' % textSize)
    
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
      mimeData = QtCore.QMimeData()
      mimeData.setData('application/x-strip', itemData)
      drag = QtGui.QDrag(self)
      drag.setMimeData(mimeData)

    else:
      event.ignore()
      return

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

      if event.keyboardModifiers() & QtCore.Qt.ShiftModifier:

        sinkIndex = self.parent().getById(self.pid)._wrappedData.index
        direction = 'left'

      else:

        sinkIndex = self.parent().getById(self.pid)._wrappedData.index + 1
        direction = 'right'

      if wrapperObject.pid.id == self.pid.id:
        wrapperObject.moveTo(sinkIndex)
      else:
        print('wrapperObject',wrapperObject.spinSystemLabel.text())
        self.parent().guiSpectrumDisplay.copyStrip(wrapperObject, sinkIndex)
        self.parent().guiSpectrumDisplay._appBase.current.strip = self.parent().guiSpectrumDisplay.orderedStrips[sinkIndex]
        self.parent().guiSpectrumDisplay._appBase.current.strip.spinSystemLabel.setText(wrapperObject.spinSystemLabel.text())
        newNmrResidue = self.parent().getById('NR:@.'+wrapperObject.spinSystemLabel.text()+'.')
        print(newNmrResidue)
        self.parent().guiSpectrumDisplay._appBase.current.assigner.addResidue(nmrResidue=newNmrResidue, direction=direction)
        # newHsqcPeak = self.parent().getById('NR:'+wrapperObject.spinSystemLabel.text())
        print(self.parent().guiSpectrumDisplay._appBase.mainWindow.bbModule)
        self.parent().guiSpectrumDisplay._appBase.mainWindow.bbModule.findMatchingPeaks(nmrResidue=newNmrResidue)
        self.parent().guiSpectrumDisplay._appBase.mainWindow.assigner.predictSequencePosition()
    else:
      event.acceptProposedAction()
      print(event)



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
