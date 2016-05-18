__author__ = 'TJ'

from ccpn.core.lib.Version import applicationVersion
from ccpn.framework.Framework import defineProgramArguments, Framework

applicationName = 'Metabolomics'


class Metabolomics(Framework):
  """Root class for Metabolomics application"""
  def __init__(self, applicationName, applicationVersion, commandLineArguments):
    Framework.__init__(self, applicationName, applicationVersion, commandLineArguments)
    self.components.add('Metabolomics')


if __name__ == '__main__':

  # argument parser
  parser = defineProgramArguments()

  # add any additional commandline argument here
  commandLineArguments = parser.parse_args()

  program = Metabolomics(applicationName, applicationVersion, commandLineArguments)
  program.start()
