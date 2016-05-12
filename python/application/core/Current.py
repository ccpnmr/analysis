"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================

import operator
# import functools
from application.core.widgets import MessageDialog
from ccpncore.api.ccp.nmr.Nmr import Peak as ApiPeak
from ccpncore.api.ccp.nmr.Nmr import Resonance as ApiNmrAtom
from ccpncore.api.ccp.nmr.Nmr import ResonanceGroup as ApiNmrResidue
from ccpncore.api.ccp.nmr.Nmr import DataSource as ApiSpectrum
from ccpncore.api.ccpnmr.gui.Task import Strip as ApiStrip
from ccpncore.api.ccpnmr.gui.Task import SpectrumDisplay as ApiSpectrumDisplay
from ccpn import Project

# Fields that are coded automatically
_autoFields = ['peaks','regions','positions', 'strips', 'nmrChains', 'nmrResidues', 'nmrAtoms',
               'spectrumDisplays', 'spectrumGroups']
# NB For each of these fields code is generated to match the explicit code for the 'spectra' field
# It is assumed that each autofield is plural, ending in a plural 's'
# Note that the singular value (e.g. 'currentSpectrum') is the last object
# in the plural value (That is e.g. current.spectra[-1]


# Fields in this dictionary
_notifyDeleteFields = {
  'peaks':ApiPeak,
  'strips':ApiStrip,
  'nmrResidues':ApiNmrResidue,
  'nmrAtoms':ApiNmrAtom,
  'spectrumDisplays':ApiSpectrumDisplay
}

_fields = ['project', 'spectra'] + _autoFields

class Current:

  def __init__(self, project):
    # initialise non-=auto fields
    self._project = project
    self._spectra = []

    for field in _autoFields:
      setattr(self, '_'+field, [])

    # initialise notifies
    notifies = self._notifies = {}
    notifies['spectra'] = []
    for field in _autoFields:
      notifies[field] = []

  def registerNotify(self, notify, field):
    # Notifiers are attached to the OBJECT, not to the class
    # They are therefore removed when a new project is created/loaded
    # Otherwise it is the responsibility of the adder to remove them when no longer relevant
    # for which the notifier function object must be kept around.
    # The function is attached to the field and is executed after the field value changes
    # In practice this goes through the setter for (the equivalent of) Current.spectra
    # The notifier function is passed the Current object as its only parameter,
    # which allows you to access the project, the value just changed or anything else.
    # If you need a graphics object (e.g. a module) you must make and register a bound method
    # on the module.

    notifies = self._notifies
    ll = notifies.get(field)
    if ll is None:
      notifies[field] = [notify]

    elif notify not in ll:
      ll.append(notify)

  def unRegisterNotify(self, notify, field):
    try:
      self._notifies[field].remove(notify)
    except ValueError:
      pass

  @property
  def project(self):
    """Project attached to current"""
    return self._project

  @property
  def spectra(self):
    """Current spectra"""
    return list(self._spectra)

  @spectra.setter
  def spectra(self, value):
    if len(set(value)) != len(value):
      raise ValueError("Current Spectra contains duplicates: %s" % value)
    self._spectra = list(value)
    for func in self._notifies.get('spectra', ()):
      func(self)

  @property
  def spectrum(self):
    return self._spectra[-1] if self._spectra else None

  @spectrum.setter
  def spectrum(self, value):
    self.spectra = [value]

  def addSpectrum(self, value):
    self.spectra = self._spectra + [value]

  def removeSpectrum(self, value):
    self._spectra.remove(value)
    self.spectra = self._spectra + [value]

  def clearSpectra(self):
    self.spectra = []


  def deleteSelected(self, parent=None):
    # TBD: more general deletion
    if self.peaks:
      n = len(self.peaks)
      title = 'Delete Peak%s' % ('' if n == 1 else 's')
      msg ='Delete %sselected peak%s?' % ('' if n == 1 else '%d ' % n, '' if n == 1 else 's')
      if MessageDialog.showYesNo(title, msg, parent):
        for peak in self.peaks[:]:

          self.project._appBase.mainWindow.pythonConsole.writeConsoleCommand('peak.delete()',
                                                                    peak=peak)
          peak.delete()
        #self.peaks = [] # not needed since _deletedPeak notifier will clear this out


# Add notifiers for deleted spectra
def current_spectra_deletion_cleanup(self:Project, apiObj):

  current = self._appBase.current
  if current:
    obj = self._data2Obj[apiObj]
    fieldData = current._spectra
    if obj in fieldData:
      fieldData.remove(obj)
#
Project._setupApiNotifier(current_spectra_deletion_cleanup, ApiSpectrum, 'preDelete')


def  _addClassField(cls, field):
  # getter function for _field; getField(obj) returns obj._field:
  getField = operator.attrgetter('_' + field)

  # getFieldItem(obj) returns obj[field]
  getFieldItem = operator.itemgetter(field)

  # setField(obj, value) sets obj._field = value and calls notifiers
  def setField(self, value, field='_' + field):
    if len(set(value)) != len(value):
      msg = "Current %s contains duplicates: %%s" % field
      raise ValueError(msg % value)
    setattr(self, field, value)
    funcs = getFieldItem(self._notifies) or ()
    for func in funcs:
      func(value)

  def getter(self):
    return tuple(getField(self))
  def setter(self, value):
    setField(self, list(value))
  #
  setattr(cls, field, property(getter, setter, None, "Current %s" % field))

  def getter(self):
    ll = getField(self)
    return ll[-1] if ll else None
  def setter(self, value):
    setField(self, [value])
  #
  setattr(cls, field[:-1], property(getter, setter, None, "Current %s" % field[:-1]))

  def adder(self, value):
    setField(self, getField(self) + [value])
  #
  setattr(cls, 'add' + field.capitalize()[:-1], adder)

  def remover(self, value):
    ll = getField(self)
    ll.remove(value)
    setField(self, ll)
  #
  setattr(cls, 'remove' + field.capitalize()[:-1], remover)

  def clearer(self):
    setField(self, [])
  #
  setattr(cls, 'clear' + field.capitalize(), clearer)

  apiClass = _notifyDeleteFields.get(field)
  if apiClass is not None:
    # Add notifiers for deleted objects
    def cleanup(self:Project, apiObj):

      current = self._appBase.current
      if current:
        obj = self._data2Obj[apiObj]
        fieldData = getField(current)
        if obj in fieldData:
          fieldData.remove(obj)
    cleanup.__name__ = 'current_%s_deletion_cleanup' % field
    #
    Project._setupApiNotifier(cleanup, apiClass, 'preDelete')

for field in _autoFields:
  _addClassField(Current, field)