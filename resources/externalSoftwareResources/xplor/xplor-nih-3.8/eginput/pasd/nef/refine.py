(opts,args) = xplor.parseArguments([
    ("nef","filename","Name of input NEF file specifying sequence and " +
                      "restraints."),
    ("dist","saveframe name", "name of one or more distance restraint " +
                             "saveframe to use in structure calculation. " +
                             "If -dist is not specified, all are used. " +
                             "Multiple names can be separated by a space " +
                             "or colon."),
    ("refFilename","filename","name of reference PDB or mmCIF file with "+
                              "comparison structure")])

numberOfStructures=100
nefFile=None
refFilename=None
distBlocks=[]
for opt in opts:
    if opt[0]=="nef": 
        nefFile=opt[1]
        pass
    if opt[0]=="refFilename":
        refFilename=opt[1]
        pass
    if opt[0]=="dist":
        sep=":" if ":" in opt[1] else None
        distBlocks += opt[1].split(sep)
    pass

if nefFile is None:
    print("a NEF file must be specified")
    exit(1)
    pass
                                   

pdbFilesIn = args
if len(pdbFilesIn) == 0:
    print("at least one structure to be refined must be specified")
    exit(1)
    pass


# protocol module has many high-level helper functions.
#
import protocol
protocol.initRandomSeed(3421)   #explicitly set random seed


protocol.initParams("protein")

# generate PSF data from sequence and initialize the correct parameters.
#
#from psfGen import seqToPSF
#seqToPSF('protG.seq')
#protocol.initStruct("g_new.psf") # - or from file


# or read an existing model
#
from nefTools import readNEF
nefData = readNEF(nefFile)

from iupacNaming import toIUPAC, fromIUPAC
toIUPAC()

protocol.initCoords(pdbFilesIn[0],deleteUnknownAtoms=True)



#protocol.fixupCovalentGeom(maxIters=100,useVDW=1)

#
# a PotList contains a list of potential terms. This is used to specify which
# terms are active during refinement.
#
from potList import PotList
potList = PotList()

# parameters to ramp up during the simulated annealing protocol
#
from simulationTools import MultRamp, StaticRamp, InitialParams

rampedParams=[]
highTempParams=[]

# compare atomic Cartesian rmsd with a reference structure
#  backbone and heavy atom RMSDs will be printed in the output
#  structure files
#
from posDiffPotTools import create_PosDiffPot
refRMSD = create_PosDiffPot("refRMSD","name CA C N O",
                            pdbFile=refFilename) if refFilename else None

# orientation Tensor - used with the dipolar coupling term
#  one for each medium
#   For each medium, specify a name, and initial values of Da, Rh.
#
from varTensorTools import create_VarTensor
#media={}
##                        medium  Da   rhombicity
#for (medium,Da,Rh) in [ ('t',   -6.5, 0.62),
#                        ('b',   -9.9, 0.23) ]:
#    oTensor = create_VarTensor(medium)
#    oTensor.setDa(Da)
#    oTensor.setRh(Rh)
#    media[medium] = oTensor
#    pass
#    

#from simulationTools import analyze
#rdcs = PotList('rdcs')
#tensors={}
#from rdcPotTools import readNEF
#for name in ('nef_rdc_restraint_list_t',
#             'nef_rdc_restraint_list_b',):
#    vtens = readNEF(rdcs,nefData[name])
#    tensors[vtens.instanceName()] = vtens
#    pass
#
#potList.append(rdcs)
#rampedParams.append( MultRamp(0.05,5.0, "rdcs.setScale( VALUE )") )
#
## calc. initial tensor orientation
## and setup tensor calculation during simulated annealing
##
#from varTensorTools import calcTensorOrientation, calcTensor
#for tensorName in tensors.keys():
#    calcTensorOrientation(tensors[tensorName])
#    rampedParams.append( StaticRamp("calcTensor(tensors['%s'])" % tensorName) )
#    pass

from noePotTools import create_NOEPot, readNEF
noe = PotList('noe')
potList.append(noe)
import nefTools

if not distBlocks: # load all distance restraints present in the NEF file
    from nefTools import getBlockNames
    distBlocks = getBlockNames(nefData,"distance")
    pass
for name in distBlocks:
    shortName= name.replace(nefTools.catPrefixes['distance']+'_','',1)
    print(f"adding distance restraints from saveframe: {name}")
    term=create_NOEPot(f"noe-{shortName}",nef=nefData,nefRestraintName=name)
    term.setPotType("soft")
    term.setAllowOverlap(False)
    term.setShowAllRestraints(True)
    noe.append( term )
    pass
rampedParams.append( MultRamp(2,30, "noe.setScale( VALUE )") )



from xplorPot import XplorPot

## Set up dihedral angles - 
from dihedralPotTools import create_DihedralPot
dihePot = create_DihedralPot('dihe',nef=nefData,
                           verbose=True)
potList.append( dihePot )
highTempParams.append( StaticRamp("dihePot.setScale(10)") )
rampedParams.append( StaticRamp("dihePot.setScale(200)") )

fromIUPAC()



# gyration volume term 
#
# gyration volume term 
#
#from gyrPotTools import create_GyrPot
#gyr = create_GyrPot("Vgyr",
#                    "all") # selection should exclude disordered tails
#potList.append(gyr)
#rampedParams.append( MultRamp(.002,1,"gyr.setScale(VALUE)") )

# HBPot - knowledge-based hydrogen bond term
#
from hbPotTools import create_HBPot
hb = create_HBPot('hb')
hb.setScale(2.5)
potList.append( hb )

#New torsion angle database potential
#
from torsionDBPotTools import create_TorsionDBPot
torsionDB = create_TorsionDBPot('torsionDB', system='protein')
potList.append( torsionDB )
rampedParams.append( MultRamp(.002,2,"torsionDB.setScale(VALUE)") )

#
# setup parameters for atom-atom repulsive term. (van der Waals-like term)
#
from repelPotTools import create_RepelPot,initRepel
repel = create_RepelPot('repel',selection="not pseudo")
potList.append(repel)
rampedParams.append( StaticRamp("initRepel(repel,use14=False)") )
rampedParams.append( MultRamp(.004,4,  "repel.setScale( VALUE)") )
# nonbonded interaction only between CA atoms
highTempParams.append( StaticRamp("""initRepel(repel,
                                               use14=True,
                                               scale=0.004,
                                               repel=1.2,
                                               moveTol=45,
                                               interactingAtoms='name CA'
                                               )""") )

# Selected 1-4 interactions.
import torsionDBPotTools
repel14 = torsionDBPotTools.create_Terminal14Pot('repel14')
potList.append(repel14)
highTempParams.append(StaticRamp("repel14.setScale(0)"))
rampedParams.append(MultRamp(0.004, 4, "repel14.setScale(VALUE)"))


potList.append( XplorPot("BOND") )
potList.append( XplorPot("ANGL") )
potList['ANGL'].setThreshold( 5 )
rampedParams.append( MultRamp(0.4,1,"potList['ANGL'].setScale(VALUE)") )
potList.append( XplorPot("IMPR") )
potList['IMPR'].setThreshold( 5 )
rampedParams.append( MultRamp(0.1,1,"potList['IMPR'].setScale(VALUE)") )
      


# Give atoms uniform weights, except for the anisotropy axis
#
protocol.massSetup()


# IVM setup
#   the IVM is used for performing dynamics and minimization in torsion-angle
#   space, and in Cartesian space.
#
from ivm import IVM
dyn = IVM()

# reset ivm topology for torsion-angle dynamics
#
dyn.reset()

protocol.torsionTopology(dyn)

# minc used for final cartesian minimization
#
minc = IVM()
protocol.initMinimize(minc)

protocol.cartesianTopology(minc)



# object which performs simulated annealing
#
from simulationTools import AnnealIVM
init_t  = 3000.     # Need high temp and slow annealing to converge
cool = AnnealIVM(initTemp =init_t,
                 finalTemp=25,
                 tempStep =12.5,
                 ivm=dyn,
                 rampedParams = rampedParams)

def accept(potList):
    """
    return True if current structure meets acceptance criteria
    """
    if potList['noe'].violations()>0:
        return False
    if dihePot.violations()>0:
        return False
    if potList['BOND'].violations()>0:
        return False
    if potList['ANGL'].violations()>0:
        return False
    if potList['IMPR'].violations()>1:
        return False
    
    return True

def calcOneStructure(loopInfo):
    """ this function calculates a single structure, performs analysis on the
    structure, and then writes out a pdb file, with remarks.
    """

    # initialize parameters for high temp dynamics.
    InitialParams( rampedParams )
    # high-temp dynamics setup - only need to specify parameters which
    #   differfrom initial values in rampedParams
    InitialParams( highTempParams )

    # high temp dynamics
    #
    protocol.initDynamics(dyn,
                          potList=potList, # potential terms to use
                          bathTemp=init_t,
                          initVelocities=1,
                          finalTime=10,    # stops at 10ps or 5000 steps
                          numSteps=5000,   # whichever comes first
                          printInterval=100)

    dyn.setETolerance( init_t/100 )  #used to det. stepsize. default: t/1000 
    dyn.run()

    # initialize parameters for cooling loop
    InitialParams( rampedParams )


    # initialize integrator for simulated annealing
    #
    protocol.initDynamics(dyn,
                          potList=potList,
                          numSteps=200,       #at each temp: 100 steps or
                          finalTime=.4 ,       # .2ps, whichever is less
                          printInterval=100)

    # perform simulated annealing
    #
    cool.run()
              
              
    # final torsion angle minimization
    #
    protocol.initMinimize(dyn,
                          printInterval=50)
    dyn.run()

    # final all- atom minimization
    #
    protocol.initMinimize(minc,
                          potList=potList,
                          dEPred=10)
    minc.run()

    #do analysis and write structure when this function returns
    toIUPAC()
    from simulationTools import analyze
    protocol.writeCIF( loopInfo.filename()+".cif",
                       remarks=analyze(potList))
    fromIUPAC()
    
    pass



from simulationTools import StructureLoop, FinalParams
StructureLoop(numStructures=numberOfStructures,
              structLoopAction=calcOneStructure,
              pdbFilesIn=pdbFilesIn,
              pdbTemplate="SCRIPT_STRUCTURE.sa",
              doWriteStructures=True,  #analyze and write coords after calc
              genViolationStats=True,
              averagePotList=potList,
              averageCrossTerms=refRMSD,
              averageTopFraction=0.2, #report only on best 20% of structs
#              averageAccept=accept,   #only use structures which pass accept()
              averageContext=FinalParams(rampedParams),
              averageFilename="SCRIPT_ave.pdb",    #generate regularized ave structure
              averageFitSel="name CA C N O",
              averageCompSel="not resname ANI and not name H*"     ).run()

