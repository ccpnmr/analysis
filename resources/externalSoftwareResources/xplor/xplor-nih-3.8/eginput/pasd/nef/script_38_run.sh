#!/bin/sh
alias xplor='/Users/Eliza/Projects/xplor-nih-3.8/bin/xplor'
alias getBest='/Users/Eliza/Projects/xplor-nih-3.8/bin/getBest'
alias ens2pdb='/Users/Eliza/Projects/xplor-nih-3.8/bin/ens2pdb'
alias talosn='/Users/Eliza/Projects/talosn/talosn'

# An example of performing a PASD calculation from  NEF-formatted input
#

# This is an executable script for bash, dash or Bourne-shell compatible
# shells. The full procedure can be run using the command
#  sh README
#  

#    Procedure

#
#  specify the prefix of the input NEF filename (portion without .nef)

name=input

# 
# 1) Generate Talos-N torsion angle restraints from chemical shifts.

./runTalos.sh ${name}.nef

# This generates ${name}_new.nef, which should be used for the 
# the PASD structure calculation.
#

 
#
# 2) a snippet to list spectra and distance restraints in the NEF file:

pyXplor <<EOF
from nefTools import *
nef=readNEF('${name}_new.nef') 
print(f"{'Spectrum Name':<50} Num Peaks")
for n in getBlockNames(nef,'spectrum'):
    n=n[17:]
    print(f"{n:<50} {len(getBlock(nef,'spectrum',n).nef_peak.index):6}")
print(f"{'Distance Table Name':<50} Num Restraints")
for n in getBlockNames(nef,'distance'):
    n=n[28:]
    print(f"{n:<50} ",end='')
    print(f"{len(getBlock(nef,'distance',n).nef_distance_restraint.index):6}")
EOF


#
#  Choose spectrum names to use

spectra='1h-noesy`3`'

# optional distance restraint names
distRestraints=""

#likelihood cutoff. Peak assignments with likelihoods lower than this value
# will be de-activated.
likelihoodCutoff="-likelihoodCut 0.4"

# 
# 3) Run initMatch3d. The second argument given to the initMatch scripts is the
# name of the spectrum in the NEF file.

for spectrum in $spectra; do xplor initMatch.py ${name}_new.nef $spectrum; done
  

# initMatch.py should work for 2D, 3D and 4D spectra. It generates
# *_pass1.pasd files used as input for jointFilter.

#
# 4) Run jointFilter - generate initial assignment likelihoods based on
# possible assignment connectivities. In connectivities implied by distance
# restraints if distRestraints is specified.

xplor jointFilter.py ${name}_new.nef *pass1.pasd

# this generates *_pass2.pasd files

#
# 5) First pass of structure calculation. Initially, assignment likelihoods
# are the jointFilter connectivity-based values. During the structure
# calculation these values are gradually switched over to being based solely
# on structure-based values. Additionally, explicit distance restraints can
# be passed using the distRestraints variable.

xplor -parallel pass2.py $distRestraints ${name}_new.nef *pass2.pasd \
      $likelihoodCutoff

# After the structures are calculated, pass2.py generates *_pass3.pasd
# files used for pass3. These can be calculated separately using
#
#   xplor analyzeStructurePass.py -inPassName pass2 -outPassName pass3 \
#             ${name}_new.nef *pass2.pasd
# 
# This step updates assignment likelihoods based on the 50 lowest
# energy structures from the structure calculation. 

# 
# 6) Second pass of structure calculation

xplor -parallel pass3.py $distRestraints ${name}_new.nef *pass3.pasd \
      $likelihoodCutoff

# After the structures are calculated, pass3.py generates *_final.pasd
# files. These could also be calculated separately using
#
#   xplor analyzeStructurePass.py -inPassName pass3 -outPassName final
# 
# This step generates assignment likelihoods based on the 50 lowest
# energy structures from the pass3 structure calculation.

#
# At any stage in the calculation a contact map can be made using
#  pasdContactMap.py:
#
#  ./pasdContactMap.py -plot -nef CCPN_H1GI_clean.nef \
#        -refFilename 1uhm.pdb *pass3.pasd
#

# 
# 7) write out a new NEF file using distance restraints from the PASD
# calculation and TalosN dihedral restraints.

xplor makeNEF.py ${name}_new.nef *final.pasd \
      $likelihoodCutoff


# this creates the file out.nef, containing distance restraints from the
# PASD calculation in addition to the Talos-N dihedral restraints.

# 
# 8) run structure calculation using the NEF restraints and, optionally,
#    the name of saveframes containing distance restraints. If the
#    $distRestraints argument is omitted, then all distance restraints in
#    out.nef are used in the calculation.

#distRestraintNames='`20`hBond:'

distRestraintNames="${distRestraintNames}$(echo $spectra | sed 's/ /:/g')"

xplor -parallel fold.py -nef out.nef -dist $distRestraintNames

# the results from the lowest energy 20 (of 100 total) structures is
# summarized in fold_##.sa.stats

# 
# 9) run a refinement of the lowest energy structures from the fold
#    calculation. Ten structures will be calculated for each input
#    structure. Again, if the $distRestraints argument is omitted, then all
#    distance restraints in out.nef are used in the calculation.

xplor -parallel refine.py -nef out.nef -dist $distRestraintNames \
      $(getBest -num 10 -suffix .cif fold_##.sa.stats)

# When run, the script validateCalc.sh validates that the number of long-range
# assignments determined by PASD is sufficient, and that the precision of
# the structures calculated by fold.py is an acceptable (small) value.
  
ens2pdb $(getBest -num 10 refine_##.sa.stats) > ensemble_r.pdb