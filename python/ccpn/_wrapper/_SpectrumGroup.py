"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

from typing import Tuple

from ccpn.util import Pid

from ccpn import AbstractWrapperObject
from ccpn import Project
from ccpn import Spectrum
from ccpn.util import Common as commonUtil
from ccpncore.api.ccp.nmr.Nmr import DataSource as ApiDataSource
from ccpncore.api.ccp.nmr.Nmr import SpectrumGroup as ApiSpectrumGroup


class SpectrumGroup(AbstractWrapperObject):
  """Group of spectra - used for organising spectra."""
  
  #: Short class name, for PID.
  shortClassName = 'SG'
  # Attribute it necessary as subclasses must use superclass className
  className = 'SpectrumGroup'

  #: Name of plural link to instances of class
  _pluralLinkName = 'spectrumGroups'
  
  #: List of child classes.
  _childClasses = []

  # Qualified name of matching API class
  _apiClassQualifiedName = ApiSpectrumGroup._metaclass.qualifiedName()
  

  # CCPN properties  
  @property
  def _apiSpectrumGroup(self) -> ApiSpectrumGroup:
    """ CCPN Project SpectrumGroup"""
    return self._wrappedData

  @property
  def _key(self) -> str:
    """Residue local ID"""
    return self._wrappedData.name.translate(Pid.remapSeparators)

  @property
  def name(self) -> str:
    """Name of SpectrumGroup, part of identifier"""
    return self._wrappedData.name

  @property
  def _parent(self) -> Project:
    """Parent (containing) object."""
    return self._project


  @property
  def spectra(self) -> Tuple[Spectrum, ...]:
    """Spectra that make up SpectrumGroup."""
    data2Obj = self._project._data2Obj
    return tuple(data2Obj[x] for x in self._wrappedData.sortedDataSources())

  @spectra.setter
  def spectra(self, value):
    self._wrappedData.dataSources = [x._wrappedData for x in value]

  # Implementation functions
  def rename(self, value):
    """Rename SpectrumGroup, changing its Id and Pid"""
    oldName = self.name
    undo = self._project._undo
    if undo is not None:
      undo.increaseBlocking()

    try:
      if not value:
        raise ValueError("SpectrumGroup name must be set")
      elif Pid.altCharacter in value:
        raise ValueError("Character %s not allowed in ccpn.SpectrumGroup.name" % Pid.altCharacter)
      else:
        commonUtil._resetParentLink(self._wrappedData, 'spectrumGroups', 'name', value)
        self._finaliseAction('rename')
        self._finaliseAction('change')

    finally:
      if undo is not None:
        undo.decreaseBlocking()

    undo.newItem(self.rename, self.rename, undoArgs=(oldName,),redoArgs=(value,))

  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:Project)-> list:
    """get wrappedData for all SpectrumGroups linked to NmrProject"""
    return parent._wrappedData.sortedSpectrumGroups()


def _newSpectrumGroup(self:Project, name:str, spectra=()) -> SpectrumGroup:
  """Create new SpectrumGroup"""

  if name and Pid.altCharacter in name:
    raise ValueError("Character %s not allowed in ccpn.SpectrumGroup.name" % Pid.altCharacter)

  apiDataSources = [x._wrappedData for x in spectra]
  return self._data2Obj.get(self._wrappedData.newSpectrumGroup(name=name,
                                                               dataSources=apiDataSources))

    
# Connections to parents:
Project._childClasses.append(SpectrumGroup)
Project.newSpectrumGroup = _newSpectrumGroup
del _newSpectrumGroup


# reverse link Spectrum.spectrumGroups
def getter(self:Spectrum) -> Tuple[SpectrumGroup, ...]:
  data2Obj = self._project._data2Obj
  return tuple(data2Obj[x] for x in self._wrappedData.sortedSpectrumGroups())
def setter(self:Spectrum, value):
    self._wrappedData.spectrumGroups = [x._wrappedData for x in value]
#
Spectrum.spectrumGroups = property(getter, setter, None,
                                   "SpectrumGroups that contain Spectrum")
del getter
del setter

# Extra Notifiers to notify changes in Spectrum-SpectrumGroup link
className = ApiSpectrumGroup._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_modifiedLink', {'classNames':('Spectrum','SpectrumGroup')}, className, 'addDataSource'),
    ('_modifiedLink', {'classNames':('Spectrum','SpectrumGroup')}, className, 'removeDataSource'),
    ('_modifiedLink', {'classNames':('Spectrum','SpectrumGroup')}, className, 'setDataSources'),
  )
)
className = ApiDataSource._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_modifiedLink', {'classNames':('Spectrum','SpectrumGroup')}, className, 'addSpectrumGroup'),
    ('_modifiedLink', {'classNames':('Spectrum','SpectrumGroup')}, className, 'removeSpectrumGroup'),
    ('_modifiedLink', {'classNames':('Spectrum','SpectrumGroup')}, className, 'setSpectrumGroups'),
  )
)
