#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2021-02-08 18:18:50 +0000 (Mon, February 08, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2021-02-08 10:28:42 +0000 (Monday, February 08, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

"""
This macro writes an NmrPipe-like file using some of the CcpNmr peak properties.

RUN: 
    - From Macro Editor:
        * Main Menu -> Macro -> New
        * Copy this macro inside the Macro Editor module
        * define a spectrum Name and the output path, any other values as required.
    
    - From Python Console
         * Copy this macro in a new text file and add the extension '.py'
         * Main Menu -> View -> Python Console (or space-space shortcut) and type:
         * %run -i thisMacro.py -o outputPath -s spectrumName
            outputPath:  the full directory path where you want save the new file
            spectrumName: the spectrum of interest
         

Post your changes/improvements on the Ccpn Forum!

If guessClusterId is set to True, it will add a cluster id for each peak.
The algorithm used is based on a "connected component analysis" as seen in https://stackoverflow.com/questions/14607317/
and might not produce the expected results! There are many other (more efficient) ways of doing this operation
but is not the purpose of this macro! Set guessClusterId to False  if not happy with the result.
In Peak there isn't a property for clusterID (although we use Multiplets) so for this macro
is hack-ish stored as peak.annotation.

Gui Tips:
    - To cycle the peakLabels on display use the shortcut "p+l" until you find the one you need.
    - To cycle the peakSymbols on display use the shortcut "p+s" until you find the one you need.
    - Change a peak annotation from a peakTable, double click on its cell value.

Warnings:
     - Always backup the project before running macros!
     - The macro will set peak annotations. This will help visualising the clusters ids. If overwrites your annotations,
       undo to revert to the previous state.
     - Before running the macro close all GuiTables to avoid waiting for Gui updates!
     - Tested only for 2D spectra and hard-coded on first two dimensions. Will not work on 1D as it is now.

"""


##############################     User's settings      #################################

spectrumName = 'test'           # Name for the spectrum of interest. (Required)
spectrumGroupName = 'group'     # Name for the spectrumGroup containing the spectra of interest (Optional). If set, the spectrumName is skipped.
peakListIndex = -1              # PeakList index to use. Default last added, index: -1. (Optional)

export = True                   # Set to False if don't want to export. Default True. (Optional)
outputPath = '~/Desktop'        # Path dir where to export the files. FileName from the spectrum Name. (Required)


# clustering options
guessClusterId = True            # Guess a clusterId for all peaks. False to use just a serial. Default True. (Optional)
tolDim1 = 8                      # tolerance for the first dimension (in points). Used to find adjacent peaks. (Optional)
tolDim2 = 8                      # tolerance for the second dimension (in points). (Optional)
clusterByPositions  = True       # cluster peaks if their positions are within tolDim1 and tolDim2. Default True. (Optional)
clusterByLWs = False             # cluster peaks with overlapping lineWidths. If True, clusterByPositions will be False. (Optional)
increaseLWByNpercent = 50        # increase (on-the-fly) the lw by n% value for finding overlaps. No data is modified. (Optional)



##############################    Start of the code      #################################

import numpy as np
import itertools
import pandas as pd
import argparse
from collections import Counter, defaultdict
from ccpn.util.Path import aPath, checkFilePath
from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar
from ccpn.util.Common import percentage
from ccpn.util.Common import makeIterableList as mi


def getArgs():
    parser = argparse.ArgumentParser( description='Create an NmrPipe Tab file')
    parser.add_argument('-o',  '--outputPath', help='Output directory path', default=outputPath)
    parser.add_argument('-s',  '--spectrumName', help='Spectrum name', default=spectrumName)
    parser.add_argument('-g',  '--spectrumGroupName', help='Spectrum group name', default=spectrumGroupName)
    parser.add_argument('-c',  '--guessClusterId', help='Guess cluster Ids', default=guessClusterId)
    parser.add_argument('-t1', '--tolDim1', help='Tolerance 1st dimension in points', default=tolDim1)
    parser.add_argument('-t2', '--tolDim2', help='Tolerance 2nd dimension in points', default=tolDim2)
    return parser

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

def getPeakPositionHz(peak):
    return [peak.position[i] * peak.peakList.spectrum.spectrometerFrequencies[i] for i, ppm in enumerate(peak.position)]

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

def _getOverlapPairsByPositions(peaks, tolDim1=10., tolDim2=10.):
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

def getMEMCNT(ids):
    return Counter(ids)

def setClusterIDs(peaks, guessClustID=True, tolDim1=8., tolDim2=8.):
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
                            peak.annotation = str(i+1)
                allClusters.append(peakCluster)
    else:
        with undoBlockWithoutSideBar():
            for i, peak in enumerate(peaks):
                peak.annotation = str(i)

############################## Build DataFrame from peaks #################################

def _getAssignmentLabel(peak):
    """
    :param peak:
    :return: str. the assignemnt in the format: TypeCode_AtomNames e.g. 'LYS1_HN'.
        If multiple assignments per peak: 'LYS1_HN-ALA2_H1N1'
    """
    dd = defaultdict(list)
    labels = []
    for na in mi(peak.assignments):
        dd[na.nmrResidue].append(na.name)
    for nr, nas in dd.items():
        l1 = ''.join([nr.residueType, nr.sequenceCode, '_', *nas])
        labels.append(l1)
    return '-'.join(labels)

VARS = ['INDEX', 'X_AXIS', 'Y_AXIS', 'DX',     'DY',   'X_PPM', 'Y_PPM', 'X_HZ',  'Y_HZ',  'XW',    'YW',    'XW_HZ', 'YW_HZ', 'X1',  'X3',   'Y1', 'Y3',  'HEIGHT', 'DHEIGHT', 'VOL', 'PCHI2', 'TYPE', 'ASS', 'CLUSTID', 'MEMCNT']
FORMAT = ['%5d', '%9.3f',   '%9.3f', '%6.3f', '%6.3f', '%8.3f', '%8.3f', '%9.3f', '%9.3f', '%7.3f', '%7.3f', '%8.3f', '%8.3f', '%4d', '%4d', '%4d', '%4d', '%+e',    '%+e',     '%+e', '%.5f',   '%d',  '%s',  '%4d',      '%4d']
VFdict = {k:v for k,v in zip(VARS, FORMAT)}

# NMRPIPE VARS https://spin.niddk.nih.gov/NMRPipe/doc2new/

INDEX = 'INDEX'     # REQUIRED      - The unique peak ID number.
X_AXIS = 'X_AXIS'   # REQUIRED      - Peak position: in points in 1st dimension, from left of spectrum limit
Y_AXIS = 'Y_AXIS'   # REQUIRED      - Peak position: in points in 2nd dimension, from bottom of spectrum limit
DX = 'DX'           # NOT REQUIRED  - Estimate of the error in peak position due to random noise, in points.
DY = 'DY'           # NOT REQUIRED  - Estimate of the error in peak position due to random noise, in points.
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
PCHI2 = 'PCHI2'     # NOT REQUIRED  - the Chi-square probability for the peak (i.e. probability due to the noise)
TYPE = 'TYPE'       # NOT REQUIRED  - the peak classification; 1=Peak, 2=Random Noise, 3=Truncation artifact.
ASS = 'ASS'         # REQUIRED      - Peak assignment
CLUSTID = 'CLUSTID' # REQUIRED      - Peak cluster id. Peaks with the same CLUSTID value are the overlapped.
MEMCNT = 'MEMCNT'   # REQUIRED      - the total number of peaks which are in a given peak's cluster
                                      # (i.e. peaks which have the same CLUSTID value)

NONE = None
NULLVALUE =  -666
NULLSTRING = '*'
UNKNOWN = 1
PCHI2Default = 0.00000
TYPEDefault = 1

VarsDict = {
        INDEX   : lambda x: VFdict.get(INDEX) % x.serial,
        X_AXIS  : lambda x: VFdict.get(X_AXIS) % (x.pointPosition[0] if x.pointPosition[0] else NULLVALUE),
        Y_AXIS  : lambda x: VFdict.get(Y_AXIS) % (x.pointPosition[1] if x.pointPosition[1] else NULLVALUE),
        DX      : lambda x: VFdict.get(DX) % (x.positionError[0] if x.positionError[0] else NULLVALUE),
        DY      : lambda x: VFdict.get(DY) % (x.positionError[1] if x.positionError[1] else NULLVALUE),
        X_PPM   : lambda x: VFdict.get(X_PPM) % (x.position[0] if x.position[0] else NULLVALUE),
        Y_PPM   : lambda x: VFdict.get(Y_PPM) % (x.position[1] if x.position[1] else NULLVALUE),
        X_HZ    : lambda x: VFdict.get(X_HZ) % (getPeakPositionHz(x)[0] if getPeakPositionHz(x)[0] else NULLVALUE),
        Y_HZ    : lambda x: VFdict.get(Y_HZ) % (getPeakPositionHz(x)[0] if getPeakPositionHz(x)[0] else NULLVALUE),
        XW      : lambda x: VFdict.get(XW) % (getLineWidthsPnt(x)[0] if getLineWidthsPnt(x)[0] else NULLVALUE),
        YW      : lambda x: VFdict.get(YW) % (getLineWidthsPnt(x)[1] if getLineWidthsPnt(x)[1] else NULLVALUE),
        XW_HZ   : lambda x: VFdict.get(XW_HZ) % (x.lineWidths[0] if x.lineWidths[0] else NULLVALUE),
        YW_HZ   : lambda x: VFdict.get(YW_HZ) % (x.lineWidths[1] if x.lineWidths[0] else NULLVALUE),
        X1      : lambda x: VFdict.get(X1) % (x.pointPosition[0]-10 if x.pointPosition[0] else NULLVALUE),
        X3      : lambda x: VFdict.get(X3) % (x.pointPosition[0]+10 if x.pointPosition[0] else NULLVALUE),
        Y1      : lambda x: VFdict.get(Y1) % (x.pointPosition[1]-10 if x.pointPosition[1] else NULLVALUE),
        Y3      : lambda x: VFdict.get(Y3) % (x.pointPosition[1]+10 if x.pointPosition[1] else NULLVALUE),
        HEIGHT  : lambda x: VFdict.get(HEIGHT) % (x.height if x.height else NULLVALUE),
        DHEIGHT : lambda x: VFdict.get(DHEIGHT) % (x.heightError if x.heightError else NULLVALUE),
        VOL     : lambda x: VFdict.get(VOL) % (x.volume if x.volume else NULLVALUE),
        PCHI2   : lambda x: VFdict.get(PCHI2) % (PCHI2Default),
        TYPE    : lambda x: VFdict.get(TYPE) % (TYPEDefault),
        ASS     : lambda x: VFdict.get(ASS) % (_getAssignmentLabel(x)),
        CLUSTID : lambda x: VFdict.get(CLUSTID) % (_getClustID(x) if _getClustID(x) else NULLVALUE),
        MEMCNT  : lambda x: VFdict.get(MEMCNT) % (UNKNOWN), # this is filled afterwards, if clusters
        }

def buildDataFrame(peaks):
    df = pd.DataFrame()
    for k, v in VarsDict.items():
        if v: df[k] = list(map(lambda x: v(x), peaks))
    _memcntDict = getMEMCNT(df[CLUSTID]) #set the MEMCNT
    df[MEMCNT] = [_memcntDict.get(i) for i in df[CLUSTID].values]
    df.set_index(df[INDEX], inplace=True)
    df.sort_index(inplace=True)
    return df

def dfToTab(df):
    "Return NmrPipe (NIH) tab-file formatted string"
    string = ''
    string += 'VARS   %s\n' % ' '.join(VARS)
    string += 'FORMAT %s\n\n' % ' '.join(FORMAT)
    string += 'NULLVALUE -666'
    string += '\nNULLSTRING *\n\n'
    string += df.to_string(header=False, index=False) # formats are already defined when building the dataframe.
    return string



def runMacro():

    args = getArgs().parse_args()
    globals().update(args.__dict__)
    info('Running macro with %s'%args)

    spectrum = get('SP:'+spectrumName)
    spectrumGroup = get('SG:'+spectrumGroupName)
    spectra = []

    if not any([spectrum, spectrumGroup]):
        msg = 'You need at least a spectrum! Set the name at the beginning of this macro'
        print(msg)
        raise RuntimeError(msg)

    if spectrumGroup:
        spectra = spectrumGroup.spectra
        info('Running macro using spectrumGroup')
    else:
        if spectrum:
            info('Running macro using a single spectrum')
            spectra = [spectrum]

    if len(spectra)==0:
        msg = 'You need at least a spectrum! Set the name at the beginning of this macro'
        print(msg)
        raise RuntimeError(msg)

    for spectrum in spectra:
        if len(spectrum.peakLists) == 0:
            warning('You need at least a peakList for %s' %spectrum)
            continue
        if len(spectrum.peakLists[peakListIndex].peaks) == 0:
            warning('You need at least a peak. %s skipped' %spectrum)
            continue

        peaks = spectrum.peakLists[peakListIndex].peaks
        peaks.sort(key=lambda x: x.pointPosition[0], reverse=False)
        _guessClusterId = True if guessClusterId in ['True', 'y', 'Y', 'yes', 'true'] else False
        setClusterIDs(peaks, _guessClusterId, float(tolDim1), float(tolDim2))
        df = buildDataFrame(peaks)
        if export:
            isPathOk, msgErr = checkFilePath(aPath(outputPath))
            if not isPathOk:
                print('File not saved. Error: %s.'%msgErr)
            else:
                fileName = aPath(outputPath).joinpath(spectrum.name + '.tab')
                string = dfToTab(df)
                with open(fileName, 'w') as f:
                    f.write(string)
                    print('File saved in: %s.' % fileName)


if __name__ == '__main__':
    runMacro()


