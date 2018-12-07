"""
Module Documentation here
# TODO : when update module, keep focus on selected item in the table, keep same zoom on the plot
check zoom

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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:46 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-04-07 10:28:43 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from functools import partial
from PyQt5 import QtCore, QtGui, QtWidgets
import random
import os
import numpy as np
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.modules.NmrResidueTable import NmrResidueTable
from ccpn.ui.gui.widgets.BarGraph import BarGraph
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.SpectraSelectionWidget import SpectraSelectionWidget
from ccpn.ui.gui.widgets.CheckBox import CheckBox, EditableCheckBox
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.FileDialog import LineEditButtonDialog
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.ui.gui.widgets.Column import ColumnClass
from ccpn.core.lib.Notifiers import Notifier
from ccpn.util.Colour import spectrumColours, hexToRgb
from ccpn.core.lib.peakUtils import getNmrResidueDeltas, MODES, LINEWIDTHS, HEIGHT, POSITIONS, VOLUME, DefaultAtomWeights, H, N, OTHER, C
from ccpn.core.lib import CcpnSorting
from ccpn.core.NmrChain import NmrChain
from ccpn.core.Project import Project
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.widgets.BarGraphWidget import BarGraphWidget
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets.Splitter import Splitter
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.guiSettings import COLOUR_SCHEMES, getColours, DIVIDER
import random
from ccpn.ui.gui.widgets.ConcentrationsWidget import ConcentrationWidget
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.util.Constants import concentrationUnits



def chemicalShiftMappingPymolTemplate(filePath, pdbPath, aboveThresholdResidues, belowThresholdResidues,
                                      missingdResidues, colourMissing, colourAboveThreshold,
                                      colourBelowThreshold, selection):

  if os.path.exists(pdbPath):
    warn = 'This script is auto-generated. Any changes here will be lost.'
    with open(filePath, 'w') as f:
      f.write('''\n"""''' + warn + '''"""''')
      f.write('''\nfrom pymol import cmd''')
      f.write('''\n''')
      f.write('''\ncmd.load("''' + pdbPath + '''") ''')
      f.write('''\ncmd.hide('lines')''')
      f.write('''\ncmd.show('cartoon')''')
      f.write('''\ncmd.color('white')''')
      if len(aboveThresholdResidues)>0:
        f.write('''\ncmd.select('aboveThreshold', 'res  ''' + aboveThresholdResidues + ''' ')''')
        f.write('''\ncmd.set_color("AboveColour", " ''' + str(colourAboveThreshold) + ''' ")''')
        f.write('''\ncmd.color('AboveColour', 'aboveThreshold')''')
      if len(belowThresholdResidues) > 0:
        f.write('''\ncmd.select('belowThreshold', 'res  ''' + belowThresholdResidues + ''' ')''')
        f.write('''\ncmd.set_color("BelowColour", " ''' + str(colourBelowThreshold) + ''' ")''')
        f.write('''\ncmd.color('BelowColour', 'belowThreshold')''')
      if len(missingdResidues) > 0:
        f.write('''\ncmd.select('missing', 'res  ''' + missingdResidues + ''' ')''')
        f.write('''\ncmd.set_color("MissingColour", " ''' + str(colourMissing) + ''' ")''')
        f.write('''\ncmd.color('MissingColour', 'missing')''')
      if len(selection)>0:
        f.write('''\ncmd.select('Selected', 'res  ''' + selection + ''' ')''')
      else:
        f.write('''\ncmd.deselect()''')

  return filePath

DefaultConcentration = 0.0
DefaultConcentrationUnit = concentrationUnits[0]
DefaultThreshould = 0.1
PymolScriptName = 'chemicalShiftMapping_Pymol_Template.py'

MORE, LESS = 'More', 'Fewer'
PreferredNmrAtoms = ['H', 'HA', 'HB', 'C', 'CA', 'CB', 'N', 'NE', 'ND']


class CustomNmrResidueTable(NmrResidueTable):
  """
  Custon nmrResidue Table with extra Delta column
  """
  deltaShiftsColumn = ('Deltas', lambda nmrResidue: nmrResidue._delta, '', None)


  def __init__(self, parent=None, mainWindow=None, moduleParent=None, actionCallback=None, selectionCallback=None,
               checkBoxCallback=None, nmrChain=None, **kwds):

    # NmrResidueTable.__init__(self, parent=parent, application=application,actionCallback=actionCallback,
    #                          selectionCallback=selectionCallback, nmrChain=nmrChain, multiSelect = True, **kwds)

    NmrResidueTable.__init__(self, parent=parent, mainWindow=mainWindow,
                             moduleParent=moduleParent,
                             actionCallback=actionCallback,
                             selectionCallback=selectionCallback,
                             checkBoxCallback = checkBoxCallback,
                             nmrChain=nmrChain,
                             multiSelect=True,
                             **kwds)

    self.NMRcolumns = ColumnClass([
        ('#', lambda nmrResidue: nmrResidue.serial, 'NmrResidue serial number', None),
        ('Pid', lambda nmrResidue:nmrResidue.pid, 'Pid of NmrResidue', None),
        ('_object', lambda nmrResidue:nmrResidue, 'Object', None),
        ('Index', lambda nmrResidue: NmrResidueTable._nmrIndex(nmrResidue), 'Index of NmrResidue in the NmrChain', None),
        ('Sequence', lambda nmrResidue: nmrResidue.sequenceCode, 'Sequence code of NmrResidue', None),
        ('Type', lambda nmrResidue: nmrResidue.residueType, 'NmrResidue type', None),
        ('Selected', lambda nmrResidue: CustomNmrResidueTable._getSelectedNmrAtomNames(nmrResidue), 'NmrAtoms selected in NmrResidue', None),
        ('Spectra', lambda nmrResidue: CustomNmrResidueTable._getNmrResidueSpectraCount(nmrResidue)
         , 'Number of spectra selected for calculating the deltas', None),
        ('Deltas', lambda nmrResidue: nmrResidue._delta, '', None),
        ('Include', lambda nmrResidue: nmrResidue._includeInDeltaShift, 'Include this residue in the Mapping calculation', lambda nmr, value: CustomNmrResidueTable._setChecked(nmr, value)),
        # ('Flag', lambda nmrResidue: nmrResidue._flag,  '',  None),
        ('Comment', lambda nmr: NmrResidueTable._getCommentText(nmr), 'Notes', lambda nmr, value: NmrResidueTable._setComment(nmr, value))
      ])        #[Column(colName, func, tipText=tipText, setEditValue=editValue) for colName, func, tipText, editValue in self.columnDefs]

    self._widget.setFixedHeight(45)
    self.chemicalShiftsMappingModule = None


  @staticmethod
  def _setChecked(obj, value):
    """
    CCPN-INTERNAL: Insert a comment into QuickTable
    """

    obj._includeInDeltaShift = value
    obj._finaliseAction('change')

  @staticmethod
  def _getNmrResidueSpectraCount(nmrResidue):

    """
    CCPN-INTERNAL: Insert an index into ObjectTable
    """
    try:
      return nmrResidue.spectraCount
    except:
      return None

  @staticmethod
  def _getSelectedNmrAtomNames(nmrResidue):

    """
    CCPN-INTERNAL: Insert an index into ObjectTable
    """
    try:
      return ', '.join(nmrResidue.selectedNmrAtomNames)
    except:
      return None

  def _selectPullDown(self, value):
    ''' Used for automatic restoring of widgets '''
    self.ncWidget.select(value)
    try:
      if self.chemicalShiftsMappingModule is not None:
        self.chemicalShiftsMappingModule.updateModule()
    except Exception as e:
      getLogger().warn('Impossible update chemicalShiftsMappingModule from restoring %s' %e)



class ChemicalShiftsMapping(CcpnModule):

  includeSettingsWidget = True
  maxSettingsState = 2  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
  settingsPosition = 'left'
  className = 'ChemicalShiftsMapping'

  def __init__(self, mainWindow, name='Chemical Shift Mapping', nmrChain= None, **kwds):
    CcpnModule.__init__(self, mainWindow=mainWindow, name=name, settingButton=True)

    BarGraph.mouseClickEvent = self._mouseClickEvent
    BarGraph.mouseDoubleClickEvent = self._mouseDoubleClickEvent

    self.mainWindow = mainWindow
    self.application = None
    self.OtherAtoms = set()
    self.Natoms = set()
    self.Hatoms = set()
    self.Catoms = set()
    self.atomWeightSpinBoxes = []
    self.nmrAtomsCheckBoxes = []
    self.nmrAtomsLabels = []
    self.atomNames = []
    if self.mainWindow is not None:
      self.project = self.mainWindow.project
      self.application = self.mainWindow.application
      self.current = self.application.current

      # if len(self.project.nmrResidues):
      #
      #   for i in self.project.nmrResidues:
      #     for atom in i.nmrAtoms:
      #       # self.atoms.add(atom.name)
      #       if 'N' in atom.name:
      #         self.Natoms.add(atom.name)
      #         self.atomNames.append('N')
      #       if 'H' in atom.name:
      #         self.Hatoms.add(atom.name)
      #         self.atomNames.append('H')
      #       if 'C' in atom.name:
      #         self.Hatoms.add(atom.name)
      #         self.atomNames.append('C')
      #       else:
      #         self.OtherAtoms.add(atom.name)
      #         self.atomNames.append('Others')


    self.thresholdLinePos = DefaultThreshould

    self.showStructureIcon = Icon('icons/showStructure')
    self.updateIcon = Icon('icons/update')

    self._setWidgets()
    self._setSettingsWidgets()
    if self.mainWindow:
      self._selectCurrentNmrResiduesNotifier = Notifier(self.current , [Notifier.CURRENT] , targetName='nmrResidues'
                                                       , callback=self._selectCurrentNmrResiduesNotifierCallback)
      self._peakDeletedNotifier = Notifier(self.project, [Notifier.DELETE], 'Peak', self._peakDeletedCallBack)

      # self._peakChangedNotifier = Notifier(self.project, [Notifier.CHANGE], 'Peak',
      #                                        self._peakChangedCallBack, onceOnly=True)
      # self._peakChangedNotifier.lastPeakPos = None

      self._nrChangedNotifier = Notifier(self.project, [Notifier.CHANGE], 'NmrResidue',self._nmrObjectChanged)
      self._nrDeletedNotifier = Notifier(self.project, [Notifier.DELETE], 'NmrResidue',self._nmrResidueDeleted)

      if self.project:
        if len(self.project.nmrChains) > 0:
          self.nmrResidueTable.ncWidget.select(self.project.nmrChains[-1].pid)
          # self._updateNmrAtomsOption()
          # self._hideNonNecessaryNmrAtomsOption()
          self._setThresholdLineBySTD()

      self.__addCheckBoxesAttr(self.nmrAtomsCheckBoxes)

  def __addCheckBoxesAttr(self, checkboxes):
    '''For restoring layouts only '''
    for n, w in enumerate(checkboxes):
      setattr(self,w.text(), w )


  def _availableNmrAtoms(self,source=None, nmrAtomType = None):
    '''
    source = ccpn object: Project or nmrChain, Default project.
    returns sorted nmrAtoms names present in nmrResidues of the selected  source.
    Used to init the option. The module starts with all nmr atoms available in the project and hides/shows only for the selected nmrChain in the pulldown.
    This solutions is a bit slower on opening the first time but makes faster switching between nmrChains.
    '''
    if source is None:
      source = self.project

    if source is not None and isinstance(source, (NmrChain, Project)):
      nmrAtoms = []
      for nmrResidue in source.nmrResidues:
        nmrAtoms += nmrResidue.nmrAtoms
      if len(nmrAtoms)>0:
        availableNmrAtoms =  list(set([nmrAtom.name for nmrAtom in nmrAtoms]))
        allAvailable = sorted(availableNmrAtoms, key=CcpnSorting.stringSortKey)
        if nmrAtomType:
          return [na for na in allAvailable if na.startswith(nmrAtomType) ]
        else:
          return allAvailable
    return []

  def _setWidgets(self):
    self.nmrResidueTable = None
    self.barGraphWidget = None

    if self.application:
      self.splitter = Splitter(horizontal=False)

      self.barGraphWidget = BarGraphWidget(self.mainWidget, application=self.application, grid = (1, 0))
      self.barGraphWidget.setViewBoxLimits(0,None,0,None)
      self.barGraphWidget.xLine.setPos(DefaultThreshould)
      self.barGraphWidget.xLine.sigPositionChangeFinished.connect(self._threshouldLineMoved)
      self.barGraphWidget.customViewBox.mouseClickEvent = self._viewboxMouseClickEvent
      self.nmrResidueTable = CustomNmrResidueTable(parent=self.mainWidget, mainWindow=self.mainWindow,
                                                   actionCallback= self._customActionCallBack, checkBoxCallback=self._checkBoxCallback,
                                                   setLayout=True, grid = (0, 0))
      self.nmrResidueTable.chemicalShiftsMappingModule = self

      self.showOnViewerButton = Button(self.nmrResidueTable._widget, tipText='Show on Molecular Viewer',
                                       icon=self.showStructureIcon,
                                       callback=self._showOnMolecularViewer,
                                       grid = (1, 1), hAlign='l')
      self.showOnViewerButton.setFixedHeight(25)

      self.updateButton1 = Button(self.nmrResidueTable._widget, text='', icon=self.updateIcon,
                                  tipText='Update all', callback=self.updateModule,
                                 grid=(1, 2), hAlign='r' )
      self.updateButton1.setFixedHeight(25)
      # self.showOnViewerButton.setFixedWidth(150)
      self.nmrResidueTable.displayTableForNmrChain = self._displayTableForNmrChain
      self.barGraphWidget.customViewBox.selectAboveThreshold = self._selectNmrResiduesAboveThreshold

      self.splitter.addWidget(self.nmrResidueTable)
      self.splitter.addWidget(self.barGraphWidget)
      self.mainWidget.getLayout().addWidget(self.splitter)
      self.splitter.setStretchFactor(0, 1)
      self.mainWidget.setContentsMargins(5, 5, 5, 5)  # l,t,r,b


  def _checkSpectraWithPeakListsOnly(self):
    for cb in self.spectraSelectionWidget.allSpectraCheckBoxes:
      sp = self.project.getByPid(cb.text())
      lsts = []
      if sp:
        for pl in sp.peakLists:
          if len(pl.peaks)>0:
            lsts.append(True)
      if not any(lsts):
        cb.setChecked(False)

  def _addMoreNmrAtomsForAtomType(self, nmrAtomsNames, widget):
    '''

    :param widget: Widget where to add the option. EG frame
    :return:
    '''
    editableOption = EditableCheckBox(widget, grid=(0,0))
    self.nmrAtomsCheckBoxes.append(editableOption)
    regioncount = 0
    totalCount  = len(nmrAtomsNames)
    valueCount = int(len(nmrAtomsNames) / 2)
    if totalCount>0:
      positions = [(i+1 + regioncount, j) for i in range(valueCount+1)
                        for j in range(2)]

      for position, nmrAtomName in zip(positions, nmrAtomsNames):
        self.atomSelection = CheckBox(widget, text=nmrAtomName, grid=position)
        self.nmrAtomsCheckBoxes.append(self.atomSelection)

  def _toggleMoreNmrAtoms(self, widget):
    if self.sender():
      name = self.sender().text()
      if widget.isHidden():
        self.sender().setText(name.replace(MORE,LESS))
        widget.show()
      else:
        self.sender().setText(name.replace(LESS,MORE))
        widget.hide()
  
  def _hideNonNecessaryNmrAtomsOption(self):
    '''
    :return: hides nmrAtoms not needed for the selected nmrChain.
    '''
    neededNmrAtoms = self._availableNmrAtoms(source=self.nmrResidueTable._nmrChain)
    for selectedWidget in self.nmrAtomsCheckBoxes:
      if not isinstance(selectedWidget, EditableCheckBox):
        if selectedWidget.text() in neededNmrAtoms:
          selectedWidget.show()
        else:
          selectedWidget.hide()

  def _updateNmrAtomsOption(self):
    otherAvailable = False
    i = 0
    availableNmrAtoms = self._availableNmrAtoms()
    # line = HLine(self.nmrAtomsFrame,  style='DashLine',  height=1, grid=(i, 1))
    line = HLine(self.nmrAtomsFrame, grid=(i, 1), colour=getColours()[DIVIDER], height=10)
    i += 1
    for name, value in DefaultAtomWeights.items():
      atomFrame = Frame(self.nmrAtomsFrame, setLayout=True, grid=(i, 1))
      hFrame = 0
      vFrame = 0
      labelRelativeContribution = Label(atomFrame, text='%s Relative Contribution' % name,  grid=(vFrame, hFrame))
      hFrame +=1
      self.atomWeightSpinBox = DoubleSpinbox(atomFrame, value=DefaultAtomWeights[name],
                                             prefix=str('Weight' + (' ' * 2)), grid=(vFrame, hFrame),
                                             tipText='Relative Contribution for the selected nmrAtom')
      self.atomWeightSpinBox.setObjectName(name)
      self.atomWeightSpinBox.setMaximumWidth(150)
      self.atomWeightSpinBoxes.append(self.atomWeightSpinBox)
      self.nmrAtomsLabels.append(labelRelativeContribution)

      vFrame += 1
      self.commonAtomsFrame = Frame(atomFrame, setLayout=True, grid=(vFrame, 0))
      # add the first three of ccpn Sorted.
      vFrame += 1

      self.scrollAreaMoreNmrAtoms = ScrollArea(atomFrame, setLayout=False, grid=(vFrame, 0))
      self.scrollAreaMoreNmrAtoms.setWidgetResizable(True)
      self.moreOptionFrame = Frame(self, setLayout=True,  )
      self.scrollAreaMoreNmrAtoms.setWidget(self.moreOptionFrame)
      self.moreOptionFrame.getLayout().setAlignment(QtCore.Qt.AlignTop)
      self.scrollAreaMoreNmrAtoms.hide()
      self.moreButton = Button(atomFrame, 'More %s NmrAtoms' % name,
                               callback=partial(self._toggleMoreNmrAtoms,self.scrollAreaMoreNmrAtoms),  grid=(vFrame-1, 1), hAlign='l', )
      self.moreButton.hide()

      availableNmrAtomsForType = self._availableNmrAtoms(nmrAtomType=name)
      n = 0
      checkFirst = False
      maxCountRow = 3
      if len(availableNmrAtomsForType)<maxCountRow:
        for nmrAtomName in availableNmrAtomsForType:
          self.atomSelection = CheckBox(self.commonAtomsFrame, text=nmrAtomName, grid=(0, n))
          if not checkFirst:
            self.atomSelection.setChecked(True)
            checkFirst = True
          self.nmrAtomsCheckBoxes.append(self.atomSelection)
          n += 1
      else:
        self.moreButton.show()
        showPreferredFirst = [nmrAtomName for nmrAtomName in availableNmrAtomsForType if nmrAtomName in PreferredNmrAtoms]
        rest = [nmrAtomName for nmrAtomName in availableNmrAtomsForType if nmrAtomName not in showPreferredFirst]
        if len(showPreferredFirst)>0:
          if len(showPreferredFirst) < maxCountRow:
            needed = maxCountRow - len(showPreferredFirst)
            if len(rest) > needed:
              showPreferredFirst += rest[:needed]
              rest = rest[needed:]
            else:
              showPreferredFirst += rest
              rest = []
              self.moreButton.hide()
          for nmrAtomName in showPreferredFirst:
            self.atomSelection = CheckBox(self.commonAtomsFrame, text=nmrAtomName, grid=(0, n))
            n += 1
            if not checkFirst:
              self.atomSelection.setChecked(True)
              checkFirst = True
            self.nmrAtomsCheckBoxes.append(self.atomSelection)
          self._addMoreNmrAtomsForAtomType(rest, self.moreOptionFrame)
        else:
          for nmrAtomName in availableNmrAtomsForType[:3]:
            self.atomSelection = CheckBox(self.commonAtomsFrame, text=nmrAtomName, grid=(0, n))
            if not checkFirst:
              self.atomSelection.setChecked(True)
              checkFirst = True
            self.nmrAtomsCheckBoxes.append(self.atomSelection)
            n += 1
          self._addMoreNmrAtomsForAtomType(availableNmrAtomsForType[2:], self.moreOptionFrame)

      vFrame += 1
      ## Scrollable area where to add more atoms

      i +=1
      if name == OTHER:
        if not otherAvailable:
          otherAvailable  = self._addOtherNmrAtomsAvailable(availableNmrAtoms)


      if name not in availableNmrAtoms and not otherAvailable:

        atomFrame.hide()

    # line = HLine(self.nmrAtomsFrame, style='DashLine', height=1, grid=(i, 1))
    line = HLine(self.nmrAtomsFrame, grid=(i, 1), colour=getColours()[DIVIDER], height=10)

  def _addOtherNmrAtomsAvailable(self, availableNmrAtoms):
    '''Adds more nmr atoms if not in the default atoms'''
    addedNmrAtoms = [i.text() for i in self.nmrAtomsCheckBoxes if i is not None]
    othersAvailable = [name for name in availableNmrAtoms if name not in addedNmrAtoms]
    if len(othersAvailable):
      self.moreButton.show()
      self._addMoreNmrAtomsForAtomType(othersAvailable, self.moreOptionFrame)
      return True
    return False


  def _setSettingsWidgets(self):

    self.scrollArea = ScrollArea(self, setLayout=False, )
    self.scrollArea.setWidgetResizable(True)
    self.scrollAreaWidgetContents = Frame(self, setLayout=True, )
    self.scrollArea.setWidget(self.scrollAreaWidgetContents)
    # self.scrollAreaWidgetContents.getLayout().setAlignment(QtCore.Qt.AlignTop)
    self.settingsWidget.getLayout().addWidget(self.scrollArea)
    self.scrollArea.setContentsMargins(10, 10, 10, 15) #l,t,r,b
    self.scrollAreaWidgetContents.setContentsMargins(10, 10, 10, 15) #l,t,r,b
    # self.scrollAreaWidgetContents.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
    self.scrollAreaWidgetContents.getLayout().setSpacing(10)
    self._splitter.setStretchFactor(1,1) #makes the setting space fully visible when opening

    i = 0
    self.inputLabel = Label(self.scrollAreaWidgetContents, text='Select Data Input', grid=(i, 0), vAlign='t')
    self.spectraSelectionWidget = SpectraSelectionWidget(self.scrollAreaWidgetContents, mainWindow=self.mainWindow, grid=(i,1), gridSpan=(1,2))
    self._checkSpectraWithPeakListsOnly()
    self.__addCheckBoxesAttr(self.spectraSelectionWidget.allSpectraCheckBoxes)
    self.__addCheckBoxesAttr(self.spectraSelectionWidget.allSG_CheckBoxes)

    i += 1
    self.concentrationLabel = Label(self.scrollAreaWidgetContents, text='Concentrations', grid=(i, 0), vAlign='t')
    self.concentrationButton = Button(self.scrollAreaWidgetContents, text='Setup...', callback=self._setupConcentrationsPopup,
                                      grid=(i, 1))

    # self.spectraSelectionWidget.setMaximumHeight(150)
    i += 1
    self.modeLabel = Label(self.scrollAreaWidgetContents, text='Calculation mode ', grid=(i, 0))
    self.modeButtons = RadioButtons(self.scrollAreaWidgetContents, selectedInd=0, texts=MODES, callback=self._toggleRelativeContribuitions, grid=(i, 1))
    i += 1


    self.atomsLabel = Label(self.scrollAreaWidgetContents, text='Select Nmr Atoms', grid=(i, 0))
    self.nmrAtomsFrame = Frame(self.scrollAreaWidgetContents,setLayout=True, grid=(i, 1))
    self._updateNmrAtomsOption()
    self._hideNonNecessaryNmrAtomsOption()
    i += 1


    i += 1
    self.thresholdLAbel = Label(self.scrollAreaWidgetContents, text='Threshold value', grid=(i, 0))
    self.thresholdFrame = Frame(self.scrollAreaWidgetContents, setLayout=True, grid=(i, 1))

    self.thresholdSpinBox = DoubleSpinbox(self.thresholdFrame, value=DefaultThreshould, step=0.01,
                                          decimals=3, callback=self.updateThresholdLineValue, tipText = 'Threshold value for deltas',
                                          grid=(0, 0))
    self.thresholdButton = Button(self.thresholdFrame, text='Default', callback=self._setDefaultThreshold, tipText = 'Default: STD of deltas',
                                          grid=(0, 1))
    self.thresholdButton.setMaximumWidth(50)
    i += 1
    self.aboveThresholdColourLabel =  Label(self.scrollAreaWidgetContents,text='Above Threshold Colour', grid=(i,0))
    self.aboveThresholdColourBox = PulldownList(self.scrollAreaWidgetContents,  grid=(i, 1))
    for item in spectrumColours.items():
      pix = QtGui.QPixmap(QtCore.QSize(20, 20))
      pix.fill(QtGui.QColor(item[0]))
      self.aboveThresholdColourBox.addItem(icon=QtGui.QIcon(pix), text=item[1])
    try:
      self.aboveThresholdColourBox.select('light green')
    except:
      self.aboveThresholdColourBox.select(random.choice(self.aboveThresholdColourBox.texts))

    i += 1
    self.belowThresholdColourLabel = Label(self.scrollAreaWidgetContents, text='Below Threshold Colour', grid=(i, 0))
    self.belowThresholdColourBox = PulldownList(self.scrollAreaWidgetContents, grid=(i, 1))
    for item in spectrumColours.items():
      pix = QtGui.QPixmap(QtCore.QSize(20, 20))
      pix.fill(QtGui.QColor(item[0]))
      self.belowThresholdColourBox.addItem(icon=QtGui.QIcon(pix), text=item[1])
    try:
      self.belowThresholdColourBox.select('red')
    except:
      self.belowThresholdColourBox.select(random.choice(self.belowThresholdColourBox.texts))



    i += 1
    disappearedTipText = 'Mark NmrResidue bar with selected colour where assigned peaks have disapperead from the spectra'
    self.disappearedColourLabel = Label(self.scrollAreaWidgetContents, text='Disappeared Peaks Colour', grid=(i, 0))
    self.disappearedColourBox = PulldownList(self.scrollAreaWidgetContents, grid=(i, 1))
    for item in spectrumColours.items():
      pix = QtGui.QPixmap(QtCore.QSize(20, 20))
      pix.fill(QtGui.QColor(item[0]))
      self.disappearedColourBox.addItem(icon=QtGui.QIcon(pix), text=item[1])
    try:
      self.disappearedColourBox.select('dark grey')
    except:
      self.disappearedColourBox.select(random.choice(self.disappearedColourBox.texts))

    i += 1
    self.disappearedBarThreshold = Label(self.scrollAreaWidgetContents, text='Disappeared value', grid=(i, 0))
    self.disappearedBarThresholdSpinBox = DoubleSpinbox(self.scrollAreaWidgetContents, value=1, step=0.01,
                                          decimals=3, callback=None, grid=(i, 1))
    i += 1


    # molecular Structure
    self.molecularStructure= Label(self.scrollAreaWidgetContents, text='Molecular Structure', grid=(i, 0))
    texts = ['PDB','CCPN Ensembles','Fetch From Server']
    self.molecularStructureRadioButton = RadioButtons(self.scrollAreaWidgetContents, texts=texts, direction='h',
                                        grid=(i, 1))
    self.molecularStructureRadioButton.set(texts[0])
    self.molecularStructureRadioButton.setEnabled(False)
    self.molecularStructureRadioButton.setToolTip('Not implemented yet')

    i += 1
    self.mvWidgetContents = Frame(self.scrollAreaWidgetContents, setLayout=True, grid=(i, 1))
    self.pdbLabel = Label(self.mvWidgetContents, text='PDB File Path', grid=(0, 0))
    scriptPath = None
    if self.mainWindow:
      # scriptPath = os.path.join(getScriptsDirectoryPath(self.project),'pymol')
      scriptPath = self.application.pymolScriptsPath
    self.pathPDB = LineEditButtonDialog(self.mvWidgetContents, textDialog='Select PDB File',
                                        filter="PDB files (*.pdb)", directory=scriptPath, grid=(0,1))


    i += 1

    self.updateButton = Button(self.scrollAreaWidgetContents, text='Update All', callback=self.updateModule,
                               grid=(i, 1))
    i += 1
    # Spacer(self.scrollAreaWidgetContents, 3, 3
    #        , QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
    #        , grid=(i,3), gridSpan=(1,1))

  def _toggleRelativeContribuitions(self):
    value = self.modeButtons.getSelectedText()
    if value == HEIGHT or value ==  VOLUME:
      'hide weight'
      for i in self.atomWeightSpinBoxes:
        i.hide()
      for i in self.nmrAtomsLabels:
        i.hide()



    else:
      for i in self.atomWeightSpinBoxes:
        i.show()
      for i in self.nmrAtomsLabels:
        i.show()

  def _setDefaultThreshold(self):
    self.updateModule(silent=True)
    self._setThresholdLineBySTD()

  def _setThresholdLineBySTD(self):
    nc = self.project.getByPid(self.nmrResidueTable.ncWidget.getText())
    if nc:
      deltas = [ n._delta for n in nc.nmrResidues if n._delta is not None]
      if len(deltas)>0:
        if not None in deltas:
          std = np.std(deltas)
          if std:
            self.thresholdLinePos = std
            self.thresholdSpinBox.set(std)



  def updateTable(self, nmrChain):
    self.nmrResidueTable.ncWidget.select(nmrChain.pid)
    # self.nmrResidueTable.setColumns(self.nmrResidueTable.NMRcolumns)

    # self.nmrResidueTable.setObjects([nr for nr in nmrChain.nmrResidues if nr._delta])

    self.nmrResidueTable._update(nmrChain)

    self.nmrResidueTable._selectOnTableCurrentNmrResidues(self.current.nmrResidues)

  def _displayTableForNmrChain(self, nmrChain):
    self.updateModule()
    self._hideNonNecessaryNmrAtomsOption()

    # self.updateTable(nmrChain)
    # self.updateBarGraph()

  def _peakDeletedCallBack(self, data):
    if len(self.current.peaks) == 0:
      self.updateModule()

  # def _peakChangedCallBack(self, data):
  #
  #   peak = data[Notifier.OBJECT]
  #   if self._peakChangedNotifier.lastPeakPos != peak.position:
  #     self._peakChangedNotifier.lastPeakPos = peak.position
  #     self.updateModule()

  def _checkBoxCallback(self, data):
    '''
    Callback from checkboxes inside a table
    '''
    # objs = data[Notifier.OBJECT]

    # itemSelection = data['rowItem']
    # att = self.nmrResidueTable.horizontalHeaderItem(itemSelection.column()).text()
    # if att == 'Included':
    # objs = data[Notifier.OBJECT]
    # print(objs)
    # if objs:
    #   obj = objs[0]
    # #     print(obj)
    # #   obj._includeInDeltaShift = data['checked']
    #   obj._finaliseAction('change')
    # self.updateModule()
    pass
    # print(data)

  def _nmrObjectChanged(self, data):
    self.updateModule()

  def _nmrResidueDeleted(self, data):
    if len(self.current.nmrResidues) == 0:
      self.updateModule()

  def _selectNmrResiduesAboveThreshold(self):
    if self.aboveObjects:
      self.current.nmrResidues = self.aboveObjects

  def _threshouldLineMoved(self):
    pos = self.barGraphWidget.xLine.pos().y()
    self.thresholdSpinBox.setValue(pos)
    self.updateBarGraph()

  def updateBarGraph(self):
    xs = []
    ys = []
    obs = []
    self.disappearedX = []
    self.disappearedY = []
    self.disappereadObjects = []
    self.aboveX = []
    self.aboveY = []
    self.aboveObjects = []
    self.belowX = []
    self.belowY = []
    self.belowObjects = []
    self.aboveBrush = 'g'
    self.belowBrush = 'r'
    self.disappearedPeakBrush = 'b'
    thresholdPos = self.thresholdSpinBox.value()
    # check if all values are none:
    shifts = [nmrResidue._delta for nmrResidue in self.nmrResidueTable._dataFrameObject.objects]
    if not any(shifts):
      self.barGraphWidget.clear()
      return

    if self.barGraphWidget.xLine:
      self.thresholdLinePos = self.thresholdSpinBox.value()

      if self.nmrResidueTable._dataFrameObject:
        for nmrResidue in self.nmrResidueTable._dataFrameObject.objects:
          if nmrResidue:
            nmrResidue.missingPeaks = False
            if hasattr(nmrResidue, '_spectraWithMissingPeaks'):
              if len(nmrResidue._spectraWithMissingPeaks) != 0:
                if nmrResidue.sequenceCode:

                  x = int(nmrResidue.sequenceCode)
                  # x = self.nmrResidueTable._dataFrameObject.objects.index(nmrResidue)
                  if nmrResidue._delta:
                    y = nmrResidue._delta
                  else:
                    if nmrResidue._includeInDeltaShift:
                      y = self.disappearedBarThresholdSpinBox.value()
                    else:
                      y = 0
                  self.disappearedY.append(y)
                  self.disappearedX.append(x)
                  self.disappereadObjects.append(nmrResidue)
                  nmrResidue.missingPeaks = True
            if nmrResidue._delta:
              if not nmrResidue.missingPeaks:
                if nmrResidue.sequenceCode:

                  x = int(nmrResidue.sequenceCode)
                  # x = self.nmrResidueTable._dataFrameObject.objects.index(nmrResidue)
                  y = float(nmrResidue._delta)

                  xs.append(x)
                  ys.append(y)
                  obs.append(nmrResidue)
                  if y > self.thresholdLinePos:
                    self.aboveY.append(y)
                    self.aboveX.append(x)
                    self.aboveObjects.append(nmrResidue)
                  else:
                    self.belowX.append(x)
                    self.belowY.append(y)
                    self.belowObjects.append(nmrResidue)


    selectedNameColourA = self.aboveThresholdColourBox.getText()
    for code, name in spectrumColours.items():
      if name == selectedNameColourA:
        self.aboveBrush = code

    selectedNameColourB = self.belowThresholdColourBox.getText()
    for code, name in spectrumColours.items():
      if name == selectedNameColourB:
        self.belowBrush = code

    selectedNameColourC = self.disappearedColourBox.getText() #disappeared peaks
    for code, name in spectrumColours.items():
      if name == selectedNameColourC:
        self.disappearedPeakBrush = code

    self.barGraphWidget.clear()
    self.barGraphWidget._lineMoved(aboveX=self.aboveX,
                                   aboveY=self.aboveY,
                                   aboveObjects=self.aboveObjects,
                                   belowX=self.belowX,
                                   belowY=self.belowY,
                                   belowObjects=self.belowObjects,
                                   belowBrush=self.belowBrush,
                                   aboveBrush=self.aboveBrush,
                                   disappearedX = self.disappearedX,
                                   disappearedY=self.disappearedY,
                                   disappearedObjects = self.disappereadObjects,
                                   disappearedBrush = self.disappearedPeakBrush,
                                   )
    if xs and ys:
      self.barGraphWidget.setViewBoxLimits(0, max(xs)*10, 0,  max(ys)*10)


  def updateThresholdLineValue(self, value):
    if self.barGraphWidget:
      self.barGraphWidget.xLine.setPos(value)

  def _updateThreshold(self):
    self.thresholdSpinBox.setValue(self.barGraphWidget.xLine.pos().y())
    self.updateBarGraph()
    # self.barGraphWidget._lineMoved()

  def _viewboxMouseClickEvent(self, event):

    if event.button() == QtCore.Qt.RightButton:
      event.accept()
      self.barGraphWidget.customViewBox._raiseContextMenu(event)
      self.barGraphWidget.customViewBox._resetBoxes()

    elif event.button() == QtCore.Qt.LeftButton:
      self.barGraphWidget.customViewBox._resetBoxes()
      self.application.current.clearNmrResidues()
      event.accept()

  def _customActionCallBack(self, data):
    from ccpn.ui.gui.lib.Strip import navigateToNmrAtomsInStrip, _getCurrentZoomRatio, navigateToNmrResidueInDisplay

    nmrResidue = data[Notifier.OBJECT]

    if nmrResidue:
      xPos = int(nmrResidue.sequenceCode)
      yPos = nmrResidue._delta
      if xPos and yPos:
        self.barGraphWidget.customViewBox.setRange(xRange=[xPos-10, xPos+10], yRange=[0, yPos],)
      self.application.ui.mainWindow.clearMarks()

      if self.current.strip is not None:
        strip = self.current.strip
        if len(nmrResidue.selectedNmrAtomNames) > 0:
          nmrAtoms = [nmrResidue.getNmrAtom(str(i)) for i in nmrResidue.selectedNmrAtomNames]
          if len(nmrAtoms) <= 1:
            navigateToNmrResidueInDisplay(display=strip.spectrumDisplay,
                                          nmrResidue=nmrResidue,
                                          widths=_getCurrentZoomRatio(strip.viewBox.viewRange()),
                                          markPositions=True
                                          )
          else:
            navigateToNmrAtomsInStrip(strip,
                                      nmrAtoms=nmrAtoms,
                                      widths=_getCurrentZoomRatio(strip.viewBox.viewRange()),
                                      markPositions=True
                                      )
      else:
        if len(self.project.strips) > 0:
          selectFirst = MessageDialog.showYesNo('No Strip selected.', ' Use first available?')
          if selectFirst:
            self.current.strip = self.project.strips[0]
            self._customActionCallBack(data)
        else:
          getLogger().warning('Impossible to navigate to peak position. Set a current strip first')

  def _isInt(self, s):
    try:
      int(s)
      return True
    except ValueError:
      return False

  def updateModule(self, silent=False):
    '''

    :param silent: if silent does not update the module!
    :return: deltas
    '''

    mode = self.modeButtons.getSelectedText()
    if not mode in MODES:
      return
    weights = {}
    for atomWSB in self.atomWeightSpinBoxes:
      weights.update({atomWSB.objectName():atomWSB.value()})

    selectedAtomNames = [cb.text() for cb in self.nmrAtomsCheckBoxes if cb.isChecked()]
    if self.nmrResidueTable:
      if self.nmrResidueTable._nmrChain is not None:
        for nmrResidue in self.nmrResidueTable._nmrChain.nmrResidues:

          if self._isInt(nmrResidue.sequenceCode):

            spectra = self.spectraSelectionWidget.getSelections()
            self._updatedPeakCount(nmrResidue, spectra)
            if nmrResidue._includeInDeltaShift:
              nmrResidue.spectraCount = len(spectra)
              nmrResidueAtoms = [atom.name for atom in nmrResidue.nmrAtoms]
              nmrResidue.selectedNmrAtomNames =  [atom for atom in nmrResidueAtoms if atom in selectedAtomNames]
              nmrResidue._delta = getNmrResidueDeltas(nmrResidue, selectedAtomNames, mode=mode, spectra=spectra, atomWeights=weights)
            else:
              nmrResidue._delta = None
        if not silent:
          self.updateTable(self.nmrResidueTable._nmrChain)
          self.updateBarGraph()



  def _updatedPeakCount(self, nmrResidue, spectra):
    if len(nmrResidue.nmrAtoms)>0:
      peaks = [p for p in nmrResidue.nmrAtoms[0].assignedPeaks if p.peakList.spectrum in spectra]


      spectraWithPeaks = [peak.peakList.spectrum for peak in peaks]
      spectraWithMissingPeaks = [spectrum for spectrum in spectra if spectrum not in spectraWithPeaks]
      nmrResidue._spectraWithMissingPeaks = spectraWithMissingPeaks
      return nmrResidue._spectraWithMissingPeaks


  def _showOnMolecularViewer(self):
    """
    1) write the script in the scripts/pymol dir
    2) run pymol with the script
    """
    import json
    import subprocess

    filePath = os.path.join(self.application.pymolScriptsPath, PymolScriptName)

    pymolPath = self.application.preferences.externalPrograms.pymol
    pdbPath = self.pathPDB.get()

    if not os.path.exists(pymolPath):
      ok = MessageDialog.showOkCancelWarning('Molecular Viewer not Set'
                                             , 'Select the executable file on preferences')
      if ok:
        from ccpn.ui.gui.popups.PreferencesPopup import PreferencesPopup
        pp = PreferencesPopup(parent=self.mainWindow, mainWindow=self.mainWindow, preferences=self.application.preferences)
        pp.tabWidget.setCurrentIndex(pp.tabWidget.count()-1)
        pp.exec_()
        return


    while not pdbPath.endswith('.pdb'):
      sucess = self.pathPDB._openFileDialog()
      if sucess:
        pdbPath = self.pathPDB.get()
      else:
        return


    aboveThresholdResidues = "+".join([str(x) for x in self.aboveX])
    belowThresholdResidues = "+".join([str(x) for x in self.belowX])
    missingdResidues = "+".join([str(x) for x in self.disappearedX])
    selection = "+".join([str(x.sequenceCode) for x in self.current.nmrResidues])

    colourAboveThreshold = hexToRgb(self.aboveBrush)
    colourBelowThreshold = hexToRgb(self.belowBrush)
    colourMissing = hexToRgb(self.disappearedPeakBrush)


    scriptPath = chemicalShiftMappingPymolTemplate(filePath, pdbPath, aboveThresholdResidues, belowThresholdResidues,
                                                   missingdResidues, colourMissing, colourAboveThreshold, colourBelowThreshold,
                                                   selection)


    try:
      self.pymolProcess = subprocess.Popen(pymolPath+' -r '+scriptPath,
                       shell=True,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
    except Exception as e:
      getLogger().warning('Pymol not started. Check executable.', e)



  def _selectCurrentNmrResiduesNotifierCallback(self, data):
    for bar in self.barGraphWidget.barGraphs:
      for label in bar.labels:
        if label.data(int(label.text())) is not None:
          if self.application is not None:

            if label.data(int(label.text())) in self.current.nmrResidues:

              if self.application.colourScheme == 'light':
                highlightColour = '#3333ff'
              else:
                highlightColour = '#00ff00'
              label.setBrush(QtGui.QColor(highlightColour))
              label.setVisible(True)
              label.setSelected(True)

            else:
              label.setSelected(False)
              label.setBrush(QtGui.QColor(bar.brush))
              if label.isBelowThreshold and not self.barGraphWidget.customViewBox.allLabelsShown:
                label.setVisible(False)


  def _mouseClickEvent(self, event):

    position = event.pos().x()
    self.clicked = int(position)
    if event.button() == QtCore.Qt.LeftButton:
      for bar in self.barGraphWidget.barGraphs:
        for label in bar.labels:
          if label.text() == str(self.clicked):
            self.current.nmrResidue = label.data(self.clicked)
            label.setSelected(True)
      event.accept()

  def _mouseDoubleClickEvent(self, event):
    from ccpn.ui.gui.lib.Strip import navigateToNmrAtomsInStrip, _getCurrentZoomRatio, navigateToNmrResidueInDisplay

    self.nmrResidueTable.scrollToSelectedIndex()

    self.application.ui.mainWindow.clearMarks()
    position = event.pos().x()
    self.doubleclicked = int(position)
    if event.button() == QtCore.Qt.LeftButton:
      for bar in self.barGraphWidget.barGraphs:
        for label in bar.labels:
          if label.text() == str(self.doubleclicked):
           nmrResidue = label.data(self.doubleclicked)
           if nmrResidue:
             if self.current.strip is not None:
               strip = self.current.strip
               if len(nmrResidue.selectedNmrAtomNames) >0:
                 nmrAtoms = [ nmrResidue.getNmrAtom(str(i)) for i  in nmrResidue.selectedNmrAtomNames]
                 if len(nmrAtoms) <= 1:
                   navigateToNmrResidueInDisplay(display=strip.spectrumDisplay,
                                                 nmrResidue=nmrResidue,
                                                 widths=_getCurrentZoomRatio(strip.viewBox.viewRange()),
                                                 markPositions=True
                                             )
                 else:
                   navigateToNmrAtomsInStrip(strip,
                                             nmrAtoms=nmrAtoms,
                                             widths=_getCurrentZoomRatio(strip.viewBox.viewRange()),
                                             markPositions=True
                                             )
             else:
               if len(self.project.strips)>0:
                 selectFirst = MessageDialog.showYesNo('No Strip selected.',' Use first available?')
                 if selectFirst:
                   self.current.strip = self.project.strips[0]
                   self._mouseDoubleClickEvent(event)
               else:
                 getLogger().warning('Impossible to navigate to peak position. Set a current strip first')


  def _setupConcentrationsPopup(self):
    popup = CcpnDialog(windowTitle='Setup Concentrations', setLayout=True)

    spectra = self.spectraSelectionWidget.getSelections()
    names = [sp.name for sp in spectra]
    w = ConcentrationWidget(popup, names=names, grid=(0,0))
    vs, u = self._getConcentrationsFromSpectra(spectra)
    w.setValues(vs)
    w.setUnit(u)
    buttons = ButtonList(popup, texts=['Cancel', 'Apply', 'Ok'],
                         callbacks=[popup.reject, partial(self._applyConcentrations,w),
                                                                            partial(self._closeConcentrationsPopup,popup,w)],
                         grid=(1,0))
    popup.show()
    popup.raise_()

  def _applyConcentrations(self, w):
    spectra = self.spectraSelectionWidget.getSelections()
    vs, u = w.getValues() , w.getUnit()
    self._addConcentrationsFromSpectra(spectra, vs, u)

  def _closeConcentrationsPopup(self,popup, w):
    self._applyConcentrations(w)
    popup.accept()

  def  _getConcentrationsFromSpectra(self, spectra):

    vs = []
    # us = []
    u = DefaultConcentrationUnit
    for spectrum in spectra:

      if spectrum.sample:
        sampleComponent = spectrum.sample._fetchSampleComponent(name=spectrum.name)
        v = sampleComponent.concentration or DefaultConcentration
        u = sampleComponent.concentrationUnit
      else:
        v = DefaultConcentration
        u = DefaultConcentrationUnit

      vs.append(v)
      # us.append(u)
      # this is unfortunate. We can select only one unit for all

    return vs, u



  def _addConcentrationsFromSpectra(self, spectra, concentrationValues, concentrationUnit):
    """
    
    :return: 
    """""

    # add concentrations

    for spectrum, value in zip(spectra, concentrationValues):
      if not spectrum.sample:
        sample = self.project.newSample(name=spectrum.name)
        sample.spectra = [spectrum]
        newSampleComponent = sample.newSampleComponent(name=spectrum.name)
        newSampleComponent.concentration = value
        newSampleComponent.concentrationUnit = concentrationUnit

      else:
        sample = spectrum.sample
        newSampleComponent = sample._fetchSampleComponent(name=spectrum.name)
        newSampleComponent.concentration = value
        newSampleComponent.concentrationUnit = concentrationUnit


  def close(self):
    """
    Close the table from the commandline
    """
    self._closeModule()

  def _closeModule(self):
    """
    Re-implementation of closeModule function from CcpnModule to unregister notification on current
    """
    if self._selectCurrentNmrResiduesNotifier is not None:
      self._selectCurrentNmrResiduesNotifier.unRegister()
    # self._peakChangedNotifier.unRegister()
    if self._peakDeletedNotifier:
      self._peakDeletedNotifier.unRegister()
    if self._nrChangedNotifier:
      self._nrChangedNotifier.unRegister()
    if self._nrDeletedNotifier:
      self._nrDeletedNotifier.unRegister()

    super(ChemicalShiftsMapping, self)._closeModule()

