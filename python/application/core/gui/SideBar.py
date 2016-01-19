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
__author__ = 'simon'

from PyQt4 import QtCore, QtGui
import pandas as pd
from ccpn import Project
# from ccpncore.gui.Button import Button
from ccpncore.util.Types import Sequence

from application.core.DropBase import DropBase
from ccpn import Spectrum
from ccpncore.util.Pid import Pid

# import sys
import os
import csv

# from ccpncore.gui.Font import Font

experimentTypeDict = {'zg':'H', 'cpmg':'T2-filtered.H', 'STD':'STD.H', 'bdwl':'Water-LOGSY.H'}



class SideBar(DropBase, QtGui.QTreeWidget):
  def __init__(self, parent=None ):
    QtGui.QTreeWidget.__init__(self, parent)


    self.setFont(QtGui.QFont('Lucida Grande', 12))
    self.header().hide()
    self.setDragEnabled(True)
    self._appBase = parent._appBase

    self.setDragDropMode(self.InternalMove)
    # self._dragroot = self.itemRootIndex()
    self.setFixedWidth(200)
    self.projectItem = QtGui.QTreeWidgetItem(self)
    self.projectItem.setText(0, "Project")
    self.projectItem.setExpanded(True)
    self.spectrumItem = QtGui.QTreeWidgetItem(self.projectItem)
    self.spectrumItem.setText(0, "Spectra")
    print(self._appBase.applicationName)
    if self._appBase.applicationName == 'Assign':


      # chainA = QtGui.QTreeWidgetItem(self.spectrumReference)
      # chainA.setText(0, 'Chain A')
      # chainB = QtGui.QTreeWidgetItem(self.spectrumReference)
      # chainB.setText(0, 'Chain B')
      # chainC = QtGui.QTreeWidgetItem(self.spectrumReference)
      # chainC.setText(0, 'Chain C')
      # self.spectrumScreening = QtGui.QTreeWidgetItem(self.projectItem)
      # self.spectrumScreening.setText(0, "Screening")
      # self.spectrumMixtures = QtGui.QTreeWidgetItem(self.projectItem)
      # self.spectrumMixtures.setText(0, "Mixtures")
      # # self.restraintsItem = QtGui.QTreeWidgetItem(self.projectItem)
      # # self.restraintsItem.setText(0, "Restraint Lists")
      # self.spectrumDeleted = QtGui.QTreeWidgetItem(self.projectItem)
      # self.spectrumDeleted.setText(0, "Deleted")
      # self.structuresItem = QtGui.QTreeWidgetItem(self.projectItem)
      # self.structuresItem.setText(0, "Structures")
      # self.samplesItem = QtGui.QTreeWidgetItem(self.projectItem)
      # self.samplesItem.setText(0, "Samples")

      self.structuresItem = QtGui.QTreeWidgetItem(self.projectItem)
      self.structuresItem.setText(0, "Structures")
      self.substancesItem = QtGui.QTreeWidgetItem(self.projectItem)
      self.substancesItem.setText(0, "Substances")
      self.notesItem = QtGui.QTreeWidgetItem(self.projectItem)
      self.notesItem.setText(0, "Notes")
      self.newNoteItem = QtGui.QTreeWidgetItem(self.notesItem)
      self.newNoteItem.setData(0, QtCore.Qt.DisplayRole, '<New Note>')

    if self._appBase.applicationName == 'Screen' :
      self.spectrumScreening = QtGui.QTreeWidgetItem(self.projectItem)
      self.spectrumScreening.setExpanded(True)
      self.spectrumScreening.setText(0, "Screening")
      self.spectrumReference = QtGui.QTreeWidgetItem(self.spectrumScreening)
      self.spectrumReference.setText(0, "Reference")
      self.spectrumReference.setExpanded(True)
      self.spectrumSamples = QtGui.QTreeWidgetItem(self.spectrumScreening)
      self.spectrumSamples.setText(0, "Samples")
      self.newSample = QtGui.QTreeWidgetItem(self.spectrumSamples)
      self.newSample.setText(0, "<New Sample>")
      self.spectrumSamples.setExpanded(True)
      # self.restraintsItem = QtGui.QTreeWidgetItem(self.projectItem)
      # self.restraintsItem.setText(0, "Restraint Lists")

    if self._appBase.applicationName == 'Metabolomics':
      self.metabolomicsTree = QtGui.QTreeWidgetItem(self.projectItem)
      self.metabolomicsTree.setExpanded(True)
      self.metabolomicsTree.setText(0, "Metabolomics")
      self.metabolomicsSamples = QtGui.QTreeWidgetItem(self.metabolomicsTree)
      self.metabolomicsSamples.setText(0, "Samples")



  def setProject(self, project:Project):
    """
    Sets the specified project as a class attribute so it can be accessed from elsewhere
    """
    self.project = project

  def addItem(self, item:QtGui.QTreeWidgetItem, data:object):
    """
    Adds a QTreeWidgetItem as a child of the item specified, which corresponds to the data object
    passed in.
    """
    newItem = QtGui.QTreeWidgetItem(item)
    newItem.setFlags(newItem.flags() & ~(QtCore.Qt.ItemIsDropEnabled))
    # newItem.setText(0, str(data.name))
    newItem.setData(0, QtCore.Qt.DisplayRole, str(data.pid))
    newItem.mousePressEvent = self.mousePressEvent
    return newItem



  def mousePressEvent(self, event):
    """
    Re-implementation of the mouse press event so right click can be used to delete items from the
    sidebar.
    """
    if event.button() == QtCore.Qt.RightButton:
      self.raiseContextMenu(event, self.itemAt(event.pos()))
    else:
      QtGui.QTreeWidget.mousePressEvent(self, event)


  def raiseContextMenu(self, event:QtGui.QMouseEvent, item:QtGui.QTreeWidgetItem):
    """
    Creates and raises a context menu enabling items to be deleted from the sidebar.
    """
    from ccpncore.gui.Menu import Menu
    contextMenu = Menu('', self, isFloatWidget=True)
    from functools import partial
    contextMenu.addAction('Delete', partial(self.removeItem, item))
    contextMenu.popup(event.globalPos())



  def removeItem(self, item:QtGui.QTreeWidgetItem):
    """
    Removes the specified item from the sidebar and the project.
    """
    import sip
    self.project.getByPid(item.data(0, QtCore.Qt.DisplayRole)).delete()
    sip.delete(item)

  def fillSideBar(self, project:Project):
    """
    Fills the sidebar with the relevant data from the project.
    """
    self.projectItem.setText(0, project.name)
    for spectrum in project.spectra:
      newItem = self.addItem(self.spectrumItem, spectrum)
      if spectrum is not None:
        for peakList in spectrum.peakLists:
          peakListItem = QtGui.QTreeWidgetItem(newItem)
          peakListItem.setText(0, peakList.pid)
        anItem = QtGui.QTreeWidgetItem(newItem)
        anItem.setText(0, '<New>')


    if self._appBase.applicationName == 'Screen' :
      # 1d
      self.onedItem = QtGui.QTreeWidgetItem(self.spectrumReference)
      self.onedItem.setText(0, "1D")
      self.stdItem = QtGui.QTreeWidgetItem(self.spectrumReference)
      self.stdItem.setText(0, "STD")
      self.logsyItem = QtGui.QTreeWidgetItem(self.spectrumReference)
      self.logsyItem.setText(0, "Water-LOGSY")
      self.t1rhoItem = QtGui.QTreeWidgetItem(self.spectrumReference)
      self.t1rhoItem.setText(0, "T1rho")


    # ### Flags
    # # set dropEnable  the item you want to move. Set dragEnable  where drop is allowed
    # self.projectItem.setFlags(self.projectItem.flags() & ~(QtCore.Qt.ItemIsDragEnabled |QtCore.Qt.ItemIsDropEnabled))
    # self.spectrumItem.setFlags(self.spectrumItem.flags() & ~(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled))
    # self.spectrumReference.setFlags(self.spectrumReference.flags()  & ~(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled))
    # self.spectrumScreening.setFlags(self.spectrumScreening.flags() & ~(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled ))
    # self.spectrumSamples.setFlags(self.spectrumSamples.flags() & ~(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled))
    # # References
    # self.onedItem.setFlags(self.onedItem.flags()  & ~(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled))
    # self.logsyItem.setFlags(self.logsyItem.flags()  & ~(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled))
    # self.t1rhoItem.setFlags(self.t1rhoItem.flags() & ~(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled))
    # self.t1rhoItem.setFlags(self.t1rhoItem.flags() & ~(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled))
    # self.stdItem.setFlags(self.stdItem.flags() & ~(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled))
    # # screening
    # self.onedItemScreening.setFlags(self.onedItemScreening.flags() & ~(QtCore.Qt.ItemIsDragEnabled))
    # self.logsyItemScreening.setFlags(self.logsyItemScreening.flags() & ~(QtCore.Qt.ItemIsDragEnabled ))
    # self.t1rhoItemScreening.setFlags(self.t1rhoItemScreening.flags() & ~(QtCore.Qt.ItemIsDragEnabled))
    # self.stdItemScreening.setFlags(self.stdItemScreening.flags() & ~(QtCore.Qt.ItemIsDragEnabled))
    # # structures, notes, deleted
    # self.structuresItem.setFlags(self.structuresItem.flags()  & ~(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled))
    # self.notesItem.setFlags(self.notesItem.flags()  & ~(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled))
    # self.spectrumDeleted.setFlags(self.spectrumDeleted.flags() & ~(QtCore.Qt.ItemIsDragEnabled ))

  def clearSideBar(self):
    """
    Clears all data from the sidebar.
    """
    self.projectItem.setText(0, "Project")
    self.spectrumItem.setText(0, "Spectra")
    self.spectrumItem.setText(0, "Reference")
    self.spectrumItem.takeChildren()

  def dragEnterEvent(self, event, enter = True):
    if event.mimeData().hasUrls():
      event.accept()
    else:

      import json

      item = self.itemAt(event.pos())
      if item:
        itemData = json.dumps({'pids':[item.text(0)]})
        event.mimeData().setData('ccpnmr-json', itemData)
        event.mimeData().setText(itemData)


  def dragMoveEvent(self, event:QtGui.QMouseEvent):
    """
    Required function to enable dragging and dropping within the sidebar.
    """
    event.accept()

  def addSpectrum(self, spectrum:(Spectrum,Pid)):
    """
    Adds the specified spectrum to the sidebar.
    """
    peakList = spectrum.newPeakList()
    newItem = self.addItem(self.spectrumItem, spectrum)
    peakListItem = QtGui.QTreeWidgetItem(newItem)
    peakListItem.setText(0, peakList.pid)

  # def processSpectrum(self, spectrum:(Spectrum,Pid), event, expTypes=None):
  #
  #   spectrum = self.project.getByPid(spectrum)


    # if self._appBase.applicationName == 'Screen':
    #   newItem = self.addItem(self.onedItem, spectrum)
    #   peakListItem = QtGui.QTreeWidgetItem(newItem)
    #   peakListItem.setText(0, peakList.pid)
    #
    # else:
    #   newItem = self.addItem(self.spectrumItem, spectrum)
    #   peakListItem = QtGui.QTreeWidgetItem(newItem)
    #   peakListItem.setText(0, peakList.pid)

  def processNotes(self, pids:Sequence[str], event):
    """Display notes defined by list of Pid strings"""
    for ss in pids:
      note = self.project.getByPid(ss)
      self.addItem(self.notesItem, note)

