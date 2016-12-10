"""
This file contains SequenceModule module

intial version by Simon;
modified by Geerten 1-9/12/2016

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


from ccpn.core.Chain import Chain
from ccpn.core.Residue import Residue

from ccpn.ui.gui.widgets.Module import CcpnModule
from ccpn.ui.gui.widgets.MessageDialog import showYesNo
from ccpn.ui.gui.guiSettings import textFontHugeBold
from ccpn.ui.gui.guiSettings import textFontHuge

import typing

from ccpn.ui.gui.DropBase import DropBase
from PyQt4 import QtCore, QtGui


class SequenceModule(CcpnModule):

  """
  The module displays all chains in the project as one-letter amino acids. The one letter residue
  sequence codes are all instances of the GuiChainResidue class and the style applied to a residue
  indicates its assignment state and, when coupled with the Sequence Graph module, indicates if a
  stretch of residues matches a given stretch of connected NmrResidues. The QGraphicsScene and
  QGraphicsView instances provide the canvas on to which the amino acids representations are drawn.
  """

  def __init__(self, project):
    CcpnModule.__init__(self, size=(10, 30), name='Sequence', closable=False)

    self.project = project
    self.colourScheme = project._appBase.colourScheme
    #self.label.hide()
    self.setAcceptDrops(True)
    self.scrollArea = QtGui.QScrollArea()
    self.scrollArea.setWidgetResizable(True)
    self.scrollArea.scene = QtGui.QGraphicsScene(self)
    self.project = project
    self.scrollContents = QtGui.QGraphicsView(self.scrollArea.scene, self)
    self.scrollContents.setAcceptDrops(True)
    self.scrollContents.setAlignment(QtCore.Qt.AlignLeft)
    self.scrollContents.setGeometry(QtCore.QRect(0, 0, 380, 1000))
    self.horizontalLayout2 = QtGui.QHBoxLayout(self.scrollContents)
    self.scrollArea.setWidget(self.scrollContents)
    self.setStyleSheet("""QScrollArea QScrollBar::horizontal {max-height: 10px;}
                          QScrollArea QScrollBar::vertical{max-width:0px;}
                      """)
    self.residueCount = 0
    self.layout.addWidget(self.scrollArea)
    # connect graphics scene dragMoveEvent to CcpnModule dragMoveEvent - required for drag-and-drop
    # assignment routines.
    self.scrollArea.scene.dragMoveEvent = self.dragMoveEvent
    self.chainLabels = []
    self.widgetHeight = 0
    if not project.chains:
      self._addChainLabel(placeholder=True)
    else:
      for chain in project.chains:
        self._addChainLabel(chain)

    self.setFixedHeight(2*self.widgetHeight)
    self.scrollContents.setFixedHeight(2*self.widgetHeight)


  def _highlightPossibleStretches(self, residues:typing.List[Residue]):
    """
    CCPN INTERNAL called in predictSequencePosition method of SequenceGraph.
    Highlights regions on the sequence specified by the list of residues passed in.
    """
    for res1 in self.chainLabels[0].residueDict.values():
      res1._styleResidue()

    for residue in residues:
      guiResidue = self.chainLabels[0].residueDict[residue.sequenceCode]
      guiResidue._styleResidue()
    if self.colourScheme == 'dark':
      colour = '#e4e15b'
    elif self.colourScheme == 'light':
      colour = '#009a00'
    guiResidues = []
    for residue in residues:
      guiResidue = self.chainLabels[0].residueDict[residue.sequenceCode]
      guiResidues.append(guiResidue)
      guiResidue.setHtml('<div style="color: %s;text-align: center; padding: 0px;">' % colour+
                           residue.shortName+'</div>')


  def _addChainLabel(self, chain:Chain=None, placeholder=False):
    """
    Creates and adds a GuiChainLabel to the sequence module.
    """
    chainLabel = GuiChainLabel(self, self.project, self.scrollArea.scene, position=[0, self.widgetHeight], chain=chain, placeholder=placeholder)
    self.scrollArea.scene.addItem(chainLabel)
    self.chainLabels.append(chainLabel)
    self.widgetHeight += (0.8*(chainLabel.boundingRect().height()))


class GuiChainLabel(QtGui.QGraphicsTextItem):
  """
  This class is acts as an anchor for each chain displayed in the Sequence Module.
  On instantiation an instance of the GuiChainResidue class is created for each residue in the chain
  along with a dictionary mapping Residue objects and GuiChainResidues, which is required for assignment.
  """
  def __init__(self, parent, project, scene, position, chain, placeholder=None):
    QtGui.QGraphicsTextItem.__init__(self)

    self.chain = chain

    self.colourScheme = project._appBase.colourScheme
    #print('>>', self.colourScheme)
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
      self.text = chain.compoundName
    self.parent = parent
    self.setHtml('<div style=><strong>'+self.text+' </strong></div>')
    self.setFont(textFontHuge)
    self.residueDict = {}
    i = 0
    if chain:
      for residue in chain.residues:
        newResidue = GuiChainResidue(self, project, residue, scene, self.boundingRect().width(), i, position[1])
        scene.addItem(newResidue)
        self.residueDict[residue.sequenceCode] = newResidue
        i += 1

class GuiChainResidue(DropBase, QtGui.QGraphicsTextItem):

  fontSize = 20

  def __init__(self, parent, project, residue, scene, labelPosition, index, yPosition):

    QtGui.QGraphicsTextItem.__init__(self)
    DropBase.__init__(self, project._appBase)
    self.setAcceptDrops(True)

    self.project = project
    self.residue = residue
    self.parent = parent

    #font = QtGui.QFont('Lucida Console', GuiChainResidue.fontSize)
    #font.setStyleHint(QtGui.QFont.Monospace)
    #self.setFont(font)
    self.setFont(textFontHuge)
    self.colourScheme = project._appBase.colourScheme
    if self.colourScheme == 'dark':
      self.colour1 = '#bec4f3'  # un-assigned
      self.colour2 = '#f7ffff'  # assigned
    elif self.colourScheme == 'light':
      #self.colour1 = '#bd8413'
      #self.colour2 = '#666e98'
      self.colour1 = 'black'
      self.colour2 = '#555D85'
    self.setDefaultTextColor(QtGui.QColor(self.colour1))

    self.setPlainText(residue.shortName)
    position = labelPosition+(20*index)
    self.setPos(QtCore.QPointF(position, yPosition))
    self.residueNumber = residue.sequenceCode
    scene.dragLeaveEvent = self._dragLeaveEvent
    scene.dragEnterEvent = self._dragEnterEvent
    scene.dropEvent = self.dropEvent
    self.scene = scene
    self.setFlags(QtGui.QGraphicsItem.ItemIsSelectable | self.flags())
    self._styleResidue()


  def _styleResidue(self):
    """
    A convenience function for applying the correct styling to GuiChainResidues depending on their state.
    """
    if self.residue.nmrResidue is not None:
      self.setHtml('<div style="color: %s; text-align: center;"><strong>' % self.colour2 +
                   self.residue.shortName+'</strong></div>')
    else:
      self.setHtml('<div style="color: %s; "text-align: center;">'% self.colour1 + self.residue.shortName+'</div')


  def _setFontBold(self):
    """
    Sets font to bold, necessary as QtGui.QGraphicsTextItems are used for display of residue
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

    if self.colourScheme == 'dark':
      colour = '#e4e15b'
    elif self.colourScheme == 'light':
      colour = '#009a00'
    item = self.scene.itemAt(event.scenePos())
    if isinstance(item, GuiChainResidue):
      item.setDefaultTextColor(QtGui.QColor(colour))
    event.accept()

  def _dragLeaveEvent(self, event:QtGui.QMouseEvent):
    """
    A re-implementation of the QGraphicsTextItem.dragLeaveEvent to facilitate the correct colouring
    of GuiChainResidues during drag-and-drop.
    Required for processNmrChains to work properly.
    """
    if self.colourScheme == 'dark':
      colour = '#f7ffff'
    elif self.colourScheme == 'light':
      colour = '#666e98'
    item = self.scene.itemAt(event.scenePos())
    if isinstance(item, GuiChainResidue):
      item.setDefaultTextColor(QtGui.QColor(colour))
    event.accept()


  def processNmrChains(self, data:typing.List[str], event:QtGui.QMouseEvent):
    """
    Processes a list of NmrResidue Pids and assigns the residue onto which the data is dropped and
    all succeeding residues according to the length of the list.
    """

    if self.colourScheme == 'dark':
      colour = '#f7ffff'
    elif self.colourScheme == 'light':
      colour = '#666e98'
    guiRes = self.scene.itemAt(event.scenePos())
    nmrChain = self.project.getByPid(data[0])
    residues = [guiRes.residue]
    toAssign = [nmrResidue for nmrResidue in nmrChain.nmrResidues if '-1' not in nmrResidue.sequenceCode]
    result = showYesNo('Assignment', 'Assign %s to residue %s?' % (toAssign[0].id, residues[0].id))
    if result:
      for ii in range(len(toAssign)-1):
        resid = residues[ii]
        next = resid.nextResidue
        residues.append(next)
      nmrChain.assignConnectedResidues(guiRes.residue)
      for ii, res in enumerate(residues):
        guiResidue = self.parent.residueDict.get(res.sequenceCode)
        guiResidue.setHtml('<div style="color: %s; text-align: center;"><strong>' % colour +
                             res.shortName+'</strong></div>')
      if self._appBase is not None:
        appBase = self._appBase
      else:
        appBase = self._appBase
      if hasattr(appBase, 'backboneModule'):
        nmrResidueTable = appBase.backboneModule.nmrResidueTable
        nmrResidueTable.nmrResidueTable.objectLists = self.project.nmrChains
        nmrResidueTable.nmrChainPulldown.select(residues[0].chain.nmrChain.pid)

      event.accept()
    self.parent.parent.overlay.hide()
    self.project._appBase.sequenceGraph.resetSequenceGraph()






