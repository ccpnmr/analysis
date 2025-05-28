
opts,args = xplor.parseArguments(["deuterated:0",
                                  "intermolecular:0",
                                  "intramolecular:0",
                                  "intensityThreshold:1",
                                  "refFilename:1"])
nefFile=args[0]
spectrumName=args[1]


deuterated=False
onlyIntermolecular=False
onlyIntramolecular=False
refFilename=None
intensityThreshold=None
for opt in opts:
    if opt[0]=="deuterated":
        deuterated=True
        pass
    if opt[0]=="intermolecular":
        onlyIntermolecular=True
        pass
    if opt[0]=="intramolecular":
        onlyIntramolecular=True
        pass
    if opt[0]=="refFilename":
        refFilename=opt[1]
        pass
    if opt[0]=="intensityThreshold":
        intensityThreshold=float(opt[1])
        pass
    pass

if onlyIntermolecular and onlyIntramolecular:
    raise Exception("only one of -intermolecular or -intramolecular" +
                    " may be specified")

    
import os
rootName=os.path.splitext(nefFile)[0]

import iupacNaming
print("naming:",iupacNaming.getCurrentScheme())

from nefTools import readNEF 
nef = readNEF(nefFile) # generates PSF information
#you might want a PSF at some later stage
#xplor.command("write psf output="+rootName+".psf end")

print("naming2:",iupacNaming.getCurrentScheme(verbose=True))

from atomAction import genRandomCoords
genRandomCoords()

import iupacNaming
iupacNaming.toIUPAC()
if not iupacNaming.getCurrentScheme(check=True)== "IUPAC":
    raise Exception("must be in IUPAC mode")


import pasd                   #load chemical shifts from NEF data
shifts = pasd.nefShifts(nef)

from pasdPot import NOEPot    #create PASD energy term
noePot=NOEPot('marv')
noePot.setUseSingleAssignment(True)


                              #read the NEF peak data and load it into
                              #the PASD noePot.
                              #  Make sure that the columns are identified
                              #  correctly.
peakInfo = pasd.nefPeaks(nef,
                         noePot,
                         name=spectrumName,
                         )
#if int(peakInfo['numDims'])!=3:
#    print("only 3-dimensional spectra handled by this script")
#    exit(1)
#    pass

peakRemarks=peakInfo['remarks']

if intensityThreshold:
    from pasd.peakTools import removeLowIntensityPeaks
    peakRemarks += removeLowIntensityPeaks(noePot,intensityThreshold)
    pass
          

#prints to stdout
unassigned = pasd.findUnassignedAtoms(shifts)
print(unassigned.message)

## 
## If the spectrum is taken in D2O, don't create to shiftAssignments 
## for exchangeable protons

if deuterated:
    fromProtonSel = toProtonSel="""
    name h* and not (name hn ht* or (resn thr and name hg1) or 
    (resn ser and name hg) or (resn lys and name hz*) or 
    (resn tyr and name hh) or (resn arg and name hh*) or
    (resn arg and name he) or (resn asn and name hd*) or
    (resn gln and name he*))"""
else:
    fromProtonSel = toProtonSel="name h*"
    pass

kwargs={}

fromHeavyatomSel=None
if peakInfo["fromHeavyatom"]:
    if peakInfo["fromHeavyatom"]=="13C":
        fromHeavyatomSel="name C*"
    elif peakInfo["fromHeavyatom"]=="15N":
        fromHeavyatomSel="name N*"
    else:
        print("unknown from heavy atom:",peakInfo["fromHeavyatom"])
        exit(1)
        pass
    fromProtonSel="segid A and name H* and bondedto (%s)" % fromHeavyatomSel
    kwargs['fromHeavyatomRange'] =peakInfo["fromHeavyatomSpectralRange"]
    pass
    
toHeavyatomSel=None
if peakInfo["toHeavyatom"]:
    if peakInfo["toHeavyatom"]=="13C":
        toHeavyatomSel="name C*"
    elif peakInfo["toHeavyatom"]=="15N":
        toHeavyatomSel="name N*"
    else:
        print("unknown to heavy atom:",peakInfo["toHeavyatom"])
        exit(1)
        pass
    toProtonSel="segid A and name H* and bondedto (%s)" % toHeavyatomSel
    kwargs['toHeavyatomRange'] =peakInfo["toHeavyatomSpectralRange"]
    pass
    


if onlyIntermolecular:
    toProtonSel = f"({toProtonSel}) and segid B"
    pass

from pasd import createShiftAssignments
assignmentInfo=createShiftAssignments(shifts,noePot,
                                      fromProtonSel=fromProtonSel,
                                      fromHeavySel=fromHeavyatomSel,
                                      toProtonSel=toProtonSel,
                                      toHeavySel=toHeavyatomSel,
                                      fromProtonSolventRange=[4.6, 4.8],
                                      namePrefix=spectrumName)

(exceptionsFilename, 
 peaksFilename,      
 shiftAssignFilename) = (spectrumName+"_pass1."+suff for suff in
                         "exceptions peaks shiftAssignments".split())


saRemarks = assignmentInfo
from pasd.protocol import standardInitMatch

standardInitMatch(noePot,
                  useIndividualTols=False,
                  refStructFilename=refFilename,
                  saRemarks=saRemarks,
                  peakRemarks=peakRemarks,
                  fromProtonTightTol=0.02,
                  toProtonTightTol=0.02,
                  writeEachStage=False,
                  writeFiles="combined",
                  filenamePrefix=spectrumName+"_pass1",
                  fromProtonRange=peakInfo["fromProtonSpectralRange"],
                  toProtonRange=peakInfo["toProtonSpectralRange"],
                  **kwargs)

#    -referenceStructureFile     reference.pdb 
#    -fromProtonSolventRange [list 4.6 4.8] 


