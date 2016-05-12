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
__author__ = 'rhf22'

#
# Import the Implementation package - this is the root package
#

from ccpn.util import Io as ioUtil

# Put project inside this directory
projectPath = './local.'
projectName = 'test'

#
# Import the Molecule and MolSystem packages

#
# Python standard stuff
#

def doTest():

  project = newProject()
  project.saveModified()
  del project

  project2 = ioUtil.loadProject(path=projectPath, projectName=projectName)
  ioUtil.saveProject(project2, newProjectName=projectName+'_out')



def newProject():

  project = ioUtil.newProject(projectName=projectName, overwriteExisting=True)

  # Make molecule using API

  molecule1 =  project.newMolecule(name='molecule1')
  #

  exampleSequence = ['Ala','Gly','Tyr','Glu','Leu','Gly','Ser','His','Ile']

  for seqPosition, ccpCode in enumerate(exampleSequence):

    chemComp = project.findFirstChemComp(molType='protein', ccpCode=ccpCode)

    if seqPosition == 0:
      linking = 'start'
    elif seqPosition == len(exampleSequence) - 1:
      linking = 'end'
    else:
      linking = 'middle'

    chemCompVar = chemComp.findFirstChemCompVar(linking=linking, isDefaultVar=True)

    molRes = molecule1.newMolResidue(chemComp=chemComp,seqCode=seqPosition+5,
                                    chemCompVar=chemCompVar)

    if linking != 'start':
      prevLink = molRes.findFirstMolResLinkEnd(linkCode = 'prev')
      prevMolRes = molecule1.sortedMolResidues()[-1]
      if prevLink and prevMolRes:
        nextLink = prevMolRes.findFirstMolResLinkEnd(linkCode = 'next')
        if nextLink:
          molecule1.newMolResLink(molResLinkEnds=(nextLink,prevLink))


  molSystem = project.newMolSystem(code='MS1', name = 'MolSystem1')

  #
  # Now create a homodimer - two chains referring to the same Molecule
  #

  molSystem.newChain(molSystem,code='A', molecule=molecule1)
  molSystem.newChain(molSystem,code='B', molecule=molecule1)


  project.checkAllValid(complete=True)

  #
  # Write out the project.
  #

  project.saveModified()

  #
  return project

if __name__ == '__main__':
    doTest()