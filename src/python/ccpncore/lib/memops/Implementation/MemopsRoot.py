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
import os
from ccpn.util import Path

def isProjectModified(self:'MemopsRoot') -> bool:
  """
  Checks whether any of project has been modified.
  """

  topObjects = (self,) + tuple(self.topObjects)

  for topObject in topObjects:
    if topObject.isModified:
      return True

  return False

def fetchDataUrl(self:'MemopsRoot', fullPath:str) -> 'DataUrl':
  """Get or create DataUrl that matches fullPath, prioritising insideData, alongsideDta, remoteData
  and existing dataUrls"""
  from ccpncore.api.memops.Implementation import Url
  standardStore = self.findFirstDataLocationStore(name='standard')
  fullPath = Path.normalisePath(fullPath, makeAbsolute=True)
  standardTags = ('insideData', 'alongsideData', 'remoteData')
  # Check standard DataUrls first
  checkUrls = [standardStore.findFirstDataUrl(name=tag) for tag in standardTags]
  # Then check other existing DataUrls
  checkUrls += [x for x in standardStore.sortedDataUrls() if x.name not in standardTags]
  for dataUrl in checkUrls:
    directoryPath = os.path.join(dataUrl.url.path, '')
    if fullPath.startswith(directoryPath):
      break
  else:
    # No matches found, make a new one
    dirName, path = os.path.split(fullPath)
    dataUrl = standardStore.newDataUrl(url=Url(path=dirName))
  #
  return dataUrl

def fetchNmrProject(self:'MemopsRoot', name:str=None) -> 'NmrProject':
  """Get existing NmrProject from MemopsRoot, or create one if there are no NmrProjects.

  If name i s passeed in, the function will return a matching NmrProject or throw an error
  If no name is passed, function takes the first nMrProject,
  or creates an NmrProject with same name as the project
  """

  nmrProjects = self.sortedNmrProjects()
  if nmrProjects:
    if name:
      nmrProject = self.findFirstNmrProject(name=name)
      if nmrProject is None:
        raise ValueError("No NmrProject found with name: %s" % name)
    else:
      nmrProject = nmrProjects[0]
  else:
    nmrProject = self.newNmrProject(name=name or self.name)

  return nmrProject