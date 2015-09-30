"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
from PyQt4 import QtGui, QtCore

from ccpncore.util import Pid
from ccpncore.lib.Io import Formats as ioFormats
from ccpnmrcore.Base import Base as GuiBase
from ccpncore.lib.Io import Formats as ioFormats

# Filled in lower down
pidTypeMap = {}

class DropBase(GuiBase):

  def __init__(self, appBase, *args, **kw):
  # def __init__(self, appBase, dropCallback, *args, **kw):

    GuiBase.__init__(self, appBase, *args, **kw)
    # self.dropCallback = dropCallback

    # This should NOT be there - use self._appBase (set in GuiBase)
    #self.appBase = appBase

  def dragEnterEvent(self, event):
    event.accept()

  def dropEvent(self, event):
    """Catch dropEvent and dispatch to processing"""


    from ccpnmrcore.util import Qt as qtUtil

    event.accept()
    print(event)

    data, dataType  = qtUtil.interpretEvent(event)

    if data and dataType:
      self.processDropData(data, dataType)

  # def dropEvent(self, event):
  #   """NBNB FIXME, must be commented out"""
  #   event.accept()
  #   if isinstance(self.parent, QtGui.QGraphicsScene):
  #     event.ignore()
  #     return
  #
  #   if event.mimeData().urls():
  #     filePaths = [url.path() for url in event.mimeData().urls()]
  #
  #     if filePaths:
  #       for filePath in filePaths:
  #         try:
  #           if isFastaFormat(filePath):
  #             sequences = parseFastaFile(filePaths[0])
  #             for sequence in sequences:
  #               self._appBase.project.makeSimpleChain(sequence=sequence[1], compoundName=sequence[0],
  #                                                     molType='protein')
  #
  #         except:
  #           try:
  #             if filePath.endswith('.spc.par'):
  #               # NBNB TBD HACK: Should be handle properly
  #               filePath = filePath[:-4]
  #             spectrum = self._appBase.project.loadSpectrum(filePath)
  #             if spectrum is not None:
  #               self._appBase.mainWindow.leftWidget.addSpectrum(spectrum)
  #               self.dropCallback(spectrum)
  #           except:
  #               pass
  #
  #   if event.mimeData().hasFormat('application/x-strip'):
  #     data = event.mimeData().data('application/x-strip')
  #     pidData = str(data.data(),encoding='utf-8')
  #     pidData = [ch for ch in pidData if 32 < ord(ch) < 127]  # strip out junk
  #     actualPid = ''.join(pidData)
  #     wrapperObject = self.getByPid(actualPid)
  #     self.dropCallback(wrapperObject)
  #   else:
  #     data = event.mimeData().data('application/x-qabstractitemmodeldatalist')
  #     pidData = str(data.data(),encoding='utf-8')
  #     pidData = [ch for ch in pidData if 32 < ord(ch) < 127]  # strip out junk
  #     actualPid = ''.join(pidData)
  #     wrapperObject = self.getObject(actualPid)
  #     self.dropCallback(wrapperObject)


  def processDropData(self, data, dataType='pids'):
    """ Process dropped-in data
    Separate function so it can be called from command line as well.
    """

    project = self._appBase.project

    if dataType == 'text':
      # data is a text string
      if hasattr(self, 'processText'):
        self.processText(data)

    else:
      pids = []
      if dataType == 'pids':
        pids = data


      elif dataType == 'urls':
        # data is list-of-urls
        # Load Urls one by one with normal loaders
        for url in data:
          ll = project.loadData(url)
          if ll:
            pids.extend(x.pid for x in ll)

      else:
        raise ValueError("processDropData does not recognise dataType %s" % dataType)


      # process pids
      for pid in pids:
        method = self.selectDispatchFunction('process', pid)
        if method:
          method(pid)

      # for pid in pids:
      #   if 'SP:' in pid:
      #     spectrum = self.getByPid(pid)
      #     self._appBase.mainWindow.sideBar.addSpectrum(spectrum)




  def selectDispatchFunction(self, prefix:str, dataType:(str,Pid)):
    """Generate file name and return bound method matching name, if defined
    dataType may be either an accepted dataType, or a Pid that is used to derive it.

    Accepted prefixes are 'process', currently
    DataTypes are singular, e.g. Spectrum, Peak, etc. even """

    if not pidTypeMap:
      # NBNB TBD FIXME: Import of ccpnmr should not be allowed here.
      # It will not break when put in function,but in theory ccpnmrcdore should not depend on ccpnmr
      import ccpn
      import ccpnmr
      for package in ccpn, ccpnmr:
        for tag in dir(package):
          obj = getattr(package, tag)
          if hasattr(obj, 'shortClassName'):
            shortClassName = getattr(obj, 'shortClassName')
            if shortClassName:
              pidTypeMap[shortClassName] = (obj.className if hasattr(obj, 'className')
                                            else obj.__class__.__name__)

    ss = dataType.split(Pid.PREFIXSEP,1)[0]
    ss = pidTypeMap.get(ss, ss)
    funcName = prefix + ss

    if hasattr(self, funcName):
      print(funcName)
      return getattr(self, funcName)
    else:

      return None
