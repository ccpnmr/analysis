__author__ = 'TJ'

from ccpn.ui.gui.AppBase import defineProgramArguments, AppBase
from ccpn.lib.Version import applicationVersion


applicationName = 'Metabolomics'


class Metabolomics(AppBase):
  """Root class for Assign application"""

  def __init__(self, applicationName, applicationVersion, commandLineArguments):
    AppBase.__init__(self, applicationName, applicationVersion, commandLineArguments)
    self.components.add('Metabolomics')


if __name__ == '__main__':

  # argument parser
  parser = defineProgramArguments()

  # add any additional commandline argument here
  commandLineArguments = parser.parse_args()

  program = Metabolomics(applicationName, applicationVersion, commandLineArguments)
  program.start()
