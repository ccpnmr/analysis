
"""
Version 3.0.3

Use this macro if you have assigned peaks for multiple spectra in a series and you want extract the peak heights.

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

            This dataframe is available from the SpectrumGroup class property 'seriesPeakHeightForPosition'.
            N.B. this feature is still under development and can change or be deprecated in future releases.

Change the user input as needed.

"""


import pandas as pd
from ccpn.core.lib.ContextManagers import undoBlock, undoBlockWithoutSideBar, notificationEchoBlocking
from ccpn.core.lib.peakUtils import estimateVolumes, updateHeight
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.popups.SpectrumGroupEditor import SpectrumGroupEditor

#####################################     User input       ####################################

exportPath = '~/Desktop/'
exportFileName = 'myAnalysis.xlsx'

recalculateHeight = True
recalculateVolume = False

spectrumGroupName = 'MySpectrumGroup'

sortByDataByNR_ID = False # Sort table by NmrResidue ID. See below for more sorting options. (see Pandas docs for advanced settings)
export = True # If you want export to other formats, change the file name and export command below.


####################################   Start of the code    ####################################

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
            list(map(lambda x: estimateVolumes(x), peaks))
info('Recalculating peak properties completed.')

######## Get dataframes for the spectrumGroup
df = spectrumGroup.seriesPeakHeightForPosition

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

if export:
    df.to_excel(exportPath+exportFileName) # or use df.to_csv() for "file.csv" fileNames. etc
    info('DataFrame exported in: %s' %exportPath+exportFileName)

print(df)
