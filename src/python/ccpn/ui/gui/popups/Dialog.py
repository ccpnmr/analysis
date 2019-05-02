"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:47 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-07-04 15:21:16 +0000 (Tue, July 04, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets
from ccpn.ui.gui.widgets.Base import Base
from ccpn.util.Logging import getLogger
from contextlib import contextmanager


def _updateGl(self, spectrumList):
    from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

    # # spawn a redraw of the contours
    # for spec in spectrumList:
    #     for specViews in spec.spectrumViews:
    #         specViews.buildContours = True

    GLSignals = GLNotifier(parent=self)
    GLSignals.emitPaintEvent()


class CcpnDialog(QtWidgets.QDialog, Base):
    def __init__(self, parent=None, windowTitle='', setLayout=False, size=(300, 100), **kwds):

        super().__init__(parent)
        Base._init(self, setLayout=setLayout, **kwds)

        self.setWindowTitle(windowTitle)
        self.setContentsMargins(15, 15, 15, 15)
        self.resize(*size)

    def fixedSize(self):
        self.sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.sizePolicy.setHorizontalStretch(0)
        self.sizePolicy.setVerticalStretch(0)
        self.setSizePolicy(self.sizePolicy)
        self.setFixedSize(self.maximumWidth(), self.maximumHeight())
        self.setSizeGripEnabled(False)

def dialogErrorReport(self, undo, es):
    """Show warning popup and check the undo stack for items that need to be culled
    """
    from ccpn.ui.gui.widgets.MessageDialog import showWarning

    showWarning(str(self.windowTitle()), str(es))

    # should only undo if something new has been added to the undo deque
    # may cause a problem as some things may be set with the same values
    # and still be added to the change list, so only undo if length has changed

    # get the name of the class propagating the error
    errorName = str(self.__class__.__name__)

    if undo.newItemsAdded:
        # undo any valid items and clear the stack above the current undo point
        undo.undo()
        undo.clearRedoItems()

        getLogger().debug('>>>Undo.%s._applychanges' % errorName)
    else:
        getLogger().debug('>>>Undo.%s._applychanges nothing to remove' % errorName)


@contextmanager
def handleDialogApply(self):
    """Context manager to wrap the apply button for dialogs
    Error trapping is contained inside the undoBlock, any error raised is placed in
    the errorValue of the yielded object and a warning popup is raised

    e.g.

        with handleDialogApply(self) as error:
            ...  code block here ...

        if error.errorValue:
            # an error occurred in the code block
    """

    from ccpn.core.lib.ContextManagers import undoBlock
    undo = self.project._undo

    # object to hold the error value
    class errorContent():
        def __init__(self):
            self.errorValue = None

    try:
        with undoBlock():

            # transfer control to the calling function
            error = errorContent()
            yield error

    except Exception as es:

        # if an error occurs, report as a warning popup and return error to the calling method
        dialogErrorReport(self, undo, es)
        error.errorValue = es

        # re-raise the error if in debug mode
        if self.application._isInDebugMode:
            raise es

