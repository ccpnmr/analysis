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
import functools
from ccpncore.gui import MessageDialog
from ccpncore.api.ccp.nmr.Nmr import Peak as ApiPeak
from ccpn import Project

# Fields that are coded automatically
_autoFields = ['peaks','regions','positions', 'strips']
# NB For each of these fields code is generated to match the explicit code for the 'spectra' field
# It is assumed that each autofield is plural, ending in a plural 's'
# Note that the singluar value (e.g. 'currentSpectrum') is the last object
# in the plural value (That is e.g. current.spectra[-1]

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
    # Otherwise it is the responsibility of teh adder to remove them when no longer relevant
    # for which the notifier function object must be kept around.
    # The function is attached to the field and is executed when the field value changes
    # In practice this goes through the setter for (the equivalent of) Current.spectra
    # The notifier function takes a list of wrapper objects (eg. wrapper spectra)
    # as their only parameter.
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
      func(value)

  @property
  def spectrum(self):
    return self._spectra[-1] if self._spectra else None

  @spectrum.setter
  def spectrum(self, value):
    self._spectra = [value]

  def addSpectrum(self, value):
    self.spectra = self._spectra + [value]

  def clearSpectra(self):
    del self._spectra[:]


  def deleteSelected(self, parent=None):
    # TBD: more general deletion
    if self.peaks:
      n = len(self.peaks)
      title = 'Delete Peak%s' % ('' if n == 1 else 's')
      msg ='Delete %sselected peak%s?' % ('' if n == 1 else '%d ' % n, '' if n == 1 else 's')
      if MessageDialog.showYesNo(title, msg, parent):
        for peak in self.peaks[:]:
          peak.delete()
        #self.peaks = [] # not needed since _deletedPeak notifier will clear this out


for field in _autoFields:
  ufield = '_' + field
  Field = field[0].upper() + field[1:-1]
  getField = operator.attrgetter(ufield)
  getFieldItem = operator.itemgetter(field)
  # We should do this, but it requires Python 3.4, so we emulate it
  # setField = functools.partialmethod(setattr, ufield)
  def setField(self, value, field=ufield):
    setattr(self, field, value)

  def getter(self):
    return list(getField(self))
  def setter(self, value):
    if len(set(value)) != len(value):
      msg = "Current %s contains duplicates: %%s" % field
      raise ValueError(msg % value)
    # self.setField(list(value))
    setField(self, list(value))
    print ("@~@~", self._notifies)
    funcs = getFieldItem(self._notifies) or ()
    # for func in self._notifies.get(field, ()):
    for func in funcs:
      func(value)
  #
  setattr(Current, field, property(getter, setter, None, "Current %s" % field))

  def getter(self):
    ll = getField(self)
    return ll[-1] if ll else None
  def setter(self, value):
    # self.setField([value])
    setField(self, [value])
  #
  setattr(Current, field[:-1], property(getter, setter, None, "Current %s" % field[:-1]))

  def adder(self, value):
    # self.setField(getField(self) + [value])
    setField(self, getField(self) + [value])
  #
  setattr(Current, 'add' + Field, adder)

  def clearer(self):
    getField(self).clear()
  #
  setattr(Current, 'clear' + Field, clearer)
#
del getter
del setter
del adder
del clearer
del ufield
del Field
del field

def _cleanupCurrentPeak(project, apiPeak):
    
  current = project._appBase.current
  if current:
    peak = project._data2Obj[apiPeak]
    ll = current.peaks
    if peak in current.peaks:
      ll.remove(peak)
      current.peaks = ll

Project._cleanupCurrentPeak = _cleanupCurrentPeak
# Register notifier for registering/unregistering
Project._apiNotifiers.append(('_cleanupCurrentPeak', {},
                              ApiPeak._metaclass.qualifiedName(), 'preDelete'))