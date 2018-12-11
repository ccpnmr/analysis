"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:28 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================

__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import collections
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.PeakList import PeakList
from ccpn.core.Spectrum import Spectrum
from typing import List, Tuple, Optional
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import IntegralList as ApiIntegralList
import numpy as np
from scipy.integrate import trapz
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, deleteObject, ccpNmrV3CoreSetter, logCommandBlock
from ccpn.util.Logging import getLogger
from ccpn.core.lib.SpectrumLib import _oldEstimateNoiseLevel1D


# moved on peakUtil ####################################################################
def _createIntersectingLine(x, y):
    '''create a straight line with x values like the original spectrum and y value from the estimated noise level'''
    return [_oldEstimateNoiseLevel1D(x, y)] * len(x)


def _getIntersectionPoints(x, y, line):
    '''
    :param line: x points of line to intersect y points
    :return: list of intersecting points
    '''
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
    '''Get the limits of each peak of the spectrum given an intersecting line. If
     intersectingLine is None, it is calculated by the STD of the spectrum'''
    if intersectingLine is None:
        intersectingLine = _createIntersectingLine(x, y)
    limits = _getIntersectionPoints(x, y, intersectingLine)
    limitsPairs = list(_pairIntersectionPoints(limits))
    return limitsPairs


########################################################################################################################################


class IntegralList(AbstractWrapperObject):
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

    # Special error-raising functions for people who think PeakList is a list
    def __iter__(self):
        raise TypeError("IntegralList object is not iterable -"
                        "for a list of integrals use IntegralList.integrals")

    def __getitem__(self, index):
        raise TypeError("IntegralList object does not support indexing -"
                        " for a list of integrals use IntegralList.integrals")

    def __len__(self):
        raise TypeError("IntegralList object has no length - "
                        "for a list of integrals use IntegralList.integrals")

    # CCPN properties
    @property
    def _apiIntegralList(self) -> ApiIntegralList:
        """API peakLists matching IntegralList."""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """id string - serial number converted to string."""
        return str(self._wrappedData.serial)

    @property
    def serial(self) -> int:
        """serial number of IntegralList, used in Pid and to identify the IntegralList."""
        return self._wrappedData.serial

    @property
    def _parent(self) -> Optional[Spectrum]:
        """Spectrum containing IntegralList."""
        return self._project._data2Obj[self._wrappedData.dataSource]

    spectrum = _parent

    @property
    def title(self) -> str:
        """title of IntegralList (not used in PID)."""
        return self._wrappedData.name

    @title.setter
    def title(self, value: str):
        self._wrappedData.name = value

    @property
    def symbolColour(self) -> str:
        """Symbol colour for integral annotation display."""
        return self._wrappedData.symbolColour

    @symbolColour.setter
    def symbolColour(self, value: str):
        self._wrappedData.symbolColour = value

    @property
    def textColour(self) -> str:
        """Text colour for integral annotation display."""
        return self._wrappedData.textColour

    @textColour.setter
    def textColour(self, value: str):
        self._wrappedData.textColour = value

    @property
    def comment(self) -> str:
        """Free-form text comment."""
        return self._wrappedData.details

    @comment.setter
    def comment(self, value: str):
        self._wrappedData.details = value

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: Spectrum) -> Tuple[ApiIntegralList, ...]:
        """get wrappedData (PeakLists) for all IntegralList children of parent Spectrum"""
        return parent._wrappedData.sortedIntegralLists()

    def _finaliseAction(self, action: str):
        """Subclassed to handle associated integralListViews
        """
        super()._finaliseAction(action=action)

        if action in ['change', 'create']:
            for ilv in self.integralListViews:
                ilv._finaliseAction(action=action)

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    def automaticIntegral1D(self, minimalLineWidth=0.01, deltaFactor=1.5, findPeak=False, noiseThreshold=None) -> List['Integral']:
        """
        minimalLineWidth:  an attempt to exclude noise. Below this threshold the area is discarded.
        noiseThreshold: value used to calculate the intersectingLine to get the peak limits
        """
        # TODO: add excludeRegions option. Calculate Negative peak integral.
        # self._project.suspendNotification()
        from ccpn.core.lib.peakUtils import peakdet

        try:
            spectrum = self.spectrum
            peakList = spectrum.newPeakList()
            x, y = np.array(spectrum.positions), np.array(spectrum.intensities)
            if noiseThreshold is None:
                intersectingLine = None
            else:
                intersectingLine = [noiseThreshold] * len(x)
            limitsPairs = _getPeaksLimits(x, y, intersectingLine)

            integrals = []

            for i in limitsPairs:
                lineWidth = abs(i[0] - i[1])
                if lineWidth > minimalLineWidth:
                    newIntegral = self.newIntegral(value=None, limits=[[min(i), max(i)], ])
                    filteredX = np.where((x <= i[0]) & (x >= i[1]))
                    filteredY = spectrum.intensities[filteredX]
                    if findPeak:  # pick peaks and link to integral
                        maxValues, minValues = peakdet(y=filteredY, x=filteredX[0], delta=noiseThreshold / deltaFactor)
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
                        newIntegral._baseline = intersectingLine[0]

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
def _newIntegralList(self: Spectrum, title: str = None, symbolColour: str = None,
                     textColour: str = None, comment: str = None, serial: int = None) -> IntegralList:
    """
    Create new IntegralList within Spectrum.

    See the IntegralList class for details.

    :param title:
    :param symbolColour:
    :param textColour:
    :param comment:
    :param serial: optional serial number.
    :return: a new IntegralList attached to the spectrum.
    """

    dd = {'name': title, 'details': comment, 'dataType': 'Integral'}
    if symbolColour:
        dd['symbolColour'] = symbolColour
    if textColour:
        dd['textColour'] = textColour

    apiDataSource = self._apiDataSource
    apiIntegralList = apiDataSource.newIntegralList(**dd)
    result = self._project._data2Obj.get(apiIntegralList)
    if result is None:
        raise RuntimeError('Unable to generate new IntegralList item')

    if serial is not None:
        try:
            result.resetSerial(serial)
        except ValueError:
            getLogger().warning("Could not reset serial of %s to %s - keeping original value"
                                % (result, serial))

    return result


# IntegralList._parentClass.newIntegralList = _newIntegralList
# del _newIntegralList

# def _factoryFunction(project:Project, wrappedData:ApiIntegralList) -> AbstractWrapperObject:
#   """create PeakList or IntegralList from API PeakList"""
#   if wrappedData.dataType == 'Peak':
#     return PeakList(project, wrappedData)
#   elif wrappedData.dataType == 'Integral':
#     return IntegralList(project, wrappedData)
#   else:
#     raise ValueError("API PeakList object has illegal dataType: %s. Must be 'Peak' or 'Integral"
#                      % wrappedData.dataType)
#
#
# IntegralList._factoryFunction = staticmethod(_factoryFunction)
# PeakList._factoryFunction = staticmethod(_factoryFunction)


# Notifiers:

# NB API level notifiers are (and must be) in PeakList instead
