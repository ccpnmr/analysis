from math import atan2, sin, cos, sqrt, degrees, radians, hypot
PI = 3.1415926535898

from PyQt5 import QtCore, QtGui, QtWidgets

from ccpnmr.chemBuild.model.Bond import Bond, BOND_TYPE_VALENCES, BOND_STEREO_DICT
import numpy as np
from ccpnmr.chemBuild.general.Constants import LINK, DISALLOWED
from ccpnmr.chemBuild.general.Constants import HIGHLIGHT, HIGHLIGHT_BG, ATOM_NAME_FG
from ccpnmr.chemBuild.general.Constants import ELEMENT_FONT, ELEMENT_DATA,  ELEMENT_DEFAULT
from ccpnmr.chemBuild.general.Constants import CHARGE_FONT, NEG_COLOR, POS_COLOR
from ccpnmr.chemBuild.general.Constants import CHIRAL_FONT, CHIRAL_COLOR
from ccpnmr.chemBuild.general.Constants import EQUIV_COLOR, PROCHIRAL_COLOR, CHARGE_BG_COLOR

from memops.qtgui.Colors import inverseGrey

Qt = QtCore.Qt
QPointF = QtCore.QPointF
QRectF = QtCore.QRectF

RADIUS = 50.0
BOND_SEP = 3.0
NULL_RECT = QRectF()
NULL_POINT = QPointF()
FONT_METRIC = QtGui.QFontMetricsF(ELEMENT_FONT)

SHADOW_COLOR = QtGui.QColor(64,64,64)
SHADOW_RADIUS = 4
SHADOW_OFFSET = (2,2)

AURA_COLOR = QtGui.QColor(255,255,255)
AURA_OFFSET = (0,0)
AURA_RADIUS = 4

ItemIsMovable = QtWidgets.QGraphicsItem.ItemIsMovable
ItemIsSelectable = QtWidgets.QGraphicsItem.ItemIsSelectable
ItemPositionChange = QtWidgets.QGraphicsItem.ItemPositionChange
ItemSendsGeometryChanges = QtWidgets.QGraphicsItem.ItemSendsGeometryChanges

REGION_PEN = QtGui.QPen(HIGHLIGHT, 0.8, Qt.SolidLine)


BOND_CHANGE_DICT = {'single':'double',
                    'aromatic':'double',
                    'singleplanar':'double',
                    'double':'triple',
                    'triple':'single',
                    'dative':'single'}

class AtomLabel(QtWidgets.QGraphicsItem):

  def __init__(self, scene, atomView, compoundView, atom):
    
    QtWidgets.QGraphicsItem.__init__(self)
    self.scene = scene
    
    #effect = QtWidgets.QGraphicsDropShadowEffect(compoundView)
    #effect.setBlurRadius(SHADOW_RADIUS)
    #effect.setColor(SHADOW_COLOR)
    #effect.setOffset(*SHADOW_OFFSET)
    
    self.setAcceptHoverEvents(True)
    self.setAcceptedMouseButtons(Qt.LeftButton)
    #self.setGraphicsEffect(effect)
    self.setZValue(1)
    self.compoundView = compoundView
    self.atomView = atomView
    self.hover = False
    self.atom = atom
    self.bbox = NULL_RECT
    self.drawData = ()
    self.syncLabel()
    self.setCacheMode(self.DeviceCoordinateCache)
  
  def delete(self):

    self.compoundView.scene.removeItem(self)

  def hoverEnterEvent(self, event):
  
    self.hover = True
    self.update()

  def hoverLeaveEvent(self, event):
       
    self.hover = False
    self.update()
  
  def mouseDoubleClickEvent(self, event):
        
    if self.atom.element == LINK:
      return
    
    self.compoundView.queryAtomName(self)
    
    return QtWidgets.QGraphicsItem.mouseDoubleClickEvent(self, event)
    
  def syncLabel(self):
    
    rad = 15.0
    
    atom = self.atom
    xa, ya, za = atom.coords
    
    if atom.bonds or atom.freeValences:
      
      angles = atom.getBondAngles()
      angles += atom.freeValences
      angles = [a % (2.0*PI) for a in angles]
      angles.sort()
      angles.append(angles[0]+2.0*PI)
      diffs = [(round(angles[i+1]-a, 3), a)
               for i, a in enumerate(angles[:-1])]
      diffs.sort()
       
      delta, angle = diffs[-1]
      angle += delta/2.0
    
    else:
      angle = 1.0

    
    name = atom.name
    if name:
      text = name
    else:
      text = '?'
    
    textRect = FONT_METRIC.tightBoundingRect(text)
    w = textRect.width() / 1.5
    h = textRect.height() / 2.0
    
    x = xa+(rad+w) * sin(angle)
    y = ya+(rad+h) * cos(angle)
    
    # Global absolute centre
    self.setPos(QPointF(x, y))
    
    center = QPointF(-w,h)
    self.drawData = (center, text)
    rect = QRectF(QPointF(-w, -h),
                  QPointF(w, h))
    self.bbox = rect.adjusted(-h, -h, h, h)
    
    self.update()

  def boundingRect(self):
    
    if not self.compoundView.nameAtoms:
      return NULL_RECT
    return self.bbox
      
  def paint(self, painter, option, widget):

    painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
    #if self.compoundView.showSkeletalFormula and self.atom.element == 'H':
      #for n in self.atom.neighbours:
        #if n.element != 'C':
          #return

    useName = self.compoundView.nameAtoms

    if useName and self.drawData:
      point, text = self.drawData
      painter.setFont(ELEMENT_FONT)
      if self.hover:
        painter.setPen(Qt.black)

      elif not isinstance(self.compoundView, QtWidgets.QGraphicsItem):
        if self.compoundView.backgroundColor == Qt.darkGray:
          painter.setPen(ATOM_NAME_FG)

        else:
          painter.setPen(QtGui.QColor(0, 0, 0, 128))

        # if self.atomView.isSelected():
        #   painter.setPen(Qt.green)

      painter.drawText(point, text)
    painter.setRenderHint(QtGui.QPainter.Antialiasing, False)


class AtomGroupLabel(QtWidgets.QGraphicsItem):

  def __init__(self, scene, atomView, compoundView, atomGroup):

    QtWidgets.QGraphicsItem.__init__(self)
    self.scene = scene
    self.setAcceptHoverEvents(True)
    self.setAcceptedMouseButtons(Qt.LeftButton)
    self.setZValue(1)
    self.compoundView = compoundView
    self.atomView = atomView
    self.center = atomView.center
    self.hover = False
    self.atomGroup = atomGroup
    self.bbox = NULL_RECT
    self.drawData = ()
    self.syncLabel()
    self.setCacheMode(self.DeviceCoordinateCache)

  def delete(self):

    self.compoundView.scene.removeItem(self)

  def hoverEnterEvent(self, event):

    self.hover = True
    self.update()


  def hoverLeaveEvent(self, event):

    self.hover = False
    self.update()

  def mouseDoubleClickEvent(self, event):

    self.compoundView.queryAtomGroupName(self)

    return QtWidgets.QGraphicsItem.mouseDoubleClickEvent(self, event)

  def syncLabel(self):

    rad = 20.0

    atomGroup = self.atomGroup
    coords =  np.array([a.coords for a in self.atomGroup.varAtoms])
    coords = list(coords.mean(axis=0))

    xa, ya, za = coords

    angle = 0

    name = atomGroup.name
    if name:
      text = name
    else:
      text = '???'

    # create a rectangle where to contain the text. Used for trigger the hover event etc
    textRect = FONT_METRIC.tightBoundingRect(text)
    textLenght = len(text)
    boxFactor = 0.5 * textLenght
    w = textRect.width() + boxFactor
    h = textRect.height() * 0.5

    x = xa + (rad + w) * sin(angle)
    y = ya + (rad + h) * sin(angle)

    # Global absolute centre
    self.setPos(QPointF(x, y))
    _center = QPointF(-w/2, h) # text position
    self.drawData = (_center, text)
    rect = QRectF(QPointF(-w, -h),
                  QPointF(w, h))
    self.bbox = rect.adjusted(-h, -h, h, h)


    self.update()

  def boundingRect(self):
    if not self.compoundView.showGroups:
      return NULL_RECT
    return self.bbox

  def paint(self, painter, option, widget):

    painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
    useName = self.compoundView.showGroups

    if useName and self.drawData:
      point, text = self.drawData

      painter.setFont(ELEMENT_FONT)
      if self.hover:
        painter.setPen(Qt.black)
      elif not isinstance(self.compoundView, QtWidgets.QGraphicsItem):
        if self.compoundView.backgroundColor == Qt.darkGray:
          painter.setPen(ATOM_NAME_FG)
        else:
          painter.setPen(QtGui.QColor(0, 0, 0, 128))

      # painter.drawRect(self.bbox)

      painter.drawText(point, text)
    painter.setRenderHint(QtGui.QPainter.Antialiasing, False)




class SelectionBox(QtWidgets.QGraphicsItem):
        
  def __init__(self, scene, compoundView):
    
    QtWidgets.QGraphicsItem.__init__(self)
    self.scene = scene
    self.setZValue(1)
    self.compoundView = compoundView
    self.begin = None
    self.region = None
    
  def updateRegion(self, begin=None, end=None):
            
    if begin and end:
      self.region = QRectF(begin, end).normalized()
      self.begin = begin
      
    elif begin:
      self.region = QRectF(begin, begin).normalized()
      self.begin = begin
    
    elif end and self.begin:
      self.region = QRectF(self.begin, end).normalized()
    
    else:
      self.region = None
      self.begin = None

    self.update()
      
  def boundingRect(self):
    
    if self.region:
      pad = 2
      return self.region.adjusted(-pad, -pad, pad, pad)
    
    else:
      return NULL_RECT
      
  def paint(self, painter, option, widget):
    
    if self.region:
      painter.setPen(REGION_PEN)
      painter.setBrush(HIGHLIGHT_BG)
      painter.drawRect( self.region )
  
class AtomGroupItem(QtWidgets.QGraphicsItem):

  def __init__(self, scene, compoundView, atomGroup):
    
    QtWidgets.QGraphicsItem.__init__(self)
    self.scene = scene
    
    compoundView.groupItems[atomGroup] = self
    
    self.compoundView = compoundView
    self.atomGroup = atomGroup
    self.atoms = atomGroup.varAtoms
    self.setZValue(-1)
    self.bbox = NULL_RECT
    self.drawData = ()
    self.center = NULL_POINT
    self.syncGroup()
    self.setCacheMode(self.DeviceCoordinateCache)
    self.name = self.atomGroup.name
    self.atomGroupLabel = AtomGroupLabel(scene, self, compoundView, self.atomGroup)
    scene.addItem(self)
    scene.addItem(self.atomGroupLabel)


  def boundingRect(self):
    
    return self.bbox

  def paint(self, painter, option, widget):

    pass

  def delete(self):

    compoundView = self.compoundView
    atomGroup = self.atomGroup
    self.atomGroupLabel.delete()
    compoundView.scene.removeItem(self)

    # del self.atomGroupLabel
    # del self
    
class EquivItem(AtomGroupItem):

  def syncGroup(self):
    
    coords = [a.coords for a in self.atoms]
    n = float(len(coords))
    
    xl = [xyz[0] for xyz in coords]
    yl = [xyz[1] for xyz in coords]
    
    xc = sum(xl)/n
    yc = sum(yl)/n

    xa = min(xl)
    ya = min(yl)
    
    xb = max(xl)
    yb = max(yl)
    
    dx = xb-xa
    dy = yb-ya
    
    self.center = QPointF(xc-xa, yc-ya)

    self.drawData = [QPointF(xyz[0]-xa, xyz[1]-ya) for xyz in coords]
    
    self.setPos(QPointF(xa, ya))
    
    rect = QRectF(QPointF(0.0,0.0),
                         QPointF(dx, dy))  
    
    pad = 2
    self.bbox = rect.normalized().adjusted(-pad, -pad, pad, pad)
    
    self.update()
   
  def paint(self, painter, option, widget):
    
    if not self.compoundView.showGroups:
      return
      
    pen = QtGui.QPen(EQUIV_COLOR, 2, Qt.DotLine)
    painter.setPen(pen)
    painter.setBrush(EQUIV_COLOR)
    
    center = self.center
    for point in self.drawData:
      painter.drawLine(point, center)
 
    pen = QtGui.QPen(EQUIV_COLOR, 2, Qt.SolidLine)
    painter.setPen(pen)
    painter.drawEllipse(center, 2.0, 2.0)


class ProchiralItem(AtomGroupItem):
    
  def syncGroup(self):
     
    atoms = self.atoms
    
    if len(atoms) == 2:
      atomA, atomB = atoms
      
      x1, y1, z1 = atomA.coords
      x2, y2, z2 = atomB.coords
      
      dx = x2-x1
      dy = y2-y1
 
      anchorPoint = QPointF(x1, y1)
      startPoint = QPointF(0.0, 0.0)
      endPoint = QPointF(dx, dy)
      
    else:
      groupDict = self.compoundView.groupItems
    
      groups = list(self.atomGroup.subGroups)
 
      if len(groups) == 2:
        groupA = groups[0]
        groupB = groups[1]
        
        gItemA = groupDict.get(groupA)
        gItemB = groupDict.get(groupB)
        
        if gItemA and gItemB:
 
          centerA = gItemA.center
          centerB = gItemB.center
 
          anchorPoint = centerA
          startPoint = self.mapFromItem(gItemA, centerA)
          endPoint = self.mapFromItem(gItemB, centerB)
        
        else:
          self.drawData = None
          return
    
      else:
        self.drawData = None
        return
    
    pad = 2.0
    rect = QRectF(startPoint, endPoint)
    self.center = rect.center()
    self.bbox = rect.normalized().adjusted(-pad, -pad, pad, pad)
    self.drawData = (startPoint, endPoint)                      
    self.setPos(anchorPoint)
    self.update()

  def paint(self, painter, option, widget):
    
    if not self.compoundView.showGroups:
      return

    if self.drawData:
      startPoint, endPoint = self.drawData
 
      pen = QtGui.QPen(PROCHIRAL_COLOR, 2, Qt.DotLine)
      painter.setPen(pen)
      painter.drawLine(startPoint, endPoint)
    

class AromaticItem(AtomGroupItem):
    
  def syncGroup(self):
    
    coords = [a.coords for a in self.atoms]
    
    n = len(coords)
    nl = list(range(n))
    n = float(n)
    
    xl = [xyz[0] for xyz in coords]
    yl = [xyz[1] for xyz in coords]
    
    xc = sum(xl)/n
    yc = sum(yl)/n

    xa = min(xl)
    ya = min(yl)
    
    xb = max(xl)
    yb = max(yl)
    
    dx = xb-xa
    dy = yb-ya
    
    dx2 = [(x-xc)*(x-xc) for x in xl]
    dy2 = [(y-yc)*(y-yc) for y in yl]
    
    d2 = [dx2[i]+dy2[i] for i in nl]
        
    r = sqrt(min(d2)) * cos(PI/n)
    
    r = max(2*BOND_SEP, r-2*BOND_SEP)
    
    self.center = QPointF(xc-xa, yc-ya)

    self.drawData = [r, r]
    
    self.setPos(QPointF(xa, ya))
    
    rect = QRectF(QPointF(0.0,0.0),
                         QPointF(dx, dy))  
    
    pad = 2
    self.bbox = rect.normalized().adjusted(-pad, -pad, pad, pad)
    
    self.update()
                 
   
  def paint(self, painter, option, widget):
    
    r1, r2 = self.drawData
    center = self.center
  
    pen = QtGui.QPen(Qt.black, 1, Qt.SolidLine)
    painter.setPen(pen)
    painter.drawEllipse(center, r1, r2)
    

class AtomItem(QtWidgets.QGraphicsItem):

  def __init__(self, scene, compoundView, atom):
    
    QtWidgets.QGraphicsItem.__init__(self)
    self.scene = scene
    
    compoundView.atomViews[atom] = self
    
    self.compoundView = compoundView
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
    #effect = QtWidgets.QGraphicsDropShadowEffect(compoundView)
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
    
    self.atomLabel = AtomLabel(scene, self, compoundView, atom)
    compoundView.scene.addItem(self.atomLabel)
    
    self.syncToAtom()
  
  def itemChange(self, change, value):
    
    if change == ItemPositionChange:
      compoundView = self.compoundView
      x0, y0, z = self.atom.coords
      
      value = value.toPoint()
      x = value.x()
      y = value.y()
      dx = x0-x
      dy = y0-y
      
      freeDrag = self.freeDrag
      
      nSelected = len(compoundView.selectedViews)
        
      # This code block is to handle position changes of branches when snapping to grid.
      # In practice it will allow two branches to swap places.
      if compoundView.snapToGrid and (dx != 0 or dy != 0) and nSelected <= 1:
        # Find which of the neighbouring atoms form the longst branch. A more proper check
        # to ensure the backbone is found could be done.
        # The shortest branch and the branch of the selected atom can be moved.
        neighbours = sorted(self.atom.neighbours, key=lambda atom: atom.name)
        prevAtom = None
        longestBranchLen = 0
        for neighbour in neighbours:
          branch = self.atom.findAtomsInBranch(neighbour)
          branchLen = len(branch)
          if branchLen > longestBranchLen:
            prevAtom = neighbour
            longestBranch = branch
            longestBranchLen = branchLen
        if prevAtom:
          xP = prevAtom.coords[0]
          yP = prevAtom.coords[1]
  #        bondLength = hypot(x0 - xP, y0 - yP)
          bondLength = 50 # TODO: A smarter way of setting the right bondlength
          neighbours = sorted(prevAtom.neighbours, key=lambda atom: atom.name)
          longestBranchLen = 0
          # Find a reference atom next to prevAtom to calculate bond angles.
          frozenNeighbour = None
          for neighbour in neighbours:
            if neighbour != self.atom and neighbour.element != 'H':
              branch = prevAtom.findAtomsInBranch(neighbour)
              branchLen = len(branch)
              if branchLen > longestBranchLen:
                longestBranch = branch
                longestBranchLen = branchLen
                frozenNeighbour = neighbour
                prevAngle = round(degrees(prevAtom.getBondAngle(neighbour)), 0)
                
          if frozenNeighbour:
            neighbour = frozenNeighbour
            atoms = neighbour.findAtomsInBranch(prevAtom) - set([prevAtom, self.atom])
          else:
            for neighbour in self.atom.neighbours:
              if neighbour.element != 'H':
                frozenNeighbour = prevAtom
                prevAngle = 330
                atoms = set([])
                break
            
          if not frozenNeighbour:
            print("No frozenNeighbour",  longestBranchLen)
            prevAtom = None
            freeDrag = True
        else:
          freeDrag = True
        
        # If the item was selected and Ctrl is pressed when the item is moved the item does not count a selected. Let it be freely movable.
        # If there are more atoms selected also let them be freely movable.
        if self.selected and not freeDrag:
          prefAngles = prevAtom.getPreferredBondAngles(prevAngle, None, atoms, False)
          # If the dragged atom only has neighbours with hydrogens (i.e. the reference atom has no other visible atoms connected) add
          # an extra possible angle.
          if frozenNeighbour == prevAtom and prevAngle == 330:
            prefAngles.append(0)
                  
          if len(prefAngles) < 2:# or self.atom.atomInSameRing(prevAtom):
            value.setX(x0)
            value.setY(y0)
            return QtWidgets.QGraphicsItem.itemChange(self, change, value)
          
          prevAngle = radians(prevAngle)
          currAngle = (prevAtom.getBondAngle(self.atom) - prevAngle) % (2.0*PI)
          newAngle = (atan2(y - yP, x - xP) - prevAngle) % (2.0*PI)

          # Find which preferred angle is closest to the new angle.
          bestAngle = None
          bestDiff = None
          for angle in prefAngles:
            if angle < 0:
              angle += 360
            angle = radians(angle)
            diff = abs(newAngle - angle)
            if not bestAngle or diff < bestDiff:
              bestAngle = angle
              bestDiff = diff

          # If the current angle is agreeing best just set the selection circle to where the atom is
          # and return.
          if abs(bestAngle - currAngle) < 0.001:
            value.setX(x0)
            value.setY(y0)
            return QtWidgets.QGraphicsItem.itemChange(self, change, value)

          bestAngle += prevAngle
          if self.atom.element == 'H':
            x = xP + bondLength * 0.75 * cos(bestAngle)
            y = yP + bondLength * 0.75 * sin(bestAngle)
          else:
            x = xP + bondLength * cos(bestAngle)
            y = yP + bondLength * sin(bestAngle)
          
        self.atom.setCoords(x, y, z)
        
        if prevAtom and not self.atom.atomInSameRing(prevAtom):
          # First snap the atoms in the same branch as the selected atom (these will not take the other branch into account when
          # deciding their positions).
          sameBranch = sorted(prevAtom.findAtomsInBranch(self.atom) - set([self.atom]))
          atoms -= longestBranch
          atoms = sorted(atoms, key=lambda atom: atom.name)
          if len(sameBranch) > 0:
            for atom in sameBranch:
              if atom in atoms:
                atoms.remove(atom)
            self.variant.snapAtomsToGrid(sameBranch, self.atom, compoundView.showSkeletalFormula, bondLength = bondLength)

          # Snap the second branch to the grid taking the first branch into account.
          if len(atoms) > 0:
            self.variant.snapAtomsToGrid(atoms, prevAtom, compoundView.showSkeletalFormula, bondLength = bondLength)

        self.compoundView.updateAll()
          
      # Synch positions
      # implicitly set bonds too
      else:
        self.atom.setCoords(x,y,z)
      
      # Make bond detection
          
      d = RADIUS
      # When using snapToGrid the distance between the atoms is so small that double and tripe bonds are created too easily if d2 is not made smaller.
      if compoundView.snapToGrid:
        d2 = d * 0.25
      else:
        d2 = d * 0.5
      r2 = 15
      atomViews = compoundView.atomViews
      self.makeBonds = set()

      addBond = self.makeBonds.add
      valencesS = self.atom.freeValences
      atoms = self.variant.varAtoms - set([self.atom])
      positionsS = [(x+r2*sin(angle),
                     y+r2*cos(angle), angle) for angle in valencesS]
      
      if valencesS:
        for atom in atoms:
          valences = atom.freeValences

          if not valences:
            continue
            
          atomView = atomViews.get(atom)
          if not atomView:
            continue
          
          x1, y1, z1 = atom.coords
 
          dx = x1-x
          dy = y1-y
          dist2 = (dx*dx) + (dy*dy)
 
          # consider using items directly
          if dist2 < d*d:

            # Other atom
            positions = [(x1+r2*sin(a),
                          y1+r2*cos(a), a) for a in valences]
 
            for x2, y2, a2 in positions:
              for x3, y3, a3 in positionsS:
                dx2 = x3-x2
                dy2 = y3-y2
 
                if (dx2*dx2) + (dy2*dy2) < (d2 * d2):
                  atomView.highlights.add(a2)
                  self.highlights.add(a3)
                  addBond( (atom, self.atom) )

          atomView.update()
        self.update()
      
      for bondItem in self.bondItems:
        bondItem.syncToBond()     
      
      groupItems = compoundView.groupItems
      for group in self.atom.atomGroups:
        groupItems[group].syncGroup()
        groupItems[group].atomGroupLabel.syncLabel()

      self.atomLabel.syncLabel()

      
    return QtWidgets.QGraphicsItem.itemChange(self, change, value)
    
  def moveAtom(self, coords):
    
    if isinstance(coords, tuple):
      (x, y) = coords

    else:
      x = coords.x()
      y = coords.y()
    
    z = self.atom.coords[2]
    self.atom.setCoords(float(x), float(y), z)
    self.syncToAtom()
  
    
  def syncToAtom(self):
  
    atom = self.atom
    compoundView = self.compoundView
    
    bondDict = compoundView.bondItems
    self.bondItems = [bondDict[bond] for bond in atom.bonds if bond in bondDict]
    
    if atom.chirality:
      r = 21.0
    elif atom.freeValences or abs(atom.charge) > 1:
      r = 18.0
    else:
      r = 15.0
    
    x, y, z = atom.coords
    
    # Global location
    coords = QPointF(x, y)
    
    # Define where local origin is in global 
    self.setPos(coords)
    
    rightBond = 0
    leftBond = 0

    if abs(atom.charge) > 1 or atom.chirality:
      adj = 9
    else:
      adj = 0
      
    #if self.compoundView.showSkeletalFormula:
      #for neighbour in atom.neighbours:
      #nH = 0
        #if neighbour.element == 'H':
          #nH += 1

      #if atom.element != 'C' or atom.freeValences or atom.chirality:# or nH == 4:
        #for neighbour in atom.neighbours:
          #if neighbour.element == 'H':
            #continue
          #nX, nY, nZ = neighbour.coords
          #if nX > x:
            #dY = max(0.0001, abs(nY - y))
            #currD = 1/dY
            #if currD > rightBond:
              #rightBond = currD
          #elif nX < x:
            #dY = max(0.0001, abs(nY - y))
            #currD = 1/dY
            #if currD > rightBond:
              #leftBond = currD
              
        #adj += 9
        #if nH > 1:
          #adj += 9
      
    # In local coords
    if rightBond > leftBond:
      self.rightBond = True
      self.bbox = QRectF(QPointF(-r-adj, -r),
                        QPointF(r, r+adj))
    else:
      self.rightBond = False
      self.bbox = QRectF(QPointF(-r, -r),
                        QPointF(r+adj, r+adj))

    for bondItem in self.bondItems:
      bondItem.syncToBond()
    
    groupItems = compoundView.groupItems
    for group in atom.atomGroups:
      groupItems[group].syncGroup()
      groupItems[group].atomGroupLabel.syncLabel()
      
    if self.compoundView.autoChirality:
      atom.autoSetChirality()
      for neighbour in atom.neighbours:
        neighbour.autoSetChirality()
    
    self.atomLabel.syncLabel()
    self.update()

  def boundingRect(self):
    
    #if self.compoundView.showSkeletalFormula and self.atom.element == 'H':
      #return NULL_RECT
    return self.bbox
   
  def delete(self):
    
    compoundView = self.compoundView
    atom = self.atom
    self.deselect()
    
    compoundView.scene.removeItem(self)
    
    for bondItem in list(self.bondItems):
      bondItem.delete()
 
    del compoundView.atomViews[atom]
    
    # Delete the master atom, not the var one
    masterAtom = atom.atom
    if not masterAtom.isDeleted:
      masterAtom.delete()
    
    self.atomLabel.delete()
    del self.atomLabel
    del self
  
  
  def deselect(self):
  
    self.selected = False
    self.setSelected(False)
    selected = self.compoundView.selectedViews
    
    if self in selected:
      selected.remove(self)
    
    for bondItem in self.bondItems:
      bondItem.deselect()
    
    self.update()

  def select(self):
    
    self.selected = True
    self.setSelected(True)
    selected = self.compoundView.selectedViews
    selected.add(self)
    
    for bondItem in self.bondItems:
      atomItemA, atomItemB = bondItem.atomItems
      
      if atomItemA.selected and atomItemB.selected:
        bondItem.select()
    
    self.update()

  def hoverEnterEvent(self, event):
  
    self.hover = True
    self.update()

  def hoverLeaveEvent(self, event):
  
    self.hover = False
    self.update()

  def mousePressEvent(self, event):
     
    QtWidgets.QGraphicsItem.mousePressEvent(self, event)
      
    selected = list(self.compoundView.selectedViews)
    
    mods = event.modifiers()
    button = event.button()
    haveCtrl = mods & Qt.CTRL
    haveShift = mods & Qt.SHIFT
    
    if haveCtrl or haveShift:
      if self.selected:
        self.deselect()
      else:
        self.select()
    
    elif not self.selected:
      for view in selected:
        view.deselect()
      self.select()
     
    self.update()
    
  def mouseMoveEvent(self, event):
    
    mods = event.modifiers()
    haveCtrl = mods & Qt.CTRL
    
    if haveCtrl:
      self.freeDrag = True
      if not self.selected:
        self.select()
    
    QtWidgets.QGraphicsItem.mouseMoveEvent(self, event)
    
    self.freeDrag = False
 
  def mouseDoubleClickEvent(self, event):
    
    if self.atomLabel.hover:
      self.compoundView.queryAtomName(self.atomLabel)
      return
     
    mods = event.modifiers()
    button = event.button()
    haveCtrl = mods & Qt.CTRL
    haveShift = mods & Qt.SHIFT
    
    if haveCtrl or haveShift:
      if self.selected:
        self.deselect()
      else:
        self.select()

    else:
      nAtoms = 1
      nPrev = 0
      atoms = set([self.atom])
 
      while nAtoms != nPrev:
        nPrev = nAtoms
        for atom in list(atoms):
          atoms.update(atom.neighbours)
 
        nAtoms = len(atoms)
 
      viewDict = self.compoundView.atomViews
      for atom in self.variant.varAtoms:
        atomView = viewDict[atom]
        if atom in atoms:
          atomView.select()
        else:
          atomView.deselect()

    self.update()

     
    QtWidgets.QGraphicsItem.mouseDoubleClickEvent(self, event)
   
      
  def mouseReleaseEvent(self, event):

    parent = self.compoundView
    atom = self.atom
    x, y, z = atom.coords

    if isinstance(parent, QtWidgets.QGraphicsItem):
      w = parent.boundingRect().width()
      h = parent.boundingRect().height()
    else:
      w = parent.width()
      h = parent.height()
    
    tl = parent.mapToScene(0, 0)
    br = parent.mapToScene(w, h)
    x1 = tl.x()
    x2 = br.x()
    y1 = tl.y()
    y2 = br.y()

    if x < x1 or y < y1 or x > x2 or y > y2:
      if not atom.neighbours:
        self.compoundView.parent.addToHistory()
        self.delete()
    
    else:
      d2 = RADIUS/2.0
      z = atom.coords[2]
      atom.setCoords(float(x), float(y), z)
      
      if self.makeBonds:
        self.compoundView.parent.addToHistory()
      
      atoms = set()
      for varAtomA, varAtomB in self.makeBonds:

        elemA = varAtomA.element
        elemB = varAtomB.element
        
        if not varAtomA.freeValences:
          continue

        if not varAtomB.freeValences:
          continue
        
        if set([elemA, elemB]) in DISALLOWED:
          continue   
        
        self.compoundView.parent.addToHistory()
        if varAtomA in varAtomB.neighbours:
          bond = self.variant.getBond(varAtomA, varAtomB)
          if varAtomA.freeValences and varAtomB.freeValences:
            bond.setBondType( BOND_CHANGE_DICT[bond.bondType] ) 
        else:
          Bond((varAtomA, varAtomB), autoVar=True)           
      
        atoms.add(varAtomA)
        atoms.add(varAtomB)
      
      #neighbourhood = set()
      #for atom in atoms:
      #  neighbourhood.update(atom.neighbours)
      
      #if atoms:
      #  #if atoms == neighbourhood:
      #  #  self.variant.minimise2d([atoms.pop(),])
      #  #else:
      #  self.variant.minimise2d([atom,])
 
        
      for bond in self.atom.bonds:
        atomA, atomB = bond.varAtoms
        
        if atomA is not atom:
          atomA.updateValences()
        
        if atomB is not atom:
          atomB.updateValences()
            
      self.atom.updateValences()
      
    if isinstance(parent, QtWidgets.QGraphicsItem):
      if parent.showSkeletalFormula:
        parent.alignMolecule()
      else:
        parent.alignMolecule(False)

    
    self.compoundView.updateAll() # Render new objs
    
    QtWidgets.QGraphicsItem.mouseReleaseEvent(self, event)
    self.update()

  def paint(self, painter, option, widget):
    
    textAlign = QtCore.Qt.AlignCenter
    qRect = QRectF
    qBrush = QtGui.QBrush
    qPoint = QPointF
    qPoly = QtGui.QPolygonF

    showChargeSymbols = self.compoundView.showChargeSymbols
    showChiralities = self.compoundView.showChiralities

    highlights = self.highlights
    atom = self.atom
        
    r  = 9.0
    r2 = 15.0
    r3 = 3.0 
    d = RADIUS
    d2 = d/2.0
    
    elem = atom.element
    
    drawText = painter.drawText
    drawEllipse = painter.drawEllipse
    drawLine = painter.drawLine
    drawPoly = painter.drawPolygon
    
    painter.setPen(Qt.black)
    painter.setFont(ELEMENT_FONT)
        
    color = ELEMENT_DATA.get(elem,  ELEMENT_DEFAULT)[1]
    if isinstance(self.compoundView, QtWidgets.QGraphicsItem):
      # SpecView
      if self.compoundView.container:
        backgroundColor = QtGui.QColor(*self.glWidget._hexToRgba(self.compoundView.container.mainApp.colors[0]))
        foregroundColor = QtGui.QColor(*self.glWidget._hexToRgba(self.compoundView.container.mainApp.colors[1]))
      # Analysis
      elif self.compoundView.glWidget:
        backgroundColor = QtGui.QColor()
        backgroundColor.setRgbF(*self.glWidget._hexToRgba(self.glWidget.spectrumWindow.analysisProfile.bgColor))
        foregroundColor = inverseGrey(backgroundColor)
        
      # Fallback alternative
      else:
        backgroundColor = Qt.white
        foregroundColor = Qt.black
    else:
      backgroundColor = self.compoundView.backgroundColor
      foregroundColor = Qt.black

    if not self.compoundView.showSkeletalFormula:
      if self.hover:
        brush = qBrush(self.gradient2)
      else:
        brush = qBrush(self.gradient)
    
      brush.setStyle(Qt.RadialGradientPattern)  
    
    else:
      brush = backgroundColor
    
    x, y, z = 0, 0, 0
    center = qPoint(x, y)
    
    painter.setBrush(foregroundColor)
    for angle in atom.freeValences:
      x2 = x+r2 * sin(angle)
      y2 = y+r2 * cos(angle)
      
      if angle in highlights:
        painter.setBrush(HIGHLIGHT)
        drawEllipse(qPoint(x2, y2), r3, r3)
        painter.setBrush(foregroundColor)
      else:
        drawEllipse(qPoint(x2, y2), r3, r3)
    
    if showChiralities and atom.chirality:
      if atom.bonds or atom.freeValences:
      
        angles = atom.getBondAngles()
        angles += atom.freeValences
        angles = [-(a-PI/2.0) % (2.0*PI) for a in angles]
        angles.sort()
        angles.append(angles[0]+2.0*PI)
        diffs = [(round(angles[i+1]-a, 3), a)
                for i, a in enumerate(angles[:-1])]
        diffs.sort()
        
        delta, angle = diffs[-1]
        angle += delta/2.0
      
      else:
        angle = 0.0

    painter.setBrush(brush)
    if self.compoundView.showSkeletalFormula:
      
      skeletalColor = self.compoundView.showSkeletalFormulaColor
      #nH = 0
      #for neighbour in atom.neighbours:
        #if neighbour.element == 'H':
          #nH += 1

      nDouble = 0
      for bond in atom.bonds:
        if bond.bondType == 'double':
          nDouble += 1
          
      #if elem == 'C' and len(atom.freeValences) == 0 and nH < 4 and nDouble < len(atom.bonds):
      if elem == 'C' and len(atom.freeValences) == 0 and nDouble < len(atom.bonds):
        transparent = QtGui.QColor(0, 0, 0, 0)
        painter.setPen(transparent)
        painter.setBrush(transparent)
        painter.drawEllipse(center, r, r)
        if self.selected:
          painter.setPen(HIGHLIGHT)
          drawEllipse(center, r+1, r+1)
          painter.setBrush(brush)
          
        if showChiralities:
          if atom.chirality and atom.chirality not in ('e', 'z', 'E', 'Z'):
            painter.setFont(CHIRAL_FONT)
            
            if skeletalColor:
              painter.setPen(CHIRAL_COLOR)
            else:
              painter.setPen(foregroundColor)
            
            chirality = atom.chirality
            
            if chirality in ('r', 's'):
              chirality = '(%s)' % chirality.upper()
            
            fontMetric = QtGui.QFontMetricsF(painter.font())
            width = fontMetric.width(chirality)
            height = fontMetric.height()
            chiralityX = x + (r+1)*cos(angle) - width/2
            chiralityY = y + (r+1)*sin(angle) + height/2
            drawText(qPoint(chiralityX, chiralityY), chirality)
        
        return
        
      #if elem == 'H':
        #for n in atom.neighbours:
          #if n.element != 'C':
            #return
      
      font = painter.font()
      smallFont = painter.font()
      font.setPointSizeF(font.pointSize()*1.5)
      painter.setFont(font)
      fontMetric = QtGui.QFontMetricsF(painter.font())
      bbox = fontMetric.tightBoundingRect(elem)
      width = fontMetric.width(elem)
      hydrogenWidth = fontMetric.width('H')
      h2 = bbox.height()/2.0
      w2 = bbox.width()/2.0
      
      if not skeletalColor:
        if isinstance(self.compoundView, QtWidgets.QGraphicsItem):
          # SpecView
          if self.compoundView.container:
            color = foregroundColor
          # Analyis
          elif self.compoundView.glWidget:
            color = foregroundColor
          # Fallback
          else:
            color = Qt.black
        else:
          color = Qt.black
      
      if elem == LINK:
        angles = atom.getBondAngles() + atom.freeValences
      
        if angles:
          startAngle = -1.0 * angles[0]
          angles = [startAngle + (i*2*PI/3.0) for i in (0,1,2)]

          if self.selected:
            painter.setPen(HIGHLIGHT)
            poly = qPoly()
            for angle in angles:
              x2 = x+(r+1)*sin(angle)
              y2 = y-(r+1)*cos(angle)
              poly.append(qPoint(x2, y2))
   
            drawPoly(poly)
            painter.setPen(foregroundColor)


          poly = qPoly()
          for angle in angles:
            x2 = x+r*sin(angle)
            y2 = y-r*cos(angle)
            poly.append(qPoint(x2, y2))

          drawPoly(poly)
              
      else:
        if self.selected:
          painter.setPen(HIGHLIGHT)
          drawEllipse(center, r+1, r+1)

        painter.setPen(backgroundColor)
        drawEllipse(center, r, r)
        textPoint = qPoint(x-w2, y+h2)
        painter.setPen(color)
        drawText(textPoint, elem)
        #hydrogenText= hydrogenNr = None
        #if nH != 0:
          #hydrogenText = 'H'
        #if nH > 1:
          #hydrogenNr = "%d" % nH
        #if hydrogenText:
          #nrWidth = 0
          #if hydrogenNr:
            #painter.setFont(smallFont)
            #fontMetric = QtGui.QFontMetricsF(smallFont)
            #nrWidth = fontMetric.width(hydrogenNr)
            #if self.rightBond:
              #textPoint = qPoint(x-width/2-nrWidth, y+h2+bbox.height()/3)
            #else:
              #textPoint = qPoint(x+width/2+hydrogenWidth, y+h2+bbox.height()/3)
            #drawText(textPoint, hydrogenNr)
            #painter.setFont(font)
          #if self.rightBond:
            #textPoint = qPoint(x-width/2-nrWidth-hydrogenWidth, y+h2)
          #else:
            #textPoint = qPoint(x+width/2, y+h2)
          #drawText(textPoint, hydrogenText)
        
        if skeletalColor:
          painter.setPen(foregroundColor)
      
        charge = atom.charge
        
        if showChiralities: 
          if atom.chirality and atom.chirality not in ('e', 'z', 'E', 'Z'):
            
            painter.setFont(CHIRAL_FONT)
            if skeletalColor:
              painter.setPen(CHIRAL_COLOR)
            
            chirality = atom.chirality
            if chirality in ('r', 's'):
              chirality = '(%s)' % chirality.upper()
            
            fontMetric = QtGui.QFontMetricsF(painter.font())
            width = fontMetric.width(chirality)
            height = fontMetric.height()
            chiralityX = x + (r+1)*cos(angle) - width/2
            chiralityY = y + (r+1)*sin(angle) + height/2
            drawText(qPoint(chiralityX, chiralityY), chirality)
          
          
          #elif atom.stereo:
          #  painter.setFont(CHIRAL_FONT)
          #  painter.setPen(CHIRAL_COLOR)
          #  drawText(qPoint(x+r, y+r+4), '*')
            
        if showChargeSymbols:  
          if charge:
            painter.setFont(smallFont)
             
            if charge == -1:
              text = '-'
              if skeletalColor:
                color = NEG_COLOR
   
            elif charge == 1:
              if skeletalColor:
                color = POS_COLOR
              text = '+'
   
            elif charge > 0:
              if skeletalColor:
                color = POS_COLOR
              text = '%d+' % charge
   
            else:
              if skeletalColor:
                color = NEG_COLOR
              text = '%d-' % abs(charge)
   
            if skeletalColor:
              painter.setPen(CHARGE_BG_COLOR)
            if self.rightBond:
              painter.setPen(color)
              drawText(qPoint(x-r-3, y-r+3), text)
            else:
              painter.setPen(color)
              drawText(qPoint(x+r-3, y-r+3), text)
      
    else:
      
      fontMetric = QtGui.QFontMetricsF(painter.font())
      bbox = fontMetric.tightBoundingRect(elem)
      h2 = bbox.height()/2.0
      w2 = bbox.width()/2.0

      if elem == LINK:
        angles = atom.getBondAngles() + atom.freeValences
      
        if angles:
          startAngle = -1.0 * angles[0]
          angles = [startAngle + (i*2*PI/3.0) for i in (0,1,2)]

          if self.selected:
            painter.setPen(HIGHLIGHT)
            poly = qPoly()
            for angle in angles:
              x2 = x+(r+1)*sin(angle)
              y2 = y-(r+1)*cos(angle)
              poly.append(qPoint(x2, y2))
   
            drawPoly(poly)
            painter.setPen(Qt.black)


          poly = qPoly()
          for angle in angles:
            x2 = x+r*sin(angle)
            y2 = y-r*cos(angle)
            poly.append(qPoint(x2, y2))

          drawPoly(poly)
              
         
      else:
        if self.selected:
          painter.setPen(HIGHLIGHT)
          drawEllipse(center, r+1, r+1)
          painter.setPen(Qt.black)

        
        drawEllipse(center, r, r)
        textPoint = qPoint(x-w2, y+h2)
        drawText(textPoint, elem)
      
        charge = atom.charge
        
        if showChiralities:
          if atom.chirality and atom.chirality not in ('e', 'z', 'E', 'Z'):
            painter.setFont(CHIRAL_FONT)
            painter.setPen(CHIRAL_COLOR)
            chirality = atom.chirality
            
            if chirality in ('r', 's'):
              chirality = '(%s)' % chirality.upper()
            
            fontMetric = QtGui.QFontMetricsF(painter.font())
            width = fontMetric.width(chirality)
            height = fontMetric.height()
            chiralityX = x + (r2+1)*cos(angle) - width/2
            chiralityY = y + (r2+1)*sin(angle) + height/2
            drawText(qPoint(chiralityX, chiralityY), chirality)
          
          #elif atom.stereo:
          #  painter.setFont(CHIRAL_FONT)
          #  painter.setPen(CHIRAL_COLOR)
          #  drawText(qPoint(x+r, y+r+4), '*')
            
        if showChargeSymbols:
          if charge:
             
            if charge == -1:
              text = '-'
              color = NEG_COLOR
   
            elif charge == 1:
              color = POS_COLOR
              text = '+'
   
            elif charge > 0:
              color = POS_COLOR
              text = '%d+' % charge
   
            else:
              color = NEG_COLOR
              text = '%d-' % abs(charge)
   
            painter.setFont(CHARGE_FONT)
            painter.setPen(CHARGE_BG_COLOR)
            drawText(qPoint(x+r-2, y-r+2), text)
            drawText(qPoint(x+r-4, y-r+4), text)
            drawText(qPoint(x+r-2, y-r+4), text)
            drawText(qPoint(x+r-4, y-r+2), text)
            painter.setPen(color)
            drawText(qPoint(x+r-3, y-r+3), text)
               
    self.highlights = set()

class BondItem(QtWidgets.QGraphicsItem):

  def __init__(self, scene, compoundView, bond):
    
    QtWidgets.QGraphicsItem.__init__(self)
    self.scene = scene
     
    compoundView.bondItems[bond] = self
   
    effect = QtWidgets.QGraphicsDropShadowEffect(compoundView)
    effect.setBlurRadius(SHADOW_RADIUS)
    effect.setColor(SHADOW_COLOR)
    effect.setOffset(*SHADOW_OFFSET)
    
    #self.setGraphicsEffect(effect)
    #self.setFlag(ItemIsSelectable)
    #self.setFlag(ItemIsMovable)

    #self.setCacheMode(self.NoCache)
    self.setAcceptedMouseButtons(Qt.LeftButton)
    self.selected = False
    self.setZValue(-2)
    
    self.compoundView = compoundView
    self.bond = bond
    self.atomItems = []
    self.setCacheMode(self.DeviceCoordinateCache)
    
    self.drawData = ()
    self.bbox = NULL_RECT
    
    self.syncToBond()
  
  def delete(self):
  
    for atomItem in self.atomItems:
      atomItem.bondItems.remove(self)
  
    compoundView = self.compoundView
    del compoundView.bondItems[self.bond]
    
    compoundView.scene.removeItem(self)

    self.bond.deleteAll()
    del self

  
  def select(self):
    
    self.selected = True
    self.update()
  
  def deselect(self):
  
    self.selected = False
    self.update()
  
  def syncToBond(self):
  
    bond = self.bond
    
    atomA, atomB = bond.varAtoms
    
    atomDict = self.compoundView.atomViews
    self.atomItems = [atomDict[atomA], atomDict[atomB]]
    
    for atomItem in self.atomItems:
      if self not in atomItem.bondItems:
        atomItem.bondItems.append(self)
    
    xa, ya, za = atomA.coords
    xb, yb, zb = atomB.coords
    
    # Model curation
      
    dx = xb-xa
    dy = yb-ya
    dz = zb-za
    
    angleA = atan2(dx, -dy)
    
    xg = BOND_SEP * cos(angleA)
    yg = BOND_SEP * sin(angleA)
    
    if atomA.isLabile or atomB.isLabile:
      isLabile = True
      if self.compoundView.showChargeSymbols:
        style = Qt.DashLine
      else:
        style = Qt.SolidLine
    else:
      isLabile = False
      style = Qt.SolidLine
    
    stereoA = atomA.stereo
    stereoB = atomB.stereo
    if stereoA or stereoB:
      if stereoA: # if they both are...
        zbase = 0
        index = stereoA.index(atomB)
        nStereo = len(stereoA)
      else:
        zbase = 1  
        index = stereoB.index(atomA)
        nStereo = len(stereoB)
      
      if 3 < nStereo < 8:
        zstep = BOND_STEREO_DICT[nStereo][index]
      else:
        zstep = 0 
      
    else:
      zstep = 0
      zbase = 0
    
    direction = self.bond.direction
    if direction:
      if direction is atomA:
        direct = 0
      else:
        direct = 1
          
    else:
      direct = None
    
    # Geometry
    
    # Set global position using first point
    self.setPos(QPointF(xa, ya))
   
    # Draw local relative to origin
    self.drawData = (style, dx, dy, xg, yg, zstep, zbase, direct)
    
    # Setup render coords
    
    nLines = int(BOND_TYPE_VALENCES[bond.bondType])
    pad = 2.0 * BOND_SEP * (nLines - 1.0) + 0.75
    
    if zstep:
      pad += BOND_SEP/2
    
    if direct is not None:
      pad += BOND_SEP*2
    
    rect = QRectF(QPointF(0.0, 0.0),
                  QPointF(dx, dy))
    
                         
    self.bbox = rect.normalized().adjusted(-pad, -pad, pad, pad)
    
    self.update()
    
  def boundingRect(self):
    
    #if self.compoundView.showSkeletalFormula:
      #for atom in self.bond.varAtoms:
        #if atom.element == 'H':
          #for n in atom.neighbours:
            #if n.element != 'C':
              #return NULL_RECT
    return self.bbox

  def getDistToBond(self, pos):
    
    xm = pos.x()
    ym = pos.y()
    
    atomItemA, atomItemB = self.atomItems
    pos = atomItemA.pos()
    xa = pos.x()
    ya = pos.y()
    
    pos = atomItemB.pos()
    xb = pos.x()
    yb = pos.y()
    
    xb -= xa
    yb -= ya
    
    lb = hypot(xb,yb)
    
    xb /= lb
    yb /= lb
        
    xm -= xa
    ym -= ya
    
    dp = xb*xm + yb*ym
    
    xb *= dp
    yb *= dp
    
    xb -= xm
    yb -= ym
    
    r = hypot(xb,yb)
     
    return r
  
  def mousePressEvent(self, event):
    
    selected = list(self.compoundView.selectedViews)
     
    mods = event.modifiers()
    button = event.button()
    haveCtrl = mods & Qt.CTRL
    haveShift = mods & Qt.SHIFT
    
    if self.getDistToBond(self.mapToScene(event.pos())) > 8:
      return
    
    atomItemA, atomItemB = self.atomItems

    if haveCtrl or haveShift:
      if atomItemA.selected and atomItemB.selected:
        atomItemA.deselect()
        atomItemB.deselect()
      else:
        atomItemA.select()
        atomItemB.select()
    
    elif not (atomItemA.selected and atomItemB.selected):
      for view in selected:
        view.deselect()
      atomItemA.select()
      atomItemB.select()

    atomItemA.update()
    atomItemB.update()
 
    QtWidgets.QGraphicsItem.mousePressEvent(self, event)
  
  def mouseDoubleClickEvent(self, event):
    
    bond = self.bond
    
    if bond.bondType == 'aromatic':
      return
    
    if self.getDistToBond(self.mapToScene(event.pos())) > 8:
      return
    
    varAtom1, varAtom2 = bond.varAtoms
    
    atomA = varAtom1.atom
    atomB = varAtom2.atom
    
    for var in bond.compound.variants:
      
      varAtomA = var.atomDict.get(atomA)
      varAtomB = var.atomDict.get(atomB)
      
      if varAtomA and varAtomB: 
        common = varAtomA.bonds & varAtomB.bonds
        if common:
          bond = common.pop()
          self.compoundView.parent.addToHistory()
          
          if varAtomA.freeValences and varAtomB.freeValences:
            bond.setBondType( BOND_CHANGE_DICT[bond.bondType] )
            varAtomA.updateValences()
            varAtomB.updateValences()
            
          elif bond.bondType in ('double','triple','quadruple'):
            bond.setBondType( 'single' )
            varAtomA.updateValences()
            varAtomB.updateValences()
            
            
    if self.compoundView.autoChirality:
      varAtom1.autoSetChirality()
      varAtom2.autoSetChirality()
     
    self.compoundView.updateAll()
     
  def paint(self, painter, option, widget):
    
    if not self.drawData:
      return

    qPoly = QtGui.QPolygonF

    if self.selected:
      color = HIGHLIGHT
    elif isinstance(self.compoundView, QtWidgets.QGraphicsItem):
      # SpecView
      if self.compoundView.container:
        color = QtGui.QColor(*self.glWidget._hexToRgba(self.compoundView.container.mainApp.colors[1]))
      # Analysis
      elif self.compoundView.glWidget:
        backgroundColor = QtGui.QColor()
        backgroundColor.setRgbF(*self.glWidget._hexToRgba(self.glWidget.spectrumWindow.analysisProfile.bgColor))
        color = inverseGrey(backgroundColor)
      # Fallback
      else:
        color = Qt.black
    else:
      color = Qt.black
    
    style, dx, dy, xg, yg, zstep, zbase, direct = self.drawData
    bondType = self.bond.bondType
    drawLine = painter.drawLine

    pen = QtGui.QPen(color, 1.5, style)
    painter.setPen(pen)
    
    #if self.compoundView.showSkeletalFormula:
      #for atom in self.bond.varAtoms:
        #if atom.element == 'H':
          #for n in atom.neighbours:
            #if n.element != 'C':
              #return
    
    if bondType in ('single','dative'):
      if bondType == 'dative':
        xindent = 3.5*yg
        yindent = -3.5*xg
 
        if direct:
          x1 = dx-xindent*1.5
          y1 = dy-yindent*1.5
          x0 = y0 = 0.0
 
        else:
          x0 = xindent*1.5
          y0 = yindent*1.5
          x1 = dx
          y1 = dy
 
      else:
        x0 = y0 = 0.0
        x1 = dx
        y1 = dy
        
      if zstep:
        drawPoly = painter.drawPolygon
        dashPattern = [0.33, 0.5]
        
        if zbase == 0: # A basis
          if zstep < 0:
            # dashed line
            pen = QtGui.QPen(color, 4.5, Qt.DotLine)
            pen.setDashPattern(dashPattern)
            pen.setCapStyle(Qt.FlatCap)
            painter.setPen(pen)
            
            drawLine(QPointF(x0, y0),
                     QPointF(x1, y1))

          else: #
            # solid triangle, points at B
            pen = QtGui.QPen(color, 0.5, Qt.SolidLine)
            painter.setPen(pen)
            painter.setBrush(color)
            p1 = QPointF(dx+xg, dy+yg)
            p2 = QPointF(dx-xg, dy-yg)
            p3 = QPointF(x0, x0)
            
            drawPoly(qPoly([p1,p2,p3]))
          
        else: # B basis
          if zstep < 0: 
            # dashed line
            pen = QtGui.QPen(color, 4.5, Qt.DotLine)
            pen.setDashPattern(dashPattern)
            pen.setCapStyle(Qt.FlatCap)
            painter.setPen(pen)
            
            drawLine(QPointF(x0, y0),
                     QPointF(x1, y1))
         
          else: 
            # solid triangle, points at A
            pen = QtGui.QPen(color, 0.5, Qt.SolidLine)
            painter.setPen(pen)
            painter.setBrush(color)
            p1 = QPointF( xg,  yg)
            p2 = QPointF(-xg, -yg)
            p3 = QPointF(x1, y1)
            
            drawPoly(qPoly([p1,p2,p3]))
         
      else:
        drawLine(QPointF(x0, y0),
                 QPointF(x1, y1))
                 
      if bondType == 'dative':
        drawPoly = painter.drawPolygon
        pen = QtGui.QPen(color, 0.5, Qt.SolidLine)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(color)
 
        if direct:
          xc = dx-xindent
          yc = dy-yindent
          p1 = QPointF(xc-xindent+2*xg, yc-yindent+2*yg)
          p2 = QPointF(xc-xindent-2*xg, yc-yindent-2*yg)
          p3 = QPointF(xc, yc)
 
        else:
          xc = xindent
          yc = yindent
          p1 = QPointF(xc+xindent+2*xg, yc+yindent+2*yg)
          p2 = QPointF(xc+xindent-2*xg, yc+yindent-2*yg)
          p3 = QPointF(xc, yc)
 
        drawPoly(qPoly([p1,p2,p3]))
 
    
    elif bondType == 'double':

      drawLine(QPointF( xg,  yg),
               QPointF(dx+xg, dy+yg))
      drawLine(QPointF(-xg, -yg),
               QPointF(dx-xg, dy-yg))
               
    elif bondType == 'aromatic':
      drawLine(QPointF(0, 0),
               QPointF(dx, dy))
    
    elif bondType == 'singleplanar':
      drawLine(QPointF(0, 0),
               QPointF(dx, dy))

    elif bondType == 'triple':
      drawLine(0.0, 0.0, dx, dy)
      xg *= 2.0
      yg *= 2.0
      drawLine(QPointF( xg,  yg),
               QPointF(dx+xg, dy+yg))
      drawLine(QPointF(-xg, -yg),
               QPointF(dx-xg, dy-yg))
    
    elif bondType == 'quadruple':
      drawLine(QPointF( xg,  yg),
               QPointF(dx+xg, dy+yg))
      drawLine(QPointF(-xg, -yg),
               QPointF(dx-xg, dy-yg))
      xg *= 3.0
      yg *= 3.0
      drawLine(QPointF( xg,  yg),
               QPointF(dx+xg, dy+yg))
      drawLine(QPointF(-xg, -yg),
               QPointF(dx-xg, dy-yg))
