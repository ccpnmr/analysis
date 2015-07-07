"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
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
from ccpn.testing.Testing import Testing

# NBNB These two imports are NECESSARY, as ccpnmr MUST be imported to register the Gui classes
import ccpn
import ccpnmr

class MarkTest(Testing):

  axisCodes = ('H', 'Hn', 'C', 'C')
  positions = (4.33, 7.92, 49.65, 17.28)
  units = ('ppm', 'ppm', 'ppm', 'Hz')
  labels = ('Proton', 'NHproton', 'carbon', 'carbonhz')

  def __init__(self, *args, **kw):
    Testing.__init__(self, 'CcpnCourse1a', *args, **kw)

  def test_create_mark(self):
    self.task = self.project.newTask('TestTask')
    mark1 = self.task.newMark('red', positions=self.positions, axisCodes=self.axisCodes,
                               units=self.units, labels=self.labels)
    assert mark1.positions == self.positions
    assert mark1.axisCodes == self.axisCodes
    assert mark1.units == self.units
    assert mark1.labels == self.labels

    mark1.delete()
    self.task.delete()

  def test_extend_mark(self):
    data = ('Hc', 1.27, None, None)
    self.task = self.project.newTask('TestTask')
    mark1 = self.task.newMark('red', positions=self.positions, axisCodes=self.axisCodes,
                               units=self.units, labels=self.labels)
    mark1.newLine(*data)

    ll = list(zip(self.axisCodes, self.positions, self.units, self.labels))
    ll.append(('Hc', 1.27, 'ppm', None))

    assert mark1.rulerData == tuple(ccpnmr.RulerData(*x) for x in ll)

    mark1.delete()
    self.task.delete()

  def test_create_single_mark(self):
    self.task = self.project.newTask('TestTask')
    data = ('Hc', 1.27, None, None)
    mark1 = self.task.newSimpleMark('red', data[0], data[1])
    print('mark1.rulerData', mark1.rulerData)
    assert  mark1.rulerData == (ccpnmr.RulerData('Hc', 1.27, 'ppm', None),)

    self.task.delete()
