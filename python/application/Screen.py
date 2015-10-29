from application.core.AppBase import startProgram
from application.core.AppBase import AppBase
from application.core.Version import applicationVersion

applicationName = 'Screen'

class Screen(AppBase):
  pass
if __name__ == '__main__':
  import argparse

  parser = argparse.ArgumentParser(description='Process startup arguments')
  parser.add_argument('--language', help='Language for menus, etc.')
  parser.add_argument('projectPath', nargs='?', help='Project path')
  args = parser.parse_args()
  startProgram(Screen, applicationName, applicationVersion, args.projectPath, args.language)
