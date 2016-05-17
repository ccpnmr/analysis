"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - : 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                 " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = ": rhfogh $"
__date__ = ": 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = ": 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================


from PyQt4 import QtGui, QtCore

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList

class SetupNmrResiduesPopup(QtGui.QDialog, Base):
  def __init__(self, parent=None, project=None, **kw):
    super(SetupNmrResiduesPopup, self).__init__(parent)
    Base.__init__(self, **kw)
    self.parent = parent
    self.project = project
    label1a = Label(self, text="Source PeakList ", grid=(0, 0))
    self.peakListPulldown = PulldownList(self, grid=(0, 1))
    self.peakListPulldown.setData([peakList.pid for peakList in project.peakLists
      if peakList.spectrum.experimentType == 'H[N]' or peakList.spectrum.experimentType == 'H[N[CO]]'])
    label1a = Label(self, text="NmrChain ", grid=(0, 2))
    self.nmrChainPulldown = PulldownList(self, grid=(0, 3))
    self.nmrChainPulldown.setData([nmrChain.pid for nmrChain in project.nmrChains])
    newWidget = QtGui.QWidget()
    newWidget.setLayout(QtGui.QGridLayout())
    self.assignmentCheckBox = CheckBox(newWidget)
    assignmentLabel = Label(newWidget, "Keep existing assignments")
    newWidget.layout().addWidget(self.assignmentCheckBox, 0, 0)
    newWidget.layout().addWidget(assignmentLabel, 0, 1)
    self.layout().addWidget(newWidget, 1, 0, 1, 2)

    self.buttonBox = ButtonList(self, grid=(1, 3), texts=['Cancel', 'Ok'],
                                callbacks=[self.reject, self._setupNmrResidues])


  def _setupNmrResidues(self):
    peakList = self.project.getByPid(self.peakListPulldown.currentText())
    nmrChain = self.project.getByPid(self.nmrChainPulldown.currentText())
    keepAssignments = self.assignmentCheckBox.checkState()
    isotopeCodes = peakList.spectrum.isotopeCodes
    axisCodes = peakList.spectrum.axisCodes
    if (isotopeCodes.count('1H') == 1 and isotopeCodes.count('15N') == 1):
      ndim = isotopeCodes.index('15N')
      hdim = isotopeCodes.index('1H')
      for peak in peakList.peaks:
        if not keepAssignments or not any(len(dimensionNmrAtoms) > 0 for dimensionNmrAtoms in peak.dimensionNmrAtoms):
          r = nmrChain.newNmrResidue()
          a = r.fetchNmrAtom(name='N')
          a2 = r.fetchNmrAtom(name='H')
          peak.assignDimension(axisCode=axisCodes[ndim], value=a)
          peak.assignDimension(axisCode=axisCodes[hdim], value=a2)
    else:
      self.project._logger.warning('''Incompatible peak list selected. Only experiments with one 1H dimension
      and one 15N dimension can be used.''')
      return


    self.accept()
