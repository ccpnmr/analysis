"""GUI SpectrumDisplay class

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
__dateModified__ = "$dateModified: 2021-07-20 21:57:02 +0100 (Tue, July 20, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from numpy import ndarray
from typing import Sequence, Tuple, Optional

from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import ResonanceGroup as ApiResonanceGroup
from ccpnmodel.ccpncore.api.ccpnmr.gui.Window import Window as ApiWindow
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import BoundDisplay as ApiBoundDisplay

from ccpn.core.NmrResidue import NmrResidue
from ccpn.core.Project import Project
from ccpn.core.Spectrum import Spectrum
import ccpn.core.lib.SpectrumLib as specLib
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import Pid
from ccpn.core.lib.OrderedSpectrumViews import OrderedSpectrumViews
from ccpn.core.lib.AxisCodeLib import doAxisCodesMatch, _axisCodeMapIndices
from ccpn.ui._implementation.Window import Window
from ccpn.util import Common as commonUtil
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, undoStackBlocking, undoBlockWithoutSideBar, deleteObject, renameObject
from ccpn.util.Logging import getLogger


class SpectrumDisplay(AbstractWrapperObject):
    """Spectrum display for 1D or nD spectrum"""

    #: Short class name, for PID.
    shortClassName = 'GD'
    # Attribute it necessary as subclasses must use superclass className
    className = 'SpectrumDisplay'

    _parentClass = Project

    #: Name of plural link to instances of class
    _pluralLinkName = 'spectrumDisplays'
    #: List of child classes.
    _childClasses = []

    _isGuiClass = True

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiBoundDisplay._metaclass.qualifiedName()

    # store the list of ordered spectrumViews
    _orderedSpectrumViews = None

    #-----------------------------------------------------------------------------------------
    # Attributes of the data structure (incomplete?)
    #-----------------------------------------------------------------------------------------

    @property
    def strips(self) -> list:
        """STUB: hot-fixed later"""
        return []

    #-----------------------------------------------------------------------------------------

    def __init__(self, project: Project, wrappedData):

        AbstractWrapperObject.__init__(self, project, wrappedData)
        # isotopeCodes in display order; set on initialisation with the first spectrum
        self._isotopeCodes = None

    @classmethod
    def _restoreObject(cls, project, apiObj):
        """Subclassed to allow for initialisations on restore
        """
        display = super()._restoreObject(project, apiObj)
        display._isotopeCodes = tuple(display.spectrumViews[0]._getByDisplayOrder('isotopeCodes'))
        return display


    #-----------------------------------------------------------------------------------------
    # CCPN properties
    #-----------------------------------------------------------------------------------------

    @property
    def _apiSpectrumDisplay(self) -> ApiBoundDisplay:
        """ CCPN SpectrumDisplay matching SpectrumDisplay"""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """short form of name, corrected to use for id"""
        return self._wrappedData.name.translate(Pid.remapSeparators)

    @property
    def title(self) -> str:
        """SpectrumDisplay title

        (corresponds to its name, but the name 'name' is taken by PyQt"""
        return self._wrappedData.name

    @property
    def _parent(self) -> Project:
        """Project containing spectrumDisplay."""
        return self._project

    project = _parent

    # @property
    # def stripDirection(self) -> str:
    #     """Strip axis direction ('X', 'Y', None) - None only for non-strip plots"""
    #     getLogger().warning('StripDirection is deprecated. Used stripArrangement instead')
    #     return self.stripArrangement
    #
    #     # return self._wrappedData.stripDirection
    #
    # @stripDirection.setter
    # def stripDirection(self, value:str='Y'):
    #     """Set the new strip direction ('X', 'Y', None) - None only for non-strip plots
    #     """
    #     self.stripArrangement(value)
    #     getLogger().warning('StripDirection is deprecated. Used stripArrangement instead')
    #     # raise RuntimeError('deprecated: use stripArrangement') no need of raising an error!
    #
    #     # if not isinstance(value, str):
    #     #     raise TypeError('stripDirection must be a string')
    #     # elif value not in ['X', 'Y']:
    #     #     raise ValueError("stripDirection must be either 'X' or 'Y'")
    #     #
    #     # # override 'frozen' set
    #     # self._wrappedData.__dict__['stripDirection'] = value

    @property
    def stripCount(self) -> int:
        """Number of strips"""
        return self._wrappedData.stripCount

    @property
    def axisCodes(self) -> Tuple[str, ...]:
        """Fixed string Axis codes in display order (X, Y, Z1, Z2, ...)"""
        return tuple(self._wrappedData.axisCodes)

    @property
    def axisOrder(self) -> Tuple[str, ...]:
        """String Axis codes in display order (X, Y, Z1, Z2, ...), determine axis display order"""
        return tuple(self._wrappedData.axisOrder)

    @axisOrder.setter
    def axisOrder(self, value: Sequence):
        self._wrappedData.axisOrder = value

    @property
    def isotopeCodes(self) -> Tuple[str, ...]:
        """Fixed string isotope codes in display order (X, Y, Z1, Z2, ...)"""
        return self._isotopeCodes

    @property
    def dimensionCount(self) -> int:
        """Dimensionality of the SpectrumDisplay"""
        return len(self.axisCodes)

    @property
    def is1D(self) -> bool:
        """True if this is a 1D display."""
        tt = self.axisCodes
        return bool(tt and tt[1] == 'intensity')

    # @property
    # def window(self) -> Window:
    #     """Gui window showing SpectrumDisplay"""
    #     # This should be renamed, but that also requires refactoring
    #     # possibly with a model change that modifies the Task/Window/Module relationship
    #     return self._project._data2Obj.get(self._wrappedData.window)
    #
    # @window.setter
    # def window(self, value: Window):
    #     value = self.getByPid(value) if isinstance(value, str) else value
    #     self._wrappedData.window = value and value._wrappedData

    @property
    def nmrResidue(self) -> NmrResidue:
        """NmrResidue attached to SpectrumDisplay"""
        return self._project._data2Obj.get(self._wrappedData.resonanceGroup)

    @nmrResidue.setter
    def nmrResidue(self, value: NmrResidue):
        value = self.getByPid(value) if isinstance(value, str) else value
        self._wrappedData.resonanceGroup = value and value._wrappedData

    @property
    def positions(self) -> Tuple[float, ...]:
        """Axis centre positions, in display order"""
        return self._wrappedData.positions

    @positions.setter
    def positions(self, value):
        self._wrappedData.positions = value

    @property
    def widths(self) -> Tuple[float, ...]:
        """Axis display widths, in display order"""
        return self._wrappedData.widths

    @widths.setter
    def widths(self, value):
        self._wrappedData.widths = value

    @property
    def units(self) -> Tuple[str, ...]:
        """Axis units, in display order"""
        return [a.unit for a in self.axes]

    @units.setter
    def units(self, value):
        # local import to avoid cycles
        from ccpn.ui.gui.lib.GuiSpectrumDisplay import AXISUNITS, AXISUNIT_NUMBER
        options = AXISUNITS + [AXISUNIT_NUMBER] # To allow for 1D intensity axis unit
        for idx, val in enumerate(value):
            if val not in options:
                raise ValueError('Invalid units[%d] %r; should be on of %r' % (idx, val, options))
            self.axes[idx].unit = val
        # assure the update of the widgets is done
        self._updateAxesUnits()
        # self._wrappedData.units = value

    def _getUnitsIndices(self):
        """Conveniance function to get units as an index
        CCPNINTERNAL: used CcppnOpenGl.initialiseAxes()
        """
        from ccpn.ui.gui.lib.GuiSpectrumDisplay import AXISUNITS, AXISUNIT_NUMBER
        options = AXISUNITS + [AXISUNIT_NUMBER] # To allow for 1D intensity axis unit
        return [options.index(unit) for unit in self.units]

    # GWV WTF?? Why is this even here?????
    # @property
    # def parameters(self) -> dict:
    #     """Keyword-value dictionary of parameters.
    #     NB the value is a copy - modifying it will not modify the actual data.
    #
    #     Values can be anything that can be exported to JSON,
    #     including OrderedDict, numpy.ndarray, ccpn.util.Tensor,
    #     or pandas DataFrame, Series, or Panel"""
    #     return dict((x.name, x.value) for x in self._wrappedData.parameters)
    #
    # def setParameter(self, name: str, value):
    #     """Add name:value to parameters, overwriting existing entries"""
    #     apiData = self._wrappedData
    #     parameter = apiData.findFirstParameter(name=name)
    #     if parameter is None:
    #         apiData.newParameter(name=name, value=value)
    #     else:
    #         parameter.value = value
    #
    # def deleteParameter(self, name: str):
    #     """Delete parameter named 'name'"""
    #     apiData = self._wrappedData
    #     parameter = apiData.findFirstParameter(name=name)
    #     if parameter is None:
    #         raise KeyError("No parameter named %s" % name)
    #     else:
    #         parameter.delete()
    #
    # def clearParameters(self):
    #     """Delete all parameters"""
    #     for parameter in self._wrappedData.parameters:
    #         parameter.delete()
    #
    # def updateParameters(self, value: dict):
    #     """update parameters"""
    #     for key, val in value.items():
    #         self.setParameter(key, val)

    def _getSpectra(self):
        if len(self.strips) > 0:  # strips
            return [x.spectrum for x in self.orderedSpectrumViews(self.strips[0].spectrumViews)]

    @renameObject()
    def rename(self, name):
        """
        Rename the Spectrum Display core object.
        Note to rename the GuiModule GuiSpectrumDisplay object use the method "renameModule".
        Renaming from the GuiSpectrumDisplay ensures all graphical objects are updated correctly.
        """
        oldName = self.title
        if name != self.id:
            if self._project.getSpectrumDisplay(name):
                getLogger().warning('Cannot rename spectrum Display', 'Name Already Taken')
                return (oldName,)
        try:
            self._validateStringValue('name', name)
            del self.project._pid2Obj[self.shortClassName][self._id]
            apiDisplay = self._wrappedData
            apiTask = apiDisplay.parent
            apiModules = apiTask.__dict__.get('modules')
            apiModules[name] = apiModules.pop(self._id)
            apiDisplay.__dict__['name'] = name
            self._id = name
            return (oldName,)
        except Exception as err:
            getLogger().warning('Cannot rename spectrum Display', err)
            getLogger().exception(str(err))

        return (oldName,)

    # #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # # ejb - orderedSpectrumViews, orderedSpectra
    # # store the current orderedSpectrumViews in the internal data store
    # # so it is hidden from external users

    def orderedSpectrumViews(self, spectrumList, includeDeleted=False) -> Optional[Tuple]:
        """
        The spectrumViews attached to the strip (ordered)
        :return tuple of SpectrumViews:
        """
        if not self._orderedSpectrumViews:
            self._orderedSpectrumViews = OrderedSpectrumViews(parent=self)
        return self._orderedSpectrumViews.orderedSpectrumViews((spectrumList or self.strips[0].spectrumViews), includeDeleted=includeDeleted)

    def getOrderedSpectrumViewsIndex(self) -> Optional[Tuple]:
        """
        The indexing of the current spectrumViews
        :return tuple of ints:
        """
        if not self._orderedSpectrumViews:
            self._orderedSpectrumViews = OrderedSpectrumViews(parent=self)
        return self._orderedSpectrumViews.getOrderedSpectrumViewsIndex()

    def _rescaleSpectra(self):
        """Reorder the buttons and spawn a redraw event
        """
        self.spectrumToolBar.reorderButtons(self.orderedSpectrumViews(self.strips[0].spectrumViews))

        # spawn the required event to reordered the spectrumViews in openGL
        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

        GLSignals = GLNotifier(parent=None)
        GLSignals._emitAxisUnitsChanged(source=None, strip=self.strips[0], dataDict={})

    def moveSpectrumByIndex(self, startInd, endInd):
        """Move spectrum in spectrumDisplay list from index startInd to endInd
        startInd/endInd are the order as seen in the spectrumToolbar
        """
        _order = self.getOrderedSpectrumViewsIndex()
        _newOrder = list(_order)

        _last = _newOrder.pop(startInd)
        _newOrder.insert(endInd, _last)

        self.setOrderedSpectrumViewsIndex(_newOrder)
        self._rescaleSpectra()

    @logCommand(get='self')
    def setOrderedSpectrumViewsIndex(self, spectrumIndex: Tuple[int]):
        """
        Set the new indexing of the spectrumViews attached to the strip/spectrumDisplay
        :param newIndex - tuple of int:
        """
        # TODO:ED this should really be in GuiSpectrumDisplay
        if not all(isinstance(val, int) for val in spectrumIndex):
            raise ValueError("spectrum indexing values must be Int")

        with undoBlockWithoutSideBar():

            # rebuild the display when the ordering has changed
            with undoStackBlocking() as addUndoItem:
                addUndoItem(undo=self._rescaleSpectra)

            if not self._orderedSpectrumViews:
                self._orderedSpectrumViews = OrderedSpectrumViews(parent=self)
            self._orderedSpectrumViews.setOrderedSpectrumViewsIndex(spectrumIndex=spectrumIndex)
            self._rescaleSpectra()

            # rebuild the display when the ordering has changed
            with undoStackBlocking() as addUndoItem:
                addUndoItem(redo=self._rescaleSpectra)

    def _removeOrderedSpectrumViewIndex(self, index):
        # self.removeOrderedSpectrumView(index)
        pass

    @logCommand(get='self')
    def removeOrderedSpectrumView(self, ind):
        if not isinstance(ind, int):
            raise TypeError('ind %s is not of type Int' % str(ind))

        index = ind  #.spectrumViews.index(spectrumView)
        with undoBlockWithoutSideBar():

            if not self._orderedSpectrumViews:
                self._orderedSpectrumViews = OrderedSpectrumViews(parent=self)
            oldIndex = list(self.getOrderedSpectrumViewsIndex())

            # rebuild the display when the ordering has changed
            with undoStackBlocking() as addUndoItem:
                addUndoItem(undo=self._rescaleSpectra)

            # index = oldIndex.index(ind)
            oldIndex.remove(index)
            for ii in range(len(oldIndex)):
                if oldIndex[ii] > index:
                    oldIndex[ii] -= 1
            self._orderedSpectrumViews.setOrderedSpectrumViewsIndex(spectrumIndex=oldIndex)

            # rebuild the display when the ordering has changed
            with undoStackBlocking() as addUndoItem:
                addUndoItem(redo=self._rescaleSpectra)

    # CCPN functions
    @logCommand(get='self')
    def resetAxisOrder(self):
        """Reset display to original axis order"""

        with undoBlockWithoutSideBar():
            self._wrappedData.resetAxisOrder()

    def findAxis(self, axisCode):
        """Find axis """
        return self._project._data2Obj.get(self._wrappedData.findAxis(axisCode))

    # def appendSpectrumView(self, spectrumView):
    #   """
    #   Append a SpectrumView to the end of the ordered spectrumviews
    #   :param spectrumView - new SpectrumView:
    #   """
    #   if not self._orderedSpectrumViews:
    #     self._orderedSpectrumViews = OrderedSpectrumViews(parent=self)
    #   self._orderedSpectrumViews.appendSpectrumView(spectrumView)
    #
    # def removeSpectrumView(self, spectrumView):
    #   """
    #   Remove a SpectrumView from the ordered spectrumviews
    #   :param spectrumView - SpectrumView to be removed:
    #   """
    #   if not self._orderedSpectrumViews:
    #     self._orderedSpectrumViews = OrderedSpectrumViews(parent=self)
    #   self._orderedSpectrumViews.removeSpectrumView(spectrumView)

    @property
    def orderedStrips(self):
        """Return the ccpn.Strips in displayed order"""
        ff = self._project._data2Obj.get
        return tuple(ff(x) for x in self._wrappedData.orderedStrips)

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: Project) -> list:
        """get wrappedData (ccp.gui.Module) for all SpectrumDisplay children of Project"""

        apiGuiTask = (parent._wrappedData.findFirstGuiTask(nameSpace='user', name='View') or
                      parent._wrappedData.root.newGuiTask(nameSpace='user', name='View'))
        return [x for x in apiGuiTask.sortedModules() if isinstance(x, ApiBoundDisplay)]

    # @deleteObject()
    # def delete(self):
    #     """Delete object, with all contained objects and underlying data.
    #     """
    #     self._wrappedData.delete()

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    def _setFromLimits(self, axis, value):
        """Set width,position for axis from value tuple/list"""
        width = value[1] - value[0] if value[1]>value[0] else value[0] - value[1]
        pos = value[0] + width*0.5 if value[1]>value[0] else value[0] - width*0.5

        positions = list(self.positions)
        positions[axis] = pos
        self.positions = positions

        widths = list(self.widths)
        widths[axis] = width
        self.widths = widths

    def _getDimensionsMapping(self, spectrum:Spectrum) -> list:
        """Get the spectrum dimensions in display order
        """
        # For now: do not allow spectrum mapping with higher dimensionality than the display
        if spectrum.dimensionCount > self.dimensionCount:
            raise RuntimeError('Cannot display %s onto %s; dimensionality mismatch' % (spectrum, self))

        spectrumAxisCodes = spectrum._mapAxisCodes(self.axisCodes)[:spectrum.dimensionCount]
        if None in spectrumAxisCodes:
            raise RuntimeError('Cannot display %s on %s; incompatible axisCodes' % (spectrum, self))

        dimensionOrder = spectrum.getByAxisCodes('dimensions', spectrumAxisCodes, exactMatch=True)

        return dimensionOrder

    def _getAxesMapping(self, spectrum:Spectrum) -> list:
        """Get the spectrum axes in display order
        CCPNMRINTERNAL: used in _newSpectrumDisplay
        """
        return [dim-1 for dim in self._getDimensionsMapping(spectrum)]

    def _setLimits(self, spectrum:Spectrum):
        """Define the relevant display limits from the dimensions of spectrum
        CCPNMRINTERNAL: used in _newSpectrumDisplay
        """
        # NB setting Axis.region translates into setting position (== halfway point)
        # and widths of the axis

        # Get the mapping of the the axes of spectrum onto this SpectrumDisplay
        spectrumAxes = self._getAxesMapping(spectrum)

        if spectrum.dimensionCount == 1:
            # 1D spectrum
            ppmLimits, valueLimits = spectrum.get1Dlimits()
            self.axes[0].region = ppmLimits
            self.axes[1].region = valueLimits

        else:
            # nD
            for ii, axis in enumerate(spectrumAxes):
                if ii < 2:
                    self.axes[ii].region = spectrum.spectrumLimits[axis]

                else:
                    # A display "plane-axis"
                    self.axes[ii].region = spectrum.spectrumLimits[axis]
                    self.axes[ii].width = spectrum.valuesPerPoint[axis]
                    if spectrum.isTimeDomains[axis]:
                        self.axes[ii].position = 1.0

        # Copy to strips
        for strip in self.strips:
            strip.positions = self.positions
            strip.widths = self.widths


    #===========================================================================================
    # new'Object' and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================


#=========================================================================================
# Connections to parents:
#=========================================================================================

@newObject(SpectrumDisplay)
@logCommand('mainWindow.')
def _newSpectrumDisplay(window: Window, spectrum: Spectrum, axisCodes: (str,),
                        stripDirection: str = 'Y', name: str = None,
                        zPlaneNavigationMode: str = None,
                        isGrouped: bool = False):
    """Create new SpectrumDisplay

    :param window:
    :param spectrum: a Spectrum instance to be displayed
    :param axisCodes: display order of the dimensions of spectrum
    :param stripDirection: stripDirection: if 'X' or 'Y' set strip axis
    :param name: optional name
    :param zPlaneNavigationMode:
    :return: a new SpectrumDisplay instance.
    """
    # local import to avoid cycles
    from ccpn.ui.gui.lib.GuiSpectrumDisplay import AXISUNIT_PPM, AXISUNIT_POINT, AXISUNIT_NUMBER

    if window is None or not isinstance(window, Window):
        raise ValueError('Expected window argument; got %r' % window)
    apiWindow = window._wrappedData
    apiTask = apiWindow.getGuiTask()
    project = window.project

    if (spectrum := project.getByPid(spectrum) if isinstance(spectrum, str) else spectrum) is None:
        raise ValueError('_newSpectrumDisplay: undefined spectrum')
    is1D = (spectrum.dimensionCount == 1)

    # set api-parameters for display generation
    displayPars = dict(
            stripDirection=stripDirection,
            window=apiWindow,
            )

    if is1D:
        axisCodes = spectrum.axisCodes + ['intensity']
    if len(axisCodes) < 2:
        raise ValueError("New SpectrumDisplay must have at least two axisCodes")
    displayPars['axisCodes'] = displayPars['axisOrder'] = axisCodes

    # Add name, setting and insuring uniqueness if necessary
    if name is None:
        excludedNames = ['intensity']
        name = ''.join(['%dD_' % spectrum.dimensionCount] + [str(x)[0:1] for x in axisCodes if x not in excludedNames])
    name = SpectrumDisplay._uniqueApiName(project, name)
    displayPars['name'] = name

    # Create Boundstrip/Nostrip display and first strip
    apiSpectrumDisplay = apiTask.newBoundDisplay(**displayPars)
    if (display := project._data2Obj.get(apiSpectrumDisplay)) is None:
        raise RuntimeError('Unable to generate new SpectrumDisplay')

    # may need to set other values here, guarantees before strip generation
    display.stripArrangement = stripDirection
    if zPlaneNavigationMode:
        display.zPlaneNavigationMode = zPlaneNavigationMode
    # GWV: no idea what these are for; just adapted from original code
    # it gets crazy on 1D displays
    # display._useFirstDefault = (False if is1D else True)
    display.isGrouped = isGrouped

    # Create first strip; looks like we need this before other things, otherwise the api goes crazy
    apiStrip = apiSpectrumDisplay.newBoundStrip()
    if (strip := project._data2Obj.get(apiStrip)) is None:
        raise RuntimeError('Unable to generate new Strip for %s' % display)

    # Create axes
    if is1D:
        if spectrum.dimensionTypes[0] == specLib.DIMENSION_FREQUENCY:
            apiSpectrumDisplay.newFrequencyAxis(code=axisCodes[0], stripSerial=1, unit=AXISUNIT_PPM)
        elif spectrum.dimensionTypes[0] == specLib.DIMENSION_TIME:
            apiSpectrumDisplay.newFidAxis('time', stripSerial=1, unit=AXISUNIT_POINT)

        apiSpectrumDisplay.newIntensityAxis(code='intensity', stripSerial=1, unit=AXISUNIT_NUMBER)

        display._isotopeCodes = tuple(spectrum.isotopeCodes)

    else:
        # nD
        spectrumAxes = display._getAxesMapping(spectrum)
        display._isotopeCodes = tuple(spectrum.isotopeCodes[axis] for axis in spectrumAxes)

        for ii, axis in enumerate(spectrumAxes):
            displayAxisCode = axisCodes[ii]

            # if (ii == 0 and stripDirection == 'X' or ii == 1 and stripDirection == 'Y' or
            #    not stripDirection):
            # Reactivate this code if we reintroduce non-strip displays (stripDirection == None)
            if (ii == 0 and stripDirection == 'X' or ii == 1 and stripDirection == 'Y'):
                stripSerial = 0
            else:
                stripSerial = 1

            # NOTE: ED setting to 1 notifies api to create a full axis set for each additional spectrum
            #       required for dynamic switching of strip arrangement
            #       stripDirection is no longer used in the api
            stripSerial = 1

            if spectrum.dimensionTypes[axis] == specLib.DIMENSION_FREQUENCY:
                apiSpectrumDisplay.newFrequencyAxis(code=displayAxisCode, stripSerial=1, unit=AXISUNIT_PPM)

            elif spectrum.dimensionTypes[axis] == specLib.DIMENSION_TIME:
                # Cannot do; all falls apart
                # apiSpectrumDisplay.newFidAxis(code=axisCode, stripSerial=1, unit=AXISUNIT_POINT)
                apiSpectrumDisplay.newFrequencyAxis(code=displayAxisCode, stripSerial=1, unit=AXISUNIT_POINT)

            else:
                raise NotImplementedError('No sampled axes (yet)')


    display._setLimits(spectrum)

    # display the spectrum, this will also create a new spectrumView
    spectrumView = display.displaySpectrum(spectrum=spectrum)
    # We only can set the z-widgets when there is a spectrumView; which we just created
    strip._setZWidgets()

    # call any post initialise routines for the spectrumDisplay here
    display._postInit()

    return display


#EJB 20181206: moved to _implementation.Window
# Window.createSpectrumDisplay = _createSpectrumDisplay
# del _createSpectrumDisplay

# GWV 20210807: moved to _implementation.Window
# # Window.spectrumDisplays property
# def getter(window: Window):
#     ll = [x for x in window._wrappedData.sortedModules() if isinstance(x, ApiBoundDisplay)]
#     return tuple(window._project._data2Obj[x] for x in ll if x in window._project._data2Obj)
#
#
# Window.spectrumDisplays = property(getter, None, None,
#                                    "SpectrumDisplays shown in Window")
# del getter

# Notifiers:

# crosslinks window, nmrResidue
Project._apiNotifiers.append(
        ('_modifiedLink', {'classNames': ('Window', 'SpectrumDisplay')},
         ApiBoundDisplay._metaclass.qualifiedName(), 'setWindow'),
        )
Project._apiNotifiers.append(
        ('_modifiedLink', {'classNames': ('NmrResidue', 'SpectrumDisplay')},
         ApiBoundDisplay._metaclass.qualifiedName(), 'setResonanceGroup'),
        )
className = ApiWindow._metaclass.qualifiedName()
Project._apiNotifiers.extend(
        (('_modifiedLink', {'classNames': ('SpectrumDisplay', 'Window')}, className, 'addModule'),
         ('_modifiedLink', {'classNames': ('SpectrumDisplay', 'Window')}, className, 'removeModule'),
         ('_modifiedLink', {'classNames': ('SpectrumDisplay', 'Window')}, className, 'setModules'),
         )
        )

# WARNING link notifiers for both Window <-> Module and Window<->SpectrumDisplay
# are triggered together when  the change is on the Window side.
# Programmer take care that your notified function will work for both inputs !!!
className = ApiResonanceGroup._metaclass.qualifiedName()
Project._apiNotifiers.extend(
        (('_modifiedLink', {'classNames': ('SpectrumDisplay', 'NmrResidue')}, className,
          'addSpectrumDisplay'),
         ('_modifiedLink', {'classNames': ('SpectrumDisplay', 'NmrResidue')}, className,
          'removeSpectrumDisplay'),
         ('_modifiedLink', {'classNames': ('SpectrumDisplay', 'NmrResidue')}, className,
          'setSpectrumDisplays'),
         )
        )
