"""
This file contains functionalities implementing Spectrum prototype definitions

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
__dateModified__ = "$dateModified: 2017-07-07 16:33:14 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2017-04-07 10:28:48 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import math
from collections import Counter
from ccpn.util.traits.CcpNmrJson import CcpNmrJson, CcpnJsonDirectoryABC
from ccpn.util.traits.CcpNmrTraits import Unicode, Int, Float, Bool

from ccpn.framework.PathsAndUrls import ccpnConfigPath
from ccpn.util.Path import aPath
from ccpn.util.decorators import singleton


class DimensionObject(object):
    """
    Class to define a dimension, a (possible) measurement along the magnetization transfer
    pathway of the experiment.
    Key attributes:
    - dimensionIndex: Dimension 'index' (0-based), needs to be unique
    - isotopeCodes:   IsotopeCode tuple (for MQ!), typically len=1
    - dimensionType   One of {'JCoupling', 'MQShift', 'Shift', 'T1', 'T1rho', 'T1zz', 'T2'}
    """
    def __init__(self, dimensionIndex, isotopeCodes=(), dimensionType='Shift', axisCode=None):
        """Initialise the object"""
        self.dimensionIndex = dimensionIndex # Dimension 'index' (0-based)
        self.isotopeCodes = isotopeCodes      # isotopeCode tuple (for MQ!), typically len=1, use isotopeCode property
        self.dimensionType = dimensionType    # one of {'JCoupling', 'MQShift', 'Shift', 'T1', 'T1rho', 'T1zz', 'T2'}
        if axisCode is None:
            axisCode = self._defaultAxisCode()
        self.axisCode = axisCode

        self.parent = None          # link to SpectrumPrototype instance

    def _defaultAxisCode(self):
        """Return a default axisCode"""
        if self.isotopeCode is not None:
            _tmp = self.isotopeCode
            # strip any leading digits
            while len(_tmp) > 0 and _tmp[0:1].isnumeric():
                _tmp = _tmp[1:]
            axisCode = '%s_%s' % (_tmp, self.dimensionIndex)
        else:
            axisCode = '%s_%s' % ('Dim', self.dimensionIndex)
        return axisCode

    @property
    def isotopeCode(self):
        """Return the first of isotopeCodes or None if undefined
        """
        if len(self.isotopeCodes) == 0:
            return None
        else:
            return self.isotopeCodes[0]

    def __str__(self):
        return '<Dim-%s (%s): %s,%s>' % (self.dimensionIndex, self.axisCode, self.isotopeCode, self.dimensionType)

    __repr__ = __str__


class ExperimentGraph(object):
    """Class to encode the 'prior' information on steps and transfers
    """
    def __init__(self, steps=(), transfers=(), sign=1.0):
        self.steps = steps          # A tuple of dimension indices (dim1, dim2, dim3, ...)
        self.transfers = transfers  # (dim1, dim2, transferType) tuple with transferType one of
                                    # {'Jcoupling', 'Jmultibond', None, 'onebond', 'relayed', 'relayed-alternate',
                                    #  'through-space'}
        self.sign = sign            # sign of resulting peak

        self.parent = None          # link to SpectrumPrototype instance

    def __str__(self):
        return '<ExperimentGraph: %d steps; %d transfers>' % (len(self.steps), len(self.transfers))

    __repr__ = __str__


class SpectrumPrototype(object):
    """Class to encapsulate the spectrum prototype for a particular NMR experiment with its
    possible nD variants. It has a name and systematic (CcpNmr) name

    A prototype is defined by:
    - A list of Dimension objects, defining the (possible) measurements along the magentization pathway
    - A list of nD experiments, each defined as a tuple of n-Dimension objects
    - A list of ExperimentGraph objects (terminology from V2, composed of steps and transfer tuples),
      each defining a possible peak
    """

    currentIndx = 0

    def __init__(self, ccpnName, name):

        self.indx = SpectrumPrototype.currentIndx
        SpectrumPrototype.currentIndx += 1

        self.ccpnName = ccpnName
        if name is None:
            name = ccpnName
        self.name = name

        self.dimensionObjects = []  # list of DimensionObject's
        self.experiments = []       # list of nD experiments, each defined as (dim1, dim2, ...) tuples
        self.experimentGraphs = []  # list of ExperimentGraph instances

    def addExperimentGraph(self, experimentGraph):
        if not isinstance(experimentGraph, ExperimentGraph):
            raise ValueError('invalid type of experimentGraph argument')
        experimentGraph.parent = self
        self.experimentGraphs.append(experimentGraph)

    def addDimension(self, dimensionObject):
        if not isinstance(dimensionObject, DimensionObject):
            raise ValueError('invalid type of dimensionObject argument')
        dimensionObject.parent = self
        self.dimensionObjects.append(dimensionObject)

    def getDimension(self, dimensionIndex):
        """get the DimensionObject corresponding to the dimension index (0-based)
        """
        dimDict = dict((d.dimensionIndex, d) for d in self.dimensionObjects)
        return dimDict.get(dimensionIndex)

    def __str__(self):
        return '<SpectrumPrototype %d: %s>' % (self.indx, self.name)

    __repr__ = __str__


def extractFromAtomSites(atomSites):
    return tuple(a.isotopeCode for a in atomSites)

def extractFromExpMeasurement(e):
    """Return a tuple from ExpMeasurement instance
    """
    result = (str(e), e.measurementType, extractFromAtomSites(e.atomSites))
    return result

def extractFromRefExperiment(refExp, updateAxisCodes=False):
    "Extract the dimensional info from refExperiment; return list of Dimension Objects"
    expDims = []
    for dim in refExp.orderedDimensions:
    # for dim in refExp.sortedRefExpDims():
        _e = list(dim.refExpDimRefs)[0].expMeasurement
        _id, tType, isotopes = extractFromExpMeasurement(_e)
        d = dimensionsMap.get(_id)
        if d is None:
            raise RuntimeError('dim %s, error getting %s, %s, %s' % (dim.dim, _id, tType, isotopes))
        if updateAxisCodes:
            d.axisCode = dim.axisCode
        expDims.append(d)
    return expDims

def extractStepsFromGraph(graph):
    """Extract the steps; return list of Dimension objects"""
    # [(s.stepNumber, extractFromExpMeasurement(s.expMeasurement)) for s in graph.sortedExpSteps()]
    steps = []
    for s in graph.sortedExpSteps():
        _id, tType, isotopes = extractFromExpMeasurement(s.expMeasurement)
        d = dimensionsMap.get(_id)
        if d is None:
            raise RuntimeError('error getting %s, %s, %s' % (_id, tType, isotopes))
        steps.append(d)
    return steps

def remediateTransferList(experimentPrototype, steps, transfers) -> list:
    """Adjust transfers list for 'missing' parts; rework the transfers into something more sensible: i.e.
    a (dim1, dim2, transferType) tuple for every step pair. Hence, if there are n steps there should be
    n-1 transfers.

    Transfers between identical dims are None; i.e. (dim1, dim1, None)
    Transfers to/from a dimension encoding a 'delay' (e.g. for T1 or T2 relaxation experiments), are None

    Original transfers lacked:
    - transfers for steps between identical dimensions
    - transfers for dim2 --> dim1 if dim1 --> dim2 was already defined
    - transfers to a dimension encoding a 'delay'
    """
    tIndex = 0
    newTransfers = []
    transferMap = {}
    for sIndex, dim1 in enumerate(steps[0:-1]):
        dim2 = steps[sIndex+1]
        dimension1 = experimentPrototype.getDimension(dim1)
        if dimension1 is None:
            raise RuntimeError('Error getting dimension %r' % dim1)
        dimension2 = experimentPrototype.getDimension(dim2)
        if dimension2 is None:
            raise RuntimeError('Error getting dimension %r' % dim2)

        if dim2 == dim1:
            newTransfers.append( (dim1, dim2, None) )
        elif (dim1,dim2) in transferMap:
            newTransfers.append( (dim1, dim2, transferMap[(dim1, dim2)]) )
        elif (dim2,dim1) in transferMap:
            newTransfers.append( (dim1, dim2, transferMap[(dim2, dim1)]) )
        elif len(transfers) == 0:
            newTransfers.append( (dim1, dim2, None) )
        elif dimension1.axisCode == 'delay' or dimension2.axisCode == 'delay':
            newTransfers.append( (dim1, dim2, None) )
        else:
            if tIndex >= len(transfers):
                # something went wrong!
                tType = 'ERROR'
                errorList.add(prototype)
            else:
                tType = transfers[tIndex][0]
                tIndex += 1
            newTransfers.append( (dim1, dim2, tType) )
            transferMap[(dim1,dim2)] = tType
    return newTransfers

#=============================================================================================================

apiExps = project._wrappedData.root.sortedNmrExpPrototypes()

errorList = set()
spectrumPrototypes = []

# tests = apiExps[0:10] + apiExps[-10:]
# tests = [apiExps[i] for i in  (154, 112, 261, 93, 55, 114, 76, 105)]
# for i, exp in enumerate(tests):
for i, apiExp in enumerate(apiExps):

    prototype = SpectrumPrototype(ccpnName=apiExp.name, name=apiExp.synonym)

    print('=== %s ===' % prototype)
    print('\t\tccpnName:              %s' % prototype.ccpnName)

    # isotopeCodes = [a.isotopeCode for a in list(apiExp.atomSites)]
    # print('\t\tisotopes (%d):          %s' % (len(isotopeCodes), isotopeCodes))

    # Create DimensionObject's and the map
    dimensionsMap = {}
    for dIndx, e in enumerate(apiExp.sortedExpMeasurements()):
        _id, tType, isotopes = extractFromExpMeasurement(e)
        d = DimensionObject(dimensionIndex=dIndx, isotopeCodes=isotopes, dimensionType=tType)
        prototype.addDimension(d)
        dimensionsMap[_id] = d

    # find experiment with higest number of dimensions
    refExperiments = list(apiExp.refExperiments)
    rIndex = max( (len(r.orderedDimensions), i) for i, r in enumerate(refExperiments))[1]
    refExp = refExperiments[rIndex]
    expDims = extractFromRefExperiment(refExp, updateAxisCodes=True)

    # now the dimensions have been updated with axisCodes; print them
    print('\t\tdimensions (%d):        %s' % (len(prototype.dimensionObjects), prototype.dimensionObjects))

    # get and print all the experiments
    for rIndex, refExp in enumerate(refExperiments):
        expDims = extractFromRefExperiment(refExp, updateAxisCodes=False)
        dims = tuple(e.dimensionIndex for e in expDims)
        string = '-'.join(str(e.axisCode) for e in expDims)
        prototype.experiments.append( dims )
        print('\t\texperiment_%d (%dD):     %s   %r' % (rIndex, len(dims), string, dims))
    print()

    # Get the ExpGraph's; these seem to encode the peaks?
    # there are eight ExpPrototype's that give errors here: (154, 112, 261, 93, 55, 114, 76, 105);
    # most likely because their original defs were wrong
    for gIndex, graph in enumerate(apiExp.expGraphs):
        steps = [d.dimensionIndex for d in extractStepsFromGraph(graph)]
        print('\t\t(%d,%d) steps (%d):        %s' % (i, gIndex, len(steps), steps))
        transfers = [(t.transferType, extractFromAtomSites(t.atomSites)) for t in graph.sortedExpTransfers()]
        print('\t\t(%d,%d) transfers (%d):    %s' % (i, gIndex, len(transfers), transfers))

        newTransfers = remediateTransferList(prototype, steps, transfers)
        print('\t\t(%d,%d) newTransfers (%d): %s' % (i, gIndex, len(newTransfers), newTransfers))

        gr = ExperimentGraph(steps=steps, transfers=newTransfers, sign=graph.peakSign)
        prototype.addExperimentGraph(gr)

        print()

    spectrumPrototypes.append(prototype)

