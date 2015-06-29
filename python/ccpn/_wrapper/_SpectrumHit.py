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

from collections.abc import Sequence
from ccpn import AbstractWrapperObject
from ccpn import Project
from ccpn import Spectrum
from ccpncore.api.ccp.nmr.Nmr import SpectrumHit as ApiSpectrumHit
from ccpncore.util import Pid


class SpectrumHit(AbstractWrapperObject):
  """Hit (active compound for screening, observed compound for Metabolomics) observed in Spectrum"""

  #: Short class name, for PID.
  shortClassName = 'SH'

  #: Name of plural link to instances of class
  _pluralLinkName = 'spectrumHits'

  #: List of child classes.
  _childClasses = []

  # CCPN properties
  @property
  def apiSpectrumHits(self) -> ApiSpectrumHit:
    """ CCPN SpectrumHit matching SpectrumHit"""
    return self._wrappedData


  @property
  def _key(self) -> str:
    """object identifier, used for id"""

    obj =  self._wrappedData
    return Pid.IDSEP.join((obj.substanceName.translate(Pid.remapSeparators),
                           str(obj.sampledDimension), str(obj.sampledPoint)))
  @property
  def _parent(self) -> Spectrum:
    """Spectrum containing spectrumReference."""
    return self._project._data2Obj[self._wrappedData.dataDim.dataSource]

  spectrum = _parent

  @property
  def substanceName(self) -> int:
    """NAme of hit substance"""
    return self._wrappedData.substanceName

  @property
  def pseudoDimension(self) -> int:
    """Dimension number for pseudoDimension (0 if none),
    if the Hit only refers to one point in a pseudoDimension"""
    return self._wrappedData.sampledDimension

  @property
  def pointNumber(self) -> int:
    """Point number for pseudoDimension (0 if none),
    if the Hit only refers to one point in a pseudoDimension"""
    return self._wrappedData.sampledPoint

  @property
  def figureOfMerit(self) -> float:
    """Figure of merit (in range 0-1) describing quality of hit"""
    return self._wrappedData.figureOfMerit

  @figureOfMerit.setter
  def figureOfMerit(self, value:float):
    self._wrappedData.figureOfMerit = value

  @property
  def normalisedChange(self) -> float:
    """Normalized size of effect (normally intensity change). in range -1 <= x <= 1.
    Positive values are large changes, negative values changes in the 'wrong' direction,
    e.g. intensity increase where a decrease was expected."""
    return self._wrappedData.normalisedChange

  @normalisedChange.setter
  def normalisedChange(self, value:float):
    self._wrappedData.normalisedChange = value

  @property
  def meritCode(self) -> str:
    """Merit code string describing quality of hit """
    return self._wrappedData.meritCode

  @meritCode.setter
  def meritCode(self, value:str):
    self._wrappedData.meritCode = value

  @property
  def isConfirmed(self) -> bool:
    """Is HIt ocnfirmed? True: yes; False; No; None: not determined"""
    return  self._wrappedData.isConfirmed

  @isConfirmed.setter
  def isConfirmed(self, value:bool):
    self._wrappedData.isConfirmed = value

  @property
  def concentration(self) -> float:
    """SpectrumHit.concentration"""
    return self._wrappedData.concentration

  @concentration.setter
  def concentration(self, value:float):
    self._wrappedData.concentration = value

  @property
  def concentrationError(self) -> float:
    """Estimated Standard error of SpectrumHit.concentration"""
    return self.swrappedData.concentrationError

  @concentrationError.setter
  def concentrationError(self, value:float):
    self._wrappedData.concentrationError = value

  @property
  def concentrationUnit(self) -> str:
    """Unit of SpectrumHit.concentration, one of: 'g/L', 'M', 'L/L', 'mol/mol', 'g/g' """
    return self._wrappedData.concentrationUnit

  @concentrationUnit.setter
  def concentrationUnit(self, value:str):
    self._wrappedData.concentrationUnit = value

  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details

  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value

  # Implementation functions

  @classmethod
  def _getAllWrappedData(cls, parent: Spectrum)-> list:
    """get wrappedData (Nmr.SpectrumHit) for all SpectrumHit children of parent Spectrum"""
    return parent._wrappedData.sortedSpectrumHits()

# Connections to parents:

Spectrum._childClasses.append(SpectrumHit)

# Notifiers:
className = ApiSpectrumHit._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':SpectrumHit}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)