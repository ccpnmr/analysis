"""
Functions to read/write parameters to a dataSet.
The dataSet parameters are stored/restored as a ccpn_parameter saveframe
in nef files.
The value is stored as a ccpn_value item in the saveframe or as a ccpn_dataframe loop.
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
__dateModified__ = "$dateModified: 2021-07-29 21:10:24 +0100 (Thu, July 29, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2021-07-07 12:49:23 +0100 (Wed, July 07, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util.Logging import getLogger
import pandas as pd


CCPNPARAMETER = 'ccpnDataSetParameter'
CCPNLOOP = 'ccpnDataFrame'


def getCcpnNefParameter(project: 'Project', dataSet, serial, name, parameterName):
    """Get the required dataSet parameter from the project
    Returns a python object/pandas dataFrame of the ccpn nef log for use in nef import/export
    If a dataFrame cannot be found, logs an error and returns None

    Columns defined by the dataframe

    Raises an error if there are any issues reading dataSet parameters

    :param project: instance of type Project
    :param dataSet: dataSet name
    :param serial: dataSet serial
    :param name: data item name
    :return: pandas dataFrame or None
    """
    try:
        # get the correct parameters from the dataSet
        dSet = project.getDataSet(dataSet)
        if dSet and dSet.serial != serial:        
            getLogger().debug(f'dataSet serials do not match: {dSet.serial} != {serial}')
        
        dd = dSet.getData(name)
        params = dd.parameters

        # return a copy of the ccpnHistory parameter
        return params.get(parameterName)

    except Exception as es:
        getLogger().debug(f"Cannot read dataSet parameter '{dataSet}:{name}:{parameterName}'")


def setCcpnNefParameter(project: 'Project', dataSet, serial, name, parameterName, value, overwrite=False):
    """Set the required dataSet parameter in the project for use in nef import/export

    Raises an error if name or value are of the wrong types
    Returns False if the dataSet parameter already exists and overwrite is False

    :param project: instance of type Project
    :param dataSet: dataSet name
    :param serial: dataSet serial
    :param name: data item name
    :param value: pandas dataFrame or None
    :param overwrite: True/False
    :return: True if successful
    """
    # check parameters
    if not isinstance(dataSet, str):
        raise ValueError(f'dataSet {repr(dataSet)} must be a string')
    if not isinstance(name, str):
        raise ValueError(f'name {repr(name)} must be a string')

    # get the required dataSet
    dSet = project.getDataSet(dataSet) or project.newDataSet(dataSet)
    if not dSet:
        raise RuntimeError(f'Error creating dataSet {repr(dataSet)}')

    # check whether the data already exists in the dataSet
    # dd = dSet.getData(name)
    # if dd and not overwrite:
    #     getLogger().warning(f'dataSet.data {repr(name)} exists')
    #     return

    try:
        # check whether the data already exists in the dataSet
        # try and write the information to the parameters
        dd = dSet.getData(name) or dSet.newData(name=name)
        if parameterName in dd.parameters and not overwrite:
            getLogger().warning(f'dataSet.data parameter {repr(parameterName)} exists')
            return

        dd.setParameter(parameterName, value)
    except Exception as es:
        raise RuntimeError(f'Error creating dataSet parameter {repr(parameterName)}')

    # operation was successful
    return True
