__author__ = 'simon1'


from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.Label import Label
from ccpncore.gui.ScrollArea import ScrollArea
from ccpncore.gui.Font import Font
from ccpnmrcore.DropBase import DropBase
from PyQt4 import QtCore, QtGui
import math

class SequenceModule(CcpnDock):

  def __init__(self, appBase, project):
    CcpnDock.__init__(self, name='Sequence')

    self.project=project
    self.label.hide()
    self.setAcceptDrops(True)
    self.scrollArea = QtGui.QScrollArea()
    self.scrollArea.setWidgetResizable(True)
    self.scrollArea.scene = QtGui.QGraphicsScene(self)
    self.project = project
    self.scrollContents = QtGui.QGraphicsView(self.scrollArea.scene, self)
    self.scrollContents.setAcceptDrops(True)
    self.scrollContents.setAlignment(QtCore.Qt.AlignLeft)
    # self.scrollContents.setInteractive(True)
    self.scrollContents.setGeometry(QtCore.QRect(0, 0, 380, 1000))
    self.horizontalLayout2 = QtGui.QHBoxLayout(self.scrollContents)
    self.scrollArea.setWidget(self.scrollContents)
    self.setStyleSheet("""QScrollArea QScrollBar::horizontal {max-height: 10px;}
                          QScrollArea QScrollBar::vertical{max-width:10px;}
                      """)
    self.residueCount = 0
    self.layout.addWidget(self.scrollArea)

    self.scrollArea.scene.dragMoveEvent = self.dragMoveEvent
    self.chainLabels = []
    self.widgetHeight = 0
    for chain in project.chains:
      self.addChainLabel(chain)

    self.setFixedHeight(2*self.widgetHeight)
    self.scrollContents.setFixedHeight(2*self.widgetHeight)
    # for chainLabel in self.chainLabels:
    #   self.highlightPossibleStretches(chainLabel)

  def highlightPossibleStretches(self, residues):
    for residue in residues:
      guiResidue = self.chainLabels[0].residueDict[residue.sequenceCode]
      guiResidue.setHtml('<div style="color: #e4e15b;text-align: center;">'+
                           residue.shortName+'</div>')


  def addChainLabel(self, chain):
    chainLabel = GuiChainLabel(self.project, self.scrollArea.scene, chain, position=[0, self.widgetHeight])
    self.scrollArea.scene.addItem(chainLabel)
    self.chainLabels.append(chainLabel)
    self.widgetHeight+=(0.8*(chainLabel.boundingRect().height()))
    # print(dir(chainLabel))


class GuiChainLabel(QtGui.QGraphicsTextItem):

  def __init__(self, project, scene, chain, position):
    QtGui.QGraphicsTextItem.__init__(self)
    self.chain = chain
    self.setPos(QtCore.QPointF(position[0], position[1]))
    self.text=chain.compoundName
    self.setHtml('<div style=><strong>'+chain.compoundName+': </strong></div>')
    self.setFont(Font(size=20, bold=True))
    self.setDefaultTextColor(QtGui.QColor('#bec4f3'))
    self.residueDict = {}
    i = 0
    for residue in chain.residues:
      newResidue = GuiChainResidue(self, project, residue, scene, self.boundingRect().width(), i, position[1])
      scene.addItem(newResidue)
      self.residueDict[residue.sequenceCode] = newResidue
      i+=1

class GuiChainResidue(DropBase, QtGui.QGraphicsTextItem):

  fontSize = 20

  def __init__(self, parent, project, residue, scene, labelPosition, index, yPosition):

    QtGui.QGraphicsTextItem.__init__(self)
    DropBase.__init__(self, project._appBase)
    self.setPlainText(residue.shortName)
    position = labelPosition+(20*index)
    self.setFont(Font(size=GuiChainResidue.fontSize, normal=True))
    self.setDefaultTextColor(QtGui.QColor('#bec4f3'))
    self.setPos(QtCore.QPointF(position, yPosition))
    self.residueNumber = residue.sequenceCode
    if residue.nmrResidue is not None:
      self.setHtml('<div style="color: #f7ffff; text-align: center;"><strong>'+
                   residue.shortName+'</strong></div>')
    else:
      self.setHtml('<div style:"text-align: center;">'+residue.shortName+'</div')
    self.project = project
    self.residue = residue
    self.setAcceptDrops(True)
    self.parent=parent
    scene.dragLeaveEvent = self.dragLeaveEvent
    scene.dragEnterEvent = self.dragEnterEvent
    scene.dropEvent = self.dropEvent
    self.scene = scene
    self.setFlags(QtGui.QGraphicsItem.ItemIsSelectable | self.flags())


  def setFontBold(self):
    format = QtGui.QTextCharFormat()
    format.setFontWeight(75)
    self.textCursor().mergeCharFormat(format)


  def dragEnterEvent(self, event):

    item = self.scene.itemAt(event.scenePos())
    if isinstance(item, GuiChainResidue):
      item.setDefaultTextColor(QtGui.QColor('#e4e15b'))
    event.accept()

  def dragLeaveEvent(self, event):
    item = self.scene.itemAt(event.scenePos())
    if isinstance(item, GuiChainResidue):
      item.setDefaultTextColor(QtGui.QColor('#f7ffff'))
    event.accept()


  def processNmrResidues(self, data, event):
    res = self.scene.itemAt(event.scenePos())
    nmrResidue = self.project.getByPid(data[0])
    res.setHtml('<div style="color: #f7ffff; text-align: center;"><strong>'+
                  res.residue.shortName+'</strong></div>')
    nmrResidue.residue = res.residue

    for assignableResidue in data[1:]:
      res = nmrResidue.residue.nextResidue
      guiResidue = self.parent.residueDict.get(res.sequenceCode)
      guiResidue.setHtml('<div style="color: #f7ffff; text-align: center;"><strong>'+
                         res.shortName+'</strong></div>')
      nmrResidue = self.project.getByPid(assignableResidue)
      nmrResidue.residue = res






