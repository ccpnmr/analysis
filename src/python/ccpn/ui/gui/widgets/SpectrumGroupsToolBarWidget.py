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
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Button import Button


class SpectrumGroupsToolBar(QtGui.QToolBar, Base):
  def __init__(self, parent=None, project=None, strip=None, spectrumGroupPid=None, **kw):
    QtGui.QWidget.__init__(self, parent)
    Base.__init__(self, **kw)

    spectrumGroupButton = SpectrumGroupsWidget(self, project=project, strip=strip, spectrumGroupPid=spectrumGroupPid)
    self.addWidget(spectrumGroupButton)

class SpectrumGroupsWidget(QtGui.QWidget):
  def __init__(self, parent=None, project=None, strip=None, spectrumGroupPid=None, **kw):
    QtGui.QWidget.__init__(self, parent)
    self.project = project
    self.strip = strip
    self.setColours()
    self.spectrumGroup = self.project.getByPid(spectrumGroupPid)
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
    self.peakListViews = [peakListView for peakListView in self.strip.spectrumDisplay.peakListViews ]
    self.peakListViewDisplayed = [peakListView.peakList for peakListView in self.strip.spectrumDisplay.peakListViews ]

  def onContextMenu(self, point):
    self.popMenu.exec_(self.spectrumGroupButton.mapToGlobal(point))

  def toggleSpectrumGroups(self):
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
      for peakListView in self.strip.spectrumDisplay.peakListViews:
        if peakList == peakListView.peakList:
          peakListView.setVisible(False)

  def showPeakList(self):
    for peakList in self.spectrumGroupPeakLists:
      for peakListView in self.strip.spectrumDisplay.peakListViews:
        if peakList == peakListView.peakList:
          peakListView.setVisible(True)

  def setColours(self):

    self.colourScheme = self.project._appBase.colourScheme
    if self.colourScheme == 'dark':
      self.setStyleSheet("""
                      Button::checked {background-color: #020F31;}
                      Button {background-color: #2a3358; }
                      """)
    else:
      self.setStyleSheet("""
                      Button::checked {background-color: #bd8413;}
                      Button {background-color: #fbf4cc; border: 1px solid  #bd8413; color: #122043}
                      """)
