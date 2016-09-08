__author__ = 'TJ Ragan'

from ccpn.util.SubclassLoader import loadSubclasses



def getExtensions(userExtensionPath=None):
  from ccpn.framework.PathsAndUrls import extensionPath
  from ccpn.framework.lib.Extension import ExtensionABC

  loadedSubclasses = set()
  loadedSubclasses.update(loadSubclasses(extensionPath, ExtensionABC))
  if userExtensionPath is not None:
    sc = loadSubclasses(userExtensionPath, ExtensionABC)
    loadedSubclasses.update(sc)
  return loadedSubclasses

