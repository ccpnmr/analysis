"""General graph handling code

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
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
from typing import Tuple

def minimumStepPath(graph:dict, startNode, endNode=None) -> Tuple[dict,dict]:
  """ Minimum-step-path by breadth-first traversal, inspired by Dijkstras algorithm
  Each edge has the same weight; among paths of the same length
  the function selects the first encountered. Breadth-first search guarantees that
  the paths with fewest steps are encountered first.

  Input:
  graph is given in form {node:{node:edgeInfo}}
  nodes can be any object that can be used as a dictionary key

  Output:
  (costDict, predecessorDict) tuple, where
  costDict is {node:Tuple[edgeInfo, ...]}, with the edgeInfo along the path from start to node
  predecessorDict is {node:predecessor} the predecessor of node in the shortest path from start
  """
  costDict = {startNode:tuple()}
  predecessorDict = {}
  traversal = [startNode]

  for node in traversal:
    cost = costDict[node]
    if node == endNode:
      break
    for node2, edgeInfo in graph[node].items():
      if node2 not in traversal:
        costDict[node2] = cost + (edgeInfo,)
        predecessorDict[node2] = node
        traversal.append((node2))
  #
  return costDict, predecessorDict
