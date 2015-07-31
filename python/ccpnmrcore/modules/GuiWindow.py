"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
# from ccpn.lib.spectrum import Spectrum

__author__ = 'simon'

from PyQt4 import QtGui

from pyqtgraph.dockarea import DockArea
from ccpncore.lib.spectrum import Util as specUtil
# from ccpncore.lib.Io.Fasta import parseFastaFile, isFastaFormat

from ccpnmrcore.Base import Base as GuiBase
from ccpnmrcore.modules.GuiBlankDisplay import GuiBlankDisplay


class GuiWindow(GuiBase):
  
  def __init__(self):
    
    GuiBase.__init__(self, self._parent._appBase)
    #self._appBase = self._project._appBase
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
          
  def loadData(self):

    paths = QtGui.QFileDialog.getOpenFileName(self, 'Load Data')

    # NBNB TBD I assume here that path is eitehr a string or a list lf string paths.
    # NBNB FIXME if incorrect

    if not paths:
      return
    elif isinstance(paths,str):
      paths = [paths]

    # NBNB TBD FIXME GuiWindow is not a subclass of DropBase. How to get hold of the function?
    self.processsDropData(paths, dataType='urls')

    # if not path:
    #   return
    # elif isFastaFormat(path):
    #   try:
    #     # NBNB TBD next line does ont make sense
    #     sequences = parseFastaFile(path[0])
    #     for sequence in sequences:
    #       self._parent._appBase.project.makeSimpleChain(sequence=sequence[1],
    #                                                     compoundName=sequence[0],
    #                                                     molType='protein')
    #
    #   except:
    #     print("DEBUG Error loading FASTA file %s" % path)
    # else:
    #   # Where we are now this can only be a spectrum
    #   spectrum = self.project.loadSpectrum(path)
    #
    #   if spectrum:
    #     msg = spectrum.name+' loaded'
    #     mainWindow = self._appBase.mainWindow
    #     spectrumItem = mainWindow.sidebar.addSpectrumToItem(spectrum)
    #     mainWindow.statusBar().showMessage(msg)
    #     mainWindow.pythonConsole.write("project.loadSpectrum('"+path+"')\n")

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
    
    # this trampled the menu py shortcut
    #toggleConsoleShortcut = QtGui.QShortcut(QtGui.QKeySequence("p, y"), self, self.toggleConsole)
    QtGui.QShortcut(QtGui.QKeySequence("c, h"), self, self.toggleCrossHairAll)
    QtGui.QShortcut(QtGui.QKeySequence("g, s"), self, self.toggleGridAll)
    QtGui.QShortcut(QtGui.QKeySequence("Del"), self, lambda: self._appBase.current.deleteSelected(self))
    QtGui.QShortcut(QtGui.QKeySequence("m, k"), self, self.createMark)
    QtGui.QShortcut(QtGui.QKeySequence("m, c"), self, self.clearMarks)
   
  def toggleCrossHairAll(self):
    # toggle crosshairs in all windows
    for window in self.project.windows:
      window.toggleCrossHair()
    
  def toggleCrossHair(self): 
    # toggle crosshairs for the spectrum displays in this window
    for spectrumDisplay in self.spectrumDisplays:
      spectrumDisplay.toggleCrossHair()

  def createMark(self):
    strip = self._appBase.current.strip
    if strip and self.task:
      strip.createMarkAtCursorPosition(self.task)
    
  def clearMarks(self):
    
    for mark in self.task.marks[:]:
      mark.delete()
      
  def toggleGridAll(self):
    # toggle grid in all windows
    for window in self.project.windows:
      window.toggleGrid()
    
  def toggleGrid(self):
    # toggle grid for the spectrum displays in this window
    for spectrumDisplay in self.spectrumDisplays:
      spectrumDisplay.toggleGrid()
    
  def setCrossHairPosition(self, axisPositionDict):
    for spectrumDisplay in self.spectrumDisplays:
      spectrumDisplay.setCrossHairPosition(axisPositionDict)
  
  # def dropEvent(self, event):
  #   '''if object can be dropped into this area, accept dropEvent, otherwise throw an error
  #       spectra, projects and peak lists can be dropped into this area but nothing else
  #       if project is dropped, it is loaded,
  #       if spectra/peak lists are dropped, these are displayed in the side bar but not displayed in
  #       spectrumPane
  #       '''
  #
  #   event.accept()
  #   data = event.mimeData()
  #   if isinstance(self.parent, QtGui.QGraphicsScene):
  #     event.ignore()
  #     return
  #
  #   if event.mimeData().urls():
  #
  #
  #     filePaths = [url.path() for url in event.mimeData().urls()]
  #
  #     if filePaths:
  #
  #       if len(filePaths) == 1:
  #         global project
  #         currentProjectDir = filePaths[0]
  #
  #         self.openProject(projectDir=filePaths[0])
  #               # peakListItem.setData(0, QtCore.Qt.UserRole + 1, peakList)
  #               # peakListItem.setData(1, QtCore.Qt.DisplayRole, str(peakList))
  #         # self.statusBar().showMessage(msg)
  #         # self.pythonConsole.write("openProject('"+currentProjectDir.name+"')\n")
  #         # list1 = self.spectrumItem.takeChildren()
  #         # for item in list1:
  #
  #       else:
  #         spectrumFormat = specUtil.getSpectrumFileFormat(filePaths[0])
  #
  #         if spectrumFormat:
  #           event.acceptProposedAction()
  #           dataSource = self.project.loadSpectrum(filePaths[0])
  #
  #
  #         # if dataSource.numDim == 1:
  #         #   data = Spectrum1dItem(self.current.pane,dataSource).spectralData
  #         #   self.widget1.plot(data, pen={'color':(random.randint(0,255),random.randint(0,255),random.randint(0,255))})
  #         # elif dataSource.numDim > 1:
  #         #   data = SpectrumNdItem(self.spectrumPane,dataSource).spectralData
  #         #   self.widget1.plot(data, pen={'color':(random.randint(0,255),random.randint(0,255),random.randint(0,255))})
  #           msg = dataSource.name+' loaded'
  #           self.statusBar().showMessage(msg)
  #           self._appBase.mainWindow.pythonConsole.write("loadSpectrum('"+filePaths[0]+"')\n")
  #
  #         # peakListFormat = getPeakListFileFormat(filePaths[0])
  #         # if peakListFormat:
  #         #   event.acceptProposedAction()
  #         #   self.mainApp.openPeakList(filePaths[0])
  #         #   return
  #
  #         else:
  #           event.ignore()
  #
  #     else:
  #       event.ignore()
  #
  #   else:
  #     event.ignore()
