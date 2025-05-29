#!/bin/sh

exit=0

#check the number of long-range peaks
file='3dNOESY-182`3`_final.pasd'
num=$(grep -A 5 "Number of peaks of type"  $file | \
          grep "long range" | sed 's/[^[0-9]*//')
status="good"
expected=110
if [ $num -lt $expected ]; then
    status="BAD "
    exit=1
fi
echo -n "[$status] "
echo "num long-range peaks for ${file}: $num (expected $expected)"

file='CNOESY-173`3`_final.pasd'
num=$(grep -A 5 "Number of peaks of type"  $file | \
          grep "long range" | sed 's/[^[0-9]*//')
status="good"
expected=380
if [ $num -lt $expected ]; then
    status="BAD "
    exit=1
fi
echo -n "[$status] "
echo "num long-range peaks for ${file}: $num (expected $expected)"
    
# check that out.nef has some linkage lines
numLines=`grep 'nef_nmr_spectrum_CNOESY-173\`3\`' out.nef | \
    grep 'nef_distance_restraint_list_CNOESY-173\`3\`' |wc -l`
status="good"
expected=1000
if [ $numLines -lt 1000 ]; then
    status="BAD "
    exit=1
fi
echo -n "[$status] "
echo "num linkage lines: $numLines (expected $expected)"

# check that the final precision is ok
prec=$(aveStruct -selection "resid 4:80  and name C CA N O" \
                 $(getBest -num 10 refine_##.sa.stats) | \
           grep 'RMSD diff. for fitted atoms:' | cut -d \  -f 7)
status="good"
expected=1.0
if [ $(echo "$prec > $expected" | bc) -eq 1 ]; then
    status="BAD "
    exit=1
fi
echo -n "[$status] "
echo "precision: $prec (expected $expected)"

# the PDB was identified by a sequence search 
acc=$(targetRMSD -diffSeq -selection "resid 41:117 and name C CA N O" \
    -selection2 "resid 4:80  and name C CA N O" \
    1uhm.pdb \
    $(getBest -num 10 refine_##.sa.stats) | cut -d \  -f 3)
status="good"
expected=3.5
if [ $(echo "$acc > $expected" | bc) -eq 1 ]; then
    status="BAD "
    exit=1
fi
echo -n "[$status] "
echo "accuracy: $acc (expected $expected)"

exit $exit
