"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2016-05-16 06:41:02 +0100 (Mon, 16 May 2016) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2016-05-16 06:41:02 +0100 (Mon, 16 May 2016) $"
__version__ = "$Revision: 9315 $"

#=====================================================================8===================
# Start of code
#=========================================================================================

import json
import typing

from PyQt4 import QtGui, QtCore

from ccpn.core.NmrAtom import NmrAtom
from ccpn.core.NmrResidue import NmrResidue
from ccpn.core.Project import Project
from ccpn.core.lib.Assignment import getNmrResiduePrediction
from ccpn.ui.gui.widgets.Module import CcpnModule
from ccpn.ui.gui.widgets.Font import Font
from ccpnmodel.ccpncore.lib.assignment.Assignment import getConnectedAtoms

EXPT_ATOM_DICT = {'H[N]': ['H', 'N'],
                  'H[N[CA]]': ['H', 'N', 'CA', 'CA-1'],
                  'H[N[co[CA]]]': ['H', 'N', 'CA-1'],
                  'H[N[co[{CA|ca[C]}]]]': ['H', 'N', 'CA-1', 'CB-1'],
                  'h{CA|Cca}coNH': ['H', 'N', 'CA-1', 'CB-1'],
                  'H[N[{CA|ca[Cali]}]]': ['H', 'N', 'CA-1', 'CB-1', 'CA', 'CB']
                  }
EXPT_DICT = {'H[N]': ['H', 'N'],
             'H[N[CA]]': [['H', 'N'], ['N', 'CA'], ['N', 'CA-1']],
             'H[N[co[CA]]]': [['H', 'N',], ['N', 'CA-1']],
             'H[N[co[{CA|ca[C]}]]]': [['H', 'N'], ['N', 'CA-1'], ['N', 'CB-1'], ['CA-1', 'CB-1']],
             'h{CA|Cca}coNH': [['H', 'N'], ['N', 'CA-1'], ['N', 'CB-1'], ['CA-1', 'CB-1']],
             'H[N[{CA|ca[Cali]}]]': [['H', 'N'], ['N', 'CA-1'], ['N', 'CB-1'],['CA-1', 'CB-1'], ['CA', 'CB'], ['N', 'CA'], ['N', 'CB']]
                  }

class GuiNmrAtom(QtGui.QGraphicsTextItem):
  """
  A graphical object specifying the position and name of an atom when created by the Assigner.
  Can be linked to a Nmr Atom.
  """

  def __init__(self, project, text, pos=None, nmrAtom=None):

    super(GuiNmrAtom, self).__init__()
    self.setPlainText(text)
    self.setPos(QtCore.QPointF(pos[0], pos[1]))
    self.nmrAtom = nmrAtom
    self.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
    self.connectedAtoms = 0
    self.setFlags(QtGui.QGraphicsItem.ItemIsSelectable | self.flags())
    if project._appBase.preferences.general.colourScheme == 'dark':
      colour1 = '#F7FFFF'
      colour2 = '#BEC4F3'
    elif project._appBase.preferences.general.colourScheme == 'light':
      colour1 = '#FDFDFC'
      colour2 = '#555D85'

    if nmrAtom:
      self.name = nmrAtom.name
    self.setDefaultTextColor(QtGui.QColor(colour1))
    if self.isSelected:
      self.setDefaultTextColor(QtGui.QColor(colour2))
    else:
      self.setDefaultTextColor(QtGui.QColor(colour1))



class GuiNmrResidue(QtGui.QGraphicsTextItem):

  """
  Object linking residues displayed in Assigner and Nmr Residues. Contains functionality for drag and
  drop assignment in conjunction with the Sequence Module.
  """

  def __init__(self, parent, nmrResidue, caAtom):

    super(GuiNmrResidue, self).__init__()
    self.setPlainText(nmrResidue.id)
    project = nmrResidue.project
    self.setFont(Font(size=12, bold=True))
    if project._appBase.preferences.general.colourScheme == 'dark':
      self.setDefaultTextColor(QtGui.QColor('#F7FFFF'))
    elif project._appBase.preferences.general.colourScheme == 'light':
      self.setDefaultTextColor(QtGui.QColor('#555D85'))
    self.setPos(caAtom.x()-caAtom.boundingRect().width()/2, caAtom.y()+30)
    self.setFlags(QtGui.QGraphicsItem.ItemIsSelectable | self.flags())
    self.parent = parent
    self.nmrResidue = nmrResidue

  def _update(self):
    self.setPlainText(self.nmrResidue.id)


  def mouseMoveEvent(self, event):

    if (event.buttons() == QtCore.Qt.LeftButton) and (event.modifiers() & QtCore.Qt.ShiftModifier):
        for item in self.parent.scene.items():
          if isinstance(item, GuiNmrResidue) and item.isSelected():
            nmrChain = item.nmrResidue.nmrChain

        drag = QtGui.QDrag(event.widget())
        mimeData = QtCore.QMimeData()
        itemData = json.dumps({'pids': [nmrChain.pid]})
        mimeData.setData('ccpnmr-json', itemData)
        mimeData.setText(itemData)
        drag.setMimeData(mimeData)

        if drag.exec_(QtCore.Qt.MoveAction | QtCore.Qt.CopyAction, QtCore.Qt.CopyAction) == QtCore.Qt.MoveAction:
          pass
          # self.close()
        else:
          self.show()



class AssignmentLine(QtGui.QGraphicsLineItem):
  """
  Object to create lines between GuiNmrAtoms with specific style, width, colour and displacement.
  """

  def __init__(self, x1, y1, x2, y2, colour, width, style=None):
    QtGui.QGraphicsLineItem.__init__(self)
    self.pen = QtGui.QPen()
    self.pen.setColor(QtGui.QColor(colour))
    self.pen.setCosmetic(True)
    self.pen.setWidth(width)
    if style and style == 'dash':
      self.pen.setStyle(QtCore.Qt.DotLine)
    self.setPen(self.pen)

    self.setLine(x1, y1, x2, y2)


class SequenceGraph(CcpnModule):
  """
  A module for the display of stretches of sequentially linked and assigned stretches of
  Nmr Residues.
  """
  def __init__(self, project=None):

    super(SequenceGraph, self).__init__(name='Sequence Graph')
    self.project = project
    self.scrollArea = QtGui.QScrollArea()
    self.scrollArea.setWidgetResizable(True)
    self.scene = QtGui.QGraphicsScene(self)
    self.scrollContents = QtGui.QGraphicsView(self.scene, self)
    self.scrollContents.setRenderHints(QtGui.QPainter.Antialiasing)
    self.scrollContents.setInteractive(True)
    self.scrollContents.setGeometry(QtCore.QRect(0, 0, 380, 1000))
    self.horizontalLayout2 = QtGui.QHBoxLayout(self.scrollContents)
    self.scrollArea.setWidget(self.scrollContents)
    self.residueCount = 0
    self.layout.addWidget(self.scrollArea)
    self.atomSpacing = 66
    self.guiResiduesShown = []
    self.predictedStretch = []
    self.direction = None
    self.selectedStretch = []
    self.scene.dragEnterEvent = self.dragEnterEvent
    self.guiNmrResidues = []
    self.guiNmrAtomDict = {}

    self.project.registerNotifier('NmrResidue', 'rename', self._resetNmrResiduePidForAssigner)

  def _resetNmrResiduePidForAssigner(self, nmrResidue, oldPid:str):
    """Reset pid for NmrResidue and all offset NmrResidues"""
    for nr in [nmrResidue] + list(nmrResidue.offsetNmrResidues):
      for guiNmrResidue in self.guiNmrResidues:
        if guiNmrResidue.nmrResidue is nr:
          guiNmrResidue._update()

  def clearAllItems(self):
    """
    Removes all displayed residues in the assigner and resets items count to zero.
    """
    for item in self.scene.items():
      self.scene.removeItem(item)
      self.residueCount = 0
      self.predictedStretch = []
      self.guiResiduesShown = []
      self.guiNmrResidues = []
      self.guiNmrAtomDict = {}

    self.scene.clear()


  def _assembleResidue(self, nmrResidue:NmrResidue, atoms:typing.Dict[str, GuiNmrAtom]):
    """
    Takes an Nmr Residue and a dictionary of atom names and GuiNmrAtoms and
    creates a graphical representation of a residue in the assigner
    """
    if self.project._appBase.preferences.general.colourScheme == 'dark':
      lineColour = '#f7ffff'
    elif self.project._appBase.preferences.general.colourScheme == 'light':
      lineColour = ''
    for item in atoms.values():
      self.scene.addItem(item)
    nmrAtoms = [atom.name for atom in nmrResidue.nmrAtoms]
    if "CB" in list(atoms.keys()):
      self._addConnectingLine(atoms['CA'], atoms['CB'], lineColour, 1.0, 0)
    if "H" in list(atoms.keys()) and nmrResidue.residueType != 'PRO':
      self._addConnectingLine(atoms['H'], atoms['N'], lineColour, 1.0, 0)
    if nmrResidue.residueType != 'PRO':
        self._addConnectingLine(atoms['H'], atoms['N'], lineColour, 1.0, 0)
    else:
      self.scene.removeItem(atoms['H'])
    # if not 'CB' in nmrAtoms:
    #   self.scene.removeItem(atoms['CB'])
    #   self.scene.removeItem(cbLine)

    self._addConnectingLine(atoms['N'], atoms['CA'], lineColour, 1.0, 0)
    self._addConnectingLine(atoms['CO'], atoms['CA'], lineColour, 1.0, 0)
    self.nmrResidueLabel = GuiNmrResidue(self, nmrResidue, atoms['CA'])
    self.guiNmrResidues.append(self.nmrResidueLabel)
    self.scene.addItem(self.nmrResidueLabel)
    self._addResiduePredictions(nmrResidue, atoms['CA'])


  def addResidue(self, nmrResidue:NmrResidue, direction:str, atomSpacing=None):
    """
    Takes an Nmr Residue and a direction, either '-1 or '+1', and adds a residue to the assigner
    corresponding to the Nmr Residue.
    Nmr Residue name displayed beneath CA of residue drawn and residue type predictions displayed
    beneath Nmr Residue name
    """
    if atomSpacing:
      self.atomSpacing = atomSpacing

    nmrAtoms = [nmrAtom.name for nmrAtom in nmrResidue.nmrAtoms]
    print(nmrResidue.residueType, nmrAtoms)
    if self.residueCount == 0:

      if 'H' in nmrAtoms:
        hAtom = self._createGuiNmrAtom("H", (0, self.atomSpacing), nmrResidue.fetchNmrAtom(name='H'))
      else:
        hAtom = self._createGuiNmrAtom("H", (0, self.atomSpacing))
      if 'N' in nmrAtoms:
        nAtom = self._createGuiNmrAtom("N", (0, hAtom.y()-self.atomSpacing), nmrResidue.fetchNmrAtom(name='N'))
      else:
        nAtom = self._createGuiNmrAtom("N", (0, hAtom.y()-self.atomSpacing))
      if 'CA' in nmrAtoms:
        caAtom = self._createGuiNmrAtom("CA", (nAtom.x()+self.atomSpacing, nAtom.y()), nmrResidue.fetchNmrAtom(name='CA'))
      else:
        caAtom = self._createGuiNmrAtom("CA", (nAtom.x()+self.atomSpacing, nAtom.y()))
      if 'CB' in nmrAtoms:
        cbAtom = self._createGuiNmrAtom("CB", (caAtom.x(), caAtom.y()-self.atomSpacing), nmrResidue.fetchNmrAtom(name='CB'))
      else:
        # cbAtom = None
        cbAtom = self._createGuiNmrAtom("CB", (caAtom.x(), caAtom.y()-self.atomSpacing))
      if 'CO' in nmrAtoms:
        coAtom = self._createGuiNmrAtom("CO", (caAtom.x()+abs(caAtom.x()-nAtom.x()),nAtom.y()), nmrResidue.fetchNmrAtom(name='CO'))
      else:
        coAtom = self._createGuiNmrAtom("CO", (caAtom.x()+abs(caAtom.x()-nAtom.x()),nAtom.y()))
      coAtom.setZValue(10)

      atoms = {'H': hAtom, 'N': nAtom, 'CA': caAtom, 'CB': cbAtom, 'CO': coAtom}

      self.guiResiduesShown.append(atoms)
      self.predictedStretch.append(nmrResidue)

    else:
        if self.residueCount == 1:
          self.nmrResidueLabel._update()
        if nmrResidue.sequenceCode.endswith('-1') or direction == '-1':

          oldGuiResidue = self.guiResiduesShown[0]
          if 'CO' in nmrAtoms:
            coAtom2 = self._createGuiNmrAtom("CO", (oldGuiResidue["N"].x()-abs(oldGuiResidue["CA"].x()
            -oldGuiResidue["N"].x())-(oldGuiResidue["N"].boundingRect().width()/2), oldGuiResidue["CA"].y()),
                                   nmrResidue.fetchNmrAtom(name='CO'))
          else:
            coAtom2 = self._createGuiNmrAtom("CO", (oldGuiResidue["N"].x()-abs(oldGuiResidue["CA"].x()
            -oldGuiResidue["N"].x())-(oldGuiResidue["N"].boundingRect().width()/2), oldGuiResidue["CA"].y()))
          coAtom2.setZValue(10)
          if 'CA' in nmrAtoms:
            caAtom2 = self._createGuiNmrAtom("CA", ((coAtom2.x()-self.atomSpacing), oldGuiResidue["N"].y()),
                                   nmrResidue.fetchNmrAtom(name='CA'))
          else:
            caAtom2 = self._createGuiNmrAtom("CA", ((coAtom2.x()-self.atomSpacing), oldGuiResidue["N"].y()))
          if 'CB' in nmrAtoms:
            cbAtom2 = self._createGuiNmrAtom("CB", (caAtom2.x(), caAtom2.y()-self.atomSpacing),
                                   nmrResidue.fetchNmrAtom(name='CB'))
          else:
            cbAtom2 = self._createGuiNmrAtom("CB", (caAtom2.x(), caAtom2.y()-self.atomSpacing))
          if 'N' in nmrAtoms:
            nAtom2 = self._createGuiNmrAtom("N",(caAtom2.x()-self.atomSpacing, coAtom2.y()),
                                  nmrResidue.fetchNmrAtom(name='N'))
          else:
            nAtom2 = self._createGuiNmrAtom("N",(caAtom2.x()-self.atomSpacing, coAtom2.y()))
          if 'H' in nmrAtoms:
            hAtom2 = self._createGuiNmrAtom("H", (nAtom2.x(), nAtom2.y()+self.atomSpacing),
                                  nmrResidue.fetchNmrAtom(name='H'))
          else:
            hAtom2 = self._createGuiNmrAtom("H", (nAtom2.x(), nAtom2.y()+self.atomSpacing))

          atoms = {'H':hAtom2, "N": nAtom2, "CA":caAtom2, "CB":cbAtom2, "CO":coAtom2, 'N-1': oldGuiResidue['N']}

          self.guiResiduesShown.insert(0, atoms)
          self.predictedStretch.insert(0, nmrResidue)

        else:

          oldGuiResidue = self.guiResiduesShown[-1]
          if 'N' in nmrAtoms:
            nAtom2 = self._createGuiNmrAtom("N", (oldGuiResidue["CO"].x()+self.atomSpacing +
            oldGuiResidue["CO"].boundingRect().width()/2, oldGuiResidue["CA"].y()),
                                  nmrResidue.fetchNmrAtom(name='N'))
          else:
            nAtom2 = self._createGuiNmrAtom("N", (oldGuiResidue["CO"].x()+self.atomSpacing+
            oldGuiResidue["CO"].boundingRect().width()/2, oldGuiResidue["CA"].y()))
          if 'H' in nmrAtoms:
            hAtom2 = self._createGuiNmrAtom("H", (nAtom2.x(), nAtom2.y()+self.atomSpacing),
                                  nmrResidue.fetchNmrAtom(name='H'))
          else:
            hAtom2 = self._createGuiNmrAtom("H", (nAtom2.x(), nAtom2.y()+self.atomSpacing))
          if 'CA' in nmrAtoms:
            caAtom2 = self._createGuiNmrAtom("CA", (nAtom2.x()+(nAtom2.x()-oldGuiResidue["CO"].x())
                  -(oldGuiResidue["CO"].boundingRect().width()/2), oldGuiResidue["CO"].y()),
                                   nmrResidue.fetchNmrAtom(name='CA'))
          else:
            caAtom2 = self._createGuiNmrAtom("CA", (nAtom2.x()+(nAtom2.x()-oldGuiResidue["CO"].x())
                  -(oldGuiResidue["CO"].boundingRect().width()/2), oldGuiResidue["CO"].y()))
          if 'CB' in nmrAtoms:
            cbAtom2 = self._createGuiNmrAtom("CB", (caAtom2.x(), caAtom2.y()-self.atomSpacing),
                                   nmrResidue.fetchNmrAtom(name='CB'))
          else:
            cbAtom2 = None
          if 'CO' in nmrAtoms:
            coAtom2 = self._createGuiNmrAtom("CO", (caAtom2.x()+abs(caAtom2.x()-nAtom2.x()),nAtom2.y()),
                                   nmrResidue.fetchNmrAtom(name='CO'))
          else:
            coAtom2 = self._createGuiNmrAtom("CO", (caAtom2.x()+abs(caAtom2.x()-nAtom2.x()),nAtom2.y()))
          coAtom2.setZValue(10)


          atoms = {'H':hAtom2, "N": nAtom2, "CA":caAtom2, "CO":coAtom2, 'N-1': oldGuiResidue['N']}
          if cbAtom2:
            atoms["CB"] = cbAtom2

          self.guiResiduesShown.append(atoms)
          self.predictedStretch.append(nmrResidue)
    self._assembleResidue(nmrResidue, atoms)


    if len(self.predictedStretch) > 2:
      self.predictSequencePosition(self.predictedStretch)

    self.residueCount += 1


  def _addResiduePredictions(self, nmrResidue:NmrResidue, caAtom:GuiNmrAtom):
    """
    Gets predictions for residue type based on BMRB statistics and determines label positions
    based on caAtom position.
    """

    predictions = list(set(map(tuple, (getNmrResiduePrediction(nmrResidue, self.project.chemicalShiftLists[0])))))
    print(predictions)
    predictions.sort(key=lambda a: float(a[1][:-1]), reverse=True)
    for prediction in predictions:
      predictionLabel = QtGui.QGraphicsTextItem()
      predictionLabel.setPlainText(prediction[0]+' '+prediction[1])
      if self.project._appBase.preferences.general.colourScheme == 'dark':
        predictionLabel.setDefaultTextColor(QtGui.QColor('#F7FFFF'))
      elif self.project._appBase.preferences.general.colourScheme == 'light':
        predictionLabel.setDefaultTextColor(QtGui.QColor('#555D85'))
      predictionLabel.setFont(Font(size=12, bold=True))
      # caAtom.x()-caAtom.boundingRect().width()/2, caAtom.y()+30)
      predictionLabel.setPos(caAtom.x()-caAtom.boundingRect().width()/2, caAtom.y()+(30*(predictions.index(prediction)+2)))
      self.scene.addItem(predictionLabel)

  def predictSequencePosition(self, nmrResidues:list):
    """
    Predicts sequence position for Nmr residues displayed in the Assigner and highlights appropriate
    positions in the Sequence Module if it is displayed.
    """
    from ccpn.core.lib.Assignment import getSpinSystemsLocation

    possibleMatches = getSpinSystemsLocation(self.project, nmrResidues,
                      self.project.chains[0], self.project.chemicalShiftLists[0])

    for possibleMatch in possibleMatches:
      if possibleMatch[0] > 1:

        if hasattr(self.project._appBase.mainWindow, 'sequenceModule'):
          self.project._appBase.mainWindow.sequenceModule._highlightPossibleStretches(possibleMatch[1])


  def _showBackboneAssignments(self, nmrChain):
    for nmrResidue in nmrChain.nmrResidues:
      self.addResidue(nmrResidue, direction='+1')
    for ii, res in enumerate(self.guiResiduesShown):
      if ii % 10 == 0:
        self.project._appBase.mainWindow.pythonConsole.writeConsoleCommand('%s residues added' % str(ii))
      if ii+1 < len(self.guiResiduesShown)-1:
        self._addConnectingLine(res['CO'], self.guiResiduesShown[ii+1]['N'], '#f7ffff', 1.0, 0)
    self._getAssignmentsFromSpectra()


  def _addConnectingLine(self, atom1:GuiNmrAtom, atom2:GuiNmrAtom, colour:str, width:float, displacement:float, style:str=None):
    """
    Adds a line between two GuiNmrAtoms using the width, colour, displacement and style specified.
    """
    if atom1.y() > atom2.y():
      if atom1.x() - atom2.x() == 0:
        x1 = atom1.x() + (atom1.boundingRect().width()/2)
        y1 = atom1.y() + (atom1.boundingRect().height()*0.2)
        x2 = atom2.x() + (atom1.boundingRect().width()/2)
        y2 = atom2.y() + (atom2.boundingRect().height()*0.8)
        newLine = AssignmentLine(x1+displacement, y1, x2+displacement, y2, colour, width, style)

      if atom1.x() > atom2.x():
        x1 = atom1.x() + (atom1.boundingRect().width()*0.5)
        x2 = atom2.x() + (atom1.boundingRect().width()*1.5)
        y1 = atom1.y() + (atom1.boundingRect().height()/8)
        y2 = atom2.y() + (atom2.boundingRect().height()/2)
        newLine = AssignmentLine(x1, y1+displacement, x2, y2+displacement, colour, width, style)

      if atom1.y() > atom2.y() and atom1.x() < atom2.x():
        x1 = atom1.x() + (atom1.boundingRect().width()*0.5)
        x2 = atom2.x() - (atom1.boundingRect().width()/16)
        y1 = atom1.y() + (atom1.boundingRect().height()/8)
        y2 = atom2.y() + (atom2.boundingRect().height()/2)
        newLine = AssignmentLine(x1+displacement, y1+displacement, x2+displacement, y2+displacement, colour, width, style)

    elif atom1.y() < atom2.y():
      if atom1.x() - atom2.x() == 0:
        x1 = atom1.x() + (atom1.boundingRect().width()/2)
        y1 = atom1.y() + (atom1.boundingRect().height()*0.8)
        x2 = atom2.x() + (atom1.boundingRect().width()/2)
        y2 = atom2.y() + (atom2.boundingRect().height()*0.2)
        newLine = AssignmentLine(x1+displacement, y1, x2+displacement, y2, colour, width, style)

      if atom1.x() < atom2.x():
        x1 = atom1.x() + (atom1.boundingRect().width())
        x2 = atom2.x() + (atom1.boundingRect().width()*0.5)
        y1 = atom1.y() + (atom1.boundingRect().height()/2)
        y2 = atom2.y() + (atom2.boundingRect().height()/8)
        newLine = AssignmentLine(x1+displacement, y1+displacement, x2+displacement, y2+displacement, colour, width, style)

      if atom1.x() > atom2.x():
        x1 = atom1.x() + (atom1.boundingRect().width())
        x2 = atom2.x() + (atom1.boundingRect().width()*0.25)
        y1 = atom1.y() + (atom1.boundingRect().height()/2)
        y2 = atom2.y() + (atom2.boundingRect().height()/8)
        newLine = AssignmentLine(x1+displacement, y1+displacement, x2+displacement, y2+displacement, colour, width, style)

    elif atom1.x() > atom2.x() and atom1.y() - atom2.y() == 0:
      x1 = atom1.x()
      x2 = atom2.x() + atom2.boundingRect().width()
      y1 = atom1.y() + (atom1.boundingRect().height()*0.5)
      y2 = atom2.y() + (atom2.boundingRect().height()*0.5)
      newLine = AssignmentLine(x1, y1+displacement, x2, y2+displacement, colour, width, style)


    elif atom1.x() < atom2.x() and atom1.y() - atom2.y() == 0:
      x1 = atom1.x() + atom1.boundingRect().width()
      x2 = atom2.x()
      y1 = atom1.y() + (atom1.boundingRect().height()*0.5)
      y2 = atom2.y() + (atom2.boundingRect().height()*0.5)
      newLine = AssignmentLine(x1, y1+displacement, x2, y2+displacement, colour, width, style)
      # self.scene.addItem(newLine)

    self.scene.addItem(newLine)

    return newLine


  def _createGuiNmrAtom(self, atomType:str, position:tuple, nmrAtom:NmrAtom=None) -> GuiNmrAtom:
    """
    Creates a GuiNmrAtom specified by the atomType and graphical position supplied.
    GuiNmrAtom can be linked to an NmrAtom by supplying it to the function.
    """
    atom = GuiNmrAtom(self.project, text=atomType, pos=position, nmrAtom=nmrAtom)
    self.guiNmrAtomDict[nmrAtom] = atom
    return atom

  def _getAssignmentsFromSpectra(self):
    for spectrum in self.project.spectra:
      apiDataSource = spectrum._wrappedData
      connections = list(set(map(tuple, getConnectedAtoms(apiDataSource))))
      for ii, connection in enumerate(connections):
        # if ii % 10 == 0:
        #   self.project._appBase.mainWindow.pythonConsole.writeConsoleCommand('%s residues coloured' % str(ii))
        nmrAtomPair = [self.project._data2Obj.get(connection[0]).nmrAtom,
                       self.project._data2Obj.get(connection[1]).nmrAtom]
        # sorting makes sure drawing is done properly
        guiNmrAtomPair = [self.guiNmrAtomDict.get(a) for a in sorted(nmrAtomPair, reverse=True)]
        if None not in guiNmrAtomPair:
          displacement = min(guiNmrAtomPair[0].connectedAtoms, guiNmrAtomPair[1].connectedAtoms)
          self._addConnectingLine(guiNmrAtomPair[0], guiNmrAtomPair[1], spectrum.positiveContourColour, 2.0, displacement)
          guiNmrAtomPair[0].connectedAtoms += 1.0
          guiNmrAtomPair[1].connectedAtoms += 1.0


#NBNB TBD:
# The below should be replaced. See commented-out code at the end fo Assigner.__init__
# After refactoring, guiNmrResidues should not be global

#
# def _resetNmrResiduePidForAssigner(project:Project, apiResonanceGroup:ApiResonanceGroup):
#   """Reset pid for NmrResidue and all offset NmrResidues"""
#   if hasattr(project._appBase.mainWindow, 'assigner'):
#     getDataObj = project._data2Obj.get
#     obj = getDataObj(apiResonanceGroup)
#     for guiNmrResidue in guiNmrResidues:
#       guiNmrResidue.update()
#
#
# Project._setupApiNotifier(_resetNmrResiduePidForAssigner, ApiResonanceGroup, 'setSequenceCode')
# Project._setupApiNotifier(_resetNmrResiduePidForAssigner, ApiResonanceGroup, 'setDirectNmrChain')
# Project._setupApiNotifier(_resetNmrResiduePidForAssigner, ApiResonanceGroup, 'setResidueType')
# Project._setupApiNotifier(_resetNmrResiduePidForAssigner, ApiResonanceGroup, 'setAssignedResidue')


