"""
Generate PulldownListCompoundWidget for project objects; 
set callback's on creation, deletion and rename

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
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:55 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2017-04-18 15:19:30 +0100 (Tue, April 18, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.widgets.CompoundWidgets import PulldownListCompoundWidget
from ccpn.core.lib.Notifiers import Notifier

SELECT = '<Select>'


class _Pulldown(PulldownListCompoundWidget):
    # need to subclass this
    className = None
    attributeName = None

    def __init__(self, parent, project,
                 showBorder=False, orientation='left',
                 minimumWidths=(100, 150), maximumWidths=None, fixedWidths=None,
                 labelText=None,
                 showSelectName=False, callback=None, default=None,
                 sizeAdjustPolicy=None, editable=False, filterFunction=None,
                 **kwds):
        """
        Create  a PulldownListCompoundWidget with callbacks responding to changes in the objects
        in project; not to be used directly, used as a base class for the specific classes for 
        the different V3 objects, as defined below.

        :param parent: parent widget
        :param project: containing project
        :param showBorder: flag to display the border of Frame (True, False)
        :param orientation: flag to determine the orientation of the labelText relative to the pulldown widget.
                            Allowed values: 'left', 'right', 'top', 'bottom'
        :param minimumWidths: tuple of two values specifying the minimum width of the Label and Pulldown widget, respectively
        :param labelText: (optional) text for the Label
        :param texts: (optional) iterable generating text values for the Pulldown
        :param showSelectName: (optional) insert <Select> at the top of the Pulldown
        :param callback: (optional) callback for the Pulldown
        :param default: (optional) initially selected element of the Pulldown (text or index)
        :param editable: If True: allows for editing the value
        :param filterFunction: a function(pids:list)->list for editing the pids shown in the pulldown;
                               returns list of new pids
        :param kwds: (optional) keyword, value pairs for the gridding of Frame
      
        :return: PulldownListCompoundWidget instance
        """
        self.project = project
        self._showSelectName = showSelectName
        self._filterFunction = filterFunction

        if labelText is None:
            labelText = self.className + ':'

        super(_Pulldown, self).__init__(parent=parent, showBorder=showBorder,
                                        orientation=orientation,
                                        minimumWidths=minimumWidths, maximumWidths=maximumWidths, fixedWidths=fixedWidths,
                                        labelText=labelText,
                                        texts=self._getPids(),
                                        sizeAdjustPolicy=sizeAdjustPolicy,
                                        callback=callback, default=default,
                                        editable=editable,
                                        **kwds)
        # add a notifier to update the pulldown list
        self._notifier = Notifier(project,
                                  [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME],
                                  self.className,
                                  self._updatePulldownList)

    def _getPids(self)->list:
        """Return a list of pids defined by 'self.attributeName' from project.
        """
        if not hasattr(self, 'attributeName'):
            raise RuntimeError('%s: attributeName needs to be defined for proper functioning' % self.__class__.__name__)
        pids = [obj.pid for obj in getattr(self.project, self.attributeName)]
        if self._filterFunction:
            pids = self._filterFunction(pids)
        if self._showSelectName:
            pids = [SELECT] + pids
        return pids

    def _updatePulldownList(self, callbackDict=None):
        "Callback to update the pulldown list; triggered by object creation, deletion or renaming"
        pids = self._getPids()
        self.modifyTexts(pids)

    def update(self):
        "Public function to update"
        self._updatePulldownList()

    def __str__(self):
        return '<PulldownListCompoundWidget for "%s">' % self.className


#==========================================================================================================
# Implementations for the various V3 objects
#==========================================================================================================

class MultipletListPulldown(_Pulldown):
    className = 'MultipletList'
    attributeName = 'multipletLists'


class NmrChainPulldown(_Pulldown):
    className = 'NmrChain'
    attributeName = 'nmrChains'


class ComplexesPulldown(_Pulldown):
    className = 'Complex'
    attributeName = 'complexes'


class ChainPulldown(_Pulldown):
    className = 'Chain'
    attributeName = 'chains'


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


class SubstancePulldown(_Pulldown):
    className = 'Substance'
    attributeName = 'substances'


class SpectrumPulldown(_Pulldown):
    className = 'Spectrum'
    attributeName = 'spectra'


class IntegralListPulldown(_Pulldown):
    className = 'IntegralList'
    attributeName = 'integralLists'
