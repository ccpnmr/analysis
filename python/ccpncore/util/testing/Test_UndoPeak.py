"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
from ccpncore.util.Undo import Undo
# from ccpncore.util import Io as ioUtil
from ccpncore.testing.CoreTesting import CoreTesting

class PeakUndoTest(CoreTesting):

  # Path of project to load (None for new project)
  projectPath = 'CcpnCourse1b'
    
  def test_new_peak_undo(self):
    
    project = self.project
    nmrProject = project.currentNmrProject or project.findFirstNmrProject()
    experiment = nmrProject.findFirstExperiment(name='HSQC')
    dataSource = experiment.findFirstDataSource(name='HSQC-115')
    peakList = dataSource.newPeakList()
    
    project._undo = Undo()
    project._undo.newWaypoint()
    print('@~@~ project undo stack size before newPeak: %d' % len(project._undo))
    peak = peakList.newPeak()
    print('@~@~ project undo stack size after newPeak: %d' % len(project._undo))
    project._undo.undo()
    print('@~@~ project undo stack size after undo: %d' % len(project._undo))
    assert len(peakList.peaks) == 0, 'len(peakList.peaks) = %d' % len(peakList.peaks)
    
  def test_new_peak_undo_redo(self):
    
    project = self.project
    nmrProject = project.currentNmrProject or project.findFirstNmrProject()
    experiment = nmrProject.findFirstExperiment(name='HSQC')
    dataSource = experiment.findFirstDataSource(name='HSQC-115')
    peakList = dataSource.newPeakList()
    
    project._undo = Undo()
    project._undo.newWaypoint()
    print('@~@~ project undo stack size before newPeak: %d' % len(project._undo))
    peak = peakList.newPeak()
    print('@~@~ project undo stack size after newPeak: %d' % len(project._undo))
    project._undo.undo()
    print('@~@~ project undo stack size after undo: %d' % len(project._undo))
    project._undo.redo()
    print('@~@~ project undo stack size after redo: %d' % len(project._undo))
    assert len(peakList.peaks) == 1, 'len(peakList.peaks) = %d' % len(peakList.peaks)
    
 
