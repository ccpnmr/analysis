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

import sys
import os
import csv

experimentTypeDict = {'zg':'H', 'cpmg':'T2-filtered.H', 'STD':'STD.H', 'bdwl':'Water-LOGSY.H'}



class SideBar(QtGui.QTreeWidget):
  def __init__(self, parent=None ):
    QtGui.QTreeWidget.__init__(self, parent)
    self.setStyleSheet("""
    QTreeWidget { background-color: #020F31;
    }
    QTreeWidget::item {background-color: #0e1a3d;
                       color: #bec4f3;
                       }
    QTreeWidget::item::selected {
                      background-color: #666e98;
                      color: #f7ffff;
                      }
    QTreeWidget::item::hover {
                      background-color: #424a71;
                      color: #e4e15b;
                      }
    QTreeView:branch:{
    background-color: #e4e15b;
    }
    """)
    self.header().hide()
    self.setDragEnabled(True)
    self.setDragDropMode(self.InternalMove)
    # self._dragroot = self.itemRootIndex()
    self.setFixedWidth(180)
    self.projectItem = QtGui.QTreeWidgetItem(self)
    self.projectItem.setText(0, "Project")
    self.spectrumItem = QtGui.QTreeWidgetItem(self.projectItem)
    self.spectrumItem.setText(0, "Spectra")
    self.spectrumReference = QtGui.QTreeWidgetItem(self.projectItem)
    self.spectrumReference.setText(0, "Reference")
    self.spectrumScreening = QtGui.QTreeWidgetItem(self.projectItem)
    self.spectrumScreening.setText(0, "Screening")
    self.spectrumMixtures = QtGui.QTreeWidgetItem(self.projectItem)
    self.spectrumMixtures.setText(0, "Mixtures")
    # self.restraintsItem = QtGui.QTreeWidgetItem(self.projectItem)
    # self.restraintsItem.setText(0, "Restraint Lists")
    self.spectrumDeleted = QtGui.QTreeWidgetItem(self.projectItem)
    self.spectrumDeleted.setText(0, "Deleted")
    self.structuresItem = QtGui.QTreeWidgetItem(self.projectItem)
    self.structuresItem.setText(0, "Structures")
    # self.samplesItem = QtGui.QTreeWidgetItem(self.projectItem)
    # self.samplesItem.setText(0, "Samples")
    self.notesItem = QtGui.QTreeWidgetItem(self.projectItem)
    self.notesItem.setText(0, "Notes")
    self.newNoteItem = QtGui.QTreeWidgetItem(self.notesItem)
    self.newNoteItem.setData(0, QtCore.Qt.DisplayRole, '<New Note>')
    self.parent = parent



  def addItem(self, item, data):
    newItem = QtGui.QTreeWidgetItem(item)
    newItem.setFlags(newItem.flags() & ~(QtCore.Qt.ItemIsDropEnabled))
    newItem.setText(0, str(data.name))
    newItem.setData(0, QtCore.Qt.DisplayRole, str(data.pid))
    return newItem



  def fillSideBar(self,project):
    self.projectItem.setText(0, project.name)
    for spectrum in project.spectra:
      newItem = self.addItem(self.spectrumItem, spectrum)
      if spectrum is not None:
        for peakList in spectrum.peakLists:
          peakListItem = QtGui.QTreeWidgetItem(newItem)
          peakListItem.setText(0, peakList.pid)

    # for mixture in project.mixtures:
    #   newMixture = self.addItem(self.spectrumMixtures, newItem)




    # self.structuresItem.addChild(QtGui.QTreeWidgetItem(["<empty>"]))
    # self.notesItem.addChild(QtGui.QTreeWidgetItem(["<empty>"]))


    # 1d
    self.onedItem = QtGui.QTreeWidgetItem(self.spectrumReference)
    self.onedItem.setText(0, "1D")
    # self.onedItemMixture = QtGui.QTreeWidgetItem(self.spectrumMixtures)
    # self.onedItemMixture.setText(0, "1D")
    self.onedItemScreening = QtGui.QTreeWidgetItem(self.spectrumScreening)
    self.onedItemScreening.setText(0, "1D")
    # STD
    self.stdItem = QtGui.QTreeWidgetItem(self.spectrumReference)
    self.stdItem.setText(0, "STD")
    # self.stdItemMixture = QtGui.QTreeWidgetItem(self.spectrumMixtures)
    # self.stdItemMixture.setText(0, "STD")
    self.stdItemScreening = QtGui.QTreeWidgetItem(self.spectrumScreening)
    self.stdItemScreening.setText(0, "STD")
    # Wlogsy
    self.logsyItem = QtGui.QTreeWidgetItem(self.spectrumReference)
    self.logsyItem.setText(0, "Water-LOGSY")
    # self.logsyItemMixture = QtGui.QTreeWidgetItem(self.spectrumMixtures)
    # self.logsyItemMixture.setText(0, "Water-LOGSY")
    self.logsyItemScreening = QtGui.QTreeWidgetItem(self.spectrumScreening)
    self.logsyItemScreening.setText(0, "Water-LOGSY")
    self.logsyItemScreening.setText(0, "Water-LOGSY")
    # T1rho
    self.t1rhoItem = QtGui.QTreeWidgetItem(self.spectrumReference)
    self.t1rhoItem.setText(0, "T1rho")
    # self.t1rhoItemMixture = QtGui.QTreeWidgetItem(self.spectrumMixtures)
    # self.t1rhoItemMixture.setText(0, "T1rho")
    self.t1rhoItemScreening= QtGui.QTreeWidgetItem(self.spectrumScreening)
    self.t1rhoItemScreening.setText(0, "T1rho")

    ### Flags
    # set dropEnable  the item you want to move. Set dragEnable  where drop is allowed
    self.projectItem.setFlags(self.projectItem.flags() & ~(QtCore.Qt.ItemIsDragEnabled |QtCore.Qt.ItemIsDropEnabled))
    self.spectrumItem.setFlags(self.spectrumItem.flags() & ~(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled))
    self.spectrumReference.setFlags(self.spectrumReference.flags()  & ~(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled))
    self.spectrumScreening.setFlags(self.spectrumScreening.flags() & ~(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled ))
    self.spectrumMixtures.setFlags(self.spectrumMixtures.flags() & ~(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled))
    # References
    self.onedItem.setFlags(self.onedItem.flags()  & ~(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled))
    self.logsyItem.setFlags(self.logsyItem.flags()  & ~(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled))
    self.t1rhoItem.setFlags(self.t1rhoItem.flags() & ~(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled))
    self.t1rhoItem.setFlags(self.t1rhoItem.flags() & ~(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled))
    self.stdItem.setFlags(self.stdItem.flags() & ~(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled))
    # screening
    self.onedItemScreening.setFlags(self.onedItemScreening.flags() & ~(QtCore.Qt.ItemIsDragEnabled))
    self.logsyItemScreening.setFlags(self.logsyItemScreening.flags() & ~(QtCore.Qt.ItemIsDragEnabled ))
    self.t1rhoItemScreening.setFlags(self.t1rhoItemScreening.flags() & ~(QtCore.Qt.ItemIsDragEnabled))
    self.stdItemScreening.setFlags(self.stdItemScreening.flags() & ~(QtCore.Qt.ItemIsDragEnabled))
    # structures, notes, deleted
    self.structuresItem.setFlags(self.structuresItem.flags()  & ~(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled))
    self.notesItem.setFlags(self.notesItem.flags()  & ~(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled))
    self.spectrumDeleted.setFlags(self.spectrumDeleted.flags() & ~(QtCore.Qt.ItemIsDragEnabled ))

  def clearSideBar(self):
    self.projectItem.setText(0, "Project")
    self.spectrumItem.setText(0, "Spectra")
    self.spectrumItem.setText(0, "Reference")
    self.spectrumItem.takeChildren()

  def dragEnterEvent(self, event, enter = True):
    if event.mimeData().hasUrls():
      event.accept()
    else:
      items = []
      item = self.itemAt(event.pos())
      if enter:
          QtGui.QTreeWidget.dragEnterEvent(self, event)
      else:
        QtGui.QTreeWidget.dragMoveEvent(self, event)
      for item, flags in items:
          item.setFlags(flags)

  def dragMoveEvent(self, event):
    event.accept()

  def addSpectrum(self, spectrum):
    newItem = self.addItem(self.spectrumItem, spectrum)
    peakList = spectrum.newPeakList()
    peakListItem = QtGui.QTreeWidgetItem(newItem)
    peakListItem.setText(0, peakList.pid)

  def addSpectrumToItem(self, spectrum, expTypes=None):

    peakList = spectrum.newPeakList()
    if spectrum.dimensionCount == 1:

      if expTypes and len(expTypes) > 0:
        spectrum.experimentType = expTypes

        if spectrum.experimentType == "STD.H":
         newItem = self.addItem(self.stdItem, spectrum)
         peakListItem = QtGui.QTreeWidgetItem(newItem)
         peakListItem.setText(0, peakList.pid)

        elif spectrum.experimentType == "Water-LOGSY.H":
          newItem = self.addItem(self.logsyItem, spectrum)
          peakListItem = QtGui.QTreeWidgetItem(newItem)
          peakListItem.setText(0, peakList.pid)

        elif spectrum.experimentType == "T2-filtered.H":
          newItem = self.addItem(self.t1rhoItem, spectrum)
          peakListItem = QtGui.QTreeWidgetItem(newItem)
          peakListItem.setText(0, peakList.pid)

      else:
        newItem = self.addItem(self.onedItem, spectrum)
        print('here1d')
        peakListItem = QtGui.QTreeWidgetItem(newItem)
        peakListItem.setText(0, peakList.pid)
        peakListItem.setFlags(peakListItem.flags() & ~(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled))
    else:
      newItem = self.addItem(self.spectrumItem, spectrum)
      peakListItem = QtGui.QTreeWidgetItem(newItem)
      peakListItem.setText(0, peakList.pid)
      peakListItem.setFlags(peakListItem.flags() & ~(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled))


  def getExpType(self, filename):
    ''' if experiment type is express in the pulseprogram file, send the spectrum in the appropriate Sidebar position.
    If more then two experiments take the first only, if not express assume is 1H

    '''
    pp = filename[:-2]
    pp.append('pulseprogram')
    ppFile = open('/'.join(pp), 'r').readlines()
    expTypes = []
    for expType in experimentTypeDict.keys():
      if expType in ppFile[1]:
        expTypes.append(experimentTypeDict[expType])
    # print(expTypes, ppFile[1])
    if len(expTypes) > 1 and 'T2-filtered.H' in expTypes:
      expTypes.remove('T2-filtered.H')
    if len(expTypes) == 1:
      return expTypes[0]
    else:
      return None

  def isLookupFile(self, filePath):
    print(filePath.split('/')[-1])
    if filePath.split('/')[-1].endswith('.csv'):
      return True
    elif '.xls' in filePath.split('/')[-1]:
      return True
    else:
      return False


  def parseLookupFile(self, filePath):

    if filePath.split('/')[-1].endswith('.csv'):
      csv_in = open(filePath, 'r')
      reader = csv.reader(csv_in)
      for row in reader:
        if row[0].split('/')[-1] == 'procs':
          filename = row[0].split('/')
          filename.pop()
          newFilename = '/'.join(filename)
          spectrum = self.parent.project.loadSpectrum(newFilename)
          expType = self.getExpType(filename)
          if spectrum is not None:
            self.addSpectrumToItem(spectrum, expType)

    elif '.xls' in filePath.split('/')[-1]:
      ex = pd.ExcelFile(filePath)
      for sheet in ex.sheet_names:
        excelSheet = ex.parse(sheet)
        for row in excelSheet['filename']:
          if row.split('/')[-1] == 'procs':
            filename = row.split('/')
            filename.pop()
            newFilename = '/'.join(filename)
            spectrum = self.parent.project.loadSpectrum(newFilename)
            print(spectrum)
            try:
              expType = self.getExpType(filename)
            except:
              expType = 'H'
            if spectrum is not None:
              self.addSpectrumToItem(spectrum, expType)
    else:
      pass

  def isProject(self, filePath):
    for dirpath, dirnames, filenames in os.walk(filePath):
      if dirpath.endswith('memops') and 'Implementation' in dirnames:
        return True


  def dropEvent(self, event):
    '''If object can be dropped into this area, accept dropEvent, otherwise throw an error
      spectra, projects and peak lists can be dropped into this area but nothing else.
      If project is dropped, it is loaded.
      If spectra/peak lists are dropped, these are displayed in the side bar but not displayed in
      spectrumDisplay
      '''

    if event.mimeData().hasUrls():
      event.setDropAction(QtCore.Qt.CopyAction)
      event.accept()
      links = []
      for url in event.mimeData().urls():
          links.append(str(url.toLocalFile()))
      self.emit(QtCore.SIGNAL("dropped"), links)

    else:
      event.setDropAction(QtCore.Qt.MoveAction)
      print('dropEvent else')
      super(SideBar, self).dropEvent(event)

    if event.mimeData().urls():
      event.accept()
      spectra = []
      filePaths = [url.path() for url in event.mimeData().urls()]
      # print(filePaths)
      if filePaths:
        for filePath in filePaths:
            print(filePath)
          # if len(filePaths) == 1:
            lookupFile = self.isLookupFile(filePath)
            if lookupFile:
              self.parseLookupFile(filePath)

            elif self.isProject(filePath):
              self.parent._appBase.mainWindow.openAProject(filePath)

            else:
              spectrum = self.parent.project.loadSpectrum(filePath)
              try:
                spectrum = self.parent.project.loadSpectrum(filePath)
                self.addSpectrumToItem(spectrum)
                spectra.append(spectrum)
              except:
                pass
        # if len(spectra) > 0:
        #   msgBox = QtGui.QMessageBox()
        #   msgBox.setText("Display all spectra")
        #   msgBox.setInformativeText("Do you want to display all loaded spectra?")
        #   msgBox.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        #   ret = msgBox.exec_()
        #   if ret == QtGui.QMessageBox.Yes:
        #     newDisplay = self.parent.createSpectrumDisplay(spectra[0])
        #     for spectrum in spectra[1:]:
        #       newDisplay.displaySpectrum(spectrum)
        #     self.parent.removeBlankDisplay()
        #   else:
        #     pass

      else:
        event.ignore()
