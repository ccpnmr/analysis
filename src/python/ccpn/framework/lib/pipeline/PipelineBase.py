"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2023-12-13 17:04:10 +0000 (Wed, December 13, 2023) $"
__version__ = "$Revision: 3.2.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-04-07 10:28:42 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util.Path import aPath, joinPath
import numpy as np

class Pipeline(object):
    '''
    Pipeline class.
    To run insert the pipes in the queue.

    '''
    className = 'Pipeline'

    def __init__(self, application, pipelineName=None, pipes=None):

        self.pipelineName = pipelineName
        self._kwargs = {}

        self.inputData = set()
        self.spectrumGroups = set()
        self.queue = []  # Pipes to be ran
        self.updateInputData = False

        self._rawDataDict = None

        self.application = application
        if self.application:
            self.current = self.application.current
            self.preferences = self.application.preferences
            self.ui = self.application.ui
            self.project = self.application.project
            self.mainWindow = self.ui.mainWindow

        if pipes is not None:
            self.pipes = [cls(application=application) for cls in pipes]
        else:
            self.pipes = []

    @property
    def pipes(self):
        return self._pipes

    @pipes.setter
    def pipes(self, pipes):
        '''
        '''

        if pipes is not None:
            allPipes = []
            for pipe in pipes:
                pipe.pipeline = self
                allPipes.append(pipe)
            self._pipes = allPipes
        else:
            self._pipes = []

    @property
    def filePath(self):
        return self._filePath

    @filePath.setter
    def filePath(self, filePath):
        self._filePath = filePath

    @filePath.getter
    def filePath(self):
        projectPipelinePath = aPath(self.application.pipelinePath)
        pipelineName = self.pipelineName
        savePath = joinPath(projectPipelinePath, pipelineName)
        self._filePath = str(savePath)
        return self._filePath

    @staticmethod
    def _updateTheNoiseSDBase(spectra, rawDataDict):
        for spectrum in spectra:
            if spectrum is None:
                continue
            if spectrum not in rawDataDict:
                x, y = np.array(spectrum.positions), np.array(spectrum.intensities)
            else:
                x, y = rawDataDict.get(spectrum)
            spectrum._noiseSD = float(np.median(y) + 1 * np.std(y))

    def _updateRunArgs(self, arg, value):
        self._kwargs[arg] = value

    def _set1DRawDataDict(self, force=True):
        from ccpn.core.lib.SpectrumLib import _1DRawDataDict
        if force or self._rawDataDict is None:
            self._rawDataDict = _1DRawDataDict(self.inputData)

    def runPipeline(self):
        '''Run all pipes in the specified order '''
        from ccpn.core.lib.ContextManagers import undoBlock, notificationEchoBlocking, undoBlockWithoutSideBar

        with undoBlockWithoutSideBar():
            with notificationEchoBlocking():
                self._kwargs = {}
                if len(self.queue) > 0:
                    for pipe in self.queue:
                        if pipe is not None:
                            self.updateInputData = False
                            pipe.inputData = self.inputData
                            pipe.spectrumGroups = self.spectrumGroups
                            result = pipe.runPipe(self.inputData)
                            # if not result: # that means the ran pipe does not return a valid data to use as input for next pipes
                            #   break
                            self.inputData = result or set()

                return self.inputData
