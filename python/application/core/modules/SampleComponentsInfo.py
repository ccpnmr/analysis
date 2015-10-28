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
    self.SamplePulldown.setData([sample.pid for sample in self.samples])


  # Object table

    self.listOfSubstances = []

  ################################################################### still hack waiting new wrapper
    columns = [Column('Name', lambda substance:str(substance.pid)),
               Column(' Sample pH', ''),
               Column('logP', lambda substance:str(substance.logPartitionCoefficient)),
               Column('psa', lambda substance:str(substance.polarSurfaceArea)),
               Column('H acceptor', lambda substance:str(substance.hBondAcceptorCount)),
               Column('H donor', lambda substance:str(substance.hBondDonorCount)),
               Column('comment', lambda substance:str(substance.comment))]

    self.sampleInfoTable = ObjectTable(self, columns, callback=self.callback, objects=[])


    self.layout().addWidget(self.sampleInfoTable, 3, 0, 1, 2)

  def pulldownSampleInfo(self, selection):
   for sample in self.project.samples:
      if sample.pid  == selection:
        self.sampleComponents =  sample.sampleComponents
        for component in self.sampleComponents:
          substance = component.substance
          self.listOfSubstances.append(substance)
          self.sampleInfoTable.setObjects(self.listOfSubstances)

  def callback(self):
    print('Not implemented yet')
