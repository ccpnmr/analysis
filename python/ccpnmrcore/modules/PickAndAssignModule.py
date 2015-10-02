__author__ = 'simon1'

from ccpncore.gui.Button import Button
from ccpncore.gui.Base import Base
from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.Label import Label
from ccpnmrcore.modules.PeakTable import PeakListSimple
from ccpnmrcore.modules.NmrResidueTable import NmrResidueTable
from ccpnmrcore.popups.SelectDisplaysPopup import SelectDisplaysAndSpectraPopup

from ccpnmrcore.lib.Window import navigateToPeakPosition, navigateToNmrResidue

class PickAndAssignModule(CcpnDock, Base):

  def __init__(self, parent=None, project=None):

    CcpnDock.__init__(self, parent=None, name='Pick And Assign')
    spacingLabel = Label(self)
    spacingLabel.setFixedHeight(15)
    self.layout.addWidget(spacingLabel, 0, 1, 1, 1)

    self.restrictedPickButton = Button(self, text='Restricted Pick', callback=self.restrictedPick)
    self.layout.addWidget(self.restrictedPickButton, 1, 2, 1, 1)

    self.project = project
    self.current = project._appBase.current
    # self.peakTable = PeakListSimple(self, project=project, callback=self.goToPositionInModules)
    self.nmrResidueTable = NmrResidueTable(self, project=project, callback=self.goToPositionInModules)
    self.layout.addWidget(spacingLabel, 2, 1, 1, 1)

    self.layout.addWidget(self.nmrResidueTable, 4, 0, 1, 4)
    # self.moreButton = Button(self, "More...", callback=self.showNmrResiduePopup)
    # self.layout.addWidget(self.moreButton, 5, 0, 1, 1)

    # parent.window().showAtomSelector()

  def restrictedPick(self):
    # position = self.selectedPeak.position
    # axisCodes = self.selectedPeak.peakList.spectrum.axisCodes
    if not self.current.nmrResidue:
      print('No current nmrResidue')
      return
    else:
      nmrResidueIsotopeCodes = [atom.isotopeCode for atom in self.current.nmrResidue.nmrAtoms]
      for module in self.project.spectrumDisplays:
        # if len(module.strips[0].orderedAxes) > 2:
        for spectrumView in module.strips[0].spectrumViews:
          if spectrumView.isVisible():
            spectrum = spectrumView.spectrum
            shiftList = spectrum.chemicalShiftList
            nmrResidueShifts = [shiftList.getChemicalShift(nmrAtom.id).value for nmrAtom in self.current.nmrResidue.nmrAtoms]
            shiftDict = dict(zip(nmrResidueIsotopeCodes, nmrResidueShifts))

            selectedRegion = [['']*len(module.axisCodes), ['']*len(module.axisCodes)]
            spectrumViewIsotopeCodes = spectrumView.spectrum.isotopeCodes

            for isotopeCode in spectrumViewIsotopeCodes:
              if isotopeCode in nmrResidueIsotopeCodes:
                index = spectrum.isotopeCodes.index(isotopeCode)
                if spectrum.assignmentTolerances[index] is None:
                  tolerance = spectrum.spectralWidths[index]/spectrum.pointCounts[index]
                  spectrumTolerances = list(spectrum.assignmentTolerances)
                  spectrumTolerances[index] =  tolerance
                  spectrum.assignmentTolerances = spectrumTolerances
                selectedRegion[0][index] = shiftDict[isotopeCode]-spectrum.assignmentTolerances[index]
                selectedRegion[1][index] = shiftDict[isotopeCode]+spectrum.assignmentTolerances[index]

              else:
                index3 = spectrumViewIsotopeCodes.index(isotopeCode)
                selectedRegion[0][index3] = spectrumView.strip.orderedAxes[index3].region[0]
                selectedRegion[1][index3] = spectrumView.strip.orderedAxes[index3].region[1]

            peakList = spectrumView.spectrum.peakLists[0]
            if spectrumView.spectrum.dimensionCount > 1:
              apiSpectrumView = spectrumView._wrappedData
              peakList.pickPeaksNd(selectedRegion, apiSpectrumView.spectrumView.orderedDataDims,
                                              doPos=apiSpectrumView.spectrumView.displayPositiveContours,
                                              doNeg=apiSpectrumView.spectrumView.displayNegativeContours)
            for strip in module.strips:
              strip.showPeaks(peakList)


  def goToPositionInModules(self, nmrResidue=None, row=None, col=None):
    navigateToNmrResidue(self.project, nmrResidue, markPositions=True)
    self.current.nmrResidue = nmrResidue

  def showNmrResiduePopup(self):
    from ccpnmrcore.popups.NmrResiduePopup import NmrResiduePopup
    NmrResiduePopup(self, self.project).exec_()


