from ccpncore.util.Classes import NmrAtom



class LinkedNmrAtom(NmrAtom):
  """Add here functions to extract data related to NmrAtom"""

  _nmrProject = None

  # NBNB TBD add functions to extract information from NmrAtom data and _nmrProject link

def makeNmrAtom(nmrProject, *args, **kwargs):
  """get NmrAtom linked to NmrProject"""

  result = LinkedNmrAtom(*args, **kwargs)
  result._nmrProject = nmrProject
  #
  return result
