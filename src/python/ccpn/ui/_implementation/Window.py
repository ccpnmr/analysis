"""GUI window class

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
__dateModified__ = "$dateModified: 2017-07-07 16:32:41 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Sequence, Tuple
from ccpn.core.Project import Project
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import Pid
from ccpnmodel.ccpncore.api.ccpnmr.gui.Window import Window as ApiWindow
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject
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

    _isGuiClass = True

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

    @logCommand('mainWindow.')
    def createSpectrumDisplay(self, spectrum, displayAxisCodes: Sequence[str] = (),
                              axisOrder: Sequence[str] = (), title: str = None, positions: Sequence[float] = (),
                              widths: Sequence[float] = (), units: Sequence[str] = (),
                              stripDirection: str = 'Y', is1D: bool = False, **kwds):
        """
        :param \*str, displayAxisCodes: display axis codes to use in display order - default to spectrum axisCodes in heuristic order
        :param \*str axisOrder: spectrum axis codes in display order - default to spectrum axisCodes in heuristic order
        :param \*float positions: axis positions in order - default to heuristic
        :param \*float widths: axis widths in order - default to heuristic
        :param \*str units: axis units in display order - default to heuristic
        :param str stripDirection: if 'X' or 'Y' set strip axis
        :param bool is1D: If True, or spectrum passed in is 1D, do 1D display
        :param bool independentStrips: if True do freeStrip display.
        """
        from ccpn.ui._implementation.SpectrumDisplay import _createSpectrumDisplay

        # axisOrder = spectrum.getDefaultOrdering(axisOrder)
        # if not axisOrder:
        #     axisOption = self.application.preferences.general.axisOrderingOptions
        #
        #     preferredAxisOrder = spectrum.preferredAxisOrdering
        #     if preferredAxisOrder is not None:
        #
        #         specAxisOrder = spectrum.axisCodes
        #         axisOrder = [specAxisOrder[ii] for ii in preferredAxisOrder]
        #
        #     else:
        #
        #         # sets an Nd default to HCN (or possibly 2d to HC)
        #         specAxisOrder = spectrum.axisCodes
        #         pOrder = spectrum.searchAxisCodePermutations(('H', 'C', 'N'))
        #         if pOrder:
        #             spectrum.preferredAxisOrdering = pOrder
        #             axisOrder = [specAxisOrder[ii] for ii in pOrder]
        #             getLogger().debug('setting default axisOrdering: ', str(axisOrder))
        #
        #         else:
        #
        #             # just set to the normal ordering
        #             spectrum.preferredAxisOrdering = tuple(ii for ii in range(spectrum.dimensionCount))
        #             axisOrder = None
        #
        #             # # try permutations of repeated codes
        #             # duplicates = [('H', 'H'), ('C', 'C'), ('N', 'N')]
        #             # for dCode in duplicates:
        #             #     pOrder = spectrum.searchAxisCodePermutations(dCode)
        #             #     if pOrder:
        #             #         spectrum.preferredAxisOrdering = pOrder
        #             #         axisOrder = [specAxisOrder[ii] for ii in pOrder]
        #             #         getLogger().debug('setting duplicate axisOrdering: ', str(axisOrder))
        #             #         break

        display = _createSpectrumDisplay(self, spectrum, displayAxisCodes=displayAxisCodes, axisOrder=axisOrder,
                                         title=title, positions=positions, widths=widths, units=units,
                                         stripDirection=stripDirection, is1D=is1D, **kwds)
        if not positions and not widths:
            display.autoRange()
        return display


#=========================================================================================
# Connections to parents:
#=========================================================================================

@newObject(Window)
def _newWindow(self: Project, title: str = None, position: tuple = (), size: tuple = (), serial: int = None) -> Window:
    """Create new child Window.

    See the Window class for details.

    :param str title: window  title (optional, defaults to 'W1', 'W2', 'W3', ...
    :param tuple position: x,y position for new window in integer pixels.
    :param tuple size: x,y size for new window in integer pixels.
    :param serial: optional serial number.
    :return: a new Window instance.
    """

    if title and Pid.altCharacter in title:
        raise ValueError("Character %s not allowed in gui.core.Window.title" % Pid.altCharacter)

    apiWindowStore = self._project._wrappedData.windowStore

    apiGuiTask = (apiWindowStore.root.findFirstGuiTask(nameSpace='user', name='View')
                  or apiWindowStore.root.newGuiTask(nameSpace='user', name='View'))
    newApiWindow = apiWindowStore.newWindow(title=title, guiTask=apiGuiTask)
    if position:
        newApiWindow.position = position
    if size:
        newApiWindow.size = size

    result = self._data2Obj.get(newApiWindow)
    if result is None:
        raise RuntimeError('Unable to generate new Window item')

    if serial is not None:
        try:
            result.resetSerial(serial)
        except ValueError:
            getLogger().warning("Could not reset serial of %s to %s - keeping original value"
                                % (result, serial))

    return result

#EJB 20181205: moved to Project
# Project.newWindow = _newWindow
# del _newWindow

# Notifiers: None
