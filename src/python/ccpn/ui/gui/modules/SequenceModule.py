"""
This file contains the SequenceModule module

GWV: modified 1-9/12/2016
GWV: 13/04/2017: Disconnected from Sequence Graph; Needs refactoring
GWV: 22/4/2018: New handling of colours

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
__dateModified__ = "$dateModified: 2017-07-07 16:32:47 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import typing

from PyQt5 import QtCore, QtGui, QtWidgets
from collections import Iterable
from ccpn.core.Chain import Chain
from ccpn.core.Residue import Residue
from ccpn.core.NmrResidue import NmrResidue
from ccpn.core.NmrChain import NmrChain
from ccpn.core.lib.Notifiers import Notifier

from ccpn.ui.gui.guiSettings import getColours
from ccpn.ui.gui.guiSettings import GUICHAINLABEL_TEXT, \
                                    GUICHAINRESIDUE_DRAGENTER, GUICHAINRESIDUE_DRAGLEAVE, \
                                    GUICHAINRESIDUE_UNASSIGNED, GUICHAINRESIDUE_ASSIGNED, \
                                    GUICHAINRESIDUE_POSSIBLE, GUICHAINRESIDUE_WARNING, \
                                    SEQUENCEMODULE_DRAGMOVE, SEQUENCEMODULE_TEXT
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.guiSettings import fixedWidthFont, fixedWidthLargeFont, helvetica8
from ccpn.ui.gui.guiSettings import textFontHugeSpacing as fontSpacing
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.MessageDialog import showYesNo
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.widgets.MessageDialog import progressManager, showWarning
from ccpn.ui.gui.widgets.Frame import Frame


class SequenceModule():
  """
  The module displays all chains in the project as one-letter amino acids. The one letter residue
  sequence codes are all instances of the GuiChainResidue class and the style applied to a residue
  indicates its assignment state and, when coupled with the Sequence Graph module, indicates if a
  stretch of residues matches a given stretch of connected NmrResidues. The QGraphicsScene and
  QGraphicsView instances provide the canvas on to which the amino acids representations are drawn.
  """
  includeSettingsWidget = False
  maxSettingsState = 2  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
  settingsPosition = 'left'

  _alreadyOpened = False
  _onlySingleInstance = True
  _currentModule = None

  className = 'SequenceModule'

  def __init__(self, moduleParent=None, parent=None, mainWindow=None, name='Sequence'):
    #CcpnModule.__init__(self, size=(10, 30), name='Sequence', closable=False)
    #TODO: make closable
    # CcpnModule.__init__(self, mainWindow=mainWindow, name=name)

    # super(SequenceModule, self).__init__(setLayout=True)

    self.moduleParent = moduleParent
    self._parent = parent
    self.mainWindow = mainWindow
    self.project = mainWindow.application.project
    #self.label.hide()

    # self.setAcceptDrops(True)
    self._parent.setAcceptDrops(True)

    self.scrollArea = QtWidgets.QScrollArea()
    self.scrollArea.setWidgetResizable(True)
    self.scrollArea.scene = QtWidgets.QGraphicsScene(self._parent)
    self.scrollContents = QtWidgets.QGraphicsView(self.scrollArea.scene, self._parent)
    self.scrollContents.setAcceptDrops(True)
    self.scrollContents.setInteractive(True)

    self.scrollContents.setAlignment(QtCore.Qt.AlignTop)
    self.scrollContents.setGeometry(QtCore.QRect(0, 0, 380, 1000))
    self.horizontalLayout2 = QtWidgets.QHBoxLayout(self.scrollContents)
    self.scrollArea.setWidget(self.scrollContents)

    self.colours = getColours()
    # self.setStyleSheet("""QScrollArea QScrollBar::horizontal {max-height: 20px;}
    #                       QScrollArea QScrollBar::vertical{max-width:20px;}
    #                   """)
    self.residueCount = 0

    # self.mainWidget.layout().addWidget(self.scrollArea)
    self._parent.layout().addWidget(self.scrollArea)

    # connect graphics scene dragMoveEvent to CcpnModule dragMoveEvent - required for drag-and-drop
    # assignment routines.
    self.scrollArea.scene.dragMoveEvent = self._dragMoveEvent
    self.scrollArea.scene.dropEvent = self._dropEvent
    self.chainLabels = []
    self._highlight = None
    self._initialiseChainLabels()

    #GWV: removed fixed height restrictions but maximum height instead
    #self.setFixedHeight(2*self.widgetHeight)
    #self.scrollContents.setFixedHeight(2*self.widgetHeight)
    # self._parent.setMaximumHeight(100)
    # self.scrollContents.setMaximumHeight(100)

    #GWV: explicit intialisation to prevent crashes
    self._chainNotifier = None
    self._residueNotifier = None
    self._chainDeleteNotifier = None
    self._registerNotifiers()

    # TODO:ED add highlight if an nmrChain already selected
    # generate a create graph event? and let the response populate the module

  def _getGuiItem(self, scene):
    for item in scene.items():
      if item.isUnderMouse() and item != self._highlight:
        if hasattr(item, 'residue'):
          # self._highlight.setPlainText(item.toPlainText())
          return item
    else:
      return None

  def _dragMoveEvent(self, event):
    pos = event.scenePos()
    pos = QtCore.QPointF(pos.x(), pos.y()-25) # WB: TODO: -25 is a hack to take account of scrollbar height

    item = self._getGuiItem(self.scrollArea.scene)
    if item:
      # _highlight is an overlay of the guiNmrResidue but with a highlight colour
      self._highlight.setHtml('<div style="color: %s; text-align: center;"><strong>' % self.colours[SEQUENCEMODULE_DRAGMOVE] +
                              item.toPlainText() + '</strong></div>')
      self._highlight.setPos(item.pos())
    else:
      self._highlight.setPlainText('')

    event.accept()

  def _dropEvent(self, event):

    self._highlight.setPlainText('')
    data, dataType = _interpretEvent(event)
    if dataType == 'pids':

      # check that the drop event contains the correct information
      # if isinstance(data, Iterable) and len(data) == 2:
      #   nmrChain = self.mainWindow.project.getByPid(data[0])
      #   nmrResidue = self.mainWindow.project.getByPid(data[1])
      #   if isinstance(nmrChain, NmrChain) and isinstance(nmrResidue, NmrResidue):
      #     if nmrResidue.nmrChain == nmrChain:
      #       self._processNmrChains(data, event)

      if isinstance(data, Iterable):
        for dataItem in data:
          obj = self.mainWindow.project.getByPid(dataItem)
          if isinstance(obj, NmrChain) or isinstance(obj, NmrResidue):
            self._processNmrChains(obj)


  def _processNmrChains(self, data:typing.Union[NmrChain, NmrResidue]):
    """
    Processes a list of NmrResidue Pids and assigns the residue onto which the data is dropped and
    all succeeding residues according to the length of the list.
    """

    guiRes = self._getGuiItem(self.scrollArea.scene)
    #self.scene.itemAt(event.scenePos())

    # if not hasattr(guiRes, 'residue'):
    #   return

    if isinstance(data, NmrChain):
      nmrChain = data     #self.mainWindow.project.getByPid(data)
      selectedNmrResidue = nmrChain.nmrResidues[0]
    elif isinstance(data, NmrResidue):
      selectedNmrResidue = data
      nmrChain = data.nmrChain
    else:
      return

    # selectedNmrResidue = self.mainWindow.project.getByPid(data[1])   # ejb - new, pass in selected nmrResidue
    residues = [guiRes.residue]
    toAssign = [nmrResidue for nmrResidue in nmrChain.nmrResidues if '-1' not in nmrResidue.sequenceCode]
    chainRes = guiRes.residue

    if toAssign:
      if isinstance(data, NmrChain):
        selectedNmrResidue = toAssign[0]
        residues = [chainRes]
        idStr = 'nmrChain: %s to residue: %s' % (toAssign[0].nmrChain.id, residues[0].id)
      else:
        try:
          selectedNmrResidue = selectedNmrResidue.mainNmrResidue

          # get the first residue of the chain
          for resLeft in range(toAssign.index(selectedNmrResidue)):
            chainRes = chainRes.previousResidue

          endRes = chainRes
          for resRight in range(len(toAssign)-1):
            endRes = endRes.nextResidue

        except:
          showWarning('Sequence Graph', 'Too close to the start of the chain')
          return

        if not chainRes:
          showWarning('Sequence Graph', 'Too close to the start of the chain')
          return

        if not endRes:
          showWarning('Sequence Graph', 'Too close to the end of the chain')
          return

        residues = [chainRes]

        idStr = 'nmrChain: %s;\nnmrResidue: %s to residue: %s' % (toAssign[0].nmrChain.id, selectedNmrResidue.id, guiRes.residue.id)

      result = showYesNo('Assignment', 'Assign %s?' % idStr)
      if result:

        with progressManager(self.mainWindow, 'Assigning %s' % idStr):

          # try:

          if nmrChain.id == '@-':
            # assume that it is the only one
            nmrChain.assignSingleResidue(selectedNmrResidue, residues[0])
          else:

            # toAssign is the list of mainNmrResidues of the chain
            for ii in range(len(toAssign)-1):
              resid = residues[ii]
              next = resid.nextResidue    #TODO:ED may not have a .nextResidue
              residues.append(next)

            try:
              nmrChain.assignConnectedResidues(residues[0])
            except Exception as es:
              showWarning('Sequence Graph', str(es))

          for ii, res in enumerate(residues):
            if hasattr(self, 'guiChainLabel'):
              guiResidue = self.guiChainLabel.residueDict.get(res.sequenceCode)
              guiResidue._setStyleAssigned()
              # guiResidue.setHtml('<div style="color: %s; text-align: center;"><strong>' % self.colours[GUICHAINRESIDUE_ASSIGNED] +
              #                      res.shortName+'</strong></div>')

          # except Exception as es:
          #   getLogger().warning('Sequence Module: %s' % str(es))

  def populateFromSequenceGraphs(self):
    """
    Take the selected chain from the first opened sequenceGraph and highlight in module
    """
    # get the list of open sequenceGraphs

    self.moduleParent.predictSequencePosition(self.moduleParent.predictedStretch)
    return

    # from ccpn.AnalysisAssign.modules.SequenceGraph import SequenceGraphModule
    # seqGraphs = [sg for sg in SequenceGraphModule.getInstances()]
    #
    # if seqGraphs:
    #   try:
    #     seqGraphs[0].predictSequencePosition(seqGraphs[0].predictedStretch)
    #   except Exception as es:
    #     getLogger().warning('Error: no predictedStretch found: %s' % str(es))

  def _clearStretches(self, chainNum):
    """
    CCPN INTERNAL called in predictSequencePosition method of SequenceGraph.
    Highlights regions on the sequence specified by the list of residues passed in.
    """
    for res1 in self.chainLabels[chainNum].residueDict.values():
      res1._styleResidue()

  def _highlightPossibleStretches(self, chainNum, residues:typing.List[Residue]):
    """
    CCPN INTERNAL called in predictSequencePosition method of SequenceGraph.
    Highlights regions on the sequence specified by the list of residues passed in.
    """
    # for res1 in self.chainLabels[chainNum].residueDict.values():
    #   res1._styleResidue()

    try:
      for residue in residues:
        guiResidue = self.chainLabels[chainNum].residueDict[residue.sequenceCode]
        guiResidue._styleResidue()
      guiResidues = []
      for residue in residues:
        guiResidue = self.chainLabels[chainNum].residueDict[residue.sequenceCode]
        guiResidues.append(guiResidue)

        if guiResidue.residue.nmrResidue is not None:
          guiResidue._setStyleWarningAssigned()
        else:
          guiResidue._setStylePossibleAssigned()
        # guiResidue._setStylePossibleAssigned()

        # guiResidue.setHtml('<div style="color: %s;text-align: center; padding: 0px;">' %
        #                     self.colours[GUICHAINRESIDUE_POSSIBLE] +  residue.shortName+'</div>')
    except Exception as es:
      getLogger().warning('_highlightPossibleStretches: %s' % str(es))

  def _chainCallBack(self, data):
    """callback for chain notifier
    """
    chain = data[Notifier.OBJECT]
    self._addChainLabel(chain=chain)

  def _addChainLabel(self, chain:Chain, placeholder=False, tryToUseSequenceCodes=False):
    """Creates and adds a GuiChainLabel to the sequence module.
    """
    if len(self.project.chains) == 1 and len(self.chainLabels) == 1:
      # first new chain created so get rid of placeholder label
      self.chainLabels = []
      self.scrollArea.scene.removeItem(self.chainLabel)
      self.widgetHeight = 0

    self.chainLabel = GuiChainLabel(self, self.mainWindow, self.scrollArea.scene, position=[0, self.widgetHeight],
                                    chain=chain, placeholder=placeholder, tryToUseSequenceCodes=tryToUseSequenceCodes)
    self.scrollArea.scene.addItem(self.chainLabel)
    self.chainLabels.append(self.chainLabel)
    self.widgetHeight += (0.8*(self.chainLabel.boundingRect().height()))

  def _addChainResidueCallback(self, data):
    """callback for residue change notifier
    """
    residue = data[Notifier.OBJECT]
    self._refreshChainLabels()

    # residue = data[Notifier.OBJECT]
    #
    # if self.chainLabel.chain is not residue.chain: # they should always be equal if function just called as a notifier
    #   return
    # number = residue.chain.residues.index(residue)
    # self.chainLabel._addResidue(number, residue)
    # self.populateFromSequenceGraphs()

  def _deleteChainResidueCallback(self, data):
    """callback for residue change notifier
    """
    residue = data[Notifier.OBJECT]
    self._refreshChainLabels()

    # if self.chainLabel.chain is not residue.chain: # they should always be equal if function just called as a notifier
    #   return
    # number = residue.chain.residues.index(residue)
    # self.chainLabel._addResidue(number, residue)
    # self.populateFromSequenceGraphs()

  def _registerNotifiers(self):
    """register notifiers
    """
    self._chainNotifier = Notifier(self.project,
                                  [Notifier.CREATE],
                                  'Chain',
                                  self._chainCallBack)
    self._residueNotifier = Notifier(self.project,
                                     [Notifier.CREATE, Notifier.CHANGE],
                                  'Residue',
                                     self._addChainResidueCallback,
                                     onceOnly=True)
    self._residueDeleteNotifier = Notifier(self.project,
                                     [Notifier.DELETE],
                                  'Residue',
                                     self._deleteChainResidueCallback,
                                     onceOnly=True)
    self._chainDeleteNotifier = Notifier(self.project,
                                  [Notifier.DELETE],
                                  'Chain',
                                  self._refreshChainLabels)

  def _unRegisterNotifiers(self):
    """unregister notifiers
    """
    if self._chainNotifier:
      self._chainNotifier.unRegister()
      self._chainNotifier = None
    if self._residueNotifier:
      self._residueNotifier.unRegister()
      self._residueNotifier = None
    if self._residueDeleteNotifier:
      self._residueDeleteNotifier.unRegister()
      self._residueDeleteNotifier = None
    if self._chainDeleteNotifier:
      self._chainDeleteNotifier.unRegister()
      self._chainDeleteNotifier = None

  def _closeModule(self):
    """
    CCPN-INTERNAL: used to close the module
    """
    self._unRegisterNotifiers()

  def close(self):
    """
    Close the table from the commandline
    """
    self._closeModule()     # ejb - needed when closing/opening project

  def _initialiseChainLabels(self):
    """initialise the chain label widgets
    """
    for chainLabel in self.chainLabels:
      for item in chainLabel.items:
        self.scrollArea.scene.removeItem(item)
      chainLabel.items = []  # probably don't need to do this
    self.chainLabels = []
    self.widgetHeight = 0  # dynamically calculated from the number of chains

    if not self.project.chains:
      self._addChainLabel(chain=None, placeholder=True)
    else:
      for chain in self.project.chains:
        self._addChainLabel(chain, tryToUseSequenceCodes=True)

    if self._highlight:
      self.scrollArea.scene.removeItem(self._highlight)
    self._highlight = QtWidgets.QGraphicsTextItem()
    self._highlight.setDefaultTextColor(QtGui.QColor(self.colours[SEQUENCEMODULE_TEXT]))
    self._highlight.setFont(fixedWidthLargeFont)
    self._highlight.setPlainText('')
    # self._highlight.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
    self.scrollArea.scene.addItem(self._highlight)

  def _refreshChainLabels(self, data=None):
    """callback to refresh chains notifier
    """
    self._initialiseChainLabels()
    # highlight any predicted stretches
    self.populateFromSequenceGraphs()


class GuiChainLabel(QtWidgets.QGraphicsTextItem):
  """
  This class is acts as an anchor for each chain displayed in the Sequence Module.
  On instantiation an instance of the GuiChainResidue class is created for each residue in the chain
  along with a dictionary mapping Residue objects and GuiChainResidues, which is required for assignment.
  """
  def __init__(self, sequenceModule, mainWindow, scene, position, chain, placeholder=None, tryToUseSequenceCodes=False):
    QtWidgets.QGraphicsTextItem.__init__(self)

    self.sequenceModule = sequenceModule
    self.mainWindow = mainWindow
    self.scene = scene
    self.chain = chain
    self.project = mainWindow.application.project

    self.items = [self]  # keeps track of items specific to this chainLabel

    self.colours = getColours()
    self.setDefaultTextColor(QtGui.QColor(self.colours[GUICHAINLABEL_TEXT]))
    self.setFont(fixedWidthLargeFont)

    self.setPos(QtCore.QPointF(position[0], position[1]))

    if placeholder:
      self.text = 'No Chains in Project!'
    else:
      self.text = '%s:%s' % (chain.compoundName, chain.shortName)
    self.setHtml('<div style=><strong>'+self.text+' </strong></div>')

    self.residueDict = {}
    self.currentIndex = 0
    self.labelPosition = self.boundingRect().width()
    self.yPosition = position[1]

    if chain:
      # useSequenceCode = False
      # if tryToUseSequenceCodes:
      #   # mark residues where sequence is multiple of 10 when you can
      #   # simple rules: sequenceCodes must be integers and consecutive
      #   prevCode = None
      #   for residue in chain.residues:
      #     try:
      #       code = int(residue.sequenceCode)
      #       if prevCode and code != (prevCode+1):
      #         break
      #       prevCode = code
      #     except: # not an integer
      #       break
      #   else:
      #     useSequenceCode = True
      for idx, residue in enumerate(chain.residues):
        self._addResidue(idx, residue)

  def _addResidue(self, idx, residue):
    """
    Add residue and optional sequenceCode for
    """
    if idx % 10 == 9:  # print out every 10
      numberItem = QtWidgets.QGraphicsTextItem(residue.sequenceCode)
      numberItem.setDefaultTextColor(QtGui.QColor(self.colours[GUICHAINLABEL_TEXT]))
      numberItem.setFont(helvetica8)
      xPosition = self.labelPosition + (fontSpacing * self.currentIndex)
      numberItem.setPos(QtCore.QPointF(xPosition, self.yPosition))
      self.scene.addItem(numberItem)
      self.items.append(numberItem)
      self.currentIndex += 1

    newResidue = GuiChainResidue(self, self.mainWindow, residue, self.scene,
                                 self.labelPosition, self.currentIndex, self.yPosition)
    self.scene.addItem(newResidue)
    self.items.append(newResidue)
    self.residueDict[residue.sequenceCode] = newResidue
    self.currentIndex += 1


# WB: TODO: this used to be in some util library but the
# way drag and drop is done now has changed but
# until someone figures out how to do it the new
# way then we are stuck with the below
# (looks like only first part of if below is needed)
def _interpretEvent(event):
  """ Interpret drop event and return (type, data)
  """

  import json
  from ccpn.util.Constants import ccpnmrJsonData

  mimeData = event.mimeData()
  if mimeData.hasFormat(ccpnmrJsonData):
    jsonData = json.loads(mimeData.text())
    pids = jsonData.get('pids')

    if pids is not None:
      # internal data transfer - series of pids
      return (pids, 'pids')

      # NBNB TBD add here slots for between-applications transfer, and other types as needed

  elif event.mimeData().hasUrls():
    filePaths = [url.path() for url in event.mimeData().urls()]
    return (filePaths, 'urls')

  elif event.mimeData().hasText():
    return (event.mimeData().text(), 'text')

  return (None, None)


class GuiChainResidue(QtWidgets.QGraphicsTextItem, Base):

  fontSize = 20

  def __init__(self, guiChainLabel, mainWindow, residue, scene, labelPosition, index, yPosition):

    QtWidgets.QGraphicsTextItem.__init__(self)
    Base._init(self, acceptDrops=True)

    self.guiChainLabel = guiChainLabel
    self.mainWindow = mainWindow
    self.residue = residue
    self.scene = scene

    self.setFont(fixedWidthLargeFont)
    self.colours = getColours()
    self.setDefaultTextColor(QtGui.QColor(self.colours[GUICHAINRESIDUE_UNASSIGNED]))

    self.setPlainText(residue.shortName)
    position = labelPosition+(fontSpacing*index)
    self.setPos(QtCore.QPointF(position, yPosition))
    self.residueNumber = residue.sequenceCode

    self.setFlags(QtWidgets.QGraphicsItem.ItemIsSelectable | self.flags())
    self._styleResidue()

  # def mousePressEvent(self, ev):
  #   pass

  def _styleResidue(self):
    """
    A convenience function for applying the correct styling to GuiChainResidues depending on their state.
    """
    try:
      if self.residue.nmrResidue is not None:
        self._setStyleAssigned()
      else:
        self._setStyleUnAssigned()
    except:
      # self.setHtml('<div style="color: %s; "text-align: center;">' % self.colours[GUICHAINRESIDUE_UNASSIGNED] + '</div')
      getLogger().warning('GuiChainResidue has been deleted')

  def _setStyleAssigned(self):
    self.setHtml('<div style="color: %s; text-align: center;"><strong>' % self.colours[GUICHAINRESIDUE_ASSIGNED] +
                 self.residue.shortName + '</strong></div>')

  def _setStyleUnAssigned(self):
    self.setHtml('<div style="color: %s; "text-align: center;">' % self.colours[GUICHAINRESIDUE_UNASSIGNED] +
                 self.residue.shortName + '</div')

  def _setStylePossibleAssigned(self):
    self.setHtml('<div style="color: %s; "text-align: center;">' % self.colours[GUICHAINRESIDUE_POSSIBLE] +
                 self.residue.shortName + '</div')

  def _setStyleWarningAssigned(self):
    self.setHtml('<div style="color: %s; "text-align: center;">' % self.colours[GUICHAINRESIDUE_WARNING] +
                 self.residue.shortName + '</div')

  def _setFontBold(self):
    """
    Sets font to bold, necessary as QtWidgets.QGraphicsTextItems are used for display of residue
    one letter codes.
    """
    format = QtGui.QTextCharFormat()
    format.setFontWeight(75)
    self.textCursor().mergeCharFormat(format)
