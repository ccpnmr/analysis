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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date$"

#=========================================================================================
# Start of code
#=========================================================================================

import os
import sys
import math
import json
import re
import time
import numpy as np
from functools import partial
# from threading import Thread
# from queue import Queue
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QPoint, QSize, Qt, pyqtSlot
from PyQt5.QtWidgets import QApplication, QOpenGLWidget
from ccpn.util.Logging import getLogger
from pyqtgraph import functions as fn
from ccpn.core.PeakList import PeakList
from ccpn.core.Integral import Integral
# from ccpn.core.IntegralList import IntegralList
from ccpn.ui.gui.lib.mouseEvents import getCurrentMouseMode
from ccpn.ui.gui.lib.GuiStrip import DefaultMenu, PeakMenu, IntegralMenu, \
    MultipletMenu, PhasingMenu

from ccpn.core.lib.Cache import cached

# from ccpn.util.Colour import getAutoColourRgbRatio
from ccpn.ui.gui.guiSettings import CCPNGLWIDGET_BACKGROUND, CCPNGLWIDGET_FOREGROUND, CCPNGLWIDGET_PICKCOLOUR, \
    CCPNGLWIDGET_GRID, CCPNGLWIDGET_HIGHLIGHT, CCPNGLWIDGET_INTEGRALSHADE, \
    CCPNGLWIDGET_LABELLING, CCPNGLWIDGET_PHASETRACE, getColours, \
    CCPNGLWIDGET_HEXBACKGROUND, CCPNGLWIDGET_ZOOMAREA, CCPNGLWIDGET_PICKAREA, \
    CCPNGLWIDGET_SELECTAREA, CCPNGLWIDGET_ZOOMLINE, CCPNGLWIDGET_MOUSEMOVELINE, \
    CCPNGLWIDGET_HARDSHADE
# from ccpn.ui.gui.lib.GuiPeakListView import _getScreenPeakAnnotation, _getPeakAnnotation  # temp until I rewrite
import ccpn.util.Phasing as Phasing
from ccpn.ui.gui.lib.mouseEvents import \
    leftMouse, shiftLeftMouse, controlLeftMouse, controlShiftLeftMouse, controlShiftRightMouse, \
    middleMouse, shiftMiddleMouse, rightMouse, shiftRightMouse, controlRightMouse, PICK


# from ccpn.core.lib.Notifiers import Notifier

try:
    # used to test whether all the arrays are defined correctly
    # os.environ.update({'PYOPENGL_ERROR_ON_COPY': 'true'})

    from OpenGL import GL, GLU, GLUT
except ImportError:
    app = QtWidgets.QApplication(sys.argv)
    QtWidgets.QMessageBox.critical(None, "OpenGL CCPN",
                                   "PyOpenGL must be installed to run this example.")
    sys.exit(1)

from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLNotifier import GLNotifier
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLGlobal import GLGlobalData
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLFonts import GLString
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLArrays import GLRENDERMODE_IGNORE, GLRENDERMODE_DRAW, \
    GLRENDERMODE_RESCALE, GLRENDERMODE_REBUILD, \
    GLREFRESHMODE_NEVER, GLREFRESHMODE_ALWAYS, \
    GLREFRESHMODE_REBUILD, GLVertexArray, \
    GLSymbolArray, GLLabelArray
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLViewports import GLViewports
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLWidgets import GLExternalRegion, \
    GLRegion, REGION_COLOURS, GLInfiniteLine
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLLabelling import GLpeakNdLabelling, GLpeak1dLabelling, \
    GLintegral1dLabelling, GLintegralNdLabelling, \
    GLmultiplet1dLabelling, GLmultipletNdLabelling
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLExport import GLExporter
import ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs as GLDefs
from ccpn.util.Common import getAxisCodeMatch, getAxisCodeMatchIndices
from typing import Tuple
from ccpn.util.Constants import AXIS_FULLATOMNAME, AXIS_MATCHATOMTYPE, AXIS_ACTIVEAXES, \
    DOUBLEAXIS_ACTIVEAXES, DOUBLEAXIS_FULLATOMNAME, DOUBLEAXIS_MATCHATOMTYPE
from ccpn.ui.gui.guiSettings import textFont, getColours, STRIPHEADER_BACKGROUND, \
    STRIPHEADER_FOREGROUND, GUINMRRESIDUE

from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.ui.gui.lib.mouseEvents import getMouseEventDict
from ccpn.core.lib.ContextManagers import undoBlock
from ccpn.util.decorators import profile


class GLSimpleStrings():
    """
    Class to handle grouped labels with an optional infinite line if required
    Labels can be locked to screen co-ordinates or top/bottom, left/right justified
    """

    def __init__(self, parent=None, strip=None, name=None, resizeGL=False,
                 blendMode=False, drawMode=GL.GL_LINES, dimension=2):
        """Initialise the class
        """
        self._GLParent = parent
        self.strip = strip
        self.name = name
        self.resizeGL = resizeGL

        self.current = self.strip.current if self.strip else None

        self.strings = {}

    def buildStrings(self):
        for spectrumView in self._GLParent._ordering:  # strip.spectrumViews:

            if spectrumView.isDeleted:
                continue

            if spectrumView not in self.strings:
                self.addString(spectrumView, (0, 0),
                               colour=spectrumView.spectrum.positiveContourColour, alpha=1.0,
                               lock=GLDefs.LOCKLEFT)

    def drawStrings(self):
        if self.strip.isDeleted:
            return

        self.buildStrings()

        # iterate over and draw all strings for visible spectrumViews
        for specView, string in self.strings.items():
            if specView in self._GLParent._visibleOrdering and string.object and not string.object.isDeleted:
                string.drawTextArrayVBO(enableVBO=True)

    def objectText(self, obj):
        """return the string to be used for the label
        To be subclassed as required
        """
        return str(obj.spectrum.id)

    def objectInstance(self, obj):
        """return the object instance to insert into the string
        To be subclassed as required
        """
        return obj.spectrum

    def objectSettings(self, string, obj):
        """Set up class specific settings for the new string
        To be subclassed as required
        """
        string.spectrumView = obj

    def addString(self, obj, position=(0, 0), axisCodes=None, colour="#FF0000", alpha=1.0,
                  lock=GLDefs.LOCKNONE, serial=0):
        """Add a new string to the list
        """
        GLp = self._GLParent
        colR = int(colour.strip('# ')[0:2], 16) / 255.0
        colG = int(colour.strip('# ')[2:4], 16) / 255.0
        colB = int(colour.strip('# ')[4:6], 16) / 255.0

        # NOTE:ED check axis units - assume 'ppm' for the minute

        # fixed ppm position - rescale will do the rest
        textX = position[0]
        textY = position[1]

        # create new label, should be ready to draw
        newLabel = GLString(text=self.objectText(obj),
                            font=GLp.globalGL.glSmallFont,
                            x=textX,
                            y=textY,
                            colour=(colR, colG, colB, alpha),
                            GLContext=GLp,
                            obj=self.objectInstance(obj),
                            serial=serial)
        newLabel.position = position
        newLabel.axisCodes = axisCodes
        newLabel.lock = lock

        # set up class specific settings, to be subclassed as required
        self.objectSettings(newLabel, obj)

        # shouldn't be necessary but here for completeness
        self._rescaleString(newLabel)

        # assume objects are only used once, will replace a previous object
        self.strings[obj] = newLabel

        # return the new created GLstring
        return newLabel

    def removeString(self, obj):
        """Remove a string from the list, if it exists
        """
        if obj in self.strings:
            del self.strings[obj]

    def _rescaleString(self, obj):
        vertices = obj.numVertices

        if vertices:
            # check the lock type to determine how to rescale

            lock = obj.lock
            GLp = self._GLParent
            position = list(obj.position)

            # move the axes to account for the stacking
            if self._GLParent._stackingMode:
                if obj.spectrumView not in GLp._spectrumSettings:
                    return

                position[1] = GLp._spectrumSettings[obj.spectrumView][GLDefs.SPECTRUM_STACKEDMATRIXOFFSET]

            if lock == GLDefs.LOCKSCREEN:

                # fixed screen co-ordinates
                offsets = [GLp.axisL + position[0] * GLp.pixelX,
                           GLp.axisB + position[1] * GLp.pixelY]

            elif lock == GLDefs.LOCKLEFT:

                # lock to the left margin
                offsets = [GLp.axisL + 3.0 * GLp.pixelX,
                           position[1]]

            elif lock == GLDefs.LOCKRIGHT:

                # lock to the right margin
                offsets = [GLp.axisR - (3.0 + obj.width) * GLp.pixelX,
                           position[1]]

            elif lock == GLDefs.LOCKBOTTOM:

                # lock to the bottom margin - updated in resize
                offsets = [position[0],
                           GLp.axisB + 3.0 * GLp.pixelY]

            elif lock == GLDefs.LOCKTOP:

                # lock to the top margin - updated in resize
                offsets = [position[0],
                           GLp.axisT - (3.0 + obj.height) * GLp.pixelY]

            else:
                return

            for pp in range(0, 2 * vertices, 2):
                obj.attribs[pp:pp + 2] = offsets

            # redefine the mark's VBOs
            obj.updateTextArrayVBOAttribs(enableVBO=True)

    def rescale(self):
        """rescale the objects
        """
        for string in self.strings.values():
            self._rescaleString(string)
