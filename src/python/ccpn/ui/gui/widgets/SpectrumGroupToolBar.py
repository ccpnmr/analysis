"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-10 10:02:29 +0100 (Mon, April 10, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtCore, QtGui
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ToolBar import ToolBar
from functools import partial
from ccpn.ui.gui.widgets.Menu import Menu

class SpectrumGroupToolBar(ToolBar):
  def __init__(self, parent=None, spectrumDisplay=None, **kwds):
    ToolBar.__init__(self, parent=parent, **kwds)
    self.spectrumDisplay = spectrumDisplay
    self._project = self.spectrumDisplay.project
    self._spectrumGroups = []


  def _addAction(self, spectrumGroup):
    if spectrumGroup not in self._spectrumGroups:
      self._spectrumGroups.append(spectrumGroup)

      action = self.addAction(spectrumGroup.pid, partial(self._toggleSpectrumGroup, spectrumGroup))
      action.setCheckable(True)
      action.setChecked(True)
      action.setToolTip(spectrumGroup.name)
      self._setupButton(action, spectrumGroup)
      # self._setupContextMenu(action, spectrumGroup)

  def _setupButton(self, action, spectrumGroup):
      widget = self.widgetForAction(action)
      widget.setIconSize(QtCore.QSize(120, 10))
      widget.setFixedSize(75, 30)
      # widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
      # widget.customContextMenuRequested.connect(self._onContextMenu)

  def mousePressEvent(self, event:QtGui.QMouseEvent):
    """
    Re-implementation of the Toolbar mouse event so a right mouse context menu can be raised.
    """
    if event.button() == QtCore.Qt.RightButton:
      button = self.childAt(event.pos())
      sg = self._project.getByPid(button.text())
      if sg is not None:
        if len(button.actions())>0:
          menu = self._setupContextMenu(button.actions()[0], sg)
          if menu:
            menu.move(event.globalPos().x(), event.globalPos().y() + 10)
            menu.exec()


  def _setupContextMenu(self, action, spectrumGroup):
    print('action -> %s , spectrumGroup-> %s ' %(action, spectrumGroup))

    popMenu = Menu('',self)
    removeAction = popMenu.addAction('Remove', partial(self._deleteSpectrumGroup, action, spectrumGroup))
    peakListAction = popMenu.addAction('PeakLists')
    peakListAction.setCheckable(True)
    peakListAction.toggled.connect(partial(self._showHidePeakListView, spectrumGroup))


    return popMenu


  def _onContextMenu(self, points):
    positions = self.sender().mapToGlobal(points)
    self.popMenu.move(positions.x(), positions.y() + 10)
    self.popMenu.exec()

  def _getStrip(self):
    strips = self.spectrumDisplay.strips
    if len(strips) > 0:
      return strips[0]

  def _toggleSpectrumGroup(self, spectrumGroup):
    spectrumGroupPeakLists = [spectrum.peakLists[0] for spectrum in spectrumGroup.spectra]
    peakListViews = [peakListView for peakListView in self.spectrumDisplay.peakListViews]

    strip = self._getStrip()
    if strip is not None:
      spectrumViews = [spectrumView for spectrumView in strip.spectrumViews
                       if spectrumView.spectrum in spectrumGroup.spectra]

      widget = self.widgetForAction(self.sender())
      if widget.isChecked():
        for spectrumView in spectrumViews:
          spectrumView.setVisible(True)
          if hasattr(spectrumView, 'plot'):
            spectrumView.plot.show()
          self._showPeakList(spectrumGroupPeakLists, peakListViews)
      else:
        for spectrumView in spectrumViews:
          spectrumView.setVisible(False)
          if hasattr(spectrumView, 'plot'):
            spectrumView.plot.hide()
        self._hidePeakLists(spectrumGroupPeakLists, peakListViews)

  def _deleteSpectrumGroup(self, action, spectrumGroup):
    strip = self._getStrip()
    if strip is not None:
      self.removeAction(action)
      for spectrumView in strip.spectrumViews:
        if spectrumView.spectrum in spectrumGroup.spectra:
          spectrumView.delete()
    if spectrumGroup in self._spectrumGroups:
      self._spectrumGroups.remove(spectrumGroup)
    if len(strip.spectra)==0:
      self.spectrumDisplay._closeModule()

  def _showHidePeakListView(self, spectrumGroup):
    print('_showHidePeakListView, action -> %s , spectrumGroup-> %s ' % (self.sender(), spectrumGroup))

    spectrumGroupPeakLists = [spectrum.peakLists[0] for spectrum in spectrumGroup.spectra]
    peakListViews = [peakListView for peakListView in self.spectrumDisplay.peakListViews]
    for plV in peakListViews:
      if plV.isVisible():
        plV.setVisible(False)
      else:
        plV.setVisible(True)
    # peakListAction= self.sender()
    # print(peakListAction.text())
    # print('BOOL ', self.sender().isChecked(), peakListViews)
    # if peakListAction.isChecked():
    # self._showPeakList(spectrumGroupPeakLists, peakListViews)
    # else:
    #   self._hidePeakLists(spectrumGroupPeakLists, peakListViews)

  def _hidePeakLists(self, spectrumGroupPeakLists, peakListViews):
    for peakList in spectrumGroupPeakLists:
      if self.spectrumDisplay is not None:
        for peakListView in peakListViews:
          if peakList == peakListView.peakList:
            peakListView.setVisible(False)

  def _showPeakList(self, spectrumGroupPeakLists, peakListViews):
    for peakList in spectrumGroupPeakLists:
      if self.spectrumDisplay is not None:
        for peakListView in peakListViews:
          if peakList == peakListView.peakList:
            peakListView.setVisible(True)



#
# class SpectrumGroupsWidget(QtGui.QWidget):
#   def __init__(self, parent=None, spectrumDisplay=None, spectrumGroup=None, **kw):
#     QtGui.QWidget.__init__(self, parent)
#
#     self.spectrumDisplay = spectrumDisplay
#     if len(spectrumDisplay.strips) > 0:
#       self.strip = spectrumDisplay.strips[0]
#
#     self.spectrumGroup = spectrumGroup
#     self.spectrumGroupButton = Button(self, text=self.spectrumGroup.id,toggle=True)
#
#     self.spectrumGroupButton.setChecked(True)
#     self.spectrumGroupButton.setMinimumSize(40,33)
#     self.spectrumGroupButton.toggled.connect(self.toggleSpectrumGroups)
#
#     self.spectrumGroupButton.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
#     self.spectrumGroupButton.customContextMenuRequested.connect(self.onContextMenu)
#
#     self.popMenu = QtGui.QMenu(self)
#     self.popMenu.addAction(QtGui.QAction('Delete',self, triggered=self.deleteSpectrumGroup))
#     self.peakListCheckBox = QtGui.QAction('PeakLists',self, checkable = True, triggered=self.showHidePeakListView)
#     self.peakListCheckBox.setChecked(True)
#     self.popMenu.addAction(self.peakListCheckBox)
#
#     self.spectrumGroupPeakLists = [spectrum.peakLists[0] for spectrum in self.spectrumGroup.spectra]
#     self.peakListViews = [peakListView for peakListView in self.spectrumDisplay.peakListViews ]
#     self.peakListViewDisplayed = [peakListView.peakList for peakListView in self.spectrumDisplay.peakListViews ]
#
#   def onContextMenu(self, points):
#     positions = self.spectrumGroupButton.mapToGlobal(points)
#     self.popMenu.move(positions.x(), positions.y() + 10)
#     self.popMenu.exec()
#
#   def toggleSpectrumGroups(self):
#     if self.strip is not None:
#       spectrumViews = [spectrumView for spectrumView in self.strip.spectrumViews
#                        if spectrumView.spectrum in self.spectrumGroup.spectra]
#
#       if self.spectrumGroupButton.isChecked():
#         for spectrumView in spectrumViews:
#           spectrumView.setVisible(True)
#           if hasattr(spectrumView, 'plot'):
#             spectrumView.plot.show()
#         self.showPeakList()
#
#       else:
#         for spectrumView in spectrumViews:
#           spectrumView.setVisible(False)
#           if hasattr(spectrumView, 'plot'):
#             spectrumView.plot.hide()
#         self.hidePeakLists()
#
#   def deleteSpectrumGroup(self):
#     if self.strip is not None:
#       self.spectrumGroupButton.deleteLater()
#       for spectrumView in self.strip.spectrumViews:
#         if spectrumView.spectrum in self.spectrumGroup.spectra:
#           spectrumView.delete()
#
#   def showHidePeakListView(self):
#     if self.peakListCheckBox.isChecked():
#       self.showPeakList()
#     else:
#       self.hidePeakLists()
#
#   def hidePeakLists(self):
#     for peakList in self.spectrumGroupPeakLists:
#       if self.spectrumDisplay is not None:
#         for peakListView in self.spectrumDisplay.peakListViews:
#           if peakList == peakListView.peakList:
#             peakListView.setVisible(False)
#
#   def showPeakList(self):
#     for peakList in self.spectrumGroupPeakLists:
#       if self.spectrumDisplay is not None:
#         for peakListView in self.spectrumDisplay.peakListViews:
#           if peakList == peakListView.peakList:
#             peakListView.setVisible(True)