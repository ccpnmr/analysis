"""
This macro writes to an NMRPipe file style some of the CcpNmr peak properties.

Copy this macro inside the Macro Editor module and amend it as necessary.
Post your changes/improvements on the Ccpn Forum!

If guessClusterId is set to True, it will add a cluster id for each peak.
The algorithm used is based on a "connected component analysis" as seen in https://stackoverflow.com/questions/14607317/
and might not produce the expected results! There are many other (more efficient) ways of doing this operation
but is not the purpose of this macro! Set guessClusterId to False  if not happy with the result.
In Peak there isn't a property for clusterID (although we use Multiplets) so for this macro
is hack-ish stored as peak.annotation.

Requirements:
    - A spectrumGroup containing the necessary spectra. Create it from sidebar if None.
    - Fill the spectrumGroupName variable and outputPath in the User's settings section

Gui Tips:
    - To cycle the peakLabels on display use the shortcut "p+l" until you find the one you need.
    - To cycle the peakSymbols on display use the shortcut "p+s" until you find the one you need.
    - Change a peak annotation from a peakTable, double click on its cell value.

Warnings:
     - Always backup the project before running macros!
     - The macro will set peak annotations. This will help visualising the clusters ids. If overwrites your annotations,
       undo to revert to the previous state.
     - Before running the macro close all GuiTables to avoid waiting for Gui updates!
     - Check the assignment formatting if is as required. Default:
       format: 'NmrChain.NmrResidue.NmrAtom1, NmrAtom2; ...'
        e.g.: 'A.66.GLN.HE21, NE2'

"""


##############################     User's settings      #################################

spectrumGroupName = 'group'     # Pid for the spectrumGroup containing the spectra of interest
peakListIndex = -1              # Use last added peakList  as default index (-1)

export = True                    # Set to False if don't want to export
outputPath = '~/myPath'          # Path dir where to export the files. FileName from the spectrum Name.
fileExt = '.tsv'                 # Extension type. Tested only with tsv


# clustering options
guessClusterId = True            # Guess a clusterId for all peaks. False to use just a serial
tolDim1 = 8                      # tolerance for the first dimension (in points). Used to find adjacent peaks
tolDim2 = 8                      # tolerance for the second dimension (in points)
clusterByPositions  = True       # cluster peaks if their positions are within tolDim1 and tolDim2.
clusterByLWs = False             # cluster peaks with overlapping lineWidths. If True, clusterByPositions will be False
increaseLWByNpercent = 50        # increase (on-the-fly) the lw by n% value for finding overlaps. No data is modified.



##############################    Start of the code      #################################

import numpy as np
import itertools
import pandas as pd
from ccpn.util.Path import aPath, checkFilePath
from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar
from ccpn.util.Common import percentage
from ccpn.ui.gui.lib.GuiPeakListView import _getScreenPeakAnnotation


##############################     Units convertion      #################################

def _hzLW2pnt(lwHz, sw, npoints):
    """
    :param lwHz: float. A peak lineWidth (in Hz)
    :param sw: float. Spectral width (in Hz)
    :param npoints: int. Total number of points
    :return: float. A peak lineWidth in points (per dimension)
    """
    if not all([lwHz, sw, npoints]): return
    hzXpnt = sw/npoints
    lwPnt = lwHz/hzXpnt
    return lwPnt

def getLineWidthsPnt(peak):
    sp = peak.peakList.spectrum
    return tuple(_hzLW2pnt(lwHz,sp.spectralWidthsHz[i],sp.totalPointCounts[i]) for i,lwHz in enumerate(peak.lineWidths))

############################## Guess peak clusters    #################################

def clusterOverlaps(nodes, adjacents):
    "Ref: https://stackoverflow.com/questions/14607317/"
    clusters = []
    nodes = list(nodes)
    while len(nodes):
        node = nodes[0]
        path = dfs(node, adjacents, nodes)
        clusters.append(path)
        for pt in path:
            nodes.remove(pt)
    return clusters

def dfs(start, adjacents, nodes):
    "Ref: https://stackoverflow.com/questions/14607317/"
    path = []
    q = [start]
    while q:
        node = q.pop(0)
        if path.count(node) >= nodes.count(node):
            continue
        path = path + [node]
        nextNodes = [p2 for p1,p2 in adjacents if p1 == node]
        q = nextNodes + q
    return path

def _getOverlapsByLineWidths(peaks, tolDim1=0.01, tolDim2=0.01, increaseByNpercent=0):
    """
    Consider two peaks adjacent if the LW are overlapping in both dimensions.
    :param peaks: list of ccpn peak objs
    :param increaseByNpercent: increase (on-the-fly) the lw by n% value for finding overlaps. No data is modified.
    :return: A list of adjacent pairs of peaks
    """
    overlaps = []
    if len(peaks) == 0: return []
    sp = peaks[0].peakList.spectrum
    for pair in itertools.combinations(peaks, 2):
        peakA, peakB = pair
        if not all(list(peakA.lineWidths) + list(peakB.lineWidths)):
            warning('LineWidths is set to None for some peaks. Peaks skipped: %s' % ''.join(map(str, pair)))
            continue
        pos1A, pos2A = [peakA.pointPosition[i] for i in range(sp.dimensionCount)]
        lw1A, lw2A = [lw + percentage(increaseByNpercent, lw) for lw in getLineWidthsPnt(peakA)]
        pos1B, pos2B = [peakB.pointPosition[i] for i in range(sp.dimensionCount)]
        lw1B, lw2B = [lw + percentage(increaseByNpercent, lw) for lw in getLineWidthsPnt(peakB)]
        dim1a, dim2a = np.linspace(pos1A-(lw1A/2), pos1A+(lw1A/2),500), np.linspace(pos2A-(lw2A/2),pos2A+(lw2A/2),500)
        dim1b, dim2b = np.linspace(pos1B-(lw1B/2), pos1B+(lw1B/2),500), np.linspace(pos2B-(lw2B/2),pos2B+(lw2B/2),500)
        inters1 = dim1b[(np.abs(dim1a[:,None] - dim1b) < tolDim1).any(0)]
        inters2 = dim2b[(np.abs(dim2a[:,None] - dim2b) < tolDim2).any(0)]
        if all([len(inters1)>0, len(inters2)>0]):
            overlaps.append(pair)
    return overlaps

def _getOverlapPairsByPositions(peaks, tolDim1=10, tolDim2=10):
    """
    Consider two peaks adjacent if the PointPositions are within the tolerances.
    :param peaks:
    :param tolDim1: tolerance for the first dimension (in points)
    :param tolDim2: tolerance for the second dimension (in points)
    :return: A list of adjacent pairs of peaks
    """
    overlaps = []
    for pair in itertools.combinations(peaks, 2):
        dim1a, dim2a = np.array(pair[0].pointPosition[0]), np.array(pair[0].pointPosition[1])
        dim1b, dim2b = np.array(pair[1].pointPosition[0]), np.array(pair[1].pointPosition[1])
        if (np.abs(dim1a - dim1b) < tolDim1) and (np.abs(dim2a - dim2b) < tolDim2):
            overlaps.append(pair)
    return overlaps

def _getClustID(peak):
    v = None
    try:
        v = int(peak.annotation)
    except Exception as e:
        warning('Error converting peak annotation in int format. %s' %e)
    return v


def setClusterIDs(peaks, guessClustID=True):
    if guessClustID:
        if clusterByPositions and not clusterByLWs:
            overlappedPeaks = _getOverlapPairsByPositions(peaks, tolDim1=tolDim1, tolDim2=tolDim2)
        else:
            overlappedPeaks = _getOverlapsByLineWidths(peaks, increaseByNpercent=increaseLWByNpercent)
        positions = [pk.pointPosition for pk in peaks]
        overlappedPositions = [(pair[0].pointPosition, pair[1].pointPosition) for pair in overlappedPeaks]
        result = clusterOverlaps(positions, overlappedPositions)
        with undoBlockWithoutSideBar():
            allClusters = []
            for i, group in enumerate(result):
                peakCluster = []
                for peak in peaks:
                    for j in group:
                        if j == peak.pointPosition:
                            peakCluster.append(peak)
                            peak.annotation = str(i)
                allClusters.append(peakCluster)
    else:
        with undoBlockWithoutSideBar():
            for i, peak in enumerate(peaks):
                peak.annotation = str(i)

############################## Build DataFrame from peaks #################################

VARS = ['INDEX', 'X_AXIS', 'Y_AXIS', 'DX',     'DY',   'X_PPM', 'Y_PPM', 'X_HZ',  'Y_HZ',  'XW',    'YW',    'XW_HZ', 'YW_HZ', 'X1',  'X3',   'Y1', 'Y3',  'HEIGHT', 'DHEIGHT', 'VOL', 'PCHI2', 'TYPE', 'ASS', 'CLUSTID', 'MEMCNT']
FORMAT = ['%5d', '%9.3f',   '%9.3f', '%6.3f', '%6.3f', '%8.3f', '%8.3f', '%9.3f', '%9.3f', '%7.3f', '%7.3f', '%8.3f', '%8.3f', '%4d', '%4d', '%4d', '%4d', '%+e',    '%+e',     '%+e', '%.5f',   '%d',  '%s',  '%4d',      '%4d']
VFdict = {k:v for k,v in zip(VARS, FORMAT)}

# NMRPIPE VARS
INDEX = 'INDEX'     # ARBITRARY     - Peak number
X_AXIS = 'X_AXIS'   # REQUIRED      - Peak position: in points in 1st dimension, from left of spectrum limit
Y_AXIS = 'Y_AXIS'   # REQUIRED      - Peak position: in points in 2nd dimension, from bottom of spectrum limit
DX = 'DX'           # NOT REQUIRED  - Line width in 1st dimension, in points
DY = 'DY'           # NOT REQUIRED  - Line width in 2nd dimension, in points
X_PPM = 'X_PPM'     # NOT REQUIRED  - Peak position: in ppm in 1st dimension
Y_PPM = 'Y_PPM'     # NOT REQUIRED  - Peak position: in ppm in 2nd dimension
X_HZ = 'X_HZ'       # NOT REQUIRED  - Peak position: in Hz in 1st dimension
Y_HZ = 'Y_HZ'       # NOT REQUIRED  - Peak position: in Hz in 2nd dimension
XW = 'XW'           # REQUIRED      - Peak width: in points in 1st dimension
YW = 'YW'           # REQUIRED      - Peak width: in points in 2nd dimension
XW_HZ = 'XW_HZ'     # REQUIRED      - Peak width: in points in 1st dimension
YW_HZ = 'YW_HZ'     # REQUIRED      - Peak width: in points in 2nd dimension
X1 = 'X1'           # NOT REQUIRED  - Left border of peak in 1st dim, in points
X3 = 'X3'           # NOT REQUIRED  - Right border of peak in 1st dim, in points
Y1 = 'Y1'           # NOT REQUIRED  - Left border of peak in 2nd dim, in points
Y3 = 'Y3'           # NOT REQUIRED  - Right border of peak in 2nd, in points
HEIGHT = 'HEIGHT'   # NOT REQUIRED  - Peak height
DHEIGHT = 'DHEIGHT' # NOT REQUIRED  - Peak height error
VOL = 'VOL'         # NOT REQUIRED  - Peak volume
PCHI2 = 'PCHI2'     # NOT REQUIRED  - ??
TYPE = 'TYPE'       # NOT REQUIRED  - ?? default 1
ASS = 'ASS'         # REQUIRED      - Peak assignment
CLUSTID = 'CLUSTID' # REQUIRED      - Peak cluster id
MEMCNT = 'MEMCNT'   # REQUIRED      - ?? default 1

NULLVALUE =  -666
NULLSTRING = '*'

VarsDict = {
        INDEX   : lambda x: VFdict.get(INDEX) % x.serial,
        DX      : None,
        DY      : None,
        X_PPM   : lambda x: VFdict.get(X_PPM) % x.position[0] if x.position[0] else NULLVALUE,
        Y_PPM   : lambda x: VFdict.get(Y_PPM) % x.position[1] if x.position[1] else NULLVALUE,
        X_HZ    : None,
        Y_HZ    : None,
        X_AXIS  : lambda x: VFdict.get(X_AXIS) % x.pointPosition[0] if x.pointPosition[0] else NULLVALUE,
        Y_AXIS  : lambda x: VFdict.get(Y_AXIS) % x.pointPosition[1] if x.pointPosition[1] else NULLVALUE,
        XW      : lambda x: VFdict.get(XW) % getLineWidthsPnt(x)[0] if getLineWidthsPnt(x)[0] else NULLVALUE,
        YW      : lambda x: VFdict.get(YW) % getLineWidthsPnt(x)[1] if getLineWidthsPnt(x)[1] else NULLVALUE,
        XW_HZ   : lambda x: VFdict.get(XW_HZ) % x.lineWidths[0] if x.lineWidths[0] else NULLVALUE,
        YW_HZ   : lambda x: VFdict.get(YW_HZ) % x.lineWidths[1] if x.lineWidths[0] else NULLVALUE,
        X1      : None,
        X3      : None,
        Y1      : None,
        Y3      : None,
        HEIGHT  : lambda x: VFdict.get(HEIGHT) % x.height if x.height else NULLVALUE,
        DHEIGHT : lambda x: VFdict.get(DHEIGHT) % x.heightError if x.heightError else NULLVALUE,
        VOL     : lambda x: VFdict.get(VOL) % x.volume if x.volume else NULLVALUE,
        PCHI2   : None,
        TYPE    : lambda x: VFdict.get(TYPE) % 1,
        ASS     : lambda x: VFdict.get(ASS) % _getScreenPeakAnnotation(x, usePid=True),
        CLUSTID : lambda x: VFdict.get(CLUSTID) % _getClustID(x) if _getClustID(x) else NULLVALUE,
        MEMCNT  : lambda x: VFdict.get(MEMCNT) % 1,
        }

def buildDataFrame(peaks):
    df = pd.DataFrame()
    for k, v in VarsDict.items():
        if v:
            df[k] = list(map(lambda x: v(x), peaks))
        else:
            df[k] = [None]*len(peaks)
    df.columns = [np.array(VARS), np.array(FORMAT)]
    return df


def runMacro():

    spectrumGroup = get('SG:'+spectrumGroupName)
    if spectrumGroup is None:
        raise RuntimeError('You need at least a SpectrumGroup! None found with Pid "%s". '
                           'Set the name at the beginning of this macro or create a new one with '
                           'the required spectra' % spectrumGroupName)

    for spectrum in spectrumGroup.spectra:
        if len(spectrum.peakLists) == 0:
            warning('You need at least a peakList for %s' %spectrum)
            continue
        if len(spectrum.peakLists[peakListIndex].peaks) == 0:
            warning('You need at least a peak. %s skipped' %spectrum)
            continue

        peaks = spectrum.peakLists[peakListIndex].peaks
        peaks.sort(key=lambda x: x.pointPosition[0], reverse=False)
        setClusterIDs(peaks, guessClusterId)
        df = buildDataFrame(peaks)

        if export:
            isPathOk, msgErr = checkFilePath(aPath(outputPath))
            if not isPathOk:
                print('File not saved. Error: %s.'%msgErr)
            else:
                fileName = aPath(outputPath).joinpath(spectrum.name + fileExt)
                df.to_csv(str(fileName), sep='\t', index=False)
                print('File saved in: %s.' % fileName)


if __name__ == '__main__':
    runMacro()


