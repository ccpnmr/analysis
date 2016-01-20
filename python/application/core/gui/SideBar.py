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
from application.core.popups.PeakListPropertesPopup import PeakListPropertiesPopup
from application.core.popups.RestraintTypePopup import RestraintTypePopup
from application.core.popups.SpectrumPropertiesPopup import SpectrumPropertiesPopup
from application.core.popups.SamplePropertiesPopup import SamplePropertiesPopup, EditSampleComponentPopup


from ccpn import Project
from ccpn import Spectrum

from ccpncore.util.Pid import Pid
from ccpncore.util.Types import Sequence

NEW_ITEM_DICT = {
  'SP': 'newPeakList',
  'NC': 'newNmrResidue',
  'NR': 'newNmrAtom',
  'RS': 'newRestraintList',
  'RL': 'newRestraint',
  'SE': 'newModel',
  'Notes': 'newNote',
  'Structures': 'newStructureEnsemble',
  'Samples': 'newSample',
  'NmrChains': 'newNmrChain',
  'Chains': 'CreateSequence',
  'Substances': 'newSubstance',
  'Chemical Shift Lists': 'newChemicalShiftList',
  'Restraint Sets': 'newRestraintSet',
}


class SideBar(DropBase, QtGui.QTreeWidget):
  def __init__(self, parent=None ):
    QtGui.QTreeWidget.__init__(self, parent)

    self.setFont(QtGui.QFont('Lucida Grande', 12))
    self.header().hide()
    self.setDragEnabled(True)
    self._appBase = parent._appBase
    self.setExpandsOnDoubleClick(False)
    self.setDragDropMode(self.InternalMove)
    self.setFixedWidth(200)
    self.projectItem = QtGui.QTreeWidgetItem(self)
    self.projectItem.setText(0, "Project")
    self.projectItem.setExpanded(True)
    self.spectrumItem = QtGui.QTreeWidgetItem(self.projectItem)
    self.spectrumItem.setText(0, "Spectra")
    self.samplesItem = QtGui.QTreeWidgetItem(self.projectItem)
    self.samplesItem.setText(0, 'Samples')
    self.newSample = QtGui.QTreeWidgetItem(self.samplesItem)
    self.newSample.setText(0, "<New>")
    self.substancesItem = QtGui.QTreeWidgetItem(self.projectItem)
    self.substancesItem.setText(0, "Substances")
    self.newSubstanceItem = QtGui.QTreeWidgetItem(self.substancesItem)
    self.newSubstanceItem.setText(0, '<New>')
    self.chainItem = QtGui.QTreeWidgetItem(self.projectItem)
    self.chainItem.setText(0, "Chains")
    self.newChainItem = QtGui.QTreeWidgetItem(self.chainItem)
    self.newChainItem.setText(0, '<New>')
    self.nmrChainItem = QtGui.QTreeWidgetItem(self.projectItem)
    self.nmrChainItem.setText(0, "NmrChains")
    self.newNmrChainItem = QtGui.QTreeWidgetItem(self.nmrChainItem)
    self.newNmrChainItem.setText(0, '<New>')
    self.chemicalShiftListsItem = QtGui.QTreeWidgetItem(self.projectItem)
    self.chemicalShiftListsItem.setText(0, "Chemical Shift Lists")
    self.newChemicalShiftListItem = QtGui.QTreeWidgetItem(self.chemicalShiftListsItem)
    self.newChemicalShiftListItem.setText(0, '<New>')
    self.structuresItem = QtGui.QTreeWidgetItem(self.projectItem)
    self.structuresItem.setText(0, "Structures")
    self.restraintSetsItem = QtGui.QTreeWidgetItem(self.projectItem)
    self.restraintSetsItem.setText(0, "Restraint Sets")
    self.newRestraintSetItem = QtGui.QTreeWidgetItem(self.restraintSetsItem)
    self.newRestraintSetItem.setText(0, '<New>')
    self.notesItem = QtGui.QTreeWidgetItem(self.projectItem)
    self.notesItem.setText(0, "Notes")
    self.newNoteItem = QtGui.QTreeWidgetItem(self.notesItem)
    self.newNoteItem.setText(0, '<New>')



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
        anItem = QtGui.QTreeWidgetItem(newItem)
        anItem.setText(0, '<New>')
        for peakList in spectrum.peakLists:
          peakListItem = QtGui.QTreeWidgetItem(newItem)
          peakListItem.setText(0, peakList.pid)

    for chain in project.chains:
      newItem = self.addItem(self.chainItem, chain)
    for nmrChain in project.nmrChains:
      newItem = self.addItem(self.nmrChainItem, nmrChain)
      for nmrResidue in nmrChain.nmrResidues:
        newItem3 = self.addItem(newItem, nmrResidue)
        for nmrAtom in nmrResidue.nmrAtoms:
          newItem5 = self.addItem(newItem3, nmrAtom)
    for chemicalShiftList in project.chemicalShiftLists:
      newItem = self.addItem(self.chemicalShiftListsItem, chemicalShiftList)

    for restraintSet in project.restraintSets:
      newItem = self.addItem(self.restraintSetsItem, restraintSet)
      newItem2 = QtGui.QTreeWidgetItem(newItem)
      newItem2.setText(0, '<New>')
      for restraintList in restraintSet.restraintLists:
        newItem4 = self.addItem(newItem, restraintList)
        newItem3 = QtGui.QTreeWidgetItem(newItem4)
        newItem3.setText(0, '<New>')
        for restraint in restraintList.restraints:
          newItem5 = self.addItem(newItem4, restraint)

    for structureEnsemble in project.structureEnsembles:
      newItem = self.addItem(self.structuresItem, structureEnsemble)
      for model in structureEnsemble.models:
        newItem3 = self.addItem(newItem, model)

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

  def addSpectrum(self, spectrum:(Spectrum,Pid)):
    """
    Adds the specified spectrum to the sidebar.
    """
    peakList = spectrum.newPeakList()
    newItem = self.addItem(self.spectrumItem, spectrum)
    peakListItem = QtGui.QTreeWidgetItem(newItem)
    peakListItem.setText(0, peakList.pid)

  def processNotes(self, pids:Sequence[str], event):
    """Display notes defined by list of Pid strings"""
    for ss in pids:
      note = self.project.getByPid(ss)
      self.addItem(self.notesItem, note)

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
    elif obj.shortClassName == 'RS':
      pass #to be decided when we design structure
    elif obj.shortClassName == 'RL':
      pass #to be decided when we design structure
    elif obj.shortClassName == 'RE':
      pass #to be decided when we design structure
    elif obj.shortClassName == 'NO':
      self.notesEditor = NotesEditor(self._appBase.mainWindow.dockArea, name='Notes Editor', note=obj, item=item)

  def createNewObject(self, item):

    itemParent = self.project.getByPid(item.parent().text(0))
    if itemParent is not None:
      if itemParent.shortClassName == 'RS':
        popup = RestraintTypePopup()
        popup.exec_()
        popup.raise_()
        restraintType = popup.restraintType
        funcName = NEW_ITEM_DICT.get(itemParent.shortClassName)
        newItem = getattr(itemParent, funcName)(restraintType)
        self.addItem(item.parent(), newItem)
      elif item.parent.shortClassName == 'SA':
        newComponent = itemParent.newSampleComponent()
        popup = EditSampleComponentPopup(sampleComponent=newComponent)
        popup.exec_()
        popup.raise_()
        return
      else:
        funcName = NEW_ITEM_DICT.get(itemParent.shortClassName)

    else:
      if item.parent().text(0) == 'Chains':
        popup = CreateSequence(project=self.project)
        popup.exec_()
        popup.raise_()
        return
      else:
        itemParent = self.project
        funcName = NEW_ITEM_DICT.get(item.parent().text(0))

    newItem = getattr(itemParent, funcName)()
    self.addItem(item.parent(), newItem)
