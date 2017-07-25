"""
Module Documentation here
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
__dateModified__ = "$dateModified: 2017-07-07 16:32:55 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b2 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Wayne Boucher $"
__date__ = "$Date: 2017-03-23 16:50:22 +0000 (Thu, March 23, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import json
from collections import OrderedDict

from PyQt4 import QtCore, QtGui

from ccpn.core import _coreClassMap
from ccpn.core.NmrResidue import NmrResidue
from ccpn.core.Project import Project
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import Pid
from ccpn.ui.gui.guiSettings import sidebarFont
from ccpn.ui.gui.lib.GuiNotifier import GuiNotifier
from ccpn.ui.gui.popups.ChemicalShiftListPopup import ChemicalShiftListPopup
from ccpn.ui.gui.popups.DataSetPopup import DataSetPopup
from ccpn.ui.gui.popups.NmrAtomPopup import NmrAtomPopup
from ccpn.ui.gui.popups.NmrChainPopup import NmrChainPopup
from ccpn.ui.gui.popups.NmrResiduePopup import NmrResiduePopup
from ccpn.ui.gui.popups.NotesPopup import NotesPopup
from ccpn.ui.gui.popups.PeakListPropertiesPopup import PeakListPropertiesPopup
from ccpn.ui.gui.popups.RestraintTypePopup import RestraintTypePopup
from ccpn.ui.gui.popups.SampleComponentPropertiesPopup import EditSampleComponentPopup
from ccpn.ui.gui.popups.SamplePropertiesPopup import SamplePropertiesPopup
from ccpn.ui.gui.popups.SpectrumGroupEditor import SpectrumGroupEditor
from ccpn.ui.gui.popups.SpectrumPropertiesPopup import SpectrumPropertiesPopup
from ccpn.ui.gui.popups.StructurePopup import StructurePopup
from ccpn.ui.gui.popups.SubstancePropertiesPopup import SubstancePropertiesPopup
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.ui.gui.widgets.MessageDialog import showInfo
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.util.Constants import ccpnmrJsonData
from ccpn.util.Logging import getLogger
from ui.gui.popups.CreateChainPopup import CreateChainPopup

# from ccpn.ui.gui.modules.NotesEditor import NotesEditorModule

# NB the order matters!
# NB 'SG' must be before 'SP', as SpectrumGroups must be ready before Spectra
# Also parents must appear before their children

_classNamesInSidebar = ['SpectrumGroup', 'Spectrum', 'PeakList', 'IntegralList',
                        'Sample', 'SampleComponent', 'Substance', 'Complex', 'Chain',
                        'NmrChain', 'NmrResidue', 'NmrAtom', 'ChemicalShiftList',
                        'StructureEnsemble', 'Model', 'DataSet', 'RestraintList', 'Note', ]

# ll = [_coreClassMap[x] for x in _classNamesInSidebar]
# classesInSideBar = OrderedDict(((x.shortClassName, x) for x in ll))
classesInSideBar = OrderedDict(((x.shortClassName, x) for x in _coreClassMap.values()
                                if x.className in _classNamesInSidebar))
# classesInSideBar = ('SG', 'SP', 'PL', 'SA', 'SC', 'SU', 'MC', 'NC', 'NR', 'NA',
#                     'CL', 'SE', 'MO', 'DS',
#                     'RL', 'NO')

classesInTopLevel = ('SG', 'SP', 'SA', 'SU', 'MC', 'MX', 'NC', 'CL', 'SE', 'DS', 'NO')

# NBNB TBD FIXME
# 1)This function (and the NEW_ITEM_DICT) it uses gets the create_new
# function from the shortClassName of the PARENT!!!
# This is the only way to do it if the create_new functions are attributes of the PARENT!!!
#
# 2) <New> in makes a new SampleComponent. This is counterintuitive!
# Anyway, how do you make a new Sample?
# You use the <New> under sample, this comment is completely inaccurate!
#
# Try putting in e.g. <New PeakList>, <New SampleComponent> etc. Done in version 9855.

NEW_ITEM_DICT = {

  'SP': 'newPeakList',
  'NC': 'newNmrResidue',
  'NR': 'newNmrAtom',
  'DS': 'newRestraintList',
  'RL': 'newRestraint',
  'SE': 'newModel',
  'Notes': 'newNote',
  'StructureEnsembles': 'newStructureEnsemble',
  'Samples': 'newSample',
  'NmrChains': 'newNmrChain',
  'Chains': 'newChain',
  'Substances': 'newSubstance',
  'ChemicalShiftLists': 'newChemicalShiftList',
  'DataSets': 'newDataSet',
  'SpectrumGroups': 'newSpectrumGroup',
  'Complexes': 'newComplex',
}
### Flag example code removed in revision 7686

class SideBar(QtGui.QTreeWidget, Base):
  def __init__(self, parent=None, mainWindow=None, multiSelect=True):

    QtGui.QTreeWidget.__init__(self, parent)
    Base.__init__(self, acceptDrops=True)

    self.multiSelect = multiSelect
    if self.multiSelect:
      self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)

    self.mainWindow = parent                      # ejb - needed for moduleArea
    self.application = self.mainWindow.application
    self._typeToItem = dd = {}

    self.setFont(sidebarFont)
    self.header().hide()
    self.setDragEnabled(True)
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
    self.newSpectrumGroup.setText(0, "<New SpectrumGroup>")

    self.samplesItem = dd['SA'] = QtGui.QTreeWidgetItem(self.projectItem)
    self.samplesItem.setFlags(self.samplesItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.samplesItem.setText(0, 'Samples')

    self.newSample = QtGui.QTreeWidgetItem(self.samplesItem)
    self.newSample.setFlags(self.newSample.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.newSample.setText(0, "<New Sample>")

    self.substancesItem = dd['SU'] = QtGui.QTreeWidgetItem(self.projectItem)
    self.substancesItem.setFlags(self.substancesItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.substancesItem.setText(0, "Substances")

    self.newSubstance = QtGui.QTreeWidgetItem(self.substancesItem)
    self.newSubstance.setFlags(self.newSubstance.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.newSubstance.setText(0, "<New Substance>")

    self.chainItem = dd['MC'] = QtGui.QTreeWidgetItem(self.projectItem)
    self.chainItem.setFlags(self.chainItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.chainItem.setText(0, "Chains")

    self.newChainItem = QtGui.QTreeWidgetItem(self.chainItem)
    self.newChainItem.setFlags(self.newChainItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.newChainItem.setText(0, '<New Chain>')

    self.complexItem = dd['MX'] = QtGui.QTreeWidgetItem(self.projectItem)
    self.complexItem.setFlags(self.complexItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.complexItem.setText(0, "Complexes")

    # TODO make COmplexEditor, install it in _createNewObject, and uncomment this
    # self.newComplex = QtGui.QTreeWidgetItem(self.complexItem)
    # self.newComplex.setFlags(self.newComplex.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    # self.newComplex.setText(0, "<New Complex>")

    self.nmrChainItem = dd['NC'] = QtGui.QTreeWidgetItem(self.projectItem)
    self.nmrChainItem.setFlags(self.nmrChainItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.nmrChainItem.setText(0, "NmrChains")

    self.newNmrChainItem = QtGui.QTreeWidgetItem(self.nmrChainItem)
    self.newNmrChainItem.setFlags(self.newNmrChainItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.newNmrChainItem.setText(0, '<New NmrChain>')

    self.chemicalShiftListsItem = dd['CL'] = QtGui.QTreeWidgetItem(self.projectItem)
    self.chemicalShiftListsItem.setFlags(self.chemicalShiftListsItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.chemicalShiftListsItem.setText(0, "ChemicalShiftLists")

    self.newChemicalShiftListItem = QtGui.QTreeWidgetItem(self.chemicalShiftListsItem)
    self.newChemicalShiftListItem.setFlags(self.newChemicalShiftListItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.newChemicalShiftListItem.setText(0, '<New ChemicalShiftList>')

    self.structuresItem = dd['SE'] = QtGui.QTreeWidgetItem(self.projectItem)
    self.structuresItem.setFlags(self.structuresItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.structuresItem.setText(0, "StructureEnsembles")

    self.newStructuresListItem = QtGui.QTreeWidgetItem(self.structuresItem)   # ejb
    self.newStructuresListItem.setFlags(self.newStructuresListItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.newStructuresListItem.setText(0, '<New StructureEnsemble>')

    self.dataSetsItem = dd['DS'] = QtGui.QTreeWidgetItem(self.projectItem)
    self.dataSetsItem.setFlags(self.dataSetsItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.dataSetsItem.setText(0, "DataSets")

    self.newDataSetItem = QtGui.QTreeWidgetItem(self.dataSetsItem)
    self.newDataSetItem.setFlags(self.newDataSetItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.newDataSetItem.setText(0, '<New DataSet>')

    self.notesItem = dd['NO'] = QtGui.QTreeWidgetItem(self.projectItem)
    self.notesItem.setFlags(self.notesItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.notesItem.setText(0, "Notes")

    self.newNoteItem = QtGui.QTreeWidgetItem(self.notesItem)
    self.newNoteItem.setFlags(self.newNoteItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
    self.newNoteItem.setText(0, '<New Note>')

    self.mousePressEvent = self._mousePressEvent
    self.mouseReleaseEvent = self._mouseReleaseEvent
    # self.mouseMoveEvent = self._mouseMoveEvent
    self.dragMoveEvent = self._dragMoveEvent
    self.dragEnterEvent = self._dragEnterEvent

    self.setDragDropMode(self.DragDrop)
    self.setAcceptDrops(True)
    self.droppedNotifier = GuiNotifier(self,
                                       [GuiNotifier.DROPEVENT], [DropBase.URLS, DropBase.PIDS],
                                       self._processDroppedItems)

  #TODO:RASMUS: assure that there is a save query first before loading a project onto an existing roject
  #TODO:RASMUS: assure proper message once the project.loadData has been cleaned up
  def _processDroppedItems(self, data):
    "Handle the dropped urls"
    for url in data.get('urls',[]):
      # print('SideBar._processDroppedItems>>> dropped:', url)
      getLogger().info('SideBar._processDroppedItems>>> dropped: '+str(url))
      objects = self.project.loadData(url)
      # if objects is None or len(objects) == 0:
      #   showWarning('Invalid File', 'Cannot handle "%s"' % url)

  def setProject(self, project:Project):
    """
    Sets the specified project as a class attribute so it can be accessed from elsewhere
    """
    self.project = project

    # Register notifiers to maintain sidebar
    for cls in classesInSideBar.values():
      className = cls.className
      project.registerNotifier(className, 'delete', self._removeItem)
      if className != 'NmrResidue':
        project.registerNotifier(className, 'create', self._createItem)
        project.registerNotifier(className, 'rename', self._renameItem)
    project.registerNotifier('NmrResidue', 'create', self._refreshParentNmrChain)
    project.registerNotifier('NmrResidue', 'rename', self._renameNmrResidueItem)

    notifier = project.registerNotifier('SpectrumGroup', 'Spectrum', self._refreshSidebarSpectra,
                                        onceOnly=True)
    project.duplicateNotifier('SpectrumGroup', 'create', notifier)
    project.duplicateNotifier('SpectrumGroup', 'delete', notifier)
    # TODO:RASMUS Add similar set of notifiers, and similar function for Complex/Chain

  def _refreshSidebarSpectra(self, dummy:Project):
    """Reset spectra in sidebar - to be called from notifiers
    """
    for spectrum in self.project.spectra:
      # self._removeItem( self.project, spectrum)
      self._removeItem(spectrum)
      self._createItem(spectrum)
      for obj in spectrum.peakLists + spectrum.integralLists:
        self._createItem(obj)

  def _refreshParentNmrChain(self, nmrResidue:NmrResidue, oldPid:Pid=None):     # ejb - catch oldName
    """Reset NmrChain sidebar - needed when NmrResidue is created or renamed to trigger re-sort

    Replaces normal _createItem notifier for NmrResidues"""

    nmrChain = nmrResidue._parent

    # Remove NmrChain item and contents
    self._removeItem(nmrChain)

    # Create NmrResidue items again - this gives them in correctly sorted order
    self._createItem(nmrChain)
    for nr in nmrChain.nmrResidues:
      self._createItem(nr)
      for nmrAtom in nr.nmrAtoms:
        self._createItem(nmrAtom)

    # nmrChain = nmrResidue._parent     # ejb - just insert the 1 item
    # for nr in nmrChain.nmrResidues:
    #   if (nr.pid == nmrResidue.pid):
    #     self._createItem(nr)
    #
    # newPid = nmrChain.pid                   # ejb - expand the tree again from nmrChain
    # for item in self._findItems(newPid):
    #   item.setExpanded(True)

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

  def _deleteItemObject(self,  objs):
    """Removes the specified item from the sidebar and deletes it from the project.
    NB, the clean-up of the side bar is done through notifiers
    """
    for obj in objs:
      if obj:
        obj.delete()

  def _cloneObject(self, objs):
    """Clones the specified objects"""
    for obj in objs:
      obj.clone()

  def _createItem(self, obj:AbstractWrapperObject):
    """Create a new sidebar item from a new object.
    Called by notifier when a new object is created or undeleted (so need to check for duplicates).
    NB Obj may be of a type that does not have an item"""

    if not isinstance(obj, AbstractWrapperObject):
      return

    shortClassName = obj.shortClassName
    parent = obj._parent
    project = obj._project

    if shortClassName in classesInSideBar:

      if parent is project:

        if shortClassName == 'SP':
          # Spectrum - special behaviour - put them under SpectrumGroups, if any
          spectrumGroups = obj.spectrumGroups
          if spectrumGroups:
            for sg in spectrumGroups:

              # # ejb - search for the spectrumGroup, if not there then create it
              # sglist = self._findItems(str(sg.pid))
              # if not sglist:
              #   # have not found the group
              #   newTempSpectrumGroup = QtGui.QTreeWidgetItem(self.spectrumGroupItem)
              #   newTempSpectrumGroup.setFlags(
              #     newTempSpectrumGroup.flags() ^ QtCore.Qt.ItemIsDragEnabled)
              #   newTempSpectrumGroup.setText(0, str(sg.pid))
              #
              #   # sglist = self._findItems('SpectrumGroups')
              #   # for sgitem in self._findItems('SpectrumGroups'):
              #   #   newSpectrumGroup = QtGui.QTreeWidgetItem(sgitem)
              #   #   newSpectrumGroup.setFlags(
              #   #     newSpectrumGroup.flags() ^ QtCore.Qt.ItemIsDragEnabled)
              #   #   newSpectrumGroup.setText(0, str(sg.pid))
              #
              # # now carry on and insert the new groups

              for sgitem in self._findItems(str(sg.pid)):   # add '<new spectrumGroup>'
                newItem = self._addItem(sgitem, str(obj.pid))
                newObjectItem = QtGui.QTreeWidgetItem(newItem)
                newObjectItem.setFlags(newObjectItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
                newObjectItem.setText(0, "<New %s>" % classesInSideBar[shortClassName].className)

            return


        itemParent = self._typeToItem.get(shortClassName)
        newItem = self._addItem(itemParent, obj.pid)
        # itemParent.sortChildren(0, QtCore.Qt.AscendingOrder)
        if shortClassName in ['SA', 'NC', 'DS']:
          newObjectItem = QtGui.QTreeWidgetItem(newItem)
          newObjectItem.setFlags(newObjectItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
          newObjectItem.setText(0, "<New %s>" % classesInSideBar[shortClassName]._childClasses[0].className)

        if shortClassName == 'SP':
          newPeakListObjectItem = QtGui.QTreeWidgetItem(newItem)
          newPeakListObjectItem.setFlags(newPeakListObjectItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
          newPeakListObjectItem.setText(0, "<New PeakList>")
          newIntegralListObjectItem = QtGui.QTreeWidgetItem(newItem)
          newIntegralListObjectItem.setFlags(newIntegralListObjectItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
          newIntegralListObjectItem.setText(0, "<New IntegralList>")

      else:
        for itemParent in self._findItems(parent.pid):
          newItem = self._addItem(itemParent, obj.pid)

          if shortClassName == 'NR':
            newObjectItem = QtGui.QTreeWidgetItem(newItem)
            newObjectItem.setFlags(newObjectItem.flags() ^ QtCore.Qt.ItemIsDragEnabled)
            newObjectItem.setText(0, "<New NmrAtom>")
          # for i in range(itemParent.childCount()):
          #   itemParent.child(i).sortChildren(0, QtCore.Qt.AscendingOrder)

    else:
      # Object type is not in sidebar
      return None


  def _itemObjects(self, item, recursive=False):

    objects = [self.project.getByPid(item.data(0, QtCore.Qt.DisplayRole))]

    if recursive:
      for i in range(item.childCount()):
        child = item.child(i)
        if child.data(0, QtCore.Qt.DisplayRole)[:2] in classesInSideBar:
          objects.extend(self._itemObjects(child, recursive=True))

    return objects

  def _renameItem(self, obj:AbstractWrapperObject, oldPid:str):
    """rename item(s) from previous pid oldPid to current object pid"""

    import sip
    newPid = obj.pid
    for item in self._findItems(oldPid):
      # item.setData(0, QtCore.Qt.DisplayRole, str(obj.pid))    # ejb - rename instead of delete

      if Pid.IDSEP not in oldPid or oldPid.split(Pid.PREFIXSEP,1)[1].startswith(obj._parent._id + Pid.IDSEP):
        # Parent unchanged, just rename
        item.setData(0, QtCore.Qt.DisplayRole, str(newPid))
      else:
        # parent has changed - we must move and rename the entire item tree.
        # NB this is relevant for NmrAtom (NmrResidue is handled elsewhere)
        objects = self._itemObjects(item, recursive=True)
        sip.delete(item) # this also removes child items

        # NB the first object cannot be found from its pid (as it has already been renamed)
        # So we do it this way
        self._createItem(obj)
        for xx in objects[1:]:
          self._createItem(xx)

  def _renameNmrResidueItem(self, obj:NmrResidue, oldPid:str):
    """rename NmrResidue(s) from previous pid oldPid to current object pid"""

    if not oldPid.split(Pid.PREFIXSEP,1)[1].startswith(obj._parent._id + Pid.IDSEP):
      # Parent has changed - remove items from old location
      import sip
      for item in self._findItems(oldPid):
        sip.delete(item) # this also removes child items

    #    # item.setData(0, QtCore.Qt.DisplayRole, str(obj.pid))    # ejb - rename instead of delete
    # else:
    #   pass        # ejb - here just for a breakpoint

    self._refreshParentNmrChain(obj, oldPid)

    # for item in self._findItems(oldPid):
    #   item.setData(0, QtCore.Qt.DisplayRole, str(obj.pid))    # ejb - rename instead of delete

  def _removeItem(self, wrapperObject:AbstractWrapperObject):
    """Removes sidebar item(s) for object with pid objPid, but does NOT delete the object.
    Called when objects are deleted."""
    import sip
    for item in self._findItems(wrapperObject.pid):
      sip.delete(item)

  def _findItems(self, objPid:str) -> list:     #QtGui.QTreeWidgetItem
    """Find items that match objPid - returns empty list if no matches"""

    if objPid[:2] in classesInSideBar:
      result = self.findItems(objPid, QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive, 0)

    else:
      result = []

    return result

  def setProjectName(self, project:Project):
    """
    (re)set project name in sidebar header.
    """

    self.projectItem.setText(0, project.name)

  def fillSideBar(self, project:Project):
    """
    Fills the sidebar with the relevant data from the project.
    """

    self.setProjectName(project)

    #TODO: check that reversing the order of Spectrum and SpectrumGroup in the list works
    listOrder = [ky for ky in classesInSideBar.keys()]
    tempKy = listOrder[0]
    listOrder[0] = listOrder[1]
    listOrder[1] = tempKy
    new_dict = OrderedDict()
    for ky in listOrder:
      new_dict[ky] = classesInSideBar[ky]

    for className, cls in new_dict.items():       # ejb - classesInSideBar.items()
      for obj in getattr(project, cls._pluralLinkName):
        self._createItem(obj)
      # dd = pid2Obj.get(className)
      # if dd:
      #   for obj in sorted(dd.values()):
      #     self._createItem(obj)

  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  # mouse events

  def _dragEnterEvent(self, event, enter=True):
    # if event.mimeData().hasFormat(ccpnmrJsonData):
    #   data = event.mimeData().data(ccpnmrJsonData)
    #   if 'test' in data:
    #     print ('>>>_dragEnterEvent has ccpnmrJsonData')
    #   else:
    #     print ('>>>_dragEnterEvent empty')
    # else:
    #   print('>>>_dragEnterEvent ---')
    # super(SideBar, self).dragEnterEvent(event)

    if event.mimeData().hasUrls():
      event.accept()
    else:
      pids = []
      for item in self.selectedItems():
        if item is not None:
          objFromPid = self.project.getByPid(item.data(0, QtCore.Qt.DisplayRole))
          if objFromPid is not None:
            pids.append(objFromPid.pid)

      itemData = json.dumps({'pids':pids})
      event.mimeData().setData(ccpnmrJsonData, itemData)
      event.mimeData().setText(itemData)
      event.accept()

  # def _startDrag(self, dropActions):
  #   item = self.currentItem()
  #   icon = item.icon()
  #   data = QByteArray()
  #   stream = QDataStream(data, QIODevice.WriteOnly)
  #   stream << item.text() << icon
  #   mimeData = QMimeData()
  #   mimeData.setData("application/x-icon-and-text", data)
  #   drag = QDrag(self)
  #   drag.setMimeData(mimeData)
  #   pixmap = icon.pixmap(24,24)
  #   drag.setHotSpot(QPoint(12,12))
  #   drag.setPixmap(pixmap)
  #   if drag.start(Qt.MoveAction) == Qt.moveAction:
  #     self.takeItem(self.row(item))

  def _dragMoveEvent(self, event:QtGui.QMouseEvent):
    """
    Required function to enable dragging and dropping within the sidebar.
    """
    event.accept()

  def dragLeaveEvent(self, event):
    # print ('>>>dragLeaveEvent %s' % str(event.type()))
    super(SideBar, self).dragLeaveEvent(event)
    event.accept()

  def _mouseMoveEvent(self, event):
    event.accept()

  def _mousePressEvent(self, event):
    """
    Re-implementation of the mouse press event so right click can be used to delete items from the
    sidebar.
    """

    # if event.button() == QtCore.Qt.LeftButton:
    #   pids = []
    #   for item in self.selectedItems():
    #     if item is not None:
    #       objFromPid = self.project.getByPid(item.data(0, QtCore.Qt.DisplayRole))
    #       if objFromPid is not None:
    #         pids.append(objFromPid.pid)
    #
    #   itemData = json.dumps({'pids':pids, 'test':'thisDrag'})
    #   mimeData = QtCore.QMimeData()
    #   mimeData.setData(ccpnmrJsonData, itemData)
    #   mimeData.setText(itemData)
    #
    #   drag = QtGui.QDrag(self)
    #   drag.setMimeData(mimeData)
    #   dropAction = drag.exec_(QtCore.Qt.CopyAction | QtCore.Qt.MoveAction, QtCore.Qt.CopyAction)

    # if event.button() == QtCore.Qt.RightButton:
    #   self._raiseContextMenu(event)
    #   event.accept()
    # else:
    # item = self.itemAt(event.pos())
    # if item:
    #   text = item.text(0)
    #   if ':' in text:
    #
    #     itemData = json.dumps({'pids':[text]})
    #     mimeData = QtCore.QMimeData()
    #     mimeData.setData(ccpnmrJsonData, itemData)
    #     # mimeData.setText(itemData)
    #     # pixmap = QtGui.QPixmap.grabWidget(item)
    #     # pixmap = QtGui.QPixmap(item)
    #     # item.render(pixmap)
    #
    #     drag = QtGui.QDrag(self)
    #     drag.setMimeData(mimeData)
    #     # drag.setPixmap(pixmap)
    #
    #     dropAction = drag.exec_(QtCore.Qt.CopyAction | QtCore.Qt.MoveAction, QtCore.Qt.CopyAction)
    #   else:
    #     super(SideBar, self).mousePressEvent(event)

    # else:
    QtGui.QTreeWidget.mousePressEvent(self, event)

  def _mouseReleaseEvent(self, event):
    """
    Re-implementation of the mouse press event so right click can be used to delete items from the
    sidebar.
    """
    if event.button() == QtCore.Qt.RightButton:
      self._raiseContextMenu(event)               # ejb - moved the context menu to button release
      event.accept()
    else:
      QtGui.QTreeWidget.mouseReleaseEvent(self, event)

  def enterEvent(self, event):
    # print ('>>>enterEvent')
    super(SideBar, self).enterEvent(event)

  def leaveEvent(self, event):
    # print ('>>>leaveEvent')
    super(SideBar, self).leaveEvent(event)

  def _raiseContextMenu(self, event:QtGui.QMouseEvent):
    """
    Creates and raises a context menu enabling items to be deleted from the sidebar.
    """
    from ccpn.ui.gui.widgets.Menu import Menu
    contextMenu = Menu('', self, isFloatWidget=True)
    from functools import partial
    # contextMenu.addAction('Delete', partial(self.removeItem, item))
    objs = []
    for item in self.selectedItems():
      if item is not None:
        objFromPid = self.project.getByPid(item.data(0, QtCore.Qt.DisplayRole))
        if objFromPid is not None:
          objs.append(objFromPid)

    if len(objs)>0:
      contextMenu.addAction('Delete', partial(self._deleteItemObject, objs))
      canBeCloned = True
      for obj in objs:
        if not hasattr(obj, 'clone'):  # TODO: possibly should check that is a method...
          canBeCloned = False
          break
      if canBeCloned:
        contextMenu.addAction('Clone', partial(self._cloneObject, objs))
      contextMenu.move(event.globalPos().x(), event.globalPos().y() + 10)
      contextMenu.exec()

  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  def raisePopup(self, obj, item):

    if obj.shortClassName == 'SP':
      popup = SpectrumPropertiesPopup(mainWindow=self.mainWindow, spectrum=obj)
      popup.exec_()
      popup.raise_()
    elif obj.shortClassName == 'PL':
      popup = PeakListPropertiesPopup(mainWindow=self.mainWindow, peakList=obj)
      popup.exec_()
      popup.raise_()
    elif obj.shortClassName == 'SG':
      popup = SpectrumGroupEditor(mainWindow=self.mainWindow, spectrumGroup=obj)
      popup.exec_()
      popup.raise_()
    elif obj.shortClassName == 'SA':
      popup = SamplePropertiesPopup(mainWindow=self.mainWindow, sample=obj)
      popup.exec_()
      popup.raise_()
    elif obj.shortClassName == 'SC':
      popup = EditSampleComponentPopup(mainWindow=self.mainWindow, sampleComponent=obj)
      popup.exec_()
      popup.raise_()
    elif obj.shortClassName == 'SU':
      popup = SubstancePropertiesPopup(mainWindow=self.mainWindow, substance=obj)
      popup.exec_()
      popup.raise_()
    elif obj.shortClassName == 'NC':
      popup = NmrChainPopup(mainWindow=self.mainWindow, nmrChain=obj)
      popup.exec_()
      popup.raise_()
    elif obj.shortClassName == 'NR':
      popup = NmrResiduePopup(mainWindow=self.mainWindow, nmrResidue=obj)
      popup.exec_()
      popup.raise_()
    elif obj.shortClassName == 'NA':
      popup = NmrAtomPopup(mainWindow=self.mainWindow, nmrAtom=obj)
      popup.exec_()
      popup.raise_()
    elif obj.shortClassName == 'CL':
      popup = ChemicalShiftListPopup(mainWindow=self.mainWindow, chemicalShiftList=obj)
      popup.exec_()
      popup.raise_()
    elif obj.shortClassName == 'SE':
      popup = StructurePopup(mainWindow=self.mainWindow, structure=obj)
      popup.exec_()
      popup.raise_()

      # if self.mainWindow:
      #   from ccpn.ui.gui.modules.StructureTable import StructureTableModule
      #
      #   self.structureTableModule = StructureTableModule(self.mainWindow, itemPid=obj.pid)
      #   self.mainWindow.moduleArea.addModule(self.structureTableModule, position='bottom',
      #                                   relativeTo=self.mainWindow.moduleArea)
      #   self.mainWindow.pythonConsole.writeConsoleCommand("application.showStructureTable()")
      #   self.project._logger.info("application.showStructureTable()")
      #
      # else:
      #   showInfo('No mainWindow?', '')

    elif obj.shortClassName == 'MC':
      #to be decided when we design structure
      info = showInfo('Not implemented yet!',
          'This function has not been implemented in the current version')
    elif obj.shortClassName == 'MD':
      #to be decided when we design structure
      showInfo('Not implemented yet!',
          'This function has not been implemented in the current version')
    elif obj.shortClassName == 'DS':
      popup = DataSetPopup(mainWindow=self.mainWindow, dataSet=obj)
      popup.exec_()
      popup.raise_()

      # ejb - test DataSet
      # if self.mainWindow:
      #
      #   # Use StructureTable for the moment
      #
      #   if obj.title is 'ensembleCCPN':
      #     from ccpn.ui.gui.modules.StructureTable import StructureTableModule
      #
      #     self.structureTableModule = StructureTableModule(self.mainWindow, itemPid=obj.pid)
      #     self.mainWindow.moduleArea.addModule(self.structureTableModule, position='bottom',
      #                                     relativeTo=self.mainWindow.moduleArea)
      #     self.mainWindow.pythonConsole.writeConsoleCommand("application.showDataSetStructureTable()")
      #     self.project._logger.info("application.showDataSetStructureTable()")
      #   else:
      #     showInfo('Not implemented yet!',
      #              'This function has not been implemented in the current version',
      #              colourScheme=self.colourScheme)


    elif obj.shortClassName == 'RL':
      #to be decided when we design structure
      showInfo('Not implemented yet!',
          'This function has not been implemented in the current version')
    elif obj.shortClassName == 'RE':
      #to be decided when we design structure
      showInfo('Not implemented yet!',
          'This function has not been implemented in the current version')
    elif obj.shortClassName == 'IL':
      # to be decided when we design structure

      # popup = IntegralListPopup(mainWindow=self.mainWindow, integralList=obj)   # ejb - temp
      # popup.exec_()
      # popup.raise_()

      showInfo('Not implemented yet!',
               'This function has not been implemented in the current version')
    elif obj.shortClassName == 'NO':
      popup = NotesPopup(mainWindow=self.mainWindow, note=obj)
      popup.exec_()
      popup.raise_()

      # if self._application.ui.mainWindow is not None:
      #   mainWindow = self._application.ui.mainWindow
      # else:
      #   mainWindow = self._application._mainWindow
      # self.notesEditor = NotesEditor(mainWindow.moduleArea, self.project,
      #                                name='Notes Editor', note=obj)

      # #FIXME:ED should be a popup or consistency
      # if self.mainWindow:
      #   self.notesEditor = NotesEditor(mainWindow=self.mainWindow, name='Notes Editor', note=obj)
      #   self.mainWindow.moduleArea.addModule(self.notesEditor, position='bottom',
      #                                   relativeTo=self.mainWindow.moduleArea)
      #   self.mainWindow.pythonConsole.writeConsoleCommand("application.showNotesEditor()")
      #   self.project._logger.info("application.showNotesEditor()")
      # else:
      #   showInfo('No mainWindow?', '', colourScheme=self.colourScheme)


  def _createNewObject(self, item):
    """Create new object starting from the <New> item
    """

    if item.text(0) == "<New IntegralList>" or item.text(0) == "<New PeakList>":

      if item.text(0) == "<New PeakList>":
        self.project.getByPid(item.parent().text(0)).newPeakList()
      if item.text(0) == "<New IntegralList>":
        self.project.getByPid(item.parent().text(0)).newIntegralList()

      # item.parent().sortChildren(0, QtCore.Qt.AscendingOrder)

    else:

      itemParent = self.project.getByPid(item.parent().text(0))

      funcName = None
      if itemParent is None:
        # Top level object - parent is project
        if item.parent().text(0) == 'Chains':
          popup = CreateChainPopup(mainWindow=self.mainWindow)
          popup.exec_()
          popup.raise_()
          return
        elif item.parent().text(0) == 'Substances':
          popup = SubstancePropertiesPopup(mainWindow=self.mainWindow, newSubstance=True)   # ejb - application=self.application,
          popup.exec_()
          popup.raise_()        # included setModal(True) in the above as was not modal???
          return
        elif item.parent().text(0) == 'SpectrumGroups':
          popup = SpectrumGroupEditor(mainWindow=self.mainWindow, addNew=True)
          popup.exec_()
          popup.raise_()
          return
        else:
          itemParent = self.project
          funcName = NEW_ITEM_DICT.get(item.parent().text(0))


      else:
        # Lower level object - get parent from parentItem
        if itemParent.shortClassName == 'DS':
          popup = RestraintTypePopup(mainWindow=self.mainWindow)
          popup.exec_()
          popup.raise_()
          restraintType = popup.restraintType
          if restraintType:

            # ejb - added here because not sure whether to put it in the popup yet
            try:
              ff = NEW_ITEM_DICT.get(itemParent.shortClassName)
              getattr(itemParent, ff)(restraintType)
            except Exception as es:
              showWarning('Restraints', 'Error modifying restraint type')

          return
        elif itemParent.shortClassName == 'SA':
          popup = EditSampleComponentPopup(mainWindow=self.mainWindow, sample=itemParent, newSampleComponent=True)
          popup.exec_()
          popup.raise_()
          return
        else:
          funcName = NEW_ITEM_DICT.get(itemParent.shortClassName)

        # for i in range(item.childCount()):

      if funcName is not None:
        newItem = getattr(itemParent, funcName)()
        # if funcName == 'newNmrResidue':
        #   newItem.parent().sortChildren(0, QtCore.Qt.AscendingOrder)

      else:
        info = showInfo('Not implemented yet!',
            'This function has not been implemented in the current version')





