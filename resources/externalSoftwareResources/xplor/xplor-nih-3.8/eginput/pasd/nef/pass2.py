
xplor.requireVersion("3.6")




#
# slow cooling protocol in torsion angle space for protein G. Uses 
# NOE, RDC, J-coupling restraints.
#
# this script performs annealing from an extended structure.
# It is faster than the original anneal.py
#
# CDS 2009/07/24
#

# this checks for typos on the command-line. User-customized arguments can
# also be specified.
#
(opts,args) = xplor.parseArguments([
    ("quick",None,"run in quick mode to test that script runs through"),
    ("dist","saveframe name", "name of distance restraint saveframe to use "+
                              "to support assignment likelihoods"),
    ("allDist",None, "use all distance restraints in the input NEF file"),
    ("likelihoodCut","val",
     "likelihood cutoff, below which peak assignments will be disabled."),
    ("refFilename","filename","name of reference PDB or mmCIF file with "+
                              "comparison structure")])

quick=False
refFilename=None

distBlocks=[]
for opt in opts:
    if opt[0]=="quick":  #specify -quick to just test that the script runs
        quick=True
        pass
    if opt[0]=="refFilename":
        refFilename=opt[1]
        pass
    if opt[0]=="dist":
        distBlocks.append( opt[1] )
    if opt[0]=="allDist":
        distBlocks=None
    pass
    if opt[0]=="likelihoodCut":
        highLikelihoodCutoff=float(opt[1])
        pass

nefFile=args[0]
pasdFilenames=args[1:]

# filename for output structures. This string must contain the STRUCTURE
# literal so that each calculated structure has a unique name. The SCRIPT
# literal is replaced by this filename (or stdin if redirected using <),
# but it is optional.
#
outFilename = "SCRIPT_STRUCTURE.pdb"
numberOfStructures=500

if quick:
    numberOfStructures=3
    pass

# protocol module has many high-level helper functions.
#
import protocol

protocol.initRandomSeed()   #set random seed - by time

command = xplor.command

# generate PSF data from sequence and initialize the correct parameters.
#
protocol.initParams('protein')
from nefTools import readNEF 
nef = readNEF(nefFile) # generates PSF information
#protocol.initStruct('cAndNpeaks200205.psf')

# generate random extended initial structure with correct covalent geometry
#
from atomAction import genRandomCoords
genRandomCoords()
#protocol.genExtendedStructure()

#
# a PotList contains a list of potential terms. This is used to specify which
# terms are active during refinement.
#
from potList import PotList
potList = PotList()

# parameters to ramp up during the simulated annealing protocol
#
from simulationTools import MultRamp, StaticRamp, InitialParams, IVMAction

rampedParams=[]
highTempParams=[]
highTemp1Params=[]
highTemp2Params=[]

# IVM setup
#   the IVM is used for performing dynamics and minimization in torsion-angle
#   space, and in Cartesian space.
#
from ivm import IVM
dyn  = IVM()
minc = IVM() # minc used for final cartesian minimization

# initialize ivm topology for torsion-angle dynamics


#
# 
#


# compare atomic Cartesian rmsd with a reference structure
#  backbone and heavy atom RMSDs will be printed in the output
#  structure files
#
#from posDiffPotTools import create_PosDiffPot
#refRMSD = create_PosDiffPot("refRMSD","name CA or name C or name N",
#                            pdbFile='cvn_reference.pdb',
#                            cmpSel="not name H*")

from iupacNaming import toIUPAC
toIUPAC()

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
potList.append(noe)
rampedParams.append( MultRamp(2,30, "noe.setScale( VALUE )") )


# pasd terms
import pasd
pasdTerms=PotList('pasd')
potList.append( pasdTerms )
for pasdFilename in pasdFilenames:
    name='_'.join( pasdFilename.split('_')[:-1] )
    print(f"processing PASD file: {pasdFilename} for spectrum {name}")

    from pasdPotTools import create_PASDPot

    pot = create_PASDPot(name,pasdFilename=pasdFilename)

    pot.setUseSingleAssignment(False)
    pot.setUseQuadraticPot(False)
    pot.setViolationCutoff( 1.0 )
    pot.invPot().setScale( 0.0 )
    pot.setSwitchViolation( 1.0 )
	
    pot.setLongRangePrimarySeqCutoff(pasd.longRangeResidCutoff)
    pot.updatePrimarySeqDists()
    pot.setMaxMonteCarloAttempts( 100 )
    pot.setUseOriginalViolationScore(True)
    pot.disallowShiftAssignmentInactivation()
    
	
    pot.setInverseBound( 4.0 )
    pot.setInverseMethylCorrection( 0.0 )
    pasdTerms.append(pot)
    pass

from pasdPotTools import cooling_updateTerms, highTemp1_updateTerms
from pasdPotTools import highTemp2_updateTerms
numHighTempReshuffles=10
highTempParams.append( 
    StaticRamp('[pot.invPot().setScale(5) for pot in pasdTerms]') )
highTemp1Params.append(
    StaticRamp('''highTemp1_updateTerms(pasdTerms,
                                        rampInfo.fractionDone,
                                        rampInfo.numSteps,
                                       )''') )
highTemp2Params.append(
    StaticRamp('''highTemp2_updateTerms(pasdTerms,
                                        rampInfo.fractionDone,
                                        rampInfo.numSteps,
                                       )''') )

rampedParams.append( 
    StaticRamp('[pot.invPot().setScale(5) for pot in pasdTerms]') )
rampedParams.append(
    MultRamp(1,30,
             "[pot.distPot().setScale(VALUE) for pot in pasdTerms]") )
rampedParams.append( StaticRamp('''cooling_updateTerms(pasdTerms,
                                  rampInfo.fractionDone,
                                  rampInfo.numSteps
                                  )''') )


from xplorPot import XplorPot




## Set up dihedral angles - one onse segid is necessary
from dihedralPotTools import create_DihedralPot
dihed = create_DihedralPot('dihe',nef=nef,
                           nefRestraintName="1") #needed in this case
potList.append( dihed )
highTempParams.append( StaticRamp("dihed.setScale(200)") )
rampedParams.append( MultRamp(200,200,"dihed.setScale(VALUE)") )


from iupacNaming import fromIUPAC
fromIUPAC()

# gyration volume term 
#
from gyrPotTools import create_GyrPot
gyr = create_GyrPot("Vgyr",
                    #                    "resid 1:56"
                    ) # selection should exclude disordered tails
potList.append(gyr)
rampedParams.append( MultRamp(.002,1,"gyr.setScale(VALUE)") )

# HBPot - hbond database-based term
#  CDS - 2017/04/24 - found to make precision worse - maybe better to use
#  during refinement only
from hbPotTools import create_HBPot
hbpot = create_HBPot('hb')
hbpot.setScale(2.5)
potList.append( hbpot )

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
repel = create_RepelPot('repel')
potList.append(repel)
rampedParams.append( StaticRamp("initRepel(repel,use14=False)") )
rampedParams.append( MultRamp(.04,4,  "repel.setScale( VALUE)") )
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


protocol.torsionTopology(dyn)

protocol.initMinimize(minc)

protocol.cartesianTopology(minc)



# object which performs simulated annealing
#
from simulationTools import AnnealIVM
init_t  = 4000.     # Need high temp and slow annealing to converge
coolTime=250. # ps
highTemp1 = AnnealIVM(initTemp =init_t,
                      finalTemp=init_t,
                      numSteps=numHighTempReshuffles,
                      ivm=dyn,
                      rampedParams = highTemp1Params+highTempParams)
highTemp2 = AnnealIVM(initTemp =init_t,
                      finalTemp=init_t,
                      numSteps=numHighTempReshuffles,
                      ivm=dyn,
                      rampedParams = highTemp2Params+highTempParams)
cool = AnnealIVM(initTemp =init_t,
                 finalTemp=25,
                 tempStep =12.5,
                 ivm=dyn,
                 rampedParams = rampedParams)


toIUPAC()

def calcOneStructure(loopInfo):
    """ this function calculates a single structure, performs analysis on the
    structure, and then writes out a pdb file, with remarks.
    """

    # generate a new structure with randomized torsion angles
    #
    from monteCarlo import randomizeTorsions
    randomizeTorsions(dyn)

    # set torsion angles from restraints
    #
    from torsionTools import setTorsionsFromTable
    setTorsionsFromTable( dihed.restraintString )
    pass
    
    protocol.fixupCovalentGeom(maxIters=100,useVDW=1)
#    protocol.writePDB(loopInfo.filename()+".init")

    # initialize parameters for high temp dynamics.
    InitialParams( rampedParams )
    # high-temp dynamics setup - only need to specify parameters which
    #   differfrom initial values in rampedParams
    InitialParams( highTemp1Params )

    # high temp dynamics 1
    #
    protocol.initDynamics(dyn,
                          potList=[pot for pot in potList
                                   if not pot.instanceName() in
                                   ('repel','hb')],
                          bathTemp=init_t,
                          initVelocities=1,
                          finalTime=20./numHighTempReshuffles,  
                          numSteps=1000,   # whichever comes first
                          printInterval=100)

    dyn.setETolerance( init_t/100 )  #used to det. stepsize. default: t/1000 

    highTemp1.run()

    # high temp dynamics 2
    #
    protocol.initDynamics(dyn,
                          potList=[pot for pot in potList
                                   if not pot.instanceName() in
                                   ('repel','hb')],
                          bathTemp=init_t,
                          initVelocities=1,
                          finalTime=60./numHighTempReshuffles,  
                          numSteps=1000,   # whichever comes first
                          printInterval=100)

    dyn.setETolerance( init_t/100 )  #used to det. stepsize. default: t/1000 

    highTemp2.run()

    # initialize integrator for simulated annealing
    #
    protocol.initDynamics(dyn,
                          potList=potList,
                          numSteps=1000,       #at each temp: 1000 steps or
                          finalTime=float(coolTime)/cool.numSteps ,
                          printInterval=100)

    # perform simulated annealing
    #
    cool.run()
              
              
    # final torsion angle minimization
    #
    protocol.initMinimize(dyn,
                          printInterval=50)
    dyn.run()

    protocol.initMinimize(minc,
                          potList=potList,
                          dEPred=10)
    minc.run()

    #do analysis and write structure when function returns
    pass



from simulationTools import StructureLoop, FinalParams
sl=StructureLoop(numStructures=numberOfStructures,
              pdbTemplate=outFilename,
#                 calcMissingStructs=True,
              structLoopAction=calcOneStructure,
              doWriteStructures=True,
              genViolationStats=True,
              averageTopFraction=0.10, #report stats on best 50 structs
              averageContext=FinalParams(rampedParams),
#              averageCrossTerms=refRMSD,
              averagePotList=potList)
sl.run()

if xplor.p_comm.procNum!=0:
    exit()
    pass


structTemplate = sl.pdbTemplate.replace("SCRIPT","pass2")

from pasd.protocol import processStructurePass
processStructurePass(pasdTerms,
                          filenames=[structTemplate.replace("STRUCTURE",
                                                            str(key)) for
                                     key in sl.sharedData.keys()],
                          inPassName="pass2",
                          outPassName="pass3",
                          refStructFilename=refFilename,
                          highLikelihoodCutoff=highLikelihoodCutoff,
                          violCutoff=0.5)

