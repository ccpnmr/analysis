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

class SpectrumGroupToolBar(ToolBar):
  def __init__(self, parent=None, spectrumDisplay=None, **kwds):
    ToolBar.__init__(self, parent=parent, **kwds)
    self.spectrumDisplay = spectrumDisplay
    self._spectrumGroups = []


  def _addAction(self, spectrumGroup):
    if spectrumGroup not in self._spectrumGroups:
      self._spectrumGroups.append(spectrumGroup)

      name = 'SG:\n'+ spectrumGroup.name
      action = self.addAction(name, partial(self._toggleSpectrumGroup, spectrumGroup))
      action.setCheckable(True)
      action.setChecked(True)
      action.setToolTip(spectrumGroup.name)
      self._setupButton(action, spectrumGroup)
      self._setupContextMenu(action, spectrumGroup)

  def _setupButton(self, action, spectrumGroup):
      widget = self.widgetForAction(action)
      widget.setIconSize(QtCore.QSize(120, 10))
      widget.setFixedSize(75, 30)

      widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
      widget.customContextMenuRequested.connect(self._onContextMenu)




  def _setupContextMenu(self, action, spectrumGroup):
    from ccpn.ui.gui.widgets.Menu import Menu
    self.popMenu = Menu('',self)
    self.popMenu.addAction('Remove', partial(self._deleteSpectrumGroup, action, spectrumGroup))

    # self.popMenu.addAction(QtGui.QAction('Delete', self, triggered=partial(self._deleteSpectrumGroup, spectrumGroup)))
    # self._peakListCheckBox = QtGui.QAction('PeakLists', self, checkable=True, triggered=self._showHidePeakListView)
    # self._peakListCheckBox.setChecked(True)
    # self.popMenu.addAction(self._peakListCheckBox)
    #
    # self._spectrumGroupPeakLists = [spectrum.peakLists[0] for spectrum in spectrumGroup.spectra]
    # self.peakListViews = [peakListView for peakListView in self.spectrumDisplay.peakListViews]
    # self.peakListViewDisplayed = [peakListView.peakList for peakListView in self.spectrumDisplay.peakListViews]

  def _onContextMenu(self, points):
    positions = self.sender().mapToGlobal(points)
    self.popMenu.move(positions.x(), positions.y() + 10)
    self.popMenu.exec()

  def _getStrip(self):
    strips = self.spectrumDisplay.strips
    if len(strips) > 0:
      return strips[0]

  def _toggleSpectrumGroup(self, spectrumGroup):

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
          self._showPeakList()
      else:
        for spectrumView in spectrumViews:
          spectrumView.setVisible(False)
          if hasattr(spectrumView, 'plot'):
            spectrumView.plot.hide()
        self._hidePeakLists()

  def _deleteSpectrumGroup(self, action, spectrumGroup):
    strip = self._getStrip()
    if strip is not None:
      print(self, self.actions())

      self.removeAction(action)
      for spectrumView in strip.spectrumViews:
        if spectrumView.spectrum in spectrumGroup.spectra:
          spectrumView.delete()

  def _showHidePeakListView(self):
    if self._peakListCheckBox.isChecked():
      self._showPeakList()
    else:
      self._hidePeakLists()

  def _hidePeakLists(self):
    for peakList in self._spectrumGroupPeakLists:
      if self.spectrumDisplay is not None:
        for peakListView in self.spectrumDisplay.peakListViews:
          if peakList == peakListView.peakList:
            peakListView.setVisible(False)

  def _showPeakList(self):
    for peakList in self._spectrumGroupPeakLists:
      if self.spectrumDisplay is not None:
        for peakListView in self.spectrumDisplay.peakListViews:
          if peakList == peakListView.peakList:
            peakListView.setVisible(True)




class SpectrumGroupsWidget(QtGui.QWidget):
  def __init__(self, parent=None, spectrumDisplay=None, spectrumGroup=None, **kw):
    QtGui.QWidget.__init__(self, parent)

    self.spectrumDisplay = spectrumDisplay
    if len(spectrumDisplay.strips) > 0:
      self.strip = spectrumDisplay.strips[0]

    self.spectrumGroup = spectrumGroup
    self.spectrumGroupButton = Button(self, text=self.spectrumGroup.id,toggle=True)

    self.spectrumGroupButton.setChecked(True)
    self.spectrumGroupButton.setMinimumSize(40,33)
    self.spectrumGroupButton.toggled.connect(self.toggleSpectrumGroups)

    self.spectrumGroupButton.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    self.spectrumGroupButton.customContextMenuRequested.connect(self.onContextMenu)

    self.popMenu = QtGui.QMenu(self)
    self.popMenu.addAction(QtGui.QAction('Delete',self, triggered=self.deleteSpectrumGroup))
    self.peakListCheckBox = QtGui.QAction('PeakLists',self, checkable = True, triggered=self.showHidePeakListView)
    self.peakListCheckBox.setChecked(True)
    self.popMenu.addAction(self.peakListCheckBox)

    self.spectrumGroupPeakLists = [spectrum.peakLists[0] for spectrum in self.spectrumGroup.spectra]
    self.peakListViews = [peakListView for peakListView in self.spectrumDisplay.peakListViews ]
    self.peakListViewDisplayed = [peakListView.peakList for peakListView in self.spectrumDisplay.peakListViews ]

  def onContextMenu(self, points):
    positions = self.spectrumGroupButton.mapToGlobal(points)
    self.popMenu.move(positions.x(), positions.y() + 10)
    self.popMenu.exec()

  def toggleSpectrumGroups(self):
    if self.strip is not None:
      spectrumViews = [spectrumView for spectrumView in self.strip.spectrumViews
                       if spectrumView.spectrum in self.spectrumGroup.spectra]

      if self.spectrumGroupButton.isChecked():
        for spectrumView in spectrumViews:
          spectrumView.setVisible(True)
          if hasattr(spectrumView, 'plot'):
            spectrumView.plot.show()
        self.showPeakList()

      else:
        for spectrumView in spectrumViews:
          spectrumView.setVisible(False)
          if hasattr(spectrumView, 'plot'):
            spectrumView.plot.hide()
        self.hidePeakLists()

  def deleteSpectrumGroup(self):
    if self.strip is not None:
      self.spectrumGroupButton.deleteLater()
      for spectrumView in self.strip.spectrumViews:
        if spectrumView.spectrum in self.spectrumGroup.spectra:
          spectrumView.delete()

  def showHidePeakListView(self):
    if self.peakListCheckBox.isChecked():
      self.showPeakList()
    else:
      self.hidePeakLists()

  def hidePeakLists(self):
    for peakList in self.spectrumGroupPeakLists:
      if self.spectrumDisplay is not None:
        for peakListView in self.spectrumDisplay.peakListViews:
          if peakList == peakListView.peakList:
            peakListView.setVisible(False)

  def showPeakList(self):
    for peakList in self.spectrumGroupPeakLists:
      if self.spectrumDisplay is not None:
        for peakListView in self.spectrumDisplay.peakListViews:
          if peakList == peakListView.peakList:
            peakListView.setVisible(True)