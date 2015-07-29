__author__ = 'luca'

from PyQt4 import QtCore, QtGui
from ccpn import AbstractWrapperObject

from ccpncore.gui.Label import Label
from ccpnmrcore.modules.GuiTableGenerator import GuiTableGenerator
from pyqtgraph.dockarea import Dock
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.LineEdit import LineEdit



class SampleTable(Dock):

  def __init__(self, parent=None, samples=None, name='Sample Table', distancevalue=None):
    Dock.__init__(self, name=name)

    self.samples = samples
    print('sampleTable', samples)
    # self.rowcount = len(sampleLists)
    #
    # distancevalue = distancevalue
    # self.distanceValue = (distancevalue * 100)/2
    #
    # self.table = QtGui.QTableWidget()
    # self.table.resizeColumnsToContents()
    # self.table.resizeRowsToContents()
    # self.table.setSortingEnabled(True)
    # header = self.table.horizontalHeader()
    # header.setStretchLastSection(True)
    # self.layout.addWidget(self.table)
    # self.populate()
    # self.setStyleSheet("""QTableWidget::item {
    #                                             background-color: #f7ffff;
    #                                             color: #00092d;
    #                                            }""")

    # samplePulldown = PulldownList(self, grid=(0, 1))

    columns = [('Sample spectra', 'pid')]

    tipTexts = ["Name of the current sample "]

    sampleTable = GuiTableGenerator(self, callback=self.callback(), columns=columns,
                                       selector=None, tipTexts=tipTexts, objects=samples)


    self.layout.addWidget(sampleTable)



  def callback(self):
    pass

  def populate(self):

      self.table.setRowCount(self.rowcount)
      self.table.setColumnCount(5)
      self.table.setHorizontalHeaderLabels(['Sample Name','Components','Minimum Score','Average Score', 'Comments'])

      row = ((i) for i in range(self.rowcount))
      for row, sample, in zip(row, self.sampleLists):

        self.name = QtGui.QTableWidgetItem(sample.pid)
        self.components = QtGui.QTableWidgetItem(str(len(sample.peakCollections)-1))

        if hasattr(sample, 'minScore'):
          self.minScore = QtGui.QTableWidgetItem(str(sample.minScore))
        else:
          self.minScore = QtGui.QTableWidgetItem('None')

        if hasattr (sample, 'averageScore'):
          if sample.averageScore >= self.distanceValue:
              self.avScore = QtGui.QTableWidgetItem(str(round(sample.averageScore, 2))) #round 2 to return only 2 decimals
              self.comments = QtGui.QTableWidgetItem('')
              print('Average Score required:', int(self.distanceValue))

          else:
            self.avScore = QtGui.QTableWidgetItem(str(round(sample.averageScore, 2)))
            self.comments = QtGui.QTableWidgetItem('Below requirements')
            print('Average Score required:', int(self.distanceValue))
        else:
          self.avScore = QtGui.QTableWidgetItem('no average')

        ###---> these labels make editable only the row 'comments'
        self.name.setFlags(self.name.flags() & ~(QtCore.Qt.ItemIsEditable))
        self.minScore.setFlags(self.minScore.flags() & ~(QtCore.Qt.ItemIsEditable))
        self.avScore.setFlags(self.avScore.flags() & ~(QtCore.Qt.ItemIsEditable))
        self.components.setFlags(self.components.flags() & ~(QtCore.Qt.ItemIsEditable))

        ###---> Tool Tip
        self.table.horizontalHeaderItem(0).setToolTip("Name of the current sample ")
        self.table.horizontalHeaderItem(1).setToolTip("Number of components present in the sample ")
        self.table.horizontalHeaderItem(2).setToolTip("The lowest score corresponds to the most overlapped "
                                                      "component in the sample ")
        self.table.horizontalHeaderItem(3).setToolTip("The average score of the components in the mixture ")

        ###---> Set row and colons
        self.table.setItem(row, 0, self.name)
        self.table.setItem(row, 1, self.components)
        self.table.setItem(row, 2, self.minScore)
        self.table.setItem(row, 3, self.avScore)
        self.table.setItem(row, 4, self.comments)


