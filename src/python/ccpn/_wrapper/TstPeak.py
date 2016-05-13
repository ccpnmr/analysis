""" Test of an API-indepenent wrapper class

The class function calles ('ccpnXyzProperty) create teh apprproate properties

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
               "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                 " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================


from .WrPeak import WrPeak
from ._PeakList import PeakList
from typing import Tuple, Optional, Union

class Peak(WrPeak):

  #: Short class name, for PID.
  shortClassName = 'PK'

  #: Name of plural link to instances of class
  _pluralLinkName = 'peaks'

  #: List of child classes.
  _childClasses = []

  # Key to Peak class
  WrPeak._key = WrPeak._ccpnKeyProperty('serial',
                                        doc="Key string, distinguishing the peak from its siblings")

  peakList = WrPeak._parent = WrPeak._ccpnProperty('_parent', PeakList, "PeakList containing Peak")

  serial = WrPeak._ccpnProperty('serial', int, "serial number, key attribute for Peak")

  height = WrPeak._ccpnProperty('height', float, "height of Peak",
                                optional=True, settable=True)

  heightError = WrPeak._ccpnProperty('heightError', float, "height error of Peak",
                                     optional=True, settable=True)

  volume = WrPeak._ccpnProperty('volume', float, "volume of Peak",
                                optional=True, settable=True)

  volumeError = WrPeak._ccpnProperty('volumeError', float, "volume error of Peak",
                                     optional=True, settable=True)

  figureOfMerit = WrPeak._ccpnProperty('figureOfMerit', float, "figure of merit for Peak",
                                       optional=False, settable=True)

  annotation = WrPeak._ccpnProperty('annotation', str, "Peak text annotation",
                                    optional=True, settable=True)

  comment = WrPeak._ccpnProperty('comment', str, "Peak test annotation",
                                    optional=True, settable=True)

  # Defined explicitly here, instead of the Implementation class.
  # This is a derived property, so it can be done without referring to the API layer
  @property
  def axisCodes(self) -> Tuple[Optional[str], ...]:
    """Spectrum axis codes in dimension order matching position."""
    return self.peakList.spectrum.axisCodes

  position = WrPeak._listViewProperty('position', float,
                 "Peak position in ppm (or other relevant unit) in dimension order.",
                  optional=True, settable=True)

  positionError = WrPeak._listViewProperty('positionError', float,
                 "Peak position error in ppm (or other relevant unit) in dimension order.",
                  optional=True, settable=True)

  pointPosition = WrPeak._listViewProperty('pointPosition', float,
                 "Peak position in points in dimension order.",
                  optional=True, settable=True)

  doc = """The full width of the peak footprint in points for each dimension,
  i.e. the width of the area that should be considered for integration, fitting, etc. ."""
  boxWidths = WrPeak._listViewProperty('boxWidths', float, doc, optional=True, settable=True)

  lineWidths = WrPeak._listViewProperty('lineWidths', float,
                            "Full-width-half-height of peak/multiplet for each dimension, in Hz.",
                            optional=True, settable=True)


  # # This is a special case, but the special coding is all in the superclass
  # doc = """Peak dimension assignment - a ListViewProperty of lists of NmrAtoms.
  #   Assignments as a list of individual combination tuples is given in 'assignedNmrAtoms'.
  #   Setting dimensionAssignments implies that all combinations are possible"""
  # dimensionNmrAtoms = WrPeak._listViewProperty('dimensionNmrAtoms', 'ListView[NmrAtom]', doc,
  #                                              optional=False, settable=False)


  # This is a special case, but the special coding is all in the superclass
  doc = """Peak assignment - a ListView of tuples of NmrAtom combinations
    (e.g. a ListView of triplets for a 3D spectrum). Missing assignments are entered as None
    Assignments per dimension are given in 'dimensionNmrAtoms'."""
  assignedNmrAtoms = WrPeak._ccpnSimpleProperty('assignedNmrAtoms', Tuple[Optional['NmrAtom'], ...],
                                                doc, optional=False, settable=True)

# Connections to parents:
PeakList._childClasses.append(Peak)