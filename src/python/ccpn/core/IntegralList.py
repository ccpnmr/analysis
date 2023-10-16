"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2023-10-16 14:45:44 +0100 (Mon, October 16, 2023) $"
__version__ = "$Revision: 3.2.0 $"
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
from ccpn.core.lib.ContextManagers import newObject
from ccpn.util.decorators import logCommand
from ccpn.util.Logging import getLogger


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

    # Qualified name of matching API class
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


    #===========================================================================================
    # new<Object> and other methods
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
                     lineColour: str = None, arrowColour: str = None,
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
    if arrowColour is not None:
        result.arrowColour = arrowColour

    return result
