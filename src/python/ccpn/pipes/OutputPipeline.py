#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Joanna Fox, Morgan Hayward, Victoria A Higman, Luca Mureddu",
               "Eliza Płoskoń, Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2024-01-16 17:48:56 +0000 (Tue, January 16, 2024) $"
__version__ = "$Revision: 3.2.2 $"
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
from PyQt5 import QtWidgets
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.FileDialog import LineEditButtonDialog
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons

#### NON GUI IMPORTS
from ccpn.framework.lib.pipeline.PipeBase import SpectraPipe, PIPE_OUTPUTS
import pandas as pd
import os


########################################################################################################################
###   Attributes:
###   Used in setting the dictionary keys on _kwargs either in GuiPipe and Pipe
########################################################################################################################

PipeName = 'Output Pipeline'
SavePath = 'Save_Directory_Path'
SaveHDF5 = 'Save_Spectra_in_HDF5'
SaveOutputMode = 'Save_Output_Mode'
CSV = 'CSV'
TAB = 'Tab'
XLSX = 'XLSX'
Json = 'Json'
DataSet = 'CCPN DataSet'
Modes = [CSV, TAB, XLSX, Json, DataSet]
DefaultPath = os.path.expanduser("~")


########################################################################################################################
##########################################      ALGORITHM       ########################################################
########################################################################################################################


def _getPipelineOutputs(pipeline):
    outputs = []
    if pipeline is not None:
        application = pipeline.application
        if application is not None:
            outputs.append(('Application Version', application.applicationName + ' ' + application.applicationVersion))
            outputs.append(('Pipeline: ' + pipeline.pipelineName, pipeline._kwargs))
            spectraNames = []
            if pipeline.inputData:
                for sp in pipeline.inputData:
                    if sp is not None:
                        spectraNames.append(sp.name)
            outputs.append(('Output spectra:', spectraNames))

            for pipe in pipeline.queue:
                if pipe is not None:
                    outputs.append(('Pipe: ' + pipe.pipeName, pipe._kwargs))

    return outputs


def _getOutPutDataFrame(outputList):
    df = pd.DataFrame(outputList)
    return df


########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################


class OutputPipelineGuiPipe(GuiPipe):
    preferredPipe = True
    pipeName = PipeName

    def __init__(self, name=pipeName, parent=None, project=None, **kwds):
        super(OutputPipelineGuiPipe, self)
        GuiPipe.__init__(self, parent=parent, name=name, project=project, **kwds)
        self._parent = parent

        row = 0
        self.saveAsHDF5Label = Label(self.pipeFrame, SaveHDF5, grid=(row, 0))
        setattr(self, SaveHDF5, CheckBox(self.pipeFrame, checked=False, grid=(row, 1)))

        row += 1
        self.modeLabel = Label(self.pipeFrame, SaveOutputMode, grid=(row, 0))
        setattr(self, SaveOutputMode,
                RadioButtons(self.pipeFrame, texts=Modes, direction='v', vAlign='c', selectedInd=1, grid=(row, 1)))

        row += 1
        self.savePathLabel = Label(self.pipeFrame, SavePath, grid=(row, 0))
        setattr(self, SavePath,
                LineEditButtonDialog(self.pipeFrame, fileMode='directory', grid=(row, 1)))
        self._setDefaultDataPath()

    def _setDefaultDataPath(self):
        'writes the default data path in the pipe lineEdit'
        if self.application is not None:
            getattr(self, SavePath).lineEdit.set(self.application.preferences.general.dataPath)


########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################


class OutputSpectraPipe(SpectraPipe):
    guiPipe = OutputPipelineGuiPipe
    pipeName = PipeName
    pipeCategory = PIPE_OUTPUTS

    _kwargs = {
        SavePath      : DefaultPath,
        SaveHDF5      : False,
        SaveOutputMode: ''
        }

    def runPipe(self, spectra, **kwargs):
        """

        """

        outputs = _getPipelineOutputs(self.pipeline)
        df = _getOutPutDataFrame(outputs)

        path = self._kwargs[SavePath] + '/'
        mode = self._kwargs['Save_Output_Mode']
        saveHDF5 = self._kwargs[SaveHDF5]

        if saveHDF5:
            for spectrum in spectra:
                if spectrum is not None:
                    fullPath = str(path) + str(spectrum.name) + '.hdf5'
                    if spectrum.dimensionCount == 1:
                        spectrum.extractSliceToFile(axisCode=spectrum.axisCodes[0],
                                                    position=[1, spectrum.pointCounts[0]],
                                                    path=fullPath)
        sucess = False
        if df is not None:
            if mode == CSV:
                df.to_csv(path + self.pipeline.pipelineName)
                sucess = True
            if mode == TAB:
                df.to_csv(path + self.pipeline.pipelineName, sep='\t')
                sucess = True
            if mode == Json:
                df.to_json(path + self.pipeline.pipelineName + '.json', orient='split')
                sucess = True
            if mode == XLSX:
                df.to_excel(path + self.pipeline.pipelineName + '.xlsx', sheet_name=self.pipeline.pipelineName,
                            index=False, )
                sucess = True
            if mode == DataSet:
                newDataSet = self.project.newStructureData(name=self.pipeline.pipelineName)
                data = newDataSet.newData(name=self.pipeline.pipelineName)
                data.setDataParameter(self.pipeline.pipelineName, df)

        if sucess:
            self.project._logger.info("Pipeline Output saved in %s" % path)

        return spectra


OutputSpectraPipe.register()
