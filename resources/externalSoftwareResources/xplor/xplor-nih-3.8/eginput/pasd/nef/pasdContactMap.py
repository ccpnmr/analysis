#!/usr/bin/env pyXplor

#script to generate contact map
#  see Kuszewski et al. J. Biomol. NMR 41, 221-239 (2008).
#
#
# joinFilter.out is the output of the joint filter script
# the second argument is the name of an optional reference pdb file.
#

usage="""usage:

  ./makeContactMap [options] <pasdFilename> ...

where options are one or more of
    -nef <NEF filename>     - specify name of input NEF file
    -psf <PSF filename>     - specify name of input PSF file
    -pdb <PDB filename>     - specify name of input PDB file
    -iupac                  - By default XPLOR-NIH proton naming is used
                              (unless -nef is specified). Specifying this
                              flag will switch to IUPAC mode.
    -refFilename <filename> - filename of reference structure
    -Rc <val>               - lower bound for passing residue pair score
                              [0.01].
    -dresid <num>           - in plot, how many residues between tick marks
                              [25].
    -cutoff <val>           - distance bound between atoms in residues
                              considered to be in contact [4].
    -print                  - print out a list of residue-residue contacts.
    -plot                   - ifspecified, make a matplotlib figure.
    -outFile <filename>     - plot filename

One of -nef, -psf or -pdb must be specified.
"""

#doesn't work:    -symmetrize             - make the contact map symmetric 


(opts,args) = xplor.parseArguments(["refFilename:1",
                                    "nef:1",
                                    "psf:1",
                                    "pdb:1",
                                    "iupac:0",
                                    "Rc:1",
                                    #"symmetrize:0",
                                    "print:0",
                                    "plot:0",
                                    "outFile:1",
                                    "dresid:1",
                                    "cutoff:1",
                                    "help-script:0"])

Rc=0.01
cutoff=4
outFilename=None
dresid=25
segidBuffer=8

refFilename=None
nefFilename=None
psfFilename=None
pdbFilename=None
useIUPAC=False
plot=False
printContacts=False
symmetrize=False
for opt in opts:
    if opt[0]=="nef":
        nefFilename=opt[1]
        pass
    if opt[0]=="psf":
        psfFilename=opt[1]
        pass
    if opt[0]=="pdb":
        pdbFilename=opt[1]
        pass
    if opt[0]=="iupac":
        useIUPAC=True
        pass
    if opt[0]=="refFilename":
        refFilename=opt[1]
        pass
    if opt[0]=="Rc":
        Rc=float(opt[1])
        pass
    if opt[0]=="symmetrize":
        symmetrize=True
        pass
    if opt[0]=="outFile":
        outFilename=opt[1]
        pass
    if opt[0]=="plot":
        plot=True
        pass
    if opt[0]=="print":
        printContacts=True
        pass
    if opt[0]=="cutoff":
        cutoff=float(opt[1])
        pass
    if opt[0]=="dresid":
        dresid=int(opt[1])
        pass
    if opt[0]=="help-script":
        print(usage)
        import sys
        sys.exit(0)
        pass
    pass


pasdFilenames=args[0:]

psfLoaded=False
import protocol
if nefFilename:
    from nefTools import readNEF
    nef=readNEF(nefFilename)
    useIUPAC=True
    psfLoaded=True
    pass
if psfFilename:
    if psfLoaded:
        print("error: only one of -nef, -psf, -pdb may be specified")
        exit(1)
        pass
    protocol.initStruct(psfFilename)
    psfLoaded=True
    pass
if pdbFilename:
    if psfLoaded:
        print("error: only one of -nef, -psf, -pdb may be specified")
        exit(1)
        pass
    protocol.loadPDB(pdbFilename)
    psfLoaded=True
    if not refFilename:
        refFilename = pdbFilename
        pass
    pass

if not psfLoaded:
    print("error: one of -nef, -psf, -pdb must be specified")
    exit(1)
    
if useIUPAC:
    import iupacNaming
    iupacNaming.toIUPAC()
    pass

from atomAction import genRandomCoords
genRandomCoords()

from potList import PotList
noes = PotList()
for pasdFilename in pasdFilenames:
    name='_'.join( pasdFilename.split('_')[:-1] )
    from pasdPotTools import create_PASDPot
    pot=create_PASDPot(name,
                       pasdFilename=pasdFilename)
    #pot.setUseSingleAssignment(True)
    noes.append(pot)

    pass

from pasd.netfilter import netFilter

kwargs={}
if Rc is not None: kwargs['passFrac']=Rc
    
nfResults = netFilter(noes,
                      **kwargs
                      )

import trace
trace.suspend()

scores=[]
for i,(iSegid,iResid) in enumerate(nfResults.residues):
    for j,(jSegid,jResid) in enumerate(nfResults.residues):
        scores.append( (iSegid,iResid,jSegid,jResid,
                        nfResults.resPairScore[i,j]) )
        pass
    pass

segids=list(set([ t[0] for t in scores ]))

numResids=0
residsInSegid=dict( [(segid,[]) for segid in segids] )
for segid in segids:
    resids = list(set([t[1] for t in scores if t[0]==segid]))
    residsInSegid[segid] = sorted(resids)
    numResids += max(resids) - min(resids) + 1
    numResids += segidBuffer
    pass

   

#minResid=min(map(lambda t:t[0], scores))
#minResid=min(minResid,min(map(lambda t:t[1], scores)))
#maxResid=max(map(lambda t:t[0], scores))
#maxResid=max(maxResid,max(map(lambda t:t[1], scores)))
#


print('numResids (including inter-segid buffers):', numResids)

def segidResidToResindex(segid,resid):
    ret = resid
    for segid2 in segids: 
        if segid==segid2:
            ret -= residsInSegid[segid][0]
            break
        else:
            ret += len(residsInSegid[segid2])
            ret += segidBuffer
            pass
        pass
    return ret

x=[]
y=[]
networkContacts=[]
for i in range(numResids):
    networkContacts.append([])
    pass
numContacts=0
for (s0,r0,s1,r1,s) in scores:
    if s>Rc:
        #print('contact', s0,r0,s1,r1,s)
    
        rid0 = segidResidToResindex(s0,r0)
        rid1 = segidResidToResindex(s1,r1)
        #print 'rid',s0,r0,rid0,s1,r1,rid1
        networkContacts[rid0].append(rid1)
        #if symmetrize: networkContacts[rid1].append(rid0) doesn't work
        numContacts+=1
        pass
    pass

print('num network contacts:', numContacts)
#        
#        x.append(r0)
#        y.append(r1)
##    if s!=0.: print r0,r1,s
#    pass

structContacts=[]
for i in range(numResids):
    structContacts.append([])
    pass
numContacts=0
if refFilename:
    xplor.simulation.deleteAtoms("all")
    from atomSelAction import minDistance
    protocol.loadPDB(refFilename,deleteUnknownAtoms=True)
    #from selectTools import minResid, maxResid
    for s0,resids0 in list(residsInSegid.items()):
        for s1,resids1 in list(residsInSegid.items()):
            for r0 in resids0:
                for r1 in resids1:
                    if (minDistance(AtomSel('segid "%s" and resid %d'%(s0,r0)),
                                    AtomSel('segid "%s" and resid %d'%(s1,r1)))
                        <cutoff):
                
                        rid0 = segidResidToResindex(s0,r0)
                        rid1 = segidResidToResindex(s1,r1)
                        structContacts[rid0].append(rid1)
                        numContacts+=1
                        pass
                    pass
                pass
            pass
        pass

    print('num physical contacts:', numContacts)
    pass

falseContacts=[]
trueContacts=[]
missingContacts=[]

for i in range(len(networkContacts)):
    for j in networkContacts[i]:
        if j in structContacts[i]:
            trueContacts.append((i,j))
        elif i>j:
            falseContacts.append((i,j))
            pass
        pass
    pass
for i in range(len(structContacts)):
    for j in structContacts[i]:
        if not j in networkContacts[i] and i<j:
            missingContacts.append((i,j))
            pass
        pass
    pass

print('false', len(falseContacts))
print('missing', len(missingContacts))
print('correct', len(trueContacts))

if printContacts:
    #FIX: this has problems
    residues = nfResults.residues
    for i,contacts in enumerate(networkContacts):
        if contacts:
            print(f"{residues[i]}: ",end="")
            for contact in contacts:
                print(f"{residues[contact]} ",end="")
                pass
            print()
        pass
    pass
            
            
    
if not plot:
    exit(0)
    
from pylab import subplot, pcolor, title, ndarray, show, get_cmap
import pylab
array=[[]]*numResids
array=ndarray((numResids,numResids))

fig=pylab.figure()#facecolor='w',figsize=(8, 8))
fig.canvas.manager.set_window_title("Contact Map")# + f" - {passName}" if passName else "")
            
pylab.gca().set_aspect('equal', adjustable='box')  # square plot

x=pylab.array(x)
y=pylab.array(y)
segid,resids=list(residsInSegid.items())[0]
from math import ceil
start = int(ceil(resids[0] /float(dresid)) * dresid)
stop  = int(float(resids[-1] /float(dresid)) * dresid)

labels = list(range(start,stop,dresid))
tics = [label-resids[0] for label in labels]
if len(list(residsInSegid.keys()))>1:
    labels = ["%s %d"%(segid,label) for label in labels]
    pass
curTic = len(resids)+segidBuffer
for segid,resids in list(residsInSegid.items())[1:]:
    start = int(ceil(resids[0] /float(dresid)) * dresid)
    stop  = int(float(resids[-1] /float(dresid)) * dresid)
    labels += ["%s %d"%(segid,label) for label in range(start,stop,dresid)]
    tics += [curTic+label-resids[0] for label in range(start,stop,dresid)]
    curTic += len(resids)+segidBuffer
    pass

pylab.xticks(tics,labels,size=8)
pylab.yticks(tics,labels,size=8)

x=pylab.array([t[0] for t in falseContacts])
y=pylab.array([t[1] for t in falseContacts])
pylab.plot(x,y,'gs',label="False")

x=pylab.array([t[0] for t in missingContacts])
y=pylab.array([t[1] for t in missingContacts])
pylab.plot(x,y,'rs',label="Missing")

x=pylab.array([t[0] for t in trueContacts])
y=pylab.array([t[1] for t in trueContacts])
pylab.plot(x,y,'ks',label="True")


pylab.xlabel("Residue Number",size=15)
pylab.ylabel("Residue Number",size=15)

pylab.grid(True)
pylab.legend(loc="right",bbox_to_anchor=(1.3,0.5))


#axis([2,20,2,14])
#setp(gca(), xticklabels=[], yticks=(4,8,12), xticks=(0,10,20))
#text(3,12, 'I', fontsize=20)


title('contact map')

if outFilename:
    #suppress warning from PostScript backend
    logName='matplotlib.backends.backend_ps'
    import logging
    logging.getLogger(logName).setLevel(logging.ERROR)
    pylab.savefig(outFilename)
else:
    show()
    pass
