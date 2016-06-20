__author__ = 'TJ'

from ccpn.framework.lib.SvnRevision import applicationVersion
from ccpn.framework.Framework import defineProgramArguments
from ccpn.Assign.Assign import Assign


if __name__ == '__main__':

  # argument parser
  parser = defineProgramArguments()

  # add any additional commandline argument here
  commandLineArguments = parser.parse_args()

  program = Assign('Assign', applicationVersion, commandLineArguments)
  program.start()
