__author__ = 'luca'

from ccpncore.gui.Label import Label
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.ScrollArea import ScrollArea
from PyQt4 import QtGui, QtCore
from ccpncore.gui.CompoundView import CompoundView, Variant, importSmiles



class SampleComponentsView(QtGui.QWidget):

  def __init__(self, parent=None, project=None, callback=None, selectedList=None):
    ''' Visualise all the molecule structure present in a mixture. '''

    QtGui.QWidget.__init__(self, parent)

    self.project = project
    self.samples = project.samples
    self.compound = None
    self.variant = None
    self.smiles = ''
    # self.smileList = []
    # self.chemicalNameList = []
    self.regioncount = 0
    self.colourScheme = self.project._appBase.preferences.general.colourScheme

    self.scrollArea = ScrollArea(self)
    self.scrollArea.setStyleSheet(""" background-color:  transparent; """)
    self.scrollArea.setWidgetResizable(True)
    self.scrollAreaWidgetContents = QtGui.QWidget()
    self.scrollArea.setWidget(self.scrollAreaWidgetContents)

    self.layout().addWidget(self.scrollArea, 3, 0, 1, 5)

    labelSelectSample = Label(self, ' Select Mixture:', grid=(0, 0), hAlign='r')
    self.SamplePulldown = PulldownList(self, grid=(0, 1), callback=self.showMolecule)
    dataSamplePuldown = [sample.pid for sample in self.samples]
    self.SamplePulldown.setData(dataSamplePuldown)

  def showMolecule(self, selection):
    ''' Fill the pulldown with the mixture names. If selected will create and display the molecule structure from smiles '''

    for sample in self.project.samples:

      if sample.pid  == selection:
        self.smileList = []
        self.chemicalNameList = []

        for components in sample.sampleComponents:
          smile = components.substance.smiles
          chemicalName = (''.join(str(x) for x in components.substance.synonyms))
          self.chemicalNameList.append(chemicalName)
          self.smileList.append(smile)

        # valueCount = (len(sample.spectra))
        valueCount = (len(sample.sampleComponents))
        self.positions = [i for i in range(valueCount)]

        for smile, name, self.position in zip( self.smileList, self.chemicalNameList, self.positions):
          self.compoundView = CompoundView(self.scrollAreaWidgetContents, grid=(1, self.position), preferences=self.project._appBase.preferences.general)
          self.chemicalName = Label(self.scrollAreaWidgetContents, grid=(0, self.position), hAlign='c')
          self.chemicalName.setText(name)
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
        self.compoundView.resetView()
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


