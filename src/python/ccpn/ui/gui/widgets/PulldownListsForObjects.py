"""
Generate PulldownListCompoundWidget for project objects; 
set callback's on creation, deletion and rename

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2017-04-13 12:24:48 +0100 (Thu, April 13, 2017) $"

#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.widgets.PulldownList import PulldownListCompoundWidget
from ccpn.core.lib.Notifiers import Notifier

def getPids(fromObject, attributeName):
    "Get a list of pids fromObject.attributeName or None on error"
    if not hasattr(fromObject, attributeName): return None
    return [obj.pid for obj in getattr(fromObject, attributeName)]


def _pulldown(objectName, attributeName,
              parent, project,
              showBorder=False, orientation='left', minimumWidths=None, labelText=None,
              callback=None, default=None, **kwds):
    """
    Create  a PulldownListCompoundWidget with callbacks responding to changes in the objects
    in project; not to be used directly 
  

    :param parent: parent widget
    :param showBorder: flag to display the border of Frame (True, False)
    :param orientation: flag to determine the orientation of the labelText relative to the pulldown widget.
                        Allowed values: 'left', 'right', 'top', 'bottom'
    :param minimumWidths: tuple of two values specifying the minimum width of the Label and Pulldown widget, respectively
    :param labelText: (optional) text for the Label
    :param texts: (optional) iterable generating text values for the Pulldown
    :param callback: (optional) callback for the Pulldown
    :param default: (optional) initially selected element of the Pulldown (text or index)
    :param kwds: (optional) keyword, value pairs for the gridding of Frame
  
    :return: PulldownListCompoundWidget instance
    """
    if labelText is None:
        labelText = objectName + ':'

    if minimumWidths is None:
        minimumWidths = (100,150)

    widget = PulldownListCompoundWidget(parent=parent, showBorder=showBorder,
                                        orientation=orientation, minimumWidths=minimumWidths,
                                        labelText=labelText,
                                        texts=getPids(project, attributeName),
                                        callback=callback, default=default, **kwds)
    # add a notifier to update the pulldown list
    widget.updatePulldownList(project,
                             [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME], objectName,
                              getPids, attributeName)

    return widget


def nmrChainPulldown(parent, project,
                     showBorder=False, orientation='left', minimumWidths=None, labelText=None,
                     callback=None, default=None, **kwds):
    """
    :return: PulldownListCompoundWidget instance for NmrChains
    """
    return _pulldown('NmrChain', 'nmrChains',
                     parent, project,
                     showBorder=showBorder, orientation=orientation, minimumWidths=minimumWidths, labelText=labelText,
                     callback=callback, default=default, **kwds
                     )


def chemicalShiftListPulldown(parent, project,
                     showBorder=False, orientation='left', minimumWidths=None, labelText=None,
                     callback=None, default=None, **kwds):
    """
    :return: PulldownListCompoundWidget instance for ChemicalShiftLists
    """
    return _pulldown('ChemicalShiftList', 'chemicalShiftLists',
                     parent, project,
                     showBorder=showBorder, orientation=orientation, minimumWidths=minimumWidths, labelText=labelText,
                     callback=callback, default=default, **kwds
                     )


def peakListPulldown(parent, project,
                     showBorder=False, orientation='left', minimumWidths=None, labelText=None,
                     callback=None, default=None, **kwds):
    """
    :return: PulldownListCompoundWidget instance for PeakLists
    """
    return _pulldown('PeakList', 'peakLists',
                     parent, project,
                     showBorder=showBorder, orientation=orientation, minimumWidths=minimumWidths, labelText=labelText,
                     callback=callback, default=default, **kwds
                     )