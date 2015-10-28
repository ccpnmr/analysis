

__author__ = 'luca'


from PyQt4 import QtCore, QtGui
from ccpncore.gui.Label import Label
from application.core.modules.GuiTableGenerator import GuiTableGenerator
from pyqtgraph.dockarea import Dock
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.LineEdit import LineEdit



class MixtureTable(Dock):


  def __init__(self, parent=None, mixtureLists=None, name='Mixture Table', **kw):

    if not mixtureLists:
      mixtureLists = []

    Dock.__init__(self, name=name)

    label = Label(self, "Mixture List")
    self.layout.addWidget(label, 0, 0)


    self.mixtureLists = mixtureLists

    self.PulldownMixture = PulldownList(self, grid=(0, 1))
    # for mixture in mixtureLists:
    #
    #   self.PulldownMixture.addItem(mixture.pid)
    #   self.mixture = mixture




      # print('# ',mixture.name , '|', 'name' , '|', 'component',(len(mixture.peakCollections)-1), '|', 'score', mixture.minScore, '|')
    columns = [('Name', 'pid'), ('Score', 'minScore' ),('N Compounds', lambda sample: len(sample.peakCollections)-1), ('Details', 'comm')]
    # columns = [('N ame', lambda mx:mx.name if mx.name else 'name'),
    #           ('Score', lambda mx:round(mx.minScore,
    #           1) if mx.minScore != None else 'tt'),
    #           ('N Compounds', lambda mx:len(mx.peakCollections)),
    #           ('Details', 'comment')]


    tipTexts = ['Name of the sample', 'Minimal distance between components in the sample',
               'Number of components in the sample', 'Textual Notes about the sample']


    print(self.mixtureLists)

    self.mixtureTable = GuiTableGenerator(self, mixtureLists, callback=None,
                                          columns=columns, selector = self.PulldownMixture,
                                          tipTexts=tipTexts)


    self.layout.addWidget(self.mixtureTable, 3, 0, 1, 4)

