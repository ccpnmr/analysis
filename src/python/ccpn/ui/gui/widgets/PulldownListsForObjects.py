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
__date__ = "$Date: 2017-04-18 15:19:30 +0100 (Tue, April 18, 2017) $"

#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.widgets.CompoundWidgets import PulldownListCompoundWidget
from ccpn.core.lib.Notifiers import Notifier


def getPids(fromObject, attributeName):
    "Get a list of pids fromObject.attributeName or None on error"
    if not hasattr(fromObject, attributeName): return None
    return [obj.pid for obj in getattr(fromObject, attributeName)]


class _Pulldown(PulldownListCompoundWidget):

    # need to subclass this
    className = None
    attributeName = None

    def __init__( self, parent, project,
                  showBorder=False, orientation='left', minimumWidths=None, labelText=None,
                  showSelectName=False, callback=None, default=None, **kwds):
        """
        Create  a PulldownListCompoundWidget with callbacks responding to changes in the objects
        in project; not to be used directly, used as a base class for the specific classes for 
        the different V3 objects
      
    
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
            labelText = self.className + ':'

        if minimumWidths is None:
            minimumWidths = (100,150)

        if showSelectName:
          self.textList = ['<Select>']+getPids(project, self.attributeName) # ejb
        else:
          self.textList = getPids(project, self.attributeName)  # ejb

        PulldownListCompoundWidget.__init__(self, parent=parent, showBorder=showBorder,
                                            orientation=orientation, minimumWidths=minimumWidths,
                                            labelText=labelText,
                                            texts=self.textList,
                                            callback=callback, default=default, **kwds)
        # add a notifier to update the pulldown list
        self.updatePulldownList(project
                                , [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME]
                                , self.className
                                , getPids, self.attributeName)

    def __str__(self):
        return '<PulldownListCompoundWidget for "%s">' % self.className


class NmrChainPulldown(_Pulldown):
    className = 'NmrChain'
    attributeName = 'nmrChains'


class StructurePulldown(_Pulldown):
  className = 'StructureEnsemble'
  attributeName = 'structureEnsembles'


class NotesPulldown(_Pulldown):
  className = 'Note'
  attributeName = 'notes'


class RestraintsPulldown(_Pulldown):
  className = 'RestraintList'
  attributeName = 'restraintLists'


class ChemicalShiftListPulldown(_Pulldown):
    className = 'ChemicalShiftList'
    attributeName = 'chemicalShiftLists'


class PeakListPulldown(_Pulldown):
    className = 'PeakList'
    attributeName = 'peakLists'


class SpectrumPulldown(_Pulldown):
    className = 'Spectrum'
    attributeName = 'spectra'
