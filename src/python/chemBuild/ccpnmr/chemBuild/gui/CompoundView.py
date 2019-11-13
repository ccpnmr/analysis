from math import cos, sin, atan2, sqrt
PI = 3.1415926535898

from os import path

from PyQt5 import QtCore, QtGui, QtWidgets
Qt = QtCore.Qt
QPointF = QtCore.QPointF
QRectF = QtCore.QRectF
from  PyQt5.QtWidgets import QGraphicsView, QGraphicsScene
from ccpnmr.chemBuild.model.Variant import Variant
from ccpnmr.chemBuild.model.VarAtom import VarAtom
from ccpnmr.chemBuild.model.Atom import Atom
from ccpnmr.chemBuild.model.Bond import Bond
from ccpnmr.chemBuild.model.Compound import loadCompoundPickle

from ccpnmr.chemBuild.gui.GraphicsItems import SelectionBox, AtomLabel, AtomItem, BondItem
from ccpnmr.chemBuild.gui.GraphicsItems import AromaticItem, EquivItem, ProchiralItem

from ccpnmr.chemBuild.general.Constants import LINK, MIMETYPE, MIMETYPE_ELEMENT, MIMETYPE_COMPOUND
from ccpnmr.chemBuild.general.Constants import ATOM_NAME_FG, ELEMENT_FONT
from ccpnmr.chemBuild.general.Constants import AROMATIC, EQUIVALENT, PROCHIRAL
    
class CompoundView(QGraphicsView):

  def __init__(self, parent=None, variant=None):

    super(CompoundView, self).__init__()
    self.scene = QGraphicsScene(self)
    self.scene.setSceneRect(0, 0, 300, 300)
    self.setScene(self.scene)
    self.setCacheMode(QGraphicsView.CacheBackground)

    self.parent = parent
    self.rotatePos = None
    if variant:
      self.compound = variant.compound
    else:
      self.compound = None
    
    self.dustbin = set()  
    self.variant = variant
    self.atomViews = {}
    self.selectedViews = set()
    self.bondItems = {}
    self.groupItems = {}
    self.update()
    self.nameAtoms = True
    self.showChargeSymbols = True
    self.showChiralities = True
    self.showStats = False
    self.showGroups = False
    self.menuAtomView = None
    self.menuAtom = None
    self.movePos = None
    self.zoomLevel = 1.0
    # Context menu
        
    self.needMenuAtom = []
    self.needSelectedAtom = []
    self.needFurtherCheck = []
    self.contextMenu = self.setupContextMenu()
  
    self.setMinimumSize(500,300)
    self.setRenderHint(QtGui.QPainter.Antialiasing)
    #self.setCacheMode(QtWidgets.QGraphicsView.CacheBackground)
    #self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)
    #self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
    self.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)
    self.setInteractive(True)

    self.scene = QtWidgets.QGraphicsScene(self)
    #self.setSceneRect(self.viewport().rect())
    self.setScene(self.scene)

    self.selectionBox = SelectionBox(self.scene, self)
    self.scene.addItem(self.selectionBox)

    self.editAtom = None
    self.editWidget = QtWidgets.QLineEdit()
    self.editWidget.setMaxLength(8)
    self.editWidget.resize(50, 30)

    effect = QtWidgets.QGraphicsDropShadowEffect(self)
    effect.setBlurRadius(3)
    effect.setOffset(2,2)
    
    #self.editWidget.setGraphicsEffect(effect)
    self.editWidget.returnPressed.connect(self.setAtomName)
    self.editWidget.hide()
    self.editProxy = self.scene.addWidget(self.editWidget)
    self.editProxy.setZValue(2)
    
    self.backgroundColor = Qt.darkGray
    
    self.setBackgroundBrush(self.backgroundColor)

    # TODO: Add settings for this
    self.showSkeletalFormula = False
    self.showSkeletalFormulaColor =  False
    self.snapToGrid = False

    self.autoChirality = True

    self.addGraphicsItems()
    
    if self.variant and self.showSkeletalFormula:
      self.variant.snapAtomsToGrid(50.0)
      self.updateAll()

    self.show()

  def resizeEvent(self, event):
    
    #self.setSceneRect(self.viewport().rect())
    
    return QtWidgets.QGraphicsView.resizeEvent(self, event)
    
  def dragEnterEvent(self, event):
    
    if event.mimeData().hasFormat(MIMETYPE_ELEMENT):
      #if event.source() == self: # Should not exist
      #  event.setDropAction(QtCore.Qt.MoveAction)
      #  event.accept()
      event.acceptProposedAction()
   
    elif event.mimeData().hasFormat(MIMETYPE_COMPOUND):
      event.acceptProposedAction()

    elif event.mimeData().urls():
      event.acceptProposedAction()
        
    else:
      event.ignore()

  def dragMoveEvent(self, event):
    
    self.dragEnterEvent(event)

  def dragLeaveEvent(self, event):
  
    event.ignore()
    
  def dropEvent(self, event):
    
    if event.mimeData().hasFormat(MIMETYPE_ELEMENT):
      element = event.mimeData().text()
      
      pos = self.mapToScene(event.pos())
      x = pos.x() - 9
      y = pos.y() - 9
      
      atom = Atom(self.compound, element, None)
      
      VarAtom(None, atom, coords=(x, y, 0.0))
      
      self.updateAll()      
      
      event.acceptProposedAction()
   
    elif event.mimeData().hasFormat(MIMETYPE_COMPOUND):
      filePath = event.mimeData().text()
      compound = loadCompoundPickle(filePath)
      self.parent.addCompound(compound)       
      event.acceptProposedAction()
 
    elif event.mimeData().urls():
      mods = event.keyboardModifiers()
      haveCtrl = mods & QtCore.Qt.ControlModifier
      haveShift = mods & QtCore.Qt.ShiftModifier
      
      if haveShift or haveCtrl:
        haveModKey = True
      else:
        haveModKey = False  
      
      filePaths = [url.path() for url in event.mimeData().urls() if path.isfile(url.path())]
      
      if filePaths:
        for filePath in filePaths:
          self.parent.importCompoundFile(filePath, haveModKey)
          haveModKey = True # Never replace the new ones
          
        event.acceptProposedAction()   
          
      else:
        event.ignore()
        
    else:
      event.ignore()
        
  def setAtomName(self):
    
    atom = self.editAtom
    
    if not atom:
      return
    
    text = self.editWidget.text().strip()

    if text and (text != atom.name):
      self.parent.addToHistory()
      used = set([a.name for a in atom.compound.atoms])
      if text in used:
        msg = 'Name "%s" was already in use: the other atom name as been modified' % text
        QtWidgets.QMessageBox.warning(self, "Warning", msg)
        prevAtom = self.compound.atomDict[text]
        name2 = text + '!'
        while name2 in used:
          name2 = name2 + '!'
        prevAtom.setName(name2)  
        atom.setName(text) 
        
      else:
        atom.setName(text) 
      
      self.parent.updateVars()
    
    self.editAtom = None
    self.editWidget.hide()
    self.updateAll()
  
  def queryAtomName(self, atomLabel):
    
    self.editAtom = atom = atomLabel.atom
    
    self.editWidget.setText(atom.name or atom.element)
    self.editWidget.setVisible(True)
    
    center = QtCore.QPointF(self.editWidget.rect().center())
    pos = atomLabel.pos() - center
    self.editProxy.setPos(pos)    
  
  def drawForeground(self, painter, viewRect):
  
    QtWidgets.QGraphicsView.drawForeground(self, painter, viewRect)
    
    #painter.setPen(QtGui.QColor(80, 0, 0, 128))
    #painter.setBrush(QtGui.QColor(80, 0, 0, 128))
    #painter.drawRect(viewRect)

  def drawBackground(self, painter, viewRect):
    
    transform = painter.transform()
    scale = float(transform.m11())
    unScale = 1.0/scale
    
    QtWidgets.QGraphicsView.drawBackground(self, painter, viewRect)

    # Text
    
    pad = 4.0
    qPoint = QtCore.QPointF
    qRectF = QtCore.QRectF
    painter.setPen(ATOM_NAME_FG)
    painter.setFont(QtGui.QFont("DejaVu Sans Mono", 9) )
    painter.scale(unScale, unScale)
    fontMetric = QtGui.QFontMetricsF(painter.font())

    tl = viewRect.topLeft()
    x0 = tl.x() * scale
    y0 = tl.y() * scale
    y1 = y0 + viewRect.height() * scale
    
    text = self.parent.compoundFileName
    if text:
      bbox = fontMetric.boundingRect(text)
      w = bbox.width()
      h = bbox.height()
      painter.drawText(qPoint(x0+pad, y1-pad), text)
    if self.compound:
      text = self.compound.name
    if text:
      bbox = fontMetric.boundingRect(text)
      h = bbox.height()
      painter.drawText(qPoint(x0+pad, y0+h), text)
          
    if self.showStats:
      text = self.getStats()
      rect = qRectF(x0+pad, y0+h+pad, self.width(), self.height()-h-pad)
      painter.drawText(rect, Qt.AlignLeft | Qt.AlignTop, text)
    
  def resetView(self):
    
    self.resetCachedContent()
    self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)
  
  def setupContextMenu(self):
    
    QAction = QtWidgets.QAction
    
    menu = QtWidgets.QMenu(self)
    
    action = QAction('Reset View', self, triggered=self.resetView)
    menu.addAction(action)
    
    subMenu = menu.addMenu('Residue Links')
    action = QAction('Linear polymer: next', self, triggered=self.addNextLink)
    subMenu.addAction(action)  
    self.needFurtherCheck.append( (action, self.getMenuLinkAtoms) )
    action = QAction('Linear polymer: previous', self, triggered=self.addPrevLink)
    subMenu.addAction(action)  
    self.needFurtherCheck.append( (action, self.getMenuLinkAtoms) )
    action = QAction('Generic link', self, triggered=self.addGenLink)
    subMenu.addAction(action)  
    self.needFurtherCheck.append( (action, self.getMenuLinkAtoms) )
    
    # ? invariable atom                       
    subMenu = menu.addMenu('Exchange')
    action = QAction('Variable atom', self, triggered=self.setVariableAtom)
    subMenu.addAction(action)  
    self.needFurtherCheck.append( (action, self.getVariableMenuAtom) )
    action = QAction('Fast H exchange', self, triggered=self.setExchangeAtom)
    subMenu.addAction(action)  
    self.needFurtherCheck.append( (action, self.getExchangeMenuAtom) )
    action = QAction('Slow or no exchange', self, triggered=self.setNoExchangeAtom)
    subMenu.addAction(action)
    self.needFurtherCheck.append( (action, self.getVariableMenuAtom) )
      
    subMenu = menu.addMenu('Charge')
    action = QAction('Add positive', self, triggered=self.addPosChargeAtom)
    subMenu.addAction(action)  
    self.needFurtherCheck.append( (action, self.getChargeMenuAtom) )
    action = QAction('Add negative', self, triggered=self.addNegChargeAtom)
    subMenu.addAction(action)  
    self.needFurtherCheck.append( (action, self.getChargeMenuAtom) )
    action = QAction('Set neutral', self, triggered=self.setNoChargeAtom)
    subMenu.addAction(action)
    self.needFurtherCheck.append( (action, self.getChargeMenuAtom) )
    
    subMenu = menu.addMenu('Stereochemistry')
    action = QAction('Toggle stereo centre', self, triggered=self.toggleStereoCentre)
    subMenu.addAction(action)  
    self.needFurtherCheck.append( (action, self.getStereoCentreAtom) )
    action = QAction('Move atom forward', self, triggered=self.moveAtomsForward)
    subMenu.addAction(action)  
    self.needFurtherCheck.append( (action, self.getStereoAtom) )
    action = QAction('Move atom backward', self, triggered=self.moveAtomsBackward)
    subMenu.addAction(action)  
    self.needFurtherCheck.append( (action, self.getStereoAtom) )
    
    subMenu = menu.addMenu('Chirality Label')
    action = QAction('R', self, triggered=self.setChiralityR)
    subMenu.addAction(action)  
    self.needFurtherCheck.append( (action, self.getChiralMenuAtom) )
    action = QAction('S', self, triggered=self.setChiralityS)
    subMenu.addAction(action)  
    self.needFurtherCheck.append( (action, self.getChiralMenuAtom) )
    action = QAction('alpha', self, triggered=self.setChiralityA)
    subMenu.addAction(action)  
    self.needFurtherCheck.append( (action, self.getChiralMenuAtom) )
    action = QAction('beta', self, triggered=self.setChiralityB)
    subMenu.addAction(action)  
    self.needFurtherCheck.append( (action, self.getChiralMenuAtom) )
    action = QAction('None or unspecified', self, triggered=self.setChiralityNone)
    subMenu.addAction(action)  
    self.needFurtherCheck.append( (action, self.getChiralMenuAtom) )

    subMenu = menu.addMenu('Aromaticity')
    action = QAction('Toggle', self, triggered=self.setAromaticity)
    subMenu.addAction(action)  
    self.needFurtherCheck.append( (action, self.getAromaticMenuAtom) )

    subMenu = menu.addMenu('NMR Groups')
    action = QAction('Magnetically equivalent', self, triggered=self.setEquivAtoms)
    subMenu.addAction(action)  
    self.needSelectedAtom.append(action)
    action = QAction('Prochiral pair', self, triggered=self.setProchiralAtoms)
    subMenu.addAction(action)  
    self.needSelectedAtom.append(action)
    action = QAction('No grouping', self, triggered=self.setNoGroupAtoms)
    subMenu.addAction(action)  
    self.needSelectedAtom.append(action)

    subMenu = menu.addMenu('Edit')
    action = QAction('Delete Atom', self, triggered=self.deleteAtom)
    subMenu.addAction(action)
    self.needMenuAtom.append(action)
    action = QAction('Delete Selected Atoms', self, triggered=self.deleteSelectedAtoms)
    subMenu.addAction(action)  
    self.needSelectedAtom.append(action)
    action = QAction('Delete Selected Bonds', self, triggered=self.deleteBonds)
    subMenu.addAction(action)  
    self.needSelectedAtom.append(action)
    action = QAction('Add Hydrogens', self, triggered=self.addHydrogens)
    subMenu.addAction(action)  
    action = QAction('Auto Bond', self, triggered=self.autoBond)
    subMenu.addAction(action)
    action = QAction('Auto Arrange', self, triggered=self.parent.minimise)
    subMenu.addAction(action)
  
    return menu

  def popupContextMenu(self, pos):
    
    menuAtomView = self.menuAtomView
    menuAtom = self.menuAtom
        
    if menuAtom:
      for action in self.needMenuAtom:
        action.setEnabled(True)
    else:
      for action in self.needMenuAtom:
        action.setEnabled(False)
   
    if self.selectedViews:
      for action in self.needSelectedAtom:
        action.setEnabled(True)
    
    else:
      for action in self.needSelectedAtom:
        action.setEnabled(False)
      
    for action, func in self.needFurtherCheck:
      action.setEnabled(bool(func()))
    
    self.contextMenu.popup(pos)


  def deleteAtom(self):
    
    if self.menuAtomView:
      self.parent.addToHistory()
      self.menuAtomView.delete()
      
      if not self.variant.varAtoms:
        variants = list(self.compound.variants)
        self.setVariant(variants[0])

      self.parent.updateVars()
      self.updateAll()
    
  def deleteSelectedAtoms(self):

    selectedViews = self.selectedViews
    
    n = len(selectedViews)
    
    if n:
      self.parent.addToHistory()
    
    if (n>1) and (n == len(list(self.atomViews.keys()))):
      if len(self.compound.variants) > 1:
        msg = 'Really delete all atoms? (Deletes only the current variant form)'
      else:
        msg = 'Really delete all atoms?'
        
      answ = QtWidgets.QMessageBox.warning(self, "Confirm", msg,
                                       QtWidgets.QMessageBox.Cancel |
                                       QtWidgets.QMessageBox.Ok)

      if answ == QtWidgets.QMessageBox.Cancel:
        return
      
      for atomView in list(self.atomViews.values()):
        atomView.delete()  
    
      self.variant.delete()
      if len(self.compound.variants) == 0 :
        self.setVariant(Variant(self.compound))
    
    else:
      for atomView in list(selectedViews):
        atomView.delete()  
    
    if n:
      if not self.variant.varAtoms:
        variants = list(self.compound.variants)
        self.setVariant(variants[0])
 
      self.selectedViews = set()
      self.parent.updateVars()
      self.updateAll()
    
    return n
    
  def deleteBonds(self):
  
    selectedViews = self.selectedViews
    
    n = len(selectedViews)
    
    if n:
      self.parent.addToHistory()
    
    if n == 1:
      atomView = list(selectedViews)[0]
      selectedBonds = atomView.atom.bonds
    else:
      atoms = set()
      bonds = set()
      selectedBonds = set()
      for atomView in selectedViews:
        atom = atomView.atom
        atoms.add(atom)
        bonds.update(atom.bonds)
    
      for bond in bonds:
        atomA, atomB = bond.varAtoms
        if (atomA in atoms) and (atomB in atoms):
          selectedBonds.add(bond)
    
    nBonds = len(selectedBonds)
    for bond in list(selectedBonds):
      bondItem = self.bondItems[bond]
      bondItem.delete()
    
    if n:
      self.updateAll()
      self.parent.updateVars()

    return nBonds
  
  
  def addHydrogens(self, atoms=None):
  
    if not atoms:
      if self.menuAtom:
        atoms = [self.menuAtom,]
      elif self.selectedViews:
        atoms = [v.atom for v in self.selectedViews]
      elif self.variant:
        atoms = list(self.variant.varAtoms)
    
    if not atoms:
      return 0
    
    compound = self.compound
    variant = self.variant
    if not variant:
      return 0
    
    self.parent.addToHistory()
    
    hydrogens = set()
    for atom in atoms:
      if atom.element == 'H':
        continue
    
      newAtoms = []
      x, y, z = atom.coords
      
      for angle in list(atom.freeValences):
        x2 = x + 34.0 * sin(angle)
        y2 = y + 34.0 * cos(angle)
        
        masterAtom = Atom(compound, 'H', None)
        VarAtom(None, masterAtom, coords=(x2,y2, 0.0)) # All vars

        hydrogen = variant.atomDict[masterAtom]
        newAtoms.append(hydrogen)
        hydrogens.add(hydrogen)
    
      for varAtom in newAtoms:
        Bond((atom, varAtom), autoVar=True)
    
    if hydrogens:  
      variant.minimise2d(hydrogens, 10)
      self.updateAll()
      #self.parent.updateVars()
    
    return hydrogens
  
  def autoBond(self):
     
    nonSelf = set(['H','Cl','Br','I','F'])
    
    importance = {frozenset(['C','C']):1.5,
                  frozenset(['C','O']):1.3,
                  frozenset(['P','O']):1.3,
                  frozenset(['C','N']):1.4,
                  frozenset(['C','H']):1.2,
                  frozenset(['N','H']):1.28,
                  frozenset(['O','H']):1.25,
                  frozenset(['N','N']):0.7,
                  frozenset(['O','O']):0.5,
                  }
  
    newBonds = []
    variant = self.variant
    if variant:
      atoms = [v.atom for v in self.selectedViews]
    
      if len(atoms) < 2:
        atoms = variant.varAtoms
    
      freeAtoms = set()
      for atom in atoms:
        if atom.freeValences:
          freeAtoms.add(atom)
       
      if len(freeAtoms) < 2:
        return 0

  
      nearNeighbours = {}
      for atom in freeAtoms:
        local = set(atom.neighbours)
        for atom1 in atom.neighbours:
          local.update(atom1.neighbours)
          for atom2 in atom1.neighbours:
            local.update(atom2.neighbours)
        
        nearNeighbours[atom] = local
  
      distList = []
      origDists = []
      freeAtoms = list(freeAtoms)
      for i, atomA in enumerate(freeAtoms[:-1]):
        x1, y1, z1 = atomA.coords
        elemA = atomA.element
        local = nearNeighbours[atomA]
        
        for atomB in freeAtoms[i+1:]:
          if atomB in local:
            continue
          
          elemB = atomB.element

          if elemB == elemA:
            if elemA in nonSelf:
              continue
        
          x2, y2, z2 = atomB.coords
          
          dx = x1-x2
          dy = y1-y2
          dz = z1-z2
          
          d = (dx*dx) + (dy*dy) + (dz*dz)
          
          elems = frozenset([elemA, elemB])
          
          d2 = d / importance.get(elems, 1.0)
           
          distList.append((d2, d, set([atomA, atomB])))
          origDists.append(d)
      
      if not distList:
        return 0
       
      self.parent.addToHistory()
      done = set()
      distList.sort()
      origDists.sort()
      threshold = origDists[0] * 1.5
      
      while distList:
        d2, d, atoms = distList.pop(0)
        atomA, atomB = atoms
        
        if d > threshold:
          break
        
        if atoms & done:
          continue
        
        if atomA in nearNeighbours[atomB]:
          continue
          
        if atomB in nearNeighbours[atomA]:
          continue
        
        newBonds.append( Bond((atomA, atomB)) )
        
        nearNeighbours[atomA].add(atomB)
        nearNeighbours[atomB].add(atomA)
        
        nearNeighbours[atomA].update(nearNeighbours[atomB])
        nearNeighbours[atomB].update(nearNeighbours[atomA])
        
        if not atomA.freeValences:
          done.add(atomA) 
 
        if not atomB.freeValences:
          done.add(atomB) 
      
      
    n = len(newBonds)
        
    if n:
      for atom in freeAtoms:
        atom.updateValences()
        
      self.updateAll()
      self.parent.updateVars()
  
    return n
  
  def setEquivAtoms(self):
    
    atoms = [v.atom for v in self.selectedViews]
  
    if atoms:
      self.parent.addToHistory()
      self.compound.setAtomsEquivalent(atoms)
      self.updateAll()
      self.parent.updateVars()
    
  def setProchiralAtoms(self):
    
    varAtoms = [v.atom for v in self.selectedViews]

    if varAtoms:
      self.parent.addToHistory()
      atoms = [va.atom for va in varAtoms]
      self.compound.setAtomsProchiral(atoms)
      self.updateAll()
      self.parent.updateVars()

  def setNoGroupAtoms(self):
    
    varAtoms = [v.atom for v in self.selectedViews]
      
    if varAtoms:
      self.parent.addToHistory()
      atoms = [va.atom for va in varAtoms]
      self.compound.unsetAtomsProchiral(atoms)
      self.compound.unsetAtomsEquivalent(atoms)
      item = self.groupItems.get(frozenset(atoms))
      if item:
        del item
      
      self.updateAll()
      self.parent.updateVars()
  
  def getMenuAtom(self, posFilter=None, negFilter=None):
   
    if self.variant and self.menuAtom:
      elem = self.menuAtom.element
    
      if posFilter is None:
        if negFilter is None:
          return self.menuAtom
        elif elem not in negFilter:
          return self.menuAtom 
      
      elif elem in posFilter:
        if negFilter is None:
          return self.menuAtom
        elif elem not in negFilter:
          return self.menuAtom 
  
  def getAromaticMenuAtom(self):
  
    return self.getMenuAtom(('C','N','O','S'),)

  def getChiralMenuAtom(self):
  
    return self.getMenuAtom(('C','N','Si','P','As','Al'),)

  def getChargeMenuAtom(self):
  
    return self.getMenuAtom(None, ('H',LINK))

  def getStereoCentreAtom(self):
    
    varAtom = self.getMenuAtom(None, ('H','O','S','Se',LINK))
    
    if varAtom:
      return len(varAtom.neighbours) == 4
    
  def getStereoAtom(self):
    
    varAtom = self.getMenuAtom()
    
    if varAtom:
      for varAtom2 in varAtom.neighbours:
        if varAtom2.stereo:
          return True
    
    return False

  def getVariableMenuAtom(self):
  
    return self.getMenuAtom(('H','O',LINK))

  def getExchangeMenuAtom(self):
  
    return self.getMenuAtom(('H',))
  
  def setAromaticity(self):
  
    atom = self.getAromaticMenuAtom()
    
    if atom:
      self.parent.addToHistory()
      atom.toggleAromatic()
      self.updateAll()
        
  def setChiralityR(self):
    
    atom = self.getChiralMenuAtom()
    
    if atom:
      self.parent.addToHistory()
      atom.setChirality('R')
      self.atomViews[atom].update()
      self.parent.updateVars()
  
  def setChiralityS(self):
    
    atom = self.getChiralMenuAtom()
    
    if atom:
      self.parent.addToHistory()
      atom.setChirality('S')
      self.atomViews[atom].update()
      self.parent.updateVars()
  
  def setChiralityA(self):

    atom = self.getChiralMenuAtom()
    
    if atom:
      self.parent.addToHistory()
      atom.setChirality('a')
      self.atomViews[atom].update()
      self.parent.updateVars()
  
  def setChiralityB(self):

    atom = self.getChiralMenuAtom()
    
    if atom:
      self.parent.addToHistory()
      atom.setChirality('b')
      self.atomViews[atom].update()
      self.parent.updateVars()
  
  def setChiralityNone(self):
    
    atom = self.getChiralMenuAtom()
    
    if atom:
      self.parent.addToHistory()
      atom.setChirality(None)
      self.atomViews[atom].update()
      self.parent.updateVars()
      
  def autoSetChirality(self):
    
    for atom in self.variant.varAtoms:
      atom.autoSetChirality()
  
  def addPosChargeAtom(self):
  
    atom = self.getChargeMenuAtom()
   
    if atom:
      self.parent.addToHistory()
      charge = max(0, atom.charge) + 1
      atom.setCharge(charge)    
      self.atomViews[atom].update()
      self.parent.updateVars()
       
  
  def addNegChargeAtom(self):
  
    atom = self.getChargeMenuAtom()
   
    if atom:
      self.parent.addToHistory()
      charge = min(0, atom.charge) - 1
      atom.setCharge(charge)
      self.atomViews[atom].update()
      self.parent.updateVars()
  
  def setNoChargeAtom(self):
 
    atom = self.getChargeMenuAtom()
   
    if atom and atom.charge:
      self.parent.addToHistory()
      atom.setCharge(0)
      self.atomViews[atom].update()
      self.parent.updateVars()
  
  def toggleStereoCentre(self):
    
    atom = self.getMenuAtom()
   
    if atom:
      self.parent.addToHistory()
      self.parent.toggleStereoCentre([atom,])
      self.updateAll()
  
  def moveAtomsForward(self):
    
    atom = self.getMenuAtom()
   
    if atom:
      self.parent.addToHistory()
      self.parent.moveAtomsForward([atom,])
      self.updateAll()
  
  def moveAtomsBackward(self):
    
    atom = self.getMenuAtom()
   
    if atom:
      self.parent.addToHistory()
      self.parent.moveAtomsBackward([atom,])
      self.updateAll()
      
  def setVariableAtom(self):
  
    atom = self.getVariableMenuAtom()

    if atom:
      self.parent.addToHistory()
      atom.setLabile(False)
      atom.setVariable(True)
      self.atomViews[atom].update()
      self.parent.updateVars()
      
      if atom in self.variant.varAtoms:
        for var in self.compound.variants:
          if atom not in var.varAtoms:
            self.setVariant(var)
            break
  
  def setExchangeAtom(self):

    atom = self.getExchangeMenuAtom()
    
    if atom:
      self.parent.addToHistory()
      atom.setLabile(True)
      self.atomViews[atom].update()
      self.parent.updateVars()

  def setNoExchangeAtom(self):
    
    atom = self.getVariableMenuAtom()
    
    if atom:
      self.parent.addToHistory()
      atom.setLabile(False)
      atom.setVariable(False)
      self.atomViews[atom].update()
      self.parent.updateVars()

  def getMenuLinkAtoms(self):
     
    if self.variant and self.menuAtom:
      if self.menuAtom.element == 'H':
        atoms = [self.menuAtom,]
      
      elif self.menuAtom.element in ('O','S'):
        atoms = [self.menuAtom,]
        for atomB in self.menuAtom.neighbours:
          if atomB.element == 'H':
            atoms.append(atomB)
            break
            
        else:
          return
      
      else:
        return
      
      return atoms
      
  def addPrevLink(self):
     
    atoms = self.getMenuLinkAtoms()
        
    if atoms:  
      self.parent.addToHistory()
      self.addLink('prev', atoms)
  
  
  def addNextLink(self):
  
    atoms = self.getMenuLinkAtoms()
    
    if atoms:  
      self.parent.addToHistory()
      self.addLink('next', atoms)
  
  
  def addGenLink(self):
  
    atoms = self.getMenuLinkAtoms()
    
    if atoms:  
      self.parent.addToHistory()
      self.addLink(LINK, atoms)
  

  def addLink(self, name, atoms):
        
    if ('next' in name) and  self.variant.polyLink in ('middle', 'start'):
      msg = 'Cannot add another next residue link'
      QtWidgets.QMessageBox.warning(self, "Abort", msg)
      return
        
    elif ('prev' in name) and self.variant.polyLink in ('middle', 'end'):
      msg = 'Cannot add another previous residue link'
      QtWidgets.QMessageBox.warning(self, "Abort", msg)
      return
  
    self.parent.addToHistory()
    atom = self.variant.addLink(name, atoms)
      
    if not atom:
      msg = 'Could not make a link: require at least one hydrogen'
      QtWidgets.QMessageBox.warning(self, "Failure", msg)
      return
    
    self.setVariant(atom.variant)
    
    for view in list(self.selectedViews):
      view.deselect()
    
    self.atomViews[atom].select()
    self.updateAll()
    self.parent.updateVars()
    
    return atom

  def setVariant(self, variant):
    
    if variant is not self.variant:
      scene = self.scene
      
      self.atomViews = {}
      self.selectedViews = set()
      self.bondItems = {}
      self.groupItems = {}
      
      items = set(scene.items())
      items.remove(self.editProxy)
      items.remove(self.selectionBox)

      for item in items:
        item.hide()

      for item in items:
        del item

      self.resetCachedContent()
      self.variant = variant
      self.compound = variant.compound
      self.parent.variant = variant
      self.parent.compound = self.compound

      self.addGraphicsItems()
      self.centerView()

  def updateAll(self):

    var = self.variant
    scene = self.scene

    if var:
      getView = self.atomViews.get
      bondItems = self.bondItems
      getBondItem = bondItems.get
      groupDict = self.groupItems

      usedGroups = set(var.atomGroups)
      for group in usedGroups:
        if group in groupDict:
          groupDict[group].syncGroup()

        elif group.groupType == EQUIVALENT:
          EquivItem(scene, self, group)

        elif group.groupType == PROCHIRAL:
          ProchiralItem(scene, self, group)

        elif group.groupType == AROMATIC:
          AromaticItem(scene, self, group)

      zombieGroups = set(groupDict.keys()) - usedGroups
      for group in zombieGroups:
        groupItem = groupDict[group]
        del groupDict[group]
        del groupItem

      for atom in var.varAtoms:
        atomView = getView(atom)

        if atomView:
          atomView.syncToAtom()
        else:
          atomView = AtomItem(scene, self, atom)
          scene.addItem(atomView)

      zombieBonds = set(self.bondItems.keys()) - set(var.bonds)
      for bond in zombieBonds:
        bondItem =  bondItems[bond]
        del bondItems[bond]
        del bondItem
      
      for bond in var.bonds:
        bondItem = getBondItem(bond)
        
        if not bondItem:
          bondItem = BondItem(scene, self, bond)
          scene.addItem(bondItem)
       
      self.parent.updateVars()
    
  def addGraphicsItems(self):

    if not self.variant:
      return

    scene = self.scene

    # Draw groups

    for group in self.variant.atomGroups:
      if group.groupType == EQUIVALENT:
        EquivItem(scene, self, group)
      
      elif group.groupType == PROCHIRAL:
        ProchiralItem(scene, self, group)

      elif group.groupType == AROMATIC:
        AromaticItem(scene, self, group)
    
    # Draw atoms
    
    self.atomViews = {}
    for atom in self.variant.varAtoms:
      a = AtomItem(scene, self, atom)
      scene.addItem(a)

    # Draw bonds
    done = set()
    self.bondItems = bondDict = {}
    for bond in self.variant.bonds:
      atoms = frozenset(bond.varAtoms)
      if atoms in done:
        pass

      bondItem = BondItem(scene, self, bond)
      scene.addItem(bondItem)
      done.add(atoms)

 
  def centroid(self, views):
  
    x0 = 0.0
    y0 = 0.0
    n = 0.0

    for view in views:
      x1, y1, z1 = view.atom.coords
      x0 += x1
      y0 += y1
      n += 1.0
    
    x0 /= n
    y0 /= n
    
    return x0, y0 

  def centroidAtoms(self, atoms):
  
    x0 = 0.0
    y0 = 0.0
    n = 0.0

    for atom in atoms:
      x1, y1, z1 = atom.coords
      x0 += x1
      y0 += y1
      n += 1.0
    
    x0 /= n
    y0 /= n
    
    return x0, y0 

  def rotateLeft(self, angle=PI*5.0/180):
    
    selected = self.selectedViews or list(self.atomViews.values())
 
    if not selected:
      return
      
    x0, y0 = self.centroid(selected)
    self.rotateAtoms(x0, y0, angle)
    
  def rotateRight(self, angle=PI*5.0/180):
    
    selected = self.selectedViews or list(self.atomViews.values())
 
    if not selected:
      return
      
    x0, y0 = self.centroid(selected)
    self.rotateAtoms(x0, y0, -angle)

  def rotateAtoms(self, x0, y0, deltaAngle):

    atoms = [v.atom for v in self.selectedViews]
    
    if atoms:
      for atom in atoms:
        x, y, z = atom.coords
        dx = x-x0
        dy = y-y0
        r = sqrt(dx*dx+dy*dy)
        angle2 = atan2(dx, dy) + deltaAngle

        x = x0+r*sin(angle2)
        y = y0+r*cos(angle2)
        atom.setCoords(x, y, z)

      for atom in atoms:
        atom.updateValences()

    elif self.compound:
      for atom in self.compound.atoms:
        for varAtom in atom.varAtoms:
          x, y, z = varAtom.coords
          dx = x-x0
          dy = y-y0
          r = sqrt(dx*dx+dy*dy)
          angle2 = atan2(dx, dy) + deltaAngle

          x = x0+r*sin(angle2)
          y = y0+r*cos(angle2)
          varAtom.coords = (x, y, z)

      for atom in self.compound.atoms:
        for varAtom in atom.varAtoms:
          varAtom.updateValences()
    
    self.updateAll()
  
  def centerView(self):
    
    if self.variant:
      x, y, z = self.variant.getCentroid()
    
    else:
      x, y = 0, 0
      
    self.ensureVisible(x-50,y-50,100,100)
  
  def resetZoom(self):
  
    fac = 1.0 / self.zoomLevel
    self.scale(fac, fac)
    self.zoomLevel = 1.0
  
  def wheelEvent(self, event):
    
    if event.angleDelta().y() < 0:
      fac = 0.8333
    else:
      fac = 1.2
    
    newLevel = self.zoomLevel * fac
    
    if 0.5 < newLevel < 5.0:
      self.zoomLevel = newLevel
      self.scale(fac, fac)
  
    event.accept()
  
  def mousePressEvent(self, event):
   
    QtWidgets.QGraphicsView.mousePressEvent(self, event)
    
    button = event.button()
    pos = event.pos()
    mods = event.modifiers()
    haveCtrl = mods & Qt.CTRL
    haveShift = mods & Qt.SHIFT
    
    bondItem = None
    item = self.itemAt(pos)
    if item and isinstance(item, AtomItem):
      self.menuAtomView = item
      self.menuAtom = item.atom
    elif item and isinstance(item, AtomLabel):
      self.menuAtomView = item.atomView
      self.menuAtom = item.atom
    elif item and isinstance(item, BondItem):
      self.menuAtomView = None
      self.menuAtom = None
      if item.getDistToBond(self.mapToScene(pos)) <= 8:
        bondItem = item
    elif item and isinstance(item, AromaticItem):
      self.menuAtomView = None
      self.menuAtom = None
      bondItem = item
    else:
      self.menuAtomView = None
      self.menuAtom = None 
    
    # deal with inconsistency in Qt versions for button naming
    try:
      MiddleButton = Qt.MiddleButton
    except AttributeError:
      MiddleButton = Qt.MidButton
    
    if button == Qt.LeftButton:
      
      if not self.menuAtom:
        self.selectionBox.updateRegion(begin=self.mapToScene(pos))
        
        if not (bondItem or haveCtrl or haveShift):
          for view in list(self.selectedViews):
            view.deselect()
    
    elif button == MiddleButton:
      if (haveCtrl or haveShift):
        selected = self.selectedViews or list(self.atomViews.values())
 
        if len(selected) > 1:
          spos = self.mapToScene(pos)
          x0, y0 = self.centroid(selected)
          startAngle = atan2(spos.x()-x0, spos.y()-y0)
          self.rotatePos = (startAngle, (x0, y0))
      
      else:
        pos = event.pos()
        h = self.horizontalScrollBar().sliderPosition()
        v = self.verticalScrollBar().sliderPosition()
        self.movePos = pos.x()+h, pos.y()+v
      
    elif button == Qt.RightButton:
      self.popupContextMenu(event.globalPos())
    
    for atomView in self.selectedViews:
      atomView.setSelected(True)
    
    if item is not self.editProxy:
      self.setAtomName()

  def mouseMoveEvent(self, event):
      
    pos = event.pos()
    
    self.menuAtomView = None  
    self.menuAtom = None
 
    if self.movePos:
      x0, y0 = self.movePos
      pos = event.pos()
      self.horizontalScrollBar().setSliderPosition(x0-pos.x())
      self.verticalScrollBar().setSliderPosition(y0-pos.y())
    
    elif self.rotatePos:
      startAngle, center = self.rotatePos
      x0, y0 = center
      spos = self.mapToScene(pos)
      dx = spos.x() - x0
      dy = spos.y() - y0
      angle = atan2(dx, dy)
      deltaAngle = angle - startAngle

      self.rotateAtoms(x0, y0, deltaAngle)
      self.rotatePos = (angle, center)
      self.update()
    
    else:
      self.selectionBox.updateRegion(end=self.mapToScene(pos))
    
    QtWidgets.QGraphicsView.mouseMoveEvent(self, event)

  def mouseReleaseEvent(self, event):
 
    if self.selectionBox.region:
      posA = self.selectionBox.region.topLeft()
      posB = self.selectionBox.region.bottomRight()
      
      if posA != posB:
        xs = [posA.x(), posB.x()]
        ys = [posA.y(), posB.y()]
        xs.sort()
        ys.sort()
        x1, x2 = xs
        y1, y2 = ys
 
        for atomView in list(self.atomViews.values()):
          pos = atomView.pos()
          x = pos.x()
          y = pos.y()
 
          if (x1 < x < x2) and (y1 < y < y2):
            atomView.select()
 
    self.selectionBox.updateRegion()
    self.rotatePos = None
    self.movePos = None
    self.update()
    
    QtWidgets.QGraphicsView.mouseReleaseEvent(self, event)

  def getStats(self):
    
    stats = []
    variant = self.variant
    
    if variant:
      atoms = list(variant.varAtoms)
      groups = variant.atomGroups
     
      # Molecular formula

      formula = variant.getMolFormula()
      stats.append('Molecular formula: %s' % formula)
      
      # Common iso mass

      mass = variant.getCommonIsoMass()
      stats.append('Common isotopic mass: %.6f' % mass)
      
      # Vars
      
      proton, link, stereo = variant.descriptor
      
      stats.append('Number of variants: %d' % len(variant.compound.variants))
      stats.append(' ')
      stats.append('Variant information:')
      
      stats.append('Protonation state: %s' % proton)
      stats.append('Polymer linking: %s' % (variant.polyLink or 'none'))
      stats.append('Non-polymer links: %s' % link)
      stats.append('Stereo label: %s' % stereo)
      
      
      # Charges
      
      charges = [a.charge for a in atoms]
      
      charge = sum(charges)
      if charge > 0:
        charge = '+%s' % charge
      else:
        charge = str(charge)
      
      numNeg = len([x for x in charges if x < 0])
      numPos = len([x for x in charges if x > 0])
      
      stats.append('Overall charge: %s' % charge)
      stats.append('Positive charges: %d' % numPos)
      stats.append('Negative charges: %d' % numNeg)
      
      # Streo centres
      
      chiralAtoms = [a for a in atoms if a.stereo]
      stats.append('Stereo centres: %d' % len(chiralAtoms))
      
      
      # Prochirals
      
      prochiralGroups = [g for g in groups if g.groupType == PROCHIRAL]
      stats.append('Prochiral pairs: %d' % len(prochiralGroups))
      
      
      # Equivalence
      
      equivalentGroups = [g for g in groups if g.groupType == EQUIVALENT]
      stats.append('NMR Equivalency groups: %d' % len(equivalentGroups))
      
      
      # Labile atoms
      
      labile = [a.name or '?' for a in atoms if a.isLabile]
      labile.sort()

      labile = ' '.join(labile)
      stats.append('Fast exchanging atoms: %s' % labile)

      #stats.append('')
      
      
    return '\n'.join(stats)
    
