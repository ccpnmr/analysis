__author__ = 'TJ'

from ccpn.core.lib.Version import applicationVersion
from ccpn.framework.Framework import defineProgramArguments
from ccpn.Screen.AnalysisScreen import Screen


if __name__ == '__main__':

  # argument parser
  parser = defineProgramArguments()

  # add any additional commandline argument here
  commandLineArguments = parser.parse_args()

  program = Screen('Screen', applicationVersion, commandLineArguments)
  program.start()

