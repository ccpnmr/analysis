
#### GUI IMPORTS
from ccpn.ui.gui.widgets.PipelineWidgets import GuiPipe

#### NON GUI IMPORTS
from ccpn.framework.lib.pipeline.PipeBase import SpectraPipe, PIPE_METABOLOMICS
from ccpn.util.Logging import getLogger
from tqdm import tqdm
from sklearn.cluster import DBSCAN
import numpy as np

########################################################################################################################
###   Attributes:
###   Used in setting the dictionary keys on _kwargs either in GuiPipe and Pipe
########################################################################################################################

PipeName = 'Cluster JRES Peaks'
DefaultEps = 0.001
DefaultMinSamples = 2

########################################################################################################################
##########################################      ALGORITHM       ########################################################
########################################################################################################################

# Uses clustering algorithms to group peaks into multiplets for 2D JRES spectra

########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################


class ClusterJRESPeaksGuiPipe(GuiPipe):
    preferredPipe = True
    pipeName = PipeName

    def __init__(self, name=pipeName, parent=None, project=None, **kwds):
        super(ClusterJRESPeaksGuiPipe, self)
        GuiPipe.__init__(self, parent=parent, name=name, project=project, **kwds)
        self._parent = parent


########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################


class ClusterJRESPeaksPipe(SpectraPipe):
    guiPipe = ClusterJRESPeaksGuiPipe
    pipeName = PipeName
    pipeCategory = PIPE_METABOLOMICS

    _kwargs = {
              }

    def runPipe(self, spectra, **kwargs):
        """
        :param data:
        :return:
        """
        for spectrum in tqdm(self.inputData):
            if spectrum.axisCodes != ['H', 'H_2']:
                getLogger().warning('Error: Incorrect axis codes for Spectrum: %s. Expected ["H", "H_2"]' % spectrum.pid)
            if len(spectrum.peakLists) > 0:
                chemicalShifts = np.array([peak.position[0] for peak in spectrum.peaks])
                dbscan = DBSCAN(eps=0.001, min_samples=2)
                clusters = dbscan.fit_predict(chemicalShifts.reshape(-1, 1))
                ml = spectrum.newMultipletList()
                for num in set(clusters):
                    if num == -1:
                        continue
                    peakList = [spectrum.peaks[i] for i in np.where(clusters == num)[0]]
                    ml.newMultiplet(peaks=peakList)
            else:
                getLogger().warning('Error: PeakList not found for Spectrum: %s. Add a new PeakList first' % spectrum.pid)
        return spectra


ClusterJRESPeaksPipe.register()  # Registers the pipe in the pipeline