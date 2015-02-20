from ccpn.lib.wrapper import Spectrum

__author__ = 'simon'

from PySide import QtGui

from pyqtgraph.dockarea import DockArea
from ccpn.lib.wrapper.Project import loadSpectrum
from ccpncore.lib.spectrum import Util as specUtil
from ccpnmrcore.Base import Base as GuiBase
from ccpnmrcore.modules.GuiBlankDisplay import GuiBlankDisplay
from ccpnmrcore.modules.GuiStripDisplay1d import GuiStripDisplay1d
from ccpnmrcore.modules.GuiStripDisplayNd import GuiStripDisplayNd

class GuiWindow(GuiBase):
  
  def __init__(self):
    
    self._appBase = self._project._appBase
    # self.apiWindow = apiWindow
    self.dockArea = DockArea()
    self.dockArea.guiWindow = self
    self.dockArea.setGeometry(0, 0, 12000, 8000)
    if not self._wrappedData.modules:
      self.blankDisplay = GuiBlankDisplay(self.dockArea)

    
    # apiModules = apiWindow.sortedModules()
    # if apiModules:
    #   for apiModule in apiModules:
    #     if isinstance(apiModule, SpectrumDisplay):
    #       className = apiModule.className
    #       classModule = importlib.import_module('ccpnmrcore.modules.Gui' + className)
    #       clazz = getattr(classModule, 'Gui'+className)
    #       guiModule = clazz(self.dockArea, apiModule)
    #     else:
    #       raise Exception("Don't know how to deal with this yet")
    #   self.blankDisplay = None
    # else:
    #   self.blankDisplay = GuiBlankDisplay(self.dockArea)
        
  def removeBlankDisplay(self):
    
    if self.blankDisplay:
      self.blankDisplay.setParent(None)
      self.blankDisplay = None
      
  ##def displayFirstSpectrum(self, spectrum):

    ##assert self.blankDisplay
    
    ##self.blankDisplay.setParent(None)
    ##self.blankDisplay = None

    # NBNB TBD consider whether this should be refactored now we use createSpectrumDisplay
    ##self.createSpectrumDisplay(spectrum)
    ##self._appBase.guiWindows.append(self)
    # apiGuiTask = self.apiWindow.windowStore.memopsRoot.findFirstGuiTask(name='Ccpn') # constant should be stored somewhere
    # #axisCodes = spectrum.axisCodes
    # axisCodes = Spectrum.getAxisCodes(spectrum)
    # if spectrum.dimensionCount == 1:
    #   apiStripDisplay = apiGuiTask.newStripDisplay1d(name='Module1_1D', axisCodes=axisCodes, axisOrder=axisCodes, stripDirection='Y')
    #   guiStripDisplay = GuiStripDisplay1d(self.dockArea, apiStripDisplay)
    # else:
    #   apiStripDisplay = apiGuiTask.newStripDisplayNd(name='Module2_ND', axisCodes=axisCodes, axisOrder=axisCodes, stripDirection='Y')
    #   guiStripDisplay = GuiStripDisplayNd(self.dockArea, apiStripDisplay)
    #   guiStripDisplay.guiStrips[0].addSpinSystemLabel(guiStripDisplay.stripFrame, 0)
    # # if spectrum.dimensionCount > 2:
    # #   for i in range(spectrum.dimensionCount-2):
    # #     guiStripDisplay.guiStrips[0].addPlaneToolbar(guiStripDisplay.stripFrame, 0)
    #
    # guiStripDisplay.addSpectrum(spectrum)
    # self.apiWindow.addModule(apiStripDisplay)
    
  def loadSpectra(self, directory=None):
    
    if directory == None:
      directory = QtGui.QFileDialog.getOpenFileName(self, 'Open Spectra')
      spectrum = loadSpectrum(self.project,directory[0])

    else:
      spectrum = loadSpectrum(self.project,directory)
      # self.leftWidget.addItem(self.leftWidget.spectrumItem,spectrum)

    msg = spectrum.name+' loaded'
    mainWindow = self._appBase.mainWindow
    mainWindow.leftWidget.addItem(mainWindow.leftWidget.spectrumItem,spectrum)
    mainWindow.statusBar().showMessage(msg)
    if len(directory) == 1:
      mainWindow.pythonConsole.write("project.loadSpectrum('"+directory+"')\n")
    else:
      mainWindow.pythonConsole.write("project.loadSpectrum('"+directory[0]+"')\n")

  def addSpectrum1dDisplay(self):
      pass
    # #newModule = Spectrum1dPane(parent=self, title='Module %s' % str(self.moduleCount+1),
    # newModule = Spectrum1dDisplay(title='Module %s_1D' % str(self.moduleCount+1),
    #                            current=self.current, pid='QP:%s' % str(self.moduleCount+1),
    #                            preferences=self.preferences, mainWindow=self)
    # self.panes[newModule.pid] = newModule
    # newModule.project = self.project
    # newModule.current = self.current
    # self.moduleCount+=1
    #
    # self.dockArea.addDock(newModule.dock)
    # return newModule

  def addSpectrumNdDisplay(self):
    pass
    # #newModule = SpectrumNdPane(parent=self, title='Module %s' % str(self.moduleCount+1),
    # newModule = SpectrumNdDisplay(title='Module %s_Nd' % str(self.moduleCount+1),
    #                            current=self.current, pid='QP:%s' % str(self.moduleCount+1),
    #                            preferences=self.preferences, mainWindow=self)
    # self.panes[newModule.pid] = newModule
    # newModule.project = self.project
    # newModule.current = self.current
    # self.moduleCount+=1
    #
    # self.dockArea.addDock(newModule.dock)
    # return newModule

  def setShortcuts(self):
    
    toggleConsoleShortcut = QtGui.QShortcut(QtGui.QKeySequence("p, y"), self, self.toggleConsole)
    toggleCrossHairShortcut = QtGui.QShortcut(QtGui.QKeySequence("c, h"), self, self.toggleCrossHair)
    toggleGridShortcut = QtGui.QShortcut(QtGui.QKeySequence("g, s"), self, self.toggleGrid)

  def dropEvent(self, event):
    '''if object can be dropped into this area, accept dropEvent, otherwise throw an error
        spectra, projects and peak lists can be dropped into this area but nothing else
        if project is dropped, it is loaded,
        if spectra/peak lists are dropped, these are displayed in the side bar but not displayed in
        spectrumPane
        '''

    event.accept()
    data = event.mimeData()
    if isinstance(self.parent, QtGui.QGraphicsScene):
      event.ignore()
      return

    if event.mimeData().urls():


      filePaths = [url.path() for url in event.mimeData().urls()]

      if filePaths:

        if len(filePaths) == 1:
          global project
          currentProjectDir = filePaths[0]

          self.openProject(projectDir=filePaths[0])
                # peakListItem.setData(0, QtCore.Qt.UserRole + 1, peakList)
                # peakListItem.setData(1, QtCore.Qt.DisplayRole, str(peakList))
          # self.statusBar().showMessage(msg)
          # self.pythonConsole.write("openProject('"+currentProjectDir.name+"')\n")
          # list1 = self.spectrumItem.takeChildren()
          # for item in list1:

        else:
          spectrumFormat = specUtil.getSpectrumFileFormat(filePaths[0])

          if spectrumFormat:
            event.acceptProposedAction()
            dataSource = loadSpectrum(self.project,filePaths[0])


          # if dataSource.numDim == 1:
          #   data = Spectrum1dItem(self.current.pane,dataSource).spectralData
          #   self.widget1.plot(data, pen={'color':(random.randint(0,255),random.randint(0,255),random.randint(0,255))})
          # elif dataSource.numDim > 1:
          #   data = SpectrumNdItem(self.spectrumPane,dataSource).spectralData
          #   self.widget1.plot(data, pen={'color':(random.randint(0,255),random.randint(0,255),random.randint(0,255))})
            msg = dataSource.name+' loaded'
            self.statusBar().showMessage(msg)
            self._appBase.mainWindow.pythonConsole.write("loadSpectrum('"+filePaths[0]+"')\n")

          # peakListFormat = getPeakListFileFormat(filePaths[0])
          # if peakListFormat:
          #   event.acceptProposedAction()
          #   self.mainApp.openPeakList(filePaths[0])
          #   return

          else:
            event.ignore()

      else:
        event.ignore()

    else:
      event.ignore()