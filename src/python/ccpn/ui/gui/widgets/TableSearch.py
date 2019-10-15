"""
Module Documentation here
"""
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
__dateModified__ = "$dateModified: 2018-12-20 15:53:27 +0000 (Thu, December 20, 2018) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2018-12-20 15:44:35 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

import re
import pandas as pd
import numpy as np
from ccpn.util.Logging import getLogger


class PandasSearchObject():
  # class used to store a list of search parameters
  def __init__(self, name, dataFrame=None, searchFilter=None):
    """
    Create a new search object for the given table
    :param name - name for this searchFilter:
    :param dataFrame - dataFrame to search on:
    :param searchFilter - search filter:
    """
    self.name = name
    self._dataFrame = dataFrame
    self._searchFilter = searchFilter

  def __repr__(self):
    unformatted = "DataSearch({}): {} ({})"
    formatted_string = unformatted.format(hex(id(self)),
                                          self.name,
                                          self._searchFilter)
    # if python_version < 3:
    #   formatted_string = unformatted.encode("utf-8")

    return formatted_string

  @property
  def dataFrame(self):
    # return the current attached dataFrame
    return self._dataFrame

  @dataFrame.setter
  def dataFrame(self, dataFrame):
    # attach a dataFrame
    self._dataFrame = dataFrame

  @property
  def searchFilter(self):
    # return the current search filter
    return self._searchFilter

  @searchFilter.setter
  def searchFilter(self, searchFilter):
    # set new search parameters, aftger removing whitespace
    searchFilter = searchFilter.strip()
    self._searchFilter = searchFilter

  def search(self):
    """Applies the filter to the stored dataframe.
    A safe environment dictionary will be created, which stores all allowed
    functions and attributes, which may be used for the filter.
    If any object in the given `searchFilter` could not be found in the
    dictionary, the filter does not apply and returns `False`.
    Returns:
        tuple: A (indexes, success)-tuple, which indicates identified objects
            by applying the filter and if the operation was successful in
            general.
    """
    # there should be a grammar defined and some lexer/parser.
    # instead of this quick-and-dirty implementation.

    safeEnvDict = {
      'freeSearch':self.freeSearch,
      'extentSearch':self.extentSearch,
      'indexSearch':self.indexSearch

    }
    for col in self._dataFrame.columns:
      safeEnvDict[col] = self._dataFrame[col]

    try:
      searchIndex = eval(self._searchFilter, {
        '__builtins__':None}, safeEnvDict)
    except NameError:
      return [], False
    except SyntaxError:
      return [], False
    except ValueError:
      # the use of 'and'/'or' is not valid, need to use binary operators.
      return [], False
    except TypeError:
      # argument must be string or compiled pattern
      return [], False
    return searchIndex, True

  def freeSearch(self, searchString):
    """Execute a free text search for all columns in the dataframe.
    Parameters
    ----------
        searchString (str): Any string which may be contained in a column.
    Returns
    -------
        list: A list containing all indexes with filtered data. Matches
            will be `True`, the remaining items will be `False`. If the
            dataFrame is empty, an empty list will be returned.
    """

    if not self._dataFrame.empty:
      # set question to the indexes of data and set everything to false.
      question = self._dataFrame.index == -9999
      for column in self._dataFrame.columns:
        dfColumn = self._dataFrame[column]
        dfColumn = dfColumn.apply(str)

        question2 = dfColumn.str.contains(searchString,
                                          flags=re.IGNORECASE,
                                          regex=True, na=False)
        question = np.logical_or(question, question2)

      return question
    else:
      return []

  def extentSearch(self, xmin, ymin, xmax, ymax):
    """Filters the data by a geographical bounding box.
    The bounding box is given as lower left point coordinates and upper
    right point coordinates.
    Note:
        It's necessary that the dataframe has a `lat` and `lng` column
        in order to apply the filter.
        Check if the method could be removed in the future. (could be done
        via freeSearch)
    Returns
    -------
        list: A list containing all indexes with filtered data. Matches
            will be `True`, the remaining items will be `False`. If the
            dataFrame is empty, an empty list will be returned.
    """
    if not self._dataFrame.empty:
      try:
        questionMin = (self._dataFrame.lat >= xmin) & (
            self._dataFrame.lng >= ymin)
        questionMax = (self._dataFrame.lat <= xmax) & (
            self._dataFrame.lng <= ymax)
        return np.logical_and(questionMin, questionMax)
      except AttributeError:
        return []
    else:
      return []

  def indexSearch(self, indexes):
    """Filters the data by a list of indexes.
    Args:
        indexes (list of int): List of index numbers to return.
    Returns:
        list: A list containing all indexes with filtered data. Matches
        will be `True`, the remaining items will be `False`. If the
        dataFrame is empty, an empty list will be returned.
    """

    if not self._dataFrame.empty:
      filter0 = self._dataFrame.index == -9999
      for index in indexes:
        filter1 = self._dataFrame.index == index
        filter0 = np.logical_or(filter0, filter1)

      return filter0
    else:
      return []
