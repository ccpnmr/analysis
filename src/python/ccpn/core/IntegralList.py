"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
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
__dateModified__ = "$dateModified: 2021-06-25 17:35:46 +0100 (Fri, June 25, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import List, Tuple
import numpy as np
from scipy import signal

from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import IntegralList as ApiIntegralList
from ccpn.core.Spectrum import Spectrum
from ccpn.core._implementation.PMIListABC import PMIListABC
from ccpn.core.lib.SpectrumLib import _oldEstimateNoiseLevel1D, estimateNoiseLevel1D, _filterROI1Darray
from ccpn.core.lib.ContextManagers import newObject
from ccpn.util.decorators import logCommand
from ccpn.util.Logging import getLogger


# moved on peakUtil ####################################################################
def _createIntersectingLine(x, y):
    """create a straight line with x values like the original spectrum and y value from the estimated noise level"""
    return [_oldEstimateNoiseLevel1D(x, y)] * len(x)


def _getIntersectionPoints(x, y, line):
    """
    :param line: x points of line to intersect y points
    :return: list of intersecting points
    """
    z = y - line
    dx = x[1:] - x[:-1]
    cross = np.sign(z[:-1] * z[1:])

    x_intersect = x[:-1] - dx / (z[1:] - z[:-1]) * z[:-1]
    negatives = np.where(cross < 0)
    points = x_intersect[negatives]
    return points


def _pairIntersectionPoints(intersectionPoints):
    """ Yield successive pair chunks from list of intersectionPoints """
    for i in range(0, len(intersectionPoints), 2):
        pair = intersectionPoints[i:i + 2]
        if len(pair) == 2:
            yield pair


def _getPeaksLimits(x, y, intersectingLine=None):
    """Get the limits of each peak of the spectrum given an intersecting line. If
     intersectingLine is None, it is calculated by the STD of the spectrum"""
    if intersectingLine is None:
        intersectingLine = _createIntersectingLine(x, y)
    limits = _getIntersectionPoints(x, y, intersectingLine)
    limitsPairs = list(_pairIntersectionPoints(limits))
    return limitsPairs


########################################################################################################################################


class IntegralList(PMIListABC):
    """An object containing Integrals. Note: the object is not a (subtype of a) Python list.
    To access all Integral objects, use integralList.integrals."""

    #: Short class name, for PID.
    shortClassName = 'IL'
    # Attribute it necessary as subclasses must use superclass className
    className = 'IntegralList'

    _parentClass = Spectrum

    #: Name of plural link to instances of class
    _pluralLinkName = 'integralLists'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class - NB shared with PeakList
    _apiClassQualifiedName = ApiIntegralList._metaclass.qualifiedName()

    #=========================================================================================
    # CCPN properties
    #=========================================================================================

    @property
    def _apiIntegralList(self) -> ApiIntegralList:
        """API peakLists matching IntegralList."""
        return self._wrappedData

    def _setPrimaryChildClass(self):
        """Set the primary classType for the child list attached to this container
        """
        from ccpn.core.Integral import Integral as klass

        if not klass in self._childClasses:
            raise TypeError('PrimaryChildClass %s does not exist as child of %s' % (klass.className,
                                                                                    self.className))
        self._primaryChildClass = klass

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: Spectrum) -> Tuple[ApiIntegralList, ...]:
        """get wrappedData (PeakLists) for all IntegralList children of parent Spectrum"""
        return parent._wrappedData.sortedIntegralLists()

    def _finaliseAction(self, action: str):
        """Subclassed to notify changes to associated integralListViews
        """
        if not super()._finaliseAction(action):
            return

        try:
            if action in ['change']:
                for ilv in self.integralListViews:
                    ilv._finaliseAction(action)
        except Exception as es:
            raise RuntimeError('Error _finalising integralListViews: %s' % str(es))

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    def findLimits(self, f=20, stdFactor=0.001):
        spectrum = self.spectrum
        x, y = np.array(spectrum.positions), np.array(spectrum.intensities)

        const = int(len(y) * 0.0039)
        y2 = signal.correlate(y, np.ones(const), mode='same') / const
        yy = y - y2
        # if noiseThreshold is None:
        maxNL, minNL = estimateNoiseLevel1D(yy, f=f, stdFactor=stdFactor)
        intersectingLine = [maxNL] * len(x)
        limitsPairs = _getPeaksLimits(x, yy, intersectingLine)
        return limitsPairs, maxNL, minNL

    def automaticIntegral1D(self, minimalLineWidth=0.01, deltaFactor=1.5, findPeak=False, noiseThreshold=None) -> List['Integral']:
        """
        minimalLineWidth:  an attempt to exclude noise. Below this threshold the area is discarded.
        noiseThreshold: value used to calculate the intersectingLine to get the peak limits
        """
        # TODO: add excludeRegions option. Calculate Negative peak integral.
        # self._project.suspendNotification
        from ccpn.core.lib.PeakPickers.PeakPicker1D import _find1DMaxima
        from ccpn.core.PeakList import estimateNoiseLevel1D

        try:
            spectrum = self.spectrum
            if findPeak:
                peakList = spectrum.newPeakList()
            x, y = np.array(spectrum.positions), np.array(spectrum.intensities)

            const = int(len(y) * 0.0039)
            y2 = signal.correlate(y, np.ones(const), mode='same') / const
            yy = y-y2
            if noiseThreshold is None:
                # maxNL, minNL = estimateNoiseLevel1D(yy, f=20, stdFactor=0.001)
                noiseThreshold, minNL = estimateNoiseLevel1D(yy, f=20, stdFactor=0.001)

            intersectingLine = [noiseThreshold] * len(x)
            # else:
            #     intersectingLine = [noiseThreshold] * len(x)
            limitsPairs = _getPeaksLimits(x, y, intersectingLine)
            spectrum.noiseLevel = noiseThreshold

            integrals = []

            for i in limitsPairs:
                minI, maxI = min(i), max(i)
                # aminI = minI - percentage(0.05, minI) #add a bit on each sides
                # amaxI = maxI + percentage(0.05, minI)
                # print(i, aminI,amaxI)
                lineWidth = abs(maxI - minI)
                if lineWidth:
                    newIntegral = self.newIntegral(value=None, limits=[[minI, maxI], ])
                    newIntegral.baseline = noiseThreshold
                    filteredX = np.where((x <= i[0]) & (x >= i[1]))
                    filteredY = spectrum.intensities[filteredX]
                    filteredX =  filteredX[0].flatten()
                    # filteredY = filteredY[1].compressed()
                    if findPeak:  # pick peaks and link to integral
                        maxValues, minValues = _find1DMaxima(y=filteredY, x=filteredX, negDelta=0, delta=noiseThreshold)
                        if len(maxValues) > 1:  #calculate centre of mass or     #   add to multiplet ??

                            positions = []
                            heights = []
                            numerator = []
                            for position, height in maxValues:
                                positions.append(x[position])
                                heights.append(height)
                            for p, h in zip(positions, heights):
                                numerator.append(p * h)
                                centerOfMass = sum(numerator) / sum(heights)
                                newPeak = peakList.newPeak(ppmPositions=[centerOfMass, ], height=max(heights))
                                newIntegral.peak = newPeak
                                newPeak.volume = newIntegral.value
                                newPeak.lineWidths = (lineWidth,)

                        else:
                            for position, height in maxValues:
                                newPeak = peakList.newPeak(ppmPositions=[float(x[position]), ], height=height)
                                newIntegral.peak = newPeak
                                newPeak.volume = newIntegral.value
                                newPeak.lineWidths = (lineWidth,)

                    if intersectingLine:
                        newIntegral.baseline = intersectingLine[0]

                    integrals.append(newIntegral)

        finally:
            # self._project.resumeNotification()
            pass

        return integrals

    #===========================================================================================
    # new'Object' and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================

    @logCommand(get='self')
    def newIntegral(self, value: List[float] = None, comment: str = None, **kwds):
        """Create a new integral within an IntegralList.

        See the Integral class for details.

        Optional keyword arguments can be passed in; see Integral._newIntegral for details.

        :param value: (min, max) values in ppm for the integral
        :param comment: optional comment string
        :return: a new Integral instance
        """
        from ccpn.core.Integral import _newIntegral  # imported here to avoid circular imports

        return _newIntegral(self, value=value, comment=comment, **kwds)


#=========================================================================================
# Connections to parents:
#=========================================================================================

@newObject(IntegralList)
def _newIntegralList(self: Spectrum, title: str = None, comment: str = None,
                     symbolStyle: str = None, symbolColour: str = None,
                     textColour: str = None,
                     meritColour: str = None, meritEnabled: bool = False, meritThreshold: float = None,
                     lineColour: str = None,
                     ) -> IntegralList:
    """
    Create new IntegralList within Spectrum.

    See the IntegralList class for details.

    :param title:
    :param symbolColour:
    :param textColour:
    :param comment:
    :return: a new IntegralList attached to the spectrum.
    """

    dd = {'name': title, 'details': comment, 'dataType': 'Integral'}
    if symbolStyle:
        dd['symbolStyle'] = symbolStyle
    if symbolColour:
        dd['symbolColour'] = symbolColour
    if textColour:
        dd['textColour'] = textColour

    apiDataSource = self._apiDataSource
    apiIntegralList = apiDataSource.newIntegralList(**dd)
    result = self._project._data2Obj.get(apiIntegralList)
    if result is None:
        raise RuntimeError('Unable to generate new IntegralList item')

    # set non-api attributes
    if meritColour is not None:
        result.meritColour = meritColour
    if meritEnabled is not None:
        result.meritEnabled = meritEnabled
    if meritThreshold is not None:
        result.meritThreshold = meritThreshold
    if lineColour is not None:
        result.lineColour = lineColour

    return result
