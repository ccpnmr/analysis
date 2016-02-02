"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - : 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
               "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                 " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = ": rhfogh $"
__date__ = ": 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = ": 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtCore, QtGui

from ccpncore.gui.Base import Base
from ccpncore.gui.Button import Button
from ccpncore.gui.ButtonList import ButtonList
from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.CheckBox import CheckBox
from ccpncore.gui.GroupBox import GroupBox
from ccpncore.gui.Icon import Icon
from ccpncore.gui.Label import Label
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.ScrollArea import ScrollArea

from application.metabolomics import GuiPipeLine as gp



class MyThread(QtCore.QThread):
    updated = QtCore.pyqtSignal(str)

    def run( self ):
        # do some functionality
        for i in range(10000):
            self.updated.emit(str(i))


class MetabolomicsModule(CcpnDock, Base):

  def __init__(self, project, **kw):

    super(MetabolomicsModule, self)
    CcpnDock.__init__(self, name='Metabolomics')
    Base.__init__(self, **kw)
    self.project = project


    self.pipelineMainGroupBox = GroupBox('Pipeline')
    self.pipelineMainVLayout = QtGui.QVBoxLayout()
    self.pipelineMainVLayout.setAlignment(QtCore.Qt.AlignTop)
    self.setLayout(self.pipelineMainVLayout)
    self.goArea = GoArea(self, project)
    self.layout.addWidget(self.goArea, 0, 0)
    self.pipelineMainGroupBox.setLayout(self.pipelineMainVLayout)
    self.scrollArea = ScrollArea(self)
    self.scrollArea.setWidget(self.pipelineMainGroupBox)
    self.scrollArea.setWidgetResizable(True)
    self.layout.addWidget(self.scrollArea, 1, 0)

    self.widget = (PipelineWidgets(self, project))
    self.pipelineMainVLayout.addWidget(self.widget)
    self._thread = MyThread(self)
    self._thread.updated.connect(self.updatePipeline)
    self.goArea.autoUpdateBox.toggled.connect(self._thread.start)
    self.goArea.goButton.clicked.connect(self.runPipeline)
    # self.checkBox = CheckBox(self, text='Auto-Update')

  def runPipeline(self):
    pipelineFunctions = []
    # for i in range(self.widget.mainWidgets_layout.count()):
    for i in range(self.pipelineMainVLayout.count()):
      widget = self.pipelineMainVLayout.itemAt(i).widget()
      if widget.mainWidgets_layout.itemAt(1).widget().isChecked():
        params = widget.mainWidgets_layout.itemAt(2).widget().getParams()
        pipelineFunctions.append(params)
    data = self.project.getByPid(self.goArea.spectrumGroupPulldown.currentText())
    # spectrumPids = [spectrum.pid for spectrum in data.spectra]
    spectraByPid = {spectrum.pid: spectrum._apiDataSource.get1dSpectrumData() for spectrum in data.spectra}
    print(spectraByPid.keys())
    print(pipelineFunctions)




  def updatePipeline(self):
    if self.goArea.autoUpdateBox.isChecked():
      self.runPipeline()

class GoArea(QtGui.QWidget):

  def __init__(self, parent=None, project=None, **kw):
    super(GoArea, self).__init__(parent)
    self.spectrumGroupLabel = Label(self, 'Input Data ', grid=(0, 0))
    self.spectrumGroupPulldown = PulldownList(self, grid=(0, 1))
    spectrumGroups = [spectrumGroup.pid for spectrumGroup in project.spectrumGroups]
    self.spectrumGroupPulldown.setData(spectrumGroups)
    self.autoUpdateLabel = Label(self, 'Auto Update', grid=(0, 2))
    self.autoUpdateBox = CheckBox(self, grid=(0, 3))
    self.autoUpdateBox.setChecked(True)
    self.goButton = Button(self, 'Go', grid=(0, 4))


class PipelineWidgets(QtGui.QWidget):
  '''
  '''


  def __init__(self, parent=None, project=None, **kw):
    super(PipelineWidgets, self).__init__(parent)
    # Base.__init__(self, **kw)
    self.project = project
    self.pullDownData = {
                'Poly Baseline': gp.PolyBaseline(self, self.project),
                'Align To Reference': gp.AlignToReference(self, self.project),
                'Align Spectra': gp.AlignSpectra(self, self.project),
                'Scale': gp.Scale(self, self.project),
                'Segmental Align': gp.SegmentalAlign(self, self.project),
                'Whittaker Baseline': gp.WhittakerBaseline(self, self.project),
                'Whittaker Smooth': gp.WhittakerSmooth(self, self.project),
                'Bin': gp.Bin(self, self.project),
                'Exclude Baseline Points': gp.ExcludeBaselinePoints(self, self.project),
                'Normalise Spectra': gp.NormaliseSpectra(self, self.project),
                'Exclude Signal Free Regions': gp.ExcludeSignalFreeRegions(self, self.project)}



    self.moveUpRowIcon = Icon('iconsNew/sort-up')
    self.moveDownRowIcon = Icon('iconsNew/sort-down')
    self.addRowIcon = Icon('iconsNew/plus')
    self.removeRowIcon = Icon('iconsNew/minus')

    self.mainWidgets = GroupBox(self)
    self.mainWidgets.setFixedHeight(80)
    self.mainWidgets_layout = QtGui.QHBoxLayout(self.mainWidgets)

    self.pulldownAction = PulldownList(self,)
    self.pulldownAction.setFixedWidth(130)
    self.pulldownAction.setFixedHeight(25)

    pdData = list(self.pullDownData.keys())
    pdData.insert(0, '< Select Method >')
    self.selectMethod = '< Select Method >'


    self.pulldownAction.setData(pdData)
    self.pulldownAction.activated[str].connect(self.addMethod)

    self.checkBox = CheckBox(self, text='active')


    self.moveUpDownButtons = ButtonList(self, texts = ['︎','︎︎'], callbacks=[self.moveRowUp, self.moveRowDown], icons=[self.moveUpRowIcon,self.moveDownRowIcon],
                                       tipTexts=['Move row up', 'Move row down'], direction='h', hAlign='r')
    self.moveUpDownButtons.setFixedHeight(40)
    self.moveUpDownButtons.setFixedWidth(40)
    self.moveUpDownButtons.setStyleSheet('font-size: 10pt')

    self.addRemoveButtons = ButtonList(self, texts = ['',''], callbacks=[self.addRow, self.removeRow],icons=[self.addRowIcon,self.removeRowIcon],
                                       tipTexts=['Add new row', 'Remove row '],  direction='H', hAlign='l' )
    self.addRemoveButtons.setStyleSheet('font-size: 10pt')
    self.addRemoveButtons.setFixedHeight(40)
    self.addRemoveButtons.setFixedWidth(40)

    self.mainWidgets_layout.addWidget(self.pulldownAction,)
    self.mainWidgets_layout.addWidget(self.checkBox,)

    self.mainWidgets_layout.addWidget(self.moveUpDownButtons,)
    self.mainWidgets_layout.addWidget(self.addRemoveButtons,)
    self.addRemoveButtons.buttons[0].setEnabled(False)
    # self.goBox = self.parent().goArea.autoUpdateBox
    # self.goBox.toggled.connect(self.runPipeline)




  def addMethod(self, selected):
     self.updateLayout()

     if selected != '< Select Method >':
      obj = self.pullDownData[selected]
      self.mainWidgets_layout.insertWidget(2, obj, 1)
      mainVboxLayout = obj.parent().parent().parent().layout()
      items = [mainVboxLayout.itemAt(i) for i in range(mainVboxLayout.count())]
      self.enableAddButton(items)


  def updateLayout(self):
    layout = self.mainWidgets_layout
    item = layout.itemAt(2)
    if item.widget() is not self.moveUpDownButtons:
      item.widget().hide()
      layout.removeItem(item)


  def moveRowUp(self):
    '''
    obj => sender = button, parent1= buttonList, parent2= GroupBox1, parent3=PipelineWidgets obj
    objLayout is the main parent layout (VLayout)
    '''
    obj = self.sender().parent().parent().parent()
    objLayout = obj.parent().layout()
    currentPosition = objLayout.indexOf(obj)
    newPosition = max(currentPosition-1, 0)
    objLayout.insertWidget(newPosition, obj)

  def moveRowDown(self):
    '''
    obj as above
    objLayout is the main parent layout (VLayout)
    '''

    obj = self.sender().parent().parent().parent()
    objLayout = obj.parent().layout()
    currentPosition = objLayout.indexOf(obj)
    newPosition = min(currentPosition+1, objLayout.count()-1)
    objLayout.insertWidget(newPosition, obj)

  def addRow(self):
    '''
    This function will add a new Pipelinewidgets obj in the next row below the clicked button.
    '''

    newObj = (PipelineWidgets(self, self.project))
    obj = self.sender().parent().parent().parent()
    objLayout = obj.parent().layout()
    currentPosition = objLayout.indexOf(obj)
    newPosition = min(currentPosition+1, objLayout.count())
    objLayout.insertWidget(newPosition, newObj)

    items = [objLayout.itemAt(i) for i in range(objLayout.count())]
    self.disableAddButton(items)


  def disableAddButton(self, items):
    '''
    If there is empty row with no method selected, will disable all the addButtons in each other row
    '''
    for i in items:
      if i.widget().pulldownAction.getText() == '< Select Method >':
        for i in items:
          i.widget().addRemoveButtons.buttons[0].setEnabled(False)

  def enableAddButton(self, items):
    '''
    If a method is selected, will enable all the addButtons in each other row
    '''
    for i in items:
      i.widget().addRemoveButtons.buttons[0].setEnabled(True)


  def removeRow (self):
    '''
    This function will remove the Pipelinewidgets selected from the main parent layout (VLayout)
    '''

    obj = self.sender().parent().parent().parent()
    objLayout = obj.parent().layout()
    currentPosition = objLayout.indexOf(obj)

    if objLayout.count() == 1 and currentPosition == 0:
      pass

    else:
      obj.deleteLater()






