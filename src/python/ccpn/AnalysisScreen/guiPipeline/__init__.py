__author__ = 'Luca'

__all__ = []

import pkgutil as _pkgutil
import inspect as _inspect

for loader, name, isPpkg in _pkgutil.walk_packages(__path__):
  module = loader.find_module(name).load_module(name)
  for name, obj in _inspect.getmembers(module):
    if hasattr(obj, 'methodName'):
      __all__.append(obj)