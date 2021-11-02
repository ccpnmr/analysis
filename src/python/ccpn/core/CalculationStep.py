"""
Module documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-11-02 18:40:28 +0000 (Tue, November 02, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


from typing import Optional, List

from ccpnmodel.ccpncore.api.ccp.nmr.NmrConstraint import CalculationStep as ApiCalculationStep
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.StructureData import StructureData
from ccpn.core.lib.ContextManagers import newObject


class CalculationStep(AbstractWrapperObject):
    """CalculationStep information, for tracking successive calculations.
    Ordered from oldest to newest"""

    #: Short class name, for PID.
    shortClassName = 'DC'
    # Attribute it necessary as subclasses must use superclass className
    className = 'CalculationStep'

    _parentClass = StructureData

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
    def _parent(self) -> StructureData:
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
    def inputStructureData(self) -> Optional[StructureData]:
        """Calculation input data set."""
        uuid = self._wrappedData.inputDataUuid
        apiDataSet = self._project._wrappedData.findFirstNmrConstraintStore(uuid=uuid)
        if apiDataSet:
            return self._project._data2Obj.get(apiDataSet)
        else:
            return None

    @inputStructureData.setter
    def inputStructureData(self, value: str):
        self._wrappedData.inputDataUuid = value if value is None else value.uuid

    @property
    def outputStructureData(self) -> Optional[StructureData]:
        """Calculation output data set."""
        uuid = self._wrappedData.outputDataUuid
        apiDataSet = self._project._wrappedData.findFirstNmrConstraintStore(uuid=uuid)
        if apiDataSet:
            return self._project._data2Obj.get(apiDataSet)
        else:
            return None

    @outputStructureData.setter
    def outputStructureData(self, value: str):
        self._wrappedData.outputDataUuid = value if value is None else value.uuid

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: StructureData) -> list:
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

def getter(self: StructureData) -> List[CalculationStep]:
    uuid = self.uuid
    return [x for x in self.project.calculationSteps if x.inputDataUuid == uuid]


StructureData.outputCalculationSteps = property(getter, None, None,
                                          "ccpn.CalculationSteps (from other DataSets) that used DataSet as input")


def getter(self: StructureData) -> List[CalculationStep]:
    uuid = self.uuid
    return [x for x in self.calculationSteps if x.outputDataUuid == uuid]


StructureData.inputCalculationSteps = property(getter, None, None,
                                         "ccpn.CalculationSteps (from this DataSet) that yielded DataSet as output"
                                         "\nNB there can be more than one, because the DataSet may result from\n"
                                         "multiple calculations that do not have intermediate DataSets stored")
del getter


#=========================================================================================


@newObject(CalculationStep)
def _newCalculationStep(self: StructureData, programName: str = None, programVersion: str = None,
                        scriptName: str = None, script: str = None,
                        inputDataUuid: str = None, outputDataUuid: str = None,
                        inputStructureData: StructureData = None, outputStructureData: StructureData = None) -> CalculationStep:
    """Create new CalculationStep within StructureData.

    See the CalculationStep class for details.

    :param programName:
    :param programVersion:
    :param scriptName:
    :param script:
    :param inputDataUuid:
    :param outputDataUuid:
    :param inputStructureData:
    :param outputStructureData:
    :return: a new CalculationStep instance.
    """

    project = self.project
    programName = programName or project.application.applicationName

    if inputStructureData is not None:
        if inputDataUuid is None:
            inputDataUuid = inputStructureData.uuid
        else:
            raise ValueError("Either inputStructureData or inputDataUuid must be None - values were %s and %s"
                             % (inputStructureData, inputDataUuid))

    if outputStructureData is not None:
        if outputDataUuid is None:
            outputDataUuid = outputStructureData.uuid
        else:
            raise ValueError("Either outputStructureData or inputDataUuid must be None - values were %s and %s"
                             % (outputStructureData, outputDataUuid))

    obj = self._wrappedData.newCalculationStep(programName=programName, programVersion=programVersion,
                                               scriptName=scriptName, script=script,
                                               inputDataUuid=inputDataUuid,
                                               outputDataUuid=outputDataUuid)
    result = project._data2Obj.get(obj)
    if result is None:
        raise RuntimeError('Unable to generate new CalculationStep item')

    return result


#EJB 20181204: moved to DataSet
# DataSet.newCalculationStep = _newCalculationStep
# del _newCalculationStep

# Notifiers:
