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

import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from ccpn.util.Colour import hexToRgbRatio
from ccpn.util.Logging import getLogger

try:
    # used to test whether all the arrays are defined correctly
    # os.environ.update({'PYOPENGL_ERROR_ON_COPY': 'true'})

    from OpenGL import GL, GLU, GLUT
except ImportError:
    app = QtWidgets.QApplication(sys.argv)
    QtWidgets.QMessageBox.critical(None, "OpenGL CCPN",
                                   "PyOpenGL must be installed to run this example.")
    sys.exit(1)

from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLFonts import GLString
import ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs as GLDefs
from ccpn.util.Common import getAxisCodeMatch, getAxisCodeMatchIndices


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
        self.axisCodes = self.strip.axisCodes
        self.current = self.strip.current if self.strip else None

        self.strings = {}

    def buildStrings(self):
        for spectrumView in self._GLParent._ordering:  # strip.spectrumViews:

            if spectrumView.isDeleted:
                continue

            if spectrumView not in self.strings:
                self.addString(spectrumView, (0, 0),
                               colour=spectrumView.spectrum.sliceColour, alpha=1.0,
                               lock=GLDefs.LOCKAXIS | GLDefs.LOCKLEFT | GLDefs.LOCKBOTTOM, axisCodes=('intensity',))

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
        if string.axisCodes:
            string.axisIndices = getAxisCodeMatchIndices(string.axisCodes, self.axisCodes)

    def addString(self, obj, position=(0, 0), axisCodes=None, colour="#FF0000", alpha=1.0,
                  lock=GLDefs.LOCKNONE, serial=0):
        """Add a new string to the list
        """
        GLp = self._GLParent
        col = hexToRgbRatio(colour)

        # NOTE:ED check axis units - assume 'ppm' for the minute

        # fixed ppm position - rescale will do the rest
        textX = position[0]
        textY = position[1]

        # create new label, should be ready to draw
        newLabel = GLString(text=self.objectText(obj),
                            font=GLp.globalGL.glSmallFont,
                            x=textX,
                            y=textY,
                            colour=(*col, alpha),
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

    def renameString(self, obj):
        """Rename a string in the list, if it exists
        """
        strings = [(specView, string) for specView, string in self.strings.items() if string.object is obj]

        for specView, string in strings:
            string.text = self.objectText(specView)
            string.buildString()
            self._rescaleString(string)

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

            if lock == GLDefs.LOCKNONE:

                # lock to the correct axisCodes if exist - not tested yet
                if obj.axisIndices[0] and obj.axisIndices[1]:
                    offsets = [position[obj.axisIndices[0]], position[obj.axisIndices[1]]]

                else:
                    offsets = position

            elif lock == GLDefs.LOCKSCREEN:

                # fixed screen co-ordinates
                offsets = [GLp.axisL + position[0] * GLp.pixelX,
                           GLp.axisB + position[1] * GLp.pixelY]

            # not locking to an axisCode
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

            elif lock & GLDefs.LOCKAXIS:

                # locking to a named axisCodes
                if len(obj.axisIndices) == 1:

                    # match to a single axisCode
                    if obj.axisIndices[0] == 1:

                        if lock & GLDefs.LOCKRIGHT:

                            # lock to the right margin
                            offsets = [GLp.axisR - (3.0 + obj.width) * GLp.pixelX,
                                       position[1]]

                        else:

                            # lock to the left margin
                            offsets = [GLp.axisL + 3.0 * GLp.pixelX,
                                       position[1]]

                    elif obj.axisIndices[0] == 0:

                        if lock & GLDefs.LOCKTOP:

                            # lock to the top margin - updated in resize
                            offsets = [position[0],
                                       GLp.axisT - (3.0 + obj.height) * GLp.pixelY]

                        else:

                            # lock to the bottom margin - updated in resize
                            offsets = [position[0],
                                       GLp.axisB + 3.0 * GLp.pixelY]

                else:
                    # can't match more than 1
                    return

            else:
                return

            for pp in range(0, 2 * vertices, 2):
                obj.attribs[pp:pp + 2] = offsets

            # redefine the string's position VBOs
            obj.updateTextArrayVBOAttribs(enableVBO=True)

            try:
                # reset the colour, may have changed due to spectrum colour change, but not caught anywhere else yet
                obj.setStringHexColour(obj.spectrumView.spectrum.sliceColour, alpha=1.0)

                # redefine the string's colour VBOs
                obj.updateTextArrayVBOColour(enableVBO=True)

            except Exception as es:
                getLogger().warning('error setting string colour')

    def rescale(self):
        """rescale the objects
        """
        for string in self.strings.values():
            self._rescaleString(string)


class GLSimpleLegend(GLSimpleStrings):
    """
    Class to handle drawing the legend to the screen
    """
    def buildStrings(self):
        for spectrumView in self._GLParent._ordering:  # strip.spectrumViews:

            if spectrumView.isDeleted:
                continue

            if spectrumView not in self.strings:
                self.addString(spectrumView, (0, 0),
                               colour=spectrumView.spectrum.sliceColour, alpha=1.0)

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
        return str(obj.id)

    def objectInstance(self, obj):
        """return the object instance to insert into the string
        To be subclassed as required
        """
        return obj

    def objectSettings(self, string, obj):
        """Set up class specific settings for the new string
        To be subclassed as required
        """
        string.spectrum = obj

    def addString(self, obj, position=(0, 0), axisCodes=None, colour="#FF0000", alpha=1.0,
                  lock=GLDefs.LOCKNONE, serial=0):
        """Add a new string to the list
        """
        GLp = self._GLParent
        col = hexToRgbRatio(colour)

        # fixed ppm position - rescale will do the rest
        textX = position[0]
        textY = position[1]

        # create new label, should be ready to draw
        newLabel = GLString(text=self.objectText(obj),
                            font=GLp.globalGL.glSmallFont,
                            x=textX,
                            y=textY,
                            colour=(*col, alpha),
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

    def _rescaleString(self, stringObj):
        vertices = stringObj.numVertices

        if vertices:

            GLp = self._GLParent
            position = list(stringObj.position)

            # fixed screen co-ordinates from top-left
            offsets = [GLp.axisL + position[0] * GLp.pixelX,
                       GLp.axisB + position[1] * GLp.pixelY]

            for pp in range(0, 2 * vertices, 2):
                stringObj.attribs[pp:pp + 2] = offsets

            # redefine the string's position VBOs
            stringObj.updateTextArrayVBOAttribs(enableVBO=True)

            try:
                # reset the colour, may have changed due to spectrum colour change, but not caught anywhere else yet
                stringObj.setStringHexColour(stringObj.object.sliceColour, alpha=1.0)

                # redefine the string's colour VBOs
                stringObj.updateTextArrayVBOColour(enableVBO=True)

            except Exception as es:
                getLogger().warning('error setting legend string colour')

    def rescale(self):
        """rescale the objects
        """
        for string in self.strings.values():
            self._rescaleString(string)
