"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================
# from ccpn.core.lib.spectrum import Spectrum

__author__ = 'simon'

from PyQt4 import QtGui

from ccpn.ui.gui.widgets import MessageDialog

# from pyqtgraph.modulearea import DockArea
from ccpn.ui.gui.widgets.ModuleArea import CcpnModuleArea
# from ccpnmodel.ccpncore.lib.Io.Fasta import parseFastaFile, isFastaFormat

from ccpn.core.lib.AssignmentLib import propagateAssignments
from ccpn.ui.gui.widgets.FileDialog import FileDialog
import typing
from ccpn.ui.gui.lib.Window import navigateToNmrResidue, navigateToPeakPosition

from ccpn.ui.gui.DropBase import DropBase
from ccpn.ui.gui.modules.GuiBlankDisplay import GuiBlankDisplay

class GuiWindow(DropBase):
  
  def __init__(self):
    
    DropBase.__init__(self, self._parent._appBase)

    self.moduleArea = CcpnModuleArea()
    # self.moduleArea = DockArea()
    self.moduleArea.guiWindow = self
    self.moduleArea.setGeometry(0, 0, 12000, 8000)
    if not self._wrappedData.modules:
      self.blankDisplay = GuiBlankDisplay(self.moduleArea)
      self.moduleArea.addModule(self.blankDisplay, position=None)

            
  def deleteBlankDisplay(self):
    """
    Removes blank display from main window modulearea if one is present.
    """
    if 'BLANK DISPLAY' in self.moduleArea.findAll()[1]:
      blankDisplay = self.moduleArea.findAll()[1]['BLANK DISPLAY']
      blankDisplay.close()
    # if self.blankDisplay:
    #   self.blankDisplay.setParent(None)
    #   self.blankDisplay = None
    #
  def loadData(self, paths=None, text=None):
    """
    Opens a file dialog box and loads data from selected file.
    """
    if text is None:
      text='Load Data'
    if paths is None:
      dialog = FileDialog(self, fileMode=0, text=text, preferences=self._appBase.preferences.general)
      paths = dialog.selectedFiles()[0]

    # NBNB TBD I assume here that path is either a string or a list lf string paths.
    # NBNB FIXME if incorrect

    if not paths:
      return
    elif isinstance(paths,str):
      paths = [paths]

    self.processDropData(paths, dataType='urls')


  def _setShortcuts(self):
    """
    Sets shortcuts for functions not specified in the main window menubar
    """
    # this trampled the menu py shortcut
    from functools import partial
    QtGui.QShortcut(QtGui.QKeySequence("c, h"), self, self.toggleCrossHairAll)
    QtGui.QShortcut(QtGui.QKeySequence("g, s"), self, self.toggleGridAll)
    QtGui.QShortcut(QtGui.QKeySequence("Del"), self, partial(self.deleteSelectedPeaks))
    QtGui.QShortcut(QtGui.QKeySequence("m, k"), self, self.createMark)
    QtGui.QShortcut(QtGui.QKeySequence("m, c"), self, self.clearMarks)
    QtGui.QShortcut(QtGui.QKeySequence("f, n"), self, partial(navigateToNmrResidue, self._parent.project))
    QtGui.QShortcut(QtGui.QKeySequence("f, p"), self, partial(navigateToPeakPosition, self._parent.project))
    QtGui.QShortcut(QtGui.QKeySequence("c, a"), self, partial(propagateAssignments, current=self._appBase.current))
    QtGui.QShortcut(QtGui.QKeySequence("c, z"), self, self._clearCurrentPeaks)
    QtGui.QShortcut(QtGui.QKeySequence("t, u"), self, partial(self.traceScaleUp, self))
    QtGui.QShortcut(QtGui.QKeySequence("t, d"), self, partial(self.traceScaleDown, self))
    QtGui.QShortcut(QtGui.QKeySequence("t, h"), self, partial(self.toggleHTrace, self))
    QtGui.QShortcut(QtGui.QKeySequence("t, v"), self, partial(self.toggleVTrace, self))
    QtGui.QShortcut(QtGui.QKeySequence("p, v"), self, self.setPhasingPivot)
    QtGui.QShortcut(QtGui.QKeySequence("p, r"), self, self.removePhasingTraces)
    QtGui.QShortcut(QtGui.QKeySequence("p, t"), self, self.newPhasingTrace)
    QtGui.QShortcut(QtGui.QKeySequence("w, 1"), self, self.getCurrentPositionAndStrip)



  def deleteSelectedPeaks(self, parent=None):

    # NBNB Moved here from Current
    # NBNB TODO: more general deletion

    current = self._appBase.current
    peaks = current.peaks
    if peaks:
      n = len(peaks)
      title = 'Delete Peak%s' % ('' if n == 1 else 's')
      msg ='Delete %sselected peak%s?' % ('' if n == 1 else '%d ' % n, '' if n == 1 else 's')
      if MessageDialog.showYesNo(title, msg, parent):
        current.project.deleteObjects(*peaks)
        # no longer needed - echo done from function
        # for peak in peaks[:]:
        #   if current.project._appBase.ui.mainWindow is not None:
        #     mainWindow = current.project._appBase.ui.mainWindow
        #   else:
        #     mainWindow = current.project._appBase._mainWindow
        #   mainWindow.pythonConsole.writeConsoleCommand('peak.delete()', peak=peak)
        #   peak.delete()



  def getCurrentPositionAndStrip(self):
    current = self._appBase.current
    current.strip = current.viewBox.parentObject().parent
    position = [current.viewBox.position.x(),
                current.viewBox.position.y()]
    if len(current.strip.axisOrder) > 2:
      for axis in current.strip.orderedAxes[2:]:
        position.append(axis.position)
    current.position = tuple(position)
    return current.strip, current.position



  def traceScaleScale(self, window:'GuiWindow', scale:float):
    """
    Changes the scale of a trace in all spectrum displays of the window.
    """
    for spectrumDisplay in window.spectrumDisplays:
      if not spectrumDisplay.is1D:
        for strip in spectrumDisplay.strips:
          for spectrumView in strip.spectrumViews:
            spectrumView.traceScale *= scale
    
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
      if not spectrumDisplay.is1D:
        for strip in spectrumDisplay.strips:
          strip.toggleHorizontalTrace()
    
  def toggleVTrace(self, window:'GuiWindow'):
    """
    Toggles whether vertical traces are displayed in the specified window.
    """
    for spectrumDisplay in window.spectrumDisplays:
      if not spectrumDisplay.is1D:
        for strip in spectrumDisplay.strips:
          strip.toggleVerticalTrace()
    
  def togglePhaseConsole(self, window:'GuiWindow'):
    """
    Toggles whether the phasing console is displayed in the specified window.
    """
    for spectrumDisplay in window.spectrumDisplays:
      spectrumDisplay.togglePhaseConsole()
      
  def newPhasingTrace(self):
    strip = self._appBase.current.strip
    if strip and (strip.spectrumDisplay.window is self):
      strip._newPhasingTrace()

      
  def setPhasingPivot(self):
    
    strip = self._appBase.current.strip
    if strip and (strip.spectrumDisplay.window is self):
      strip._setPhasingPivot()
    
  def removePhasingTraces(self):
    """
    Removes all phasing traces from all strips.
    """
    strip = self._appBase.current.strip
    if strip and (strip.spectrumDisplay.window is self):
      strip.removePhasingTraces()

   
  def _clearCurrentPeaks(self):
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
      strip._createMarkAtCursorPosition(self.task)
    
  def clearMarks(self):
    """
    Clears all marks in all windows for the current task.
    """
    for mark in self.task.marks[:]:
      mark.delete()
    for spectrumDisplay in self.spectrumDisplays:
      for strip in spectrumDisplay.strips:
        for atomLabel in strip.xAxisAtomLabels:
          strip.plotWidget.removeItem(atomLabel)
        for atomLabel in strip.yAxisAtomLabels:
          strip.plotWidget.removeItem(atomLabel)

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
    
  def _setCrossHairPosition(self, axisPositionDict:typing.Dict[str, float]):
    """
    # CCPN INTERNAL - called in mouseMoved method of GuiStrip
    Sets crosshair position in all spectrum displays using positions specified in the axisPositionDict.
    """
    for spectrumDisplay in self.spectrumDisplays:
      spectrumDisplay._setCrossHairPosition(axisPositionDict)

