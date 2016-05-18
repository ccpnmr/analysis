from argparse import Namespace as argparseNamespace
from ccpn.util.Namespace import Namespace


def setupSettings(options: argparseNamespace=None,
                  preferences: argparseNamespace=None) -> Namespace:
  settings = Namespace()
  settings.language = 'English-UK'
  settings.autoBackupOnOpen = False
  settings.autoSaveOnQuit = True
  settings.autoSaveLayoutOnQuit = True
  settings.auxiliaryFilesPath = '~/.ccpn'
  settings.macroPath = '/home/ccpn/code/svnsf/trunk/ccpnv3/python/ccpn/macros/'
  settings.editor = 'default'
  settings.colourScheme = 'dark'
  settings.license = ''
  settings.toolbarHidden = False
  settings.recentMacros = []
  settings.spectra = _spectraNamespace()
  settings.recentFiles = []

  for ns in [preferences, options]:
    if ns is not None:
      ns = vars(ns)
      for k, v in ns.items():
        setattr(settings, k, v)

  return settings


def _spectraNamespace()-> Namespace:
  spectra = Namespace()
  spectra.keepExternal = True
  spectra.brukerTemplates = "pdata/*"
  spectra.nmrPipeTemplates = "*ft*"  # TODO: Should this be *.ft* ?
  spectra.ucsfTemplates = ["*.ucsf", "*.UCSF"]
  return spectra