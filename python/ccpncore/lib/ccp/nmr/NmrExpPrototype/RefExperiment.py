"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
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


from ccpncore.util import Graph
import collections

def magnetisationTransferDict(self) -> dict:
  """returns {frozenset((refExpDimRef1, refExpDimRef2)):(transferType:str, isIndirect:bool}

  The transferType describes the shortest transfer path (from the longest ExpTransfer object)
  that does not go via another RefExpDimRef present in the RefExperiment.

  transfertype is one of (in order of decreasing priority):
 'through-space', 'relayed-alternate', 'relayed',  'Jmultibond', 'Jcoupling', 'onebond',
  isIndirect is used where there is more than one successive transfer step;
   it is combined with the highest-priority transferType in the transfer path

  The function caches graph representation and results, so will not give updated results if you
  modify the ExpPrototype between calls (but that should never happen anyway).
  """

  TypePriorityOrder = ['through-space', 'relayed-alternate', 'relayed',  'Jmultibond',
                       'Jcoupling', 'onebond',]

  if hasattr(self, '_magnetisationTransferDict'):
    return self._magnetisationTransferDict

  else:
    nmrExpPrototype = self.nmrExpPrototype

    if hasattr(nmrExpPrototype, '_atomSiteGraph'):
      graph = nmrExpPrototype._atomSiteGraph

    else:
      # Make atomSite graph and save it in the nmrExpPrototype

      # Heuristic - pick the longest ExpGraph
      expGraph = nmrExpPrototype.sortedExpGraphs()[0]    # There will be at least one, for ral data
      expGraphLength = len(expGraph.expTransfers)
      for xg in nmrExpPrototype.sortedExpGraphs()[1:]:
        length = len(xg.expTransfers)
        if length > expGraphLength:
          expGraphLength = length
          expGraph = xg

      # Make graph from ExpTransfers
      graph = {}
      for expTransfer in expGraph.expTransfers:
        atomSites = list(expTransfer.atomSites)
        transferType = expTransfer.transferType
        if transferType:
          for ii in range(2):
            dd = graph.setdefault(atomSites[0], {})
            dd[atomSites[1]] = transferType
            atomSites.reverse()
      #
      nmrExpPrototype._atomSiteGraph = graph

    # Set up for making results dictionary
    site2Rxdr = collections.OrderedDict()
    for rxd in self.sortedRefExpDims():
      for rxdr in rxd.sortedRefExpDimRefs():
        atomSites = list(rxdr.expMeasurement.atomSites)
        if len(atomSites) == 1:
          # Ignore RefExpDimRef that do not match a single AtomSite
          # NB these will be unique in practice for Atomsite graph data
          site2Rxdr[atomSites[0]] = rxdr

    # Make results dictionary
    result = {}
    sites = list(site2Rxdr)
    for ii,site in enumerate(sites[:-1]):
      costDict, predecessorDict = Graph.minimumStepPath(graph, site)

      for site2 in sites[ii+1:]:

        path = [site2]
        while path[-1] != site:
          path.append(predecessorDict[path[-1]])
        path.reverse()

        if not any(x in site2Rxdr for x in path[1:-1]):
          # Transfer does not go via one of the other dimension atomSites. OK.
          costs = costDict[site2]
          if len(costs) == 1:
            transferType = costs[0]
            isIndirect = False

          else:
            isIndirect = True
            for ss in TypePriorityOrder:
              if ss in costs:
                transferType = ss
                break
            else:
              raise ValueError("Unknown transferType in RefExperiment: %s" % costs)
          #
          result[frozenset((site2Rxdr[site], site2Rxdr[site2]))] = (transferType, isIndirect)
    #
    self._magnetisationTransferDict = result
    return result