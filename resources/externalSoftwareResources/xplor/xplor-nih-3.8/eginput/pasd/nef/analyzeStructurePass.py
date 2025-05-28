
opts,args = xplor.parseArguments([
    ("inPassName","name","name of structure calculation pass to analyze"),
    ("outPassName","name","name of next PASD pass"),
    ("refFilename","filename","filename of reference structure"),
    ("structureGlob","glob","glob matching calculated structures"),
    ("likelihoodCut","val",
     "likelihood cutoff, below which peak assignments will be disabled."),
                          
])

refFilename=None
inFileGlob="INPASS_[0-9]*.pdb"
inPassName="pass2"
outPassName="pass3"
highLikelihoodCutoff=0.25
for opt in opts:
    if opt[0]=="refFilename":
        refFilename=opt[1]
        pass
    if opt[0]=="structureGlob":
        inFileGlob=opt[1]
        pass
    if opt[0]=="inPassName":
        inPassName=opt[1]
        pass
    if opt[0]=="outPassName":
        outPassName=opt[1]
        pass
    if opt[0]=="likelihoodCut":
        highLikelihoodCutoff=float(opt[1])
        pass
pass

nefFile=args[0]
pasdFiles=args[1:]

import protocol

protocol.initParams("protein")
from nefTools import readNEF 
nef = readNEF(nefFile) # generates PSF information

from iupacNaming import toIUPAC
toIUPAC()

from atomAction import genRandomCoords
genRandomCoords()

from potList import PotList
pasdPots = PotList()
for file in pasdFiles:
    name='_'.join( file.split('_')[:-1] )
    from pasdPotTools import create_PASDPot
    noePot=create_PASDPot(name,
                          pasdFilename=file)

    noePot.setUseSingleAssignment(True)
    pasdPots.append(noePot)
    print( noePot.instanceName(), len(noePot.peaks()))
    pass

import simulation
simulation.makeCurrent( xplor.simulation )

import pasd
pasd.updateUser_enabled=True

from pasd.protocol import processStructurePass
processStructurePass(pasdPots,
                          filenames=inFileGlob,
                          inPassName=inPassName,
                          outPassName=outPassName,
                          refStructFilename=refFilename,
                          highLikelihoodCutoff=highLikelihoodCutoff,
                          violCutoff=0.5)

