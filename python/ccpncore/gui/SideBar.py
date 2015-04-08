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

class SideBar(QtGui.QTreeWidget):
  def __init__(self, parent=None):
    super(SideBar, self).__init__(parent)
    self.header().hide()
    self.setDragEnabled(True)
    self.acceptDrops()
    self.setFixedWidth(180)
    # self.itemDoubleClicked.connect(self.test)
    self.setDropIndicatorShown(True)
    self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
    self.projectItem = QtGui.QTreeWidgetItem(self)
    self.projectItem.setText(0, "Project")
    self.spectrumItem = QtGui.QTreeWidgetItem(self.projectItem)
    self.spectrumItem.setText(0, "Spectra")
    self.restraintsItem = QtGui.QTreeWidgetItem(self.projectItem)
    self.restraintsItem.setText(0, "Restraint Lists")
    self.structuresItem = QtGui.QTreeWidgetItem(self.projectItem)
    self.structuresItem.setText(0, "Structures")
    self.samplesItem = QtGui.QTreeWidgetItem(self.projectItem)
    self.samplesItem.setText(0, "Samples")
    self.notesItem = QtGui.QTreeWidgetItem(self.projectItem)
    self.notesItem.setText(0, "Notes")
    self.parent = parent
    self.parent = parent


  def addItem(self, item, data):
    newItem = QtGui.QTreeWidgetItem(item)
    newItem.setText(0, data.name)
    newItem.setData(0, QtCore.Qt.DisplayRole, str(data.pid))
    return newItem

  def dragEnterEvent(self, event):
    if event.mimeData().hasUrls():
      event.accept()
    else:
      super(SideBar, self).dragEnterEvent(event)

  def dragMoveEvent(self, event):

    event.accept()


  def fillSideBar(self,project):
    self.projectItem.setText(0, project.name)
    for spectrum in project.spectra:
      newItem = self.addItem(self.spectrumItem,spectrum)
      if spectrum is not None:
        for peakList in spectrum.peakLists:
          peakListItem = QtGui.QTreeWidgetItem(newItem)
          peakListItem.setText(0, peakList.pid)


    # empty = 'empty'
    self.restraintsItem.addChild(QtGui.QTreeWidgetItem(["<empty>"]))
    self.structuresItem.addChild(QtGui.QTreeWidgetItem(["<empty>"]))
    self.samplesItem.addChild(QtGui.QTreeWidgetItem(["<empty>"]))
    self.notesItem.addChild(QtGui.QTreeWidgetItem(["<empty>"]))
    # newItem3 = QtGui.QTreeWidgetItem(self.restraintsItem)
    # newItem2 = self.addItem(self.structuresItem, empty)
    # newItem3 = self.addItem(self.structuresItem, empty)
    # newItem3.setText(0, "empty")

  def clearSideBar(self):
    self.projectItem.setText(0, "Project")
    self.spectrumItem.setText(0, "Spectra")
    self.spectrumItem.takeChildren()


  def dropEvent(self, event):
    '''If object can be dropped into this area, accept dropEvent, otherwise throw an error
      spectra, projects and peak lists can be dropped into this area but nothing else.
      If project is dropped, it is loaded.
      If spectra/peak lists are dropped, these are displayed in the side bar but not displayed in
      spectrumPane
      '''

    event.accept()
    data = event.mimeData()
    print(data,"dropped")
    print("dropped")
    print(event.source())
    if isinstance(self.parent, QtGui.QGraphicsScene):
      event.ignore()
      return

    if event.mimeData().urls():
      event.accept()

      filePaths = [url.path() for url in event.mimeData().urls()]

      if filePaths:

        print(filePaths)
        if len(filePaths) == 1:

          self.parent.openProject(filePaths[0])

        else:
          pass

      else:
        event.ignore()

    else:
      event.ignore()
