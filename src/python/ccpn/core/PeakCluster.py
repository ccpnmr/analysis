"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:29 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.Peak import Peak
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import PeakCluster as apiPeakCluster
from typing import Optional, Tuple, Any, Sequence, Union
from ccpn.util.Common import makeIterableList
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, undoBlock
from ccpn.util.Logging import getLogger


class PeakCluster(AbstractWrapperObject):
    """PeakCluster object, holding position, intensity, and assignment information.

    Measurements that require more than one NmrAtom for an individual assignment
    (such as  splittings, J-couplings, MQ dimensions, reduced-dimensionality
    experiments etc.) are not supported (yet). Assignments can be viewed and set
    either as a list of assignments for each dimension (dimensionNmrAtoms) or as a
    list of all possible assignment combinations (assignedNmrAtoms).
    """

    #: Short class name, for PID.
    shortClassName = 'PC'
    # Attribute it necessary as subclasses must use superclass className
    className = 'PeakCluster'

    _parentClass = Project

    #: Name of plural link to instances of class
    _pluralLinkName = 'peakClusters'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = apiPeakCluster._metaclass.qualifiedName()

    # CCPN properties
    @property
    def _apiPeakCluster(self) -> apiPeakCluster:
        """ API peakClusters matching PeakCluster"""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """id string - serial number converted to string"""
        return str(self._wrappedData.serial)

    @property
    def serial(self) -> int:
        """serial number of PeakCluster, used in Pid and to identify the PeakCluster. """
        return self._wrappedData.serial

    @property
    def _parent(self) -> Optional['Project']:
        """parent containing peakCluster."""
        return self._project._data2Obj[self._wrappedData.nmrProject]

    peakClusterParent = _parent

    @property
    def annotation(self) -> Optional[str]:
        """Peak text annotation"""
        return self._wrappedData.annotation

    @annotation.setter
    def annotation(self, value: str):
        self._wrappedData.annotation = value

    @property
    def peaks(self) -> Optional[Tuple[Any]]:
        """List of peaks attached to the peakCluster"""
        try:
            return tuple([self._project._data2Obj[pk] for pk in self._wrappedData.sortedPeaks()])
        except:
            return None

    @property
    def numPeaks(self) -> int:
        """return number of peaks in the peakCluster"""
        return len(self._wrappedData.sortedPeaks())

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: 'Project') -> Tuple[apiPeakCluster]:
        """get wrappedData (PeakClusters) for all PeakCluster children of parent PeakClusterList"""
        return parent._wrappedData.sortedPeakClusters()

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    @logCommand(get='self')
    def addPeaks(self, peaks: Sequence[Union['Peak', str]]):
        """
        Add a peak or list of peaks to the peakCluster.
        The peaks must belong to the spectrum containing the multipletList.

        :param peaks: single peak or list of peaks, as objects or pid strings.
        """
        peakList = makeIterableList(peaks)
        pks = []
        for peak in peakList:
            pks.append(self.project.getByPid(peak) if isinstance(peak, str) else peak)

        for pp in pks:
            if not isinstance(pp, Peak):
                raise TypeError('%s is not of type Peak' % pp)

        with undoBlock():
            for pk in pks:
                self._wrappedData.addPeak(pk._wrappedData)

    @logCommand(get='self')
    def removePeaks(self, peaks: Sequence[Union['Peak', str]]):
        """
        Remove a peak or list of peaks from the peakCluster.
        The peaks must belong to the peakCluster.

        :param peaks: single peak or list of peaks, as objects or pid strings.
        """
        peakList = makeIterableList(peaks)
        pks = []
        for peak in peakList:
            pks.append(self.project.getByPid(peak) if isinstance(peak, str) else peak)

        for pp in pks:
            if not isinstance(pp, Peak):
                raise TypeError('%s is not of type Peak' % pp)
            if pp not in self.peaks:
                raise ValueError('%s does not belong to peakCluster: %s' % (pp.pid, self.pid))

        with undoBlock():
            for pk in pks:
                self._wrappedData.removePeak(pk._wrappedData)

#===========================================================================================
# new'Object' and other methods
# Call appropriate routines in their respective locations
#===========================================================================================


#=========================================================================================
# Connections to parents:
#=========================================================================================

@newObject(PeakCluster)
def _newPeakCluster(self: Project, peaks: Sequence[Union['Peak', str]] = None, serial: int = None) -> PeakCluster:
    """Create new PeakCluster.

    See the PeakCluster class for details.

    :param peaks: optional list of peaks as objects or pids.
    :param serial: optional serial number.
    :return: a new PeakCluster instance.
    """

    apiParent = self._wrappedData
    if peaks:
        apiPeakCluster = apiParent.newPeakCluster(clusterType='multiplet',
                                                  peaks=[p._wrappedData for p in peaks])
    else:
        apiPeakCluster = apiParent.newPeakCluster(clusterType='multiplet')

    result = self._project._data2Obj.get(apiPeakCluster)
    if result is None:
        raise RuntimeError('Unable to generate new PeakCluster item')

    if serial is not None:
        try:
            result.resetSerial(serial)
        except ValueError:
            getLogger().warning("Could not reset serial of %s to %s - keeping original value"
                                % (result, serial))

    return result

#EJB 20181205: moved to Project
# PeakCluster._parentClass.newPeakCluster = _newPeakCluster
# del _newPeakCluster
