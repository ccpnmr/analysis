from PyQt4 import QtCore, QtGui, QtSvg
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.InputDialog import askString
from ccpncore.gui.Label import Label
from ccpncore.gui.ScrollArea import ScrollArea
from ccpncore.gui.Button import Button


from ccpnmrcore.modules.GuiTableGenerator import GuiTableGenerator

from ccpncore.gui.CompoundView import CompoundView, Variant, importSmiles


from functools import partial

Qt = QtCore.Qt
Qkeys = QtGui.QKeySequence


class PeakListSampleComponent(QtGui.QWidget):

  def __init__(self, parent=None, project=None, callback=None):

    QtGui.QWidget.__init__(self, parent)
    self.project = project
    self.peakLists = project.peakLists
    self.samples = project.samples

    self.compound = None
    self.variant = None
    self.smiles = ''

    QtGui.QShortcut(Qkeys("Ctrl+S"), self, self.addSmiles)



    dataPulldownSample = [sample.pid for sample in self.samples if len(sample.spectra) > 1]


    if not project.peakLists:
      peakLists = []

    ##### Set Sample pulldown #####
    labelSelectSample = Label(self, ' Select Mixture:', grid=(1, 0), hAlign='l')
    self.samplePulldown = PulldownList(self, grid=(1, 1), callback=self.pulldownSample)
    self.samplePulldown.setData(dataPulldownSample)

    ##### Set Components PL  pulldown #####
    labelSelectComponent = Label(self, 'Select Substance:')
    self.layout().addWidget(labelSelectComponent, 1, 2, QtCore.Qt.AlignRight)
    self.peakListPulldown = PulldownList(self, grid=(1, 3), callback= self.pulldownSample)


    ##### Set moleculeview  pulldown #####
    # self.showMoleculeButton = Button(self, text="Show molecule 3D", grid=(2, 1))
    # self.showMoleculeButton.clicked.connect(self.showMolecule)
    #
    dataPulldownSampleView = [sample.pid for sample in self.samples if len(sample.spectra) < 2]
    labelSelectSampleView = Label(self, ' Select molecule to display:', grid=(1, 4), hAlign='l')
    self.samplePulldownView = PulldownList(self, grid=(1, 5), callback=self.showMolecule)
    self.samplePulldownView.setData(dataPulldownSampleView)


    #### set  layout only
    self.scrollArea = ScrollArea(self)
    self.scrollArea.setWidgetResizable(True)
    self.scrollAreaWidgetContents = QtGui.QWidget()
    self.scrollArea.setWidget(self.scrollAreaWidgetContents)
    self.layout().addWidget(self.scrollArea, 3, 0, 1, 2)
    # self.scrollArea.hide()
    compoundView = CompoundView(self.scrollAreaWidgetContents)
    self.compoundView = compoundView




  def pulldownSample(self, selection):

    for sample in self.project.samples:


      if sample.pid  == selection:

          pidPl = [peakList.pid for spectrum in sample.spectra for peakList in spectrum.peakLists]
          self.peakListPulldown.setData(pidPl)

          listofPLobjects = []    #this because the peakTable needs to have a list of objects on the selector(pulldown)
          for spectrum in sample.spectra:

            for peakListObject in spectrum.peakLists:
              listofPLobjects.append(peakListObject)

              ##### Set Peak List Table #######
              columns = [('#', 'serial'), ('Height', lambda pk: self._getPeakHeight(pk))]
              tipTexts=['Peak serial number', 'Magnitude of spectrum intensity at peak center (interpolated), unless user edited']
              self.peakTable = GuiTableGenerator(self, objectLists=listofPLobjects, callback=self.highLightAtom, columns=columns,
                                      selector=self.peakListPulldown,  tipTexts=tipTexts)#selectorCallback=None,
              # self.peakTable.selector.setCallback(self.peakTable)
              self.layout().addWidget(self.peakTable, 3, 2, 2, 4)



  def _getPeakHeight(self, peak):
    if peak.height:
      return peak.height*peak.peakList.spectrum.scale


  def highLightAtom(self):
    print('Not implemented yet')
  #
  # def updateTableAndWidget(self, peakTable, item):
  #   peakTable.updateSelectorContents()
  #   peakList = self.project.getByPid(peakTable.selector.currentText())

    # sample = peakList.spectrum.sample

    # for sample in  self.project.samples:
    #   if len(sample.spectra) < 2:
    #     print(sample)
    #
    # smilesString = sample.comment
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


  ########## Setting to create 2D molecules from smiles

  def showMolecule(self, selection):
    for sample in self.project.samples:
      if sample.pid  == selection:
        smilesString = sample.comment

        if smilesString:
          self.smiles = smilesString
          compound = importSmiles(smilesString)
          variant = list(compound.variants)[0]
          self.setCompound(compound, replace = True)
          x, y = self.getAddPoint()
          variant.snapAtomsToGrid(ignoreHydrogens=False)
          self.compoundView.centerView()
          self.compoundView.updateAll()


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

