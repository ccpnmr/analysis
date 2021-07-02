"""
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
__dateModified__ = "$dateModified: 2021-07-02 13:03:48 +0100 (Fri, July 02, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import datetime
from typing import Optional

from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpnmodel.ccpncore.api.ccp.nmr.NmrConstraint import NmrConstraintStore as ApiNmrConstraintStore
from ccpnmodel.ccpncore.api.ccp.nmr.NmrConstraint import FixedResonance as ApiFixedResonance
from ccpn.core.lib import Pid
from ccpn.core.lib.ContextManagers import newObject, renameObject
from ccpn.util.decorators import logCommand
from ccpn.util.isotopes import name2IsotopeCode
from ccpn.util.Logging import getLogger


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
        #return str(self._wrappedData.serial)
        #return str(self.title)+'_'+str(self.serial)
        return self.name.translate(Pid.remapSeparators)  # Title should not be unique

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
        """Title of DataSet.
        """
        getLogger().warning('Deprecated, please use DataSet.name')
        return self.name

    @title.setter
    def title(self, value: str):
        """Set title of the DataSet.
        """
        getLogger().warning('Deprecated, please use DataSet.name')
        self.name = value

    @property
    def name(self) -> str:
        """Name of DataSet.
        """
        # Reading V2 project resulted in name being None; create one on the fly
        if self._wrappedData.name is None:
            # needed to stop recursion of generating unique names
            name = DataSet._uniqueApiName(self.project)
            self._wrappedData.__dict__['name'] = name  # The only way to access this

        return self._wrappedData.name

    @name.setter
    def name(self, value: str):
        self.rename(value)

    @property
    def programName(self) -> str:
        """Name of program performing the calculation
        """
        return self._none2str(self._wrappedData.programName)

    @programName.setter
    def programName(self, value: str):
        self._wrappedData.programName = self._str2none(value)

    @property
    def programVersion(self) -> Optional[str]:
        """Version of program performing the calculation
        """
        return self._none2str(self._wrappedData.programVersion)

    @programVersion.setter
    def programVersion(self, value: str):
        self._wrappedData.programVersion = self._str2none(value)

    @property
    def dataPath(self) -> Optional[str]:
        """File path where dataSet is stored"""
        return self._none2str(self._wrappedData.dataPath)

    @dataPath.setter
    def dataPath(self, value: str):
        self._wrappedData.dataPath = self._str2none(value)

    @property
    def creationDate(self) -> Optional[datetime.datetime]:
        """Creation timestamp for DataSet"""
        return self._wrappedData.creationDate

    @creationDate.setter
    def creationDate(self, value: datetime.datetime):
        self._wrappedData.creationDate = self._str2none(value)

    @property
    def uuid(self) -> Optional[str]:
        """Universal identifier for dataSet"""
        return self._none2str(self._wrappedData.uuid)

    @uuid.setter
    def uuid(self, value: str):
        self._wrappedData.uuid = self._str2none(value)

    def _fetchFixedResonance(self, assignment: str, checkUniqueness: bool = True) -> ApiFixedResonance:
        """Fetch FixedResonance matching assignment string, creating anew if needed.

        If checkUniqueness is False the uniqueness of FixedResonance assignments will
        not be checked. NB, the odd duplicate should not be a major problem."""

        apiNmrConstraintStore = self._wrappedData

        tt = [x or None for x in Pid.splitId(assignment)]
        if len(tt) != 4:
            raise ValueError("assignment %s must have four dot-separated fields" % tt)

        dd = {
            'chainCode'   : tt[0],
            'sequenceCode': tt[1],
            'residueType' : tt[2],
            'name'        : tt[3]
            }

        if checkUniqueness:
            result = apiNmrConstraintStore.findFirstFixedResonance(**dd)
        else:
            result = None

        if result is None:
            dd['isotopeCode'] = name2IsotopeCode(tt[3]) or '?'
            result = apiNmrConstraintStore.newFixedResonance(**dd)
        #
        return result

    def _getTempItemMap(self) -> dict:
        """Get itemString:FixedResonance map, used as optional input for
        RestraintContribution.addRestraintItem(), as a faster alternative to
        calling _fetchFixedResonance (above). No other uses expected.
        Since FixedResonances are in principle mutable, this map should
        be used for a single series of creation operations (making or loading
        a set of restraint lists) and then discarded."""

        result = {}
        for fx in self._wrappedData.fixedResonances:
            ss = '.'.join(x or '' for x in (fx.chainCode, fx.sequenceCode, fx.residueType, fx.name))
            result[ss] = fx
        #
        return result

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: Project) -> list:
        """get wrappedData for all NmrConstraintStores linked to NmrProject"""
        return parent._wrappedData.sortedNmrConstraintStores()

    @renameObject()
    @logCommand(get='self')
    def rename(self, value: str):
        """Rename DataSet, changing its name and Pid.
        NB, the serial remains immutable.
        """
        return self._rename(value)

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    #===========================================================================================
    # new'Object' and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================

    @logCommand(get='self')
    def newRestraintList(self, restraintType, name: str = None, origin: str = None,
                         comment: str = None, unit: str = None, potentialType: str = 'unknown',
                         tensorMagnitude: float = 0.0, tensorRhombicity: float = 0.0,
                         tensorIsotropicValue: float = 0.0, tensorChainCode: str = None,
                         tensorSequenceCode: str = None, tensorResidueType: str = None,
                         restraintItemLength=None, **kwds):
        """Create new RestraintList of type restraintType within DataSet.

        See the RestraintList class for details.

        Optional keyword arguments can be passed in; see RestraintList._newRestraintList for details.

        :param restraintType:
        :param name:
        :param origin:
        :param comment:
        :param unit:
        :param potentialType:
        :param tensorMagnitude:
        :param tensorRhombicity:
        :param tensorIsotropicValue:
        :param tensorChainCode:
        :param tensorSequenceCode:
        :param tensorResidueType:
        :param restraintItemLength:
        :return: a new RestraintList instance.
        """
        from ccpn.core.RestraintList import _newRestraintList

        return _newRestraintList(self, restraintType, name=name, origin=origin,
                                 comment=comment, unit=unit, potentialType=potentialType,
                                 tensorMagnitude=tensorMagnitude, tensorRhombicity=tensorRhombicity,
                                 tensorIsotropicValue=tensorIsotropicValue, tensorChainCode=tensorChainCode,
                                 tensorSequenceCode=tensorSequenceCode, tensorResidueType=tensorResidueType,
                                 restraintItemLength=restraintItemLength, **kwds)

    @logCommand(get='self')
    def newCalculationStep(self, programName: str = None, programVersion: str = None,
                           scriptName: str = None, script: str = None,
                           inputDataUuid: str = None, outputDataUuid: str = None,
                           inputDataSet=None, outputDataSet=None, **kwds):
        """Create new CalculationStep within DataSet.

        See the CalculationStep class for details.

        Optional keyword arguments can be passed in; see CalculationStep._newCalculationStep for details.

        :param programName:
        :param programVersion:
        :param scriptName:
        :param script:
        :param inputDataUuid:
        :param outputDataUuid:
        :param inputDataSet:
        :param outputDataSet:
        :return: a new CalculationStep instance.
        """
        from ccpn.core.CalculationStep import _newCalculationStep

        return _newCalculationStep(self, programName=programName, programVersion=programVersion,
                                   scriptName=scriptName, script=script,
                                   inputDataUuid=inputDataUuid, outputDataUuid=outputDataUuid,
                                   inputDataSet=inputDataSet, outputDataSet=outputDataSet,
                                   **kwds)

    @logCommand(get='self')
    def newData(self, name: str, attachedObjectPid: str = None,
                attachedObject: AbstractWrapperObject = None, **kwds):
        """Create new Data within DataSet.

        See the Data class for details.

        Optional keyword arguments can be passed in; see Data._newData for details.

        :param name:
        :param attachedObjectPid:
        :param attachedObject:
        :return: a new Data instance.
        """
        from ccpn.core.Data import _newData

        return _newData(self, name=name, attachedObjectPid=attachedObjectPid,
                        attachedObject=attachedObject, **kwds)


#=========================================================================================
# Connections to parents:
#=========================================================================================

@newObject(DataSet)
def _newDataSet(self: Project, name: str = None, title: str = None, programName: str = None, programVersion: str = None,
                dataPath: str = None, creationDate: datetime.datetime = None, uuid: str = None,
                comment: str = None) -> DataSet:
    """Create new DataSet

    See the DataSet class for details.

    :param name:
    :param programName:
    :param programVersion:
    :param dataPath:
    :param creationDate:
    :param uuid:
    :param comment:
    :return: a new DataSet instance.
    """

    if title and name:
        raise TypeError('Cannot create new DataSet with title and name; DataSet.title is deprecated, please use DataSet.name')
    if title:
        getLogger().warning('DataSet.title is deprecated, please use DataSet.name')
        name = title

    name = DataSet._uniqueName(project=self, name=name)

    nmrProject = self._wrappedData

    if programName is not None and not isinstance(programName, str):
        raise TypeError("programName must be a string")
    if programVersion is not None and not isinstance(programVersion, str):
        raise TypeError("programName must be a string")

    apiNmrConstraintStore = nmrProject.root.newNmrConstraintStore(nmrProject=nmrProject,
                                                                  name=name,
                                                                  programName=programName,
                                                                  programVersion=programVersion,
                                                                  dataPath=dataPath,
                                                                  creationDate=creationDate,
                                                                  uuid=uuid,
                                                                  details=comment)
    result = self._data2Obj.get(apiNmrConstraintStore)
    if result is None:
        raise RuntimeError('Unable to generate new DataSet item')

    return result
