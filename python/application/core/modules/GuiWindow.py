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

from ccpncore.util import Types
from application.core.lib.Window import navigateToNmrResidue, navigateToPeakPosition

from application.core.DropBase import DropBase
from application.core.modules.GuiBlankDisplay import GuiBlankDisplay
from application.core.popups.ExperimentTypePopup import ExperimentTypePopup
from application.core.modules.GuiStripNd import GuiStripNd

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
    #       classModule = importlib.import_module('application.core.modules.Gui' + className)
    #       clazz = getattr(classModule, 'Gui'+className)
    #       guiModule = clazz(self.dockArea, apiModule)
    #     else:
    #       raise Exception("Don't know how to deal with this yet")
    #   self.blankDisplay = None
    # else:
    #   self.blankDisplay = GuiBlankDisplay(self.dockArea)
            
  def deleteBlankDisplay(self):
    """
    Removes blank display from main window dockarea if one is present.
    """
    if self.blankDisplay:
      self.blankDisplay.setParent(None)
      self.blankDisplay = None
          
  def loadData(self, paths=None, text=None):
    """
    Opens a file dialog box and loads data from selected file.
    """
    if text is None:
      text='Load Data'
    if paths is None:
      paths = QtGui.QFileDialog.getOpenFileName(self, text)

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
    """
    Sets shortcuts for functions not specified in the main window menubar
    """
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
    QtGui.QShortcut(QtGui.QKeySequence("t, h"), self, partial(self.toggleHTrace, self))
    QtGui.QShortcut(QtGui.QKeySequence("t, v"), self, partial(self.toggleVTrace, self))

    QtGui.QShortcut(QtGui.QKeySequence("p, c"), self, partial(self.togglePhaseConsole, self))
    ###QtGui.QShortcut(QtGui.QKeySequence("p, h"), self, self.newHPhasingTrace)
    #QtGui.QShortcut(QtGui.QKeySequence("p, v"), self, self.newVPhasingTrace)
    QtGui.QShortcut(QtGui.QKeySequence("p, v"), self, self.setPhasingPivot)
    QtGui.QShortcut(QtGui.QKeySequence("p, r"), self, self.removePhasingTraces)
    QtGui.QShortcut(QtGui.QKeySequence("p, t"), self, self.newPhasingTrace)
    ###QtGui.QShortcut(QtGui.QKeySequence("p, i"), self, self.togglePhasingPivot)

  def traceScaleScale(self, window:'GuiWindow', scale:float):
    """
    Changes the scale of a trace in all spectrum displays of the window.
    """
    for spectrumDisplay in window.spectrumDisplays:
      for strip in spectrumDisplay.strips:
        if isinstance(strip, GuiStripNd):
          for spectrumView in strip.spectrumViews:
            spectrumView.traceScale *= scale
        else:
          pass # should this change the y region??
    
  def traceScaleUp(self, window:'GuiWindow'):
    """
    Doubles the scale for all traces in the specified window.
    """
    self.traceScaleScale(window, 2.0)
    
  def traceScaleDown(self, window:'GuiWindow'):
    """
    Halves the scale for all traces in the specified window.
    """
    self.traceScaleScale(window, 0.5)
    
  def toggleHTrace(self, window:'GuiWindow'):
    """
    Toggles whether horizontal traces are displayed in the specified window.
    """
    for spectrumDisplay in window.spectrumDisplays:
      for strip in spectrumDisplay.strips:
        if isinstance(strip, GuiStripNd):
          strip.toggleHTrace()
    
  def toggleVTrace(self, window:'GuiWindow'):
    """
    Toggles whether vertical traces are displayed in the specified window.
    """
    for spectrumDisplay in window.spectrumDisplays:
      for strip in spectrumDisplay.strips:
        if isinstance(strip, GuiStripNd):
          strip.toggleVTrace()
    
  def togglePhaseConsole(self, window:'GuiWindow'):
    """
    Toggles whether the phasing console is displayed in the specified window.
    """
    for spectrumDisplay in window.spectrumDisplays:
      spectrumDisplay.togglePhaseConsole()
      
  def newPhasingTrace(self):
    strip = self._appBase.current.strip
    if strip and (strip.spectrumDisplay.window is self):
      strip.newPhasingTrace()
    
  """  
  def newHPhasingTrace(self):
    
    strip = self._appBase.current.strip
    if strip and (strip.spectrumDisplay.window is self):
      strip.newHPhasingTrace()
      
  def newVPhasingTrace(self):
    
    strip = self._appBase.current.strip
    if strip and (strip.spectrumDisplay.window is self):
      strip.newVPhasingTrace()
  """
      
  def setPhasingPivot(self):
    
    strip = self._appBase.current.strip
    if strip and (strip.spectrumDisplay.window is self):
      strip.setPhasingPivot()
    
  def removePhasingTraces(self):
    """
    Removes all phasing traces from all strips.
    """
    strip = self._appBase.current.strip
    if strip and (strip.spectrumDisplay.window is self):
      strip.removePhasingTraces()
    
  """
  def togglePhasingPivot(self):
    
    strip = self._appBase.current.strip
    if strip and (strip.spectrumDisplay.window is self):
      strip.togglePhasingPivot()
  """
   
  def clearCurrentPeaks(self):
    """
    Sets current.peaks to an empty list.
    """
    self._appBase.current.peaks = []

  def toggleCrossHairAll(self):
    """
    Toggles whether crosshairs are displayed in all windows.
    """
    for window in self.project.windows:
      window.toggleCrossHair()
    
  def toggleCrossHair(self):
    """
    Toggles whether crosshairs are displayed in all spectrum di
    """
    # toggle crosshairs for the spectrum displays in this window
    for spectrumDisplay in self.spectrumDisplays:
      spectrumDisplay.toggleCrossHair()

  def createMark(self):
    """
    Creates a mark at the current cursor position in the current strip.
    """
    strip = self._appBase.current.strip
    if strip and self.task:
      strip.createMarkAtCursorPosition(self.task)
    
  def clearMarks(self):
    """
    Clears all marks in all windows for the current task.
    """
    for mark in self.task.marks[:]:
      mark.delete()
      
  def toggleGridAll(self):
    """
    Toggles grid display in all windows
    """
    for window in self.project.windows:
      window.toggleGrid()
    
  def toggleGrid(self):
    """
    toggle grid for the spectrum displays in this window.
    """
    for spectrumDisplay in self.spectrumDisplays:
      spectrumDisplay.toggleGrid()
    
  def setCrossHairPosition(self, axisPositionDict:Types.Dict[str, float]):
    """
    Sets crosshair position in all spectrum displays using positions specified in the axisPositionDict.
    """
    for spectrumDisplay in self.spectrumDisplays:
      spectrumDisplay.setCrossHairPosition(axisPositionDict)

  def showExptTypePopup(self, project):
    """
    Displays experiment type popup.
    """
    popup = ExperimentTypePopup(self, project)
    popup.exec_()
