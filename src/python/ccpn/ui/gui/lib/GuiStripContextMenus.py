"""
A File containing all the context menus of a gui Strip.
To create a menu:
 - make a list of objs of type _SCMitem
 - call the function _createMenu, give the strip where the context menu will be needed and the list of items

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
__dateModified__ = "$dateModified: 2021-10-07 18:40:32 +0100 (Thu, October 07, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2018-05-17 10:28:43 +0000 (Thu, May 17, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.widgets.Menu import Menu
from ccpn.util.Logging import getLogger
from functools import partial


MENU = 'Menu'
ITEM = 'Item'
SEPARATOR = 'Separator'

ItemTypes = {
    MENU     : Menu.addMenu.__name__,
    ITEM     : Menu.addItem.__name__,
    SEPARATOR: Menu._addSeparator.__name__
    }


class _SCMitem(object):
    """Strip context menu item base class. Used to autogenerate the context menu items in a Gui strip """

    def __init__(self, typeItem, **kwargs):
        """
        :param typeItem: any value of ItemTypes: (menu,item,separator)
        :param kwargs: needed  any of _kwrgs: name, icon, tooltip, shortcut, checkable, checked, callback, stripMethodName
        or any other accepted by Base or Action widgets
        """
        self._kwrgs = {'name'   : '', 'icon': None, 'tooltip': '', 'shortcut': None, 'checkable': False,
                       'checked': False, 'callback': None, 'stripMethodName': '', 'obj': self}
        self._kwrgs.update(kwargs)
        for k, v in self._kwrgs.items():
            setattr(self, k, v)
        self.typeItem = typeItem


def _createMenu(strip, items):
    """
    :param strip: 1D or nD GuiStrip Object
    :param items:  a list of _SCMitem obj :
    :return: Creates and returns a context menu for the guiStrip from a list of items
    """
    if not hasattr(strip, '_spectrumUtilActions'):
        strip._spectrumUtilActions = {}

    menu = strip.contextMenu = Menu('', strip, isFloatWidget=True)  # generate new menu

    for i in items:
        try:
            ff = getattr(menu, i.typeItem)
            if ff:
                action = ff(i.name, **vars(i))
                if i.stripMethodName:
                    if hasattr(strip, i.stripMethodName):
                        # check whether items already in widget
                        raise RuntimeError(f'Strip already contains action {i.stripMethodName}')
                    setattr(strip, i.stripMethodName, action)
                    if hasattr(strip, '_spectrumUtilActions'):
                        strip._spectrumUtilActions[i.stripMethodName] = action

        except Exception as e:
            getLogger().warning('_createMenu error: %s' % str(e))
    return menu


def _addMenuItems(widget, menu, items):
    """Add items to an existing menu
    """
    for i in items:
        try:
            ff = getattr(menu, i.typeItem)
            if ff:
                action = ff(i.name, **vars(i))
                if i.stripMethodName:
                    if hasattr(widget, i.stripMethodName):
                        # check whether items already in widget
                        raise RuntimeError(f'Strip already contains action {i.stripMethodName}')
                    setattr(widget, i.stripMethodName, action)
                    if hasattr(widget, '_spectrumUtilActions'):
                        widget._spectrumUtilActions[i.stripMethodName] = action

        except Exception as e:
            getLogger().warning('_addMenuItems error: %s' % str(e))


##############################  Common default  menu items ##############################
## These items are used to create both 1D and Nd menus


def _toolBarItem(strip):
    return _SCMitem(name='Toolbar',
                    typeItem=ItemTypes.get(ITEM), toolTip='Toggle Toolbar On/Off',
                    callback=strip.spectrumDisplay.toggleToolbar,
                    checkable=True, checked=True, shortcut='TB', stripMethodName='toolbarAction')


def _spectrumToolBarItem(strip):
    return _SCMitem(name='Spectrum Toolbar',
                    typeItem=ItemTypes.get(ITEM), toolTip='Toggle Spectrum Toolbar On/Off',
                    callback=strip.spectrumDisplay.toggleSpectrumToolbar,
                    checkable=True, checked=True, shortcut='SB', stripMethodName='spectrumToolbarAction')


def _crosshairItem(strip):
    return _SCMitem(name='Crosshair',
                    typeItem=ItemTypes.get(ITEM), toolTip='Toggle Crosshair Mouse On/Off',
                    checkable=True, checked=True, shortcut='CH',
                    callback=strip.spectrumDisplay.toggleCrosshair, stripMethodName='crosshairAction')


def _doubleCrosshairItem(strip):
    return _SCMitem(name='Double Crosshair',
                    typeItem=ItemTypes.get(ITEM), toolTip='Toggle Double/Single Crosshair Mouse',
                    checkable=True, checked=True, shortcut='CD',
                    callback=strip.spectrumDisplay.mainWindow.toggleDoubleCrosshairAll, stripMethodName='doubleCrosshairAction')


def _gridItem(strip):
    return _SCMitem(name='Grid',
                    typeItem=ItemTypes.get(ITEM), toolTip='Toggle Grid On/Off', callback=strip.spectrumDisplay.toggleGrid,
                    checkable=True, checked=True, shortcut='GS', stripMethodName='gridAction')


def _sideBandsItem(strip):
    return _SCMitem(name='Show MAS Side Bands',
                    typeItem=ItemTypes.get(ITEM), toolTip='Toggle MAS Side Bands On/Off', callback=strip.spectrumDisplay.toggleSideBands,
                    checkable=True, checked=True, stripMethodName='sideBandsAction')


def _cyclePeakLabelsItem(strip):
    return _SCMitem(name='Cycle Peak Labels',
                    typeItem=ItemTypes.get(ITEM), icon='icons/preferences-desktop-font',
                    toolTip='Cycle Peak Labelling Types',
                    callback=strip.cycleSymbolLabelling, shortcut='PL', stripMethodName='')


def _cyclePeakSymbolsItem(strip):
    return _SCMitem(name='Cycle Peak Symbols',
                    typeItem=ItemTypes.get(ITEM), icon='icons/peak-symbols',
                    toolTip='Cycle Peak Symbol Types',
                    callback=strip.cyclePeakSymbols, shortcut='PS', stripMethodName='')


def _shareYAxisItem(strip):
    return _SCMitem(name='Share Last Axis',
                    typeItem=ItemTypes.get(ITEM), toolTip='Share last axis among strips', checkable=True, checked=True,
                    callback=strip._toggleLastAxisOnly, shortcut='LA', stripMethodName='lastAxisOnlyCheckBox')


def _contoursItem(strip):
    return _SCMitem(name='Contours...',
                    typeItem=ItemTypes.get(ITEM), icon='icons/contours', toolTip='Change Contour Settings',
                    callback=strip.spectrumDisplay.adjustContours, shortcut='CO')


def _coloursItem(strip):
    return _SCMitem(name='Colours...',
                    typeItem=ItemTypes.get(ITEM), icon='icons/contour-pos-neg', toolTip='Change colours',
                    callback=strip.spectrumDisplay.adjustContours, shortcut='CO')


def _raiseContoursItem(strip):
    return _SCMitem(name='Raise Base Level',
                    typeItem=ItemTypes.get(ITEM), icon='icons/contour-base-up', toolTip='Raise Contour Base Level',
                    callback=strip.spectrumDisplay.raiseContourBaseLevel)


def _lowerContoursItem(strip):
    return _SCMitem(name='Lower Base Level',
                    typeItem=ItemTypes.get(ITEM), icon='icons/contour-base-down', toolTip='Lower Contour Base Level',
                    callback=strip.spectrumDisplay.lowerContourBaseLevel)


def _resetZoom(strip):
    return _SCMitem(name='Reset Zoom',
                    typeItem=ItemTypes.get(ITEM), icon='icons/zoom-full', toolTip='Reset Zoom',
                    callback=strip.resetZoom)


def _zoomXItem(strip):
    return _SCMitem(name='Zoom best X fit',
                    typeItem=ItemTypes.get(ITEM), icon='icons/zoom-full-1d', toolTip='X Auto Scale',
                    callback=strip._resetXZoom),


def _zoomYItem(strip):
    return _SCMitem(name='Zoom best Y fit',
                    typeItem=ItemTypes.get(ITEM), icon='icons/zoom-best-fit-1d', toolTip='Y Auto Scale',
                    callback=strip._resetYZoom),


def _calibrateX(strip):
    return _SCMitem(name='Calibrate X',
                    typeItem=ItemTypes.get(ITEM), toolTip='Calibrate X Axis', checkable=True, checked=False,
                    callback=strip.toggleCalibrateX, stripMethodName='calibrateXAction')


def _calibrateY(strip):
    return _SCMitem(name='Calibrate Y',
                    typeItem=ItemTypes.get(ITEM), toolTip='Calibrate Y Axis', checkable=True, checked=False,
                    callback=strip.toggleCalibrateY, stripMethodName='calibrateYAction')


def _calibrateFromPeaks():
    from ccpn.framework.Framework import getApplication

    _app = getApplication()
    return _SCMitem(name='Calibrate Spectra from Peaks...',
                    typeItem=ItemTypes.get(ITEM), toolTip='Calibrate Spectra from Selected Peaks',
                    # callback=strip.calibrateFromPeaks
                    )


def _calibrateXY(strip):
    return _SCMitem(name='Calibrate Spectra',
                    typeItem=ItemTypes.get(ITEM), toolTip='Calibrate Spectrum Axes', checkable=True, checked=False,
                    callback=strip.toggleCalibrateXY, stripMethodName='calibrateXYAction')


def _toggleHorizontalTraceItem(strip):
    return _SCMitem(name='Horizontal Trace',
                    typeItem=ItemTypes.get(ITEM), toolTip='Toggle Horizontal Trace On/off',
                    checkable=True, checked=False, shortcut='TH', stripMethodName='hTraceAction',
                    callback=strip.toggleHorizontalTrace)


def _toggleVerticalTraceItem(strip):
    return _SCMitem(name='Vertical Trace',
                    typeItem=ItemTypes.get(ITEM), toolTip='Toggle Vertical Trace On/Off',
                    checkable=True, checked=False, shortcut='TV', stripMethodName='vTraceAction',
                    callback=strip.toggleVerticalTrace)


def _phasingConsoleItem(strip):
    return _SCMitem(name='Enter Phasing Console',
                    typeItem=ItemTypes.get(ITEM), icon='icons/phase-console', toolTip='Enter Phasing Console',
                    shortcut='PC', callback=strip.spectrumDisplay.togglePhaseConsole)


def _marksItem(strip):
    return _SCMitem(name='Mark Positions',
                    typeItem=ItemTypes.get(ITEM), toolTip='Mark positions of all Axes', shortcut='MK',
                    callback=strip.createMark)


def _clearMarksItem(strip):
    return _SCMitem(name='Clear Marks',
                    typeItem=ItemTypes.get(ITEM), toolTip='Clear all Marks', shortcut='MC',
                    callback=strip.clearMarks)


def _estimateNoise(strip):
    return _SCMitem(name='Estimate Noise',
                    typeItem=ItemTypes.get(ITEM), toolTip='Estimate spectral noise in the visible region', shortcut='EN',
                    callback=strip.estimateNoise)


def _makeStripPlot(strip):
    return _SCMitem(name='Make Strip Plot...',
                    typeItem=ItemTypes.get(ITEM), toolTip='Make a strip plot in the current SpectrumDisplay', shortcut='SP',
                    callback=strip.makeStripPlot)


def _printItem(strip):
    return _SCMitem(name='Print to File...',
                    typeItem=ItemTypes.get(ITEM), icon='icons/print', toolTip='Print SpectrumDisplay to File',
                    shortcut='⌃p', callback=strip.showExportDialog)


def _separator():
    return _SCMitem(typeItem=ItemTypes.get(SEPARATOR))


def _newStripPlotItem(strip):
    return _SCMitem(name='New strip with same axes',
                    typeItem=ItemTypes.get(ITEM), toolTip='Create new spectrumDisplay from the current strip',
                    callback=strip.copyStrip)


def _newStripPlotXYItem(strip):
    return _SCMitem(name='New strip with X-Y Axes flipped',
                    typeItem=ItemTypes.get(ITEM), toolTip='Create new spectrumDisplay from the current strip\n'
                                                          'with the X-Y axes flipped',
                    shortcut='xy',
                    callback=strip.flipXYAxis)


def _newStripPlotXZItem(strip):
    return _SCMitem(name='New strip with X-Z Axes flipped',
                    typeItem=ItemTypes.get(ITEM), toolTip='Create new spectrumDisplay from the current strip\n'
                                                          'with the X-Z axes flipped',
                    shortcut='xz',
                    callback=strip.flipXZAxis)


def _newStripPlotYZItem(strip):
    return _SCMitem(name='New strip with Y-Z Axes flipped',
                    typeItem=ItemTypes.get(ITEM), toolTip='Create new spectrumDisplay from the current strip\n'
                                                          'with the Y-Z axes flipped',
                    shortcut='yz',
                    callback=strip.flipYZAxis)


def _newStripPlotFAItem(strip):
    from ccpn.framework.Application import getApplication

    app = getApplication()
    return _SCMitem(name='New strip with Axes Flipped...',
                    typeItem=ItemTypes.get(ITEM), toolTip='Create new spectrumDisplay from the current strip',
                    shortcut='fa',
                    callback=app.showFlipArbitraryAxisPopup)


##############################  Common Integral menu items ##############################
## These items are used to create both 1D and Nd integral menus

def _deleteIntegralItem(strip):
    return _SCMitem(name='Delete Integral(s)',
                    typeItem=ItemTypes.get(ITEM), toolTip='Delete Integral(s) from project', callback=strip.mainWindow.deleteSelectedItems)


##############################  Common Multiplet menu items ##############################
## These items are used to create both 1D and Nd Multiplet menus

def _deleteMultipletItem(strip):
    return _SCMitem(name='Delete Multiplet(s)',
                    typeItem=ItemTypes.get(ITEM), toolTip='Delete Multiplet(s) from project', callback=strip.mainWindow.deleteSelectedItems)


##############################  Common Peak menu items ##############################
## These items are used to create both 1D and Nd Peak menus


def _copyPeakItem():
    from ccpn.framework.Framework import getApplication

    _app = getApplication()
    return _SCMitem(name='Copy Peak(s)',
                    typeItem=ItemTypes.get(ITEM), toolTip='Copy Peak(s) to a PeakList', shortcut='CP',
                    callback=_app.mainWindow._openCopySelectedPeaks)


def _deletePeakItem():
    from ccpn.framework.Framework import getApplication

    _app = getApplication()
    return _SCMitem(name='Delete Peak(s)',
                    typeItem=ItemTypes.get(ITEM), toolTip='Delete Peak(s) from project',
                    callback=_app.mainWindow.deleteSelectedItems)


def _editPeakAssignmentItem():
    from ccpn.framework.Framework import getApplication

    _app = getApplication()
    return _SCMitem(name='Edit Peak Assignments',
                    typeItem=ItemTypes.get(ITEM), toolTip='Edit current peak assignments',
                    callback=_app.showPeakAssigner, shortcut='AP')


# def _viewPeakOnTableItem(strip):
#     return _SCMitem(name='View Peak on PeakList Table',
#                     typeItem=ItemTypes.get(ITEM), toolTip='View current peak on a PeakList table', callback=strip._showPeakOnPLTable)

def _deassignPeaksItem():
    from ccpn.framework.Framework import getApplication

    _app = getApplication()
    return _SCMitem(name='Deassign Peak(s)',
                    typeItem=ItemTypes.get(ITEM), toolTip='Deassign Peaks',
                    callback=_app.mainWindow.deassignPeaks)


def _setPeakAliasingItem():
    from ccpn.framework.Framework import getApplication

    _app = getApplication()
    return _SCMitem(name='Set Aliasing...',
                    typeItem=ItemTypes.get(ITEM), toolTip='Set aliasing for current peak(s)',
                    callback=_app.mainWindow.setPeakAliasing)


def _refitPeakItem():
    from ccpn.framework.Framework import getApplication

    _app = getApplication()
    return _SCMitem(name='Refit Peak(s) Singular',
                    typeItem=ItemTypes.get(ITEM), toolTip='Refit current peak(s) as singular', shortcut='RP',
                    callback=partial(_app.mainWindow.refitCurrentPeaks, singularMode=True))


def _refitPeakGroupItem():
    from ccpn.framework.Framework import getApplication

    _app = getApplication()
    return _SCMitem(name='Refit Peak(s) Group',
                    typeItem=ItemTypes.get(ITEM), toolTip='Refit current peak(s) as a group', shortcut='RG',
                    callback=partial(_app.mainWindow.refitCurrentPeaks, singularMode=False))


def _snapToExtremaItem():
    from ccpn.framework.Framework import getApplication

    _app = getApplication()
    return _SCMitem(name='Snap Peak(s) to Extrema',
                    typeItem=ItemTypes.get(ITEM), toolTip='Snap current peak(s) to closest extrema', shortcut='SE',
                    callback=_app.mainWindow.snapCurrentPeaksToExtremum)


def _estimateVolumesItem():
    from ccpn.framework.Framework import getApplication

    _app = getApplication()
    return _SCMitem(name='Estimate Volume(s)',
                    typeItem=ItemTypes.get(ITEM), toolTip='Estimate peak volume(s)', shortcut='EV',
                    callback=_app.mainWindow.estimateVolumes)


def _recalculatePeakHeightsItem():
    from ccpn.framework.Framework import getApplication

    _app = getApplication()
    return _SCMitem(name='Recalculate Height(s)',
                    typeItem=ItemTypes.get(ITEM), toolTip='Recalculate peak height(s) for the same position',
                    shortcut='RH',
                    callback=_app.mainWindow.recalculateCurrentPeakHeights)


def _reorderPeakListAxesItem():
    from ccpn.framework.Framework import getApplication

    _app = getApplication()
    return _SCMitem(name='Reorder PeakList Axes...',
                    typeItem=ItemTypes.get(ITEM), toolTip='Reorder axes for all peaks in peakList containing this peak', shortcut='RL',
                    callback=_app.mainWindow.reorderPeakListAxes)


def _makeStripPlotItem():
    from ccpn.framework.Framework import getApplication

    _app = getApplication()
    return _SCMitem(name='Make Strip Plot...',
                    typeItem=ItemTypes.get(ITEM), toolTip='Make Strip Plot from Selected Peaks', shortcut='SP',
                    callback=partial(_app.mainWindow.makeStripPlot, includePeakLists=True, includeNmrChains=False))


def _newMultipletItem():
    from ccpn.framework.Framework import getApplication

    _app = getApplication()
    return _SCMitem(name='New Multiplet',
                    typeItem=ItemTypes.get(ITEM), toolTip='Add New Multiplet', shortcut='AM',
                    callback=_app.mainWindow.addMultiplet)


def _integrate1DItem():
    from ccpn.framework.Framework import getApplication

    _app = getApplication()
    return _SCMitem(name='Integrate Peak',
                    typeItem=ItemTypes.get(ITEM), toolTip='Add integral and link to peak',
                    callback=_app.mainWindow.add1DIntegral)


def _navigateToCursorPosItem(strip):
    return _SCMitem(name='Navigate to:',
                    typeItem=ItemTypes.get(MENU), toolTip='Show this position in the selected strip ',
                    stripMethodName='navigateCursorMenu',
                    callback=None)


def _navigateToPeakPosItem(menuId):
    return _SCMitem(name='Navigate to:',
                    typeItem=ItemTypes.get(MENU), toolTip='Show current.peak.position in the selected strip ',
                    stripMethodName=f'navigateToPeakMenu{menuId}',
                    callback=None)


def _customiseMenuItem(strip):
    return _SCMitem(name='Customise:',
                    typeItem=ItemTypes.get(MENU), toolTip='Change visible settings for the spectrumDisplay ',
                    stripMethodName='_customiseMenu',
                    callback=None)


def _copyAxesMenuItem(strip):
    return _SCMitem(name='Copy Axes:',
                    typeItem=ItemTypes.get(MENU), toolTip='Copy selected axis ranges from selected strip to this strip ',
                    stripMethodName='_copyAxesMenu',
                    callback=None)


def _selectedPeaksMenuItem(strip):
    return _SCMitem(name='Selected Peaks:',
                    typeItem=ItemTypes.get(MENU), toolTip='Actions availalbe on the currently selected peaks ',
                    stripMethodName='_selectedPeaksMenu',
                    callback=None)


def _flipAxesMenuItem(strip):
    return _SCMitem(name='New spectrumDisplay from strip:',
                    typeItem=ItemTypes.get(MENU), toolTip='Create new spectrumDisplay from current strip with flipped axes ',
                    stripMethodName='_flipAxesMenu',
                    callback=None)


# mark positions
def _markCursorPosItem(strip):
    return _SCMitem(name='Mark in:',
                    typeItem=ItemTypes.get(MENU), toolTip='Mark this position in the selected strip ',
                    stripMethodName='markInCursorMenu',
                    callback=None)


def _markPeakPosItem(strip):
    return _SCMitem(name='Mark in:',
                    typeItem=ItemTypes.get(MENU), toolTip='Mark positions of selected peaks',
                    stripMethodName='markInPeakMenu',
                    callback=None)


def _markPeaksItem():
    from ccpn.framework.Framework import getApplication

    _app = getApplication()
    return _SCMitem(name='Mark Peak(s)',
                    typeItem=ItemTypes.get(ITEM), toolTip='Mark positions of selected peaks',
                    callback=_app.mainWindow.markSelectedPeaks, shortcut='PM')


def _markMultipletsItem():
    from ccpn.framework.Framework import getApplication

    _app = getApplication()
    return _SCMitem(name='Mark Multiplet(s)',
                    typeItem=ItemTypes.get(ITEM), toolTip='Mark positions of selected multiplets',
                    callback=_app.mainWindow.markSelectedMultiplets, shortcut='UM')


def _markAxesItem(strip):
    return _SCMitem(name='Mark Axes:',
                    typeItem=ItemTypes.get(MENU), toolTip='Mark axisCodes ',
                    stripMethodName='markAxesMenu',
                    callback=None)


def _markAxesItem2(strip):
    return _SCMitem(name='Mark Axes:',
                    typeItem=ItemTypes.get(MENU), toolTip='Mark axisCodes ',
                    stripMethodName='markAxesMenu2',
                    callback=None)


def _markCursorXPosItem(strip):
    return _SCMitem(name='Mark %s' % strip.axisCodes[0],
                    typeItem=ItemTypes.get(ITEM), toolTip='Mark %s axiscode' % strip.axisCodes[0],
                    callback=partial(strip.markAxisIndices, indices=(0,)))


def _markCursorYPosItem(strip):
    return _SCMitem(name='Mark %s' % strip.axisCodes[1],
                    typeItem=ItemTypes.get(ITEM), toolTip='Mark %s axiscode' % strip.axisCodes[1],
                    callback=partial(strip.markAxisIndices, indices=(1,)))


def _markPeakXYPosItem(strip):
    return _SCMitem(name='Mark Selected Peaks:',
                    typeItem=ItemTypes.get(MENU), toolTip='Mark selected peaks ',
                    stripMethodName='markXYInPeakMenu',
                    callback=None)


# axis items for the main view
def _copyXAxisRangeFromStripItem(strip):
    return _SCMitem(name='Copy X Axis Range From:',
                    typeItem=ItemTypes.get(MENU), toolTip='Copy X axis range from selected strip',
                    stripMethodName='copyXAxisFromMenu',
                    callback=None)


def _copyYAxisRangeFromStripItem(strip):
    return _SCMitem(name='Copy Y Axis Range From:',
                    typeItem=ItemTypes.get(MENU), toolTip='Copy Y axis range from selected strip',
                    stripMethodName='copyYAxisFromMenu',
                    callback=None)


def _copyAllAxisRangeFromStripItem(strip):
    return _SCMitem(name='Copy X/Y Axis Ranges From:',
                    typeItem=ItemTypes.get(MENU), toolTip='Copy X and Y axis range from selected strip',
                    stripMethodName='copyAllAxisFromMenu',
                    callback=None)


def _copyXAxisCodeRangeFromStripItem(strip):
    return _SCMitem(name='Copy Axis Range to %s from:' % strip.axisCodes[0],
                    typeItem=ItemTypes.get(MENU), toolTip='Copy axis range to %s from selected strip' % strip.axisCodes[0],
                    stripMethodName='matchXAxisCodeToMenu',
                    callback=None)


def _copyYAxisCodeRangeFromStripItem(strip):
    return _SCMitem(name='Copy Axis Range to %s from:' % strip.axisCodes[1],
                    typeItem=ItemTypes.get(MENU), toolTip='Copy axis range to %s from selected strip' % strip.axisCodes[1],
                    stripMethodName='matchYAxisCodeToMenu',
                    callback=None)


# axis items for the axis and corner menues
def _copyXAxisRangeFromStripItem2(strip):
    """Separate item needed for the new axis menu
    """
    return _SCMitem(name='Copy X Axis Range From:',
                    typeItem=ItemTypes.get(MENU), toolTip='Copy X axis range from selected strip',
                    stripMethodName='copyXAxisFromMenu2',
                    callback=None)


def _copyYAxisRangeFromStripItem2(strip):
    """Separate item needed for the new axis menu
    """
    return _SCMitem(name='Copy Y Axis Range From:',
                    typeItem=ItemTypes.get(MENU), toolTip='Copy Y axis range from selected strip',
                    stripMethodName='copyYAxisFromMenu2',
                    callback=None)


def _copyAllAxisRangeFromStripItem2(strip):
    return _SCMitem(name='Copy X/Y Axis Ranges From:',
                    typeItem=ItemTypes.get(MENU), toolTip='Copy X and Y axis range from selected strip',
                    stripMethodName='copyAllAxisFromMenu2',
                    callback=None)


def _copyXAxisCodeRangeFromStripItem2(strip):
    return _SCMitem(name='Copy Axis Range to %s from:' % strip.axisCodes[0],
                    typeItem=ItemTypes.get(MENU), toolTip='Copy axis range to %s from selected strip' % strip.axisCodes[0],
                    stripMethodName='matchXAxisCodeToMenu2',
                    callback=None)


def _copyYAxisCodeRangeFromStripItem2(strip):
    return _SCMitem(name='Copy Axis Range to %s from:' % strip.axisCodes[1],
                    typeItem=ItemTypes.get(MENU), toolTip='Copy axis range to %s from selected strip' % strip.axisCodes[1],
                    stripMethodName='matchYAxisCodeToMenu2',
                    callback=None)


def _showSpectraOnPhasingItem(strip):
    return _SCMitem(name='Show Spectra on Phasing',
                    typeItem=ItemTypes.get(ITEM), toolTip='Show Spectra while phasing traces are visible',
                    checkable=True, checked=strip.showSpectraOnPhasing, shortcut='CH',
                    callback=strip._toggleShowSpectraOnPhasing, stripMethodName='spectraOnPhasingAction')


def _showActivePhaseTraceItem(strip):
    return _SCMitem(name='Show Active Phasing Trace',
                    typeItem=ItemTypes.get(ITEM), toolTip='Show active phasing trace under cursor',
                    checkable=True, checked=strip.showActivePhaseTrace, shortcut='AT',
                    callback=strip._toggleShowActivePhaseTrace, stripMethodName='activePhaseTraceAction')


# def _propagateAssignmentItem(strip):
#     # Not implemented
#     return


def _setEnabledAllItems(menu, state):
    for action in menu.actions():
        action.setEnabled(state)


def _hidePeaksSingleActionItems(menu):
    """ Greys out items that should appear only if one single peak is selected"""
    hideItems = [
        # _editPeakAssignmentItem(strip).name if _editPeakAssignmentItem(strip) else None,
        _integrate1DItem().name if _integrate1DItem() else None
        ]
    hideItems = [itm for itm in hideItems if itm is not None]

    for action in menu.actions():
        for item in hideItems:
            if action.text() == item:
                action.setEnabled(False)


##############################  Common Phasing  menu items ##############################
## These items are used to create both 1D and Nd Phasing menus

def _addTraceItem(strip):
    return _SCMitem(name='Add Trace',
                    typeItem=ItemTypes.get(ITEM), toolTip='Add new trace',
                    shortcut='TA', callback=strip._newPhasingTrace)


def _removeAllTracesItem(strip):
    return _SCMitem(name='Remove All Traces',
                    typeItem=ItemTypes.get(ITEM), toolTip='Remove all traces',
                    shortcut='TR', callback=strip.removePhasingTraces)


def _increaseTraceScaleItem(strip):
    return _SCMitem(name='Increase Trace Scale',
                    typeItem=ItemTypes.get(ITEM), toolTip='Increase Trace Scale',
                    shortcut='TU', icon='icons/tracescale-up', callback=strip.spectrumDisplay.increaseTraceScale)


def _decreaseTraceScaleItem(strip):
    return _SCMitem(name='Decrease Trace Scale',
                    typeItem=ItemTypes.get(ITEM), toolTip='Decrease Trace Scale',
                    shortcut='TD', icon='icons/tracescale-down', callback=strip.spectrumDisplay.decreaseTraceScale)


def _setPivotItem(strip):
    return _SCMitem(name='Set Pivot',
                    typeItem=ItemTypes.get(ITEM), toolTip='Set pivot value',
                    shortcut='PV', callback=strip._setPhasingPivot)


def _exitPhasingConsoleItem(strip):
    return _SCMitem(name='Exit Phasing Console',
                    typeItem=ItemTypes.get(ITEM), toolTip='Exit phasing console',
                    shortcut='PC', callback=strip.spectrumDisplay.togglePhaseConsole, icon='icons/phase-console', )


def _stackSpectraDefaultItem(strip):
    return _SCMitem(name='Stack Spectra',
                    typeItem=ItemTypes.get(ITEM), toolTip='Stack Spectra',
                    checkable=True, checked=strip._CcpnGLWidget._stackingMode,
                    callback=strip._toggleStack, shortcut='SK', stripMethodName='stackAction')


def _stackSpectraPhaseItem(strip):
    return _SCMitem(name='Stack Spectra',
                    typeItem=ItemTypes.get(ITEM), toolTip='Stack Spectra',
                    checkable=True, checked=strip._CcpnGLWidget._stackingMode,
                    callback=strip._toggleStackPhase, stripMethodName='stackActionPhase')


########################################################################################################################
#########################################      1D menus     ############################################################
########################################################################################################################


def _get1dDefaultMenu(guiStrip1d) -> Menu:
    """
    Creates and returns the 1d default context menu. Opened when right clicked on the background canvas
    """
    items = [
        _customiseMenuItem(guiStrip1d),
        _separator(),

        _coloursItem(guiStrip1d),
        _calibrateX(guiStrip1d),
        _calibrateY(guiStrip1d),
        _stackSpectraDefaultItem(guiStrip1d),
        _phasingConsoleItem(guiStrip1d),
        _separator(),

        _marksItem(guiStrip1d),
        _markAxesItem(guiStrip1d),
        _clearMarksItem(guiStrip1d),
        _separator(),

        _navigateToCursorPosItem(guiStrip1d),
        _copyAxesMenuItem(guiStrip1d),
        _separator(),

        _estimateNoise(guiStrip1d),
        _selectedPeaksMenuItem(guiStrip1d),
        _separator(),
        _printItem(guiStrip1d),
        ]
    items = [itm for itm in items if itm is not None]
    menu = _createMenu(guiStrip1d, items)

    # customise submenu - add to Strip._customiseMenu
    items = [
        _toolBarItem(guiStrip1d),
        _spectrumToolBarItem(guiStrip1d),
        _crosshairItem(guiStrip1d),
        _gridItem(guiStrip1d),
        _cyclePeakLabelsItem(guiStrip1d),
        ]
    items = [itm for itm in items if itm is not None]
    # attach to the _customiseMenu submenu
    _addMenuItems(guiStrip1d, guiStrip1d._customiseMenu, items)

    # copy axes submenu - add to Strip._copyAxesMenu
    items = [
        _copyAllAxisRangeFromStripItem(guiStrip1d),
        _copyXAxisRangeFromStripItem(guiStrip1d),
        _copyYAxisRangeFromStripItem(guiStrip1d),
        ]
    items = [itm for itm in items if itm is not None]
    # attach to the _copyAxesMenu submenu
    _addMenuItems(guiStrip1d, guiStrip1d._copyAxesMenu, items)

    # _selectedPeaksMenu submenu - add to Strip._selectedPeaksMenu
    items = _getNdPeakMenuItems(menuId='Main')
    # attach to the _selectedPeaksMenu submenu
    _addMenuItems(guiStrip1d, guiStrip1d._selectedPeaksMenu, items)

    return menu


def _get1dPhasingMenu(guiStrip1d) -> Menu:
    """
    Creates and returns the phasing 1d context menu. Opened when right clicked on the background canvas in "phasing State mode"
    """
    items = [
        _addTraceItem(guiStrip1d),
        _removeAllTracesItem(guiStrip1d),
        _setPivotItem(guiStrip1d),
        _showSpectraOnPhasingItem(guiStrip1d),
        _stackSpectraPhaseItem(guiStrip1d),
        _separator(),
        _exitPhasingConsoleItem(guiStrip1d),
        _separator(),
        _printItem(guiStrip1d),
        ]
    items = [itm for itm in items if itm is not None]
    return _createMenu(guiStrip1d, items)


def _get1dPeakMenuItems(menuId) -> list:
    items = [
        _deletePeakItem(),
        _copyPeakItem(),
        _editPeakAssignmentItem(),
        _deassignPeaksItem(),
        _setPeakAliasingItem(),
        _calibrateFromPeaks(),
        _separator(),

        _refitPeakItem(),
        _refitPeakGroupItem(),
        _recalculatePeakHeightsItem(),
        _snapToExtremaItem(),
        _estimateVolumesItem(),
        _separator(),

        _newMultipletItem(),
        _integrate1DItem(),
        _separator(),

        _navigateToPeakPosItem(menuId),
        _markPeaksItem()
        ]
    return [itm for itm in items if itm is not None]


def _get1dPeakMenu(guiStrip1d) -> Menu:
    """
    Creates and returns the current peak 1d context menu. Opened when right clicked on selected peak/s
    """
    items = _get1dPeakMenuItems(menuId='Selected')
    return _createMenu(guiStrip1d, items)


def _get1dIntegralMenu(guiStrip1d) -> Menu:
    """
    Creates and returns the current integral 1d context menu. Opened when right clicked on selected integral/s
    """
    items = [
        _deleteIntegralItem(guiStrip1d),
        ]
    items = [itm for itm in items if itm is not None]
    return _createMenu(guiStrip1d, items)


def _get1dMultipletMenu(guiStrip1d) -> Menu:
    """
    Creates and returns the current multiplet 1d context menu. Opened when right clicked on selected multiplet/s
    """
    items = [
        _deleteMultipletItem(guiStrip1d),
        _separator(),
        _markMultipletsItem(),
        ]
    items = [itm for itm in items if itm is not None]
    return _createMenu(guiStrip1d, items)


def _get1dAxisMenu(guiStrip) -> Menu:
    """
    Creates and returns the current Axis context menu. Opened when right clicked on axis
    """
    items = [
        # _copyAllAxisRangeFromStripItem2(guiStrip),
        # _copyXAxisRangeFromStripItem2(guiStrip),
        # _copyYAxisRangeFromStripItem2(guiStrip),
        ]
    items = [itm for itm in items if itm is not None]
    return _createMenu(guiStrip, items)


########################################################################################################################
#########################################      Nd Menus     ############################################################
########################################################################################################################


def _getNdDefaultMenu(guiStripNd) -> Menu:
    """
    Creates and returns the Nd default context menu. Opened when right clicked on the background canvas.
    """
    items = [
        _customiseMenuItem(guiStripNd),
        _separator(),

        _contoursItem(guiStripNd),
        _calibrateXY(guiStripNd),
        _toggleHorizontalTraceItem(guiStripNd),
        _toggleVerticalTraceItem(guiStripNd),
        _phasingConsoleItem(guiStripNd),
        _separator(),

        _marksItem(guiStripNd),
        _markAxesItem(guiStripNd),
        _clearMarksItem(guiStripNd),
        _separator(),

        _navigateToCursorPosItem(guiStripNd),
        _copyAxesMenuItem(guiStripNd),
        _flipAxesMenuItem(guiStripNd),
        _separator(),

        _estimateNoise(guiStripNd),
        _makeStripPlot(guiStripNd),
        _selectedPeaksMenuItem(guiStripNd),
        _separator(),

        _printItem(guiStripNd),
        ]
    items = [itm for itm in items if itm is not None]
    menu = _createMenu(guiStripNd, items)

    # customise submenu - add to Strip._customiseMenu
    items = [
        _toolBarItem(guiStripNd),
        _spectrumToolBarItem(guiStripNd),
        _crosshairItem(guiStripNd),
        _doubleCrosshairItem(guiStripNd),
        _gridItem(guiStripNd),
        _sideBandsItem(guiStripNd),
        _shareYAxisItem(guiStripNd),
        _cyclePeakLabelsItem(guiStripNd),
        _cyclePeakSymbolsItem(guiStripNd),
        ]
    items = [itm for itm in items if itm is not None]
    # attach to the _customiseMenu submenu
    _addMenuItems(guiStripNd, guiStripNd._customiseMenu, items)

    # copy axes submenu - add to Strip._copyAxesMenu
    items = [
        _copyAllAxisRangeFromStripItem(guiStripNd),
        _copyXAxisRangeFromStripItem(guiStripNd),
        _copyYAxisRangeFromStripItem(guiStripNd),
        _copyXAxisCodeRangeFromStripItem(guiStripNd),
        _copyYAxisCodeRangeFromStripItem(guiStripNd),
        ]
    items = [itm for itm in items if itm is not None]
    # attach to the _copyAxesMenu submenu
    _addMenuItems(guiStripNd, guiStripNd._copyAxesMenu, items)

    # _flipAxesMenu submenu - add to Strip._flipAxesMenu
    items = [
        _newStripPlotItem(guiStripNd),
        _newStripPlotXYItem(guiStripNd),
        _newStripPlotXZItem(guiStripNd),
        _newStripPlotYZItem(guiStripNd),
        _newStripPlotFAItem(guiStripNd),
        ]
    items = [itm for itm in items if itm is not None]
    # attach to the _flipAxesMenu submenu
    _addMenuItems(guiStripNd, guiStripNd._flipAxesMenu, items)

    # _selectedPeaksMenu submenu - add to Strip._selectedPeaksMenu
    items = _getNdPeakMenuItems(menuId='Main')
    # attach to the _selectedPeaksMenu submenu
    _addMenuItems(guiStripNd, guiStripNd._selectedPeaksMenu, items)

    return menu


def _getNdPhasingMenu(guiStripNd) -> Menu:
    """
    Creates and returns the phasing Nd context menu.  Opened when right clicked on the background canvas in "phasing State mode"
    """
    items = [
        _addTraceItem(guiStripNd),
        _removeAllTracesItem(guiStripNd),
        _increaseTraceScaleItem(guiStripNd),
        _decreaseTraceScaleItem(guiStripNd),
        _setPivotItem(guiStripNd),
        _showActivePhaseTraceItem(guiStripNd),
        _separator(),
        _exitPhasingConsoleItem(guiStripNd),
        _separator(),
        _printItem(guiStripNd),
        ]
    items = [itm for itm in items if itm is not None]
    return _createMenu(guiStripNd, items)


def _getNdPeakMenuItems(menuId) -> list:
    items = [
        _deletePeakItem(),
        _copyPeakItem(),
        _editPeakAssignmentItem(),
        _deassignPeaksItem(),
        _setPeakAliasingItem(),
        _separator(),

        _refitPeakItem(),
        _refitPeakGroupItem(),
        _recalculatePeakHeightsItem(),
        _snapToExtremaItem(),
        _estimateVolumesItem(),
        _reorderPeakListAxesItem(),
        _separator(),

        _makeStripPlotItem(),
        _calibrateFromPeaks(),
        _separator(),

        _newMultipletItem(),
        _separator(),

        _navigateToPeakPosItem(menuId),
        _markPeaksItem(),
        ]
    return [itm for itm in items if itm is not None]


def _getNdPeakMenu(guiStripNd) -> Menu:
    """
    Creates and returns the current peak Nd context menu. Opened when right clicked on selected peak/s
    """
    items = _getNdPeakMenuItems(menuId='Selected')
    return _createMenu(guiStripNd, items)


def _getNdIntegralMenu(guiStripNd) -> Menu:
    """
    Creates and returns the current integral Nd context menu. Opened when right clicked on selected integral/s
    """
    items = [
        _deleteIntegralItem(guiStripNd),
        ]
    items = [itm for itm in items if itm is not None]
    return _createMenu(guiStripNd, items)


def _getNdMultipletMenu(guiStripNd) -> Menu:
    """
    Creates and returns the current multiplet Nd context menu. Opened when right clicked on selected multiplet/s
    """
    items = [
        _deleteMultipletItem(guiStripNd),
        _separator(),
        _markMultipletsItem(),
        ]
    items = [itm for itm in items if itm is not None]
    return _createMenu(guiStripNd, items)


def _getNdAxisMenu(guiStripNd) -> Menu:
    """
    Creates and returns the current Axis context menu. Opened when right clicked on axis
    """
    items = [
        # _copyAllAxisRangeFromStripItem2(guiStrip),
        # _copyXAxisRangeFromStripItem2(guiStrip),
        # _copyYAxisRangeFromStripItem2(guiStrip),
        # _copyXAxisCodeRangeFromStripItem2(guiStrip),
        # _copyYAxisCodeRangeFromStripItem2(guiStrip),
        ]
    items = [itm for itm in items if itm is not None]
    return _createMenu(guiStripNd, items)


def _getSpectrumDisplayMenu(guiStripNd) -> Menu:
    """
    Creates and returns the current spectrumDisplay menu. Opened when right clicked on axis
    """
    items = []
    items = [itm for itm in items if itm is not None]
    newMenu = _createMenu(guiStripNd, items)
    # setting visible=False works, but need an icon to set the checkbox correctly (Qt bug?)
    # hideItems = ['TestCheckIcon']
    # for action in newMenu.actions():
    #     if action.text() in hideItems:
    #         action.setVisible(False)
    return newMenu


from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs import MAINVIEW, BOTTOMAXIS, RIGHTAXIS, AXISCORNER


def _addCopyMenuItems(guiStrip, viewPort, thisMenu, is1D):
    items = copyAttribs = matchAttribs = ()
    if viewPort in (MAINVIEW, AXISCORNER):
        items = (_copyAllAxisRangeFromStripItem2(guiStrip),
                 _copyXAxisRangeFromStripItem2(guiStrip),
                 _copyYAxisRangeFromStripItem2(guiStrip),)
        if not is1D:
            items = items + (_copyXAxisCodeRangeFromStripItem2(guiStrip),
                             _copyYAxisCodeRangeFromStripItem2(guiStrip),
                             )
        items = items + (_separator(),)

    elif viewPort == BOTTOMAXIS:
        items = (_copyAllAxisRangeFromStripItem2(guiStrip),
                 _copyXAxisRangeFromStripItem2(guiStrip),)
        if not is1D:
            items = items + (_copyXAxisCodeRangeFromStripItem2(guiStrip),
                             )
        items = items + (_separator(),)
    elif viewPort == RIGHTAXIS:
        items = (_copyAllAxisRangeFromStripItem2(guiStrip),
                 _copyYAxisRangeFromStripItem2(guiStrip),)
        if not is1D:
            items = items + (_copyYAxisCodeRangeFromStripItem2(guiStrip),
                             )
        items = items + (_separator(),)

    _addMenuItems(guiStrip, thisMenu, items)

    if viewPort in (MAINVIEW, AXISCORNER):
        copyAttribs = ((guiStrip.copyAllAxisFromMenu2, 'All'),
                       (guiStrip.copyXAxisFromMenu2, 'X'),
                       (guiStrip.copyYAxisFromMenu2, 'Y'),
                       )
        matchAttribs = ((guiStrip.matchXAxisCodeToMenu2, 0),
                        (guiStrip.matchYAxisCodeToMenu2, 1),
                        ) if not is1D else ()
    elif viewPort == BOTTOMAXIS:
        copyAttribs = ((guiStrip.copyAllAxisFromMenu2, 'All'),
                       (guiStrip.copyXAxisFromMenu2, 'X'),
                       )
        matchAttribs = ((guiStrip.matchXAxisCodeToMenu2, 0),
                        ) if not is1D else ()
    elif viewPort == RIGHTAXIS:
        copyAttribs = ((guiStrip.copyAllAxisFromMenu2, 'All'),
                       (guiStrip.copyYAxisFromMenu2, 'Y'),
                       )
        matchAttribs = ((guiStrip.matchYAxisCodeToMenu2, 1),
                        ) if not is1D else ()

    return copyAttribs, matchAttribs
