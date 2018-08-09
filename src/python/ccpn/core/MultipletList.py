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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:29 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import itertools
import collections
import operator

from ccpn.util import Undo
from ccpn.util import Common as commonUtil
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.SpectrumReference import SpectrumReference
from ccpn.core.Peak import Peak
from ccpn.core.Spectrum import Spectrum
# from ccpn.core.Multiplet import Multiplet
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import MultipletList as ApiMultipletList
from typing import Optional, Tuple


LINECOLOUR = 'lineColour'
DEFAULTLINECOLOUR = '#7a7a7a'
MULTIPLETAVERAGING = 'multipletAveraging'
DEFAULTMULTIPLETAVERAGING = 0


class MultipletList(AbstractWrapperObject):
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

    # CCPN properties
    @property
    def _apiMultipletList(self) -> ApiMultipletList:
        """ API multipletLists matching MultipletList"""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """id string - serial number converted to string"""
        return str(self._wrappedData.serial)

    @property
    def serial(self) -> int:
        """serial number of MultipletList, used in Pid and to identify the MultipletList. """
        return self._wrappedData.serial

    @property
    def _parent(self) -> Optional[Spectrum]:
        """parent containing multipletList."""
        return self._project._data2Obj[self._wrappedData.dataSource]

    spectrum = _parent

    @property
    def title(self) -> str:
        """title of multiplet (not used in PID)."""
        return self._wrappedData.name

    @title.setter
    def title(self, value: str):
        self._wrappedData.name = value

    @property
    def dataType(self) -> str:
        """dataType of multipletList."""
        return self._wrappedData.dataType

    @dataType.setter
    def dataType(self, value: str):
        self._wrappedData.dataType = value

    @property
    def symbolColour(self) -> str:
        """Symbol colour for multipletList annotation display"""
        return self._wrappedData.symbolColour

    @symbolColour.setter
    def symbolColour(self, value: str):
        self._wrappedData.symbolColour = value

    @property
    def textColour(self) -> str:
        """Text colour for multipletList annotation display"""
        return self._wrappedData.textColour

    @textColour.setter
    def textColour(self, value: str):
        self._wrappedData.textColour = value

    def _setLineColour(self, value):
        """set the internal line colour
        """
        tempCcpn = self._ccpnInternalData.copy()
        tempCcpn[LINECOLOUR] = value
        self._ccpnInternalData = tempCcpn

    @property
    def lineColour(self) -> str:
        """Line colour for multipletList annotation display"""
        if self._ccpnInternalData:
            if LINECOLOUR not in self._ccpnInternalData:
                self._setLineColour(DEFAULTLINECOLOUR)
        else:
            self._ccpnInternalData = {LINECOLOUR: DEFAULTLINECOLOUR}

        return self._ccpnInternalData[LINECOLOUR]

    @lineColour.setter
    def lineColour(self, value: str):
        if not self._ccpnInternalData:
            self._ccpnInternalData = {LINECOLOUR: value}
        else:
            self._setLineColour(value)

    def _setMultipletAveraging(self, value):
        """set the internal line colour
        """
        tempCcpn = self._ccpnInternalData.copy()
        tempCcpn[MULTIPLETAVERAGING] = value
        self._ccpnInternalData = tempCcpn

    @property
    def multipletAveraging(self) -> str:
        """Line colour for multipletList annotation display"""
        if self._ccpnInternalData:
            if MULTIPLETAVERAGING not in self._ccpnInternalData:
                self._setMultipletAveraging(DEFAULTMULTIPLETAVERAGING)
        else:
            self._ccpnInternalData = {MULTIPLETAVERAGING: DEFAULTMULTIPLETAVERAGING}

        return self._ccpnInternalData[MULTIPLETAVERAGING]

    @multipletAveraging.setter
    def multipletAveraging(self, value: str):
        if not self._ccpnInternalData:
            self._ccpnInternalData = {MULTIPLETAVERAGING: value}
        else:
            self._setMultipletAveraging(value)

    @property
    def comment(self) -> str:
        """Free-form text comment"""
        return self._wrappedData.details

    @comment.setter
    def comment(self, value: str):
        self._wrappedData.details = value

    # Implementation functions
    @classmethod
    def _getAllWrappedData(cls, parent: Spectrum) -> Tuple[ApiMultipletList, ...]:
        """get wrappedData (MultipletLists) for all MultipletList children of parent MultipletListList"""
        return parent._wrappedData.sortedMultipletLists()


# Connections to parents:
def _newMultipletList(self: Spectrum, title: str = None,
                      symbolColour: str = None, textColour: str = None, lineColour: str = None,
                      multipletAveraging = 0,
                      comment: str = None, multiplets: ['Multiplet'] = None) -> MultipletList:
    """Create new MultipletList within Spectrum"""

    defaults = collections.OrderedDict(
            (('title', None), ('symbolColour', None), ('textColour', None), ('comment', None), ('multiplets', None),
             )
            )

    dd = {'name': title, 'details': comment}
    if symbolColour:
        dd['symbolColour'] = symbolColour
    if textColour:
        dd['textColour'] = textColour
    if multiplets:
        dd['multiplets'] = multiplets

    undo = self._project._undo
    self._startCommandEchoBlock('newMultipletList', values=locals(), defaults=defaults,
                                parName='newMultipletList')
    try:
        apiParent = self._wrappedData
        # if multiplets:
        #   apiMultipletList = apiParent.newMultipletList(multiplets=[mm._wrappedData for mm in multiplets])
        # else:
        #   apiMultipletList = apiParent.newMultipletList()

        apiMultipletList = apiParent.newMultipletList(**dd)

        result = self._project._data2Obj.get(apiMultipletList)

        # set non-api attributes
        result.lineColour = lineColour
        result.multipletAveraging = multipletAveraging

    finally:
        self._endCommandEchoBlock()

    return result


MultipletList._parentClass.newMultipletList = _newMultipletList
del _newMultipletList
