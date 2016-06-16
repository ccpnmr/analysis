"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtCore, QtGui

from ccpn.ui.gui.DropBase import DropBase

from ccpn.ui.gui.modules.CreateSequence import CreateSequence
from ccpn.ui.gui.modules.NotesEditor import NotesEditor

from ccpn.ui.gui.popups.NmrChainPopup import NmrChainPopup
from ccpn.ui.gui.popups.NmrResiduePopup import NmrResiduePopup
from ccpn.ui.gui.popups.PeakListPropertiesPopup import PeakListPropertiesPopup
from ccpn.ui.gui.popups.RestraintTypePopup import RestraintTypePopup
from ccpn.ui.gui.popups.SpectrumPropertiesPopup import SpectrumPropertiesPopup
from ccpn.ui.gui.popups.SamplePropertiesPopup import SamplePropertiesPopup
from ccpn.ui.gui.popups.SamplePropertiesPopup import EditSampleComponentPopup
from ccpn.ui.gui.popups.SpectrumGroupEditor import SpectrumGroupEditor

from ccpn.ui.gui.widgets.MessageDialog import showInfo

from ccpn.core.Project import Project
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject

# NB RestraintList ('RL') is not in for the moment. Needs to be added later
# NB the order matters!
# NB 'SG' must be before 'SP', as SpectrumGroups must be ready before Spectra
# Also parents must appear before their children
classesInSideBar = ('SG', 'SP', 'PL', 'SA', 'SC', 'SU', 'MC', 'NC', 'NR', 'NA',
                    'CL', 'SE', 'MO', 'DS',
                    'RL', 'NO')

classesInTopLevel =('SG', 'SP', 'SA', 'SU', 'MC', 'NC', 'CL', 'SE', 'DS', 'NO')

# NBNB TBD FIXME
# 1)This function (and the NEW_ITEM_DICT) it uses gets the create_new
# function from the shortClassName of the PARENT!!!
# This is the only way to do it if the create_new functions are attributes of the PARENT!!!
#
# 2) <New> in makes a new SampleComponent. This is counterintuitive!
# Anyway, how do you make a new Sample?
# You use the <New> under sample, this comment is completely inaccurate!
#
# Try putting in e.g. <New PeakList>, <New SampleComponent> etc.
# This would 1) Clutter the SideBar with unnecessary words
#            2) Break the convention that hitting new under a list of objects or parent creates
#               a new object of that type, or a new child, respectively.

NEW_ITEM_DICT = {

  'SP': 'newPeakList',
  'NC': 'newNmrResidue',
  'NR': 'newNmrAtom',
  'DS': 'newRestraintList',
  'RL': 'newRestraint',
  'SE': 'newModel',
  'Notes': 'newNote',
  'Structures': 'newStructureEnsemble',
  'Samples': 'newSample',
  'NmrChains': 'newNmrChain',
  'Chains': 'CreateSequence',
  'Substances': 'newSubstance',
  'Chemical Shift Lists': 'newChemicalShiftList',
  'DataSets': 'newDataSet',
  'SpectrumGroups': 'newSpectrumGroup',
}
### Flag example code removed in revision 7686

class SideBar(DropBase, QtGui.QTreeWidget):
  def __init__(self, parent=None ):
    QtGui.QTreeWidget.__init__(self, parent)

    self._typeToItem = dd = {}

    self.setFont(QtGui.QFont('Lucida Grande', 12))
    self.header().hide()
    self.setDragEnabled(True)
    self._appBase = parent._appBase
    self.setExpandsOnDoubleClick(False)
    self.setDragDropMode(self.InternalMove)
    self.setMinimumWidth(200)
    self.projectItem = dd['PR'] = QtGui.QTreeWidgetItem(self)
    self.projectItem.setFlags(self.projectItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.projectItem.setText(0, "Project")
    self.projectItem.setExpanded(True)
    self.spectrumItem = dd['SP'] = QtGui.QTreeWidgetItem(self.projectItem)
    self.spectrumItem.setFlags(self.spectrumItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.spectrumItem.setText(0, "Spectra")
    self.spectrumGroupItem = dd['SG'] = QtGui.QTreeWidgetItem(self.projectItem)
    self.spectrumGroupItem.setFlags(self.spectrumGroupItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.spectrumGroupItem.setText(0, "SpectrumGroups")
    self.newSpectrumGroup = QtGui.QTreeWidgetItem(self.spectrumGroupItem)
    self.newSpectrumGroup.setFlags(self.newSpectrumGroup.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.newSpectrumGroup.setText(0, "<New>")
    self.samplesItem = dd['SA'] = QtGui.QTreeWidgetItem(self.projectItem)
    self.samplesItem.setFlags(self.samplesItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.samplesItem.setText(0, 'Samples')
    self.newSample = QtGui.QTreeWidgetItem(self.samplesItem)
    self.newSample.setFlags(self.newSample.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.newSample.setText(0, "<New>")
    self.substancesItem = dd['SU'] = QtGui.QTreeWidgetItem(self.projectItem)
    self.substancesItem.setFlags(self.substancesItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.substancesItem.setText(0, "Substances")
    self.chainItem = dd['MC'] = QtGui.QTreeWidgetItem(self.projectItem)
    self.chainItem.setFlags(self.chainItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.chainItem.setText(0, "Chains")
    self.newChainItem = QtGui.QTreeWidgetItem(self.chainItem)
    self.newChainItem.setFlags(self.newChainItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.newChainItem.setText(0, '<New>')
    self.nmrChainItem = dd['NC'] = QtGui.QTreeWidgetItem(self.projectItem)
    self.nmrChainItem.setFlags(self.nmrChainItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.nmrChainItem.setText(0, "NmrChains")
    self.newNmrChainItem = QtGui.QTreeWidgetItem(self.nmrChainItem)
    self.newNmrChainItem.setFlags(self.newNmrChainItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.newNmrChainItem.setText(0, '<New>')
    self.chemicalShiftListsItem = dd['CL'] = QtGui.QTreeWidgetItem(self.projectItem)
    self.chemicalShiftListsItem.setFlags(self.chemicalShiftListsItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.chemicalShiftListsItem.setText(0, "Chemical Shift Lists")
    self.newChemicalShiftListItem = QtGui.QTreeWidgetItem(self.chemicalShiftListsItem)
    self.newChemicalShiftListItem.setFlags(self.newChemicalShiftListItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.newChemicalShiftListItem.setText(0, '<New>')
    self.structuresItem = dd['SE'] = QtGui.QTreeWidgetItem(self.projectItem)
    self.structuresItem.setFlags(self.structuresItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.structuresItem.setText(0, "Structures")
    self.dataSetsItem = dd['DS'] = QtGui.QTreeWidgetItem(self.projectItem)
    self.dataSetsItem.setFlags(self.dataSetsItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.dataSetsItem.setText(0, "DataSets")
    self.newDataSetItem = QtGui.QTreeWidgetItem(self.dataSetsItem)
    self.newDataSetItem.setFlags(self.newDataSetItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.newDataSetItem.setText(0, '<New>')
    self.notesItem = dd['NO'] = QtGui.QTreeWidgetItem(self.projectItem)
    self.notesItem.setFlags(self.notesItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.notesItem.setText(0, "Notes")
    self.newNoteItem = QtGui.QTreeWidgetItem(self.notesItem)
    self.newNoteItem.setFlags(self.newNoteItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.newNoteItem.setText(0, '<New>')
    self.mousePressEvent = self._mousePressEvent
    self.dragMoveEvent = self._dragMoveEvent
    self.dragEnterEvent = self._dragEnterEvent



  def setProject(self, project:Project):
    """
    Sets the specified project as a class attribute so it can be accessed from elsewhere
    """
    self.project = project
    self.colourScheme = project._appBase.preferences.general.colourScheme

    # Register notifiers to maintain sidebar
    notifier = project.registerNotifier('AbstractWrapperObject', 'create', self._createItem)
    notifier = project.registerNotifier('AbstractWrapperObject', 'delete', self._removeItem)
    notifier = project.registerNotifier('AbstractWrapperObject', 'rename', self._renameItem)
    notifier = project.registerNotifier('SpectrumGroup', 'Spectrum', self._refreshSidebarSpectra,
                                        onceOnly=True)
    project.duplicateNotifier('SpectrumGroup', 'create', notifier)
    project.duplicateNotifier('SpectrumGroup', 'delete', notifier)


  def _refreshSidebarSpectra(self, dummy:Project):
    """Reset spectra in sidebar - to be called from notifiers
    """
    for spectrum in self.project.spectra:
      # self._removeItem( self.project, spectrum)
      self._removeItem(spectrum)
      self._createItem(spectrum)



  def _addItem(self, item:QtGui.QTreeWidgetItem, pid:str):
    """
    Adds a QTreeWidgetItem as a child of the item specified, which corresponds to the data object
    passed in.
    """

    newItem = QtGui.QTreeWidgetItem(item)
    newItem.setFlags(newItem.flags() & ~(QtCore.Qt.ItemIsDropEnabled))
    newItem.setData(0, QtCore.Qt.DisplayRole, str(pid))
    newItem.mousePressEvent = self.mousePressEvent
    return newItem
  #
  # def renameItem(self, pid):
  #   # item = FindItem
  #   pass

  def processText(self, text, event=None):
    newNote = self.project.newNote()
    newNote.text = text


  def _mousePressEvent(self, event):
    """
    Re-implementation of the mouse press event so right click can be used to delete items from the
    sidebar.
    """
    if event.button() == QtCore.Qt.RightButton:
      self._raiseContextMenu(event, self.itemAt(event.pos()))
    else:
      QtGui.QTreeWidget.mousePressEvent(self, event)

  def _raiseContextMenu(self, event:QtGui.QMouseEvent, item:QtGui.QTreeWidgetItem):
    """
    Creates and raises a context menu enabling items to be deleted from the sidebar.
    """
    from ccpn.ui.gui.widgets.Menu import Menu
    contextMenu = Menu('', self, isFloatWidget=True)
    from functools import partial
    # contextMenu.addAction('Delete', partial(self.removeItem, item))
    contextMenu.addAction('Delete', partial(self._deleteItemObject, item))
    contextMenu.popup(event.globalPos())


  def _deleteItemObject(self,  item:QtGui.QTreeWidgetItem):
    """Removes the specified item from the sidebar and deletes it from the project.
    NB, the clean-up of the side bar is done through notifiers
    """
    self.project.getByPid(item.data(0, QtCore.Qt.DisplayRole)).delete()

  def _createItem(self, obj:AbstractWrapperObject):
    """Create a new sidebar item from a new object.
    Called by notifier when a new object is created or undeleted (so need to check for duplicates).
    NB Obj may be of a type that does not have an item"""

    if not isinstance(obj, AbstractWrapperObject):
      return

    shortClassName = obj.shortClassName

    if shortClassName == 'SP':
      # Spectrum - special behaviour - put them under SpectrumGroups, if any
      spectrumGroups = obj.spectrumGroups
      if spectrumGroups:
        for sg in spectrumGroups:
          for sgitem in self._findItems(str(sg.pid)):
            self._addItem(sgitem, str(obj.pid))

        return


    if shortClassName in classesInTopLevel:
      itemParent = self._typeToItem.get(shortClassName)
      newItem = self._addItem(itemParent, obj.pid)

      if shortClassName in ['SP', 'SA', 'NC']:
        newObjectItem = QtGui.QTreeWidgetItem(newItem)
        newObjectItem.setFlags(newObjectItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
        newObjectItem.setText(0, "<New>")

    elif shortClassName == 'PL':
      for itemParent in self._findItems(obj.spectrum.pid):
        self._addItem(itemParent, obj.pid)

    elif shortClassName == 'SC':
      for itemParent in self._findItems(obj.sample.pid):
        self._addItem(itemParent, obj.pid)

    elif shortClassName == 'NR':
      for itemParent in self._findItems(obj.nmrChain.pid):
        self._addItem(itemParent, obj.pid)

    elif shortClassName == 'NA':
      for itemParent in self._findItems(obj.nmrResidue.pid):
        self._addItem(itemParent, obj.pid)

    elif shortClassName == 'RL':
      for itemParent in self._findItems(obj.dataSet.pid):
        self._addItem(itemParent, obj.pid)

    elif shortClassName == 'MO':
      for itemParent in self._findItems(obj.structureEnsemble.pid):
        self._addItem(itemParent, obj.pid)

    else:
      # Object type is not in sidebar
      return None


  def _renameItem(self, obj:AbstractWrapperObject, oldPid:str):
    """rename item(s) from previous pid oldPid to current object pid"""
    newPid = obj.pid
    for item in self._findItems(oldPid):
      item.setData(0, QtCore.Qt.DisplayRole, str(newPid))

  def _removeItem(self, wrapperObject:AbstractWrapperObject):
  # def _removeItem(self, parent, objPid):
    """Removes sidebar item(s) for object with pid objPid, but does NOT delete the object.
    Called when objects are deleted.
    The parent parameter is necessary to match the standard calling interface of notifiers"""
    import sip
    for item in self._findItems(wrapperObject.pid):
      sip.delete(item)

  def _findItems(self, objPid:str) -> QtGui.QTreeWidgetItem:
    """Find items that match objPid - returns empty list if no matches"""

    if objPid[:2] in classesInSideBar:
      result = self.findItems(objPid, QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive, 0)

    else:
      result = []

    return result

  def fillSideBar(self, project:Project):
    """
    Fills the sidebar with the relevant data from the project.
    """

    self.projectItem.setText(0, project.name)
    pid2Obj = project._pid2Obj
    for className in classesInSideBar:
      dd = pid2Obj.get(className)
      if dd:
        for obj in sorted(dd.values()):
          self._createItem(obj)

  def _dragEnterEvent(self, event, enter=True):
    if event.mimeData().hasUrls():
      event.accept()
    else:
      import json
      item = self.itemAt(event.pos())
      if item:
        text = item.text(0)
        if ':' in text:
          itemData = json.dumps({'pids':[text]})
          event.mimeData().setData('ccpnmr-json', itemData)
          event.mimeData().setText(itemData)


  def _dragMoveEvent(self, event:QtGui.QMouseEvent):
    """
    Required function to enable dragging and dropping within the sidebar.
    """
    event.accept()

  def raisePopup(self, obj, item):

    if obj.shortClassName == 'SP':
      popup = SpectrumPropertiesPopup(obj)
      popup.exec_()
      popup.raise_()
    elif obj.shortClassName == 'PL':
      popup = PeakListPropertiesPopup(peakList=obj)
      popup.exec_()
      popup.raise_()
      # info = showInfo('Not implemented yet!',
      #     'This function has not been implemented in the current version',
      #     colourScheme=self.colourScheme)

    elif obj.shortClassName == 'SG':
      popup = SpectrumGroupEditor(project=self.project, spectrumGroup=obj)
      popup.exec_()
      popup.raise_()

    elif obj.shortClassName == 'SA':
      popup = SamplePropertiesPopup(obj, project=self.project)
      popup.exec_()
      popup.raise_()

    elif obj.shortClassName == 'SC':
      popup = EditSampleComponentPopup(sampleComponent=obj)
      popup.exec_()
      popup.raise_()
    elif obj.shortClassName == 'SU':
      pass
    elif obj.shortClassName == 'NC':
      popup = NmrChainPopup(nmrChain=obj)
      popup.exec_()
      popup.raise_()
    elif obj.shortClassName == 'NR':
      # info = showInfo('Not implemented yet!',
      #     'This function has not been implemented in the current version',
      #     colourScheme=self.colourScheme)
      popup = NmrResiduePopup(nmrResidue=obj)
      popup.exec_()
      popup.raise_()
    elif obj.shortClassName == 'NA':
      info = showInfo('Not implemented yet!',
          'This function has not been implemented in the current version',
          colourScheme=self.colourScheme)
      # popup = NmrAtomPopup(nmrAtom=obj)
      # popup.exec_()
      # popup.raise_()
    elif obj.shortClassName == 'CL':
      info = showInfo('Not implemented yet!',
          'This function has not been implemented in the current version',
          colourScheme=self.colourScheme)
    elif obj.shortClassName == 'SE':
      info = showInfo('Not implemented yet!',
          'This function has not been implemented in the current version',
          colourScheme=self.colourScheme)
    elif obj.shortClassName == 'MC':
      #to be decided when we design structure
      info = showInfo('Not implemented yet!',
          'This function has not been implemented in the current version',
          colourScheme=self.colourScheme)
    elif obj.shortClassName == 'MD':
      #to be decided when we design structure
      showInfo('Not implemented yet!',
          'This function has not been implemented in the current version',
          colourScheme=self.colourScheme)
    elif obj.shortClassName == 'DS':
      #to be decided when we design structure
      showInfo('Not implemented yet!',
          'This function has not been implemented in the current version',
          colourScheme=self.colourScheme)
    elif obj.shortClassName == 'RL':
      #to be decided when we design structure
      showInfo('Not implemented yet!',
          'This function has not been implemented in the current version',
          colourScheme=self.colourScheme)
    elif obj.shortClassName == 'RE':
      #to be decided when we design structure
      showInfo('Not implemented yet!',
          'This function has not been implemented in the current version',
          colourScheme=self.colourScheme)
    elif obj.shortClassName == 'NO':
      if self._appBase.ui.mainWindow is not None:
        mainWindow = self._appBase.ui.mainWindow
      else:
        mainWindow = self._appBase._mainWindow
      self.notesEditor = NotesEditor(mainWindow.moduleArea, self.project,
                                     name='Notes Editor', note=obj)

  def _createNewObject(self, item):
    """Create new object starting from the <New> item
    """

    # NBNB TBD FIXME
    # This function (and the NEW_ITEM_DICT) it uses gets the create_new
    # function from the shortClassName of the PARENT!!!
    # The assumes that each parent can have only ONE kind of new child.
    # This is true as of 16/2/2016, but may NOT remain true
    # (e.g. Spectrum has multiple children).

    itemParent = self.project.getByPid(item.parent().text(0))

    funcName = None
    if itemParent is None:
      # Top level object - parent is project
      if item.parent().text(0) == 'Chains':
        popup = CreateSequence(project=self.project)
        popup.exec_()
        popup.raise_()
        return
      else:
        itemParent = self.project
        funcName = NEW_ITEM_DICT.get(item.parent().text(0))

    else:
      # Lower level object - get parent from parentItem
      if itemParent.shortClassName == 'DS':
        popup = RestraintTypePopup()
        popup.exec_()
        popup.raise_()
        restraintType = popup.restraintType
        ff = NEW_ITEM_DICT.get(itemParent.shortClassName)
        getattr(itemParent, ff)(restraintType)
        return
      elif itemParent.shortClassName == 'SA':
        popup = EditSampleComponentPopup(project=self.project, sample=itemParent)
        popup.exec_()
        popup.raise_()
        return
      else:
        funcName = NEW_ITEM_DICT.get(itemParent.shortClassName)
    if funcName is not None:
      if (item.parent().text(0)) == 'SpectrumGroups':
        getattr(itemParent, funcName)('NewSpectrumGroup')
      else:
        getattr(itemParent, funcName)()
    else:
      info = showInfo('Not implemented yet!',
          'This function has not been implemented in the current version',
          colourScheme=self.colourScheme)
