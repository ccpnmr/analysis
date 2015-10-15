__author__ = 'luca'


from PyQt4 import QtGui, QtCore
from ccpncore.gui.Label import Label
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.ScrollArea import ScrollArea
from ccpncore.gui.Table import ObjectTable, Column


class SampleComponentInfo(QtGui.QWidget):
  def __init__(self, parent=None, project=None):
    super(SampleComponentInfo, self).__init__(parent)

    self.project = project
    self.peakLists = project.peakLists
    self.samples = project.samples


    labelSelectSample = Label(self, ' Select Mixture:', grid=(0, 0), hAlign='r')
    self.SamplePulldown = PulldownList(self, grid=(0, 1), callback=self.pulldownSampleInfo)
    self.SamplePulldown.setData([sample.pid for sample in self.samples if len(sample.spectra) > 1])


  ## Object table

    listOfSample = []

    for sample in self.samples:

        if len(sample.spectra) < 2:
          listOfSample.append(sample)

    columns = [Column('Name', lambda sample:str(sample.pid)),
               Column('logP', lambda sample: str(sample.ionicStrength)),
               Column('molWeight',lambda sample: float(sample.amount)) ,
               Column('numAtoms', lambda sample: float(sample.numAtoms)),
               Column('pH', lambda sample: float(sample.pH)),
               Column('solvent', lambda sample: str(sample.batchIdentifier))]



    sampleInfoTable = ObjectTable(self, columns, callback=self.callback, objects=[])
    sampleInfoTable.setObjects(listOfSample)


    self.layout().addWidget(sampleInfoTable, 3, 0, 1, 2)

  def pulldownSampleInfo(self, selection):
    for sample in self.samples:
      if sample.pid == selection:
       for i in sample.spectra:
         print(i)










        # for spectrumInSample in sample.spectra:
        #
        #
        #   listofSpectraPerSample.append(spectrumInSample)
        # listoSamples = [sample.pid for sample in self.samples if len(sample.spectra)<2]
        #
        #



  def callback(self):
    print('Not implemented yet')
