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
from typing import Optional, List
from ccpncore.api.ccp.nmr.NmrConstraint import CalculationStep as ApiCalculationStep
from ccpn import AbstractWrapperObject
from ccpn import DataSet


class CalculationStep(AbstractWrapperObject):
  """CalculationStep information, for tracking successive calculations.
  Orderd from oldest to newest"""
  
  #: Short class name, for PID.
  shortClassName = 'DC'
  # Attribute it necessary as subclasses must use superclass className
  className = 'CalculationStep'

  #: Name of plural link to instances of class
  _pluralLinkName = 'calculationSteps'

  #: List of child classes.
  _childClasses = []

  # Qualified name of matching API class
  _apiClassQualifiedName = ApiCalculationStep._metaclass.qualifiedName()


  # CCPN properties
  @property
  def _apiCalculationStep(self) -> ApiCalculationStep:
    """ CCPN CalculationStep matching CalculationStep"""
    return self._wrappedData

  @property
  def _key(self) -> str:
    """id string - serial number converted to string"""
    return str(self._wrappedData.serial)

  @property
  def serial(self) -> int:
    """serial number of CalculationStep, used in Pid and to identify the CalculationStep. """
    return self._wrappedData.serial
    
  @property
  def _parent(self) -> DataSet:
    """DataSet containing ccpn.RestraintList."""
    return  self._project._data2Obj[self._wrappedData.nmrConstraintStore]
  
  dataSet = _parent
  
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
  def scriptName(self) -> Optional[str]:
    """Name of script used for calculation"""
    return self._wrappedData.scriptName

  @scriptName.setter
  def scriptName(self, value:str):
    self._wrappedData.scriptName = value

  @property
  def script(self) -> Optional[str]:
    """Text of script used for calculation"""
    return self._wrappedData.script

  @script.setter
  def script(self, value:str):
    self._wrappedData.script = value
  
  @property
  def inputDataUuid(self) -> Optional[str]:
    """Universal identifier (uuid) for calculation input data set."""
    return self._wrappedData.inputDataUuid

  @inputDataUuid.setter
  def inputDataUuid(self, value:str):
    self._wrappedData.inputDataUuid = value

  @property
  def outputDataUuid(self) -> Optional[str]:
    """Universal identifier (uuid) for calculation output data set"""
    return self._wrappedData.outputDataUuid

  @outputDataUuid.setter
  def outputDataUuid(self, value:str):
    self._wrappedData.outputDataUuid = value

  @property
  def inputDataSet(self) -> Optional[DataSet]:
    """Calculation input data set."""
    uuid = self._wrappedData.inputDataUuid
    apiDataSet = self._project._wrappedData.findFirstNmrConstraintStore(uuid=uuid)
    if apiDataSet:
      return  self._project._data2Obj.get(apiDataSet)
    else:
      return None

  @inputDataSet.setter
  def inputDataSet(self, value:str):
    self._wrappedData.inputDataUuid = value if value is None else value.uuid

  @property
  def outputDataSet(self) -> Optional[DataSet]:
    """Calculation output data set."""
    uuid = self._wrappedData.outputDataUuid
    apiDataSet = self._project._wrappedData.findFirstNmrConstraintStore(uuid=uuid)
    if apiDataSet:
      return  self._project._data2Obj.get(apiDataSet)
    else:
      return None

  @outputDataSet.setter
  def outputDataSet(self, value:str):
    self._wrappedData.outputDataUuid = value if value is None else value.uuid



  @classmethod
  def _getAllWrappedData(cls, parent:DataSet)-> list:
    """get wrappedData - all ConstraintList children of parent NmrConstraintStore"""
    return parent._wrappedData.sortedCalculationSteps()

# Connections to parents:
DataSet._childClasses.append(CalculationStep)

def getter(self:DataSet) -> List[CalculationStep]:
  uuid = self.uuid
  return [x for x in self.project.calculationSteps if x.inputDataUuid == uuid]
DataSet.outputCalculationSteps = property(getter, None, None,
                          "ccpn.CalculationSteps (from other DataSets) that used DataSet as input")

def getter(self:DataSet) -> List[CalculationStep]:
  uuid = self.uuid
  return [x for x in self.calculationSteps if x.outputDataUuid == uuid]
DataSet.inputCalculationSteps = property(getter, None, None,
                          "ccpn.CalculationSteps (from this DataSet) that gave DataSet as output"
                          "\nNB there can be more than one, because the DataSet may result from\n"
                          "multiple calculations that do not have intermediate DataSets stored")
del getter

def _newCalculationStep(self:DataSet, programName:str=None, programVersion:str=None,
                        scriptName:str=None, script:str=None,
                        inputDataUuid:str=None, outputDataUuid:str=None,
                        inputDataSet:DataSet=None, outputDataSet:DataSet=None,) -> CalculationStep:
  """Create new ccpn.CalculationStep within ccpn.DataSet"""

  project = self.project
  programName = programName or project.programName

  if inputDataSet is not None:
    if inputDataUuid is None:
      inputDataUuid = inputDataSet.uuid
    else:
      raise ValueError("Either inputDataSet or inputDataUuid must be None - values were %s and %s"
                      % (inputDataSet, inputDataUuid))

  if outputDataSet is not None:
    if outputDataUuid is None:
      outputDataUuid = outputDataSet.uuid
    else:
      raise ValueError("Either outputDataSet or inputDataUuid must be None - values were %s and %s"
                      % (outputDataSet, outputDataUuid))


  obj = self._wrappedData.newCalculationStep(programName=programName, programVersion=programVersion,
                                             scriptName=scriptName, script=script,
                                             inputDataUuid=inputDataUuid,
                                             outputDataUuid=outputDataUuid)
  return project._data2Obj.get(obj)

DataSet.newCalculationStep = _newCalculationStep
del _newCalculationStep

# Notifiers:

