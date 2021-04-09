"""GUI SpectrumDisplay class

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-04-09 10:45:12 +0100 (Fri, April 09, 2021) $"
__version__ = "$Revision: 3.0.3 $"
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
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import Pid
from ccpn.core.lib.OrderedSpectrumViews import OrderedSpectrumViews
from ccpn.core.lib.ContextManagers import newObject, undoStackBlocking, undoBlock, deleteObject
from ccpn.ui._implementation.Window import Window
from ccpn.util import Common as commonUtil
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, undoStackBlocking, undoBlockWithoutSideBar, deleteObject
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

    # CCPN properties
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
    def stripCount(self) -> str:
        """Number of strips"""
        return self._wrappedData.stripCount

    @property
    def axisCodes(self) -> Tuple[str, ...]:
        """Fixed string Axis codes in original display order (X, Y, Z1, Z2, ...)"""
        # TODO axisCodes shold be unique, but I am not sure this is enforced
        return self._wrappedData.axisCodes

    @property
    def axisOrder(self) -> Tuple[str, ...]:
        """String Axis codes in display order (X, Y, Z1, Z2, ...), determine axis display order"""
        return self._wrappedData.axisOrder

    @axisOrder.setter
    def axisOrder(self, value: Sequence):
        self._wrappedData.axisOrder = value

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
        return self._wrappedData.units

    @property
    def parameters(self) -> dict:
        """Keyword-value dictionary of parameters.
        NB the value is a copy - modifying it will not modify the actual data.

        Values can be anything that can be exported to JSON,
        including OrderedDict, numpy.ndarray, ccpn.util.Tensor,
        or pandas DataFrame, Series, or Panel"""
        return dict((x.name, x.value) for x in self._wrappedData.parameters)

    def setParameter(self, name: str, value):
        """Add name:value to parameters, overwriting existing entries"""
        apiData = self._wrappedData
        parameter = apiData.findFirstParameter(name=name)
        if parameter is None:
            apiData.newParameter(name=name, value=value)
        else:
            parameter.value = value

    def deleteParameter(self, name: str):
        """Delete parameter named 'name'"""
        apiData = self._wrappedData
        parameter = apiData.findFirstParameter(name=name)
        if parameter is None:
            raise KeyError("No parameter named %s" % name)
        else:
            parameter.delete()

    def clearParameters(self):
        """Delete all parameters"""
        for parameter in self._wrappedData.parameters:
            parameter.delete()

    def updateParameters(self, value: dict):
        """update parameters"""
        for key, val in value.items():
            self.setParameter(key, val)

    def _getSpectra(self):
        if len(self.strips) > 0:  # strips
            return [x.spectrum for x in self.orderedSpectrumViews(self.strips[0].spectrumViews)]

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

    @deleteObject()
    def delete(self):
        """Delete object, with all contained objects and underlying data.
        """
        self._wrappedData.delete()

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    #===========================================================================================
    # new'Object' and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================


#=========================================================================================
# Connections to parents:
#=========================================================================================

@newObject(SpectrumDisplay)
def _newSpectrumDisplay(self: Project, axisCodes: (str,), stripDirection: str = 'Y',
                        title: str = None, window: Window = None, comment: str = None,
                        independentStrips=False, nmrResidue=None, serial: int = None,
                        zPlaneNavigationMode: str = None):
    """Create new SpectrumDisplay

    See the SpectrumDisplay class for details.

    :param axisCodes:
    :param stripDirection:
    :param title:
    :param window:
    :param comment:
    :param independentStrips:
    :param nmrResidue:
    :param serial: optional serial number.
    :return: a new SpectrumDisplay instance.
    """

    window = self.getByPid(window) if isinstance(window, str) else window
    nmrResidue = self.getByPid(nmrResidue) if isinstance(nmrResidue, str) else nmrResidue

    apiTask = (self._wrappedData.findFirstGuiTask(nameSpace='user', name='View') or
               self._wrappedData.root.newGuiTask(nameSpace='user', name='View'))

    if len(axisCodes) < 2:
        raise ValueError("New SpectrumDisplay must have at least two axisCodes")

    # set parameters for display
    window = window or apiTask.sortedWindows()[0]
    displayPars = dict(
            stripDirection=stripDirection, window=window,
            details=comment, resonanceGroup=nmrResidue and nmrResidue._wrappedData
            )

    # Add name, setting and insuring uniqueness if necessary
    if title is None:
        if 'intensity' in axisCodes:
            title = ''.join(['1D:', axisCodes[0]] + list(axisCodes[2:]))
        else:
            title = ''.join([str(x)[0:1] for x in axisCodes])
    elif Pid.altCharacter in title:
        raise ValueError("Character %s not allowed in gui.core.SpectrumDisplay.name" % Pid.altCharacter)
    while apiTask.findFirstModule(name=title):
        title = commonUtil.incrementName(title)
    displayPars['name'] = title

    if independentStrips:
        # Create FreeStripDisplay
        apiSpectrumDisplay = apiTask.newFreeDisplay(**displayPars)
    else:
        # Create Boundstrip/Nostrip display and first strip
        displayPars['axisCodes'] = displayPars['axisOrder'] = axisCodes
        apiSpectrumDisplay = apiTask.newBoundDisplay(**displayPars)

    # Create axes
    for ii, code in enumerate(axisCodes):
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

        if code[0].isupper():
            apiSpectrumDisplay.newFrequencyAxis(code=code, stripSerial=stripSerial)
        elif code == 'intensity':
            apiSpectrumDisplay.newIntensityAxis(code=code, stripSerial=stripSerial)
        elif code.startswith('fid'):
            apiSpectrumDisplay.newFidAxis(code=code, stripSerial=stripSerial)
        else:
            apiSpectrumDisplay.newSampledAxis(code=code, stripSerial=stripSerial)

    result = self._project._data2Obj.get(apiSpectrumDisplay)
    if result is None:
        raise RuntimeError('Unable to generate new SpectrumDisplay item')

    result.stripArrangement = stripDirection
    # may need to set other values here, guarantees before strip generation
    if zPlaneNavigationMode:
        result.zPlaneNavigationMode = zPlaneNavigationMode

    # Create first strip
    if independentStrips:
        apiSpectrumDisplay.newFreeStrip(axisCodes=axisCodes, axisOrder=axisCodes)
    else:
        apiSpectrumDisplay.newBoundStrip()

    if serial is not None:
        try:
            result.resetSerial(serial)
        except ValueError:
            logger = getLogger()
            logger.warning("Could not reset serial of %s to %s - keeping original value"
                           % (result, serial))

    return result


#EJB 20181205: moved to Project
# Project.newSpectrumDisplay = _newSpectrumDisplay
# del _newSpectrumDisplay


def _createSpectrumDisplay(window: Window, spectrum: Spectrum, displayAxisCodes: Sequence[str] = (),
                           axisOrder: Sequence[str] = (), title: str = None, positions: Sequence[float] = (),
                           widths: Sequence[float] = (), units: Sequence[str] = (),
                           stripDirection: str = 'Y', is1D: bool = False,
                           independentStrips: bool = False, isGrouped=False,
                           zPlaneNavigationMode: str = 'strip'):
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

    if title and Pid.altCharacter in title:
        raise ValueError("Character %s not allowed in gui.core.SpectrumDisplay.name" % Pid.altCharacter)

    spectrum = window.getByPid(spectrum) if isinstance(spectrum, str) else spectrum
    dataSource = spectrum._wrappedData
    project = window._project

    axisOrder = spectrum.getDefaultOrdering(axisOrder)
    spectrumAxisCodes = spectrum.axisCodes

    if axisOrder:
        mapIndices = commonUtil._axisCodeMapIndices(spectrumAxisCodes, axisOrder)
        if displayAxisCodes:
            if not commonUtil.doAxisCodesMatch(axisOrder, displayAxisCodes):
                raise ValueError("AxisOrder %s do not match display axisCodes %s"
                                 % (axisOrder, displayAxisCodes))
        else:
            displayAxisCodes = axisOrder
    elif displayAxisCodes:
        mapIndices = commonUtil._axisCodeMapIndices(spectrumAxisCodes, displayAxisCodes)
    else:
        displayAxisCodes = list(spectrumAxisCodes)
        mapIndices = list(range(dataSource.numDim))
        if is1D:
            displayAxisCodes.insert(1, 'intensity')
            mapIndices.insert(1, None)

    # Make DataDim ordering
    sortedDataDims = dataSource.sortedDataDims()
    orderedDataDims = []
    for index in mapIndices:
        if index is None:
            orderedDataDims.append(None)
        else:
            orderedDataDims.append(sortedDataDims[index])

    # Make dimensionOrdering
    dimensionOrdering = [(0 if x is None else x.dim) for x in orderedDataDims]

    # Add intensity dimension for 1D if necessary
    if dataSource.numDim == 1 and len(displayAxisCodes) == 1:
        displayAxisCodes += ('intensity',)
        dimensionOrdering.append(0)

    if dataSource.findFirstDataDim(className='SampledDataDim') is not None:
        # logger.warning( "Display of sampled dimension spectra is not implemented yet")
        # showWarning("createSpectrumDisplay", "Display of sampled dimension spectra is not implemented yet")
        # return
        raise NotImplementedError(
                "Display of sampled dimension spectra is not implemented yet")
        # # NBNB TBD FIXME

    with undoBlockWithoutSideBar():
        display = project.newSpectrumDisplay(axisCodes=displayAxisCodes, stripDirection=stripDirection,
                                             independentStrips=independentStrips,
                                             title=title, zPlaneNavigationMode=zPlaneNavigationMode)

        # Set unit, position and width
        orderedApiAxes = display._wrappedData.orderedAxes
        for ii, dataDim in enumerate(orderedDataDims):

            if dataDim is not None:
                # Set values only if we have a spectrum axis

                # Get unit, position and width
                dataDimRef = dataDim.primaryDataDimRef
                if dataDimRef:
                    # This is a FreqDataDim
                    unit = dataDimRef.expDimRef.unit
                    position = dataDimRef.pointToValue(1) - dataDimRef.spectralWidth / 2
                    if ii < 2:
                        width = dataDimRef.spectralWidth
                    else:
                        width = dataDimRef.valuePerPoint

                elif dataDim.className == 'SampledDataDim':

                    unit = dataDim.unit
                    width = len(dataDim.pointValues)
                    position = 1 + width // 2
                    if ii >= 2:
                        width = 1
                    # NBNB TBD this may not work, once we implement sampled axes

                else:
                    # This is a FidDataDim
                    unit = dataDim.unit
                    width = dataDim.maxValue - dataDim.firstValue
                    position = width / 2
                    if ii >= 2:
                        width = dataDim.valuePerPoint

                # Set values
                apiAxis = orderedApiAxes[ii]
                apiAxis.unit = unit
                apiAxis.position = position
                apiAxis.width = width

        # set the intensity axes not caught by the dataDims
        for apiAxis in orderedApiAxes[len(orderedDataDims):]:
            if apiAxis.code == 'intensity':
                _intensities = spectrum.intensities
                # assumes _intensities if a numpy array
                if not isinstance(_intensities, ndarray):
                    raise TypeError(f'spectrum.intensities {spectrum.id} must be an ndarray')

                if _intensities is not None and _intensities.size != 0:
                    _max, _min = max(_intensities), min(_intensities)
                    apiAxis.position = float(_min + _max) / 2
                    apiAxis.width = float(_max - _min)

        if dataSource.numDim != 1:  # it gets crazy on 1D displays
            display._useFirstDefault = False

        display.isGrouped = isGrouped

    # Make spectrumView. NB We need notifiers on for these
    stripSerial = 1 if independentStrips else 0
    _newSpectrumView = display._wrappedData.newSpectrumView(spectrumName=dataSource.name,
                                                            stripSerial=stripSerial, dataSource=dataSource,
                                                            dimensionOrdering=dimensionOrdering)

    # call any post initialise routines for the spectrumDisplay here
    display._postInit()

    return display


#EJB 20181206: moved to _implementation.Window
# Window.createSpectrumDisplay = _createSpectrumDisplay
# del _createSpectrumDisplay


# Window.spectrumDisplays property
def getter(window: Window):
    ll = [x for x in window._wrappedData.sortedModules() if isinstance(x, ApiBoundDisplay)]
    return tuple(window._project._data2Obj[x] for x in ll if x in window._project._data2Obj)


Window.spectrumDisplays = property(getter, None, None,
                                   "SpectrumDisplays shown in Window")
del getter

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
