
opts,args = xplor.parseArguments([
    ("refFilename","filename","filename of reference structure"),
    ("dist","saveframe name", "name of distance restraint saveframe to use "+
                              "to support assignment likelihoods"),
    ("allDist",None, "use all distance restraints in the input NEF file"),
    ("verb",None,"verbose TCL updateUser output"),
])

refFilename=None
distBlocks=[]
for opt in opts:
    if opt[0]=="refFilename":
        refFilename=opt[1]
        pass
    if opt[0]=="dist":
        distBlocks.append( opt[1] )
    if opt[0]=="allDist":
        distBlocks=None
    pass

nefFile=args[0]
pasdFilenames=args[1:]

passName='pass1'

import protocol
protocol.initRandomSeed( 483)

from nefTools import readNEF
nef=readNEF(nefFile)

import iupacNaming
iupacNaming.toIUPAC()  #switch to IUPAC naming

from atomAction import genRandomCoords
genRandomCoords()


# distance restraints, if any present
from noePotTools import create_NOEPot, readNEF
noe=PotList("dist")
if distBlocks is None:
    from nefTools import getBlockNames
    distBlocks = getBlockNames(nef,"distance")
    pass
for name in distBlocks:
    print("reading distance restraint block named " + name)
    pot=create_NOEPot(name,nef=nef,nefRestraintName=name,verbose=True)
    pot.setAllowOverlap(False)
    pot.setShowAllRestraints(True)
    noe.append( pot )
    pass

contacts=[]
for term in noe:
    for r in term.restraints():
        if len(r.selPairs())==1:
            contacts.append( (r.selPairs()[0].a,r.selPairs()[0].b) )
            pass
        pass
    pass


xplor.disableOutput()
xplor.command("set message off echo off end")



import trace
#trace.suspend()

from potList import PotList
noes = PotList()
for pasdFile in pasdFilenames:
    name='_'.join( pasdFile.split('_')[:-1] )
    from pasdPotTools import create_PASDPot
    pot=create_PASDPot(name,
                       pasdFilename=pasdFile)
                   
    pot.setUseSingleAssignment(True)
    noes.append(pot)

    pass

from pasd.protocol import jointFilter

jointFilter(noes,
            assignmentThreshold=20,
            knownContacts=contacts,
            #initScoresFrom="contacts",
            refStructFilename=refFilename,
            deleteNonIntraPAs=True,
            writeFiles="combined")


##
#   The following is from an email from Charles nov. 9, 2018 2:30 PM
##
##   Filenames are generated from filenamePrefix by substituting the PASDPot
##    instanceName for the 'NAME' literal, and then appending .exceptions,
##    .peaks or .shiftAssignments for the respective filenames.
## #
##    Additional arguments:
## #
##    assignmentThreshold - if set, delete all peaks which have more peak
##                          assignments than this value.
## #
##    inactiveAssignmentThreshold - if set, delete peaks with no active peaks,
##                                  but with more assignments than this value.
## #
##    activePAThreshold   - if set, delete peaks with more active peak
##                          assignments than this value.
## #
##    deleteNonIntraPAs   - if True, delete all non-intramolecular peak
##                          assignments if there is an intramolecular peak
##                          assignment.
## #
##    The above filters are run after the network filter.
