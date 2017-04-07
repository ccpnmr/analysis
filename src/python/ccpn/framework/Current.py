"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:40:36 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"

__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import operator
import typing
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Chain import Chain
from ccpn.core.Residue import Residue
from ccpn.core.NmrChain import NmrChain
from ccpn.core.NmrResidue import NmrResidue
from ccpn.core.NmrAtom import NmrAtom
from ccpn.core.ChemicalShiftList import ChemicalShiftList
from ccpn.core.ChemicalShift import ChemicalShift
# from ccpn.core.Spectrum import Spectrum
from ccpn.core.SpectrumGroup import SpectrumGroup
from ccpn.core.Peak import Peak
# from ccpn.core.Integral import Integral
from ccpn.ui._implementation.Strip import Strip
# from ccpn.ui._implementation.SpectrumDisplay import SpectrumDisplay

_currentClasses = {
  SpectrumGroup:{'singularOnly':True},
  Peak:{},
  NmrChain:{},
  NmrResidue:{},
  NmrAtom:{},
  Strip:{'singularOnly':True},
  Chain:{},
  Residue:{},
  ChemicalShiftList:{},
  ChemicalShift:{}
}

_currentExtraFields = {
  'positions':{'docTemplate':"last cursor %s"},
  'cursorPositions':{'singularOnly':True, 'docTemplate':'last cursor %s - (posX,posY) tuple'},
  'axisCodes':{'singularOnly':True, 'docTemplate':'last selected %s'},
}

# Fields in current (there is a current.xyz attribute with related functions
# for every 'xyz' in fields
_fields = [x._pluralLinkName for x in _currentClasses] + list(_currentExtraFields.keys())


def noCap(string):
  """return de-capitalised string"""
  if len(string) <= 0: return string
  return string[0].lower() + string[1:]


class Current:

  # create the doc-string dynamically from definitions above;
  # cannot do newlines as Python console falls over when querying using the current? syntax (too many newlines?)

  ll = []
  for cls in sorted(_currentClasses.keys(), key=operator.attrgetter('className')):
    ss = noCap(cls.className)
    ll.append('\n%s (last selected %s)' % (ss, ss))
    if not _currentClasses[cls].get('singularOnly'):
      ss = noCap(cls._pluralLinkName)
      ll.append('%s (all selected %s)' % (ss, ss))

  for field in sorted(_currentExtraFields.keys()):
    ss = field[:-1]
    dd = _currentExtraFields[field]
    ll.append('\n%s (%s)' % (ss, dd['docTemplate'] % ss))
    if not dd.get('singularOnly'):
      ss = field
      ll.append('%s (%s)' % (ss, dd['docTemplate'] % ss))

  __doc__ = (
  """The current object gives access to the collection of active or selected objects and values.

Currently implemented:
%s

Use print(current) to get a list of attribute, value pairs')
""" % '; '.join(ll)
  )
  # + '; '.join(('%s (%s)' % (f,v) for f,t,v in _definitions))
  # + '\n\nUse print(current) to get a list of attribute, value pairs')

  def __init__(self, project):
    # initialise non-=auto fields
    self._project = project

    for field in _fields:
      setattr(self, '_' + field, [])

    # initialise notifies
    notifies = self._notifies = {}
    for field in _fields:
      notifies[field] = []

    self.registerNotify(self._updateSelectedPeaks, 'peaks')

  def registerNotify(self, notify, field):
    # Notifiers are attached to the Current OBJECT, not to the class
    # They are therefore removed when a new project is created/loaded
    # Otherwise it is the responsibility of the adder to remove them when no longer relevant
    # for which the notifier function object must be kept around.
    # The function is attached to the field and is executed after the field value changes
    # In practice this goes through the setter for (the equivalent of) Current.spectra
    # The notifier function is passed the new value of the field as its only parameter.
    # If you need a graphics object (e.g. a module) you must make and register a bound method
    # on the module.

    self._notifies[field].append(notify)

  def unRegisterNotify(self, notify, field):
    """Remove 'current' notifier"""
    self._notifies[field].remove(notify)

  def _updateSelectedPeaks(self, currentPeaks):
    """ Update selected status of peaks.
    This attribute is redundant information but is done for time efficiency in drawing,
    so you don't have to check whether a peak is in a list / set but just check the attribute.
    """
    for peakList in self.project.peakLists:
      for peak in peakList.peaks:
        peak._isSelected = False

    for peak in currentPeaks:
      peak._isSelected = True

  @property
  def project(self):
    """Project attached to current"""
    return self._project

  def __str__(self):
    """
    Return string representation of self listing all attribute, value pairs
    """
    ll = []
    for cls in sorted(_currentClasses.keys(), key=operator.attrgetter('className')):
      ss = noCap(cls.className)
      ll.append((ss, getattr(self, ss)))
      if not _currentClasses[cls].get('singularOnly'):
        ss = noCap(cls._pluralLinkName)
        ll.append((ss, getattr(self, ss)))

    for field in sorted(_currentExtraFields.keys()):
      ss = field[:-1]
      ll.append((ss, getattr(self, ss)))
      if not _currentExtraFields[field].get('singularOnly'):
        ss = field
        ll.append((ss, getattr(self, ss)))

    maxlen = max((len(tt[0]) for tt in ll))
    fmt = 'current.%-' + str(maxlen) + 's : %s'
    # fmt = "current.%%-%s : %%s" % maxlen
    return '\n'.join(fmt % tt for tt in ll)


    # maxlen = max((len(f) for f,t,v in self._definitions))
    # fmt = 'current.%-' + str(maxlen) + 's : %s'
    # #return "current\n" + '\n'.join((fmt % (f,getattr(self,f)) for f,t,v in _definitions))
    # return '\n'.join((fmt % (f,getattr(self,f)) for f,t,v in self._definitions))

  @classmethod
  def  _addClassField(cls, param:typing.Union[str, AbstractWrapperObject]):
    """Add new 'current' field with necessary function for input
    param (wrapper class or field name)"""

    if isinstance(param, str):
      plural = param
      singular = param[:-1]  # It is assumed that param ends in plural 's'
      singularOnly = _currentExtraFields[param].get('singularOnly')
    else:
      # param is a wrapper class
      plural = param._pluralLinkName
      singular = param.className
      singular = singular[0].lower() + singular[1:]
      singularOnly = _currentClasses[param].get('singularOnly')

    # getter function for _field; getField(obj) returns obj._field:
    getField = operator.attrgetter('_' + plural)

    # getFieldItem(obj) returns obj[field]
    getFieldItem = operator.itemgetter(plural)

    # setField(obj, value) sets obj._field = value and calls notifiers
    def setField(self, value, plural=plural):
      if len(set(value)) != len(value):
        raise ValueError( "Current %s contains duplicates: %s" % (plural, value))
      setattr(self, '_'+plural, value)
      funcs = getFieldItem(self._notifies) or ()
      for func in funcs:
        func(value)

    def getter(self):
      ll = getField(self)
      return ll[-1] if ll else None
    def setter(self, value):
      setField(self, [value])
    #
    setattr(cls, singular, property(getter, setter, None, "Current %s" % singular))

    if not singularOnly:

      def getter(self):
        return tuple(getField(self))
      def setter(self, value):
        setField(self, list(value))
      #
      setattr(cls, plural, property(getter, setter, None, "Current %s" % plural))

      def adder(self, value):
        """Add %s to current.%s""" % (singular, plural)
        values = getField(self)
        if value not in values:
          setField(self, values + [value])
      #
      setattr(cls, 'add' + singular.capitalize(), adder)

      def remover(self, value):
        """Remove %s from current.%s""" % (singular, plural)
        values = getField(self)
        if value in values:
          values.remove(value)
        setField(self, values)
      #
      setattr(cls, 'remove' + singular.capitalize(), remover)

      def clearer(self):
        """Clear current.%s""" % plural
        setField(self, [])
      #
      setattr(cls, 'clear' + plural.capitalize(), clearer)

    if not isinstance(param, str):
      # param is a class - Add notifiers for deleted objects
      def cleanup(self:AbstractWrapperObject):
        current = self._project._appBase.current
        if current:
          fieldData = getField(current)
          if self in fieldData:
            fieldData.remove(self)
      cleanup.__name__ = 'current_%s_deletion_cleanup' % singular
      #
      param._setupCoreNotifier('delete', cleanup)

# Add fields to current
for cls in _currentClasses:
  Current._addClassField(cls)
for field in _currentExtraFields:
  Current._addClassField(field)
