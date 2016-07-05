"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

import collections
import datetime
from typing import Sequence, Optional
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpnmodel.ccpncore.api.ccp.nmr.NmrConstraint import NmrConstraintStore as ApiNmrConstraintStore
from ccpnmodel.ccpncore.api.ccp.nmr.NmrConstraint import FixedResonance as ApiFixedResonance
from ccpnmodel.ccpncore.lib.spectrum.Spectrum import name2IsotopeCode


class DataSet(AbstractWrapperObject):
  """Data set. Used to store the input to (or output from) a calculation, including data
  selection and parameters, to group Restraints that are used together, to track
  data history and file loads. """

  #: Short class name, for PID.
  shortClassName = 'DS'
  # Attribute it necessary as subclasses must use superclass className
  className = 'DataSet'

  _parentClass = Project

  #: Name of plural link to instances of class
  _pluralLinkName = 'dataSets'
  
  #: List of child classes.
  _childClasses = []

  # Qualified name of matching API class
  _apiClassQualifiedName = ApiNmrConstraintStore._metaclass.qualifiedName()

  # CCPN properties  
  @property
  def _apiDataSet(self) -> ApiNmrConstraintStore:
    """ CCPN NmrConstraintStore matching DataSet"""
    return self._wrappedData

    
  @property
  def _key(self) -> str:
    """id string - serial number converted to string"""
    return str(self._wrappedData.serial)

  @property
  def serial(self) -> int:
    """serial number of DataSet, used in Pid and to identify the DataSet. """
    return self._wrappedData.serial

  @property
  def _parent(self) -> Project:
    """Parent (containing) object."""
    return self._project

  @property
  def title(self) -> str:
    """Title of DataSet"""
    return self._wrappedData.name

  @title.setter
  def title(self, value:str):
    self._wrappedData.name = value

  @property
  def programName(self) -> str:
    """Name of program doing calculation"""
    return self._wrappedData.programName

  @programName.setter
  def programName(self, value:str):
    self._wrappedData.programName = value

  @property
  def programVersion(self) -> Optional[str]:
    """Version of program doing calculation"""
    return self._wrappedData.programVersion

  @programVersion.setter
  def programVersion(self, value:str):
    self._wrappedData.programVersion = value

  @property
  def dataPath(self) -> Optional[str]:
    """File path where dataSet is stored"""
    return self._wrappedData.dataPath

  @dataPath.setter
  def dataPath(self, value:str):
    self._wrappedData.dataPath = value

  @property
  def creationDate(self) -> Optional[datetime.datetime]:
    """Creation timestamp for DataSet"""
    return self._wrappedData.creationDate

  @creationDate.setter
  def creationDate(self, value:datetime.datetime):
    self._wrappedData.creationDate = value

  @property
  def uuid(self) -> Optional[str]:
    """Univcersal identifier for dataSet"""
    return self._wrappedData.uuid

  @uuid.setter
  def uuid(self, value:str):
    self._wrappedData.uuid = value

  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details
    
  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value


  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:Project)-> list:
    """get wrappedData for all NmrConstraintStores linked to NmrProject"""
    return parent._wrappedData.sortedNmrConstraintStores()

  def _fetchFixedResonance(self, assignment:Sequence[str]) -> ApiFixedResonance:
    """Fetch FixedResonance matching assignment tuple, creating anew if needed."""

    apiNmrConstraintStore = self._wrappedData

    tt = assignment
    if len(tt) != 4:
      raise ValueError("assignment %s must have four fields" % tt)

    dd = {
      'chainCode':tt[0],
      'sequenceCode':tt[1],
      'residueType':tt[2],
      'name':tt[3]
    }
    result = apiNmrConstraintStore.findFirstFixedResonance(**dd)

    if result is None:
      dd['isotopeCode'] = name2IsotopeCode(tt[3])
      result = apiNmrConstraintStore.newFixedResonance(**dd)
    #
    return result


def _newDataSet(self:Project, title:str=None, programName:str=None, programVersion:str=None,
                dataPath:str=None, creationDate:datetime.datetime=None, uuid:str=None,
                comment:str=None) -> DataSet:
  """Create new ccpn.DataSet"""

  defaults = collections.OrderedDict((('title', None), ('programName', None),
                                     ('programVersion', None), ('dataPath', None),
                                     ('creationDate', None), ('uuid', None), ('comment', None))
  )
  
  nmrProject = self._wrappedData
  self._startFunctionCommandBlock('newDataSet', values=locals(), defaults=defaults,
                                  parName='newDataSet')
  try:
    newApiNmrConstraintStore = nmrProject.root.newNmrConstraintStore(nmrProject=nmrProject,
                                                                     name=title,
                                                                     programName=programName,
                                                                     programVersion=programVersion,
                                                                     dataPath=dataPath,
                                                                     creationDate=creationDate,
                                                                     uuid=uuid,
                                                                     details=comment)
  finally:
    self._project._appBase._endCommandBlock()
  return self._data2Obj.get(newApiNmrConstraintStore)
    
    
# Connections to parents:
Project.newDataSet = _newDataSet
del _newDataSet

# Notifiers:
