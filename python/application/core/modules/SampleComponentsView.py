__author__ = 'luca'

from ccpncore.gui.Label import Label
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.ScrollArea import ScrollArea
from PyQt4 import QtGui, QtCore
from ccpncore.gui.CompoundView import CompoundView, Variant, importSmiles


from functools import partial
from ccpncore.gui.InputDialog import askString
Qt = QtCore.Qt
Qkeys = QtGui.QKeySequence



class SampleComponentsView(QtGui.QWidget):

  def __init__(self, parent=None, project=None, callback=None, selectedList=None):

    QtGui.QWidget.__init__(self, parent)

    self.project = project
    self.samples = project.samples
    self.compound = None
    self.variant = None
    self.smiles = ''
    self.smileList = []
    self.regioncount = 0
    self.colourScheme = self.project._appBase.preferences.general.colourScheme

    self.scrollArea = ScrollArea(self)
    self.scrollArea.setStyleSheet(""" background-color:  transparent; """)
    self.scrollArea.setWidgetResizable(True)
    self.scrollAreaWidgetContents = QtGui.QWidget()
    # self.scrollAreaWidgetContents.setMaximumWidth(700)
    # self.scrollAreaWidgetContents.setMinimumWidth(700)
    self.scrollArea.setWidget(self.scrollAreaWidgetContents)

    self.layout().addWidget(self.scrollArea, 3, 0, 1, 5)

    labelSelectSample = Label(self, ' Select Mixture:', grid=(0, 0), hAlign='r')
    self.SamplePulldown = PulldownList(self, grid=(0, 1), callback=self.showMolecule)
    dataSamplePuldown = [sample.pid for sample in self.samples]
    self.SamplePulldown.setData(dataSamplePuldown)


  def showMolecule(self, selection):

    for sample in self.project.samples:
      if sample.pid  == selection:

        for components in sample.sampleComponents:
          smile = components.substance.smiles
          self.smileList.append(smile)
          self.testName = components.substance.name

        valueCount = (len(sample.spectra))
        self.positions = [i for i in range(valueCount)]


        for smile, self.position in zip( self.smileList, self.positions):
          self.compoundView = CompoundView(self.scrollAreaWidgetContents, grid=(1, self.position))
          self.chemicalName = Label(self.scrollAreaWidgetContents, text=str(smile), grid=(0, self.position))
          self.smiles = smile
          compound = importSmiles(smile)
          variant = list(compound.variants)[0]
          self.setCompound(compound, replace = True)
          x, y = self.getAddPoint()
          variant.snapAtomsToGrid(ignoreHydrogens=False)
          self.compoundView.centerView()
          self.compoundView.updateAll()
          self.compoundView.setGeometry(0, 0, 350, 350)
          self.compoundView.setMaximumWidth(350)
          if self.colourScheme == 'dark':
            self.compoundView.setStyleSheet(""" background-color:  #0E1A3D;""")
          else:
            self.compoundView.setStyleSheet(""" background-color:  #EDCF83;""")

  def setCompound(self, compound, replace=True):

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
