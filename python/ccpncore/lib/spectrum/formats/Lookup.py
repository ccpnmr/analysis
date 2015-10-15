from PyQt4 import QtCore, QtGui
import pandas as pd
import csv


def readXls(project, path=None):

  ex = pd.ExcelFile(path)
  for sheet in ex.sheet_names:
    excelSheet = ex.parse(sheet)
    xlsDict = excelSheet.to_dict()

    #NB this is for now only a hack
    header = sorted(xlsDict.keys())


    for spectrumPath, id, expType, pH , amount, comment, ionicStrength, numAtoms, buffer\
        in zip(excelSheet['filename'], excelSheet['Id'], excelSheet['expType'],
        excelSheet['pH'], excelSheet['amount'], excelSheet['comments'],
        excelSheet['ionicStrength'], excelSheet['numHAtoms'],  excelSheet['buffer'] ):

      if spectrumPath.split('/')[-1] == 'procs':
        filename = spectrumPath.split('/')
        filename.pop()
        filenamePath = '/'.join(filename)
        for spectrum in project.loadData(filenamePath):
          spectrum.experimentType = expType
          loadInSideBar(project, spectrum)

          # create Sample
          newSample = project.newSample(name=str(id))
          spectrum.sample = newSample
          newSample.pH = pH
          newSample.amount = amount
          newSample.comment = comment
          newSample.ionicStrength = ionicStrength
          newSample.numAtoms = numAtoms
          newSample.batchIdentifier = buffer





def readCsv(project, path=None):
  csv_in = open(path, 'r')
  reader = csv.reader(csv_in)
  for row in reader:
    print(row)
    if row[0].split('/')[-1] == 'procs':
      filename = row[0].split('/')
      filename.pop()
      filenamePath = '/'.join(filename)
      loadedSpectrum = project.loadData(filenamePath)
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
    newitem = sideBar.addItem(onedItemSideBar, spectrum)
    peakListItem = QtGui.QTreeWidgetItem(newitem)
    peakListItem.setText(0, peakList.pid)
