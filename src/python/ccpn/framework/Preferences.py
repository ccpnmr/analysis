import argparse
import os
import json
import shutil

from ccpn.framework.languages import languages, defaultLanguage
from ccpn.util import Path


DOTFILENAME = 'v3preferences.json'

def defaultPreferencesPath():
  return os.path.join(Path.getTopDirectory(), 'config', 'defaultv3settings.json')


def homeDotfileLocation() -> str:
  homeDir = os.path.expanduser('~')
  ccpnDir = os.path.join(homeDir, '.ccpn')
  return ccpnDir


def homeDotfileName() -> str:
  return os.path.join(homeDotfileLocation(), DOTFILENAME)



def getDotfilePreferences(dotfilePath=None) -> dict:
  if dotfilePath is None:
    dotfilePath = homeDotfileName()
    if not os.path.isfile(dotfilePath):
      initializeUserPreferencesDotfile(dotfilePath)
  with open(dotfilePath) as f:
    dotfilePreferences = json.load(f)

  return dotfilePreferences


def initializeUserPreferencesDotfile(dotfilePath, overwrite=False):
  os.makedirs(os.path.dirname(dotfilePath))
  shutil.copyfile(defaultPreferencesPath(), dotfilePath)


def getCommandLineOptions(parser:argparse.ArgumentParser) -> dict:
  args = parser.parse_args()
  argsAsDict = vars(args)
  return argsAsDict


def commandLineArguementParser() -> argparse.ArgumentParser:
  '''
  Define the arguments of the program
  return argparse instance
  '''

  parser = argparse.ArgumentParser(description='Process startup arguments')

  # for component in componentNames:
  #   parser.add_argument('--'+component.lower(), dest='include'+component, action='store_true',
  #                                               help='Show %s component' % component.lower())
  parser.add_argument('--language',
                      help='Language for menus, etc.; valid options = (' +
                           '|'.join(languages) + '); default='+defaultLanguage,
                      default=defaultLanguage)
  parser.add_argument('--skip-user-preferences',
                      dest='skipUserPreferences',
                      action='store_true',
                      help='Skip loading user preferences'
                     )
  parser.add_argument('--nologging',
                      dest='nologging',
                      action='store_true',
                      help='Do not log information to a file'
                     )
  parser.add_argument('projectPath',
                      nargs='?',
                      help='Project path'
                     )

  return parser


def getInstalledLanguages() -> tuple:
  return (None,)
