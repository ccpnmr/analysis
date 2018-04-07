"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = ""
__credits__ = ""
__licence__ = ("")
__reference__ = ("")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy$"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================

import sys, os
import math
from threading import Thread
# from queue import Queue
from imageio import imread
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import (QPoint, QSize, Qt, pyqtSignal, pyqtSlot)
from PyQt5.QtWidgets import QApplication, QOpenGLWidget
from ccpn.util.Logging import getLogger
import numpy as np
from pyqtgraph import functions as fn
from ccpn.core.PeakList import PeakList
from ccpn.core.IntegralList import IntegralList

from ccpn.ui.gui.guiSettings import getColours
from ccpn.util.Colour import hexToRgbRatio
from ccpn.ui.gui.guiSettings import CCPNGLWIDGET_BACKGROUND, CCPNGLWIDGET_FOREGROUND, CCPNGLWIDGET_PICKCOLOUR, \
                                    CCPNGLWIDGET_GRID, CCPNGLWIDGET_HIGHLIGHT, \
                                    CCPNGLWIDGET_LABELLING, CCPNGLWIDGET_PHASETRACE
from ccpn.ui.gui.lib.GuiPeakListView import _getScreenPeakAnnotation, _getPeakAnnotation    # temp until I rewrite
import ccpn.util.Phasing as Phasing
from ccpn.util.decorators import singleton
from ccpn.ui.gui.lib.mouseEvents import \
              leftMouse, shiftLeftMouse, controlLeftMouse, controlShiftLeftMouse, \
              middleMouse, shiftMiddleMouse, rightMouse, shiftRightMouse, controlRightMouse, PICK
from ccpn.core.lib.Notifiers import Notifier
from ccpn.framework.PathsAndUrls import fontsPath


@singleton
class GLNotifier(QtWidgets.QWidget):
  """
  Class to control the communication between different strips
  """
  GLSOURCE = 'source'
  GLAXISVALUES = 'axisValues'
  GLMOUSECOORDS = 'mouseCoords'
  GLMOUSEMOVEDDICT = 'mouseMovedict'
  GLSPECTRUMDISPLAY = 'spectrumDisplay'
  GLSTRIP = 'strip'
  GLBOTTOMAXISVALUE = 'bottomAxis'
  GLTOPAXISVALUE = 'topAxis'
  GLLEFTAXISVALUE = 'leftAxis'
  GLRIGHTAXISVALUE = 'rightAxis'
  GLADD1DPHASING = 'add1DPhasing'
  GLCLEARPHASING = 'clearPhasing'
  GLCONTOURS = 'updateContours'
  GLHIGHLIGHTPEAKS = 'glHighlightPeaks'
  GLALLPEAKS = 'glAllPeaks'
  GLPEAKNOTIFY = 'glPeakNotify'
  GLPEAKLISTS = 'glUpdatePeakLists'
  GLPEAKLISTLABELS = 'glUpdatePeakListLabels'
  GLINTEGRALLISTS = 'glUpdateIntegralLists'
  GLGRID = 'glUpdateGrid'
  GLAXES = 'glUpdateAxes'
  GLCURSOR = 'glUpdateCursor'
  GLANY = 'glUpdateAny'
  GLMARKS = 'glUpdateMarks'
  GLTARGETS = 'glTargets'
  GLTRIGGERS = 'glTriggers'
  GLVALUES = 'glValues'
  GLDATA = 'glData'

  _triggerKeywords = (GLHIGHLIGHTPEAKS, GLALLPEAKS,
                      GLPEAKNOTIFY, GLPEAKLISTS, GLPEAKLISTLABELS, GLGRID, GLAXES,
                      GLCURSOR, GLANY, GLMARKS, GLTARGETS, GLTRIGGERS, GLVALUES, GLDATA)

  glXAxisChanged = pyqtSignal(dict)
  glYAxisChanged = pyqtSignal(dict)
  glAllAxesChanged = pyqtSignal(dict)
  glMouseMoved = pyqtSignal(dict)
  glEvent = pyqtSignal(dict)
  glAxisLockChanged = pyqtSignal(dict)

  def __init__(self, parent=None, strip=None):
    super(GLNotifier, self).__init__()
    self._parent = parent
    self._strip = strip

  def emitPaintEvent(self, source=None):
    if source:
      self.glEvent.emit({GLNotifier.GLSOURCE: source,
                          GLNotifier.GLTARGETS: [],
                          GLNotifier.GLTRIGGERS: []})
    else:
      self.glEvent.emit({})

  def emitEvent(self, source=None, strip=None, display=None, targets=[], triggers=[], values={}):
    aDict = {GLNotifier.GLSOURCE: source,
             GLNotifier.GLSTRIP: strip,
             GLNotifier.GLSPECTRUMDISPLAY: display,
             GLNotifier.GLTARGETS: tuple(targets),
             GLNotifier.GLTRIGGERS: tuple(triggers),
             GLNotifier.GLVALUES: values,
             }
    self.glEvent.emit(aDict)

  def emitEventToSpectrumDisplay(self, source=None, strip=None, display=None, targets=[], triggers=[], values={}):
    aDict = {GLNotifier.GLSOURCE: source,
             GLNotifier.GLSTRIP: strip,
             GLNotifier.GLSPECTRUMDISPLAY: display,
             GLNotifier.GLTARGETS: tuple(targets),
             GLNotifier.GLTRIGGERS: tuple(triggers),
             GLNotifier.GLVALUES: values,
             }
    self.glEvent.emit(aDict)

  def _emitAllAxesChanged(self, source=None, strip=None,
                         axisB=None, axisT=None, axisL=None, axisR=None):
    aDict = {GLNotifier.GLSOURCE: source,
             GLNotifier.GLSTRIP: strip,
             GLNotifier.GLSPECTRUMDISPLAY: strip.spectrumDisplay,
             GLNotifier.GLAXISVALUES: {GLNotifier.GLBOTTOMAXISVALUE: axisB,
                                       GLNotifier.GLTOPAXISVALUE: axisT,
                                       GLNotifier.GLLEFTAXISVALUE: axisL,
                                       GLNotifier.GLRIGHTAXISVALUE: axisR}
             }
    self.glAllAxesChanged.emit(aDict)

  def _emitXAxisChanged(self, source=None, strip=None,
                         axisB=None, axisT=None, axisL=None, axisR=None):
    aDict = {GLNotifier.GLSOURCE: source,
             GLNotifier.GLSTRIP: strip,
             GLNotifier.GLSPECTRUMDISPLAY: strip.spectrumDisplay,
             GLNotifier.GLAXISVALUES: {GLNotifier.GLBOTTOMAXISVALUE: axisB,
                                       GLNotifier.GLTOPAXISVALUE: axisT,
                                       GLNotifier.GLLEFTAXISVALUE: axisL,
                                       GLNotifier.GLRIGHTAXISVALUE: axisR}
             }
    self.glXAxisChanged.emit(aDict)

  def _emitMouseMoved(self, source=None, coords=None, mouseMovedDict=None):
    aDict = { GLNotifier.GLSOURCE: source,
              GLNotifier.GLMOUSECOORDS: coords,
              GLNotifier.GLMOUSEMOVEDDICT: mouseMovedDict }
    self.glMouseMoved.emit(aDict)

  def _emitYAxisChanged(self, source=None, strip=None,
                         axisB=None, axisT=None, axisL=None, axisR=None):
    aDict = {GLNotifier.GLSOURCE: source,
             GLNotifier.GLSTRIP: strip,
             GLNotifier.GLSPECTRUMDISPLAY: strip.spectrumDisplay,
             GLNotifier.GLAXISVALUES: {GLNotifier.GLBOTTOMAXISVALUE: axisB,
                                       GLNotifier.GLTOPAXISVALUE: axisT,
                                       GLNotifier.GLLEFTAXISVALUE: axisL,
                                       GLNotifier.GLRIGHTAXISVALUE: axisR}
             }
    self.glYAxisChanged.emit(aDict)

  def _emitAxisLockChanged(self, source=None, strip=None, lock=False):
    aDict = {GLNotifier.GLSOURCE: source,
             GLNotifier.GLSTRIP: strip,
             GLNotifier.GLSPECTRUMDISPLAY: strip.spectrumDisplay,
             GLNotifier.GLVALUES: lock
             }
    self.glAxisLockChanged.emit(aDict)
