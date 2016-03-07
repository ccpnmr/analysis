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

from PyQt4 import QtCore, QtGui

from application.core.DropBase import DropBase
from application.core.modules.CreateSequence import CreateSequence
from application.core.modules.NotesEditor import NotesEditor
from application.core.popups.NmrAtomPopup import NmrAtomPopup
from application.core.popups.NmrChainPopup import NmrChainPopup
from application.core.popups.NmrResiduePopup import NmrResiduePopup
from application.core.popups.PeakListPropertiesPopup import PeakListPropertiesPopup
from application.core.popups.RestraintTypePopup import RestraintTypePopup
from application.core.popups.SpectrumPropertiesPopup import SpectrumPropertiesPopup
from application.core.popups.SamplePropertiesPopup import SamplePropertiesPopup, EditSampleComponentPopup


from ccpn import Project
from ccpn import AbstractWrapperObject


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
#
# 2) <New> in makes a new SampleComponent. This is counterintuitive!
# Anyway, how do you make a new Sample?
#
# Try putting in e.g. <New PeakList>, <New SampleComponent> etc.
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
  'Data Sets': 'newDataSet',
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
    self.projectItem.setText(0, "Project")
    self.projectItem.setExpanded(True)
    self.spectrumItem = dd['SP'] = QtGui.QTreeWidgetItem(self.projectItem)
    self.spectrumItem.setText(0, "Spectra")
    self.spectrumGroupItem = dd['SG'] = QtGui.QTreeWidgetItem(self.projectItem)
    self.spectrumGroupItem.setText(0, "Spectrum Groups")
    self.samplesItem = dd['SA'] = QtGui.QTreeWidgetItem(self.projectItem)
    self.samplesItem.setText(0, 'Samples')
    self.newSample = QtGui.QTreeWidgetItem(self.samplesItem)
    self.newSample.setText(0, "<New>")
    self.substancesItem = dd['SU'] = QtGui.QTreeWidgetItem(self.projectItem)
    self.substancesItem.setText(0, "Substances")
    self.newSubstanceItem = QtGui.QTreeWidgetItem(self.substancesItem)
    self.newSubstanceItem.setText(0, '<New>')
    self.chainItem = dd['MC'] = QtGui.QTreeWidgetItem(self.projectItem)
    self.chainItem.setText(0, "Chains")
    self.newChainItem = QtGui.QTreeWidgetItem(self.chainItem)
    self.newChainItem.setText(0, '<New>')
    self.nmrChainItem = dd['NC'] =  QtGui.QTreeWidgetItem(self.projectItem)
    self.nmrChainItem.setText(0, "NmrChains")
    self.newNmrChainItem = QtGui.QTreeWidgetItem(self.nmrChainItem)
    self.newNmrChainItem.setText(0, '<New>')
    self.chemicalShiftListsItem = dd['CL'] = QtGui.QTreeWidgetItem(self.projectItem)
    self.chemicalShiftListsItem.setText(0, "Chemical Shift Lists")
    self.newChemicalShiftListItem = QtGui.QTreeWidgetItem(self.chemicalShiftListsItem)
    self.newChemicalShiftListItem.setText(0, '<New>')
    self.structuresItem = dd['SE'] = QtGui.QTreeWidgetItem(self.projectItem)
    self.structuresItem.setText(0, "Structures")
    self.dataSetsItem = dd['DS'] = QtGui.QTreeWidgetItem(self.projectItem)
    self.dataSetsItem.setText(0, "DataSets")
    self.newDataSetItem = QtGui.QTreeWidgetItem(self.dataSetsItem)
    self.newDataSetItem.setText(0, '<New>')
    self.notesItem = dd['NO'] = QtGui.QTreeWidgetItem(self.projectItem)
    self.notesItem.setText(0, "Notes")
    self.newNoteItem = QtGui.QTreeWidgetItem(self.notesItem)
    self.newNoteItem.setText(0, '<New>')



  def setProject(self, project:Project):
    """
    Sets the specified project as a class attribute so it can be accessed from elsewhere
    """
    self.project = project

  def addItem(self, item:QtGui.QTreeWidgetItem, pid:str):
    """
    Adds a QTreeWidgetItem as a child of the item specified, which corresponds to the data object
    passed in.
    """
    newItem = QtGui.QTreeWidgetItem(item)
    newItem.setFlags(newItem.flags() & ~(QtCore.Qt.ItemIsDropEnabled))
    newItem.setData(0, QtCore.Qt.DisplayRole, str(pid))
    newItem.mousePressEvent = self.mousePressEvent
    return newItem

  def renameItem(self, pid):
    # item = FindItem
    pass

  def processText(self, text, event=None):
    newNote = self.project.newNote()
    newNote.text = text


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
            self.addItem(sgitem, str(obj.pid))

        return


    if shortClassName in classesInTopLevel:
      itemParent = self._typeToItem.get(shortClassName)
      self.addItem(itemParent, obj.pid)

    elif shortClassName == 'PL':
      for itemParent in self._findItems(obj.spectrum.pid):
        self.addItem(itemParent, obj.pid)
      # newPeakListItem = QtGui.QTreeWidgetItem(itemParent)
      # newPeakListItem.setText(0, '<New>')


    elif shortClassName == 'SC':
      for itemParent in self._findItems(obj.sample.pid):
        self.addItem(itemParent, obj.pid)

    elif shortClassName == 'NR':
      for itemParent in self._findItems(obj.nmrChain.pid):
        self.addItem(itemParent, obj.pid)

    elif shortClassName == 'NA':
      for itemParent in self._findItems(obj.nmrResidue.pid):
        self.addItem(itemParent, obj.pid)

    elif shortClassName == 'RL':
      for itemParent in self._findItems(obj.dataSet.pid):
        self.addItem(itemParent, obj.pid)

    elif shortClassName == 'MO':
      for itemParent in self._findItems(obj.structureEnsemble.pid):
        self.addItem(itemParent, obj.pid)

    else:
      # Object type is not in sidebar
      return None


  def _renameItem(self, oldPid:str, newPid:str):
    """rename item(s) from object pdi oldPid to object pid newPid"""
    for item in self._findItems(oldPid):
      item.setData(0, QtCore.Qt.DisplayRole, str(newPid))

  def _removeItem(self, objPid):
    """Removes sidebar item(s) for object with pid objPid, but does NOT delete the object.
    Called when objects are deleted"""
    import sip
    for item in self._findItems(objPid):
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

  def dragEnterEvent(self, event, enter=True):
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

  def raisePopup(self, obj, item):
    if obj.shortClassName == 'SP':
      popup = SpectrumPropertiesPopup(obj)
      popup.exec_()
      popup.raise_()
    elif obj.shortClassName == 'PL':
      popup = PeakListPropertiesPopup(peakList=obj)
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
      popup = NmrResiduePopup(nmrResidue=obj)
      popup.exec_()
      popup.raise_()
    elif obj.shortClassName == 'NA':
      popup = NmrAtomPopup(nmrAtom=obj)
      popup.exec_()
      popup.raise_()
    elif obj.shortClassName == 'CS':
      pass
    elif obj.shortClassName == 'SE':
      pass #to be decided when we design structure
    elif obj.shortClassName == 'MD':
      pass #to be decided when we design structure
    elif obj.shortClassName == 'DS':
      pass #to be decided when we design structure
    elif obj.shortClassName == 'RL':
      pass #to be decided when we design structure
    elif obj.shortClassName == 'RE':
      pass #to be decided when we design structure
    elif obj.shortClassName == 'NO':
      self.notesEditor = NotesEditor(self._appBase.mainWindow.dockArea, self.project, name='Notes Editor', note=obj)

  def createNewObject(self, item):
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
        newComponent = itemParent.newSampleComponent()
        popup = EditSampleComponentPopup(sampleComponent=newComponent)
        popup.exec_()
        popup.raise_()
        return
      else:
        funcName = NEW_ITEM_DICT.get(itemParent.shortClassName)

    if funcName is not None:
      getattr(itemParent, funcName)()
