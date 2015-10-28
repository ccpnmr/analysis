__author__ = 'luca'

from PyQt4 import QtCore, QtGui
from ccpncore.gui.Table import ObjectTable, Column
from pandas import DataFrame


class SampleTableSimple(QtGui.QWidget):

#
  def __init__(self, parent=None, project=None, callback=None):
    QtGui.QWidget.__init__(self, parent)

    self.project = project


    listOfSample = []

    for sample in self.project.samples:
        listOfSample.append(sample)


    columns = [Column('Mixture Name', lambda sample:str(sample.pid)),
               Column('Number of Substances', lambda sample: (int(len(sample.peakCollections)))),
               Column('Minimum Score', lambda sample: int(sample.minScore)),
               Column('Average Score', lambda sample: int(sample.averageScore))]


    sampleTable = ObjectTable(self, columns, callback=self.showSample, objects=[])
    sampleTable.setObjects(listOfSample)


    self.layout().addWidget(sampleTable, 3, 0, 1, 3)
    self.exportToXls()




  def showSample(self):
    print('Not implemented yet')


  def exportToXls(self):

    sampleColumn = [str(self.project.samples)]
    # componentsColumn = [str(self.project.sample.sampleComponents)]
    df = DataFrame({'Mixture name': sampleColumn})


    df.to_excel('Mixtures.xlsx', sheet_name='sheet1', index=False)
