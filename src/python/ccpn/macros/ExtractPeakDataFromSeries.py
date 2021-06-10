
#=========================================================================================
# General CCPN Licence, Reference and Credits
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")

#=========================================================================================
# Macro Created by:
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-06-10 14:59:40 +0100 (Thu, June 10, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author__author__      =   "$Author: Luca Mureddu $"
__date__ = "$Date__date__        =   "$Date: 2021-06-09 14:02:46 +0100 (Wed, June 09, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================
__version__ = "$Revision: 3.0.4 $"
__Title__       =   "Extract peak properties to file  "
__Category__    =   "Assign"
__tags__        =   ("Relaxation", "Refit peaks")
__Description__ =   """
                    Use this macro if you have assigned peaks for multiple spectra in a series and you want extract the peak property 
                    for a Relaxation Analysis or similar.

                    This macro will update first the peak height, then will group all in a Pandas dataFrame for easy exporting to file.
                    
                    The dataFrame has the following structure:
                    
                    
                                            |  NR_ID  |   SP1     |    SP2    |   SP3
                                H     N     |         |           |           |
                               -------------+-------- +-----------+-----------+---------
                                7.5  104.3  | A.1.ARG |    10     |  100      | 1000
                    
                                Index: multiIndex => axisCodes as levels;
                                Columns => NR_ID: ID for the nmrResidue(s) assigned to the peak if available
                                           Spectrum series values sorted by ascending values, if series values are not set, then the
                                           spectrum name is used instead.
                                           Cell values: heights (for this macro)
                    
                                   
                    """

__Prerequisites__ = """
                    A spectrum Group with series values and peaks
                    """


"""
Cite us:

Simple High-Resolution NMR Spectroscopy as A Tool in Molecular Biology. LG Mureddu and GW Vuister. FEBS Journal (2019). doi:10.1111/febs.14771
CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis. SP Skinner et al. J. Biomol. NMR (2016). doi:10.1007/s10858-016-0060-y

"""
##################################################################################################
#####################################    User's  Parameters  #####################################
##################################################################################################



import pandas as pd
from ccpn.core.lib.ContextManagers import undoBlock, undoBlockWithoutSideBar, notificationEchoBlocking
from ccpn.core.lib.peakUtils import estimateVolumes, updateHeight
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.popups.SpectrumGroupEditor import SpectrumGroupEditor
from ccpn.core.lib.peakUtils import _getSpectralPeakPropertyAsDataFrame, NR_ID, HEIGHT , POSITIONS, VOLUME


#####################################     User input       ####################################

exportPath = 'REPLACE_with_your_path/' # must finish with slash
exportFileName = 'myAnalysis.xlsx' # other valid formats are .csv, .tsv, .json

recalculateHeight = True
recalculateVolume = True #this will also refit lineWidth maintaining the original position

spectrumGroupName = 'REPLACE_with_your_spectrGroup_name'

sortByDataByNR_ID = False # Sort table by NmrResidue ID. See below for more sorting options. (see Pandas docs for advanced settings)
Export            = True  # If you want export to other formats, change the file name and export command below.
PeakProperty      = 'volume' # one of: 'volume', 'height', 'positions' (lower case)

####################################   Start of the code    ####################################


def getDFforPeakProperty(spectra, peakProperty, peakListIndexes:list=None) -> pd.DataFrame:
    """
    return: Pandas DataFrame with the following structure:
            Index:  ID for the nmrResidue(s) assigned to the peak ;
            Columns => Spectrum series values sorted by ascending values, if series values are not set, then the
                       spectrum name is used instead.

                   |   SP1     |    SP2    |   SP3
        NR_ID      |           |           |
       ------------+-----------+-----------+----------
        A.1.ARG    |    10     |  100      | 1000

        """
    df = _getSpectralPeakPropertyAsDataFrame(spectra, peakProperty=HEIGHT, peakListIndexes=peakListIndexes)
    newDf = df[df[NR_ID] != ''] # remove rows if NR_ID is not defined
    newDf = newDf.reset_index(drop=True).groupby(NR_ID).max()
    return newDf


spectrumGroup = get('SG:'+spectrumGroupName)

def _queryForNewSpectrumGroup(spectrumGroup=None):

    msg = 'This macro requires a SpectrumGroup containing spectra and defined series'
    if not spectrumGroup:
        needCreateNewSG = MessageDialog.showYesNo('SpectrumGroup not found','%s. Create new?'% msg)
        if needCreateNewSG:
            sge = SpectrumGroupEditor(parent=mainWindow, mainWindow=mainWindow, editMode=False)
            sge.exec_()
            spectrumGroup = sge.obj
            if spectrumGroup.name != spectrumGroupName:
                warning('The spectrumGroupName variable in this macro is different from the new spectrumGroup name.'
                        'If you run this macro again it will prompt another Popup.')
        else:
            raise RuntimeError('SpectrumGroup not found. %s'% msg)

    return spectrumGroup

while not spectrumGroup:
    spectrumGroup = _queryForNewSpectrumGroup(spectrumGroup)


######## Get the spectra from the spectrumGroup and their peaks from the last added peakList
spectra = [sp for sp in spectrumGroup.spectra]
peaks = [pk for sp in spectra for pk in sp.peakLists[-1].peaks]
info('Using peaks contained in the last peakList for spectra %s' % ', '.join(map(str, spectra)))

########  Recalculate peak properties
info('Recalculating peak properties...')
with undoBlockWithoutSideBar():
    with notificationEchoBlocking():
        if recalculateHeight:
            list(map(lambda x: updateHeight(x), peaks))
        if recalculateVolume:
            list(map(lambda x: x.fit(keepPosition=True), peaks))
            list(map(lambda x: x.estimateVolume(), peaks))
info('Recalculating peak properties completed.')

######## Get dataframes for the spectrumGroup
df = getDFforPeakProperty(spectra, PeakProperty)

def naturalSort(df, col):
    df['_int'] = df[col].str.extract('(\d+)')
    _nonIntDF = df[df['_int'].isnull()]
    df = df[~df['_int'].isnull()]
    df['_int'] = df['_int'].astype(int)
    df = df.sort_values(by=['_int'])
    df = pd.concat([df, _nonIntDF])
    df.drop(['_int'], axis=1, inplace = True)
    return df

if sortByDataByNR_ID:
    df = naturalSort(df, 'NR_ID')

## to sort by axis: e.g. H. The table will be sorted ascending for H ppm position
# df = df.sort_index(level='H')

if Export:
    df.to_excel(exportPath+exportFileName) # or use df.to_csv() for "file.csv" fileNames. etc
    info('DataFrame exported in: %s' %exportPath+exportFileName)

print(df)
