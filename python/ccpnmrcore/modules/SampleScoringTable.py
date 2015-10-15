__author__ = 'luca'

from PyQt4 import QtCore, QtGui
from ccpncore.gui.Table import ObjectTable, Column



class SampleTableSimple(QtGui.QWidget):
  pass
#
  def __init__(self, parent=None, project=None, callback=None):
    QtGui.QWidget.__init__(self, parent)

    self.project = project


    listOfSample = []

    for sample in self.project.samples:
      if len(sample.spectra) > 1:
        listOfSample.append(sample)

    columns = [Column('Mixture Name', lambda sample:str(sample.pid)),
               Column('Number of Substances', lambda sample: (int(len(sample.peakCollections)))),
               Column('Minimum Score', lambda sample: int(sample.minScore)),
               Column('Average Score', lambda sample: int(sample.averageScore))]


    sampleTable = ObjectTable(self, columns, callback=self.showSample, objects=[])
    sampleTable.setObjects(listOfSample)


    self.layout().addWidget(sampleTable, 3, 0, 1, 4)


  def showSample(self):
    print('Not implemented yet')

