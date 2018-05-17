"""
A File containing all the context menus of a gui Strip.
To create a menu:
 - make a list of objs of type _SCMitem
 - call the function _createMenu, give the strip where the context menu will be needed and the list of items

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
SEPARATOR = 'Separator'

ItemTypes =  {
             MENU:      Menu.addMenu.__name__,
             ITEM:      Menu.addItem.__name__,
             SEPARATOR: Menu._addSeparator.__name__
             }

class _SCMitem(object):
    '''Strip context menu item base class. Used to autogenerate the context menu items in a Gui strip '''
    def __init__(self, typeItem, **kwargs):
        '''
        :param typeItem: any value of ItemTypes: (menu,item,separator)
        :param kwargs: needed  any of _kwrgs: name, icon, tooltip, shortcut, checkable, checked, callback, stripMethodName
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
        try:
            ff = getattr(menu, i.typeItem)
            if ff:
                action = ff(i.name, **vars(i))
                setattr(strip, i.stripMethodName, action)
                strip._spectrumUtilActions[i.name] = action
        except Exception as e:
            print(e, "menus")

    return menu


##############################  Common menu items ##############################


def _toolBarItem(strip):
    return _SCMitem(name='ToolBar',
                 typeItem=ItemTypes.get(ITEM), toolTip='toolbarAction',
                 callback=strip.spectrumDisplay.toggleToolbar,
                 checkable=True, checked=True, shortcut='TB', stripMethodName='toolbarAction')

def _crossHairItem(strip):
    return _SCMitem(name='Crosshair',
                     typeItem=ItemTypes.get(ITEM), toolTip='CrossHair Action',
                     checkable=True, checked=True, shortcut ='CH',
                     callback=strip.spectrumDisplay.toggleCrossHair)
def _gridItem(strip):
    return _SCMitem(name='Grid',
                 typeItem=ItemTypes.get(ITEM), toolTip='gridAction', callback=strip.spectrumDisplay.toggleGrid,
                 checkable=True, checked=True, shortcut='GS', stripMethodName='gridAction')

def _cyclePeakLabelsItem(strip):
    return _SCMitem(name='Cycle Peak Labels',
                 typeItem=ItemTypes.get(ITEM), icon='icons/preferences-desktop-font',
                 toolTip='Cycle Peak Labelling Types',
                 callback=strip.cyclePeakLabelling, shortcut='PL', stripMethodName='')

def _cyclePeakSymbolsItem(strip):
    return _SCMitem(name='Cycle Peak Symbols',
                    typeItem=ItemTypes.get(ITEM), icon='icons/peak-symbols',
                    toolTip='Cycle Peak Labelling Types',
                    callback=strip.cyclePeakSymbols, shortcut='PS', stripMethodName='')

def _shareYAxisItem(strip):
    return _SCMitem(name='Share Y Axis',
                        typeItem=ItemTypes.get(ITEM), toolTip='Share Y axis among strips',checkable=True, checked=True,
                        callback=strip._toggleLastAxisOnly,shortcut='TA', stripMethodName='lastAxisOnlyCheckBox')

def _contoursItem(strip):
    return _SCMitem(name='Contours...',
                        typeItem=ItemTypes.get(ITEM), icon='icons/contours', toolTip='Change Contour Settings',
                        callback=strip.spectrumDisplay.adjustContours)

def _resetZoom(strip):
    return _SCMitem(name='Reset Zoom',
             typeItem=ItemTypes.get(ITEM), icon='icons/zoom-full', toolTip='Reset Zoom',
             callback=strip.resetZoom)


def _navigateItem(strip):
    return _SCMitem(name='Navigate To',
                     typeItem=ItemTypes.get(MENU), toolTip='Navigate To ...',
                     shortcut='NT', stripMethodName='navigateToMenu',
                     callback=None)

def _toggleHorizontalTraceItem(strip):
    return _SCMitem(name='Horizontal Trace',
         typeItem=ItemTypes.get(ITEM), toolTip='Toggle horizontal trace on/off',
         checkable=True, checked=False, shortcut='TH', stripMethodName='hTraceAction',
         callback=strip.toggleHorizontalTrace)

def _toggleVerticalTraceItem(strip):
    return _SCMitem(name='Vertical Trace',
         typeItem=ItemTypes.get(ITEM), toolTip='Toggle vertical trace on/off',
         checkable=True, checked=False, shortcut='TV', stripMethodName='vTraceAction',
         callback=strip.toggleVerticalTrace)


def _phasingConsoleItem(strip):
    return _SCMitem(name='Enter Phasing Console',
                        typeItem=ItemTypes.get(ITEM),icon= 'icons/phase-console', toolTip='Enter Phasing Console',
                        shortcut='PC',callback=strip.spectrumDisplay.togglePhaseConsole)

def _marksItem(strip):
    return _SCMitem(name='Mark Positions',
            typeItem=ItemTypes.get(ITEM), toolTip='Mark positions of all axes', shortcut='MK',
            callback=strip.createMark)

def _clearMarksItem(strip):
    return _SCMitem(name='Clear Marks',
            typeItem=ItemTypes.get(ITEM), toolTip='Clear all Marks from', shortcut='MC',
            callback=strip.clearMarks)

def _printItem(strip):
    return _SCMitem(name='Print to File...',
            typeItem=ItemTypes.get(ITEM), icon='icons/print', toolTip='Print Spectrum Display to File',
            shortcut='PT', callback=strip.showExportDialog)
def _separator():
    return _SCMitem(typeItem=ItemTypes.get(SEPARATOR))

##############################  1D menus ##############################

def _get1dDefaultMenu(guiStrip1d) -> Menu:
    """
    Creates and returns the 1d default context menu
    """
    items = [
            _toolBarItem(guiStrip1d),
            _gridItem(guiStrip1d),
            _crossHairItem(guiStrip1d),
            _cyclePeakLabelsItem(guiStrip1d),
            _separator(),       
            _SCMitem(name='Colours...',
                        typeItem=ItemTypes.get(ITEM), icon='icons/contour-pos-neg', toolTip='Change colours',
                        callback=guiStrip1d.spectrumDisplay.adjustContours),

            _SCMitem(name='Zoom best Y fit',
                        typeItem=ItemTypes.get(ITEM), icon='icons/zoom-best-fit-1d', toolTip='Y Auto Scale',
                        callback=guiStrip1d.resetYZoom),

            _SCMitem(name='Zoom best X fit',
                        typeItem=ItemTypes.get(ITEM),  icon='icons/zoom-full-1d', toolTip='X Auto Scale',
                        callback=guiStrip1d.resetXZoom),
            _separator(),
            _SCMitem(name='Calibrate X',
                        typeItem=ItemTypes.get(ITEM), toolTip='calibrate X points', callback=guiStrip1d._toggleCalibrateXSpectrum),

            _SCMitem(name='Calibrate Y',
                        typeItem=ItemTypes.get(ITEM),toolTip='calibrate Y points', callback=guiStrip1d._toggleCalibrateYSpectrum),

            _SCMitem(name='Stack Spectra',
                        typeItem=ItemTypes.get(ITEM), toolTip='Stack Spectra', checkable=True, checked=False,
                        callback=guiStrip1d.toggleStack, stripMethodName='stackAction'),
            _separator(),
            _phasingConsoleItem(guiStrip1d),
            _separator(),
            _marksItem(guiStrip1d),
            _clearMarksItem(guiStrip1d),
            _separator(),
            _printItem(guiStrip1d),
            ]
    return _createMenu(guiStrip1d, items)

def _commonPhasingMenuItems(strip):

    items = [
            _SCMitem(name='Add Trace',
                         typeItem=ItemTypes.get(ITEM), toolTip='Add new trace',
                         shortcut='PT', callback=strip._newPhasingTrace),

            _SCMitem(name='Remove All Traces',
                         typeItem=ItemTypes.get(ITEM), toolTip='Remove all traces',
                         shortcut='TR', callback=strip.removePhasingTraces),

            _SCMitem(name='Increase Trace Scale',
                         typeItem=ItemTypes.get(ITEM), toolTip='Increase Trace Scale',
                         shortcut='TU',icon='icons/tracescale-up', callback=strip.spectrumDisplay.increaseTraceScale),

            _SCMitem(name='Decrease Trace Scale',
                         typeItem=ItemTypes.get(ITEM), toolTip='Decrease Trace Scale',
                         shortcut='TD', icon='icons/tracescale-down', callback=strip.spectrumDisplay.decreaseTraceScale),

            _SCMitem(name='Set Pivot',
                        typeItem=ItemTypes.get(ITEM), toolTip='Set pivot value', checkable=True, checked=True,
                        shortcut='PV', callback=strip._setPhasingPivot),

            _separator(),

            _SCMitem(name='Exit Phasing Console',
                     typeItem=ItemTypes.get(ITEM), toolTip='Exit phasing console', checkable=True, checked=True,
                     shortcut='PC', callback=strip.spectrumDisplay.togglePhaseConsole, icon='icons/phase-console', )
            ]

    return items

def _get1dPhasingMenu(guiStrip1d) -> Menu:
    """
    Creates and returns the phasing 1d context menu
    """
    items = _commonPhasingMenuItems(guiStrip1d)

    return _createMenu(guiStrip1d, items)


##############################  Nd menus ##############################


def _getNdDefaultMenu(guiStripNd) -> Menu:
    """
    Creates and returns the 1d default context menu
    """
    items = [
            _toolBarItem(guiStripNd),
            _crossHairItem(guiStripNd),
            _gridItem(guiStripNd),
            _shareYAxisItem(guiStripNd),
            _cyclePeakLabelsItem(guiStripNd),
            _cyclePeakSymbolsItem(guiStripNd),
            _separator(),
            _contoursItem(guiStripNd),
            _separator(),

            # _SCMitem(name='Add Contour Level',
            #          typeItem=ItemTypes.get(ITEM), icon='icons/contour-add', toolTip='Add One Level',
            #          callback=guiStripNd.spectrumDisplay.addContourLevel),
            # _SCMitem(name='Remove Contour Level',
            #          typeItem=ItemTypes.get(ITEM), icon='icons/contour-remove', toolTip='Remove One Level',
            #          callback=guiStripNd.spectrumDisplay.removeContourLevel),
            # _SCMitem(name='Raise Base Level',
            #          typeItem=ItemTypes.get(ITEM), icon='icons/contour-base-up', toolTip='Raise Contour Base Level',
            #          callback=guiStripNd.spectrumDisplay.raiseContourBase),
            # _SCMitem(name='Lower Base Level',
            #          typeItem=ItemTypes.get(ITEM), icon='icons/contour-base-down', toolTip='Lower Contour Base Level',
            #          callback=guiStripNd.spectrumDisplay.lowerContourBase),
            # _SCMitem(name='Store Zoom',
            #          typeItem=ItemTypes.get(ITEM), icon='icons/zoom-store', toolTip='Store Zoom',
            #          callback=guiStripNd.spectrumDisplay._storeZoom),
            # _SCMitem(name='Restore Zoom',
            #          typeItem=ItemTypes.get(ITEM), icon='icons/zoom-restore', toolTip='Restore Zoom',
            #          callback=guiStripNd.spectrumDisplay._restoreZoom),
            _resetZoom(guiStripNd),
            _navigateItem(guiStripNd),
            _separator(),
            _toggleHorizontalTraceItem(guiStripNd),
            _toggleVerticalTraceItem(guiStripNd),
            _phasingConsoleItem(guiStripNd),
            _separator(),
            _marksItem(guiStripNd),
            _clearMarksItem(guiStripNd),
            _separator(),
            _printItem(guiStripNd),
            ]
    return _createMenu(guiStripNd, items)



def _getNdPhasingMenu(guiStripNd) -> Menu:
    """
    Creates and returns the phasing 1d context menu
    """
    items = _commonPhasingMenuItems(guiStripNd)

    return _createMenu(guiStripNd, items)



def _getPeakMenu(guiStrip) -> Menu:
    """
    Creates and returns the phasing Nd context menu

    """
    items = [
            _SCMitem(name='Delete peak/s',
                     typeItem=ItemTypes.get(ITEM), toolTip='Delete Peak/s from project', callback=guiStrip.mainWindow.deleteSelectedPeaks),

            ]


    return _createMenu(guiStrip, items)