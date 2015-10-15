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
    QtGui.QShortcut(Qkeys("Ctrl+S"), self, self.addSmiles)

    labelSelectSample = Label(self, ' Select Sample:', grid=(0, 0), hAlign='r')
    self.SamplePulldown = PulldownList(self, grid=(0, 1))
    self.SamplePulldown.setData([sample.pid for sample in project.samples if len(sample.spectra) > 1])

    # labelSelectComponent = Label(self, 'Select Component:', grid=(0, 2), hAlign='r')
    # self.componentsPulldown = PulldownList(self, grid=(0, 3))


    self.scrollArea = ScrollArea(self)
    self.scrollArea.setWidgetResizable(True)
    self.scrollAreaWidgetContents = QtGui.QWidget()
    self.scrollArea.setWidget(self.scrollAreaWidgetContents)
    self.layout().addWidget(self.scrollArea, 3, 0, 1, 5)

    dataPulldownSampleView = [sample.pid for sample in self.samples if len(sample.spectra) < 2]
    labelSelectSampleView = Label(self, ' Select molecule to display:', grid=(0, 2), hAlign='r')
    self.samplePulldownView = PulldownList(self, grid=(0, 3), callback=self.showMolecule)
    self.samplePulldownView.setData(dataPulldownSampleView)

    self.regioncount = 0


  def showMolecule(self, selection):


    valueCount = 2 #for now
    self.positions = [(i+self.regioncount, j) for i in range(valueCount)
                 for j in range(3)]

    for self.position in self.positions:

      compoundView = CompoundView(self.scrollAreaWidgetContents, grid=(self.position))
      self.compoundView = compoundView

    for sample in self.project.samples:
      if sample.pid  == selection:

        pLsamples = [sample.pid for sample in sample.spectra]
        print(len(sample.spectra, 'number'))

        self.samplePulldownView.setData(pLsamples)

        smilesString = sample.comment


        #
        #
        # if smilesString:
        #   self.smiles = smilesString
        #   compound = importSmiles(smilesString)
        #   variant = list(compound.variants)[0]
        #   self.setCompound(compound, replace = True)
        #   x, y = self.getAddPoint()
        #   variant.snapAtomsToGrid(ignoreHydrogens=False)
        #   self.compoundView.centerView()
        #   self.compoundView.updateAll()
        #

  #
  #
  #
  # def setCompound(self, compound, replace=True):
  #
  #   if compound is not self.compound:
  #     if replace or not self.compound:
  #       self.compound = compound
  #       variants = list(compound.variants)
  #       if variants:
  #         for variant2 in variants:
  #           if (variant2.polyLink == 'none') and (variant2.descriptor == 'neutral'):
  #             variant = variant2
  #             break
  #         else:
  #           for variant2 in variants:
  #             if variant2.polyLink == 'none':
  #               variant = variant2
  #               break
  #           else:
  #             variant = variants[0]
  #       else:
  #         variant =  Variant(compound)
  #         print(variant)
  #       self.variant = variant
  #       self.compoundView.setVariant(variant)
  #
  #     else:
  #       variant = list(compound.variants)[0]
  #       x, y = self.getAddPoint()
  #       self.compound.copyVarAtoms(variant.varAtoms, (x,y))
  #       self.compoundView.centerView()
  #       self.compoundView.updateAll()
  #
  #
  # def getAddPoint(self):
  #   compoundView = self.compoundView
  #   globalPos = QtGui.QCursor.pos()
  #   pos = compoundView.mapFromGlobal(globalPos)
  #   widget = compoundView.childAt(pos)
  #
  #   if widget:
  #     x = pos.x()
  #     y = pos.y()
  #
  #   else:
  #     x = compoundView.width()/2.0
  #     y = compoundView.height()/2.0
  #
  #   point = compoundView.mapToScene(x, y)
  #
  #   return point.x(), point.y()
  #
  def addSmiles(self):

    prompt = 'Enter SMILES string to add:'
    smilesString = askString('User input', prompt, initialValue=self.smiles, parent=self)

    if smilesString:
      self.smiles = smilesString
      compound = importSmiles(smilesString)
      variant = list(compound.variants)[0]
      self.setCompound(compound, replace = True)
      x, y = self.getAddPoint()
      variant.snapAtomsToGrid(ignoreHydrogens=False)
      self.compoundView.centerView()
      self.compoundView.updateAll()

  #
  #
  #
