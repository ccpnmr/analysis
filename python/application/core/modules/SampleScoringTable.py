__author__ = 'luca'

from PyQt4 import QtCore, QtGui
from ccpncore.gui.Table import ObjectTable, Column
from pandas import DataFrame
from ccpncore.gui.Button import Button


class SampleTableSimple(QtGui.QWidget):

  def __init__(self, parent=None, project=None, callback=None):
    QtGui.QWidget.__init__(self, parent)

    self.project = project
    exportButton = Button(self, text = 'Export Results', grid=(5,1), callback= self.exportToXls)

    listOfSample = []

    for sample in self.project.samples:
        listOfSample.append(sample)

    columns = [Column('Mixture Name', lambda sample:str(sample.pid)),
               Column('Number of Components', lambda sample: (int(len(sample.spectra)))),
               Column('Minimum Score', lambda sample: int(sample.minScore)),
               Column('Average Score', lambda sample: int(sample.averageScore))]


    sampleTable = ObjectTable(self, columns, callback=self.showSample, objects=[])
    sampleTable.setObjects(listOfSample)


    self.layout().addWidget(sampleTable, 3, 0, 1, 3)


  def showSample(self):
    print('Not implemented yet')

  def exportToXls(self):
    self.nameAndPath = ''
    fType = 'XLS (*.xlsx)'
    dialog = QtGui.QFileDialog
    filePath = dialog.getSaveFileName(self,filter=fType)
    self.nameAndPath = filePath

    sampleColumn = [str(sample.pid) for sample in self.project.samples]
    sampleComponents = [str(sample.spectra) for sample in self.project.samples]
    # print([sampleComponent.name for sample in self.project.samples for sampleComponent in sample.sampleComponents ])
    df = DataFrame({'Mixture name': sampleColumn, 'Sample Components': sampleComponents})
    df.to_excel(self.nameAndPath, sheet_name='sheet1', index=False)
