import csv
from collections import OrderedDict

import pandas as pd
from PyQt4 import QtCore, QtGui


# if project._appBase.applicationName == 'Screen':
# if project._appBase.applicationName == 'Metabolomics':

def readXls(project, path=None):

  newSpectrumGroup = project.newSpectrumGroup('STD')
  ex = pd.ExcelFile(path)
  for p,f in screenExcelSheetProcessors.items():
    if p in ex.sheet_names:
      e = ex.parse(p)
      e.fillna('Empty',inplace=True)
      f(project, e)



# def readXls(project, path=None):
#   ex = pd.ExcelFile(path)
#   excelSheet = ex.parse(ex.sheet_names[0])
#   excelSheet.fillna('Empty',inplace=True)
#   createDataDict(project, excelSheet)
#
#   if len(ex.sheet_names) > 1:
#     secondSheetExcel = ex.parse(ex.sheet_names[1])
#     secondSheetExcel.fillna('Empty',inplace=True)
#     createSampleDicts(project, secondSheetExcel)

def readCsv(project, path=None):

  csv_in = open(path, 'r')
  reader = csv.reader(csv_in)
  for row in reader:
    if row[0].split('/')[-1] == 'procs':
      filename = row[0].split('/')
      filename.pop()
      filenamePath = '/'.join(filename)
      spectrum = project.loadData(filenamePath)

def createDataDict(project, excelSheet):
  ''' excelSheet: data frame containing all data from the look up file.
  This function will read the spectrum file path and load the spectrum to the project.
  For each obj spectrum creates a dictionary containing all its data '''
  dataDicts = []
  for data in excelSheet.to_dict(orient="index").values():
    dataDict= {project.loadData(spectrumPath)[0]:data for header, spectrumPath in data.items() if header == 'SpectrumPath'}
    dataDicts.append(dataDict)
  loadDataToProject(project, dataDicts)

def loadDataToProject(project, dataDicts):
  ''' dispatch data to the project'''
  createGroupNameDicts(project, dataDicts)

  if project._appBase.applicationName == 'Screen':
    createNewSubstance(project, dataDicts)

def createGroupNameDicts(project,dataDicts):
  ''' creates dicts group name with its spectrum '''
  groupNameDicts = []
  for dataDict in dataDicts:
    for spectrum, data in dataDict.items():
      groupNameDict= {str(groupName):spectrum for header, groupName in data.items() if header == 'groupName'}
      groupNameDicts.append(groupNameDict)

  newSpectrumGroup(project, groupNameDicts)

def newSpectrumGroup(project, groupNameDicts):
  '''creates new spectrum group for the project. If more groups have the same name they are merged'''
  newGroupsDict = {}
  for groupName in set(k for d in groupNameDicts for k in d):
    newGroupsDict[groupName] = [d[groupName] for d in groupNameDicts if groupName in d]
  for groupName, spectra in newGroupsDict.items():
    newSpectrumGroup = project.newSpectrumGroup(name=groupName, spectra=spectra)
    # loadSpectrumGroupInSideBar(project, newSpectrumGroup)

def createSampleDicts(project, secondSheetExcel):
  sampleDicts = []
  for data in secondSheetExcel.to_dict(orient="index").values():
    sampleDict={project.newSample(name=str(sampleName)):data for header, sampleName in data.items() if header == 'sampleName'}
    sampleDicts.append(sampleDict)
  getSampleObj(project, sampleDicts)

def getSampleObj(project, sampleDicts):
  for sampleDict in sampleDicts:
    for sample, data in sampleDict.items():
      addSampleSpectra(project, sample, data)
      dispatchSampleProperties(sample, data)

def createNewSubstance(project, dataDicts):
  for dataDict in dataDicts:
    for spectrum, data in dataDict.items():
      expType = ([[key, value] for key, value in data.items() if key == 'expType'])
      newSubstance = project.newSubstance(name=spectrum.name, labeling=str(expType[0][1]))
      # newChain = project.createChain(sequence=str('A'),compoundName=str(spectrum.name), molType='protein')
      newSubstance.referenceSpectra = [spectrum]
      dispatchSubstanceProperties(newSubstance, data)

screenExcelSheetProcessors = OrderedDict([('Reference', createDataDict),
                                          ('STD_Samples', createSampleDicts),
                                         ])

def dispatchSubstanceProperties(substance, data):
  for substanceProperty in substanceProperties:
    substanceProperty(substance, data)

def dispatchSampleProperties(sample, data):
  for sampleProperty in sampleProperties:
    sampleProperty(sample, data)

def addSampleComponents(sample, data):
  sampleComponents = [[header, sampleComponentName] for header, sampleComponentName in data.items() if header == 'sampleComponents']
  for name in sampleComponents[0][1].split(','):
    sampleComponent = sample.newSampleComponent(name=(str(name) +'-1'), labeling='H')

# def addSampleSpectra(project, sample, data):
#   sampleSpectra = []
#   sampleSpectraPath = [[header, sampleSpectra] for header, sampleSpectra in data.items() if header == 'sampleSpectraPaths']
#   experimentType = [[excelHeader, value] for excelHeader, value in data.items() if excelHeader == 'expType']
#
#   for sampleSpectrumPath in sampleSpectraPath[0][1].split(','):
#     sampleSpectrum = project.loadData(sampleSpectrumPath)
#     sampleSpectrum[0].newPeakList()
#     sampleSpectrum[0].experimentType = experimentType[0][1]
#     sampleSpectra.append(sampleSpectrum[0])
#   sample.spectra = sampleSpectra

# To fix soon:


def addSampleSpectra(project, sample, data):
  sampleSpectra = []
  sampleSpectrum1Path = [[header, sampleSpectra] for header, sampleSpectra in data.items()
                         if header == 'sampleSpectrum1Path' and sampleSpectra != 'Empty']
  sampleSpectrum1ExpType = [[excelHeader, value] for excelHeader, value in data.items()
                            if excelHeader == 'sampleSpectrum1ExpType' and value != 'Empty']
  sampleSpectrum1Comment = [[excelHeader, value] for excelHeader, value in data.items()
                            if excelHeader == 'sampleSpectrum1Comment']

  sampleSpectrum2Path = [[header, sampleSpectra] for header, sampleSpectra in data.items()
                         if header == 'sampleSpectrum2Path' and sampleSpectra != 'Empty']
  sampleSpectrum2ExpType = [[excelHeader, value] for excelHeader, value in data.items()
                            if excelHeader == 'sampleSpectrum2ExpType'and sampleSpectra != 'Empty']
  sampleSpectrum2Comment = [[excelHeader, value] for excelHeader, value in data.items()
                            if excelHeader == 'sampleSpectrum2Comment']

  if len(sampleSpectrum1Path)>0:
    sampleSpectrum1 = project.loadData(sampleSpectrum1Path[0][1])
    # sampleSpectrum1[0].newPeakList()
    sampleSpectrum1[0].experimentType = sampleSpectrum1ExpType[0][1]
    sampleSpectrum1[0].comment = sampleSpectrum1Comment[0][1]
    sampleSpectra.append(sampleSpectrum1[0])

  if len(sampleSpectrum2Path)>0:
    sampleSpectrum2 = project.loadData(sampleSpectrum2Path[0][1])
    # sampleSpectrum2[0].newPeakList()
    sampleSpectrum2[0].experimentType = sampleSpectrum2ExpType[0][1]
    sampleSpectrum2[0].comment = sampleSpectrum2Comment[0][1]
    sampleSpectra.append(sampleSpectrum2[0])

  sample.spectra = sampleSpectra

  # allSpectra.append(sample.spectra)
  createStdSpectrumGroup(project)

def createStdSpectrumGroup(project,):
  spectra = []
  for sample in project.samples:
    for spectrum in sample.spectra:
      spectra.append(spectrum)
  for spectrumGroup in project.spectrumGroups:
    if spectrumGroup.name == 'STD':
      spectrumGroup.spectra = spectra


def setSamplepH(sample, data):
  samplePH = [[excelHeader, value] for excelHeader, value in data.items()
              if excelHeader == 'pH' and value != 'Empty']
  if len(samplePH)>0:
    sample.ph = samplePH[0][1]

def setSampleIonicStrength(sample, data):
  ionicStrength = [[excelHeader, value] for excelHeader, value in data.items()
                   if excelHeader == 'ionicStrength'and value != 'Empty']
  if len(ionicStrength)>0:
    sample.ph = ionicStrength[0][1]

def setSampleAmount(sample, data):
  amount = [[excelHeader, value] for excelHeader, value in data.items()
            if excelHeader == 'amount' and value != 'Empty']
  if len(amount)>0:
    sample.amount = amount[0][1]

def setSampleAmountUnit(sample, data):
  amountUnit = [[excelHeader, value] for excelHeader, value in data.items()
                if excelHeader == 'amountUnit' and value != 'Empty']
  if len(amountUnit)>0:
    sample.amountUnit = amountUnit[0][1]

def setSampleCreationDate(sample, data):
  creationDate = [[excelHeader, value] for excelHeader, value in data.items()
                  if excelHeader == 'creationDate' and value != 'Empty']
  if len(creationDate)>0:
    sample.creationDate = creationDate[0][1]

def setSampleBatchIdentifier(sample, data):
  batchIdentifier = [[excelHeader, value] for excelHeader, value in data.items()
                     if excelHeader == 'batchIdentifier' and value != 'Empty']
  if len(batchIdentifier)>0:
    sample.batchIdentifier = batchIdentifier[0][1]

def setSamplePlateIdentifier(sample, data):
  plateIdentifier = [[excelHeader, value] for excelHeader, value in data.items()
                     if excelHeader == 'plateIdentifier' and value != 'Empty']
  if len(plateIdentifier)>0:
   sample.plateIdentifier = plateIdentifier[0][1]

def setSampleRowNumber(sample, data):
  rowNumber = [[excelHeader, value] for excelHeader, value in data.items()
               if excelHeader == 'rowNumber' and value != 'Empty']
  if len(rowNumber)>0:
    sample.rowNumber = rowNumber[0][1]

def setSampleColumnNumberr(sample, data):
  columnNumber = [[excelHeader, value] for excelHeader, value in data.items()
                  if excelHeader == 'columnNumber' and value != 'Empty']
  if len(columnNumber)>0:
    sample.columnNumber = columnNumber[0][1]

def setSampleComment(sample, data):
  comments = [[excelHeader, value] for excelHeader, value in data.items()
              if excelHeader == 'sampleComments' and value != 'Empty']
  if len(comments)>0:
    sample.comments = comments[0][1]

sampleProperties = [addSampleComponents, setSamplepH,
  setSampleIonicStrength, setSampleAmount, setSampleAmountUnit, setSampleCreationDate,
  setSampleBatchIdentifier, setSampleRowNumber, setSampleColumnNumberr, setSampleComment]

### Setting Substance properties

def setSubstanceType(substance, data):
  substanceType = [[excelHeader, value] for excelHeader, value in data.items()
                   if excelHeader == 'substanceType' and value != 'Empty']
  if len(substanceType)>0:
   substance.substanceType = str(substanceType[0][1])

def setSubstanceSynonyms(substance, data):
  substanceSynonyms = [[excelHeader, value] for excelHeader, value in data.items()
                       if excelHeader == 'substanceSynonyms']
  if len(substanceSynonyms)>0:
    substance.synonyms = substanceSynonyms[0][1]

def setSubstanceComment(substance, data):
  comments = [[excelHeader, value] for excelHeader, value in data.items()
              if excelHeader == 'substanceComments' and value != 'Empty']
  if len(comments)>0:
    substance.comments = comments[0][1]

def setSubstanceUserCode(substance, data):
  userCode = [[excelHeader, value] for excelHeader, value in data.items()
              if excelHeader == 'substanceUserCode' and value != 'Empty']
  if len(userCode)>0:
    substance.userCode = userCode[0][1]

def setSubstanceSmiles(substance, data):
  smiles = [[excelHeader, value] for excelHeader, value in data.items()
            if excelHeader == 'substanceSmiles' and value != 'Empty']
  if len(smiles)>0:
    substance.smiles = smiles[0][1]

def setSubstanceInChi(substance, data):
  inChi = [[excelHeader, value] for excelHeader, value in data.items()
           if excelHeader == 'substanceInChi' and value != 'Empty']
  if len(inChi)>0:
    substance.inChi = inChi[0][1]

def setSubstanceCasNumber(substance, data):
  substanceCasNumber = [[excelHeader, value] for excelHeader, value in data.items()
                        if excelHeader == 'substanceCasNumber' and value != 'Empty']
  if len(substanceCasNumber)>0:
    substance.casNumber = substanceCasNumber[0][1]

def setSubstanceEmpiricalFormula(substance, data):
  substanceEmpiricalFormula = [[excelHeader, value] for excelHeader, value in data.items()
                               if excelHeader == 'substanceEmpiricalFormula' and value != 'Empty']
  if len(substanceEmpiricalFormula)>0:
    substance.empiricalFormula = substanceEmpiricalFormula[0][1]

def setSubstanceMolecularMass(substance, data):
  substanceMolecularMass = [[excelHeader, value] for excelHeader, value in data.items()
                            if excelHeader == 'molecularMass' and value != 'Empty']
  if len(substanceMolecularMass)>0:
    substance.molecularMass = substanceMolecularMass[0][1]

def setSubstanceHAtomCount(substance, data):
  substanceHAtomCount = [[excelHeader, value] for excelHeader, value in data.items()
                         if excelHeader == 'substanceHAtomCount' and value != 'Empty']
  if len(substanceHAtomCount)>0:
    substance.atomCount = substanceHAtomCount[0][1]

def setSubstanceBondCount(substance, data):
  substanceBondCount = [[excelHeader, value] for excelHeader, value in data.items()
                        if excelHeader == 'substanceBondCount' and value != 'Empty']
  if len(substanceBondCount)>0:
    substance.bondCount = substanceBondCount[0][1]

def setSubstanceRingCount(substance, data):
  substanceRingCount = [[excelHeader, value] for excelHeader, value in data.items()
                        if excelHeader == 'substanceRingCount' and value != 'Empty']
  if len(substanceRingCount)>0:
    substance.ringCount = substanceRingCount[0][1]

def setSubstanceHBondDonorCount(substance, data):
  substanceHBondDonorCount = [[excelHeader, value] for excelHeader, value in data.items()
                              if excelHeader == 'Hdonor' and value != 'Empty']
  if len(substanceHBondDonorCount)>0:
    substance.hBondDonorCount = substanceHBondDonorCount[0][1]

def setSubstanceHBondAcceptorCount(substance, data):
  substanceHBondDonorCount = [[excelHeader, value] for excelHeader, value in data.items()
                              if excelHeader == 'Hacceptor' and value != 'Empty']
  if len(substanceHBondDonorCount)>0:
    substance.hBondAcceptorCount = substanceHBondDonorCount[0][1]

def setSubstancePolarSurfaceArea(substance, data):
  substancePolarSurfaceArea = [[excelHeader, value] for excelHeader, value in data.items()
                               if excelHeader == 'substancePolarSurfaceArea' and value != 'Empty']
  if len(substancePolarSurfaceArea)>0:
    substance.polarSurfaceArea = substancePolarSurfaceArea[0][1]

def setSubstanceLogPartitionCoefficient(substance, data):
  substanceLogPartitionCoefficient = [[excelHeader, value] for excelHeader, value in data.items()
                                      if excelHeader == 'cLogP' and value != 'Empty']
  if len(substanceLogPartitionCoefficient)>0:
    substance.logPartitionCoefficient = substanceLogPartitionCoefficient[0][1]

substanceProperties = [setSubstanceType, setSubstanceComment, setSubstanceSynonyms, setSubstanceUserCode,
  setSubstanceSmiles, setSubstanceInChi, setSubstanceCasNumber, setSubstanceEmpiricalFormula,
  setSubstanceMolecularMass, setSubstanceHAtomCount, setSubstanceBondCount, setSubstanceRingCount,
  setSubstanceLogPartitionCoefficient,setSubstancePolarSurfaceArea,
  setSubstanceHBondDonorCount, setSubstanceHBondAcceptorCount]


### Loading obj in SideBar

# Feb 2106 Rasmus Fogh. No longer needed

# def loadSpectrumInSideBar(project, spectrum):
#   ''' load the spectrum in the sidebar '''
#   peakList = spectrum.newPeakList()
#   sideBar = project._appBase.mainWindow.sideBar
#   spectra = sideBar.spectrumItem
#   newSpectrumItem = sideBar.addItem(spectra, spectrum)
#   peakListItem = QtGui.QTreeWidgetItem(newSpectrumItem)
#   peakListItem.setText(0, peakList.pid)

# def loadSampleInSideBar(project, sample):
#   sideBar = project._appBase.mainWindow.sideBar
#   sampleSideBar = sideBar.samplesItem
#   sampleItem =  sideBar.addItem(sampleSideBar, sample)
#   for sampleComponent in sample.sampleComponents[0:]:
#     sideBar.addItem(sampleItem, sampleComponent)
#
# def loadSpectrumGroupInSideBar(project, newSpectrumGroup):
#   sideBar = project._appBase.mainWindow.sideBar
#   spectrumGroupItem = sideBar.spectrumGroupItem
#   newGroupItem =  sideBar.addItem(spectrumGroupItem, newSpectrumGroup)
#   for spectrum in newSpectrumGroup.spectra:
#     sideBar.addItem(newGroupItem, spectrum)
#     peakList = spectrum.newPeakList()
