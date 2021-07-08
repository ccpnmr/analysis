"""
Functions to read/write ccpn logging information to a dataSet.
The Ccpn logging dataSet is stored/restored as a ccpn_logging saveframe
in nef files.
"""
#=========================================================================================
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
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-07-07 20:15:17 +0100 (Wed, July 07, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2021-07-01 17:37:42 +0100 (Thu, July 01, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util.Logging import getLogger
import pandas as pd


CCPNLOGGING = 'ccpnLogging'
CCPNHISTORY = 'ccpnHistory'


def getCcpnNefLogging(project: 'Project', name):
    """Get the required ccpnNefLogging dataframe from the project
    Returns a pandas dataFrame of the ccpn nef log for use in nef import/export
    If a dataFrame cannot be found, logs an error and returns None

    Columns are:
        date, username, program_name, input_uuid, saveframe, comment

    Raise an error if there are any issues reading dataSet parameters

    :param project: instance of type Project
    :param name: string name of the log
    :return: pandas dataFrame or None
    """
    try:
        # get the correct parameters from the dataSet
        ccpnLogging = project.getDataSet(CCPNLOGGING)
        dd = ccpnLogging.getData(name)
        params = dd.parameters

        # return a copy of the ccpnHistory parameter
        return params.get(CCPNHISTORY)

    except Exception as es:
        getLogger().debug(f'Cannot read ccpnLogging {repr(name)}')


def setCcpnNefLogging(project: 'Project', name, value, overwrite=False):
    """Set the required ccpnNefLogging dataframe in the project for use in nef import/export

    Raise an error if name or value are of the wrong types
    Returns False if the ccpnLogging already exists and overwrite is False

    :param project: instance of type Project
    :param name: string name of the log
    :param value: pandas dataFrame or None
    :param overwrite: True/False
    :return: True if successful
    """
    # check parameters
    if not isinstance(name, str):
        raise ValueError(f'ccpnLogging.name {repr(name)} must be a string')
    if not isinstance(value, (pd.DataFrame, type(None))):
        raise ValueError(f'ccpnLogging.value {repr(value)} must be a pandas dataFrame or None')

    # get the required dataSet
    ccpnLogging = project.getDataSet(CCPNLOGGING) or project.newDataSet(CCPNLOGGING)
    if not ccpnLogging:
        raise RuntimeError(f'Error creating ccpnLogging dataSet {repr(name)}')

    # check whether the data already exists in the dataSet
    dd = ccpnLogging.getData(name)
    if dd and not overwrite:
        getLogger().warning(f'ccpnLogging {repr(name)} exists')
        return

    try:
        # try and write the information to the parameters
        dd = dd or ccpnLogging.newData(name=name)
        dd.setParameter(CCPNHISTORY, value)
    except Exception as es:
        raise RuntimeError(f'Error creating ccpnLogging history {repr(name)}')

    # operation was successful
    return True
