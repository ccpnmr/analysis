"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-04-07 11:40:44 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"

__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================
from ccpn.core.testing.WrapperTesting import WrapperTesting

# NBNB These two imports are NECESSARY,
# as  ccpn.ui.gui.core MUST be imported to register the Gui classes
from ccpn.ui._implementation import Mark


class MarkTest(WrapperTesting):

  # Path of project to load (None for new project)
  projectPath = 'CcpnCourse1a'

  axisCodes = ('H', 'Hn', 'C', 'C')
  positions = (4.33, 7.92, 49.65, 17.28)
  units = ('ppm', 'ppm', 'ppm', 'Hz')
  labels = ('Proton', 'NHproton', 'carbon', 'carbonhz')

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
    data = (1.27, 'Hc', None, None)
    self.task = self.project.newTask('TestTask')
    mark1 = self.task.newMark('red', positions=self.positions, axisCodes=self.axisCodes,
                               units=self.units, labels=self.labels)
    mark1.newLine(*data)

    ll = list(zip(self.positions, self.axisCodes, self.units, self.labels))
    ll.append((1.27, 'Hc', 'ppm', None))

    assert mark1.rulerData == tuple(Mark.RulerData(*x) for x in ll)

    mark1.delete()
    self.task.delete()

  def test_create_single_mark(self):
    self.task = self.project.newTask('TestTask')
    data = (1.27, 'Hc', None, None)
    mark1 = self.task.newSimpleMark('red', data[0], data[1])
    assert  mark1.rulerData == (Mark.RulerData(1.27, 'Hc', 'ppm', None),)

    self.task.delete()
