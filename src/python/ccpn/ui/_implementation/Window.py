"""GUI window class

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
__dateModified__ = "$dateModified: 2017-07-07 16:32:41 +0100 (Fri, July 07, 2017) $"
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
from typing import Sequence, Tuple

from ccpn.core.Project import Project
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import Pid
from ccpnmodel.ccpncore.api.ccpnmr.gui.Window import Window as ApiWindow
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, deleteObject, ccpNmrV3CoreSetter, logCommandBlock
from ccpn.util.Logging import getLogger


class Window(AbstractWrapperObject):
    """UI window, corresponds to OS window"""

    #: Short class name, for PID.
    shortClassName = 'GW'
    # Attribute it necessary as subclasses must use superclass className
    className = 'Window'

    _parentClass = Project

    #: Name of plural link to instances of class
    _pluralLinkName = 'windows'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiWindow._metaclass.qualifiedName()

    # CCPN properties
    @property
    def _apiWindow(self) -> ApiWindow:
        """ CCPN Window matching Window"""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """short form of name, corrected to use for id"""
        return self._wrappedData.title.translate(Pid.remapSeparators)

    @property
    def _localCcpnSortKey(self) -> Tuple:
        """Local sorting key, in context of parent."""
        return (self._wrappedData.title,)

    @property
    def title(self) -> str:
        """Window display title (not used in PID)."""
        return self._wrappedData.title

    @property
    def _parent(self) -> Project:
        """Parent (containing) object."""
        return self._project

    @property
    def position(self) -> tuple:
        """Window X,Y position in integer pixels"""
        return self._wrappedData.position

    @position.setter
    def position(self, value: Sequence):
        self._wrappedData.position = value

    @property
    def size(self) -> tuple:
        """Window X,Y size in integer pixels"""
        return self._wrappedData.size

    @size.setter
    def size(self, value: Sequence):
        self._wrappedData.size = value

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: Project) -> list:
        """get wrappedData (ccp.gui.windows) for all Window children of parent NmrProject.windowStore"""
        windowStore = parent._wrappedData.windowStore

        if windowStore is None:
            return []
        else:
            return windowStore.sortedWindows()


#=========================================================================================
# Connections to parents:
#=========================================================================================

def _newWindow(self: Project, title: str = None, position: tuple = (), size: tuple = ()) -> Window:
    """Create new child Window

    :param str title: window  title (optional, defaults to 'W1', 'W2', 'W3', ...
    :param tuple size: x,y size for new window in integer pixels
    :param tuple position: x,y position for new window in integer pixels"""

    if title and Pid.altCharacter in title:
        raise ValueError("Character %s not allowed in gui.core.Window.title" % Pid.altCharacter)

    apiWindowStore = self._project._wrappedData.windowStore

    defaults = collections.OrderedDict((('title', None), ('position', ()), ('size', ())))

    self._startCommandEchoBlock('newWindow', values=locals(), defaults=defaults,
                                parName='newWindow')
    try:
        apiGuiTask = (apiWindowStore.root.findFirstGuiTask(nameSpace='user', name='View')
                      or apiWindowStore.root.newGuiTask(nameSpace='user', name='View'))
        newApiWindow = apiWindowStore.newWindow(title=title, guiTask=apiGuiTask)
        if position:
            newApiWindow.position = position
        if size:
            newApiWindow.size = size
    finally:
        self._endCommandEchoBlock()

    result = self._data2Obj.get(newApiWindow)

    return result


Project.newWindow = _newWindow
del _newWindow

# Notifiers: None
