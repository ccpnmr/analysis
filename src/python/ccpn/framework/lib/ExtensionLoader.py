__author__ = 'TJ Ragan'

from ccpn.util.SubclassLoader import loadSubclasses



def getPipes(userExtensionPath=None):
  from ccpn.framework.PathsAndUrls import pipePath
  from ccpn.framework.lib.Pipe import Pipe

  loadedPipes = set()
  loadedPipes.update(loadSubclasses(pipePath, Pipe))
  if userExtensionPath is not None:
    sc = loadSubclasses(userExtensionPath, Pipe)
    loadedPipes.update(sc)
  return loadedPipes


def getPlugins(pluginPath):
  from ccpn.framework.lib.Plugin import Plugin
  loadedPlugins = set()
  loadedPlugins.update(loadSubclasses(pluginPath, Plugin))
  return loadedPlugins