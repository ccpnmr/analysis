#!/usr/bin/env pyXplor

opts,args = xplor.parseArguments()


filename = args[0]

from nefTools import readNEF 
nef = readNEF(filename) # generates PSF information

from atomAction import genRandomCoords
genRandomCoords()

import iupacNaming
iupacNaming.toIUPAC()  #switch to IUPAC naming

import pasd                   #load chemical shifts from NEF data
shifts = pasd.nefShifts(nef)

#sequence from the first chain
chainSel = "segid A"
residSel=AtomSel(f"tag and {chainSel}")

from selectTools import threeToOne
sequence="".join( [threeToOne(atom.residueName()) for atom in residSel] )
firstResid = residSel[0].residueNum()

from sparta import GDB
gdb=GDB()

gdb.VARS_str_parser("  RESID RESNAME ATOMNAME SHIFT");
gdb.FORMAT_str_parser(" %4d   %1s     %4s      %8.3f");
gdb.setData("FIRST_RESID", str(firstResid) +"\n")
gdb.setData("SEQUENCE", sequence);

includedAtomNames="H HN N CA CB C HA HA2 HA3".split()

glycines={}

cnt=1
for (val,selString,err) in shifts:
    from atomSel import intersection
    atomSel = intersection(chainSel,AtomSel(selString))
    if len(atomSel)== 0:
        print(f"Warning: selection ({atomSel.string()}) does not any atoms")
        continue
    atom = atomSel[0]
    name = atom.atomName() #convert?
    resid = atom.residueNum()
    resname = threeToOne( atom.residueName() )
    if not name in includedAtomNames:
        continue

    if resname=="G" and name.startswith("HA"):
        if not resid in glycines:
             glycines[resid]=1
             name="HA2"
        elif glycines[resid]==1:
            glycines[resid]=2
            name="HA3"
        else:
            raise Exception(
                f"more than two HA Glycine entries for ({atomSel.string()})?")
    elif len(atomSel)!= 1:
        raise Exception("sel: (%s) does not selection one atom"%sel)

    
#    print(val,sel,name)
    gdb.setEntry(cnt,"RESID",str(resid))
    gdb.setEntry(cnt,"RESNAME",resname)
    gdb.setEntry(cnt,"ATOMNAME",name)
    gdb.setEntry(cnt,"SHIFT",str(val))
    cnt += 1
    pass

gdb.saveGDB("%s.tab"% filename)
