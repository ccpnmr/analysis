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
__modifiedBy__ = "$modifiedBy: Author: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:44 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================



from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.Menu import Menu


class MenuItemType:
    menu, item, actn, sep = range(1, 5)

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

class _StripCMenuItem(object):

    __dict__ = {'name':'','icon':None,'tooltip':'','shortcut':None,
                'checkable':False,'checked':False,'callback':None,'stripMethodName':''}

    def __init__(self, typeItem, **kwargs):
        '''
        :param typeItem: any value of ItemTypes: (menu,item,action,separator)
        :param kwargs: needed  any of __dict__: name, icon, tooltip, shortcut, checkable, checked, callback, stripMethodName
        for creating a new action/item. Not necessary for Separator and Menu type
        '''

        self.__dict__.update(kwargs)
        for k,v in  self.__dict__.items():
            setattr(self, k,v)
        self.typeItem = typeItem

def _createMenu(strip, items):

    strip._spectrumUtilActions = {}
    menu = strip.contextMenu = Menu('', strip, isFloatWidget=True)  # generate new menu
    for i in items:
        method = getattr(menu, i.typeItem)
        if method:
            action = method(i.name, **vars(i))
            setattr(strip, i.stripMethodName, action)
            strip._spectrumUtilActions[i.name] = action

    return menu

def _exampleMenu(strip):

    items = [
        _StripCMenuItem(ItemTypes.get(ACTION),
                        name='toggleGrid', icon=None,
                        callback=strip.toggleGrid,)
          ]
    return _createMenu(strip, items)





def _createContextMenu(strip, menuItems) -> Menu:

    """
    :param strip: 1D or nD GuiStrip Object
    :param menuItems:  a list of menuItem :
                        [   type,
                            action name,
                            icon,
                            tooltip/name,
                            shortcut,
                            active,
                            checked,
                            callback,
                            method
                        ]
    E.g. (MenuItemType.actn, 'Add Trace', None, 'Add new trace', 'PT', True,True, strip._newPhasingTrace,''),

    :return: Creates and returns a context menu for the guistrip
    """

    strip._spectrumUtilActions = {}
    strip.contextMenu = Menu('', strip, isFloatWidget=True)  # generate new menu

    for aType, aName, icon, tooltip, shortcut, active, checked, callback, attrib in menuItems:  # build the menu items/actions
        def tempMethod():
            return

        if aType == MenuItemType.menu:
            action = strip.contextMenu.addMenu(aName)
            tempMethod.__doc__ = ''
            tempMethod.__name__ = attrib
            setattr(strip.contextMenu, tempMethod.__name__, action)  # add to the menu

        elif aType == MenuItemType.item:
            action = strip.contextMenu.addItem(aName, callback=callback, checkable=active, checked=checked)
            tempMethod.__doc__ = ''
            tempMethod.__name__ = attrib
            setattr(strip, tempMethod.__name__, action)
            # add to strip

        elif aType == MenuItemType.actn:
            action = strip.contextMenu.addItem(aName, callback=callback, shortcut=shortcut)
            if icon is not None:
                ic = Icon(icon)
                action.setIcon(ic)
            strip._spectrumUtilActions[aName] = action

        elif aType == MenuItemType.sep:
            strip.contextMenu.addSeparator()

    return strip.contextMenu





##############################  1D menus ##############################




def _get1dDefaultMenu(guiStrip1d) -> Menu:
    """
    Creates and returns the 1d default context menu
    """


    menuItems = [
        (MenuItemType.item, 'ToolBar',               'toolbarAction',          '',                         'TB', True, True, guiStrip1d.spectrumDisplay.toggleToolbar, 'toolbarAction'),
        (MenuItemType.item, 'Grid',                  'gridAction',             '',                         'GS', True, True, guiStrip1d.spectrumDisplay.toggleGrid, 'gridAction'),
        (MenuItemType.actn, 'Cycle Peak Labels', 'icons/preferences-desktop-font', 'Cycle Peak Labelling Types', 'PL', True, True, guiStrip1d.cyclePeakLabelling, ''),

        (MenuItemType.sep, None, None, None, None, None, None, None, None),
        (MenuItemType.actn, 'Colours...',        'icons/contour-pos-neg'   ,      None,            '', True, True, guiStrip1d.spectrumDisplay.adjustContours, ''),

        (MenuItemType.actn, 'Zoom best fit',     'icons/zoom-best-fit-1d',    'Auto Scale',               '', None, None, guiStrip1d.resetYZoom, ''),
        (MenuItemType.actn, 'Zoom full',         'icons/zoom-full-1d',        'Auto Scale',               '', None, None, guiStrip1d.resetXZoom, ''),

        (MenuItemType.sep, None, None, None, None, None, None, None, None),
        (MenuItemType.actn, 'Calibrate X', None, 'calibrate X points ', None, True, False, guiStrip1d._toggleCalibrateXSpectrum, ''),
        (MenuItemType.actn, 'Calibrate Y', None, 'calibrate y points ', None, True, False, guiStrip1d._toggleCalibrateYSpectrum, ''),
        (MenuItemType.actn, 'Stack Spectra', None, 'Stack Spectra ', None, True, False,  guiStrip1d.toggleStack, ''),

        (MenuItemType.sep, None, None, None, None, None, None, None, None),
        (MenuItemType.actn, 'Enter Phasing Console',  'icons/phase-console',    'Enter Phasing Console',    'PC', True, True, guiStrip1d.spectrumDisplay.togglePhaseConsole, ''),

        (MenuItemType.sep, None, None, None, None, None, None, None, None),
        (MenuItemType.actn, 'Clear Marks', None,                     'Clear all mark',          'MC', True, False, guiStrip1d.clearMarks, ''),

        (MenuItemType.sep, None, None, None, None, None, None, None, None),
        (MenuItemType.actn, 'Print to File...',      'icons/print',            'Print Spectrum Display to File', 'PT', True, True, guiStrip1d.showExportDialog, ''),
    ]

    return _createContextMenu(guiStrip1d, menuItems)


def _get1dPhasingMenu(guiStrip1d) -> Menu:
    """
    Creates and returns the phasing 1d context menu
    """

    menuItems = [
                (MenuItemType.actn, 'Add Trace',               None,                     'Add new trace',          'PT',   True,   True,       guiStrip1d._newPhasingTrace, ''),
                (MenuItemType.actn, 'Remove All Traces',       None,                     'Remove all traces',      'TR',   True,   True,       guiStrip1d.removePhasingTraces,''),
                (MenuItemType.actn, 'Set Pivot',               None,                     'Set pivot value',        'PV',   True,   True,       guiStrip1d._setPhasingPivot,''),

                (MenuItemType.sep, None, None, None, None, None, None, None, None),
                (MenuItemType.actn, 'Exit Phasing Console',  'icons/phase-console',   'Exit phasing console',      'PC',   True,   True,       guiStrip1d.spectrumDisplay.togglePhaseConsole,    ''),
                ]

    return _createContextMenu(guiStrip1d, menuItems)



##############################  Nd menus ##############################





def _getNdDefaultMenu(guiStripNd) -> Menu:
    """
    Creates and returns the Nd default context menu
    """

    menuItems = [
      (MenuItemType.item, 'ToolBar',               'toolbarAction',          '',                         'TB',     True,   True,       guiStripNd.spectrumDisplay.toggleToolbar,   'toolbarAction'),
      (MenuItemType.item, 'Crosshair',             'crossHairAction',        '',                         'CH',     True,   True,       guiStripNd.spectrumDisplay.toggleCrossHair,                'crossHairAction'),
      (MenuItemType.item, 'Grid',                  'gridAction',             '',                         'GS',     True,   True,       guiStripNd.spectrumDisplay.toggleGrid,                      'gridAction'),
      (MenuItemType.item, 'Share Y Axis',          '',                       '',                         'TA',     True,   True,       guiStripNd._toggleLastAxisOnly, 'lastAxisOnlyCheckBox'),
      (MenuItemType.actn, 'Cycle Peak Labels', 'icons/preferences-desktop-font', 'Cycle Peak Labelling Types', 'PL', True,  True,      guiStripNd.cyclePeakLabelling, ''),
      (MenuItemType.actn, 'Cycle Peak Symbols', 'icons/peak-symbols', 'Cycle Peak Symbols',              'PS',     True,   True,       guiStripNd.cyclePeakSymbols, ''),

      (MenuItemType.sep, None, None, None, None, None, None, None, None),
      (MenuItemType.actn, 'Contours...',           'icons/contours',      'Contour Settings',            '',       True,   True,       guiStripNd.spectrumDisplay.adjustContours, ''),
      # (MenuItemType.actn, 'Add Contour Level',     'icons/contour-add',      'Add One Level',            True,   True,       guiStripNd.spectrumDisplay.addContourLevel, ''),
      # (MenuItemType.actn, 'Remove Contour Level',  'icons/contour-remove',   'Remove One Level',         True,   True,       guiStripNd.spectrumDisplay.removeContourLevel,''),
      # (MenuItemType.actn, 'Raise Base Level',      'icons/contour-base-up',  'Raise Contour Base Level', True,   True,       guiStripNd.spectrumDisplay.raiseContourBase,''),
      # (MenuItemType.actn, 'Lower Base Level',      'icons/contour-base-down','Lower Contour Base Level', True,   True,       guiStripNd.spectrumDisplay.lowerContourBase,''),
      # (MenuItemType.actn, 'Store Zoom',            'icons/zoom-store',       'Store Zoom',               True,   True,       guiStripNd.spectrumDisplay._storeZoom,      ''),
      # (MenuItemType.actn, 'Restore Zoom',          'icons/zoom-restore',     'Restore Zoom',             True,   True,       guiStripNd.spectrumDisplay._restoreZoom,    ''),
      (MenuItemType.actn, 'Reset Zoom',            'icons/zoom-full',        'Reset Zoom',               'ZR',   True,   True,       guiStripNd.resetZoom,                       ''),
      (MenuItemType.menu, 'Navigate To', '', '', 'NT', True, True, None, 'navigateToMenu'),

      (MenuItemType.sep, None, None, None, None, None, None, None, None),
      (MenuItemType.item, 'Horizontal Trace',       'hTraceAction',     'Toggle horizontal trace on/off', 'TH',   True,   False,      guiStripNd.toggleHorizontalTrace,                   'hTraceAction'),
      (MenuItemType.item, 'Vertical Trace',         'vTraceAction',     'Toggle vertical trace on/off',   'TV',   True,   False,      guiStripNd.toggleVerticalTrace,                   'vTraceAction'),
      (MenuItemType.actn, 'Enter Phasing Console',  'icons/phase-console',    'Enter Phasing Console',    'PC',   True,   True,       guiStripNd.spectrumDisplay.togglePhaseConsole, ''),

      (MenuItemType.sep, None, None, None, None, None, None, None, None),
      (MenuItemType.actn, 'Mark Positions',          None,                  'Mark positions of all axes', 'MK', True, False,        guiStripNd.createMark, ''),
      (MenuItemType.actn, 'Clear Marks',             None,                     'Clear all mark',          'MC', True, False,        guiStripNd.clearMarks, ''),

      (MenuItemType.sep, None, None, None, None, None, None, None, None),
      (MenuItemType.actn, 'Print to File...',      'icons/print',            'Print Spectrum Display to File', 'PT', True, True,   guiStripNd.showExportDialog, ''),
    ]

    return _createContextMenu(guiStripNd, menuItems)

def _getNdPhasingMenu(guiStripNd) -> Menu:
    """
    Creates and returns the phasing Nd context menu
    """

    menuItems = [
        (MenuItemType.actn, 'Add Trace',               None,                     'Add new trace',          'PT',   True,   True,       guiStripNd._newPhasingTrace,''),
        (MenuItemType.actn, 'Remove All Traces',       None,                     'Remove all traces',      'TR',   True,   True,       guiStripNd.spectrumDisplay.removePhasingTraces,''),
        (MenuItemType.actn, 'Set Pivot',               None,                     'Set pivot value',        'PV',   True,   True,       guiStripNd._setPhasingPivot,''),
        (MenuItemType.actn, 'Increase Trace Scale',    'icons/tracescale-up',  'Increase trace scale',     'TU',   True,   True,       guiStripNd.spectrumDisplay.increaseTraceScale,''),
        (MenuItemType.actn, 'Decrease Trace Scale',    'icons/tracescale-down','Decrease trace scale',     'TD',   True,   True,       guiStripNd.spectrumDisplay.decreaseTraceScale,      ''),

        (MenuItemType.sep, None, None, None, None, None, None, None, None),
        (MenuItemType.actn, 'Exit Phasing Console', 'icons/phase-console',                     'Exit phasing console',   'PC',   True,   True,       guiStripNd.spectrumDisplay.togglePhaseConsole,    ''),
    ]
    return _createContextMenu(guiStripNd, menuItems)



def _getPeakMenu(guiStrip) -> Menu:
    """
    Creates and returns the phasing Nd context menu

    """

    menuItems = [
        (MenuItemType.actn, 'Add to a new multiplet',  None,  'Add peak to multiplet',  'AM',   None,   None,       guiStrip.mainWindow.addMultiplet,''),
        (MenuItemType.actn, 'Show in Peak Table', None, 'Open Peak Table', None, None, None, None, ''),

        (MenuItemType.sep, None, None, None, None, None, None, None, None),
        (MenuItemType.actn, 'Delete peak/s', None, 'Delete Peak/s from project ',None, None, None, guiStrip.mainWindow.deleteSelectedPeaks,''),

        (MenuItemType.sep, None, None, None, None, None, None, None, None),
    ]
    return _createContextMenu(guiStrip, menuItems)