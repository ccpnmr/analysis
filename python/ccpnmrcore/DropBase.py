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

from ccpnmrcore.Base import Base as GuiBase

from ccpncore.lib.Io.FastaIo import parseFastaFile, isFastaFormat

class DropBase(GuiBase):
  
  def __init__(self, appBase, dropCallback, *args, **kw):
    
    GuiBase.__init__(self, appBase, *args, **kw)
    self.dropCallback = dropCallback
    
  def dragEnterEvent(self, event):
    event.accept()


  def dropEvent(self, event):
    event.accept()
    if isinstance(self.parent, QtGui.QGraphicsScene):
      event.ignore()
      return

    if event.mimeData().urls():
      filePaths = [url.path() for url in event.mimeData().urls()]

      if filePaths:
        for filePath in filePaths:
          try:
            if isFastaFormat(filePath):
              sequences = parseFastaFile(filePaths[0])
              for sequence in sequences:
                self._appBase.project.makeSimpleChain(sequence=sequence[1], compoundName=sequence[0],
                                                      molType='protein')

          except:
            try:
              spectrum = self._appBase.project.loadSpectrum(filePath)
              self._appBase.mainWindow.leftWidget.addSpectrum(spectrum)
              self.dropCallback(spectrum)
            except:
                pass

    if event.mimeData().hasFormat('application/x-strip'):
      data = event.mimeData().data('application/x-strip')
      pidData = str(data.data(),encoding='utf-8')
      pidData = [ch for ch in pidData if 32 < ord(ch) < 127]  # strip out junk
      actualPid = ''.join(pidData)
      wrapperObject = self.getById(actualPid)
      self.dropCallback(wrapperObject)
    else:
      data = event.mimeData().data('application/x-qabstractitemmodeldatalist')
      pidData = str(data.data(),encoding='utf-8')
      pidData = [ch for ch in pidData if 32 < ord(ch) < 127]  # strip out junk
      actualPid = ''.join(pidData)
      wrapperObject = self.getObject(actualPid)
      self.dropCallback(wrapperObject)

  def rhfDropEvent(self, event):
    """Catch dropEvent and dispatch to processing"""

    from ccpnmrCore.util import Qt as qtUtil

    event.accept()

    dataType, data = qtUtil.interpretEvent(event)

    if dataType and data:
      self.processDropData(data, dataType)


  def rhfProcessDropData(self, data, dataType='pids'):
    """ Digest dropped-in data
    Separate so it can be called from command line as well.
    """
    from ccpnmrCore.util import Qt as qtUtil

    if dataType == 'pids':
      # data is list-of-pids
      commonType = qtUtil.getCommonType(data)
      func = self.pickDispatchFunction('digest', commonType)
      if func:
        func(data)

    elif dataType == 'ccpnmr-io':
      # Importing (duplicating) wrapper objects from (another) project
      raise NotImplementedError("CCPN data import not yet implemented")

    elif dataType == 'urls':
      # data is list-of-urls

      urlType, urlInfo = qtUtil.analyseUrls(data)
      # urlInfo is list of triplets of (type, subType, modifiedUrl),
      # e.g. ('spectrum', 'Bruker', newUrl)

      multifunc = None if len(data) <= 1 else self.pickDispatchFunction('multiload', urlType)

      if multifunc is None:
        pids = []
        for fileType, subType, useUrl in urlInfo:
          func = self.pickDispatchFunction('load', fileType)
          if func:
            ll = func(useUrl, subType=subType)
            if ll:
              pids.extend(ll)

      else:
        pids = multifunc(urlInfo)

      commonType = qtUtil.getCommonType(pids)
      func = self.pickDispatchFunction('digest', commonType)
      if func:
        func(pids)

    elif type == 'text':
      # data is a text string
      self.digestText(data)


def pickDispatchFunction(self, prefix, dataType):
  """Generate file name and return bound method matching name, if defined"""

  funcName = prefix + dataType

  if hasattr(self, funcName):
    return getattr(self, funcName)
  else:
    return None