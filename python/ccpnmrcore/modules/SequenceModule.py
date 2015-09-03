__author__ = 'simon1'


from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.Label import Label
from ccpncore.gui.ScrollArea import ScrollArea
from ccpncore.gui.Font import Font
from ccpnmrcore.DropBase import DropBase
from PyQt4 import QtCore, QtGui
import math

class SequenceModule(DropBase, CcpnDock):

  def __init__(self, appBase, project):
    CcpnDock.__init__(self, name='Sequence')

    self.project=project
    self.setStyleSheet("""
    QWidget { background-color: #000021;
              border: 1px solid #00092d;
    }
    """)
    DropBase.__init__(self, appBase)
    self.setAcceptDrops(True)
    self.scrollArea = QtGui.QScrollArea()
    self.scrollArea.setWidgetResizable(True)
    self.scrollArea.scene = QtGui.QGraphicsScene(self)
    self.project = project
    self.scrollContents = QtGui.QGraphicsView(self.scrollArea.scene, self)
    self.scrollContents.setAcceptDrops(True)
    self.scrollContents.setAlignment(QtCore.Qt.AlignLeft)
    self.scrollContents.setInteractive(True)
    self.scrollContents.setGeometry(QtCore.QRect(0, 0, 380, 1000))
    self.horizontalLayout2 = QtGui.QHBoxLayout(self.scrollContents)
    self.scrollArea.setWidget(self.scrollContents)
    self.residueCount = 0
    self.layout.addWidget(self.scrollArea)
    self.scrollArea.scene.dragMoveEvent = self.dragMoveEvent
    for chain in project.chains:
      self.addChainLabel(chain)

  def addChainLabel(self, chain):
    chainLabel = GuiChainLabel(self.project, self.scrollArea.scene, chain)
    self.scrollArea.scene.addItem(chainLabel)

class GuiChainLabel(QtGui.QGraphicsTextItem):

  def __init__(self, project, scene, chain):
    QtGui.QGraphicsTextItem.__init__(self)
    self.chain = chain
    self.text=chain.compoundName
    self.setHtml('<div style=><strong>'+chain.compoundName+': </strong></div>')
    self.setFont(Font(size=14, bold=True))
    self.setDefaultTextColor(QtGui.QColor('#f7ffff'))
    self.residueDict = {}
    i = 0
    for residue in chain.residues:
      newResidue = scene.addItem(GuiChainResidue(self, project, residue, scene, self.boundingRect().width(), i))
      self.residueDict[residue.sequenceCode] = newResidue
      i+=1

class GuiChainResidue(QtGui.QGraphicsTextItem):

  fontSize = 20

  def __init__(self, parent, project, residue, scene, labelPosition, index):

    QtGui.QGraphicsTextItem.__init__(self)
    self.setPlainText(residue.shortName)
    position = labelPosition+(20*index)
    self.setFont(Font(size=GuiChainResidue.fontSize, normal=True))
    self.setDefaultTextColor(QtGui.QColor('#f7ffff'))
    self.setPos(QtCore.QPointF(position, 0))
    self.residueNumber = residue.sequenceCode
    if residue.nmrResidue is not None:
      self.setHtml('<div style="color: #04C317; text-align: center;"><strong>'+residue.shortName+'</strong></div>')
    else:
      self.setHtml('<div style:"text-align: center;">'+residue.shortName+'</div')
    self.project = project
    self.residue = residue
    self.setAcceptDrops(True)
    scene.dragLeaveEvent = self.dragLeaveEvent
    scene.dragEnterEvent = self.dragEnterEvent
    # scene.dropEvent = self.dropEvent
    self.scene = scene
    self.setFlags(QtGui.QGraphicsItem.ItemIsSelectable | self.flags())
    self.parent=parent


  def setFontBold(self):
    format = QtGui.QTextCharFormat()
    format.setFontWeight(75)
    self.textCursor().mergeCharFormat(format)




  def dragEnterEvent(self, event):

    item = self.scene.itemAt(event.scenePos())
    if isinstance(item, GuiChainResidue):
      print(item.residueNumber)

      item.setDefaultTextColor(QtGui.QColor('#e4e15b'))
    event.accept()

  def dragLeaveEvent(self, event):
    item = self.scene.itemAt(event.scenePos())
    if isinstance(item, GuiChainResidue):
      item.setDefaultTextColor(QtGui.QColor('#f7ffff'))
    event.accept()


  # def hoverEnterEvent(self, event):
  #   # self.setDefaultTextColor(QtGui.QColor('#e4e15b'))
  #   self.setHtml('<div style="color: #e4e15b;">'+self.residue.shortName+'</div>')
  #
  # def hoverLeaveEvent(self, event):
  #   if hasattr(self.residue, 'nmrResidue'):
  #     if self.residue.nmrResidue is not None:
  #       self.setFont(Font(size=14, bold=True))
  #       self.setHtml('<div style="color: #04C317;"><strong>'+self.residue.shortName+'<strong></div>')
  #     else:
  #       self.setFont(Font(size=14, normal=True))
  #       self.setHtml('<div style="color: #f7ffff;">'+self.residue.shortName+'</div>')
  #   else:
  #     self.setHtml('<div style="color: #f7ffff;">'+self.residue.shortName+'</div>')
  #     self.setFont(Font(size=14, normal=True))

  # def dropEvent(self, event):
  #   res = self.scene.itemAt(event.scenePos())
  #   event.accept()
  #   if event.mimeData().hasFormat('application/x-assignedStretch'):
  #     data = event.mimeData().data('application/x-assignedStretch')
  #     nmrResidues = str(data, encoding='utf-8').split(',')
  #     nmrResidue = self.project.getById(nmrResidues[0])
  #     res.setHtml('<div style="color: #04C317; text-align: center;"><strong>'+
  #                 res.residue.shortName+'</strong></div>')
  #     nmrResidue.residue = res.residue
  #     res = res.residue
  #     print(nmrResidues,'nmrResidues')
  #     for assignableResidue in nmrResidues[1:]:
  #       res = res.nextResidue
  #       print('res')
  #       guiResidue = self.parent.residueDict.get(res.sequenceCode)
  #       guiResidue.setHtml('<div style="color: #04C317; text-align: center;"><strong>'+
  #                          res.shortName+'</strong></div>')
  #       nmrResidue = self.project.getById(assignableResidue)
  #       print(nmrResidue, 'before')
  #       nmrResidue.residue = res
  #       print(nmrResidue, 'after')






