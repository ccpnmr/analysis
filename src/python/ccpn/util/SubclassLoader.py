__author__ = 'TJ Ragan'

import os
import sys
import importlib
import inspect



def loadSubclasses(path: str, baseclass) -> set:
  '''
  Gather subclasses of baseclass from path

  This attempts to import any file in the directory that doesn't start with a period or underscore,
  Then checks each class definition in that imported module for subclasses of the specified baseclass
  and finally returns the set of all classes it found.
  '''

  extensions = []
  savedPythonPath = sys.path
  try:
    sys.path = [path]
    moduleFiles = os.listdir(path)
    moduleFiles = [f for f in moduleFiles if not f.startswith('_')]
    moduleFiles = [f for f in moduleFiles if not f.startswith('.')]
    moduleFiles = [os.path.splitext(f)[0] for f in moduleFiles]
    for f in moduleFiles:
      try:  # Fails on non-python files, directories, etc,...
        module = importlib.import_module(f)
        potentials = inspect.getmembers(module, inspect.isclass)
        for name, p in potentials:
          if issubclass(p, baseclass):
            if p.__module__ == f:  # Make sure we only import classes declared in that module.
              extensions.append(p)
      except ImportError:
        pass
  finally:
    sys.path = savedPythonPath
  return set(extensions)
