"""
  ejb - orderedSpectrumViews, orderedSpectra
  store the current orderedSpectrumViews in the internal data store _ccpnInternalData
  so it is hidden from external users

  accessed with the functions:
      strip.orderedSpectra()        returns tuple(spectra) or None
      strip.orderedSpectrumViews    returns tuple(spectrumViews) or None

  use setOrderedSpectrumViews(<tuple>) to set the list
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = ""
__credits__ = ""
__licence__ = ("")
__reference__ = ("")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy$"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Tuple,Optional

ORDEREDSPECTRUMVIEWS = '_orderedSpectrumViews'


class OrderedSpectrumViews(object):

  def __init__(self, parent=None):
    self.parent = parent
    self.project = parent.project
    self.spectrumViews = parent.spectrumViews

  def _retrieveOrderedSpectrumViewPids(self):
    if isinstance(self.parent._ccpnInternalData, dict) and ORDEREDSPECTRUMVIEWS in self.parent._ccpnInternalData:
      return self.parent._ccpnInternalData[ORDEREDSPECTRUMVIEWS]
    else:
      return None

  def _storeOrderedSpectrumViewPids(self, spectrumViewPids):
    if isinstance(self.parent._ccpnInternalData, dict):
      self.parent._ccpnInternalData[ORDEREDSPECTRUMVIEWS] = spectrumViewPids

  def orderedSpectra(self) -> Optional[Tuple]:
    """The spectra attached to the strip (ordered)"""
    if hasattr(self, ORDEREDSPECTRUMVIEWS):
      return tuple(x.spectrum for x in getattr(self, ORDEREDSPECTRUMVIEWS) if 'Deleted' not in x.pid)
    else:
      # create a dataset with the spectrumViews attached (will be alphabetical) if doesn't exist
      # store by pids

      pids = self._retrieveOrderedSpectrumViewPids()
      if not pids:
        self._storeOrderedSpectrumViewPids(tuple(x.pid for x in self.spectrumViews))
        views = tuple(x for x in self.spectrumViews)
      else:
        views = tuple(self.project.getByPid(x) for x in pids if self.project.getByPid(x))

        # this should be the first read from loading the project, so write back without bad pids
        self._storeOrderedSpectrumViewPids(tuple(x.pid for x in views))

    setattr(self, ORDEREDSPECTRUMVIEWS, views)
    return tuple(x.spectrum for x in views)

  def orderedSpectrumViews(self) -> Optional[Tuple]:
    """The spectra attached to the strip (ordered)"""
    if hasattr(self, ORDEREDSPECTRUMVIEWS):
      views = getattr(self, ORDEREDSPECTRUMVIEWS)
      return views   # tuple(value for value in values if 'Deleted' not in value.pid or includeDeleted)
    else:
      # create a dataset with the spectrumViews attached (will be alphabetical) if doesn't exist
      # store by pid
      pids = self._retrieveOrderedSpectrumViewPids()
      if not pids:
        self._storeOrderedSpectrumViewPids(tuple(x.pid for x in self.spectrumViews))
        views = tuple(x for x in self.spectrumViews)
      else:
        views = tuple(self.project.getByPid(x) for x in pids if self.project.getByPid(x))

        # this should be the first read from loading the project, so write back without bad pids
        self._storeOrderedSpectrumViewPids(tuple(x.pid for x in views))

    setattr(self, ORDEREDSPECTRUMVIEWS, views)
    return views

  def _setOrderedSpectrumViews(self, spectrumViews:Tuple):
    self._storeOrderedSpectrumViewPids(tuple(x.pid for x in spectrumViews))
    setattr(self, ORDEREDSPECTRUMVIEWS, tuple(spectrumViews))

  def _undoOrderedSpectrumViews(self, spectrumViews:Tuple):
    self._storeOrderedSpectrumViewPids(tuple(x.pid for x in spectrumViews))
    setattr(self, ORDEREDSPECTRUMVIEWS, tuple(spectrumViews))

  def setOrderedSpectrumViews(self, spectrumViews:Tuple):
    pidStr = ','.join(["project.getByPid('%s')" % sp.pid for sp in spectrumViews])
    self.project._appBase._startCommandBlock("project.getByPid('%s').setOrderedSpectrumViews(spectrumViews=(%s))" % \
                                             (self.parent.pid, pidStr))
    _undo = self.project._undo
    if _undo is not None:
      _undo.increaseBlocking()

    try:
      _oldSpectrumViews = self.orderedSpectrumViews()
      self._setOrderedSpectrumViews(tuple(spectrumViews))

    finally:
      self.project._appBase._endCommandBlock()

    if _undo is not None:
      _undo.decreaseBlocking()

      _undo.newItem(self._undoOrderedSpectrumViews, self._setOrderedSpectrumViews
                    , undoArgs=(_oldSpectrumViews,), redoArgs=(spectrumViews,))

      # need to fire a notifier that the spectrumViews have changed
      # this should notify SpectrumDisplay to redraw its toolbar

    # self.parent._finalise(action='change')

  def appendSpectrumView(self, spectrumView):
    # retrieve the list from the dataset
    # append to the end
    # write back to the dataset
    if hasattr(self, ORDEREDSPECTRUMVIEWS):
      spectra = (getattr(self, ORDEREDSPECTRUMVIEWS), (spectrumView,))
      spectra = tuple(j for i in spectra for j in i)
    else:
      spectra = tuple(spectrumView,)

    self._storeOrderedSpectrumViewPids(tuple(x.pid for x in spectra))

    values = tuple(x for x in spectra)
    setattr(self, ORDEREDSPECTRUMVIEWS, values)

  def removeSpectrumView(self, spectrumView):
    if hasattr(self, ORDEREDSPECTRUMVIEWS):
      spectra = getattr(self, ORDEREDSPECTRUMVIEWS)
    else:
      spectra = tuple(spectrumView,)

    self._storeOrderedSpectrumViewPids(tuple(x.pid for x in spectra))

    values = tuple(x for x in spectra)
    setattr(self, ORDEREDSPECTRUMVIEWS, values)

  def copyOrderedSpectrumViews(self, fromStrip):
    if hasattr(fromStrip, ORDEREDSPECTRUMVIEWS):
      fromSpectraV = getattr(fromStrip, ORDEREDSPECTRUMVIEWS)

      # loop through the source list of spectra and append the new matching spectra in this spectrumView
      newSpectra = []
      for fromSP in fromSpectraV:
        for selfSPV in self.spectrumViews:

          # fromSP could be a 'deleted' structure, so no 'spectrum' attribute
          if hasattr(fromSP, 'spectrum'):
            if fromSP.spectrum == selfSPV.spectrum:
              newSpectra.append(selfSPV)

      self._storeOrderedSpectrumViewPids(tuple(x.pid for x in newSpectra))

      values = tuple(x for x in newSpectra)
      setattr(self, ORDEREDSPECTRUMVIEWS, values)

