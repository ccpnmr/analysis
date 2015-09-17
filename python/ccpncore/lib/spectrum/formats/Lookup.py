from PyQt4 import QtCore, QtGui

import pandas as pd
import csv
# from ccpnmrcore.gui.SideBar import SideBar

FILE_TYPE = 'xls', 'csv'
experimentTypeDict = {'zg':'H', 'cpmg':'T2-filtered.H', 'STD':'STD.H', 'bdwl':'Water-LOGSY.H'}


def readXls(project, path=None):

  ex = pd.ExcelFile(path)
  for sheet in ex.sheet_names:
    excelSheet = ex.parse(sheet)
    xlsDict = excelSheet.to_dict()
    parseXls(project, excelSheet)

    for spectrumPath in(excelSheet['filename']):
      if spectrumPath.split('/')[-1] == 'procs':
        filename = spectrumPath.split('/')
        filename.pop()
        Filename = '/'.join(filename)
        loadSpectrum = project.loadData(Filename)

        for spectrum in loadSpectrum:
          loadInSideBar(project, filename, spectrum)





def readCsv(project, path=None):

  csv_in = open(path, 'r')
  reader = csv.reader(csv_in)
  for row in reader:
    if row[0].split('/')[-1] == 'procs':
      filename = row[0].split('/')
      filename.pop()
      Filename = '/'.join(filename)
      loadedSpectrum = project.loadData(Filename)
      for spectrum in loadedSpectrum:
        loadInSideBar(project, filename, spectrum)


def loadInSideBar(project, filename, spectrum):
  ''' load the spectrum in the sidebar tree according with the experiment type found in
  the "pulseprogram file" (E.G.: 'H, STD, WLogsy, T2') '''

  peakList = spectrum.newPeakList()

  sideBar = project._appBase.mainWindow.sideBar
  onedItemSideBar = sideBar.onedItem
  stdItemSideBar = sideBar.stdItem
  logsyItemSideBar = sideBar.logsyItem
  t1rhoItemSideBar = sideBar.t1rhoItem

  pulseprogram = 'pulseprogram'
  pp = filename[:-2]

  pp.append(pulseprogram)
  if pp[-1] == pulseprogram:
    try:
      ppFile = open('/'.join(pp), 'r').readlines()

      expTypes = []
      for expType in experimentTypeDict.keys():

        try:
          if expType in ppFile[1]:
            print(expType)
            expTypes.append(experimentTypeDict[expType])
            print(spectrum.pid,  expTypes , ' before to delete T2')
            spectrum.experimentType = expTypes[0]
            print(spectrum.experimentType)
            if len(expTypes) >1 and 'T2-filtered.H' in expTypes :
              expTypes.remove('T2-filtered.H')
              spectrum.experimentType = expTypes[0]

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
            continue
        except:
          pass
    except:
        peakList = spectrum.newPeakList()
        newitem = sideBar.addItem(onedItemSideBar, spectrum)
        peakListItem = QtGui.QTreeWidgetItem(newitem)
        peakListItem.setText(0, peakList.pid)


def parseXls(project, excelSheet):
  '''xlsDict is the dictionary of all present inside the file  '''

  for exp in excelSheet['expType']:
    print(exp)