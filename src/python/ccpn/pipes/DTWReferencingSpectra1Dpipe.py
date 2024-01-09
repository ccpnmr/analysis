#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Joanna Fox, Morgan Hayward, Victoria A Higman, Luca Mureddu",
               "Eliza Płoskoń, Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2024-01-09 14:19:15 +0000 (Tue, January 09, 2024) $"
__version__ = "$Revision: 3.2.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


#### GUI IMPORTS
from ccpn.ui.gui.widgets.PipelineWidgets import GuiPipe
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.AnalysisScreen.gui.widgets import HitFinderWidgets as hw
from ccpn.ui.gui.widgets.DoubleSpinbox import ScientificDoubleSpinBox

#### NON GUI IMPORTS
from ccpn.framework.lib.pipeline.PipeBase import SpectraPipe, PIPE_SCREEN
from ccpn.util.Logging import getLogger
from ccpn.core.lib.PeakPickers.PeakSnapping1D import _1DregionsFromLimits
from ccpn.core.lib.PeakPickers.PeakPicker1D import _find1DPositiveMaxima, _getPositionsHeights
from scipy import signal


########################################################################################################################
###   Attributes:
###   Used in setting the dictionary keys on _kwargs either in GuiPipe and Pipe
########################################################################################################################

PipeName = 'Referencing Spectra'
Shift = 'Shift'
Origin = 'Origin'
Target = 'Target'

DefaultToleranceFoM = 0.5


########################################################################################################################
##########################################      ALGORITHM       ########################################################
########################################################################################################################


def dtw(x, y):
    cost_matrix = np.zeros((len(x), len(y)))

    for i in range(len(x)):
        for j in range(len(y)):
            cost_matrix[i, j] = (x[i] - y[j]) ** 2

    accumulated_cost = np.zeros_like(cost_matrix)
    accumulated_cost[0, 0] = cost_matrix[0, 0]

    for i in range(1, len(x)):
        accumulated_cost[i, 0] = cost_matrix[i, 0] + accumulated_cost[i - 1, 0]

    for j in range(1, len(y)):
        accumulated_cost[0, j] = cost_matrix[0, j] + accumulated_cost[0, j - 1]

    for i in range(1, len(x)):
        for j in range(1, len(y)):
            accumulated_cost[i, j] = cost_matrix[i, j] + min(
                accumulated_cost[i - 1, j],        # insertion
                accumulated_cost[i, j - 1],        # deletion
                accumulated_cost[i - 1, j - 1]     # match
            )

    i, j = len(x) - 1, len(y) - 1
    path = [(i, j)]

    while i > 0 or j > 0:
        if i == 0:
            cell = (0, j - 1)
        elif j == 0:
            cell = (i - 1, 0)
        else:
            neighbors = [(i - 1, j), (i, j - 1), (i - 1, j - 1)]
            costs = [accumulated_cost[n] for n in neighbors]
            cell = neighbors[np.argmin(costs)]

        path.insert(0, cell)
        i, j = cell

    return path



import numpy as np
from scipy.spatial.distance import cdist
ToleranceFoM = 'Use Existing Peaks with FoM above'
ORIGINSPECTRUMGROUP = 'Origin_SpectrumGroup'
DestinationSpectrumGroups = 'Destination_SpectrumGroups'
ReferenceSpectrumGroup = 'Reference_SpectrumGroup'
ControlSpectrumGroup = 'Control_SpectrumGroup'
DisplacerSpectrumGroup = 'Displacer_SpectrumGroup'
TargetSpectrumGroup = 'Target_SpectrumGroup'
SGVarNames = [ReferenceSpectrumGroup, ControlSpectrumGroup, TargetSpectrumGroup, DisplacerSpectrumGroup]



########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################


class ReferencingSpectraGuiPipe(GuiPipe):
    preferredPipe = True
    pipeName = PipeName

    def __init__(self, name=pipeName, parent=None, project=None, **kwds):
        super(ReferencingSpectraGuiPipe, self)
        GuiPipe.__init__(self, parent=parent, name=name, project=project, **kwds)
        self._parent = parent

        row = 0
        hw._addSGpulldowns(self, row, SGVarNames)
        row += len(SGVarNames)

        row += 1
        self.tolleranceFoMLabel = Label(self.pipeFrame, text=ToleranceFoM, grid=(row, 0))
        setattr(self, ToleranceFoM, ScientificDoubleSpinBox(self.pipeFrame, value=DefaultToleranceFoM, min=0,
                                                            step=0.1, decimals=2, grid=(row, 1)))

        self._updateWidgets()

    def _updateWidgets(self):
        self._setSpectrumGroupPullDowns(SGVarNames, headerEnabled=True)

########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################


class DTWReferencingSpectra(SpectraPipe):
    """
    Add a shift value to all the spectra in the pipeline
    """

    guiPipe = ReferencingSpectraGuiPipe
    pipeName = PipeName
    pipeCategory = PIPE_SCREEN

    _kwargs = {
        ReferenceSpectrumGroup: 'ReferenceSpectrumGroup.pid',
        ControlSpectrumGroup  : 'ControlSpectrumGroup.pid',  # this will be replaced by the SG pid in the gui
        TargetSpectrumGroup   : 'TargetSpectrumGroup.pid',
        DisplacerSpectrumGroup: 'DisplacerSpectrumGroup.pid',
        ToleranceFoM:               DefaultToleranceFoM,
        }

    def runPipe(self, spectra):
        '''
        :param spectra: inputData
        :return: aligned spectra
        '''

        self.pipeline._set1DRawDataDict()  # we need to refresh the rawData as we shift the values
        referenceSpectrumGroup = self._getSpectrumGroup(self._kwargs[ReferenceSpectrumGroup])
        controlSpectrumGroup = self._getSpectrumGroup(self._kwargs[ControlSpectrumGroup])
        targetSpectrumGroup = self._getSpectrumGroup(self._kwargs[TargetSpectrumGroup])
        displacerSpectrumGroup = self._getSpectrumGroup(self._kwargs[DisplacerSpectrumGroup])
        groups = [controlSpectrumGroup, targetSpectrumGroup, displacerSpectrumGroup]
        toleranceFoM = self._kwargs[ToleranceFoM]
        defaultPeakListIndice = -1
        _spectra = []
        destinationSpectrumGroups = []
        for sg in groups:
            if sg is not None:
                destinationSpectrumGroups.append(sg)
                _spectra.extend(sg.spectra)
        rawDataDict = self.pipeline._rawDataDict

        for destinationSpectrumGroup in destinationSpectrumGroups:
            for originSpectrum, destinationSpectrum in zip(referenceSpectrumGroup.spectra, destinationSpectrumGroup.spectra):
                if originSpectrum not in rawDataDict:
                    xOrigin, yOrigin = np.array(originSpectrum.positions), np.array(originSpectrum.intensities)
                else:
                    xOrigin, yOrigin = rawDataDict.get(originSpectrum)

                if destinationSpectrum not in rawDataDict:
                    xDestination, yDestination = np.array(destinationSpectrum.positions), np.array(destinationSpectrum.intensities)
                else:
                    xDestination, yDestination = rawDataDict.get(destinationSpectrum)

                # use the peaks with fig Of Mer > threshold to filter the array, so to reduce the searching window.
                originPeakList = originSpectrum.peakLists[defaultPeakListIndice]
                if len(originPeakList.peaks)>1:
                    peaksPoints = [pk.pointPositions[0] for pk in originPeakList.peaks if pk.figureOfMerit >= toleranceFoM]
                    minPeak = np.min(peaksPoints)
                    maxPeak = np.max(peaksPoints)
                    leftLimit = minPeak - 100 # arbitrary pnts
                    rightLimit = maxPeak + 100 # arbitrary pnts
                    leftPpm = originSpectrum.point2ppm(leftLimit, originSpectrum.axisCodes[0])
                    rightPpm = originSpectrum.point2ppm(rightLimit, originSpectrum.axisCodes[0])
                    x1f, y1f = _1DregionsFromLimits(xOrigin, yOrigin, limits=[leftPpm, rightPpm])
                    x2f, y2f = _1DregionsFromLimits(xDestination, yDestination, limits=[leftLimit, rightPpm])

                else:
                    # use the whole spectrum
                    x1f, y1f = xOrigin, yOrigin
                    x2f, y2f = xDestination, yDestination

                mh1 = float(np.median(y1f) + 3 * np.std(y1f)) #quick picking at high threshold.
                mh2 = float(np.median(y2f) + 3 * np.std(y2f))
                positions1, heights1 = _getPositionsHeights(x1f, y1f, mh1)
                positions2, heights2 = _getPositionsHeights(x2f, y2f, mh2)
                path = dtw(positions1, positions2)
                deltas = np.array([positions2[j] - positions1[i] for i, j in path])
                delta_shift = np.median(deltas)

                simple_shift = (np.argmax(signal.correlate(heights1, heights2)) - (len(heights2) - 1)) * np.mean(np.diff(positions1))
                print(f'Before > {destinationSpectrum.referenceValues} - Applying the {simple_shift} INSTEAD OF {delta_shift} -> ')
                b = destinationSpectrum.referenceValues
                destinationSpectrum.referenceValues = [destinationSpectrum.referenceValues[0] + simple_shift]
                diff = destinationSpectrum.referenceValues[0] - b[0]
                print(f'AFTER > {destinationSpectrum.referenceValues}  -- DIFF: {diff}')

        return spectra

DTWReferencingSpectra.register()  # Registers the pipe in the pipeline
