from __future__ import unicode_literals, print_function, absolute_import, division

__author__ = 'TJ Ragan'

ITEM_PAD = '  '

def _datablockText( nef ):
    return 'data_{}\n'.format(nef.datablock)


def _saveframeHeaderText(nef, saveframeName):
    return 'save_{}\n'.format(nef[saveframeName]['sf_framecode'])


def _dataLabelText(saveframe, dataLabel):
    sf_framecode = saveframe['sf_framecode']
    return '_{0}.{1}'.format(sf_framecode, dataLabel)


def _dataValueText(saveframe, dataLabel):
    template = '{}'
    if '\n' in saveframe[dataLabel]:
        template = ';\n{}\n;\n'
    elif '"' in saveframe[dataLabel]:
        template = "'{}'"
    elif "'" in saveframe[dataLabel]:
        template = '"{}"'
    return template.format(saveframe[dataLabel])


def _dataItemText(saveframe, dataLabel):
    return '{0}{1}\t{2}\n'.format(ITEM_PAD,
                              _dataLabelText(saveframe, dataLabel),
                              _dataValueText(saveframe, dataLabel))


def _loopHeaderText(saveframe, loopName):
    return '{}loop_\n'.format(ITEM_PAD)


def _saveframeFooterText(nef, saveframeName):
    return 'save_\n'


def _loopFooterText(saveframe, loopName):
    return '  stop_\n'


def _saveframeItemsText(nef, saveframeName):
    text = ''
    sf = nef[saveframeName]
    labels = tuple(sf.keys())

    itemLabels = [x for x in labels if type(sf[x]) in (str, float, int)]

    for l in ['sf_category', 'sf_framecode']:
        itemLabels.remove(l)
        text += _dataItemText(sf, l)
    for l in itemLabels:
        text += _dataItemText(sf, l)

    return text


def _loopLabelsText(loopName, loopColumnNames):
    text = ''
    for loopColumnName in loopColumnNames:
        text += '{0}{0}_{1}.{2}\n'.format(ITEM_PAD, loopName, loopColumnName)
    return text


def _loopText(saveframe, loopName, strict=True):
    loop = saveframe[loopName]
    text = _loopHeaderText(saveframe, loopName)

    if len(loop) == 0:
        raise IndexError('loop {} must contain at least one entry.'.format(loopName))

    loopColumnNames = tuple(loop[0].keys())
    if strict is False:
        raise NotImplementedError('Non-strict loop writing not yet implemented.')
    text += _loopLabelsText(loopName, loopColumnNames)
    text += '\n'

    text += _loopRowsText(loop, loopColumnNames, strict)

    text += _loopFooterText(saveframe, loopName)
    text += '\n'

    return text


def _adjustTemplate(baseLoopRowTextTemplate, loopRow):
    for k, v in loopRow.items():
        quoteString = None
        if '\n' in v:
            quoteString = '\n;\n'
        elif '"' in v:
            quoteString = "'"
        elif "'" in v:
            quoteString = '"'

        if quoteString is not None:
            topSplit = baseLoopRowTextTemplate.find(k)-1
            bottomSplit = topSplit + len(k) + 2
            loopRowTextTemplate = baseLoopRowTextTemplate[:topSplit]
            loopRowTextTemplate += quoteString
            loopRowTextTemplate += baseLoopRowTextTemplate[topSplit:bottomSplit]
            loopRowTextTemplate += quoteString
            loopRowTextTemplate += baseLoopRowTextTemplate[bottomSplit:]
            return loopRowTextTemplate
    return baseLoopRowTextTemplate

def _loopRowsText(loop, loopColumnNames, strict):
    text = ''

    baseLoopRowTextTemplate = '{0}{0}{{'.format( ITEM_PAD )
    for loopColumnName in loopColumnNames:
        baseLoopRowTextTemplate += str( loopColumnName ) + '}\t{'
    baseLoopRowTextTemplate = baseLoopRowTextTemplate[ :-2 ]
    for loopRow in loop:
        if strict:
            if len( loopRow ) == len( loopColumnNames ):
                loopRowTextTemplate = _adjustTemplate(baseLoopRowTextTemplate, loopRow)
                text += loopRowTextTemplate.format( **loopRow ) + '\n'
        else:
            raise NotImplementedError( 'Non-strict loop writing not yet implemented.' )
    return text


def _findLoopsInSaveframe(saveframe):
    loopNames = []
    for k,v in saveframe.items():
        if type(v) == list:
            loopNames.append(k)
    return loopNames


def _saveframeText(nef, saveframeName):
    sf = nef[saveframeName]

    text = _saveframeHeaderText(nef, saveframeName)
    text += '\n'
    text += _saveframeItemsText(nef, saveframeName)

    for loopName in _findLoopsInSaveframe(sf):
        text += '\n'
        text += _loopText(sf, loopName)

    text += _saveframeFooterText(nef, saveframeName)
    text += '\n'
    return text


def nefToText(nef):
    text = _datablockText(nef)
    text += '\n'
    for saveframeName in nef.keys():
        text += _saveframeText(nef, saveframeName)

    return text