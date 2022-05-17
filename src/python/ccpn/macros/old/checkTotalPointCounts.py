
# small macro to fix the issue with the numPointOrig not matching numPoints

print('Checking spectrum totalPointCounts')

for sp in project.spectra:
    pointCounts = sp.pointCounts
    totalPointCounts = sp.totalPointCounts
    
    if pointCounts != totalPointCounts:
        print(f'Spectrum: {sp}    pointCounts: {sp.pointCounts}   ->   {totalPointCounts}')
        sp.totalPointCounts = pointCounts
