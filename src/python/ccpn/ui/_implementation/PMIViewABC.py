"""
Module Documentation here
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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2023-06-01 19:39:56 +0100 (Thu, June 01, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2023-04-28 17:16:13 +0100 (Fri, April 28, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

import typing

from ccpn.core.lib import Pid
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib.ContextManagers import ccpNmrV3CoreSetter  #, undoStackBlocking
from ccpn.util.decorators import logCommand

# TODO:ED - should be in a Gui-class
from ccpn.ui.gui.lib.PeakListLib import line_rectangle_intersection


class PMIViewABC(AbstractWrapperObject):
    """Peak/Integral/Multiplet View for 1D or nD core objects
    """

    #: Short class name, for PID.
    shortClassName = 'Undefined'
    # Attribute it necessary as subclasses must use superclass className
    className = 'Undefined'

    _parentClass = 'Undefined'
    _parentClassName = 'Undefined'

    #: Name of plural link to instances of class
    _pluralLinkName = 'Undefined'

    #: List of child classes.
    _childClasses = []

    _isGuiClass = True

    # Qualified name of matching API class
    _apiClassQualifiedName = None

    # TODO:ED - should be in Gui class :|
    _width = 18
    _height = 18
    _text = ''

    #=========================================================================================
    # CCPN properties
    #=========================================================================================

    @property
    def _parent(self):
        """List containing -view."""
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")

    @property
    def _key(self) -> str:
        """id string - """
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")

    @property
    def _localCcpnSortKey(self) -> typing.Tuple:
        """Local sorting key, in context of parent."""
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")

    @property
    def textOffset(self) -> tuple:
        """X,Y text annotation offset in ppm.
        Positive is always towards the top-right irrespective of axis direction.
        """
        return self._wrappedData.textOffset

    @textOffset.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def textOffset(self, value: tuple):
        """Set the visible offset for the text annotation in ppm.
        """
        try:
            # with undoStackBlocking():
            # this is a gui operation and shouldn't need an undo? if no undo, remove core decorator above
            self._wrappedData.textOffset = value

        except Exception as es:
            raise TypeError(f'{self.__class__.__name__}:textOffset must be a tuple of int/floats') from es

    ppmOffset = textOffset

    @property
    def size(self):
        """X,Y text annotation size in pixels.
        """
        return (self._width, self._height)

    @size.setter
    def size(self, value):
        """Set the X,Y text annotation size in pixels.
        """
        self._width, self._height = value

    @property
    def pixelOffset(self) -> tuple:
        """X,Y text annotation offset in pixels.
        """
        if not (pixelSize := self._parent.pixelSize):
            raise TypeError(f'{self.__class__.__name__}:pixelOffset - {self._parent.className} pixelSize is undefined')
        if 0.0 in pixelSize:
            raise ValueError(f'{self.__class__.__name__}:pixelOffset - {self._parent.className} pixelSize contains 0.0')

        return tuple(to / abs(ps) for to, ps in zip(self._wrappedData.textOffset, pixelSize))

    @pixelOffset.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def pixelOffset(self, value: tuple):
        """Set the visible offset for the text annotation in pixels.
        """
        if not (pixelSize := self._parent.pixelSize):
            raise TypeError(f'{self.__class__.__name__}:pixelOffset - {self._parent.classname} pixelSize is undefined')
        if 0.0 in pixelSize:
            raise ValueError(f'{self.__class__.__name__}:pixelOffset - {self._parent.classname} pixelSize contains 0.0')

        try:
            # with undoStackBlocking():
            # this is a gui operation and shouldn't need an undo? if no undo, remove core decorator above
            self._wrappedData.textOffset = tuple(to * abs(ps) for to, ps in zip(value, pixelSize))

        except Exception as es:
            raise TypeError(f'{self.__class__.__name__}:pixelOffset must be a tuple of int/floats') from es

    @property
    def textCentre(self) -> tuple:
        """X,Y text annotation centre in ppm.
        """
        if not (pixelSize := self._parent.pixelSize):
            raise TypeError(f'{self.__class__.__name__}:pixelOffset - {self._parent.classname} pixelSize is undefined')
        if 0.0 in pixelSize:
            raise ValueError(f'{self.__class__.__name__}:pixelOffset - {self._parent.classname} pixelSize contains 0.0')

        offset = self._wrappedData.textOffset
        return (offset[0] + abs(pixelSize[0] * self._width / 2.0), offset[1] + abs(pixelSize[1] * self._height / 2.0))

    ppmCentre = textCentre

    @property
    def pixelCentre(self) -> tuple:
        """X,Y text annotation centre in pixels.
        """
        offset = self.pixelOffset
        return (offset[0] + self._width / 2, offset[1] + self._height / 2)

    def getIntersect(self, ppmPoint):
        """X,Y text annotation co-ordinates to nearest point of bounding box from start-point in ppm.
        """
        if not (pixelSize := self._parent.pixelSize):
            raise TypeError(f'{self.__class__.__name__}:getIntersect - {self._parent.classname} pixelSize is undefined')
        if 0.0 in pixelSize:
            raise ValueError(f'{self.__class__.__name__}:getIntersect - {self._parent.classname} pixelSize contains 0.0')

        bLeft = self._wrappedData.textOffset
        tRight = (bLeft[0] + abs(self._width * pixelSize[0]), bLeft[1] + abs(self._height * pixelSize[1]))

        return line_rectangle_intersection(ppmPoint, self.textCentre, bLeft, tRight)

    getPpmIntersect = getIntersect

    def getPixelIntersect(self, pixelPoint):
        """X,Y text annotation co-ordinates to nearest point of bounding box from start-point in pixels.
        """
        bLeft = self.pixelOffset
        tRight = (bLeft[0] + self._width, bLeft[1] + self._height)

        return line_rectangle_intersection(pixelPoint, self.textCentre, bLeft, tRight)

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: typing.Any) -> list:
        """get wrappedData in serial number order
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError("Code error: function not implemented")

    def _resetIds(self):
        """Reset the ids when renamed.
        Different  from abstractWrapperObject as the _id needs to be hacked to remove
        the strip identifier.
        """
        # reset id
        oldId = self._id
        project = self._project
        parent = self._parent

        # strip the 'strip' identifier from the _id as this can change the peakView pid
        # when strips are deleted, _id was originally associated with the stripPeakListView
        parentId = self._parent._id.split(Pid.IDSEP)
        del parentId[1]
        parentId = Pid.IDSEP.join(parentId)

        className = self.className

        _id = f'{parentId}{Pid.IDSEP}{self._key}'
        sortKey = list(parent._ccpnSortKey[2:] + self._localCcpnSortKey)
        # strip the 'strip' identifier as above
        del sortKey[1]

        self._id = _id
        self._ccpnSortKey = (id(project), list(project._className2Class.keys()).index(className)) + tuple(sortKey)

        # update pid:object mapping dictionary
        dd = project._pid2Obj.get(className)
        if dd is None:
            dd = {}
            project._pid2Obj[className] = dd
            project._pid2Obj[self.shortClassName] = dd
        # assert oldId is not None
        if oldId in dd:
            del dd[oldId]
        dd[_id] = self

    def delete(self):
        """PeakViews cannot be deleted, except as a consequence of deleting other things.
        """
        raise RuntimeError(f"{str(self._pluralLinkName)} cannot be deleted.")

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    # None
