from ccpn.core.lib.Version import applicationVersion
from ccpn.ui.gui.AppBase import defineProgramArguments, AppBase

applicationName = 'Screen'


class Screen(AppBase):
  """Root class for Screen application"""

  def __init__(self, applicationName, applicationVersion, commandLineArguments):
    AppBase.__init__(self, applicationName, applicationVersion, commandLineArguments)
    self.components.add('Screen')


if __name__ == '__main__':

  # argument parser
  parser = defineProgramArguments()

  # add any additional commandline argument here
  commandLineArguments = parser.parse_args()

  program = Screen(applicationName, applicationVersion, commandLineArguments)
  program.start()
