"""
Functions to read/write ccpn logging information to project data
The Ccpn logging data is stored/restored as a ccpn_logging saveframe
in nef files.
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2022-02-05 18:39:30 +0000 (Sat, February 05, 2022) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2021-07-01 17:37:42 +0100 (Thu, July 01, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

import pandas as pd
import numpy as np
from typing import Optional
from ccpn.framework.lib.ccpnNef.CcpnNefCommon import nef2CcpnMap
from ccpn.util.Logging import getLogger


CCPNLOGGING = 'ccpnLogging'
CCPNHISTORY = 'ccpnHistory'
CCPNDEFAULT = 'log'
NEFMAPPING = 'ccpn_history'


def getCcpnNefLogNames(project: 'Project'):
    """Return a tuple of CcpnNef log names

    :param project: instance of type Project
    :return: tuple of log names, or None if undefined
    """
    try:
        # get the correct parameters from data
        data = project._wrappedData.data
        ccpnLogging = data.get(CCPNLOGGING)
        keys = tuple(ccpnLogging.keys())

    except Exception as es:
        # cannot read, return None
        getLogger().debug(f'skipping ccpnLogging')

    else:
        return keys


def getCcpnNefLog(project: 'Project', name: str):
    """Get the required ccpnNefLogging dataframe from the project
    Returns a COPY of pandas dataFrame of the ccpn nef log for use in nef import/export
    to ensure integrity
    If a dataFrame cannot be found, logs an error and returns None

    Columns are:
        date, username, program_name, program_version, script_name, input_uuid, saveframe, comment

    Raise an error if there are any issues reading parameters

    :param project: instance of type Project
    :param name: string name of the log
    :return: pandas dataFrame, value or None
    """
    if not (name and isinstance(name, str)):
        raise ValueError(f'ccpnLogging.name {repr(name)} must be a string')

    try:
        # get the correct parameters from data
        data = project._wrappedData.data
        ccpnLogging = data.get(CCPNLOGGING)
        val = ccpnLogging[name].copy()
        if isinstance(val, pd.DataFrame):
            # remove any NaN that may be there from load/save
            val.replace([np.nan], [None], inplace=True)
        else:
            raise ValueError('pd.DataFrame not found')

    except Exception as es:
        # cannot read, return None
        getLogger().debug(f'skipping ccpnLogging')  # {repr(name)}: {es}')

    else:
        return val


def setCcpnNefLog(project: 'Project', name: str, dataFrame: Optional[pd.DataFrame]=None, overwrite=False):
    """Set the required ccpnNefLogging dataframe in the project for use in nef import/export
    Stores a COPY of the dataFrame in the log

    Raise an error if name or value are of the wrong types
    Returns False if the ccpnLogging already exists and overwrite is False

    Columns are enforced to be:
        date, username, program_name, program_version, script_name, input_uuid, saveframe, comment
    Other columns will be ignored
    If value is None, wll create an empty dataFrame

    :param project: instance of type Project
    :param name: string name of the log
    :param dataFrame: pandas dataFrame or None
    :param overwrite: True/False
    :return: True if successful
    """

    # check parameters
    if not (name and isinstance(name, str)):
        raise ValueError(f'ccpnLogging.name {repr(name)} must be a string')
    if not isinstance(dataFrame, (pd.DataFrame, type(None))):
        raise ValueError(f'ccpnLogging.value {repr(dataFrame)} must be a pandas dataFrame or None')

    # set the empty data
    data = project._wrappedData.data
    if data is None:
        data = project._wrappedData.data = {}

    ccpnLogging = data.setdefault(CCPNLOGGING, {})
    param = ccpnLogging.get(name)
    if param is not None and not overwrite:
        getLogger().warning(f'ccpnLogging {repr(name)} exists')
        return

    try:
        # try and write the information to the parameters
        mapping = nef2CcpnMap[NEFMAPPING]
        df = pd.DataFrame(columns=list(mapping.keys()))
        if dataFrame is not None:
            # enforce the correct columns
            for col in df.columns:
                if col in dataFrame.columns:
                    df[col] = dataFrame[col]
            # remove any NaN that may be there from load/save
            df.replace([np.nan], [None], inplace=True)

        # write a copy into data
        ccpnLogging[name] = df

    except Exception as es:
        raise RuntimeError(f'Error creating ccpnLogging history {repr(name)}: {es}')

    else:
        # Explicit flag assignment to enforce saving
        project._wrappedData.__dict__['isModified'] = True

        # operation was successful
        return True


def resetCcpnNefLog(project: 'Project', name: str, overwrite=False):
    """reset the required ccpnNefLogging dataframe in the project for use in nef import/export

    Raise an error if name is not a string
    Returns False if the ccpnLogging already exists and overwrite is False

    Creates empty dataframe with columns:
        date, username, program_name, program_version, script_name, input_uuid, saveframe, comment

    :param project: instance of type Project
    :param name: string name of the log
    :param overwrite: True/False
    :return: True if successful
    """
    if not (name and isinstance(name, str)):
        raise ValueError(f'ccpnLogging.name {repr(name)} must be a string')

    try:
        # set the empty data
        data = project._wrappedData.data
        if data is None:
            data = project._wrappedData.data = {}

        ccpnLogging = data.setdefault(CCPNLOGGING, {})
        param = ccpnLogging.get(name)
        if param is not None and not overwrite:
            getLogger().warning(f'ccpnLogging {repr(name)} exists')
            return

        # create a new empty dataframe with the correct columns
        mapping = nef2CcpnMap[NEFMAPPING]
        ccpnLogging[name] = pd.DataFrame(columns=list(mapping.keys()))

    except Exception as es:
        getLogger().debug(f'Error resetting ccpnLogging {repr(name)}: {es}')

    else:
        # Explicit flag assignment to enforce saving
        project._wrappedData.__dict__['isModified'] = True

        # operation was successful
        return True
