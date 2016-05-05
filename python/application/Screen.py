

from application.core.AppBase import defineProgramArguments, AppBase
from ccpn.lib.Version import applicationVersion

applicationName = 'Screen'


class Screen(AppBase):
  """Root class for Assign application"""

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
