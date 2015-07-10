__author__ = 'simon1'


from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.Label import Label
from ccpncore.gui.ScrollArea import ScrollArea
from ccpncore.gui.Font import Font
from PyQt4 import QtCore, QtGui
import math

class SequenceModule(CcpnDock):

  def __init__(self, name=None, project=None):
    CcpnDock.__init__(self, name='Sequence')
    self.project=project
    self.setStyleSheet("""
    QWidget { background-color: #000021;
              border: 1px solid #00092d;
    }
    """)
    self.label.hide()
    # self.label = DockLabel('Assigner', self)
    # self.label.show()
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
    # #
    # def dragMoveEvent(self, event):
    #   event.accept()

  # def dropEvent(self, event):
  #   print(event)
    # print(self.itemAtPos(event.pos()))

    # scrollArea = ScrollArea(None)
    # self.addWidget(scrollArea, 0, 0)
    #
    # widget = QtGui.QWidget(self)
    # self.scrollArea = QtGui.QScrollArea()
    # self.scrollArea.setWidgetResizable(True)
    # self.scene = QtGui.QGraphicsScene(self)
    # self.scrollContents = QtGui.QGraphicsView(self.scene, self)
    # self.scrollContents.setInteractive(True)
    # self.horizontalLayout = QtGui.QHBoxLayout(self.scrollContents)
    # self.layout.addWidget(self.scrollArea)
    # for chain in project.chains:
    #     chainLabel = GuiChainLabel(self.scene, chain)
    # #   sequenceToShow = ''.join(self.getSpacedSequence(chain))
    # #   self.chainLabel = ChainLabel(widget, chain.compoundName+': '+sequenceToShow, grid=(0, 0), dragDrop=True)
    # #   self.chainLabel.dropEvent = self.dropEvent
    # #   self.chainLabel.chainCode = chain.compoundName
    # #   # self.chainLabel.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
    #
    #
    # scrollArea.setWidget(widget)
    # self.hideTitleBar()
    # # print(scrollArea.minimumSizeHint())
    # self.setMinimumHeight(30)
    # # scrollArea.setWidget(sequence1)

  def addChainLabel(self, chain):
    chainLabel = GuiChainLabel(self.project, self.scrollArea.scene, chain)
    self.scrollArea.scene.addItem(chainLabel)


  def getSpacedSequence(self, chain):
    residues = [residue.shortName for residue in chain.residues]
    for i in range(len(residues)):
      if i % 10 == 0 and i !=0:
        residues.insert(int(i+i/10)-1, ' ')

    return residues

  # def dropEvent(self, event):
  #   if event.mimeData().hasFormat('application/x-assignedStretch'):
  #     data = event.mimeData().data('application/x-assignedStretch')
  #     residues = str(data, encoding='utf-8').split(',')
  #     print(residues)
  #     print(event.pos())
  #     print(self.itemAtPos(event.pos()))


class ChainLabel(Label):

  def __init__(self, parent, text, **kw):
    Label.__init__(self, parent, text, **kw)
    # self.setMouseTracking(1)
    self.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
  #
  # def hoverEvent(self, event):
  #   print('hovering')

  # def mouseMoveEvent(self, event):
  #       print("on Hover")
  #       event.pos().x(), event.pos().y()



class GuiChainLabel(QtGui.QGraphicsTextItem):

  def __init__(self, project, scene, chain):
    QtGui.QGraphicsTextItem.__init__(self)
    self.chain = chain
    # print(self.chain.residues)
    self.text=chain.compoundName
    # self.setPos(QtCore.QPointF(0, 0))
    self.setPlainText(chain.compoundName)
    self.setFont(Font(size=12, bold=True))
    self.setDefaultTextColor(QtGui.QColor('#f7ffff'))
    self.residueDict = {}
    i = 0
    for residue in chain.residues:
      newResidue = scene.addItem(GuiChainResidue(self, project, residue, scene, self.boundingRect().width(), i))
      self.residueDict[residue.sequenceCode] = newResidue
      i+=1

class GuiChainResidue(QtGui.QGraphicsTextItem):

  def __init__(self, parent, project, residue, scene, labelPosition, index):

    QtGui.QGraphicsTextItem.__init__(self)
    self.setPlainText(residue.shortName)
    position = labelPosition+(10*index)
    self.setFont(Font(size=12, normal=True))
    self.setDefaultTextColor(QtGui.QColor('#f7ffff'))
    self.setPos(QtCore.QPointF(position, 0))
    self.residueNumber = residue.sequenceCode
    if residue.nmrResidue is not None:
      self.setHtml('<div style="background-color: red;"><strong>'+residue.shortName+'</strong></div>')
    else:
      self.setPlainText(residue.shortName)
    self.project = project
    self.residue = residue
    self.setAcceptDrops(True)
    # scene.dragMoveEvent = self.dragMoveEvent
    scene.dragLeaveEvent = self.dragLeaveEvent
    scene.dragEnterEvent = self.dragEnterEvent
    scene.dropEvent = self.dropEvent
    self.scene = scene
    self.setFlags(QtGui.QGraphicsItem.ItemIsSelectable | self.flags())
    self.parent=parent
    # self.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)


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
      print(item.residueNumber)
      item.setDefaultTextColor(QtGui.QColor('#f7ffff'))
    event.accept()


  # def dragLeaveEvent(self, event):
  #   event.accept()
  #   self.setDefaultTextColor(QtGui.QColor('#f7ffff'))
    # print('here222')
    # print(self.residue.name)
    # print(self.residue.sequenceCode)
    # if event.mimeData().hasFormat('application/x-assignedStretch'):
    #     data = event.mimeData().data('application/x-assignedStretch')
    #     residues = str(data, encoding='utf-8').split(',')
    #     self.project.getById(residues[0])
    #     for residue in residues:
    #       print(residue)
    #       print(self.project.getById(residue))

  #
  # def dragMoveEvent(self, event):
  #   event.accept()
    # pass
  def hoverEnterEvent(self, event):
    self.setDefaultTextColor(QtGui.QColor('#e4e15b'))


  def hoverLeaveEvent(self, event):
    if hasattr(self.residue, 'nmrResidue'):
      self.setFont(Font(size=12, bold=True))
      self.setDefaultTextColor(QtGui.QColor('#f7ffff'))
    else:
      self.setDefaultTextColor(QtGui.QColor('#f7ffff'))
      self.setFont(Font(size=12, normal=True))

  def dropEvent(self, event):
    res = self.scene.itemAt(event.scenePos())
    event.accept()
    # self.setDefaultTextColor(QtGui.QColor('#e4e15b'))
    if event.mimeData().hasFormat('application/x-assignedStretch'):
      data = event.mimeData().data('application/x-assignedStretch')
      nmrResidues = str(data, encoding='utf-8').split(',')
      # for datum in data:
      nmrResidue = self.project.getById(nmrResidues[0])
      # nmrResidue.name = res.residue.name
      res.setHtml('<div style="background-color: red;"><strong>'+res.residue.shortName+'</strong></div>')
      nmrResidue.residue = res.residue
      print(nmrResidue, 'after')
      print(self.residueNumber)
      res = res.residue
      for assignableResidue in nmrResidues[1:]:
        res = res.nextResidue
        guiResidue = self.parent.residueDict.get(res.sequenceCode)
        guiResidue.setHtml('<div style="background-color: red;"><strong>'+res.shortName+'</strong></div>')
        nmrResidue = self.project.getById(assignableResidue)
        nmrResidue.residue = res






