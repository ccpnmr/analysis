from application.core.popups.SampleSetupPopup import solvents, SamplePopup, ExcludeRegions

from PyQt4 import QtCore, QtGui
from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.Base import Base
from ccpncore.gui.ScrollArea import ScrollArea
from ccpncore.gui.Table import ObjectTable, Column
from ccpncore.gui.LineEdit import LineEdit
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.Frame import Frame
from ccpncore.gui.CheckBox import CheckBox
from ccpncore.gui.ButtonList import ButtonList
from ccpncore.gui.Button import Button
from ccpncore.gui.Icon import Icon
from ccpncore.gui.GroupBox import GroupBox
from ccpncore.gui.DoubleSpinbox import DoubleSpinbox
from ccpncore.gui.Label import Label
from functools import partial
from application.metabolomics.GuiPipeLine import PolyBaseline



#
class MetabolomicsModule(CcpnDock, Base):

  def __init__(self, project, **kw):

    super(MetabolomicsModule, self)
    CcpnDock.__init__(self, name='Metabolomics')
    Base.__init__(self, **kw)
    self.project = project
    self.layout.addWidget(PipelineWidgets(self, project))


class PipelineWidgets(QtGui.QWidget, Base):
  '''This create the second tab to exclude Regions from Spectrum when peak picking '''

  def __init__(self, parent=None, project=None, **kw):
    super(PipelineWidgets, self).__init__(parent)
    Base.__init__(self, **kw)
    self.project = project
    self.pullDownData = {'< Select Method >' : '',
                'Reference': '',
                'Fit': '',
                 'Baseline': '',
               'Auto-scale': '',
                'Exclude Regions': ExcludeRegions(self)}



    self.moveUpRowIcon = Icon('iconsNew/sort-up')
    self.moveDownRowIcon = Icon('iconsNew/sort-down')
    self.addRowIcon = Icon('iconsNew/plus')
    self.removeRowIcon = Icon('iconsNew/minus')

    # Main layout: a scrollable group box with a gridLayout layout. 3 different areas inside:
    # left: method selection(groupbox, hLayout);
    # middle: actions (groupbox, GridLayout);
    # right: layout management(groupbox, hLayout).
    # This proposed solution will allow to have every time the left and right widgets aligned within the the main layout.


    self.pipelineGroupBox = GroupBox('Pipeline')
    self.groupBoxMainLayout = QtGui.QGridLayout()
    self.groupBoxMainLayout.setAlignment(QtCore.Qt.AlignTop)
    self.setLayout(self.groupBoxMainLayout)


    self.pipelineGroupBox.setLayout(self.groupBoxMainLayout)
    self.scrollArea = ScrollArea(self)
    self.scrollArea.setWidget(self.pipelineGroupBox)
    self.scrollArea.setWidgetResizable(True)




    self.left = GroupBox()
    self.left.setFixedWidth(220)
    self.left.setFixedHeight(90)
    self.groupBoxMainLayout.addWidget(self.left,0,0)
    self.left_layout = QtGui.QHBoxLayout(self.left)


    self.middle = GroupBox()
    self.middle.setFixedHeight(90)
    self.groupBoxMainLayout.addWidget(self.middle,0,1)
    self.middle_layout = QtGui.QHBoxLayout(self.middle)
    polyBL = PolyBaseline(self, self.project._appBase.current)
    self.middle_layout.addWidget(polyBL)

    self.right = GroupBox()
    self.right.setFixedWidth(120)
    self.right.setFixedHeight(90)
    self.right_layout = QtGui.QHBoxLayout(self.right)
    self.groupBoxMainLayout.addWidget(self.right,0,2)



    self.pulldownAction = PulldownList(self,)
    self.pulldownAction.setFixedWidth(130)
    self.pulldownAction.setFixedHeight(30)
    for item in sorted( self.pullDownData):
      self.pulldownAction.addItem(item)
    self.pulldownAction.activated[str].connect(self.addMethod)

    # self.pulldownAction.setData(PullDownData)
    self.checkBox = CheckBox(self, text='active')

    self.moveUpDownButtons = ButtonList(self, texts = ['︎','︎︎'], callbacks=[self.moveRowUp, self.moveRowDown], icons=[self.moveUpRowIcon,self.moveDownRowIcon],
                                       tipTexts=['Move row up', 'Move row down'], direction='h', hAlign='r')
    self.moveUpDownButtons.setMaximumSize(90, 70) #Lenght,Height
    self.moveUpDownButtons.setStyleSheet('font-size: 10pt')

    self.addRemoveButtons = ButtonList(self, texts = ['',''], callbacks=[self.addRow, self.removeRow],icons=[self.addRowIcon,self.removeRowIcon],
                                       tipTexts=['Add new row', 'Remove row '], direction='H', hAlign='l')
    self.addRemoveButtons.setStyleSheet('font-size: 10pt')
    self.addRemoveButtons.setMaximumSize(90, 70)

    self.left_layout.addWidget(self.pulldownAction)
    self.left_layout.addWidget(self.checkBox)


    self.right_layout.addWidget(self.moveUpDownButtons)
    self.right_layout.addWidget(self.addRemoveButtons)



    # self.layout.addWidget(self.scrollArea)



  def addMethod(self, selected):

    for method in sorted(self.pullDownData):
      if selected == ('%s' %method):
        obj = (self.pullDownData[method])
        self.middle_layout.addWidget(obj)



  def addRow (self):
    print('addRow')

  def removeRow (self):
    print('removeRow')

  def moveRowUp (self):
    print('moveRowUp')

  def moveRowDown (self):
    print('moveRowDown')













