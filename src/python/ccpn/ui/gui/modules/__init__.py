

def importCcpnModules(modulesDict):
  '''
  moduleDict = Dict with module name class: guiModule name
  return a list with imported CCPN gui Modules
  '''
  CcpnModules = []
  import pkgutil as _pkgutil
  import inspect as _inspect
  for clsName, ccpnModuleName in modulesDict.items():
    for loader, name, isPpkg in _pkgutil.walk_packages(__path__):
      module = loader.find_module(name).load_module(name)
      for name, obj in _inspect.getmembers(module):
        if clsName == name:
          CcpnModules.append(obj)
  return CcpnModules

