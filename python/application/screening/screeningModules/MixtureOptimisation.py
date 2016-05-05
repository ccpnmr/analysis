from PyQt4 import QtCore, QtGui
from ccpncore.gui.ButtonList import ButtonList
from ccpncore.gui.Icon import Icon
# from ccpncore.gui.VerticalTab import VerticalTabWidget
from ccpncore.gui.RadioButtons import RadioButtons
from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.DoubleSpinbox import DoubleSpinbox
from ccpncore.gui.Spinbox import Spinbox
from ccpncore.gui.Label import Label
from ccpncore.gui.LineEdit import LineEdit
# from application.core.popups.SampleSetupPopup import ExcludeRegions


class MixtureOptimisation(CcpnDock):

  '''Creates a module to analyse the mixtures'''

  def __init__(self, project):
    super(MixtureOptimisation, self)
    CcpnDock.__init__(self, name='Mixture Optimisation')

    self.project = project
    self.mainWindow = self.project._appBase.mainWindow
    self.dockArea = self.mainWindow.dockArea
    self.generalPreferences = self.project._appBase.preferences.general
    self.colourScheme = self.generalPreferences.colourScheme
    # self.excludeRegions = ExcludeRegions

    ######## ======== Set Main Layout ====== ########
    self.mainFrame = QtGui.QFrame()
    self.mainLayout = QtGui.QVBoxLayout()
    self.mainFrame.setLayout(self.mainLayout)
    self.layout.addWidget(self.mainFrame, 0, 0)

    ######## ======== Set Secondary Layout ====== ########
    self.settingFrameLayout = QtGui.QHBoxLayout()
    self.buttonsFrameLayout = QtGui.QHBoxLayout()
    self.mainLayout.addLayout(self.settingFrameLayout)
    self.mainLayout.addLayout(self.buttonsFrameLayout)

    ######## ======== Set Tabs  ====== ########
    self.tabWidget = QtGui.QTabWidget()
    self.settingFrameLayout.addWidget(self.tabWidget)
    # self.tabWidget.setTabBar(VerticalTabWidget(width=130,height=25))
    self.tabWidget.setTabPosition(QtGui.QTabWidget.West)

    ######## ======== Set Buttons  ====== ########
    self.panelButtons = ButtonList(self, texts=['Show Status', 'Show Graph', 'Cancel', 'Perform'],
                                   callbacks=[None, None, None, None],
                                   icons=[None, None, None, None],
                                   tipTexts=[None, None, None, None],
                                   direction='H')
    self.buttonsFrameLayout.addWidget(self.panelButtons)

    ######## ======== Set 1 Tab  ====== ########
    self.tab1Frame = QtGui.QFrame()
    self.tab1Layout = QtGui.QVBoxLayout()
    self.tab1Frame.setLayout(self.tab1Layout)
    self.tabWidget.addTab(self.tab1Frame, 'Iterations')

    self.selectNumberLabel = Label(self, 'Select Number of Iterations')
    self.iterationBox = Spinbox(self, value=1, min=1)
    self.tab1Layout.addWidget(self.selectNumberLabel)
    self.tab1Layout.addWidget(self.iterationBox)

    ######## ======== Set 2 Tab  ====== ########
    self.tab2Frame = QtGui.QFrame()
    self.tab2Layout = QtGui.QVBoxLayout()
    self.tab2Frame.setLayout(self.tab2Layout)
    self.tabWidget.addTab(self.tab2Frame, 'Minimal overlap')

    self.distanceLabel = Label(self, text="Minimal distance between peaks")
    self.ppmDistance = DoubleSpinbox(self)
    self.tab2Layout.addWidget(self.distanceLabel)
    self.tab2Layout.addWidget(self.ppmDistance)

    ######## ======== Set 3 Tab  ====== ########
    self.tab3Frame = QtGui.QFrame()
    self.tab3Layout = QtGui.QVBoxLayout()
    self.tab3Frame.setLayout(self.tab3Layout)
    self.tabWidget.addTab(self.tab3Frame, 'Exclude Regions')

    # self.excludeRegions = ExcludeRegions()
    # self.tab3Layout.addWidget(self.excludeRegions)


    ######## ======== Set 4 Tab  ====== ########
    self.tab4Frame = QtGui.QFrame()
    self.tab4Layout = QtGui.QVBoxLayout()
    self.tab4Frame.setLayout(self.tab4Layout)
    self.tabWidget.addTab(self.tab4Frame, 'Others')

    self.replaceMixtureLabel = Label(self, text="Replace Mixtures")
    self.replaceRadioButtons = RadioButtons(self,
                                            texts=['Yes', 'No'],
                                            selectedInd=0,
                                            callback=None,
                                            tipTexts=None)
    self.tab4Layout.addWidget(self.replaceMixtureLabel)
    self.tab4Layout.addWidget(self.replaceRadioButtons)