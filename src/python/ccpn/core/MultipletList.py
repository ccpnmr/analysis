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
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.Peak import Peak
from ccpn.core.Spectrum import Spectrum
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import MultipletList as ApiMultipletList
from typing import Tuple, Sequence, Union
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject
from ccpn.util.Logging import getLogger
from ccpn.core._implementation.PMIListABC import PMIListABC


MULTIPLETSETTINGS = 'multipletSettings'
MULTIPLETAVERAGING = 'multipletAveraging'
MULTIPLETAVERAGE = 'Average'
MULTIPLETWEIGHTEDAVERAGE = 'Weighted Average'
MULTIPLETLINECOLOURDEFAULT = '#7f7f7f'
MULTIPLETAVERAGINGTYPES = [MULTIPLETAVERAGE, MULTIPLETWEIGHTEDAVERAGE]


class MultipletList(PMIListABC):
    """MultipletList object, holding position, intensity, and assignment information

    Measurements that require more than one NmrAtom for an individual assignment
    (such as  splittings, J-couplings, MQ dimensions, reduced-dimensionality
    experiments etc.) are not supported (yet). Assignments can be viewed and set
    either as a list of assignments for each dimension (dimensionNmrAtoms) or as a
    list of all possible assignment combinations (assignedNmrAtoms)"""

    #: Short class name, for PID.
    shortClassName = 'ML'
    # Attribute it necessary as subclasses must use superclass className
    className = 'MultipletList'

    _parentClass = Spectrum

    #: Name of plural link to instances of class
    _pluralLinkName = 'multipletLists'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiMultipletList._metaclass.qualifiedName()

    #=========================================================================================
    # CCPN properties
    #=========================================================================================

    @property
    def _apiMultipletList(self) -> ApiMultipletList:
        """ API multipletLists matching MultipletList"""
        return self._wrappedData

    def _setPrimaryChildClass(self):
        """Set the primary classType for the child list attached to this container
        """
        from ccpn.core.Multiplet import Multiplet as klass

        if not klass in self._childClasses:
            raise TypeError('PrimaryChildClass %s does not exist as child of %s' % (klass.className,
                                                                                    self.className))
        self._primaryChildClass = klass

    @property
    def multipletAveraging(self) -> str:
        """Multiplet averaging method
        """
        value = self.getParameter(MULTIPLETSETTINGS, MULTIPLETAVERAGING)
        return MULTIPLETAVERAGINGTYPES[value] if value is not None and \
                                                 0 <= value < len(MULTIPLETAVERAGINGTYPES) else None

    @multipletAveraging.setter
    def multipletAveraging(self, value: str):
        if not isinstance(value, str):
            raise ValueError("multipletAveraging must be a string")
        if value not in MULTIPLETAVERAGINGTYPES:
            raise ValueError("multipletAveraging %s not defined correctly, must be in %s" % (value, MULTIPLETAVERAGINGTYPES))

        self.setParameter(MULTIPLETSETTINGS, MULTIPLETAVERAGING, MULTIPLETAVERAGINGTYPES.index(value))

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: Spectrum) -> Tuple[ApiMultipletList, ...]:
        """get wrappedData (MultipletLists) for all MultipletList children of parent MultipletListList"""
        return parent._wrappedData.sortedMultipletLists()

    def _finaliseAction(self, action: str):
        """Subclassed to notify changes to associated peakListViews
        """
        if not super()._finaliseAction(action):
            return

        try:
            if action in ['change']:
                for mlv in self.multipletListViews:
                    mlv._finaliseAction(action)
        except Exception as es:
            raise RuntimeError('Error _finalising multipletListViews: %s' % str(es))

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    #===========================================================================================
    # new'Object' and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================

    @logCommand(get='self')
    def newMultiplet(self, peaks: ['Peak'] = (), comment: str = None, **kwds):
        """Create a new Multiplet within a multipletList.

        See the Multiplet class for details.

        Optional keyword arguments can be passed in; see Multiplet._newMultiplet for details.

        :param peaks: list of peaks as objects, or pids
        :param comment: optional comment string
        :return: a new Multiplet instance.
        """
        from ccpn.core.Multiplet import _newMultiplet  # imported here to avoid circular imports

        return _newMultiplet(self, comment=comment, peaks=peaks, **kwds)


#=========================================================================================
# Connections to parents:
#=========================================================================================

@newObject(MultipletList)
def _newMultipletList(self: Spectrum, title: str = None, comment: str = None,
                      symbolStyle: str = None, symbolColour: str = None,
                      textColour: str = None,
                      meritColour: str = None, meritEnabled: bool = False, meritThreshold: float = None,
                      lineColour: str = MULTIPLETLINECOLOURDEFAULT, multipletAveraging=MULTIPLETAVERAGE,
                      multiplets: Sequence[Union['Multiplet', str]] = None,
                      ) -> MultipletList:
    """Create new MultipletList within Spectrum.

    See the MultipletList class for details.

    :param title: title string
    :param symbolColour:
    :param textColour:
    :param lineColour:
    :param multipletAveraging:
    :param comment: optional comment string
    :param multiplets: optional list of multiplets as objects or pids
    :return: a new MultipletList attached to the Spectrum.
    """

    dd = {'name': title, 'details': comment}
    if symbolStyle:
        dd['symbolStyle'] = symbolStyle
    if symbolColour:
        dd['symbolColour'] = symbolColour
    if textColour:
        dd['textColour'] = textColour
    if multiplets:
        dd['multiplets'] = multiplets

    apiDataSource = self._apiDataSource
    apiMultipletList = apiDataSource.newMultipletList(**dd)
    result = self._project._data2Obj.get(apiMultipletList)
    if result is None:
        raise RuntimeError('Unable to generate new MultipletList item')

    # set non-api attributes
    if meritColour is not None:
        result.meritColour = meritColour
    if meritEnabled is not None:
        result.meritEnabled = meritEnabled
    if meritThreshold is not None:
        result.meritThreshold = meritThreshold
    if lineColour is not None:
        result.lineColour = lineColour
    if multipletAveraging is not None:
        result.multipletAveraging = multipletAveraging

    return result
