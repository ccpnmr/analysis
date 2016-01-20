
def getPeakPosition(peak, dim, unit='ppm'):

    # peakDim = peak.position[dim]

    if peak.position[dim] is None:
      value = "*NOT SET*"

    elif unit == 'ppm':
      value = peak.position[dim]

    elif unit == 'point':
      value = peak.pointPosition[dim]

    elif unit == 'Hz':
      value = peak.position[dim]*peak.sortedPeakDims()[dim].dataDimRef.expDimRef.sf

    else: # sampled
      value = unit.pointValues[int(peak.sortedPeakDims()[dim].position)-1]

    return '%7.2f' % float(value)

def getPeakAnnotation(peak, dim):

  if len(peak.dimensionNmrAtoms[dim]) > 0:
    return peak.dimensionNmrAtoms[dim][0].pid.id
