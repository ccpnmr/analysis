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
# from ccpncore.lib.Io.Fasta import parseFastaFile, isFastaFormat

from ccpn.lib.Assignment import propagateAssignments
from ccpnmrcore.lib.Window import navigateToNmrResidue, navigateToPeakPosition

from ccpnmrcore.DropBase import DropBase
from ccpnmrcore.modules.GuiBlankDisplay import GuiBlankDisplay
from ccpnmrcore.popups.ExperimentTypePopup import ExperimentTypePopup
from ccpnmrcore.modules.GuiStripNd import GuiStripNd

class GuiWindow(DropBase):
  
  def __init__(self):
    
    DropBase.__init__(self, self._parent._appBase)
    #self._appBase = self._project._appBase
    # self._apiWindow = apiWindow
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
            
  def deleteBlankDisplay(self):
    
    if self.blankDisplay:
      self.blankDisplay.setParent(None)
      self.blankDisplay = None
          
  def loadData(self):

    paths = QtGui.QFileDialog.getOpenFileName(self, 'Load Data')

    # NBNB TBD I assume here that path is either a string or a list lf string paths.
    # NBNB FIXME if incorrect

    if not paths:
      return
    elif isinstance(paths,str):
      paths = [paths]

    self.processDropData(paths, dataType='urls')


  # def addSpectrum1dDisplay(self):
  #     pass
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

  # def addSpectrumNdDisplay(self):
  #   pass
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
    from functools import partial
    #toggleConsoleShortcut = QtGui.QShortcut(QtGui.QKeySequence("p, y"), self, self.toggleConsole)
    QtGui.QShortcut(QtGui.QKeySequence("c, h"), self, self.toggleCrossHairAll)
    QtGui.QShortcut(QtGui.QKeySequence("g, s"), self, self.toggleGridAll)
    QtGui.QShortcut(QtGui.QKeySequence("Del"), self, partial(self._appBase.current.deleteSelected, self))
    QtGui.QShortcut(QtGui.QKeySequence("m, k"), self, self.createMark)
    QtGui.QShortcut(QtGui.QKeySequence("m, c"), self, self.clearMarks)
    QtGui.QShortcut(QtGui.QKeySequence("f, r"), self, partial(navigateToNmrResidue, self._parent.project))
    QtGui.QShortcut(QtGui.QKeySequence("f, p"), self, partial(navigateToPeakPosition, self._parent.project))
    QtGui.QShortcut(QtGui.QKeySequence("e, t"), self, partial(self.showExptTypePopup, self._parent.project))
    QtGui.QShortcut(QtGui.QKeySequence("c, a"), self, partial(propagateAssignments, current=self._appBase.current))
    QtGui.QShortcut(QtGui.QKeySequence("c, z"), self, self.clearCurrentPeaks)

    QtGui.QShortcut(QtGui.QKeySequence("t, u"), self, partial(self.traceScaleUp, self))
    QtGui.QShortcut(QtGui.QKeySequence("t, d"), self, partial(self.traceScaleDown, self))

    QtGui.QShortcut(QtGui.QKeySequence("p, c"), self, partial(self.togglePhaseConsole, self))
    QtGui.QShortcut(QtGui.QKeySequence("p, h"), self, self.newHPhasingTrace) # for now only do H, not V
    QtGui.QShortcut(QtGui.QKeySequence("p, r"), self, self.removePhasingTraces)
    QtGui.QShortcut(QtGui.QKeySequence("p, i"), self, self.togglePhasingPivot)

  def traceScaleScale(self, window, scale):
    for spectrumDisplay in window.spectrumDisplays:
      for strip in spectrumDisplay.strips:
        if isinstance(strip, GuiStripNd):
          for spectrumView in strip.spectrumViews:
            spectrumView.traceScale *= scale
        else:
          pass # should this change the y region??
    
  def traceScaleUp(self, window):
    self.traceScaleScale(window, 2.0)
    
  def traceScaleDown(self, window):
    self.traceScaleScale(window, 0.5)
    
  def togglePhaseConsole(self, window):
    for spectrumDisplay in window.spectrumDisplays:
      spectrumDisplay.togglePhaseConsole()
    
  def newHPhasingTrace(self):
    
    strip = self._appBase.current.strip
    if strip and (strip.spectrumDisplay.window is self):
      strip.newHPhasingTrace()
      
  def removePhasingTraces(self):
    
    strip = self._appBase.current.strip
    if strip and (strip.spectrumDisplay.window is self):
      strip.removePhasingTraces()
    
  def togglePhasingPivot(self):
    
    strip = self._appBase.current.strip
    if strip and (strip.spectrumDisplay.window is self):
      strip.togglePhasingPivot()
      
  def clearCurrentPeaks(self):
    self._appBase.current.peaks = []

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

  def showExptTypePopup(self, project):
    popup = ExperimentTypePopup(self, project)
    popup.exec_()
