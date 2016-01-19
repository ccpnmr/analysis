__author__ = 'luca'

from PyQt4 import QtCore, QtGui
from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.Base import Base
from ccpncore.gui.ScrollArea import ScrollArea
from ccpncore.gui.Table import ObjectTable, Column
from ccpncore.gui.CompoundView import CompoundView, Variant, importSmiles
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.Label import Label

pullDown1 = ["PQN"]
pullDown2 = ["Pareto Scale"]
#
class MetabolomicsModule(CcpnDock, Base):
  def __init__(self, project, **kw):
    super(MetabolomicsModule, self)
    CcpnDock.__init__(self, name='Metabolomics')
    self.project = project
    self.smiles = ''
    self.compound = None
    self.variant = None
    self.colourScheme = self.project._appBase.preferences.general.colourScheme

  # 1st Area:
    self.metaboliteArea = ScrollArea(self)
    self.setOrientation('vertical', force=True)
    self.metaboliteArea.setWidgetResizable(True)
    self.metaboliteArea.setMaximumSize(400,900)
    self.metaboliteAreaWidget = QtGui.QWidget()
    self.metaboliteArea.setWidget(self.metaboliteAreaWidget)
    self.layout.addWidget(self.metaboliteArea, 0, 0, 9, 1)
    self.metaboliteArea.setStyleSheet("border-style: outset; border-width: 1px; border-color: beige;""border-radius: 1px;")


  # widget 1st Area: HACKED to create the module mock
    self.listOfMetabolites = []
    for sample in self.project.samples:
        sampleComponents = [metabolite for metabolite in sample.sampleComponents]
        for sc in sampleComponents:
          self.listOfMetabolites.append(sc.substance)

    columns = [Column('Metabolite', ''),
               Column('Concentration',''),
               Column('Error', '')]


    self.metaboliteTable = ObjectTable(self.metaboliteAreaWidget, columns,callback=self.showMolecule,  grid=(0, 0))
    self.metaboliteTable.setObjects(self.listOfMetabolites)
    self.compoundView  = CompoundView(self.metaboliteAreaWidget,  grid=(2, 0))




  def showMolecule(self, row:int=None, col:int=None, obj:object=None):

    objectTable = self.metaboliteTable
    metabolite = objectTable.getCurrentObject()

    smiles = metabolite.smiles
    self.smiles = smiles
    compound = importSmiles(smiles)
    variant = list(compound.variants)[0]
    self.setCompound(compound, replace = True)
    x, y = self.getAddPoint()
    variant.snapAtomsToGrid(ignoreHydrogens=False)
    self.compoundView.centerView()
    self.compoundView.updateAll()
    if self.colourScheme == 'dark':
      self.compoundView.setStyleSheet(""" background-color:  #040000;""")
    else:
      self.compoundView.setStyleSheet(""" background-color:  #A9BCF5;""")

  def setCompound(self, compound, replace=True):
    ''' Set the compound on the graphic scene. '''
    if compound is not self.compound:
      if replace or not self.compound:
        self.compound = compound
        variants = list(compound.variants)
        if variants:
          for variant2 in variants:
            if (variant2.polyLink == 'none') and (variant2.descriptor == 'neutral'):
              variant = variant2
              break
          else:
            for variant2 in variants:
              if variant2.polyLink == 'none':
                variant = variant2
                break
            else:
              variant = variants[0]
        else:
          variant =  Variant(compound)
          print(variant)
        self.variant = variant
        self.compoundView.setVariant(variant)

      else:
        variant = list(compound.variants)[0]
        x, y = self.getAddPoint()
        self.compound.copyVarAtoms(variant.varAtoms, (x,y))
        self.compoundView.centerView()
        self.compoundView.updateAll()

  def getAddPoint(self):
    ''' Set the compound on the specific position on the graphic scene. '''
    compoundView = self.compoundView
    globalPos = QtGui.QCursor.pos()
    pos = compoundView.mapFromGlobal(globalPos)
    widget = compoundView.childAt(pos)
    if widget:
      x = pos.x()
      y = pos.y()
    else:
      x = compoundView.width()/2.0
      y = compoundView.height()/2.0
    point = compoundView.mapToScene(x, y)
    return point.x(), point.y()

