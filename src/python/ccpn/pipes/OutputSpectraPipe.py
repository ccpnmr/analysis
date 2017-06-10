#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

#### GUI IMPORTS

from ccpn.ui.gui.widgets.PipelineWidgets import GuiPipe
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from PyQt4 import QtGui
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.FileDialog import LineEditButtonDialog



#### NON GUI IMPORTS
from ccpn.framework.lib.Pipe import SpectraPipe
from ccpn.util.Hdf5 import convertDataToHdf5


########################################################################################################################
##########################################      ALGORITHM       ########################################################
########################################################################################################################





########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################

# TODO: all the pipe!

class OutputPipelineGuiPipe(GuiPipe):

  preferredPipe = True
  pipeName = 'Output Pipeline'

  def __init__(self, name=pipeName, parent=None, project=None,   **kw):
    super(OutputPipelineGuiPipe, self)
    GuiPipe.__init__(self, parent=parent, name=name, project=project, **kw )
    self.parent = parent

    self.saveAsHDF5CheckBox = CheckBox(self.pipeFrame, checked=True, text='Save output spectra as HDF5',  grid=(0,0))
    self.saveAsHDF5Label = Label(self.pipeFrame, 'Saving  directory path',  grid=(0,1))
    self.saveAsHDF5LineEdit = LineEditButtonDialog(self.pipeFrame, fileMode=QtGui.QFileDialog.Directory,  grid=(0,2))



########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################


class OutputSpectraPipe(SpectraPipe):

  guiPipe = OutputPipelineGuiPipe
  pipeName = guiPipe.pipeName


  def runPipe(self, spectra):
    '''
    :param data:
    :return: it copies the input data as dummy spectra. Dummy spectra can be then modified.
    '''


    if self.project is not None:

      hdf5Spectra = []
      path = ''
      for spectrum in spectra:
        fullPath = str(path) + str(spectrum.name) + '.hdf5'
        convertDataToHdf5(spectrum=spectrum, outputPath=fullPath)

      # newDummySpectra = []
      # for spectrum in self.inputData:
      #   if spectrum is not None:
      #     try:
      #       dummySpectrum = self.project.createDummySpectrum(axisCodes=spectrum.axisCodes, name=spectrum.name)
      #       dummySpectrum._positions = spectrum._positions
      #       dummySpectrum._intensities = spectrum._intensities
      #       dummySpectrum.pointCounts = spectrum.pointCounts
      #       newDummySpectra.append(dummySpectrum)
      #     except Exception as e:
      #       print('Impossible create Dummy Spectrum for %s.' %spectrum,  e)



      return hdf5Spectra



# OutputSpectraPipe.register()

