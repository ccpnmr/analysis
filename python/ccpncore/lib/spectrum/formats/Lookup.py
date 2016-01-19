from PyQt4 import QtCore, QtGui
import pandas as pd
import csv


def readXls(project, path=None):
  ex = pd.ExcelFile(path)
#   xlsDict = excelSheet.to_dict()
  excelSheet = ex.parse(ex.sheet_names[0])


  # Parse sheet 1
  for spectrumPath, id, expType, smile , molecularMass, numHAtoms,Hacceptor, Hdonor,\
      psa, cLogP, concentration, empiricalFormula, chemicalName, comment,numBonds, numRings\
      in zip(excelSheet['filename'], excelSheet['Id'], excelSheet['expType'],
      excelSheet['smiles'], excelSheet['molecularMass'], excelSheet['numHAtoms'],
      excelSheet['Hacceptor'], excelSheet['Hdonor'],  excelSheet['psa'],
      excelSheet['cLogP'],excelSheet['concentration'],  excelSheet['empiricalFormula'],excelSheet['ChemicalName'],
      excelSheet['comments'], excelSheet['numBonds'], excelSheet['numRings']):

      for spectrum in project.loadData(spectrumPath):
        spectrum.scale = 1
        spectrum.experimentType = expType
        loadInSideBar(project, spectrum)


        newSubstance = project.newSubstance(name=spectrum.name, labeling=str(expType))

        newSubstance.smiles = smile
        newSubstance.referenceSpectra = [spectrum]
        newSubstance.atomCount = int(numHAtoms)
        newSubstance.hBondAcceptorCount = int(Hacceptor)
        newSubstance.hBondDonorCount = int(Hdonor)
        newSubstance.comment = str(comment)
        newSubstance.logPartitionCoefficient = cLogP
        newSubstance.empiricalFormula = str(empiricalFormula)
        newSubstance.molecularMass = molecularMass
        newSubstance.synonyms = str(chemicalName)
        newSubstance.bondCount = int(numBonds)
        newSubstance.ringCount = int(numRings)
        newSubstance.polarSurfaceArea = float(psa)

    # Parse sheet 2.  Create Sample
  if len(ex.sheet_names) > 1:
    excelSheet = ex.parse(ex.sheet_names[1])
    for name, expType, id ,sampleComponent, spectraPath , pH, ionicStrength, amount, amountUnit,\
      creationDate, batchIdentifier, plateIdentifier, rowNumber, columnNumber, comment\
      \
      in zip(excelSheet['name'], excelSheet['expType'], excelSheet['id'],
      excelSheet['sampleComponents'], excelSheet['spectra'],excelSheet['pH'],  excelSheet['ionicStrength'],
      excelSheet['amount'],excelSheet['amountUnit'], excelSheet['creationDate'],
      excelSheet['batchIdentifier'], excelSheet['plateIdentifier'],excelSheet['rowNumber'],
      excelSheet['columnNumber'], excelSheet['comment']):

      sampleSpectra = []
      for i in spectraPath.split(','):
        sampleSpectrum = project.loadData(i)
        sampleSpectrum[0].newPeakList()
        sampleSpectrum[0].experimentType = expType
        sampleSpectra.append(sampleSpectrum[0])

      sample = project.newSample(name=str(id))
      sample.spectra = sampleSpectra
      for sc in sampleComponent.split(','):
        sampleComponent = sample.newSampleComponent(name=(str(sc) +'-1'), labeling='H')

      loadSampleInSideBar(project, sample)




def readCsv(project, path=None):
  csv_in = open(path, 'r')
  reader = csv.reader(csv_in)
  for row in reader:
    if row[0].split('/')[-1] == 'procs':
      filename = row[0].split('/')
      filename.pop()
      filenamePath = '/'.join(filename)
      loadedSpectrum = project.loadData(filenamePath)
      # loadedSpectrum.scale = 0.5
      for spectrum in loadedSpectrum:
        loadInSideBar(project, spectrum)
        # create Sample
        newSample = project.newSample(name=spectrum.pid)
        spectrum.sample = newSample


def loadInSideBar(project, spectrum):
  ''' load the spectrum in the sidebar tree according with the experiment type found in
  the "Lookup file" (E.G.: 'H, STD, WLogsy, T2') '''

  peakList = spectrum.newPeakList()

  sideBar = project._appBase.mainWindow.sideBar
  spectra = sideBar.spectrumItem

  if project._appBase.applicationName == 'Screen' :
    onedItemSideBar = sideBar.onedItem
    stdItemSideBar = sideBar.stdItem
    logsyItemSideBar = sideBar.logsyItem
    t1rhoItemSideBar = sideBar.t1rhoItem

    if spectrum.experimentType == "T2-filtered.H":
      newitem =  sideBar.addItem(t1rhoItemSideBar, spectrum)
      peakListItem = QtGui.QTreeWidgetItem(newitem)
      peakListItem.setText(0, peakList.pid)
    elif spectrum.experimentType == "Water-LOGSY.H":
      newitem =  sideBar.addItem(logsyItemSideBar, spectrum)
      peakListItem = QtGui.QTreeWidgetItem(newitem)
      peakListItem.setText(0, peakList.pid)
    elif spectrum.experimentType == "STD.H":
      newitem =  sideBar.addItem(stdItemSideBar, spectrum)
      peakListItem = QtGui.QTreeWidgetItem(newitem)
      peakListItem.setText(0, peakList.pid)
    elif spectrum.experimentType == "H":
      newitem = sideBar.addItem(onedItemSideBar, spectrum)
      peakListItem = QtGui.QTreeWidgetItem(newitem)
      peakListItem.setText(0, peakList.pid)
    else:
      newitem = sideBar.addItem(sideBar, spectrum)
      peakListItem = QtGui.QTreeWidgetItem(newitem)
      peakListItem.setText(0, peakList.pid)
  else:
    if spectrum.experimentType == "H":
      newitem = sideBar.addItem(spectra, spectrum)
      peakListItem = QtGui.QTreeWidgetItem(newitem)
      peakListItem.setText(0, peakList.pid)



def loadSampleInSideBar(project, sample):

  sideBar = project._appBase.mainWindow.sideBar

  if project._appBase.applicationName == 'Screen' :

    sampleSideBar = sideBar.spectrumSamples
    newitem =  sideBar.addItem(sampleSideBar, sample)
    for sampleComponent in sample.sampleComponents[0:]:
      sideBar.addItem(newitem, sampleComponent)

  if project._appBase.applicationName == 'Metabolomics':

    metabolomicsSideBar = sideBar.metabolomicsSamples
    newitem =  sideBar.addItem(metabolomicsSideBar, sample)
    for sampleComponent in sample.sampleComponents[0:]:
      sideBar.addItem(newitem, sampleComponent)

