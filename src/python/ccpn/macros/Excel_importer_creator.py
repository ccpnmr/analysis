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
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified:  2019-06-05 10:28:41 +0000 (Wed, June 05, 2019) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca $"
__date__ = "$Date: 2019-06-05 10:28:41 +0000 (Wed, June 05, 2019) $"
#=========================================================================================
# Start of code
#=========================================================================================



"""

This script aims to facilitate the creation of Lookup files for loading large dataset into Ccpnmr V3.
Specifically designed for loading screening datasets.
This Will create an excel file which can be dropped into Ccpnmr to load all the metadata associated with it.

Run:
    V3 Main Menus:
    - > Macro > Open... > select thisFile.py
    - modify as needed
    - run 
    
    or from command line:
    - open with an editor and modify as needed
    - on the terminal: change to V3 top dir
    - ./bin/python thisFile.py


"""
WorkingPathDir = ''
ReferenceSpectraPath = '/Users/luca/Desktop/DFCI/cpmg_development/4A_data/NMX_BionetG2_NMR_data' # top dir path containing all reference files
ControlSpectraPath= '/Users/luca/Desktop/DFCI/cpmg_development/4A_data/4A_H2_SF'
TargetSpectraPath= '/Users/luca/Desktop/DFCI/cpmg_development/4A_data/4A_H2_SP'


ReferenceSpectrumGroupName = 'References'
ControlSampleName_prefix = 'Control_SF' # use for creating sample name identifier.
TargetSampleName_prefix = 'Target_SP'  # use for creating sample name identifier.

## Only for Bruker files. The sub directories containing the spectra to import
Bruker_expNo_SubDirectory = '1' # Default Take the first experiment if multiple
Bruker_pdata_SubDirectory = '1' # Default Take the first processing file if multiple

outputPath = '/Users/luca/Desktop/DFCI/cpmg_development/4A_data'
outputName = 'lookupFile.xls'

'''
# Divide spectra experiment types by filename pattern
# ExperimentTypesMap = { id : { key : value } }
                        # id = identifier for experimental type
                        # key = FileName identifier. 
                                E.g. File name 101 (as bruker dir 101). 
                                Where "1" stands for sample number 1. 
                                and   "01" will be the experiment of type CPMG
                         
                        # Value = parameter like seconds or concentration 
                                  for sample 1 experiment 1 time of 0s
'''

ReferenceExperimentType = 'H'
ExperimentTypesMap = {
    'H'     : {'0': None},
    'CPMG_0': {'01': (0, 'ms')},
    'CPMG_1': {'02': (45, 'ms')},
    'CPMG_2': {'03': (50, 'ms')},
    'CPMG_3': {'04': (100, 'ms')},
    'CPMG_4': {'05': (300, 'ms')},
    'CPMG_5': {'06': (500, 'ms')},
    'CPMG_6': {'07': (800, 'ms')},
    'ON'    : {'08': None},
    'OFF'   : {'09': None},
    }



import os
import glob
import pandas as pd
from ccpnmodel.ccpncore.lib.Io import Formats as ioFormats

from ccpn.util import ExcelReader as er



from ccpn.util.ExcelReader import ExcelReader



def getSpectraNames(topDirPath, fileType):
    """
    :param topDirPath: str of path containing the spectra
    :param fileType: eg 1r or hdf5
    :return: lists of names
    """
    if fileType == '1r':
        names = [n for n in os.listdir(topDirPath) if os.path.isdir(os.path.join(topDirPath, n))]
        return names
    else:
        names = [n.split('.')[0] for n in os.listdir(topDirPath) if n.endswith(fileType)]
        return names

def get_last_digits(num, last_digits_count=2):
    return int(str(num)[-last_digits_count:])



ref1r = ioFormats._searchSpectraPathsInSubDir(ReferenceSpectraPath)
filteredReferencePaths = er._filterBrukerExperiments(ref1r, multipleExp=True) #these Bruker Files ahave multiple experiments on the top dir
referenceExperimentTypes = [ReferenceExperimentType]*len(filteredReferencePaths)
referenceNames = getSpectraNames(ReferenceSpectraPath, '1r')

pathMatchesName = all([name in path.split('/') for name, path in zip(referenceNames,filteredReferencePaths) ])
referenceDataFrame = er.getDefaultSubstancesDF()
if pathMatchesName:
    setattr(referenceDataFrame, er.SUBSTANCE_NAME, referenceNames)
    setattr(referenceDataFrame, er.SPECTRUM_PATH, filteredReferencePaths)
    setattr(referenceDataFrame, er.SPECTRUM_GROUP_NAME, ReferenceSpectrumGroupName)
    setattr(referenceDataFrame, er.EXP_TYPE, ReferenceExperimentType)


# samplesWithoutTarget
control1r = ioFormats._searchSpectraPathsInSubDir(ControlSpectraPath)
controlSpectra =  er._filterBrukerExperiments(control1r, multipleExp=False)
controlNames = getSpectraNames(ControlSpectraPath, '1r')

for i in controlNames:
 lastDigit = get_last_digits(int(112),2)


print(sorted([int(i) for i in controlNames]))


if outputPath:
    outputPath = outputPath + '/' + outputName if not outputPath.endswith('/') else outputPath + outputName
else:
    outputPath = os.getcwd() + '/' + outputName if not outputPath.endswith('/') else os.getcwd() + outputName

if True:
# Create a Excel Writer object
    writer = pd.ExcelWriter(outputPath, engine='xlsxwriter')
    referenceDataFrame.to_excel(writer, sheet_name=er.SUBSTANCE)
    writer.save()
