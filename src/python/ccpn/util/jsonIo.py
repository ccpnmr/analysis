"""Local enhancements to json, adding support for reading and writing
pandas.Series, pandas.DataFrame, pandas.Panel, numpy.ndarray, OrderedDict,
and ccpnmodel.ccpncore.Tensor


"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                 " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

import json
import numpy
import pandas
from collections import OrderedDict

def load(fp, **kw):
  """Load json from file fp with extended object type support"""
  return json.load(fp, object_pairs_hook=_ccpnObjectPairHook, **kw)

def loads(s:str, **kw):
  """Load json from string s with extended object type support"""
  return json.loads(s, object_pairs_hook=_ccpnObjectPairHook, **kw)

def dump(obj:object, fp:str, indent:int=2, **kw):
  """Dump object to json file with extended object type support"""
  return json.dump(obj, fp, indent=indent, cls=_CcpnMultiEncoder, **kw)

def dumps(obj:object, indent:int=2, **kw):
  """Dump object to json string with extended object type support"""
  return json.dumps(obj, indent=indent, cls=_CcpnMultiEncoder, **kw)


class _CcpnMultiEncoder(json.JSONEncoder):
  """Overrides normal JSON encoder, supporting additional types.
  """
  def default(self, obj):

    # Sentinel - reset if we find a supported type
    typ = None

    if isinstance(obj, OrderedDict):
      typ = 'OrderedDict'
      data = list(obj.items())

    elif isinstance(obj, pandas.DataFrame):
      # NB this converts both None and NaN to 'null'
      # We assume that pandas will get back the correct value from the type of teh array
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
      typ = 'pandas.Panel'
      data = list( ( (item, obj.loc[item ,: , :])
                            for item in obj.items() ) )

    elif isinstance(obj, numpy.ndarray):
      typ = 'numpy.ndarray'
      data = obj.toList()

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
      return OrderedDict(('__type__',typ),('__data__',data))


def _ccpnObjectPairHook(pairs):
  if len(pairs) == 2:
    tag1,typ = pairs[0]
    tag2, data = pairs[1]
    if tag1 == '__type__' and tag2 == '__data__':

      if typ == 'OrderedDict':
        return OrderedDict(data)

      elif typ == 'pandas.DataFrame':
        return pandas.DataFrame(data=data.get('data'), index=data.get('index'),
                                columns=data.get('columns'))

      elif typ == 'pandas.Panel':
        # NBNB TBD CHECKME this may well not work!!!
        return pandas.Panel(data=OrderedDict(data))

      elif typ == 'pandas.Series':
        columns = data.get('columns')
        # Does the series name get stored in columns? Presumably. Let us try
        name = columns[0] if columns else None
        return pandas.Series(data=data.get('data'), index=data.get('index'),
                             name=name)

      elif typ == 'numpy.ndarray':
        return numpy.ndarray(data)

      elif typ == 'ccpncore.Tensor':
        # Put here to avoid circular imports
        from ccpn.util.Tensor import Tensor
        return Tensor._fromDict(data)

  # default option, std json behaviouor
  return dict(pairs)