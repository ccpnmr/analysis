"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification
#=========================================================================================
__author__ = "$Author: CCPN $"
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:40:40 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"

#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: simon $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


from PyQt4 import QtCore, QtGui

import typing
from ccpn.core.lib import AssignmentLib

from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets.CcpnModuleArea import CcpnModuleArea
from ccpn.core.lib.AssignmentLib import propagateAssignments
from ccpn.ui.gui.widgets.FileDialog import FileDialog
from ccpn.ui.gui.lib.SpectrumDisplay import navigateToPeakPosition
from ccpn.ui.gui import guiSettings


#TODO:WAYNE: incorporate most functionality in GuiMainWindow. See also MainMenu
# For readability there should be a class
# _MainWindowShortCuts which (Only!) has the shortcut definitions and the callbacks to initiate them.
# The latter should all be private methods!

class GuiWindow():
  
  def __init__(self, application):
    self.application = application

  def _setShortcuts(self):
    """
    Sets shortcuts for functions not specified in the main window menubar
    """
    # this trampled the menu py shortcut
    from functools import partial
    context = QtCore.Qt.ApplicationShortcut
    QtGui.QShortcut(QtGui.QKeySequence("c, h"), self, self.toggleCrossHairAll, context=context)
    QtGui.QShortcut(QtGui.QKeySequence("g, s"), self, self.toggleGridAll, context=context)
    QtGui.QShortcut(QtGui.QKeySequence("Del"), self, partial(self.deleteSelectedPeaks), context=context)
    QtGui.QShortcut(QtGui.QKeySequence("m, k"), self, self.createMark, context=context)
    QtGui.QShortcut(QtGui.QKeySequence("m, c"), self, self.clearMarks, context=context)
    # QtGui.QShortcut(QtGui.QKeySequence("f, n"), self, partial(navigateToNmrResidue, self._parent.project), context=context)
    QtGui.QShortcut(QtGui.QKeySequence("f, p"), self, partial(navigateToPeakPosition, self._parent.project),
                    context=context)
    QtGui.QShortcut(QtGui.QKeySequence("c, a"), self, partial(AssignmentLib.propagateAssignments,
                                                              current=self.application.current),
                    context=context)
    QtGui.QShortcut(QtGui.QKeySequence("c, z"), self, self._clearCurrentPeaks, context=context)
    QtGui.QShortcut(QtGui.QKeySequence("t, u"), self, partial(self.traceScaleUp, self), context=context)
    QtGui.QShortcut(QtGui.QKeySequence("t, d"), self, partial(self.traceScaleDown, self), context=context)
    QtGui.QShortcut(QtGui.QKeySequence("t, h"), self, partial(self.toggleHTrace, self), context=context)
    QtGui.QShortcut(QtGui.QKeySequence("t, v"), self, partial(self.toggleVTrace, self), context=context)
    QtGui.QShortcut(QtGui.QKeySequence("p, v"), self, self.setPhasingPivot, context=context)
    QtGui.QShortcut(QtGui.QKeySequence("p, r"), self, self.removePhasingTraces, context=context)
    QtGui.QShortcut(QtGui.QKeySequence("p, t"), self, self.newPhasingTrace, context=context)
    QtGui.QShortcut(QtGui.QKeySequence("w, 1"), self, self.getCurrentPositionAndStrip, context=context)
    QtGui.QShortcut(QtGui.QKeySequence("r, p"), self, self.refitCurrentPeaks, context=context)

  def setUserShortcuts(self, preferences=None):

    from functools import reduce, partial

    context = QtCore.Qt.ApplicationShortcut
    userShortcuts = preferences.shortcuts
    for shortcut, function in userShortcuts.items():

      if function.split('(')[0] == 'runMacro':
        QtGui.QShortcut(QtGui.QKeySequence("%s, %s" % (shortcut[0], shortcut[1])),
                  self, partial(self.namespace['runMacro'], function.split('(')[1].split(')')[0]), context=context)

      else:
        stub = self.namespace.get(function.split('.')[0])
        QtGui.QShortcut(QtGui.QKeySequence("%s, %s" % (shortcut[0], shortcut[1])), self,
                        reduce(getattr, function.split('.')[1:], stub), context=context)

  def deleteSelectedPeaks(self, parent=None):

    # NBNB Moved here from Current
    # NBNB TODO: more general deletion

    current = self.application.current
    peaks = current.peaks
    if peaks:
      n = len(peaks)
      title = 'Delete Peak%s' % ('' if n == 1 else 's')
      msg ='Delete %sselected peak%s?' % ('' if n == 1 else '%d ' % n, '' if n == 1 else 's')
      if MessageDialog.showYesNo(title, msg, parent):
        current.project.deleteObjects(*peaks)

  def getCurrentPositionAndStrip(self):
    current = self.application.current
    """
    # this function is called as a shortcut macro ("w1") but
    # with the code commented out that is pretty pointless.
    # current.strip and current.cursorPosition are now set by
    # clicking on a position in the strip so this commented
    # out code is no longer useful, and this function might
    # be more generally useful, so leave the brief version
    current.strip = current.viewBox.parentObject().parent
    cursorPosition = (current.viewBox.position.x(),
                      current.viewBox.position.y())
    # if len(current.strip.axisOrder) > 2:
    #   for axis in current.strip.orderedAxes[2:]:
    #     position.append(axis.position)
    # current.position = tuple(position)
    current.cursorPosition = cursorPosition
    """
    return current.strip, current.cursorPosition

  def _getPeaksParams(self, peaks):
    params = []
    for peak in peaks:
      params.append((peak.height, peak.position, peak.lineWidths))
    return params

  def _setPeaksParams(self, peaks, params):
    for n, peak in enumerate(peaks):
      height, position, lineWidths = params[n]
      peak.height = height
      peak.position = position
      peak.lineWidths = lineWidths

  def refitCurrentPeaks(self):
    peaks = self.application.current.peaks
    if not peaks:
      return

    project = peaks[0].project
    undo = project._undo

    project.newUndoPoint()
    undo.increaseBlocking()

    currentParams = self._getPeaksParams(peaks)
    try:
      AssignmentLib.refitPeaks(peaks)
    finally:
      undo.decreaseBlocking()
      undo.newItem(self._setPeaksParams, self._setPeaksParams, undoArgs=[peaks, currentParams],
                   redoArgs=[peaks, self._getPeaksParams(peaks)])


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
    strip = self.application.current.strip
    if strip and (strip.spectrumDisplay.window is self):
      strip._newPhasingTrace()

      
  def setPhasingPivot(self):
    
    strip = self.application.current.strip
    if strip and (strip.spectrumDisplay.window is self):
      strip._setPhasingPivot()
    
  def removePhasingTraces(self):
    """
    Removes all phasing traces from all strips.
    """
    strip = self.application.current.strip
    if strip and (strip.spectrumDisplay.window is self):
      strip.removePhasingTraces()

   
  def _clearCurrentPeaks(self):
    """
    Sets current.peaks to an empty list.
    """
    # self.application.current.peaks = []
    self.application.current.clearPeaks()

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
    strip = self.application.current.strip
    if strip and self.task:
      strip._createMarkAtCursorPosition(self.task)
    
  def clearMarks(self):
    """
    Clears all marks in all windows for the current task.
    """
    for mark in self.task.marks[:]:
      mark.delete()

  def markPositions(self, axisCodes, chemicalShifts):
    """
    Create marks based on the axisCodes and adds annotations where appropriate.

    :param axisCodes: The axisCodes making a mark for
    :param chemicalShifts: A list or tuple of ChemicalShifts at whose values the marks should be made
    """
    project = self.application.project
    project._startCommandEchoBlock('markPositions', project, axisCodes, chemicalShifts)
    try:
      task = self.task

      colourDict = guiSettings.MARK_LINE_COLOUR_DICT  # maps atomName --> colour
      for ii, axisCode in enumerate(axisCodes):
        for chemicalShift in chemicalShifts[ii]:
          atomName = chemicalShift.nmrAtom.name
          # TODO: the below fails, for example, if nmrAtom.name = 'Hn', can that happen?
          colour = colourDict.get(atomName[:min(2,len(atomName))])
          if colour:
            task.newMark(colour, [chemicalShift.value], [axisCode], labels=[atomName])
          else:
            task.newMark('white', [chemicalShift.value], [axisCode])

    finally:
      project._endCommandEchoBlock()

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

