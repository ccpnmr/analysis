"""
This file contains the SequenceModule module

GWV: modified 1-9/12/2016
GWV: 13/04/2017: Disconnected from Sequence Graph; Needs rafactoring

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
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.guiSettings import fixedWidthFont, fixedWidthLargeFont
from ccpn.ui.gui.guiSettings import textFontHugeSpacing as fontSpacing
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.MessageDialog import showYesNo
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.widgets.MessageDialog import progressManager


class SequenceModule(CcpnModule):
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

  def __init__(self, mainWindow, name='Sequence'):
    #CcpnModule.__init__(self, size=(10, 30), name='Sequence', closable=False)
    #TODO: make closable
    CcpnModule.__init__(self, mainWindow=mainWindow, name=name)

    self.mainWindow = mainWindow
    self.project = mainWindow.application.project
    self.colourScheme = mainWindow.application.colourScheme
    #self.label.hide()

    self.setAcceptDrops(True)
    self.scrollArea = QtWidgets.QScrollArea()
    self.scrollArea.setWidgetResizable(True)
    self.scrollArea.scene = QtWidgets.QGraphicsScene(self)
    self.scrollContents = QtWidgets.QGraphicsView(self.scrollArea.scene, self)
    self.scrollContents.setAcceptDrops(True)
    self.scrollContents.setInteractive(True)

    self.scrollContents.setAlignment(QtCore.Qt.AlignLeft)
    self.scrollContents.setGeometry(QtCore.QRect(0, 0, 380, 1000))
    self.horizontalLayout2 = QtWidgets.QHBoxLayout(self.scrollContents)
    self.scrollArea.setWidget(self.scrollContents)
    self.setStyleSheet("""QScrollArea QScrollBar::horizontal {max-height: 20px;}
                          QScrollArea QScrollBar::vertical{max-width:20px;}
                      """)
    self.residueCount = 0
    self.mainWidget.layout().addWidget(self.scrollArea)
    # connect graphics scene dragMoveEvent to CcpnModule dragMoveEvent - required for drag-and-drop
    # assignment routines.
    self.scrollArea.scene.dragMoveEvent = self._dragMoveEvent
    self.scrollArea.scene.dropEvent = self._dropEvent
    self.chainLabels = []
    self._highlight = None
    self._refreshChainLabels()

    #GWV: removed fixed height restrictions but maximum height instead
    #self.setFixedHeight(2*self.widgetHeight)
    #self.scrollContents.setFixedHeight(2*self.widgetHeight)
    self.setMaximumHeight(100)
    self.scrollContents.setMaximumHeight(100)

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
      self._highlight.setHtml('<div style="color: %s; text-align: center;"><strong>' % 'orange' +
                              item.toPlainText() + '</strong></div>')
      self._highlight.setPos(item.pos())
    else:
      self._highlight.setPlainText('')

    # item = self.scrollArea.scene.itemAt({"pids": ["NC:@2", "NR:@2.@142."]}pos)
    # ###item = self.scene.itemAt(event.scenePos())
    # if isinstance(item, GuiChainResidue):
    #   item.setDefaultTextColor(QtGui.QColor('orange'))
    #   self._highlight.setPlainText(item.toPlainText())
    #   self._highlight.setPos(item.pos())
    # else:
    #   self._highlight.setPlainText('')
    event.accept()

  def _dropEvent(self, event):

    self._highlight.setPlainText('')
    data, dataType = _interpretEvent(event)
    if dataType == 'pids':

      # check that the drop event contains the corrcect information
      if isinstance(data, Iterable) and len(data) == 2:
        nmrChain = self.mainWindow.project.getByPid(data[0])
        nmrResidue = self.mainWindow.project.getByPid(data[1])
        if isinstance(nmrChain, NmrChain) and isinstance(nmrResidue, NmrResidue):
          if nmrResidue.nmrChain == nmrChain:
            self._processNmrChains(data, event)

  def _processNmrChains(self, data:typing.List[str], event:QtGui.QMouseEvent):
    """
    Processes a list of NmrResidue Pids and assigns the residue onto which the data is dropped and
    all succeeding residues according to the length of the list.
    """

    if self.colourScheme == 'dark':
      colour = '#f7ffff'
    elif self.colourScheme == 'light':
      colour = '#666e98'
    guiRes = self._getGuiItem(self.scrollArea.scene)
    #self.scene.itemAt(event.scenePos())

    # if not hasattr(guiRes, 'residue'):
    #   return

    nmrChain = self.mainWindow.project.getByPid(data[0])
    selectedNmrResidue = self.mainWindow.project.getByPid(data[1])   # ejb - new, pass in selected nmrResidue
    residues = [guiRes.residue]
    toAssign = [nmrResidue for nmrResidue in nmrChain.nmrResidues if '-1' not in nmrResidue.sequenceCode]
    result = showYesNo('Assignment', 'Assign nmrChain: %s to residue: %s?' % (toAssign[0].nmrChain.id, residues[0].id))
    if result:

      with progressManager(self.mainWindow, 'Assigning nmrChain: %s to residue: %s' % (toAssign[0].nmrChain.id, residues[0].id)):

        try:
          if nmrChain.id == '@-':
            # assume that it is the only one
            nmrChain.assignSingleResidue(selectedNmrResidue, guiRes.residue)
          else:
            for ii in range(len(toAssign)-1):
              resid = residues[ii]
              next = resid.nextResidue    #TODO:ED may not have a .nextResidue
              residues.append(next)
            nmrChain.assignConnectedResidues(guiRes.residue)
          for ii, res in enumerate(residues):
            if hasattr(self, 'guiChainLabel'):
              guiResidue = self.guiChainLabel.residueDict.get(res.sequenceCode)
              guiResidue.setHtml('<div style="color: %s; text-align: center;"><strong>' % colour +
                                   res.shortName+'</strong></div>')
        except Exception as es:
          getLogger().warning('Sequence Module: %s' % str(es))

  def populateFromSequenceGraphs(self):
    """
    Take the selected chain from the first opened sequenceGraph and highlight in module
    """
    # get the list of open sequenceGraphs
    from ccpn.AnalysisAssign.modules.SequenceGraph import SequenceGraphModule
    seqGraphs = [sg for sg in SequenceGraphModule.getInstances()]

    if seqGraphs:
      try:
        seqGraphs[0].predictSequencePosition(seqGraphs[0].predictedStretch)
      except Exception as es:
        getLogger().warning('Error: no predictedStretch found: %s' % str(es))

  def _highlightPossibleStretches(self, residues:typing.List[Residue]):
    """
    CCPN INTERNAL called in predictSequencePosition method of SequenceGraph.
    Highlights regions on the sequence specified by the list of residues passed in.
    """
    for res1 in self.chainLabels[0].residueDict.values():
      res1._styleResidue()

    try:
      for residue in residues:
        guiResidue = self.chainLabels[0].residueDict[residue.sequenceCode]
        guiResidue._styleResidue()
      if self.colourScheme == 'dark':
        colour = '#e4e15b'
      elif self.colourScheme == 'light':
        colour = '#009a00'
      else:
        colour = '#808080'
      guiResidues = []
      for residue in residues:
        guiResidue = self.chainLabels[0].residueDict[residue.sequenceCode]
        guiResidues.append(guiResidue)
        guiResidue.setHtml('<div style="color: %s;text-align: center; padding: 0px;">' % colour+
                             residue.shortName+'</div>')
    except Exception as es:
      pass

  def _addChainLabel(self, chain:Chain, placeholder=False, tryToUseSequenceCodes=False):
    """
    Creates and adds a GuiChainLabel to the sequence module.
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

  def _addChainResidue(self, residue):
    if self.chainLabel.chain is not residue.chain: # they should always be equal if function just called as a notifier
      return
    number = residue.chain.residues.index(residue)
    self.chainLabel._addResidue(number, residue)

  def _registerNotifiers(self):
    # self.project.registerNotifier('Chain', 'create', self._addChainLabel)
    # self.project.registerNotifier('Residue', 'create', self._addChainResidue)
    # self.project.registerNotifier('Chain', 'delete', self._refreshChainLabels)

    self._chainNotifier = Notifier(self.project
                                  , [Notifier.CREATE]
                                  , 'Chain'
                                  , self._addChainLabel)
    self._residueNotifier = Notifier(self.project
                                  , [Notifier.CREATE]
                                  , 'Residue'
                                  , self._addChainResidue)
    self._chainDeleteNotifier = Notifier(self.project
                                  , [Notifier.DELETE]
                                  , 'Chain'
                                  , self._refreshChainLabels)

  def _unRegisterNotifiers(self):
    if self._chainNotifier:
      self._chainNotifier.unRegister()
    if self._residueNotifier:
      self._residueNotifier.unRegister()
    if self._chainDeleteNotifier:
      self._chainDeleteNotifier.unRegister()

  def _closeModule(self):
    self._unRegisterNotifiers()
    SequenceModule._alreadyOpened = False
    action = self.mainWindow.application._findMenuAction('View', 'Show Sequence')
    if action: # should be True
      action.setChecked(False)
    CcpnModule._closeModule(self)

  def close(self):
    self._closeModule()     # ejb - needed when closing/opening project

  def _refreshChainLabels(self, *args, **kw):
    for chainLabel in self.chainLabels:
      for item in chainLabel.items:
        self.scrollArea.scene.removeItem(item)
      chainLabel.items = [] # probably don't need to do this
    self.chainLabels = []
    self.widgetHeight = 0 # dynamically calculated from the number of chains

    if not self.project.chains:
      self._addChainLabel(chain=None, placeholder=True)
    else:
      for chain in self.project.chains:
        self._addChainLabel(chain, tryToUseSequenceCodes=True)

    if self._highlight:
      self.scrollArea.scene.removeItem(self._highlight)
    self._highlight = QtWidgets.QGraphicsTextItem()
    self._highlight.setDefaultTextColor(QtGui.QColor('orange'))
    self._highlight.setFont(fixedWidthLargeFont)
    self._highlight.setPlainText('')
    # self._highlight.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
    self.scrollArea.scene.addItem(self._highlight)

class GuiChainLabel(QtWidgets.QGraphicsTextItem):
  """
  This class is acts as an anchor for each chain displayed in the Sequence Module.
  On instantiation an instance of the GuiChainResidue class is created for each residue in the chain
  along with a dictionary mapping Residue objects and GuiChainResidues, which is required for assignment.
  """
  def __init__(self, sequenceModule, mainWindow, scene, position, chain, placeholder=None, tryToUseSequenceCodes=False):
    QtWidgets.QGraphicsTextItem.__init__(self)

    self.mainWindow = mainWindow
    self.chain = chain
    self.items = [self]  # keeps track of items specific to this chainLabel

    # self.colourScheme = project._appBase.colourScheme
    self.colourScheme = mainWindow.application.colourScheme

    if self.colourScheme == 'dark':
      self.colour1 = '#bec4f3'
      self.colour2 = '#f7ffff'
    elif self.colourScheme == 'light':
      #colour = '#bd8413'
      self.colour1 = 'black'
      self.colour2 = '#555D85'
    self.setDefaultTextColor(QtGui.QColor(self.colour1))

    self.setPos(QtCore.QPointF(position[0], position[1]))
    if placeholder:
      self.text = 'No Chains in Project!'
    else:
      self.text = '%s:%s' % (chain.compoundName, chain.shortName)
    self.sequenceModule = sequenceModule
    self.setHtml('<div style=><strong>'+self.text+' </strong></div>')
    self.setFont(fixedWidthLargeFont)
    self.residueDict = {}
    self.project = mainWindow.application.project
    self.currentIndex = 0
    self.scene = scene
    self.labelPosition = self.boundingRect().width()
    self.yPosition = position[1]
    if chain:
      useSequenceCode = False
      if tryToUseSequenceCodes:
        # mark residues where sequence is multiple of 10 when you can
        # simple rules: sequenceCodes must be integers and consecutive
        prevCode = None
        for residue in chain.residues:
          try:
            code = int(residue.sequenceCode)
            if prevCode and code != (prevCode+1):
              break
            prevCode = code
          except: # not an integer
            break
        else:
          useSequenceCode = True
      for n, residue in enumerate(chain.residues):
        self._addResidue(n, residue, useSequenceCode)

  def _addResidue(self, number, residue, useSequenceCode=False):
    newResidue = GuiChainResidue(self, self.mainWindow, residue, self.scene,
                                 self.labelPosition, self.currentIndex, self.yPosition)
    self.scene.addItem(newResidue)
    self.items.append(newResidue)
    self.residueDict[residue.sequenceCode] = newResidue
    self.currentIndex += 1
    value = int(residue.sequenceCode)-1 if useSequenceCode else number
    if value % 10 == 9:  # print out every 10
      numberItem = QtWidgets.QGraphicsTextItem(residue.sequenceCode)
      numberItem.setDefaultTextColor(QtGui.QColor(self.colour1))
      numberItem.setFont(fixedWidthFont)
      xPosition = self.labelPosition + (fontSpacing * self.currentIndex)
      numberItem.setPos(QtCore.QPointF(xPosition, self.yPosition))
      self.scene.addItem(numberItem)
      self.items.append(numberItem)
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
    Base.__init__(self, acceptDrops=True)

    # self.project = project
    self.mainWindow = mainWindow

    self.residue = residue
    self.guiChainLabel = guiChainLabel

    #font = QtGui.QFont('Lucida Console', GuiChainResidue.fontSize)
    #font.setStyleHint(QtGui.QFont.Monospace)
    #self.setFont(font)
    self.setFont(fixedWidthLargeFont)
    # self.colourScheme = project._appBase.colourScheme
    self.colourScheme = mainWindow.application.colourScheme

    if self.colourScheme == 'dark':
      self.colour1 = '#bec4f3'  # un-assigned
      self.colour2 = '#f7ffff'  # assigned
      self.colour3 = '#e4e15b'  # drag-enter event
    elif self.colourScheme == 'light':
      #self.colour1 = '#bd8413'
      #self.colour2 = '#666e98'
      self.colour1 = 'black'
      self.colour2 = '#555D85'
      self.colour3 = '#009a00'  # drag-enter event

    self.setDefaultTextColor(QtGui.QColor(self.colour1))

    self.setPlainText(residue.shortName)
    position = labelPosition+(fontSpacing*index)
    self.setPos(QtCore.QPointF(position, yPosition))
    self.residueNumber = residue.sequenceCode
    # WB: TODO: below is terrible code (the scene functions are trampled over and over)
    # but somehow this seems to be the way it has to be done
    # and this then means there is that awful itemAt(position) check in the drag functions
    # scene.dragLeaveEvent = self._dragLeaveEvent
    # scene.dragEnterEvent = self._dragEnterEvent
    # scene.dropEvent = self.dropEvent
    self.scene = scene
    self.setFlags(QtWidgets.QGraphicsItem.ItemIsSelectable | self.flags())
    self._styleResidue()

  def mousePressEvent(self, ev):
    pass

  def _styleResidue(self):
    """
    A convenience function for applying the correct styling to GuiChainResidues depending on their state.
    """
    try:
      if self.residue.nmrResidue is not None:
        self.setHtml('<div style="color: %s; text-align: center;"><strong>' % self.colour2 +
                     self.residue.shortName+'</strong></div>')
      else:
        self.setHtml('<div style="color: %s; "text-align: center;">'% self.colour1 + self.residue.shortName+'</div')
    except:
      # self.setHtml('<div style="color: %s; "text-align: center;">' % self.colour1 + '</div')
      getLogger().warning('GuiChainResidue has been deleted')

  def _setFontBold(self):
    """
    Sets font to bold, necessary as QtWidgets.QGraphicsTextItems are used for display of residue
    one letter codes.
    """
    format = QtGui.QTextCharFormat()
    format.setFontWeight(75)
    self.textCursor().mergeCharFormat(format)

  def _dragEnterEvent(self, event:QtGui.QMouseEvent):
    """
    A re-implementation of the QGraphicsTextItem.dragEnterEvent to facilitate the correct colouring
    of GuiChainResidues during drag-and-drop.
    Required for processNmrChains to work properly.
    """
    # WB: TODO: this is awful, having to check what item is at the position
    # the trampling of the scene drag functions above means that self is always
    # the last GuiChainResidue, and a much better way would be if self was the
    # GuiChainResidue of interest, which would then eliminate this itemAt check
    pos = event.scenePos()
    pos = QtCore.QPointF(pos.x(), pos.y()-25) # WB: TODO: -25 is a hack to take account of scrollbar height

    # item = self.scene.itemAt(pos)
    item = self.scene.itemAt(pos, QtGui.QTransform())     # ejb - pyqt5

    ###item = self.scene.itemAt(event.scenePos())
    if isinstance(item, GuiChainResidue):
      item.setDefaultTextColor(QtGui.QColor('orange'))    #self.colour3))
      self.scene.update()
    event.accept()

  def _dragLeaveEvent(self, event:QtGui.QMouseEvent):
    """
    A re-implementation of the QGraphicsTextItem.dragLeaveEvent to facilitate the correct colouring
    of GuiChainResidues during drag-and-drop.
    Required for processNmrChains to work properly.
    GWV: TODO: this need to call the _StyleResidue function
    """
    if self.colourScheme == 'dark':
      colour = '#f7ffff'
    elif self.colourScheme == 'light':
      colour = '#666e98'
    pos = event.scenePos()
    pos = QtCore.QPointF(pos.x(), pos.y()-25) # WB: TODO: -25 is a hack to take account of scrollbar height

    # item = self.scene.itemAt(pos)
    item = self.scene.itemAt(pos, QtGui.QTransform())     # ejb - pyqt5

    ###item = self.scene.itemAt(event.scenePos())
    if isinstance(item, GuiChainResidue):
      item.setDefaultTextColor(QtGui.QColor(colour))
    event.accept()

  # WB: TODO: a version of this used to be in DropBase but that has
  # been changed but it is not clear (to me) how to use this new
  # system so stick with the old for now
  def _dropEvent(self, event):

    data, dataType = _interpretEvent(event)
    if dataType == 'pids':

      # check that the drop event contains the corrcect information
      if isinstance(data, Iterable) and len(data) == 2:
        nmrChain = self.mainWindow.project.getByPid(data[0])
        nmrResidue = self.mainWindow.project.getByPid(data[1])
        if isinstance(nmrChain, NmrChain) and isinstance(nmrResidue, NmrResidue):
          if nmrResidue.nmrChain == nmrChain:
            self._processNmrChains(data, event)


    #   if self._appBase is not None:
    #     appBase = self._appBase
    #   else:
    #     appBase = self._appBase
    #   if hasattr(appBase, 'backboneModule'):
    #     nmrResidueTable = appBase.backboneModule.nmrResidueTable
    #     nmrResidueTable.nmrResidueTable.objectLists = self.project.nmrChains
    #     nmrResidueTable.nmrChainPulldown.select(residues[0].chain.nmrChain.pid)
    #
    #   event.accept()
    # self.guiChainLabel.sequenceModule.overlay.hide()
    # self.project._appBase.sequenceGraph.resetSequenceGraph()





