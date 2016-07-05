
from PyQt4 import QtGui, QtCore

from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.Slider import Slider
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.ListWidget import ListWidget


class LookupSetupPopup(QtGui.QDialog):

  def __init__(self, parent=None, project=None,  **kw):
    super(LookupSetupPopup, self).__init__(parent)

    self.project = project
    self.mainWindow = parent
    self.moduleArea = self.mainWindow.moduleArea
    self.application = self.mainWindow.application
    self.generalPreferences = self.application.preferences.general
    self.colourScheme = self.generalPreferences.colourScheme
    self._setMainLayout()
    self._setWidgets()


  def _setMainLayout(self):
    self.mainLayout = QtGui.QGridLayout()
    self.setLayout(self.mainLayout)
    self.setWindowTitle("Lookup Setup")
    self.resize(300, 400)


  def _setWidgets(self):
    # self.lineInfo = Label(self, 'Reference Path')
    self.setPathDetectorWidget()
    self.setButtons()


  def setPathDetectorWidget(self):
    self.pathDetectorWidget = ListWidget(self, rightMouseCallback=None)
    self.pathDetectorWidget.setMinimumHeight(40)
    self.pathDetectorWidget.setAcceptDrops(True)
    self.connect(self.pathDetectorWidget, QtCore.SIGNAL("dropped"), self._getPathFromDrop)
    self.mainLayout.addWidget(self.pathDetectorWidget)

  def setButtons(self):
    self.performButtons = ButtonList(self, texts=['Cancel', 'Clear','Export', 'Confirm'],
                                           callbacks=[self.reject, self._clearList, self._exportPathsToXlsx, None],
                                           tipTexts=['','','', ''], direction='H')
    self.mainLayout.addWidget(self.performButtons)


  def _getPathFromDrop(self, pathsList):
    # return pathsList
    self.populatePathWidget(pathsList)

  def populatePathWidget(self, paths):
    for path in paths:
      item = QtGui.QListWidgetItem(str(path))
      item.setFlags(QtCore.Qt.NoItemFlags)
      self.pathDetectorWidget.addItem(item)

  def _clearList(self):
    self.pathDetectorWidget.clear()

  def _exportPathsToXlsx(self):
    ''' Export a simple xlxs with reference Path '''
    dataFrame = self._createDataFrame()

    fType = 'XLS (*.xls)'
    dialog = QtGui.QFileDialog
    filePath = dialog.getSaveFileName(self, filter=fType)
    dataFrame.to_excel(filePath, sheet_name='Reference', index=False)

  def _createDataFrame(self):
    from pandas import DataFrame
    df = DataFrame({
                   'SpectrumPath': [],
                   'groupName': [],
                   'expType': [],
                   'id': [],
                   'comments': [],
                   'substanceSmiles': [],
                   'stereoInfo': [],
                   'molecularMass': [],
                   'substanceEmpiricalFormula': []
                    },
                   )
    return df
