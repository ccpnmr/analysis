"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:56 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b2 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: simon1 $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtGui, QtWidgets

from ccpn.ui.gui.widgets.Menu import Menu
from ccpn.ui.gui.widgets.ToolBar import ToolBar

from functools import partial

import json
from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.ui.gui.lib.mouseEvents import getMouseEventDict


class SpectrumToolBar(ToolBar):

  def __init__(self, parent=None, widget=None, **kwds):

    ToolBar.__init__(self, parent=parent, **kwds)
    self.widget = widget
    self.parent = parent
    self.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)

    # this is in the wrong place
    # self.eventFilter = self._eventFilter        # ejb - only need this one now
    # self.setAcceptDrops(True)
    # self.installEventFilter(self)   # ejb
    # self.setDropEventCallback(None)

  def mousePressEvent(self, event:QtGui.QMouseEvent):
    """
    Re-implementation of the Toolbar mouse event so a right mouse context menu can be raised.
    """
    if event.button() == QtCore.Qt.RightButton:
      button = self.childAt(event.pos())
      menu = self._createContextMenu(button)
      if menu:
        menu.move(event.globalPos().x(), event.globalPos().y() + 10)
        menu.exec()

  def _createContextMenu(self, button:QtWidgets.QToolButton):
    """
    Creates a context menu containing a command to delete the spectrum from the display and its
    button from the toolbar.
    """
    if not button:
      return None
    contextMenu = Menu('', self, isFloatWidget=True)
    peakListViews = self.widget.peakListViews
    action = button.actions()[0]
    keys = [key for key, value in self.widget.spectrumActionDict.items() if value is action]
    if not keys: # if you click on >> button which shows more spectra
      return None
    key = keys[0]
    allPlAction = contextMenu.addAction('Show All PL', partial(self._allPeakLists, contextMenu, button))
    noPlAction = contextMenu.addAction('Hide All PL', partial(self._noPeakLists, contextMenu, button))

    for peakListView in peakListViews:
      if peakListView.spectrumView._apiDataSource == key:
        action = contextMenu.addAction(peakListView.peakList.id)
        action.setCheckable(True)
        if peakListView.isVisible():
          action.setChecked(True)
        # else:
        #   allPlAction.setChecked(False)
        action.toggled.connect(peakListView.setVisible)
    contextMenu.addAction('Remove SP', partial(self._removeSpectrum, button))
    return contextMenu

  def _allPeakLists(self, contextMenu, button):
    key = [key for key, value in self.widget.spectrumActionDict.items() if value == button.actions()[0]][0]
    for peakListView in self.widget.peakListViews:
      if peakListView.spectrumView._apiDataSource == key:
        for action in contextMenu.actions():
          if action is not self.sender():
            if not action.isChecked():
              action.setChecked(True)
              action.toggled.connect(peakListView.setVisible)

  def _noPeakLists(self, contextMenu, button):
    key = [key for key, value in self.widget.spectrumActionDict.items() if value == button.actions()[0]][0]
    for peakListView in self.widget.peakListViews:
      if peakListView.spectrumView._apiDataSource == key:
        for action in contextMenu.actions():
          if action is not self.sender():
            if action.isChecked():
              action.setChecked(False)
              action.toggled.connect(peakListView.setVisible)

  def _removeSpectrum(self, button:QtWidgets.QToolButton):
    """
    Removes the spectrum from the display and its button from the toolbar.
    """

    # remove the item from the toolbar
    self.removeAction(button.actions()[0])

    # and delete the spectrumView from the V2
    key = [key for key, value in self.widget.spectrumActionDict.items() if value == button.actions()[0]][0]
    stripUpdateList = []
    for spectrumView in self.widget.spectrumViews:
      if spectrumView._apiDataSource == key:
        stripUpdateList.append(spectrumView.strip)

        # this spawns the creation of all orderedSpectra
        # should be done on loading though
        spectrumView.strip.orderedSpectra()

    for spectrumView in self.widget.spectrumViews:
      if spectrumView._apiDataSource == key:

        # delete the spectrumView
        try:
          # spectrumView._wrappedData.spectrumView.delete()
          spectrumView.delete()
        except Exception as es:
          pass

    for st in stripUpdateList:
      st.removeSpectrumView(None)

  def _mousePressEvent(self, event:QtGui.QMouseEvent):
    """
    Re-implementation of the mouse press event to enable a NmrResidue label to be dragged as a json object
    containing its id and a modifier key to encode the direction to drop the strip.
    """
    event.accept()
    mimeData = QtCore.QMimeData()
    # create the dataDict
    dataDict = {self._dragKey:self.text()}
    # update the dataDict with all mouseEvents
    dataDict.update(getMouseEventDict(event))
    # convert into json
    itemData = json.dumps(dataDict)
    mimeData.setData(DropBase.JSONDATA, self.text())
    mimeData.setText(itemData)
    drag = QtGui.QDrag(self)
    drag.setMimeData(mimeData)

    pixmap = QtGui.QPixmap.grabWidget(self)     # ejb - set the pixmap to the image of the label
    painter = QtGui.QPainter(pixmap)            #       replaces the block text
    painter.setCompositionMode(painter.CompositionMode_DestinationIn)
    painter.fillRect(pixmap.rect(), QtGui.QColor(0, 0, 0, 240))
    painter.end()
    drag.setPixmap(pixmap)
    drag.setHotSpot(event.pos())

    drag.start(QtCore.Qt.MoveAction)
    # if drag.exec_(QtCore.Qt.MoveAction | QtCore.Qt.CopyAction, QtCore.Qt.CopyAction) == QtCore.Qt.MoveAction:
    #     pass
    # else:
    #   self.show()

  def _eventFilter(self, obj, event):
    """
    Replace all the events with a single filter process
    Not sure if this is the best solution, but doesn't interfere with _processDroppedItems
    and allows changing of the cursor - ejb
    """
    if event.type() == QtCore.QEvent.MouseButtonPress:
      self._mousePressEvent(event)                      # call the standard mouse event
      return True

    if event.type() == QtCore.QEvent.DragEnter:
      self._source = event.source()
      try:

        # need to change this to the button

        if isinstance(obj,SpectrumToolBar) and self._source != self:
          mime = event.mimeData().text()
          dataItem = json.loads(mime)
          if 'text' in dataItem and dataItem['text'].startswith('NR'):
          # only test NmrResidues
          # print('>>>DragEnterFilter %s' % dataItem['text'])
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.DragCopyCursor)
      finally:
        event.accept()
        return True

    if event.type() == QtCore.QEvent.DragLeave:
      QtWidgets.QApplication.restoreOverrideCursor()
      # print('>>>DragLeaveFilter')
      event.accept()
      return True

    if event.type() == QtCore.QEvent.Leave:
      QtWidgets.QApplication.restoreOverrideCursor()
      # print('>>>DragLeaveFilter')
      event.accept()
      return True

    if event.type() == QtCore.QEvent.MouseMove:
      if not isinstance(obj,SpectrumToolBar):
        QtWidgets.QApplication.restoreOverrideCursor()
        event.accept()
        return True

    if event.type() == QtCore.QEvent.Drop:
      QtWidgets.QApplication.restoreOverrideCursor()
      # print(">>>DropFilter")
      event.ignore()
      # no return True needed, so BackboneAssignment._processDroppedItem still fires

    return super(SpectrumToolBar, self).eventFilter(obj,event)    # do the rest
