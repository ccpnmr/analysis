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
import sys
from PyQt4 import QtGui,QtCore

from ccpn.lib.Assignment import CCP_CODES

from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.Font import Font
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.lib.assignment.ChemicalShift import getSpinSystemResidueProbability


EXPT_ATOM_DICT = {'H[N]' : ['H', 'N'],
                  'H[N[CA]]': ['H', 'N', 'CA', 'CA-1'],
                  'H[N[co[CA]]]': ['H', 'N', 'CA-1'],
                  'H[N[co[{CA|ca[C]}]]]': ['H', 'N', 'CA-1', 'CB-1'],
                  'h{CA|Cca}coNH': ['H', 'N', 'CA-1', 'CB-1'],
                  'H[N[{CA|ca[Cali]}]]': ['H', 'N', 'CA-1', 'CB-1', 'CA', 'CB']
                  }

class Assigner(CcpnDock):

  def __init__(self, project=None):

    super(Assigner, self).__init__(name='Assigner')
    self.project=project
    self.scrollArea = QtGui.QScrollArea()
    self.scrollArea.setWidgetResizable(True)
    self.scene = QtGui.QGraphicsScene(self)
    self.scrollContents = QtGui.QGraphicsView(self.scene, self)
    self.scrollContents.setInteractive(True)
    self.scrollContents.setGeometry(QtCore.QRect(0, 0, 380, 1000))
    self.horizontalLayout2 = QtGui.QHBoxLayout(self.scrollContents)
    self.scrollArea.setWidget(self.scrollContents)
    self.residueCount = 0
    self.layout.addWidget(self.scrollArea)
    self.atomSpacing = 66
    self.residuesShown = []
    self.predictedStretch = []
    self.direction = None
    self.selectedStretch = []
    self.scene.dragEnterEvent = self.dragEnterEvent

  def clearAllItems(self):
    for item in self.scene.items():
      self.scene.removeItem(item)
      self.residueCount = 0




  def assembleResidue(self, nmrResidue, atoms):
    for item in atoms.values():
      self.scene.addItem(item)
    nmrAtoms = [atom.name for atom in nmrResidue.atoms]
    cbLine = self.addConnectingLine(atoms['CA'], atoms['CB'], 'grey', 1.0, 0)
    if not 'CB' in nmrAtoms:
      self.scene.removeItem(atoms['CB'])
      self.scene.removeItem(cbLine)

    self.addConnectingLine(atoms['H'], atoms['N'], 'grey', 1.0, 0)
    self.addConnectingLine(atoms['N'], atoms['CA'], 'grey', 1.0, 0)
    self.addConnectingLine(atoms['CO'], atoms['CA'], 'grey', 1.0, 0)
    nmrAtomLabel = GuiNmrResidue(self, nmrResidue, atoms['CA'])
    self.scene.addItem(nmrAtomLabel)
    self.addResiduePredictions(nmrResidue, atoms['CA'])


  def addResidue(self, nmrResidue):

    if self.residueCount == 0:
      self.nmrChain = self.project.newNmrChain()
      self.nmrChain.connectedNmrResidues = [nmrResidue]
      hAtom = self.addAtom("H", (0, self.atomSpacing), nmrResidue.fetchNmrAtom(name='H'))
      nAtom = self.addAtom("N", (0, hAtom.y()-self.atomSpacing),nmrResidue.fetchNmrAtom(name='N'))
      caAtom = self.addAtom("CA", (nAtom.x()+self.atomSpacing, nAtom.y()),nmrResidue.fetchNmrAtom(name='CA'))
      cbAtom = self.addAtom("CB", (caAtom.x(), caAtom.y()-self.atomSpacing), nmrResidue.fetchNmrAtom(name='CB'))
      coAtom = self.addAtom("CO", (caAtom.x()+abs(caAtom.x()-nAtom.x()),nAtom.y()),nmrResidue.fetchNmrAtom(name='CO'))
      coAtom.setZValue(10)

      atoms = {'H': hAtom, 'N': nAtom, 'CA': caAtom, 'CB': cbAtom, 'CO': coAtom}

      self.residuesShown.append(atoms)

    else:
        if self.direction == 'left':
          newConnectedStretch = list(self.nmrChain.connectedNmrResidues).insert(0, nmrResidue)
          self.nmrChain.connectedNmrResidues = newConnectedStretch
          oldResidue = self.residuesShown[0]
          coAtom2 = self.addAtom("CO", (oldResidue["N"].x()-abs(oldResidue["CA"].x()
          -oldResidue["N"].x())-(oldResidue["N"].boundingRect().width()/2),oldResidue["CA"].y()),
                                 nmrResidue.fetchNmrAtom(name='CO'))
          coAtom2.setZValue(10)
          caAtom2 = self.addAtom("CA", ((coAtom2.x()-self.atomSpacing), oldResidue["N"].y()),
                                 nmrResidue.fetchNmrAtom(name='CA'))
          cbAtom2 = self.addAtom("CB", (caAtom2.x(), caAtom2.y()-self.atomSpacing),
                                 nmrResidue.fetchNmrAtom(name='CB'))
          nAtom2 = self.addAtom("N",(caAtom2.x()-self.atomSpacing, coAtom2.y()),
                                nmrResidue.fetchNmrAtom(name='N'))
          hAtom2 = self.addAtom("H", (nAtom2.x(), nAtom2.y()+self.atomSpacing),
                                nmrResidue.fetchNmrAtom(name='H'))

          atoms = {'H':hAtom2, "N": nAtom2, "CA":caAtom2, "CB":cbAtom2, "CO":coAtom2, 'N-1': oldResidue['N']}

          self.residuesShown.insert(0, atoms)

        if self.direction == 'right':
          newConnectedStretch = list(self.nmrChain.connectedNmrResidues).append(nmrResidue)
          self.nmrChain.connectedNmrResidues = newConnectedStretch
          oldResidue = self.residuesShown[-1]
          nAtom2 = self.addAtom("N", (oldResidue["CO"].x()+self.atomSpacing+
          oldResidue["CO"].boundingRect().width()/2, oldResidue["CA"].y()),
                                nmrResidue.fetchNmrAtom(name='CA'))
          hAtom2 = self.addAtom("H", (nAtom2.x(), nAtom2.y()+self.atomSpacing),
                                nmrResidue.fetchNmrAtom(name='H'))
          caAtom2 = self.addAtom("CA", (nAtom2.x()+(nAtom2.x()-oldResidue["CO"].x())
                -(oldResidue["CO"].boundingRect().width()/2), oldResidue["CO"].y()),
                                 nmrResidue.fetchNmrAtom(name='CA'))
          cbAtom2 = self.addAtom("CB", (caAtom2.x(), caAtom2.y()-self.atomSpacing),
                                 nmrResidue.fetchNmrAtom(name='CB'))
          coAtom2 = self.addAtom("CO", (caAtom2.x()+abs(caAtom2.x()-nAtom2.x()),nAtom2.y()),
                                 nmrResidue.fetchNmrAtom(name='CO'))
          coAtom2.setZValue(10)

          atoms = {'H':hAtom2, "N": nAtom2, "CA":caAtom2, "CB":cbAtom2, "CO":coAtom2, 'N-1': oldResidue['N']}

          self.residuesShown.append(atoms)

    self.assembleResidue(nmrResidue, atoms)
    for spectrum in self.project.spectra:
      self.addSpectrumAssignmentLines(spectrum, atoms)
    # self.addSpectrumAssignmentLines(self.project.getById(self.spectra['intra'][0]), atoms)
    # self.addSpectrumAssignmentLines(self.project.getById(self.spectra['inter'][0]), atoms)

    self.residueCount+=1
    print(self.nmrChain.connectedNmrResidues)

  def addResiduePredictions(self, nmrResidue, caAtom):
    predictions = getNmrResiduePrediction(nmrResidue, self.project.chemicalShiftLists[0])
    for prediction in predictions:
      predictionLabel = QtGui.QGraphicsTextItem()
      predictionLabel.setPlainText(prediction[0]+' '+prediction[1])
      predictionLabel.setDefaultTextColor(QtGui.QColor('#f7ffff'))
      predictionLabel.setFont(Font(size=12, bold=True))
      predictionLabel.setPos(caAtom.x()-caAtom.boundingRect().width(), caAtom.y()+(30*(predictions.index(prediction)+2)))
      self.scene.addItem(predictionLabel)

  def predictSequencePosition(self):
    sequence = ''.join([residue.shortName for residue in self.project.chains[0].residues])
    if len(self.predictedStretch) > 3:
      string = ''.join(self.predictedStretch)
      import re
      matcher = re.search(string, sequence)
      newSequenceText = '<div>'+sequence[:matcher.start()]+'<span style="background-color: #000; ' \
                        'color: #FFF; display: inline-block; padding: 0 3px;"><strong>'+sequence[
                        matcher.start():matcher.end()]+'</strong></span>'+sequence[matcher.end():]+'</div>'
      self.project._appBase.mainWindow.sequenceWidget.chainLabel(chainCode=self.project.chains[0].compoundName).setText(newSequenceText)
    #
    # else:
    #   print(self.predictedStretch)

  def addSpectrumAssignmentLines(self, spectrum, residue):
      assignedAtoms1 = []
      if not spectrum.experimentType in EXPT_ATOM_DICT:
        pass
      else:
        possibleAtoms = EXPT_ATOM_DICT[spectrum.experimentType]
        lineColour = spectrum.positiveContourColour
        for atom in residue.values():
          for peak in atom.nmrAtom.assignedPeaks[0]:
            if peak.peakList.spectrum == spectrum:
              for atom in peak.dimensionNmrAtoms:
                for a in atom:
                  assignedAtoms1.append(a)



        assignedAtoms = list(set(assignedAtoms1))
        print(spectrum, assignedAtoms)
        if 'H' and 'N' in assignedAtoms:
          displacement = min(residue['H'].connectedAtoms, residue['N'].connectedAtoms)
          if displacement % 2 == 0:
            self.addConnectingLine(residue['H'], residue['N'], lineColour, 2.0, displacement*2/2)
          else:
            self.addConnectingLine(residue['H'], residue['N'], lineColour, 2.0, displacement*-2)
          residue['H'].connectedAtoms +=1
          residue['N'].connectedAtoms +=1
        if 'N' and 'CA' in assignedAtoms:
          displacement = min(residue['CA'].connectedAtoms, residue['N'].connectedAtoms)
          if displacement % 2 == 0:
            self.addConnectingLine(residue['CA'], residue['N'], lineColour, 2.0, displacement*2/2)
          else:
            self.addConnectingLine(residue['CA'], residue['N'], lineColour, 2.0, displacement*-2)
          self.addConnectingLine(residue['N'], residue['CA'], lineColour, 2.0, displacement*2)
          residue['CA'].connectedAtoms +=1
          residue['N'].connectedAtoms +=1
        if 'N' and 'CB' in assignedAtoms:
          displacement = min(residue['CB'].connectedAtoms, residue['N'].connectedAtoms)
          if displacement % 2 == 0:
            self.addConnectingLine(residue['N'], residue['CB'], lineColour, 2.0, displacement*2/2)
          else:
            self.addConnectingLine(residue['N'], residue['CB'], lineColour, 2.0, displacement*-2)
          residue['CB'].connectedAtoms +=1
          residue['N'].connectedAtoms +=1
        if 'CA' and 'CB' in assignedAtoms:
          displacement = min(residue['CA'].connectedAtoms, residue['CB'].connectedAtoms)
          if displacement % 2 == 0:
            self.addConnectingLine(residue['CA'], residue['CB'], lineColour, 2.0, displacement*2/2)
          else:
            self.addConnectingLine(residue['CA'], residue['CB'], lineColour, 2.0, displacement*-2)
          residue['CA'].connectedAtoms +=1
          residue['CB'].connectedAtoms +=1

        if 'N-1' in residue:
          if 'CA-1' and 'N' in assignedAtoms:
            displacement = min(residue['CA'].connectedAtoms, residue['N-1'].connectedAtoms)
            if displacement % 2 == 0:
              self.addConnectingLine(residue['N-1'], residue['CA'], lineColour, 2.0, displacement*2/2)
            else:
              self.addConnectingLine(residue['N-1'], residue['CA'], lineColour, 2.0, displacement*-2)

          if 'CB-1' and 'N' in assignedAtoms:
            displacement = min(residue['CB'].connectedAtoms, residue['N-1'].connectedAtoms)
            if displacement % 2 == 0:
              self.addConnectingLine(residue['N-1'], residue['CB'], lineColour, 2.0, displacement*2/2)
            else:
              self.addConnectingLine(residue['N-1'], residue['CB'], lineColour, 2.0, displacement*-2)

        if 'CB-1' in residue:
           if 'CB-1' and 'N' in assignedAtoms:
            displacement = min(residue['CB-1'].connectedAtoms, residue['N'].connectedAtoms)
            if displacement % 2 == 0:
              self.addConnectingLine(residue['N'], residue['CB-1'], lineColour, 2.0, displacement*2/2)
            else:
              self.addConnectingLine(residue['N'], residue['CB-1'], lineColour, 2.0, displacement*-2)

        if 'CA-1' in residue:
           if 'CA-1' and 'N' in assignedAtoms:
            displacement = min(residue['CA-1'].connectedAtoms, residue['N'].connectedAtoms)
            if displacement % 2 == 0:
              self.addConnectingLine(residue['N'], residue['CA-1'], lineColour, 2.0, displacement*2/2)
            else:
              self.addConnectingLine(residue['N'], residue['CA-1'], lineColour, 2.0, displacement*-2)


  def addConnectingLine(self, atom1, atom2, colour, width, displacement):

    if atom1.y() > atom2.y() and atom1.x() - atom2.x() == 0:
      x1 = atom1.x() + (atom1.boundingRect().width()/2)
      y1 = atom1.y() + (atom1.boundingRect().height()*0.2)
      x2 = atom2.x() + (atom1.boundingRect().width()/2)
      y2 = atom2.y() + (atom2.boundingRect().height()*0.8)
      newLine = AssignmentLine(x1+displacement, y1, x2+displacement, y2, colour, width)
      self.scene.addItem(newLine)

    elif atom1.y() < atom2.y() and atom1.x() - atom2.x() == 0:
      x1 = atom1.x() + (atom1.boundingRect().width()/2)
      y1 = atom1.y() + (atom1.boundingRect().height()*0.8)
      x2 = atom2.x() + (atom1.boundingRect().width()/2)
      y2 = atom2.y() + (atom2.boundingRect().height()*0.2)
      newLine = AssignmentLine(x1+displacement, y1, x2+displacement, y2, colour, width)
      self.scene.addItem(newLine)

    elif atom1.x() > atom2.x() and atom1.y() - atom2.y() == 0:
      x1 = atom1.x()
      x2 = atom2.x() + atom2.boundingRect().width()
      y1 = atom1.y() + (atom1.boundingRect().height()*0.5)
      y2 = atom2.y() + (atom2.boundingRect().height()*0.5)
      newLine = AssignmentLine(x1, y1+displacement, x2, y2+displacement, colour, width)
      self.scene.addItem(newLine)

    elif atom1.x() < atom2.x() and atom1.y() - atom2.y() == 0:
      x1 = atom1.x() + atom1.boundingRect().width()
      x2 = atom2.x()
      y1 = atom1.y() + (atom1.boundingRect().height()*0.5)
      y2 = atom2.y() + (atom2.boundingRect().height()*0.5)
      newLine = AssignmentLine(x1, y1+displacement, x2, y2+displacement, colour, width)
      self.scene.addItem(newLine)

    elif atom1.y() > atom2.y() and atom1.x() > atom2.x():
      x1 = atom1.x() + (atom1.boundingRect().width()*0.5)
      x2 = atom2.x() + (atom1.boundingRect().width()*1.5)
      y1 = atom1.y() + (atom1.boundingRect().height()/8)
      y2 = atom2.y() + (atom2.boundingRect().height()/2)
      newLine = AssignmentLine(x1, y1+displacement, x2, y2+displacement, colour, width)
      self.scene.addItem(newLine)

    elif atom1.y() < atom2.y() and atom1.x() < atom2.x():
      x1 = atom1.x() + (atom1.boundingRect().width())
      x2 = atom2.x() + (atom1.boundingRect().width()*0.5)
      y1 = atom1.y() + (atom1.boundingRect().height()/2)
      y2 = atom2.y() + (atom2.boundingRect().height()/8)
      newLine = AssignmentLine(x1+displacement, y1+displacement, x2+displacement, y2+displacement, colour, width)
      self.scene.addItem(newLine)

    elif atom1.y() > atom2.y() and atom1.x() < atom2.x():
      x1 = atom1.x() + (atom1.boundingRect().width()*0.5)
      x2 = atom2.x() - (atom1.boundingRect().width()/16)
      y1 = atom1.y() + (atom1.boundingRect().height()/8)
      y2 = atom2.y() + (atom2.boundingRect().height()/2)
      newLine = AssignmentLine(x1+displacement, y1+displacement, x2+displacement, y2+displacement, colour, width)
      self.scene.addItem(newLine)

    elif atom1.y() < atom2.y() and atom1.x() > atom2.x():
      x1 = atom1.x() + (atom1.boundingRect().width())
      x2 = atom2.x() + (atom1.boundingRect().width()*0.25)
      y1 = atom1.y() + (atom1.boundingRect().height()/2)
      y2 = atom2.y() + (atom2.boundingRect().height()/8)
      newLine = AssignmentLine(x1+displacement, y1+displacement, x2+displacement, y2+displacement, colour, width)
      self.scene.addItem(newLine)

    return newLine


  def addAtom(self, atomType, position, nmrAtom):
    atom = GuiNmrAtom(text=atomType, pos=position, nmrAtom=nmrAtom)
    return(atom)

class GuiNmrAtom(QtGui.QGraphicsTextItem):

  def __init__(self, text, pos=None, nmrAtom=None):

    super(GuiNmrAtom, self).__init__()
    self.setPlainText(text)
    self.setPos(QtCore.QPointF(pos[0], pos[1]))
    self.nmrAtom = nmrAtom
    self.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
    self.connectedAtoms = 0
    self.setFlags(QtGui.QGraphicsItem.ItemIsSelectable | self.flags())
    self.name = nmrAtom.name
    # self.brush = QtGui.QBrush()
    self.setDefaultTextColor(QtGui.QColor('#f7ffff'))
    # self.setBrush(self.brush)
    if self.isSelected:
      # self.setFont(Font(size=17.5, bold=True))
      print(self.nmrAtom)
      self.setDefaultTextColor(QtGui.QColor('#bec4f3'))
    else:
      self.setDefaultTextColor(QtGui.QColor('#f7ffff'))
      # self.setBrush(self.brush)



  def hoverEnterEvent(self, event):
    self.setDefaultTextColor(QtGui.QColor('#e4e15b'))

  def hoverLeaveEvent(self, event):
    self.setDefaultTextColor(QtGui.QColor('#f7ffff'))

  def printAtom(self):
    print(self)


class GuiNmrResidue(QtGui.QGraphicsTextItem):

  def __init__(self, parent, nmrResidue, caAtom):

    super(GuiNmrResidue, self).__init__()
    self.setPlainText(nmrResidue.id)
    self.setFont(Font(size=12, bold=True))
    self.setDefaultTextColor(QtGui.QColor('#f7ffff'))
    self.setPos(caAtom.x()-caAtom.boundingRect().width()/2, caAtom.y()+30)
    self.setFlags(QtGui.QGraphicsItem.ItemIsSelectable | self.flags())
    self.parent = parent
    self.nmrResidue = nmrResidue

  def mouseMoveEvent(self, event):

    if (event.buttons() == QtCore.Qt.LeftButton) and (event.modifiers() & QtCore.Qt.ShiftModifier):
        print("Left click drag")
        aDict = {}
        for item in self.parent.scene.items():
          if isinstance(item, GuiNmrResidue) and item.isSelected():
            aDict[item.x()] = item.nmrResidue.pid

        assignStretch = ','.join([aDict[key] for key in sorted(aDict.keys())])

        drag = QtGui.QDrag(event.widget())
        mime = QtCore.QMimeData()
        drag.setMimeData(mime)
        mime.setData('application/x-assignedStretch',assignStretch)

        drag.exec_()



class AssignmentLine(QtGui.QGraphicsLineItem):

  def __init__(self, x1, y1, x2, y2, colour, width):
    QtGui.QGraphicsLineItem.__init__(self)
    self.pen = QtGui.QPen()
    self.pen.setColor(QtGui.QColor(colour))
    self.pen.setCosmetic(True)
    self.pen.setWidth(width)
    self.setPen(self.pen)
    self.setLine(x1, y1, x2, y2)

def getNmrResiduePrediction(nmrResidue, sl):
    predictions = {}
    spinSystem = nmrResidue._wrappedData
    shiftList = sl._wrappedData
    for code in CCP_CODES:
      predictions[code] = float(getSpinSystemResidueProbability(spinSystem, shiftList, code))
    tot = sum(predictions.values())
    refinedPredictions = {}
    for code in CCP_CODES:
      v = round(predictions[code]/tot * 100, 2)
      if v > 0:
        refinedPredictions[code] = v

    finalPredictions = []

    for value in sorted(refinedPredictions.values(), reverse=True)[:5]:
      key = [key for key, val in refinedPredictions.items() if val==value][0]
      finalPredictions.append([key, str(value)+' %'])

    return finalPredictions