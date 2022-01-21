"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-01-21 11:22:12 +0000 (Fri, January 21, 2022) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import sys
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox, ScientificDoubleSpinBox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.util.floatUtils import fRound


# default steps sizes of the DoubleSpinBox, ..
# used in ZoomPopup
spinBoxStepsByAxisCode = {'H'        : 0.05,
                          'C'        : 0.5,
                          'N'        : 0.5,
                          'intensity': 1e4, }


class ZoomPopup(CcpnDialog):
    """
    Set Zoom for for current.strip; works for 1D and nD
    """

    def __init__(self, parent=None, mainWindow=None, **kwds):
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle='Set Zoom', **kwds)

        self.mainWindow = mainWindow
        self.project = self.mainWindow.project
        self.application = self.mainWindow.application
        self.current = self.application.current

        if self.current.strip:

            self.minPositionBoxes = []
            self.maxPositionBoxes = []

            if self.current.strip.spectrumDisplay.is1D:
                axisCode2dimension = dict([aCode, i] for i, aCode in enumerate(self.current.strip.axisCodes))
            else:
                # For nD, we need to look at the spectra as the axes could be flipped from the actual order in the spectra
                # axisCode2dimension = dict([aCode, i] for i, aCode in enumerate(self.current.strip.spectra[0].axisCodes))
                axisCode2dimension = dict([aCode, i] for i, aCode in enumerate(self.current.strip.axisCodes))

            steps = spinBoxStepsByAxisCode

            for ii, axisCode in enumerate(self.current.strip.axisCodes):
                dim = axisCode2dimension[axisCode]
                if axisCode == 'intensity':
                    # 1D, set min,max to largest number
                    maxVal = sys.float_info.max
                    minVal = -maxVal
                    region = list(self.current.strip.axes[ii].region)
                    # assume we want 50 steps to cover the current region
                    step = (region[1] - region[0]) / 50.0
                    # round to some sensible number
                    step = fRound(step)
                    suffix = None
                else:
                    # PPM axis
                    suffix = self.current.strip.axes[ii].unit
                    step = steps.setdefault(axisCode[0:1], 0.5)
                    # assure that we can zoom to the largest range of all displayed spectra (plus a bit extra)
                    minVal = min([(s.aliasingLimits[dim][0] - s.spectralWidths[dim] / 2) for s in self.current.strip.spectra])
                    minVal = _round(minVal, step, -0.5)
                    maxVal = max([(s.aliasingLimits[dim][1] + s.spectralWidths[dim] / 2) for s in self.current.strip.spectra])
                    maxVal = _round(maxVal, step, 1.5)

                region = list(self.current.strip.axes[ii].region)
                # get some rounded values for the regions
                #print('>>> region, step, minVal, maxVal:', region, step, minVal, maxVal)
                for ax in range(2):
                    region[ax] = _round(region[ax], step, 0.5)  # float(int(region[ax]/step+0.5)*step)

                dim1MinLabel = Label(self, text='%s-min' % axisCode, grid=(2 + ii, 0), vAlign='t')
                dim1MinDoubleSpinBox = DoubleSpinbox(self, step=step,
                                                     min=minVal, max=maxVal, value=region[0],
                                                     decimals=3, grid=(2 + ii, 1), vAlign='t')

                dim1MaxLabel = Label(self, text='%s-max' % axisCode, grid=(2 + ii, 2), vAlign='t')
                dim1MaxDoubleSpinBox = DoubleSpinbox(self, step=step,
                                                     min=minVal, max=maxVal, value=region[1],
                                                     decimals=3, grid=(2 + ii, 3))

                self.minPositionBoxes.append(dim1MinDoubleSpinBox)
                self.maxPositionBoxes.append(dim1MaxDoubleSpinBox)

            self.buttonBox = ButtonList(self, grid=(5, 0), gridSpan=(1, 4), texts=['Zoom', 'Done'],
                                        callbacks=[self._zoom, self.reject])
        else:
            self.close()

    def _zoom(self):
        from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar

        with undoBlockWithoutSideBar():

            positions = [(minVal.value(), maxVal.value()) for minVal, maxVal in zip(self.minPositionBoxes, self.maxPositionBoxes)]
            self.current.strip.zoom(positions[0], positions[1])

        self.accept()


def _round(value, step, offset=0.5):
    """Round value in multiples of step as int(n+offset)*step"""
    return float(int(value / step + offset) * step)
