
opts,args = xplor.parseArguments()

nefFile=args[0]

from nefTools import readNEF
nefData = readNEF(nefFile)

from iupacNaming import toIUPAC, fromIUPAC

restraintType="distance"
from nefTools import getBlockNames
names = getBlockNames(nefData,restraintType)
for name in names:
    oname = "%s.tbl"%name
    print( "writing %s restraint table with name %s" % (restraintType,name))
    from noePotTools import create_NOEPot, makeTable
    toIUPAC()
    noe = create_NOEPot('noe',nefRestraintName=name,nef=nefData)
    fromIUPAC()
    open(oname,"w").write( makeTable(noe) )
    pass

restraintType="dihedral"
from nefTools import getBlockNames
names = getBlockNames(nefData,restraintType)
for name in names:
    oname = "%s.tbl"%name
    print( "writing %s restraint table with name %s" % (restraintType,name))
    from dihedralPotTools import create_DihedralPot, makeTable
    toIUPAC()
    dihe = create_DihedralPot('dihedral',nefRestraintName=name,nef=nefData)
    fromIUPAC()
    open(oname,"w").write( makeTable(dihe) )
    pass

# restraintType in ['distance',
#                      'dihedral']:
#    if restraintType==
#noePot
#
