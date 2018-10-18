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
                  showSelectName=False, callback=None, default=None,
                  sizeAdjustPolicy=None, *args, **kwds):
        """
        Create  a PulldownListCompoundWidget with callbacks responding to changes in the objects
        in project; not to be used directly, used as a base class for the specific classes for 
        the different V3 objects

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
        :param kwds: (optional) keyword, value pairs for the gridding of Frame
      
        :return: PulldownListCompoundWidget instance
        """
        self.project = project
        self.showSelectName = showSelectName

        if labelText is None:
            labelText = self.className + ':'

        if minimumWidths is None:
            minimumWidths = (100,150)

        if showSelectName:
          gotPids = getPids(project, self.attributeName)
          if gotPids:
            self.textList = [SELECT]+gotPids
          else:
            self.textList = [SELECT]
        else:
          self.textList = getPids(project, self.attributeName)  # ejb

        super(_Pulldown, self).__init__(parent=parent, showBorder=showBorder,
        # self.PulldownListCompoundWidget.__init__(self, parent=parent, showBorder=showBorder,
                                                orientation=orientation, minimumWidths=minimumWidths,
                                                labelText=labelText,
                                                texts=self.textList,
                                                sizeAdjustPolicy=sizeAdjustPolicy,
                                                callback=callback, default=default, **kwds)
        # add a notifier to update the pulldown list
        if project:
          self.updatePulldownList(project,
                                  [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME],
                                  self.className,
                                  self._getPids)
                                  # getPids, self.attributeName)

    def __str__(self):
        return '<PulldownListCompoundWidget for "%s">' % self.className

    def _getPids(self, data):
      "Get a list of pids 'self.attributeName' from project or None on error"
      if not hasattr(self, 'attributeName'):
          return None

      if self.showSelectName:
        gotPids = getPids(self.project, self.attributeName)
        if gotPids:
          self.textList = ['<Select>'] + gotPids
        else:
          self.textList = ['<Select>']
      else:
        self.textList = getPids(self.project, self.attributeName)

      return self.textList


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
