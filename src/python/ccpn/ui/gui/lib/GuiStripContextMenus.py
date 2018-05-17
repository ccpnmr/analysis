"""
A File containing all the context menus of a gui Strip
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
__modifiedBy__ = "$modifiedBy:  Luca Mureddu $"
__dateModified__ = "$dateModified: 2018-05-17 10:28:43 +0000 (Thu, May 17, 2018) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2018-05-17 10:28:43 +0000 (Thu, May 17, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================


from ccpn.ui.gui.widgets.Menu import Menu


MENU =      'Menu'
ITEM =      'Item'
ACTION =    'Action'
SEPARATOR = 'Separator'

ItemTypes =  {
             MENU:      Menu.addMenu.__name__,
             ITEM:      Menu.addItem.__name__,
             ACTION:    Menu.addItem.__name__,
             SEPARATOR: Menu._addSeparator.__name__
             }

class _SCMitem(object):
    '''Strip context menu item base class. Used to autogenerate the context menu items in a Gui strip '''
    def __init__(self, typeItem, **kwargs):
        '''
        :param typeItem: any value of ItemTypes: (menu,item,action,separator)
        :param kwargs: needed  any of _kwrgs: name, icon, tooltip, shortcut, checkable, checked, callback, stripMethodName
        for creating a new action/item. Not necessary for Separator and Menu type.
        Not a strict rule, but the only difference between ITEM and ACTION seems to be: Action has usually an icon.
        Item has a checkbox on the left side.
        '''
        self._kwrgs = {'name': '', 'icon': None, 'tooltip': '', 'shortcut': None, 'checkable': False,
                       'checked': False, 'callback': None, 'stripMethodName': ''}
        self._kwrgs.update(kwargs)
        for k,v in  self._kwrgs.items():
            setattr(self, k,v)
        self.typeItem = typeItem

def _createMenu(strip, items):
    """
    :param strip: 1D or nD GuiStrip Object
    :param items:  a list of _SCMitem obj :
    :return: Creates and returns a context menu for the guiStrip from a list of items
    """
    strip._spectrumUtilActions = {}
    menu = strip.contextMenu = Menu('', strip, isFloatWidget=True)  # generate new menu
    for i in items:
        method = getattr(menu, i.typeItem)
        if method:
            action = method(i.name, **vars(i))
            setattr(strip, i.stripMethodName, action)
            strip._spectrumUtilActions[i.name] = action

    return menu



##############################  1D menus ##############################




def _get1dDefaultMenu(guiStrip1d) -> Menu:
    """
    Creates and returns the 1d default context menu
    """
    items = [
            _SCMitem(name='ToolBar',
                        typeItem= ItemTypes.get(ITEM), toolTip='toolbarAction', callback=guiStrip1d.spectrumDisplay.toggleToolbar,
                        checkable=True, checked=True, shortcut='TB', stripMethodName='toolbarAction'),

            _SCMitem(name='Grid',
                        typeItem=ItemTypes.get(ITEM), toolTip='gridAction', callback=guiStrip1d.spectrumDisplay.toggleGrid,
                        checkable=True, checked=True, shortcut='GS', stripMethodName='gridAction'),

            _SCMitem(name='Cycle Peak Labels',
                         typeItem=ItemTypes.get(ACTION),  icon='icons/preferences-desktop-font', toolTip='Cycle Peak Labelling Types',
                         callback=guiStrip1d.cyclePeakLabelling,shortcut='PL', stripMethodName=''),

            _SCMitem(typeItem=ItemTypes.get(SEPARATOR)),

            _SCMitem(name='Colours...',
                        typeItem=ItemTypes.get(ACTION), icon='icons/contour-pos-neg', toolTip='Change colours',
                        callback=guiStrip1d.spectrumDisplay.adjustContours),

            _SCMitem(name='Zoom best Y fit',
                        typeItem=ItemTypes.get(ACTION), icon='icons/zoom-best-fit-1d', toolTip='Y Auto Scale',
                        callback=guiStrip1d.resetYZoom),

            _SCMitem(name='Zoom best X fit',
                        typeItem=ItemTypes.get(ACTION),  icon='icons/zoom-full-1d', toolTip='X Auto Scale',
                        callback=guiStrip1d.resetXZoom),

            _SCMitem(typeItem=ItemTypes.get(SEPARATOR)),

            _SCMitem(name='Calibrate X',
                        typeItem=ItemTypes.get(ACTION), toolTip='calibrate X points', callback=guiStrip1d._toggleCalibrateXSpectrum),

            _SCMitem(name='Calibrate Y',
                        typeItem=ItemTypes.get(ACTION),toolTip='calibrate Y points', callback=guiStrip1d._toggleCalibrateYSpectrum),

            _SCMitem(name='Stack Spectra',
                        typeItem=ItemTypes.get(ITEM), toolTip='Stack Spectra', checkable=True, checked=False,
                        callback=guiStrip1d.toggleStack, stripMethodName='stackAction'),

            _SCMitem(typeItem=ItemTypes.get(SEPARATOR)),

            _SCMitem(name='Enter Phasing Console',
                        typeItem=ItemTypes.get(ACTION),icon= 'icons/phase-console', toolTip='Enter Phasing Console',
                        shortcut='PC',callback=guiStrip1d.spectrumDisplay.togglePhaseConsole),

            _SCMitem(typeItem=ItemTypes.get(SEPARATOR)),

            _SCMitem(name='Clear Marks',
                        typeItem=ItemTypes.get(ACTION), toolTip='Clear all Marks from', shortcut='MC',
                        callback=guiStrip1d.clearMarks),

            _SCMitem(typeItem=ItemTypes.get(SEPARATOR)),

            _SCMitem(name='Print to File...',
                        typeItem=ItemTypes.get(ACTION), icon='icons/print', toolTip='Print Spectrum Display to File',
                        shortcut='PT', callback=guiStrip1d.showExportDialog),
                ]

    return _createMenu(guiStrip1d, items)


def _get1dPhasingMenu(guiStrip1d) -> Menu:
    """
    Creates and returns the phasing 1d context menu
    """

    # menuItems = [
    #             (MenuItemType.actn, 'Add Trace',               None,                     'Add new trace',          'PT',   True,   True,       guiStrip1d._newPhasingTrace, ''),
    #             (MenuItemType.actn, 'Remove All Traces',       None,                     'Remove all traces',      'TR',   True,   True,       guiStrip1d.removePhasingTraces,''),
    #             (MenuItemType.actn, 'Set Pivot',               None,                     'Set pivot value',        'PV',   True,   True,       guiStrip1d._setPhasingPivot,''),
    #
    #             (MenuItemType.sep, None, None, None, None, None, None, None, None),
    #             (MenuItemType.actn, 'Exit Phasing Console',  'icons/phase-console',   'Exit phasing console',      'PC',   True,   True,       guiStrip1d.spectrumDisplay.togglePhaseConsole,    ''),
    #             ]
    #
    # return _createContextMenu(guiStrip1d, menuItems)

    return _createMenu(guiStrip1d, [])

##############################  Nd menus ##############################





def _getNdDefaultMenu(guiStripNd) -> Menu:
    """
    Creates and returns the Nd default context menu
    """

    # menuItems = [
    #   (MenuItemType.item, 'ToolBar',               'toolbarAction',          '',                         'TB',     True,   True,       guiStripNd.spectrumDisplay.toggleToolbar,   'toolbarAction'),
    #   (MenuItemType.item, 'Crosshair',             'crossHairAction',        '',                         'CH',     True,   True,       guiStripNd.spectrumDisplay.toggleCrossHair,                'crossHairAction'),
    #   (MenuItemType.item, 'Grid',                  'gridAction',             '',                         'GS',     True,   True,       guiStripNd.spectrumDisplay.toggleGrid,                      'gridAction'),
    #   (MenuItemType.item, 'Share Y Axis',          '',                       '',                         'TA',     True,   True,       guiStripNd._toggleLastAxisOnly, 'lastAxisOnlyCheckBox'),
    #   (MenuItemType.actn, 'Cycle Peak Labels', 'icons/preferences-desktop-font', 'Cycle Peak Labelling Types', 'PL', True,  True,      guiStripNd.cyclePeakLabelling, ''),
    #   (MenuItemType.actn, 'Cycle Peak Symbols', 'icons/peak-symbols', 'Cycle Peak Symbols',              'PS',     True,   True,       guiStripNd.cyclePeakSymbols, ''),
    #
    #   (MenuItemType.sep, None, None, None, None, None, None, None, None),
    #   (MenuItemType.actn, 'Contours...',           'icons/contours',      'Contour Settings',            '',       True,   True,       guiStripNd.spectrumDisplay.adjustContours, ''),
    #   # (MenuItemType.actn, 'Add Contour Level',     'icons/contour-add',      'Add One Level',            True,   True,       guiStripNd.spectrumDisplay.addContourLevel, ''),
    #   # (MenuItemType.actn, 'Remove Contour Level',  'icons/contour-remove',   'Remove One Level',         True,   True,       guiStripNd.spectrumDisplay.removeContourLevel,''),
    #   # (MenuItemType.actn, 'Raise Base Level',      'icons/contour-base-up',  'Raise Contour Base Level', True,   True,       guiStripNd.spectrumDisplay.raiseContourBase,''),
    #   # (MenuItemType.actn, 'Lower Base Level',      'icons/contour-base-down','Lower Contour Base Level', True,   True,       guiStripNd.spectrumDisplay.lowerContourBase,''),
    #   # (MenuItemType.actn, 'Store Zoom',            'icons/zoom-store',       'Store Zoom',               True,   True,       guiStripNd.spectrumDisplay._storeZoom,      ''),
    #   # (MenuItemType.actn, 'Restore Zoom',          'icons/zoom-restore',     'Restore Zoom',             True,   True,       guiStripNd.spectrumDisplay._restoreZoom,    ''),
    #   (MenuItemType.actn, 'Reset Zoom',            'icons/zoom-full',        'Reset Zoom',               'ZR',   True,   True,       guiStripNd.resetZoom,                       ''),
    #   (MenuItemType.menu, 'Navigate To', '', '', 'NT', True, True, None, 'navigateToMenu'),
    #
    #   (MenuItemType.sep, None, None, None, None, None, None, None, None),
    #   (MenuItemType.item, 'Horizontal Trace',       'hTraceAction',     'Toggle horizontal trace on/off', 'TH',   True,   False,      guiStripNd.toggleHorizontalTrace,                   'hTraceAction'),
    #   (MenuItemType.item, 'Vertical Trace',         'vTraceAction',     'Toggle vertical trace on/off',   'TV',   True,   False,      guiStripNd.toggleVerticalTrace,                   'vTraceAction'),
    #   (MenuItemType.actn, 'Enter Phasing Console',  'icons/phase-console',    'Enter Phasing Console',    'PC',   True,   True,       guiStripNd.spectrumDisplay.togglePhaseConsole, ''),
    #
    #   (MenuItemType.sep, None, None, None, None, None, None, None, None),
    #   (MenuItemType.actn, 'Mark Positions',          None,                  'Mark positions of all axes', 'MK', True, False,        guiStripNd.createMark, ''),
    #   (MenuItemType.actn, 'Clear Marks',             None,                     'Clear all mark',          'MC', True, False,        guiStripNd.clearMarks, ''),
    #
    #   (MenuItemType.sep, None, None, None, None, None, None, None, None),
    #   (MenuItemType.actn, 'Print to File...',      'icons/print',            'Print Spectrum Display to File', 'PT', True, True,   guiStripNd.showExportDialog, ''),
    # ]
    #
    return _createMenu(guiStripNd, [])

def _getNdPhasingMenu(guiStripNd) -> Menu:
    """
    Creates and returns the phasing Nd context menu
    """

    # menuItems = [
    #     (MenuItemType.actn, 'Add Trace',               None,                     'Add new trace',          'PT',   True,   True,       guiStripNd._newPhasingTrace,''),
    #     (MenuItemType.actn, 'Remove All Traces',       None,                     'Remove all traces',      'TR',   True,   True,       guiStripNd.spectrumDisplay.removePhasingTraces,''),
    #     (MenuItemType.actn, 'Set Pivot',               None,                     'Set pivot value',        'PV',   True,   True,       guiStripNd._setPhasingPivot,''),
    #     (MenuItemType.actn, 'Increase Trace Scale',    'icons/tracescale-up',  'Increase trace scale',     'TU',   True,   True,       guiStripNd.spectrumDisplay.increaseTraceScale,''),
    #     (MenuItemType.actn, 'Decrease Trace Scale',    'icons/tracescale-down','Decrease trace scale',     'TD',   True,   True,       guiStripNd.spectrumDisplay.decreaseTraceScale,      ''),
    #
    #     (MenuItemType.sep, None, None, None, None, None, None, None, None),
    #     (MenuItemType.actn, 'Exit Phasing Console', 'icons/phase-console',                     'Exit phasing console',   'PC',   True,   True,       guiStripNd.spectrumDisplay.togglePhaseConsole,    ''),
    # ]
    # return _createContextMenu(guiStripNd, menuItems)
    return _createMenu(guiStripNd, [])


def _getPeakMenu(guiStrip) -> Menu:
    """
    Creates and returns the phasing Nd context menu

    """

    # menuItems = [
    #     (MenuItemType.actn, 'Add to a new multiplet',  None,  'Add peak to multiplet',  'AM',   None,   None,       guiStrip.mainWindow.addMultiplet,''),
    #     (MenuItemType.actn, 'Show in Peak Table', None, 'Open Peak Table', None, None, None, None, ''),
    #
    #     (MenuItemType.sep, None, None, None, None, None, None, None, None),
    #     (MenuItemType.actn, 'Delete peak/s', None, 'Delete Peak/s from project ',None, None, None, guiStrip.mainWindow.deleteSelectedPeaks,''),
    #
    #     (MenuItemType.sep, None, None, None, None, None, None, None, None),
    # ]
    # return _createContextMenu(guiStrip, menuItems)
    return _createMenu(guiStrip, [])