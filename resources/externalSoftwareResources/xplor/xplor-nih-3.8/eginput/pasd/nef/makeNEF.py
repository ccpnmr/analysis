#
# Script for generating a unified NEF restraint file from
# Talos and PASD output.
#

xplor.requireVersion("3.0")

# this checks for typos on the command-line. User-customized arguments can
# also be specified.
#
(opts,args) = xplor.parseArguments([
    ("likelihoodCut","val",
     "likelihood cutoff, below which peak assignments will be disabled."),
                                    ])

likelihoodCut=0.9
for opt in opts:
    if opt[0]=="likelihoodCut":
        likelihoodCut=float(opt[1])
        pass
    pass
    

nefFile=args[0]
pasdFilenames=args[1:]

from nefTools import readNEF 
nef = readNEF(nefFile) # generates PSF information

#
# The following will create NEF file containing the distance and dihedral
# restraints.
#

from iupacNaming import toIUPAC
toIUPAC()

from nefTools import genHeader
nefString = genHeader()

#grab the (one for now) chemical shift table from the input NEF, and
# add it to the output NEF string
from nefTools import getBlock, catPrefixes
shiftsBlock = getBlock(nef,'shifts')
shiftsPrefix=catPrefixes['shifts']
name=shiftsBlock[shiftsPrefix].sf_framecode[0][len(shiftsPrefix)+1:]

#      _nef_chemical_shift_list.sf_framecode  nef_chemical_shift_list_ShiftList_2

from nefTools import shifts_writeNEF
nefString += shifts_writeNEF(name,shiftsBlock)

#grab the (one for now) dihedral restraint table from the input NEF, and
# add it to the output NEF string
from nefTools import getBlock, catPrefixes
dihedralBlock = getBlock(nef,'dihedral','1')
dihedralPrefix=catPrefixes['dihedral']
name=dihedralBlock[dihedralPrefix].sf_framecode[0][len(dihedralPrefix)+1:]

import nefTools
dihedral0=nefTools.makeNEF()
dihedral0[dihedralPrefix+'_'+name] = dihedralBlock

nefString += "\n" + dihedral0.asString() + "\n"

#
# copy over pre-existing distance restraints - not derived from the current
# NOE assignment procedure
prefix=catPrefixes['distance']
for name in nefTools.getBlockNames(nef,"distance"):
    block = getBlock(nef,'distance',name)
    
    tmpNEF=nefTools.makeNEF()
    tmpNEF[name] = block
    
    nefString += "\n" + tmpNEF.asString() + "\n"
    pass
        


#grab the spectra used from the input NEF, and
# add them to the output NEF string
spectrumNames=[]
for pasdFilename in pasdFilenames:
    name='_'.join( pasdFilename.split('_')[:-1] )
    print(f"initializing spectrum {name}")
    spectrumNames.append( name )
    
    from nefTools import getBlock, catPrefixes
    block = getBlock(nef,'spectrum',name)
    prefix=catPrefixes['spectrum']
    name=block[prefix].sf_framecode[0][len(prefix)+1:]

    newNEF=nefTools.makeNEF()
    newNEF[prefix+'_'+name] = block

    nefString += "\n" + newNEF.asString() + "\n"
    pass


from tclInterp import TCLInterp
tcl = TCLInterp()

tcl.command("package require aeneas")
tcl.command("package require marvin")

from potList import PotList
pots=[]
linkageInfo=[]
for pasdFilename in pasdFilenames:
    name='_'.join( pasdFilename.split('_')[:-1] )
    print(f"processing PASD file: {pasdFilename} for spectrum {name}")
    from pasdPotTools import create_PASDPot
    noePot = create_PASDPot(name,
                            pasdFilename=pasdFilename)
#    from pasdPot import NOEPot    #create PASD energy term
#    noePot=NOEPot(name)
    pots.append( noePot )
    noePot.useSingleAssignment()

#    #make TCL version of PASD NOEPot
#    from pyInterp import portableStringRep
#    tcl.command("rc_PASDPot noe_%s -this $ptr\n" % name,
#                ("ptr",portableStringRep(noePot)))
#    tcl.command("puts $errorInfo")
#
#    tcl.command("""
#    readShiftAssignments \
#        -fileName "%s_final.shiftAssignments" \
#        -pot noe_%s""" % tuple([name]*2))
#
#
#    tcl.command("""
#    readMarvinPeaks \
#        -fileName "%s_final.peaks" \
#        -pot noe_%s""" % tuple([name]*2))

#    numRemoved = 0
#    for peak in noePot.peaks():
#        if peak.prevLikelihood()  < 0.9:
#            numRemoved += 1
#            noePot.removePeakNamed( peak.name() )
#            pass
#        pass

    from pasd.noeTools import removeLowLikelihoodPeakAssignments
    info = removeLowLikelihoodPeakAssignments(noePot,
                                              cutoff=likelihoodCut)

    numRemoved = info.numRemoved
    from nefTools import nefComment
    nefString += nefComment("""Converted from PASD NOEs
%d Low-likelihood assignments were removed""" % numRemoved)

    from pasdPotTools import writeNEF
    from nefTools import catPrefixes
    s,l= writeNEF(noePot,
                  "{}_{}".format(catPrefixes['distance'],name),
                  )
    nefString += s
    linkageInfo.append(l)
    pass

from pasd.noeTools import makeNEFRestraintLinks
nefString += makeNEFRestraintLinks(spectrumNames,linkageInfo)


#from rdcPotTools import writeNEF
#for medium in list(media.keys()):
#    nefString += writeNEF(media[medium],
#                          "nef_rdc_restraint_list_"+medium)
#    pass

open("out.nef","w").write(nefString)
