# Macro to set the NmrResidues of the N and CO dimensions of a peak in an experiment containing an NCO
# onebond transfer as being connected in the N(i)-CO(i-1) direction


from ccpn.core.lib.ContextManagers import undoBlock
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.AnalysisAssign.modules.SequenceGraph import SequenceGraphModule

def _checkNumPeaks():
    if len(current.peaks) > 1:
        showWarning('Too many peaks selected', 'Please make sure you have only select one peak.')
        return(False)
    elif len(current.peaks) == 0:
        showWarning('No peak selected', 'Please make sure you select one peak.')
        return(False)
    else:
        return(True)

def _connectNmrResidues():
    peak = current.peak
    if 'NCO' in peak.spectrum.experimentType:
        for assignments in peak.assignedNmrAtoms:
            for na in assignments:
                if na.name == 'N':
                    nNmrRes = na.nmrResidue
                elif na.name == 'C':
                    coNmrRes = na.nmrResidue
        nNmrRes.connectPrevious(coNmrRes)
    else:
        showWarning('Incorrect peak selected', 'Please make sure your peak is from a spectrum type that connects '
                                               'N(i) with CO(i-1) via a one-bond transfer.')


###### Start of Macro #########

with undoBlock():
    if _checkNumPeaks():
        _connectNmrResidues()

for sg in mainWindow.modules:
    if isinstance(sg, SequenceGraphModule):
        print(f'  module {sg}')
        sg.showNmrChainFromPulldown()
