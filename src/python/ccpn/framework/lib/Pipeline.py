"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:37 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-04-07 10:28:42 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


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

        self.application = application
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

    def _updateRunArgs(self, arg, value):
        self._kwargs[arg] = value

    def runPipeline(self):
        '''Run all pipes in the specified order '''
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
