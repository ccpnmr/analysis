__author__ = 'luca'

from PyQt4 import QtCore, QtGui, QtSvg
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.InputDialog import askString
from ccpncore.gui.Label import Label
from ccpncore.gui.ScrollArea import ScrollArea
from ccpncore.gui.Button import Button
from ccpnmrcore.modules.GuiTableGenerator import GuiTableGenerator
from ccpncore.gui.Table import ObjectTable, Column
from ccpncore.gui.CompoundView import CompoundView, Variant, importSmiles


class PeakListSampleComponent(QtGui.QWidget):

  def __init__(self, parent=None, project=None, callback=None):

    QtGui.QWidget.__init__(self, parent)
    self.project = project
    self.peakLists = project.peakLists
    self.samples = project.samples
    self.compound = None
    self.variant = None
    self.smiles = ''

    dataPulldownSample = [sample.pid for sample in self.samples]
    if not project.peakLists:
      peakLists = []

    ##### Set Sample pulldown #####
    labelSelectSample = Label(self, ' Select Mixture:', grid=(1, 1), hAlign='l')
    self.samplePulldown = PulldownList(self, grid=(1, 2), callback=self.pulldownSample)
    self.samplePulldown.setData(dataPulldownSample)

    ##### Set Components PL  pulldown #####
    labelSelectComponent = Label(self, 'Select Substance:')
    self.layout().addWidget(labelSelectComponent, 1, 3, QtCore.Qt.AlignRight)
    self.peakListPulldown = PulldownList(self, grid=(1, 4), callback= self.showPLOnTable)

    compoundView = CompoundView(self, grid=(3,0), gridSpan=(3,2))
    self.compoundView = compoundView

    self.peakListObjects = []

    columns = [Column('#', 'serial'),
               Column('Position', lambda peak: '%.3f' % peak.position[0] ),
               Column('Height', lambda peak: self._getPeakHeight(peak))]

    self.peakTable = ObjectTable(self, columns, callback=self.callback, objects=[], grid=(3,2), gridSpan=(3,3))
    self.colourScheme = self.project._appBase.preferences.general.colourScheme
    if self.colourScheme == 'dark':
      self.compoundView.setStyleSheet(""" background-color:  #0E1A3D;""")
    else:
      self.compoundView.setStyleSheet(""" background-color:  #EDCF83;""")

  def pulldownSample(self, selection):

    for sample in self.project.samples:
      if sample.pid  == selection:
        substanceList = []
        pidPl = [peakList.pid for spectrum in sample.spectra for peakList in spectrum.peakLists]
        self.peakListPulldown.setData(pidPl)


  def showPLOnTable(self, selection):

    for sample in self.project.samples:
      for spectrum in sample.spectra:
          for peakList in spectrum.peakLists:
            pl = peakList.pid
            if selection == pl:
              peakLs = peakList.peaks
              self.peakListObjects.append(peakLs)
              self.peakTable.setObjects(self.peakListObjects[-1])
              peak = self.project.getByPid(selection)
              self.selection = peak
              sampleComponents = peak.spectrum.sample.sampleComponents
              for sampleComponent in sampleComponents:
                selectionOfPeaks = sampleComponent.substance.referenceSpectra[0].peakLists[0]
                if self.selection == selectionOfPeaks:
                  smile = sampleComponent.substance.smiles
                  self.smiles = smile
                  compound = importSmiles(smile)
                  variant = list(compound.variants)[0]
                  self.setCompound(compound, replace = True)
                  x, y = self.getAddPoint()
                  variant.snapAtomsToGrid(ignoreHydrogens=False)
                  self.compoundView.centerView()
                  # self.compoundView.resetView()
                  self.compoundView.updateAll()

  def _getPeakHeight(self, peak):
    if peak.height:
      return peak.height*peak.peakList.spectrum.scale

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

  def callback(self):
    print('Not implemented yet')