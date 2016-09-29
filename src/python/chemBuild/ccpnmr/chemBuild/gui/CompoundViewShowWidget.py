from math import cos, sin, atan2, sqrt
PI = 3.1415926535898

from os import path

from PyQt4 import QtCore, QtGui
Qt = QtCore.Qt
QPointF = QtCore.QPointF
QRectF = QtCore.QRectF

from ccpnmr.chemBuild.model.VarAtom import VarAtom
from ccpnmr.chemBuild.model.Atom import Atom
from ccpnmr.chemBuild.model.Bond import Bond
from ccpnmr.chemBuild.model.Compound import loadCompoundPickle

from ccpnmr.chemBuild.gui.CompoundView import CompoundView
from ccpnmr.chemBuild.gui.GraphicsItems import SelectionBox, AtomLabel, AtomItem, BondItem
from ccpnmr.chemBuild.gui.GraphicsItems import AromaticItem, EquivItem, ProchiralItem

from ccpnmr.chemBuild.general.Constants import LINK, DISALLOWED, MIMETYPE, MIMETYPE_ELEMENT, MIMETYPE_COMPOUND
from ccpnmr.chemBuild.general.Constants import HIGHLIGHT, HIGHLIGHT_BG, ATOM_NAME_FG, ELEMENT_FONT
from ccpnmr.chemBuild.general.Constants import AROMATIC, EQUIVALENT, PROCHIRAL
from ccpnmr.chemBuild.general.Constants import ELEMENT_FONT, ELEMENT_DATA,  ELEMENT_DEFAULT
from ccpnmr.chemBuild.general.Constants import CHARGE_FONT, NEG_COLOR, POS_COLOR
from ccpnmr.chemBuild.general.Constants import EQUIV_COLOR, PROCHIRAL_COLOR, CHARGE_BG_COLOR
from ccpnmr.chemBuild.general.Constants import CHIRAL_FONT, CHIRAL_COLOR

from memops.qtgui.Menu import Menu
from memops.qtgui.Colors import inverseGrey

RADIUS = 50.0

NULL_RECT = QRectF()
ItemIsMovable = QtGui.QGraphicsItem.ItemIsMovable
ItemIsSelectable = QtGui.QGraphicsItem.ItemIsSelectable
ItemPositionChange = QtGui.QGraphicsItem.ItemPositionChange
ItemSendsGeometryChanges = QtGui.QGraphicsItem.ItemSendsGeometryChanges

BOND_CHANGE_DICT = {'single':'double',
                    'aromatic':'double',
                    'singleplanar':'double',
                    'double':'triple',
                    'triple':'single',
                    'dative':'single'}


class AtomLabelShowWidget(AtomLabel):

  def hoverEnterEvent(self, event):
  
    event.ignore()

  def hoverLeaveEvent(self, event):
       
    event.ignore()
  
  def mouseDoubleClickEvent(self, event):
        
    event.ignore()
      
class EquivItemShowWidget(EquivItem):
  
  def paint(self, painter, option, widget):
    
    painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
    
    EquivItem.paint(self, painter, option, widget)
    
    painter.setRenderHint(QtGui.QPainter.Antialiasing, False)
    
class ProchiralItemShowWidget(ProchiralItem):
  
  def paint(self, painter, option, widget):
    
    painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
    
    ProchiralItem.paint(self, painter, option, widget)
    
    painter.setRenderHint(QtGui.QPainter.Antialiasing, False)
    
class AromaticItemShowWidget(AromaticItem):
  
  def paint(self, painter, option, widget):
    
    painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
    
    AromaticItem.paint(self, painter, option, widget)
    
    painter.setRenderHint(QtGui.QPainter.Antialiasing, False)
    
class AtomItemShowWidget(AtomItem):

  def __init__(self, scene, compoundView, atom):
    
    QtGui.QGraphicsItem.__init__(self, scene=scene)
    
    compoundView.atomViews[atom] = self
    
    self.compoundView = compoundView
    if compoundView.glWidget:
      self.glWidget = compoundView.glWidget
    else:
      self.glWidget = compoundView.container.parent
      
    self.variant = atom.variant
    self.atom = atom
    self.bondItems = []
    self.bbox = NULL_RECT

    self.setFlag(ItemIsSelectable)
    self.selected = False
    self.setFlag(ItemIsMovable)
    self.setFlag(ItemSendsGeometryChanges)
    self.setAcceptHoverEvents(True)
    self.setAcceptedMouseButtons(Qt.LeftButton)

    color = ELEMENT_DATA.get(atom.element,  ELEMENT_DEFAULT)[1]
    self.gradient = QtGui.QRadialGradient(0,0,9,4,-4)
    self.gradient.setColorAt(1, color.darker())
    self.gradient.setColorAt(0.5, color)
    self.gradient.setColorAt(0, color.lighter())
    self.gradient2 = QtGui.QRadialGradient(0,0,9,4,-4)
    self.gradient2.setColorAt(1, color.darker().darker())
    self.gradient2.setColorAt(0.5, color.darker())
    self.gradient2.setColorAt(0, color)
    #effect = QtGui.QGraphicsDropShadowEffect(compoundView)
    #effect.setBlurRadius(SHADOW_RADIUS)
    #effect.setColor(SHADOW_COLOR)
    #effect.setOffset(*SHADOW_OFFSET)
    
    #self.setGraphicsEffect(effect)
    self.setCacheMode(self.DeviceCoordinateCache)

    self.highlights = set()
    self.makeBonds = set()
    self.hover = False
    self.rightBond = False
    self.freeDrag = False

    self.atomLabel = AtomLabelShowWidget(scene, self, compoundView, atom)
    compoundView.addToGroup(self.atomLabel)
    #compoundView.scene.addItem(self.atomLabel)
    
    self.syncToAtom()

#  @profile
  def paint(self, painter, option, widget):
    
    painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
    
    AtomItem.paint(self, painter, option, widget)
    
    painter.setRenderHint(QtGui.QPainter.Antialiasing, False)


class BondItemShowWidget(BondItem):

  def __init__(self, scene, compoundView, bond):
    
    QtGui.QGraphicsItem.__init__(self, scene=scene)
     
    compoundView.bondItems[bond] = self
   
    self.setAcceptedMouseButtons(Qt.LeftButton)
    self.selected = False
    self.setZValue(-2)
    
    self.setCacheMode(self.DeviceCoordinateCache)
    self.compoundView = compoundView
    if compoundView.glWidget:
      self.glWidget = compoundView.glWidget
    else:
      self.glWidget = compoundView.container.parent
      
    self.bond = bond
    self.atomItems = []
    
    self.drawData = ()
    self.bbox = NULL_RECT
    
    self.syncToBond()
    
#  @profile
  def paint(self, painter, option, widget):
    
    if not self.drawData:
      return

    painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

    BondItem.paint(self, painter, option, widget)

    painter.setRenderHint(QtGui.QPainter.Antialiasing, False)
    
class LabelItemShowWidget(QtGui.QGraphicsItem):
  
  def __init__(self, scene, compoundView):
    
    QtGui.QGraphicsItem.__init__(self, scene=scene)
    self.compoundView = compoundView
    self.label = compoundView.compound.name
    if compoundView.glWidget:
      self.glWidget = compoundView.glWidget
    else:
      self.glWidget = compoundView.container.parent
      
    self.spectrum = self.compoundView.spectrum
    self.setCacheMode(self.DeviceCoordinateCache)
    self.bbox = NULL_RECT
    
  def boundingRect(self):
    
    return self.bbox
    
  def paint(self, painter, option, widget):
    qPoint = QtCore.QPointF
    qRectF = QtCore.QRectF
    painter.save()
    fontMetric = QtGui.QFontMetricsF(painter.font())
    
    tl = self.compoundView.boundingRect().topLeft()
    x0 = tl.x()
    y0 = tl.y()
    #y1 = y0 + viewRect.height()
    
    painter.setFont(QtGui.QFont("Arial", 22) )
    fontMetric = QtGui.QFontMetricsF(painter.font())
    bboxY = fontMetric.boundingRect('X')
    h = bboxY.height()
    if self.bbox is NULL_RECT:
      bbox = fontMetric.boundingRect(self.label)
      self.bbox = QRectF(x0-5, y0+4, bbox.width()+11, h+1)
      
    posColor = None
    if self.spectrum:
      if hasattr(self.spectrum, 'posColor'):
        posColor = QtGui.QColor(*self.glWidget._hexToRgba(self.spectrum.posColor))
      elif hasattr(self.spectrum, 'posColors'):
        posColorValue = list(self.spectrum.posColors)[-1]
        posColor = QtGui.QColor()
        posColor.setRgbF(*self.glWidget._hexToRgba(posColorValue))
    if not posColor:
      posColor = QtGui.QColor()
      posColor.setRgbF(0, 0.31, 1, 1)
      
    painter.fillRect(self.bbox, posColor)
    painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
    painter.setPen(inverseGrey(posColor))

    painter.drawText(qPoint(x0, y0+h), self.label)
    painter.restore()
               
class CompoundViewShowWidget(QtGui.QGraphicsItemGroup):

  def __init__(self, parent=None, variant=None, spectrum = None, container = None, glWidget = None):

    QtGui.QGraphicsItemGroup.__init__(self, None)
#    parent.addItem(self)
    self.parent = parent
    self.scene = parent
    self.rotatePos = None
    if variant:
      self.compound = variant.compound
    else:
      self.compound = None

    self.container = container
    self.glWidget = glWidget
    self.spectrum = spectrum
    self.name = None
    
    self.setHandlesChildEvents(False)
    
    self.dustbin = set()  
    self.variant = variant
    self.atomViews = {}
    self.selectedViews = set()
    self.bondItems = {}
    self.groupItems = {}
    self.update()
    self.nameAtoms = False
    self.showChargeSymbols = True
    self.showChiralities = False
    self.showStats = False
    self.showGroups = False
    self.menuAtomView = None
    self.menuAtom = None
    self.movePos = None
    #self.zoomLevel = 1.0
    # Context menu
        
    self.needMenuAtom = []
    self.needSelectedAtom = []
    self.needFurtherCheck = []
    self.contextMenu = self.setupContextMenu()

    self.selectionBox = SelectionBox(self.scene, self)
    self.label = None
    #self.scene.addItem(self.selectionBox)
    self.bbox = None
    
    self.showSkeletalFormula = True
    self.showSkeletalFormulaColor = False
    self.snapToGrid = True
    
    self.autoChirality = True

    self.addGraphicsItems()
    
    if self.variant and self.snapToGrid:
      self.variant.snapAtomsToGrid()
      self.updateAll()
      self.alignMolecule(False)
    
    self.show()
  
  def resizeEvent(self, event):
    
    #self.setSceneRect(self.viewport().rect())
    
    return QtGui.QGraphicsView.resizeEvent(self, event)
    
  def dragEnterEvent(self, event):
    
    event.ignore()

  def dragMoveEvent(self, event):
    
    event.ignore()

  def dragLeaveEvent(self, event):
  
    event.ignore()
    
  def dropEvent(self, event):
    
    event.ignore()
    
#  def mouseReleaseEvent(self, event):
#
#    return QtGui.QGraphicsItemGroup.mouseReleaseEvent(self, event)
#
  def wheelEvent(self, event):
    
    delta = event.delta()
    
    scale = self.scale()
    
    if delta < 0:
      scale=0.8 * scale
    else:
      scale=1.25 * scale

    self.setScale(scale)

  def contextMenuEvent(self, event):
    
    self.contextMenu.exec_(event.screenPos())

  def setupContextMenu(self):
    
    QAction = QtGui.QAction
    
    menu = Menu()
    
    # Do not add all menu items if CompoundView is included inside a dock widget, i.e. not called from ChemBuild itself.

    action = QAction('Add Hydrogens', None, triggered=self.addHydrogens)
    menu.addAction(action)  
    action = QAction('Auto Bond', None, triggered=self.autoBond)
    menu.addAction(action)
    action = QAction('Auto Arrange', None, triggered=self.minimise)
    menu.addAction(action)
    menu.addSeparator()
    menu.addItem('Show atom names', self.toggleAtomNames, checked=self.nameAtoms, object=self)
    if self.container:
      action = QAction('Close', None, triggered=self.container.close)
    menu.addAction(action)
  
    return menu
    
  def minimise(self):

    if self.variant:
    
      # Switch automatic chirality determination off during minimisation to save time.
      autoChirality = self.autoChirality
      self.autoChirality=False
      
      varAtoms = [v.atom for v in self.selectedViews]
      if not varAtoms:
        varAtoms = self.variant.varAtoms
      
      drawFunc=self.forceRedraw
      window = self.scene.parent().mainApp
      try:
        window.setCursor(QtCore.Qt.WaitCursor)
      except AttributeError:
        window = self.scene.parent().widget.window()
        window.setCursor(QtCore.Qt.WaitCursor)
        
      if self.showSkeletalFormula:
        self.variant.snapAtomsToGrid(sorted(varAtoms, key=lambda atom: atom.name), ignoreHydrogens = False)
        self.updateAll()
        self.alignMolecule()
      else:
        self.variant.minimise2d(varAtoms, drawFunc=drawFunc)
      atoms = set(self.variant.atomDict.keys())
      
      # If the whole var was selected
      if varAtoms == self.variant.varAtoms:
        for var in self.variant.compound.variants:
          if var is self.variant:
            continue
 
          # Update the atoms in other vars not minimised
          atomsB = set(var.atomDict.keys())
          different = atoms ^ atomsB
          unique = different & atomsB
 
          if unique:
            uniqAtoms = [var.atomDict[a] for a in unique]
            var.minimise2d(uniqAtoms, drawFunc=None)
            atoms.update(unique)
      window.unsetCursor()
      self.autoChirality = autoChirality

  def addHydrogens(self, atoms=None):
  
    scale = self.scale()
    self.setScale(1.0)
    if not atoms:
      if self.menuAtom:
        atoms = [self.menuAtom,]
      elif self.selectedViews:
        atoms = [v.atom for v in self.selectedViews]
      elif self.variant:
        atoms = list(self.variant.varAtoms)
    
    if not atoms:
      self.setScale(scale)
      return 0
    
    compound = self.compound
    variant = self.variant
    if not variant:
      self.setScale(scale)
      return 0
        
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
    
    self.setScale(scale)
    return hydrogens
    
  def autoSetChirality(self):
    
    if not self.autoChirality:
      return
    
    variant = self.variant
    varAtoms = variant.varAtoms
    
    for atom in varAtoms:
      atom.autoSetChirality()

  def addGraphicsItems(self):
  
    if not self.variant:
      return
   
    scene = self.scene
    scale = self.scale()
    self.setScale(1.0)
         
    # Draw groups

    self.groupItems = {}
    for group in self.variant.atomGroups:
      if group.groupType == EQUIVALENT:
        item = EquivItemShowWidget(scene, self, group)
        self.addToGroup(item)
      
      elif group.groupType == PROCHIRAL:
        item = ProchiralItemShowWidget(scene, self, group)
        self.addToGroup(item)

      elif group.groupType == AROMATIC:
        item = AromaticItemShowWidget(scene, self, group)
        self.addToGroup(item)
   
    # Draw atoms
    
    self.atomViews = {}
    for atom in self.variant.varAtoms:
      atomItem = AtomItemShowWidget(scene, self, atom)
      self.addToGroup(atomItem)

  
    # Draw bonds
    done = set()
    self.bondItems = bondDict = {}
    for bond in self.variant.bonds:
      atoms = frozenset(bond.varAtoms)
      if atoms in done:
        pass
        
      bondItem = BondItemShowWidget(scene, self, bond)
      self.addToGroup(bondItem)
      done.add(atoms)
    self.setScale(scale)

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
          atomView = AtomItemShowWidget(scene, self, atom)
          self.addToGroup(atomView)

      zombieBonds = set(self.bondItems.keys()) - set(var.bonds)
      for bond in zombieBonds:
        bondItem =  bondItems[bond]
        del bondItems[bond]
        del bondItem
      
      for bond in var.bonds:
        bondItem = getBondItem(bond)
        
        if not bondItem:
          bondItem = BondItemShowWidget(scene, self, bond)
          self.addToGroup(bondItem)
       
#      self.updateVars()

  def autoBond(self):
    
    scale = self.scale()
    self.setScale(1.0)
    pos = self.pos()
    self.setPos(0, 0)
     
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
        self.setScale(scale)
        self.setPos(pos)
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
        self.setScale(scale)
        self.setPos(pos)
        return 0
       
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
  
    self.setScale(scale)
    self.setPos(pos)
    return n

  def forceRedraw(self):
  
    self.updateAll()
    self.update()
      
  def toggleAtomNames(self, object):
    
    self.nameAtoms = not self.nameAtoms
    self.forceRedraw()
    
  def boundingRect(self):

    if self.bbox:
      return self.bbox
    else:
      return QtGui.QGraphicsItemGroup.boundingRect(self)

  # Places the molecule in the top left corner of the viewable area.
  def alignMolecule(self, ignoreHydrogens = False):
    
    leftAtom = None
    leftAtomCoord = None
    topAtom = None
    topAtomCoord = None
    rightAtom = None
    rightAtomCoord = None
    bottomAtom = None
    bottomAtomCoord = None

    atoms = self.atomViews
    x0 = 20
    y0 = 50
    
    for atom in atoms:
      if ignoreHydrogens and atom.element == 'H':
        continue
      x, y, z = atom.coords
      if leftAtom == None or x < leftAtomCoord:
        leftAtom = atom
        leftAtomCoord = x
      if topAtom == None or y < topAtomCoord:
        topAtom = atom
        topAtomCoord = y
      if rightAtom == None or x > rightAtomCoord:
        rightAtom = atom
        rightAtomCoord = x
      if bottomAtom == None or y > bottomAtomCoord:
        bottomAtom = atom
        bottomAtomCoord = y
    
    dX = x0 - leftAtomCoord
    dY = y0 - topAtomCoord
    
    for atom in atoms:
      x, y, z = atom.coords
      atom.coords = (x+dX, y+dY, z)
      
    topAtomCoord += dY
    leftAtomCoord += dX
    bottomAtomCoord += dY
    rightAtomCoord += dX

    tl = QPointF(leftAtomCoord-20, topAtomCoord-50)
    br = QPointF(rightAtomCoord+10, bottomAtomCoord+10)
    
    self.forceRedraw()
    
    self.bbox = QRectF(tl, br)
