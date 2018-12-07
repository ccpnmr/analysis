"""
Module documentation here
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
__dateModified__ = "$dateModified: 2017-07-07 16:32:27 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


from typing import Optional, List
import collections
from ccpnmodel.ccpncore.api.ccp.nmr.NmrConstraint import CalculationStep as ApiCalculationStep
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.DataSet import DataSet
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, deleteObject, ccpNmrV3CoreSetter, logCommandBlock
from ccpn.util.Logging import getLogger


class CalculationStep(AbstractWrapperObject):
    """CalculationStep information, for tracking successive calculations.
    Ordered from oldest to newest"""

    #: Short class name, for PID.
    shortClassName = 'DC'
    # Attribute it necessary as subclasses must use superclass className
    className = 'CalculationStep'

    _parentClass = DataSet

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
        """DataSet containing RestraintList."""
        return self._project._data2Obj[self._wrappedData.nmrConstraintStore]

    dataSet = _parent

    @property
    def programName(self) -> str:
        """Name of program doing calculation"""
        return self._wrappedData.programName

    @programName.setter
    def programName(self, value: str):
        self._wrappedData.programName = value

    @property
    def programVersion(self) -> Optional[str]:
        """Version of program doing calculation"""
        return self._wrappedData.programVersion

    @programVersion.setter
    def programVersion(self, value: str):
        self._wrappedData.programVersion = value

    @property
    def scriptName(self) -> Optional[str]:
        """Name of script used for calculation"""
        return self._wrappedData.scriptName

    @scriptName.setter
    def scriptName(self, value: str):
        self._wrappedData.scriptName = value

    @property
    def script(self) -> Optional[str]:
        """Text of script used for calculation"""
        return self._wrappedData.script

    @script.setter
    def script(self, value: str):
        self._wrappedData.script = value

    @property
    def inputDataUuid(self) -> Optional[str]:
        """Universal identifier (uuid) for calculation input data set."""
        return self._wrappedData.inputDataUuid

    @inputDataUuid.setter
    def inputDataUuid(self, value: str):
        self._wrappedData.inputDataUuid = value

    @property
    def outputDataUuid(self) -> Optional[str]:
        """Universal identifier (uuid) for calculation output data set"""
        return self._wrappedData.outputDataUuid

    @outputDataUuid.setter
    def outputDataUuid(self, value: str):
        self._wrappedData.outputDataUuid = value

    @property
    def inputDataSet(self) -> Optional[DataSet]:
        """Calculation input data set."""
        uuid = self._wrappedData.inputDataUuid
        apiDataSet = self._project._wrappedData.findFirstNmrConstraintStore(uuid=uuid)
        if apiDataSet:
            return self._project._data2Obj.get(apiDataSet)
        else:
            return None

    @inputDataSet.setter
    def inputDataSet(self, value: str):
        self._wrappedData.inputDataUuid = value if value is None else value.uuid

    @property
    def outputDataSet(self) -> Optional[DataSet]:
        """Calculation output data set."""
        uuid = self._wrappedData.outputDataUuid
        apiDataSet = self._project._wrappedData.findFirstNmrConstraintStore(uuid=uuid)
        if apiDataSet:
            return self._project._data2Obj.get(apiDataSet)
        else:
            return None

    @outputDataSet.setter
    def outputDataSet(self, value: str):
        self._wrappedData.outputDataUuid = value if value is None else value.uuid

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: DataSet) -> list:
        """get wrappedData - all ConstraintList children of parent NmrConstraintStore"""
        return parent._wrappedData.sortedCalculationSteps()

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    #===========================================================================================
    # new'Object' and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================

#=========================================================================================
# Connections to parents:
#=========================================================================================

def getter(self: DataSet) -> List[CalculationStep]:
    uuid = self.uuid
    return [x for x in self.project.calculationSteps if x.inputDataUuid == uuid]


DataSet.outputCalculationSteps = property(getter, None, None,
                                          "ccpn.CalculationSteps (from other DataSets) that used DataSet as input")


def getter(self: DataSet) -> List[CalculationStep]:
    uuid = self.uuid
    return [x for x in self.calculationSteps if x.outputDataUuid == uuid]


DataSet.inputCalculationSteps = property(getter, None, None,
                                         "ccpn.CalculationSteps (from this DataSet) that yielded DataSet as output"
                                         "\nNB there can be more than one, because the DataSet may result from\n"
                                         "multiple calculations that do not have intermediate DataSets stored")
del getter


@newObject(CalculationStep)
def _newCalculationStep(self: DataSet, programName: str = None, programVersion: str = None,
                        scriptName: str = None, script: str = None,
                        inputDataUuid: str = None, outputDataUuid: str = None,
                        inputDataSet: DataSet = None, outputDataSet: DataSet = None, serial: int = None) -> CalculationStep:
    """Create new CalculationStep within DataSet.

    See the CalculationStep class for details.

    :param programName:
    :param programVersion:
    :param scriptName:
    :param script:
    :param inputDataUuid:
    :param outputDataUuid:
    :param inputDataSet:
    :param outputDataSet:
    :param serial: optional serial number.
    :return: a new CalculationStep instance.
    """

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
    result = project._data2Obj.get(obj)
    if result is None:
        raise RuntimeError('Unable to generate new CalculationStep item')

    if serial is not None:
        try:
            result.resetSerial(serial)
        except ValueError:
            self.project._logger.warning("Could not reset serial of %s to %s - keeping original value"
                                         % (result, serial))

    return result


#EJB 20181204: moved to DataSet
# DataSet.newCalculationStep = _newCalculationStep
# del _newCalculationStep

# Notifiers:
