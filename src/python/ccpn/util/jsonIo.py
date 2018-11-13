"""Local enhancements to json, adding support for reading and writing
pandas.Series, pandas.DataFrame, pandas.Panel, numpy.ndarray, OrderedDict,
and ccpnmodel.ccpncore.Tensor


"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:58 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================

__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import json
import numpy
import pandas
from collections import OrderedDict

def load(fp, **kwds):
  """Load json from file fp with extended object type support"""
  return json.load(fp, object_pairs_hook=_ccpnObjectPairHook, **kwds)

def loads(s:str, **kwds):
  """Load json from string s with extended object type support"""
  return json.loads(s, object_pairs_hook=_ccpnObjectPairHook, **kwds)

def dump(obj:object, fp:str, indent:int=2, **kwds):
  """Dump object to json file with extended object type support"""
  return json.dump(obj, fp, indent=indent, cls=_CcpnMultiEncoder, **kwds)

def dumps(obj:object, indent:int=2, **kwds):
  """Dump object to json string with extended object type support"""
  return json.dumps(obj, indent=indent, cls=_CcpnMultiEncoder, **kwds)


class _CcpnMultiEncoder(json.JSONEncoder):
  """Overrides normal JSON encoder, supporting additional types.
  """
  def default(self, obj):

    # Sentinel - reset if we find a supported type
    typ = None

    try:
      from ccpn.util.StructureData import EnsembleData
    except ImportError:
      EnsembleData = None

    if isinstance(obj, OrderedDict):
      typ = 'OrderedDict'
      data = list(obj.items())

    elif EnsembleData is not None and isinstance(obj,EnsembleData):
      # Works like pandas.DataFrame (see comments there), but instantiates subclass.
      typ = 'ccpn.EnsembleData'
      data = obj.to_json(orient='split')

    elif isinstance(obj, pandas.DataFrame):
      # NB this converts both None and NaN to 'null'
      # We assume that pandas will get back the correct value from the type of the array
      # (NaN in numeric data, None in object data).
      typ = 'pandas.DataFrame'
      data = obj.to_json(orient='split')

    elif isinstance(obj, pandas.Series):
      # NB this converts both None and NaN to 'null'
      # We assume that pandas will get back the correct value from the type of teh array
      # (NaN in numeric data, None in object data).
      typ = 'pandas.Series'
      data = obj.to_json(orient='split')

    elif isinstance(obj, pandas.Panel):
      # NBNB NOT TESTED
      frame = obj.to_frame()
      data = frame.to_json(orient='split')

    elif isinstance(obj, numpy.ndarray):
      typ = 'numpy.ndarray'
      data = obj.tolist()

    else:
      try:
        # Put here to avoid circular imports
        from ccpn.util.Tensor import Tensor
        if isinstance(obj, Tensor):
          typ = 'ccpncore.Tensor'
          data = obj._toDict()
      except ImportError:
        pass

    # We are done.
    if typ is None:
      # Let the base class default method raise the TypeError
      return json.JSONEncoder.default(self, obj)

    else:
      # NB we assume that this OrderedDict will not be further processed, but that its contents will
      return OrderedDict((('__type__',typ),('__data__',data)))


def _ccpnObjectPairHook(pairs):
  if len(pairs) == 2:
    tag1,typ = pairs[0]
    tag2, data = pairs[1]
    if tag1 == '__type__' and tag2 == '__data__':

      if typ == 'OrderedDict':
        return OrderedDict(data)

      elif typ == 'ccpn.EnsembleData':

        try:
          from ccpn.util.StructureData import EnsembleData
        except ImportError:
          EnsembleData = None

        if EnsembleData is None:
          return pandas.read_json(data, orient='split')
        else:

          # NBNB HACK:
          # We want the pandas read_json to instantiate EnsembleData, which is a subclass
          # of DataFrame. Hence this temporary monkeypatching
          from pandas.io import json as pandasJson
          backup= pandasJson.DataFrame
          pandasJson.DataFrame = EnsembleData
          result = None
          try:
            result = pandas.read_json(data, orient='split')
          finally:
            pandasJson.DataFrame = backup
          return result

      elif typ == 'pandas.DataFrame':
        # return pandas.DataFrame(data=data.get('data'), index=data.get('index'),
        #                         columns=data.get('columns'))
        return pandas.read_json(data, orient='split')

      elif typ == 'pandas.Panel':
        # NBNB NOT TESTED
        return pandas.read_json(data, orient='split').to_panel()

      elif typ == 'pandas.Series':
        # columns = data.get('columns')
        # # Does the series name get stored in columns? Presumably. Let us try
        # name = columns[0] if columns else None
        # return pandas.Series(data=data.get('data'), index=data.get('index'),
        #                      name=name)
        return pandas.read_json(data, typ='series', orient='split')

      elif typ == 'numpy.ndarray':
        return numpy.array(data)

      elif typ == 'ccpncore.Tensor':
        # Put here to avoid circular imports
        from ccpn.util.Tensor import Tensor
        return Tensor._fromDict(data)

  # default option, std json behaviouor
  return dict(pairs)
