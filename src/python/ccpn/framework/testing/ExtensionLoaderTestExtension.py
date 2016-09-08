__author__ = 'TJ Ragan'


from ccpn.framework.lib.Extension import ExtensionABC



class Hair(ExtensionABC):
  METHODNAME = 'Useless Extension 1'

  def runMethod(self, dataset):
    return 1



class Fingernail(ExtensionABC):
  METHODNAME = 'Useless Extension 1'

  def runMethod(self, dataset):
    return 2



class UselessNotExtension1:
  METHODNAME = 'Useless Not Extension 1'

  def runMethod(self, dataset):
    return



class UselessNotExtension2:
  METHODNAME = 'Useless Not Extension 2'

  def runMethod(self, dataset):
    return
