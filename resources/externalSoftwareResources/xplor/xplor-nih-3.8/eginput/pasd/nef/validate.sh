#!/bin/sh

#
# check that the expected number of peaks were found
#

spectrum=3dNOESY-182
pasdFile=${spectrum}_pass1.pasd

echo "checking initMatch output"
exit=0
intraPeaks=`grep -A 5 "Number of peaks of type" $pasdFile | \
                 grep intraresidue| tail -1 |sed 's/[^0-9]*//'`
if [ $intraPeaks -lt 315 ]; then
    echo "Unexpected number of intraresidue peaks: $intraPeaks"
    exit=1
fi

seqPeaks=`grep -A 5 "Number of peaks of type" $pasdFile | \
                 grep sequential| tail -1 |sed 's/[^0-9]*//'`
if [ $seqPeaks -lt 329 ]; then
    echo "Unexpected number of sequential peaks: $seqPeaks"
    exit=1
fi

srPeaks=`grep -A 5 "Number of peaks of type" $pasdFile | \
                 grep "short range"| tail -1 |sed 's/[^0-9]*//'`
if [ $srPeaks -lt 254 ]; then
    echo "Unexpected number of short range peaks: $srPeaks"
    exit=1
fi

lrPeaks=`grep -A 5 "Number of peaks of type" $pasdFile | \
                 grep "long range"| tail -1 |sed 's/[^0-9]*//'`
if [ $lrPeaks -lt 199 ]; then
    echo "Unexpected number of long range peaks: $lrPeaks"
    exit=1
fi

numPeaks=`grep -c ^peak $pasdFile`
if [ $numPeaks != 1147 ]; then
    echo "Unexpected number of peaks: $numPeaks"
    exit=1
fi

numExceptions=`grep -c ^except $pasdFile`
if [ $numExceptions -lt 123 ]; then
    echo "Unexpected number of exceptions: $numExceptions"
    exit=1
fi

numShifts=`grep -c ^shiftA $pasdFile`
if [ $numShifts != 652 ]; then
    echo "Unexpected number of shifts: $numShifts"
    exit=1
fi

echo "checking jointFilter output"
#pass2 input
pasdFile=${spectrum}_pass2.pasd

lrPeaks=`grep -A 5 "Number of peaks of type" $pasdFile | \
                 grep "long range"| tail -1 |sed 's/[^0-9]*//'`
if [ $lrPeaks -lt 213 ]; then
    echo "Unexpected number of long range peaks: $lrPeaks"
    exit=1
fi


numPeaks=`grep -c ^peak $pasdFile`
if [ $numPeaks != 1106 ]; then
    echo "Unexpected number of peaks: $numPeaks"
    exit=1
fi

numExceptions=`grep -c ^except $pasdFile`
if [ $numExceptions -lt 11901 ]; then
    echo "Unexpected number of exceptions: $numExceptions"
    exit=1
fi

numShifts=`grep -c ^shiftA $pasdFile`
if [ $numShifts != 652 ]; then
    echo "Unexpected number of shifts: $numShifts"
    exit=1
fi

#exercise this helper
./pasdContactMap.py -plot -outFile contactMap.png \
                    -nef CCPN_H1GI_clean.nef -refFilename 1uhm.pdb \
                    3dNOESY-182_pass2.pasd

exit $exit
