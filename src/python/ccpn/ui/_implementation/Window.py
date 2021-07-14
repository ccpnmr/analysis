"""GUI window class

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
__dateModified__ = "$dateModified: 2021-06-29 09:34:32 +0100 (Tue, June 29, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from functools import partial
from typing import Sequence, Tuple

from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import BoundDisplay as ApiBoundDisplay
from ccpnmodel.ccpncore.api.ccpnmr.gui.Window import Window as ApiWindow

from ccpn.core.Project import Project
from ccpn.core.Spectrum import Spectrum
from ccpn.core.SpectrumGroup import SpectrumGroup
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import Pid
from ccpn.core.lib.SpectrumLib import DIMENSION_FREQUENCY
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, undoBlockWithoutSideBar, undoStackBlocking
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

    #=========================================================================================
    @property
    def spectrumDisplays(self):
        """A tuple of SpectrumDisplay instances displayed in the window"""
        ll = [x for x in self._wrappedData.sortedModules() if isinstance(x, ApiBoundDisplay)]
        return tuple(self._project._data2Obj[x] for x in ll if x in self._project._data2Obj)

    #=========================================================================================
    # CCPN properties
    #=========================================================================================

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
    # CCPN Routines
    #=========================================================================================

    def _getModuleInsertList(self, moduleArea):
        """Generate the list of .moveDock instructions that are required to move all modules back to their
        original positions in the layout
        """
        from collections import OrderedDict

        # initialise lists
        cntrsDict = OrderedDict()
        cntrsDict[moduleArea.topContainer] = None
        nodes = []
        insertsDict = OrderedDict()

        def _setContainerWidget(cntr):
            """Label the containers with the attached display

                   A/\
                   /  \
                  /    \            Tree traversed from left-right, i.e. iterating through widget(ii) of containers
                 /      \           items will always be either to the right, or below previous modules
               A/        \C
               /\        /\         A found first, and propagated up to the containers which
              /  \      /  \            are located at the forks
             /    \E   /    \G      E propagated up, but only one fork not allocated
            A     /\  C     /\      F has nothing
                 /  \      /  \     C propagated up, but only one fork not allocated
                /    \    /    \    G&H nothing to set
               E     F   G     H

            """
            count = cntr.count()
            for ww in range(count):
                widget = cntr.widget(ww)

                if not hasattr(widget, 'type'):
                    # widget is a module, add to list
                    nodes.append(widget)

                    # find the chain of containers to the topContainer/moduleArea that have not been set
                    # and set to the current module
                    parentContainer = cntr
                    while parentContainer is not moduleArea:
                        if parentContainer not in cntrsDict:
                            cntrsDict[parentContainer] = None

                        if cntrsDict[parentContainer] is None:
                            cntrsDict[parentContainer] = widget
                            parentContainer = parentContainer.container()
                        else:
                            break
                else:
                    _setContainerWidget(widget)

        def _insertWidgets(cntr, root=None):
            """Get the ordering for inserting the new containers
            Iterate through the modue structure of containers and modules

            If a container found (a fork shown above) then add to the list
                position will always be to the right, below or 'top' if the first item
                relativeTo will be the node labelled at the fork, or
                    None if the first item - all following items will be referenced to this

            If a module found then and to the list
                position will always be to the right or below
                relativeTo will be the node labelled at the fork.
            """
            count = cntr.count()
            reorderedWidgets = [cntr.widget(0)] + [cntr.widget(ii) for ii in range(count - 1, 0, -1)]

            for ww in range(count):
                widget = reorderedWidgets[ww]

                vv = cntrsDict[widget] if widget in cntrsDict else widget
                if vv not in insertsDict:
                    parent = cntrsDict[cntr]
                    typ = cntr.type()
                    if typ == 'vertical':
                        position = 'bottom'
                    else:
                        position = 'right'  # assume no 'tab' yet
                    insertsDict[vv] = (position, parent)

            # go through the next depth
            for ww in range(count):
                widget = cntr.widget(ww)

                if widget in cntrsDict:
                    _insertWidgets(widget, cntrsDict[widget])

        if moduleArea.topContainer:
            _setContainerWidget(moduleArea.topContainer)
            insertsDict[nodes[0]] = ('top', None)
            _insertWidgets(moduleArea.topContainer, None)
            return insertsDict

        return {}

    def _restoreModules(self, moduleList):
        """Recover modules to their original positions
        """
        # NOTE:ED currently recovers all modules, not just spectrumDisplays
        # needs to handle different moduleAreas
        for mods, (pos, rel) in moduleList.items():
            # may need to have a dock.float() in here somewhere if from a deleted moduleArea
            self.moduleArea.moveDock(mods, pos, rel)
            # recover sizes?

    def _recoverSpectrumToolbar(self, display, specViewList):
        """Re-insert the spectra into the spectrumToolbar
        """
        for specView, selected in specViewList:
            action = display.spectrumToolBar._addSpectrumViewToolButtons(specView)
            if action:
                action.setChecked(selected)

    def _setBlankingSpectrumDisplayNotifiers(self, display, value):
        """Blank all spectrumDisplay and contained strip notifiers
        """
        display.setBlankingAllNotifiers(value)
        for strip in display.strips:
            strip.setBlankingAllNotifiers(value)

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

    # @logCommand('mainWindow.')
    # def newSpectrumDisplay(self, spectrum: Spectrum, axisCodes: (str,) = None, stripDirection: str = 'Y',
    #                        name: str = None, zPlaneNavigationMode: str = None):
    #     """Create new SpectrumDisplay
    #
    #     :param spectrum: a Spectrum instance to be displayed
    #     :param axisCodes: display order of the dimensions of spectrum (defaults to spectrum.preferredAxisOrdering)
    #     :param stripDirection: stripDirection: if 'X' or 'Y' set strip axis
    #     :param name: optional name
    #     :param zPlaneNavigationMode:
    #     :return: a new SpectrumDisplay instance.
    #     """
    #     from ccpn.ui._implementation.SpectrumDisplay import _newSpectrumDisplay
    #     if axisCodes is None:
    #         axisCodes = tuple(spectrum.axisCodes[aa] for aa in spectrum.preferredAxisOrdering)
    #     return _newSpectrumDisplay(window=self, spectrum=spectrum, axisCodes=axisCodes,
    #                                stripDirection=stripDirection, name=name, zPlaneNavigationMode=zPlaneNavigationMode)


    def newSpectrumDisplay(self, spectra, axisCodes: Sequence[str] = (), stripDirection: str = 'Y',
                              position='right', relativeTo=None):
        """Create new SpectrumDisplay

        :param spectra: a Spectrum or SpectrumGroup instance to be displayed
        :param axisCodes: display order of the dimensions of spectrum (defaults to spectrum.preferredAxisOrdering)
        :param stripDirection: stripDirection: if 'X' or 'Y' sets strip axis

        :return: a new SpectrumDisplay instance.
        """

        from ccpn.ui._implementation.SpectrumDisplay import _newSpectrumDisplay
        from ccpn.ui.gui.lib.GuiSpectrumDisplay import STRIPDIRECTIONS
        from ccpn.ui.gui.guiSettings import ZPlaneNavigationModes

        if isinstance(spectra, str):
            spectra = self.project.getByPid(spectra)

        if not isinstance(spectra, (Spectrum, SpectrumGroup)):
            raise ValueError('Invalid spectra argument, expected Spectrum or SpectrumGroup; got "%s"' % spectra)

        if isinstance(spectra, Spectrum):
            isGrouped = False
        elif isinstance(spectra, SpectrumGroup) and len(spectra.spectra) > 0:
            isGrouped = True
        else:
            raise ValueError('%s has no spectra' % spectra)
        spectrum = spectra.spectra[0] if isGrouped else spectra

        if not axisCodes:
            axisCodes = tuple(spectrum.axisCodes[ac] for ac in spectrum.preferredAxisOrdering)

        # change string names to objects
        if isinstance(relativeTo, str):
            modules = [module for module in self.modules if module.pid == relativeTo]
            if len(modules) > 1:
                raise ValueError("Error, not a unique module")
            relativeTo = modules[0] if modules else None

        @logCommand('mainWindow.')
        def newSpectrumDisplay(spectra, axisCodes, stripDirection, position, relativeTo):
            with undoBlockWithoutSideBar():

                try:
                    zPlaneNavigationMode = ZPlaneNavigationModes(0).label

                    # default to preferences if not set
                    _stripDirection = self.project.application.preferences.general.stripArrangement
                    stripDirection = stripDirection or STRIPDIRECTIONS[_stripDirection]
                    _zPlaneNavigationMode = self.project.application.preferences.general.zPlaneNavigationMode
                    zPlaneNavigationMode = ZPlaneNavigationModes(_zPlaneNavigationMode).label
                except Exception as es:
                    getLogger().warning(f'createSpectrumDisplay {es}')

                # create the new spectrumDisplay
                display = _newSpectrumDisplay(self,
                                              spectrum = spectrum,
                                              axisCodes=axisCodes,
                                              stripDirection=stripDirection,
                                              zPlaneNavigationMode=zPlaneNavigationMode,
                                              isGrouped = isGrouped
                                              )

                # add the new module to mainWindow at the required position
                self.moduleArea.addModule(display, position=position, relativeTo=relativeTo)
                display._insertPosition = (position, relativeTo)

                with undoStackBlocking() as addUndoItem:
                    # disable all notifiers in spectrumDisplays
                    addUndoItem(undo=partial(self._setBlankingSpectrumDisplayNotifiers, display, True),
                                redo=partial(self._setBlankingSpectrumDisplayNotifiers, display, False))

                    # add/remove spectrumDisplay from module Area - use moveDock not addModule, otherwise introduces extra splitters
                    addUndoItem(undo=partial(self._hiddenModules.moveDock, display, position='top', neighbor=None),
                                redo=partial(self.moduleArea.moveDock, display, position=position, neighbor=relativeTo))

                # if not positions and not widths:
                #     display.autoRange()

                if isGrouped:
                    display._colourChanged(spectra)
                    display.spectrumToolBar.hide()
                    display.spectrumGroupToolBar.show()
                    display.spectrumGroupToolBar._addAction(spectra)

                return display

        return newSpectrumDisplay(spectra, axisCodes, stripDirection, position, relativeTo)

    # deprecated
    createSpectrumDisplay = newSpectrumDisplay

    @logCommand('mainWindow.')
    def _deleteSpectrumDisplay(self, display):
        """Delete a spectrumDisplay from the moduleArea
        Removes the display to a hidden moduleArea of mainWindow, deletes the _wrappedData, and disables all notifiers
        Object is recovered through the deleteObject decorator
        """
        with undoBlockWithoutSideBar():
            # get the current state of the layout
            _list = self._getModuleInsertList(moduleArea=display.area)

            # get the list of spectra currently displayed in the spectrumDisplay
            specViewList = [(specView, action.isChecked()) for specView in display.spectrumViews
                            for action in display.spectrumToolBar.actions()
                            if action.objectName() == specView.spectrum.pid]

            with undoStackBlocking() as addUndoItem:
                # re-insert spectrumToolbar
                addUndoItem(undo=partial(self._recoverSpectrumToolbar, display, specViewList), )

                # disable all notifiers in spectrumDisplays
                addUndoItem(undo=partial(self._setBlankingSpectrumDisplayNotifiers, display, False),
                            redo=partial(self._setBlankingSpectrumDisplayNotifiers, display, True))

                # add/remove spectrumDisplay from module Area - using moveDock method
                addUndoItem(undo=partial(self._restoreModules, _list),
                            redo=partial(self._hiddenModules.moveDock, display, position='top', neighbor=None), )

            # disable the spectrumDisplay notifiers
            self._setBlankingSpectrumDisplayNotifiers(display, True)

            # move to the hidden module area
            self._hiddenModules.moveDock(display, position='top', neighbor=None)

            # delete the spectrumDisplay
            display.delete()


#=========================================================================================
# Connections to parents:
#=========================================================================================

@newObject(Window)
def _newWindow(self: Project, title: str = None, position: tuple = (), size: tuple = ()) -> Window:
    """Create new child Window.

    See the Window class for details.

    :param str title: window  title (optional, defaults to 'W1', 'W2', 'W3', ...
    :param tuple position: x,y position for new window in integer pixels.
    :param tuple size: x,y size for new window in integer pixels.
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

    return result

#EJB 20181205: moved to Project
# Project.newWindow = _newWindow
# del _newWindow

# Notifiers: None
