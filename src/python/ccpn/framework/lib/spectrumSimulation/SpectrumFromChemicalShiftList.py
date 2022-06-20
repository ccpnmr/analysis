"""
This module defines the creation of a Simulated Spectrum from a ChemicalShift List
"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2022-06-20 19:34:52 +0100 (Mon, June 20, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-05-20 12:59:02 +0100 (Fri, May 20, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================



from ccpn.util.traits.CcpNmrTraits import Any, List, Bool, Odict, CString, CInt
from ccpn.util.Common import flattenLists
from ccpn.util.traits.TraitBase import TraitBase
from ccpn.util.traits.CcpNmrTraits import Any, List, Bool, Odict, CString
from ccpn.core.ChemicalShiftList import ChemicalShiftList, CS_ATOMNAME, CS_VALUE,\
    CS_NMRATOM, CS_NMRRESIDUE, CS_SEQUENCECODE, CS_CHAINCODE
from ccpn.framework.Application import getApplication
from ccpn.util.OrderedSet import OrderedSet
from ccpn.core.NmrResidue import NmrResidue, _getNmrResidue
import pandas as pd
from ccpn.core.lib.ContextManagers import undoStackBlocking, undoBlockWithoutSideBar, notificationEchoBlocking, PandasChainedAssignment
from ccpn.util.Logging import getLogger
from collections import OrderedDict




#--------------------------------------------------------------------------------------------
# ExperimentTypeSimulator class
#--------------------------------------------------------------------------------------------

class SimulatedSpectrumByExperimentTypeABC(TraitBase):

    #=========================================================================================
    # to be subclassed
    #=========================================================================================
    experimentType = None
    peakAtomNameMappers = [[],]
    isotopeCodes =  []
    axisCodes = []

    #=========================================================================================
    # end to be subclassed
    #=========================================================================================

    # traits
    application = Any(default_value=None, allow_none=True)


    #=========================================================================================
    # start of methods
    #=========================================================================================

    def __init__(self, chemicalShiftList, spectrumKwargs=None):
        super().__init__()
        self.chemicalShiftList = chemicalShiftList
        if not isinstance(self.chemicalShiftList, ChemicalShiftList):
            raise ValueError('Invalid chemicalShiftList "%s"' % chemicalShiftList)

        self.application = getApplication()
        self._spectrum = None
        self._spectrumKwargs = spectrumKwargs or {}
        self._initSpectrum()
        self._peakListIndex = -1

    @property
    def spectrum(self):
        return self._spectrum

    @property
    def peakList(self):
        return self._spectrum.peakLists[self._peakListIndex]

    def _initSpectrum(self):
        ''' init a new empty spectrum from the defined options
        '''
        name = self._spectrumKwargs.get('name', self.chemicalShiftList.name)
        spectrum = self.project.newEmptySpectrum(isotopeCodes=self.isotopeCodes, name=name)
        spectrum.chemicalShiftList =  self.chemicalShiftList
        spectrum.axisCodes = self.axisCodes
        spectrum.experimentType = self.experimentType
        self._spectrum = spectrum
        return spectrum

    @property
    def project(self):
        return self.application.project

    @classmethod
    def checkForValidExperimentType(cls, experimentType):
        """check if valid experimentType"""
        pass

    def _getAllRequiredAtomNames(self):
        values = [v._getAllAtomNames() for mm in self.peakAtomNameMappers for v in mm]
        return OrderedSet(flattenLists(values))

    def simulatePeakList(self):
        """ create new peaks based on the AtomNames defined in the Mapper. No check on offset."""

        data = self.chemicalShiftList._data
        requiredAtomNames = self._getAllRequiredAtomNames()
        ## filter CSL on the atomNames of interest
        data = data[data[CS_ATOMNAME].isin(requiredAtomNames)]
        # check if the nmrAtom exists in the project. it should!. create a new column nmrResidue because we need for groupby
        with PandasChainedAssignment():
            data[CS_NMRRESIDUE] = [self.project.getByPid(na).nmrResidue if self.project.getByPid(na) else None for na in
                               data[CS_NMRATOM]]
        # Filter any Rows where No NmrResidue
        data = data[data[CS_NMRRESIDUE].notna()]

        with undoBlockWithoutSideBar():
            with notificationEchoBlocking():
                for ix, filteredData in data.groupby(CS_NMRRESIDUE):
                    for mappers in self.peakAtomNameMappers:
                        # make a new Peak for each mapperGroup
                        peak = self.peakList.newPeak()
                        # loop through mappers to get the required atoms names  to fill the peak assignments and CS value
                        ppmPositions = []
                        for mapper in mappers:
                            for offset, requiredAtomName in mapper.offsetNmrAtomNames.items():
                                for rowCount, (localIndex, dataRow) in enumerate(filteredData.iterrows()):
                                    if requiredAtomName == dataRow[CS_ATOMNAME]:
                                        # get the right nmrAtom based on the offset. Cannot do yet @, @@, # and hardcoded offsets
                                        nmrAtomName = dataRow[CS_ATOMNAME]
                                        sequenceCode = dataRow[CS_SEQUENCECODE]
                                        try:
                                            sequenceCode = int(sequenceCode)
                                        except:
                                            getLogger().warn('Cannot deal yet with non-numerical nmrResidue sequenceCode. Skipping: %s' % sequenceCode)
                                            continue
                                        nmrChain = self.project.getNmrChain(dataRow[CS_CHAINCODE])
                                        if sequenceCode:
                                            sequenceCode += offset
                                        nmrResidue = _getNmrResidue(nmrChain, sequenceCode)
                                        if nmrResidue is not None:
                                            na = nmrResidue.getNmrAtom(nmrAtomName)
                                            if na:
                                                peak.assignDimension(mapper.axisCode, [na])
                                                # find the CS value based on the offset
                                                cs4naValues = data[data[CS_NMRATOM] == na.pid][CS_VALUE].values
                                                if len(cs4naValues) == 1:  # should be always present!?
                                                    ppmPositions.append(float(cs4naValues[0]))
                                        break
                        if len(ppmPositions) == self.spectrum.dimensionCount:
                            peak.ppmPositions = tuple(ppmPositions)
                        if len(ppmPositions) == 0:
                            peak.delete()

    def __str__(self):
        return f'<{self.__class__.__name__}>'

    __repr__ = __str__


#--------------------------------------------------------------------------------------------
# AtomNamesMapper class
#--------------------------------------------------------------------------------------------

class AtomNamesMapper(object):
    """
    A container to facilitate the nmrAtoms assignment mapping to a particular axisCode/dimension from a ChemicalShift
    """
    dimension           = None
    isotopeCode         = None
    axisCode            = None
    offsetNmrAtomNames  = {}


    def __init__(self, dimension=None, isotopeCode=None, axisCode=None, offsetNmrAtomNames=None, **kwargs):
        """
        :param kwargs:
            dimension:      int. Dimension number (starting from 1)
            isotopeCode:    str. e.g.:'1H'. Used to define the EmptySpectrum isotopeCodes list
            axisCode:       str. any allowed. Used to define the EmptySpectrum axisCodes list
            offsetNmrAtomNames:  dict, key-value.
                                -Key: offset definition, int  e.g.: 0 to define as "i"; -1 to define as "i-1".
                                -Value: string to be used for fetching nmrAtom (i) and assign using the defined axisCode
        """
        super().__init__()
        if dimension:
            self.dimension = dimension
        if isotopeCode:
            self.isotopeCode = isotopeCode
        if axisCode:
            self.axisCode = axisCode
        if offsetNmrAtomNames:
         self.offsetNmrAtomNames = offsetNmrAtomNames
        self._kwargs = {v:getattr(self, v, None) for v in dir(self) if not v.startswith('_')}
        self._kwargs.update(**kwargs)

    def _getAllAtomNames(self):
        return list(self.offsetNmrAtomNames.values())


    def __str__(self):
        return f'<{self.__class__.__name__}> : {self._kwargs}'

    __repr__ = __str__


class HAtomNamesMapper(AtomNamesMapper):

    dimension           = 1
    isotopeCode         = '1H'
    axisCode            = 'Hn'
    offsetNmrAtomNames  = {0: 'H'}

class NAtomNamesMapper(AtomNamesMapper):

    dimension           = 2
    isotopeCode         = '15N'
    axisCode            = 'Nh'
    offsetNmrAtomNames  = {0: 'N'}

class COAtomNamesMapper(AtomNamesMapper):

    dimension           = 3
    isotopeCode         = '13C'
    axisCode            = 'C'
    offsetNmrAtomNames  = {0: 'C'}

class COM1AtomNamesMapper(AtomNamesMapper):

    dimension           = 3
    isotopeCode         = '13C'
    axisCode            = 'C'
    offsetNmrAtomNames  = {-1: 'C'}

class CAAtomNamesMapper(AtomNamesMapper):

    dimension           = 3
    isotopeCode         = '13C'
    axisCode            = 'C'
    offsetNmrAtomNames  = {0: 'CA'}

class CAM1AtomNamesMapper(AtomNamesMapper):

    dimension           = 3
    isotopeCode         = '13C'
    axisCode            = 'C'
    offsetNmrAtomNames  = {-1: 'CA'}

class CBAtomNamesMapper(AtomNamesMapper):

    dimension           = 3
    isotopeCode         = '13C'
    axisCode            = 'C'
    offsetNmrAtomNames  = {0: 'CB'}

class CBM1AtomNamesMapper(AtomNamesMapper):

    dimension           = 3
    isotopeCode         = '13C'
    axisCode            = 'C'
    offsetNmrAtomNames  = {-1: 'CB'}


#--------------------------------------------------------------------------------------------
# The Various ExperimentType classes
#--------------------------------------------------------------------------------------------
#
# Subclass of SimulatedSpectrumByExperimentTypeABC to allow customised behaviour/implementation
#
#--------------------------------------------------------------------------------------------
# 1D ExperimentTypes
#--------------------------------------------------------------------------------------------

class SimulatedSpectrum_1H(SimulatedSpectrumByExperimentTypeABC):

    experimentType = 'H'
    isotopeCodes = ['1H']
    axisCodes = ['H']
    peakAtomNameMappers = [
        [AtomNamesMapper(dimension=1, isotopeCode='1H', axisCode='H', offsetNmrAtomNames={0:'H'})]
        ]



#--------------------------------------------------------------------------------------------
# 2D ExperimentTypes
#--------------------------------------------------------------------------------------------

class SimulatedSpectrum_15N_HSQC(SimulatedSpectrumByExperimentTypeABC):

    experimentType = '15N HSQC/HMQC'
    isotopeCodes = ['1H', '15N']
    axisCodes = ['Hn', 'Nh']
    peakAtomNameMappers = [
                            [
                            HAtomNamesMapper(),
                            NAtomNamesMapper()
                            ],
                          ]


#--------------------------------------------------------------------------------------------
# 3D ExperimentTypes
#--------------------------------------------------------------------------------------------

class SimulatedSpectrum_HNCO(SimulatedSpectrumByExperimentTypeABC):

    experimentType = 'HNCO'
    isotopeCodes = ['1H', '13C', '15N']
    axisCodes = ['Hn', 'C', 'Nh']
    peakAtomNameMappers = [
                            [
                            HAtomNamesMapper(),
                            COM1AtomNamesMapper(),
                            NAtomNamesMapper()
                            ]
                        ]


class SimulatedSpectrum_HNCACO(SimulatedSpectrumByExperimentTypeABC):

    experimentType = 'HNCACO'
    isotopeCodes = ['1H', '13C', '15N']
    axisCodes = ['Hn', 'C', 'Nh']
    peakAtomNameMappers = [
                            ## first peak assignments
                            [
                                HAtomNamesMapper(),
                                COAtomNamesMapper(),
                                NAtomNamesMapper(),
                            ],
                            ## second peak assignments
                            [
                                HAtomNamesMapper(),
                                COM1AtomNamesMapper(),
                                NAtomNamesMapper()
                            ]
                            ## end peak assignments
                            ]

class SimulatedSpectrum_HNCA(SimulatedSpectrumByExperimentTypeABC):

    experimentType  = 'HNCA'
    isotopeCodes    = ['1H', '13C', '15N']
    axisCodes       = ['Hn', 'C', 'Nh']
    peakAtomNameMappers = [
                            ## first peak assignments
                            [
                            HAtomNamesMapper(),
                            CAAtomNamesMapper(),
                            NAtomNamesMapper()
                            ],
                            ## second peak assignments
                            [
                            HAtomNamesMapper(),
                            CAM1AtomNamesMapper(),
                            NAtomNamesMapper(),
                            ]
                            ## end peak assignments
                         ]

class SimulatedSpectrum_HNCOCA(SimulatedSpectrumByExperimentTypeABC):

    experimentType  = 'HNCOCA'
    isotopeCodes    = ['1H', '13C', '15N']
    axisCodes       = ['Hn', 'C', 'Nh']
    peakAtomNameMappers = [
                            ## first peak assignments
                            [
                            HAtomNamesMapper(),
                            CAM1AtomNamesMapper(),
                            NAtomNamesMapper(),
                            ]
                            ## end peak assignments
                         ]

class SimulatedSpectrum_HNCACB(SimulatedSpectrumByExperimentTypeABC):

    experimentType  = 'HNCA/CB'
    isotopeCodes    = ['1H', '13C', '15N']
    axisCodes       = ['Hn', 'C', 'Nh']
    peakAtomNameMappers = [
                            ## first peak assignments: CA (i)
                            [
                            HAtomNamesMapper(),
                            CAAtomNamesMapper(),
                            NAtomNamesMapper(),
                            ],
                            ## second peak assignments CB (i)
                            [
                            HAtomNamesMapper(),
                            CBAtomNamesMapper(),
                            NAtomNamesMapper(),
                            ],
                            ## third peak assignments: CA (i-1)
                            [
                            HAtomNamesMapper(),
                            CAM1AtomNamesMapper(),
                            NAtomNamesMapper(),
                            ],
                            ## forth peak assignments CB (i-1)
                            [
                            HAtomNamesMapper(),
                            CBM1AtomNamesMapper(),
                            NAtomNamesMapper(),
                            ]
                         ]



#--------------------------------------------------------------------------------------------
#  Register the Various ExperimentType classes
#--------------------------------------------------------------------------------------------

CSL2SPECTRUM_DICT = OrderedDict([
                            (SimulatedSpectrum_1H.experimentType, SimulatedSpectrum_1H),
                            (SimulatedSpectrum_15N_HSQC.experimentType, SimulatedSpectrum_15N_HSQC),
                            (SimulatedSpectrum_HNCO.experimentType, SimulatedSpectrum_HNCO),
                            (SimulatedSpectrum_HNCA.experimentType, SimulatedSpectrum_HNCA),
                            (SimulatedSpectrum_HNCOCA.experimentType, SimulatedSpectrum_HNCOCA),
                            (SimulatedSpectrum_HNCACB.experimentType, SimulatedSpectrum_HNCACB),
                            ])
