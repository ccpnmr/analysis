
"""Functions for calculating axisCodes for NmrExpPrototypes, adn necessary utilities.
For normal cases, use only refExpFimRefCodeMap function, and get axisCodes from
refExpDimRefs and the map.

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

import operator
from typing import Dict

def resetAllAxisCodes(nmrProject):
  """Reset all axisCodes (ExpDimRef.name) in project to be unique, match the isotope,
  and match the standard Prototype where a prototype is known"""

  stdCodeMap = refExpDimRefCodeMap(nmrProject.root)

  for experiment in nmrProject.sortedExperiments():

    if experiment.refExperiment is None:
      # No prototype - just use nucleus as axis code

      foundCodes = {}
      for expDim in experiment.expDims:
        for expDimRef in expDim.expDimRefs:
          isotopeCodes = expDimRef.isotopeCodes

          # Get axis code
          if expDimRef.measurementType.lower() == 'shift' and len(isotopeCodes) == 1:
            # Normal shift axis, use nucleus to set
            code = isotope2Nucleus(isotopeCodes[0])
          else:
            # Different type of axis.
            # For simplicity set to axis_1, axis_2, ... for now
            print ("WARNING, non-std axis - axisCode set to 'axis'")
            code = 'axis'
            foundCodes[code] = 0

          # add index for duplicates
          indx = foundCodes.get(code)
          if indx is None:
            foundCodes[code] = 0
          else:
            indx += 1
            foundCodes[code] = indx
            code = '%s_%s' % (code, str(indx))

          # Set the attribute
          expDimRef.name = code


    else:
      # We have a prototype - use standard axisCode map
      for expDim in experiment.expDims:
        for expDimRef in expDim.expDimRefs:
          expDimRef.name = stdCodeMap[expDimRef.refExpDimRef]



def refExpDimRefCodeMap(project):
  """get RefExpDimRef: axisCode map for all NmrExpPrototypes in project"""
  result = {}

  for nxp in project.sortedNmrExpPrototypes():
    for isReversed in False, True:
      refExperiments = nxp.findAllRefExperiments(isReversed=isReversed)
      if refExperiments:
        measurementMap = _measurementCodeMap(nxp, forReversed=isReversed)
        for re in refExperiments:
          for red in re.refExpDims:
            for redr in red.refExpDimRefs:
              result[redr] = measurementMap[redr.expMeasurement]
  #
  return result


def _measurementCodeMap(nmrExpPrototype, forReversed=False):
  """get expMeasurement:axisCode map"""
  result = {}
  measurements = _orderedMeasurements(nmrExpPrototype, forReversed=forReversed)

  foundCodes = {}
  # get axisCodes per expMeasurement
  for measurement in measurements:
    code = rawAxisCode(measurement)
    indx = foundCodes.get(code)
    if indx is None:
      foundCodes[code] = 0
    else:
      indx += 1
      foundCodes[code] = indx
      code = '%s%s' % (code, indx)
    result[measurement] = code
  #
  return result


def _connectedShiftMeasurements(expMeasurement):
  """find expMeasurements that are of type Shift, match a HX bond, and onebonded to the input measurement"""
  result = []

  nmrExpPrototype = expMeasurement.nmrExpPrototype

  if expMeasurement.measurementType.lower() != 'shift':
    return result

  atomSites = expMeasurement.atomSites
  if len(atomSites) != 1:
    print ("WARNING%s Shift must have single AtomSite, has: %s"
           % (expMeasurement.nmrExpPrototype.name, [x.name for x in atomSites]))
    if not atomSites:
      return result

  expSite = atomSites[0]
  expIsotope = expSite.isotopeCode
  sites = []
  if expIsotope in ('1H', '19F'):
    for et in expSite.findAllExpTransfers(transferType='onebond'):
      for site in et.atomSites:
        if site is not expSite:
          if site.isotopeCode in ('13C', '15N') and site.maxNumber != 0:
            sites.append(site)
          break

  elif expIsotope in ('13C', '15N'):
    for et in expSite.findAllExpTransfers(transferType='onebond'):
      for site in et.atomSites:
        if site is not expSite:
          if site.isotopeCode in ('1H', '19F') and site.maxNumber != 0:
            sites.append(site)
          break

  result = [x for x in nmrExpPrototype.expMeasurements if x.measurementType.lower() == 'shift'
            and x.findFirstAtomSite() in sites]
  #
  return result

def _orderedMeasurements(nmrExpPrototype, forReversed=False):
  """get ExpMeasurements in order: acquisition last, furthest from acquisition last,
  connected measurements grouped together. If forReversed, get with acquisition last
  (for reversed experiments"""

  ll = [tt[1].expMeasurement
        for tt in sorted((x.stepNumber,x)
                         for x in nmrExpPrototype.findFirstExpGraph().expSteps)]
  if not forReversed:
    ll.reverse()

  measurements = []
  for measurement in ll:
    if measurement not in measurements:
      measurements.append(measurement)
      for me in _connectedShiftMeasurements(measurement):
        if me not in measurements:
          measurements.append(me)

  # we do not search all expGraphs, so just add missing measurements to the end
  # this is a heuristic, not a rigid ordering
  for measurement in nmrExpPrototype.expMeasurements:
    if measurement not in measurements:
      measurements.append(measurement)
      for me in _connectedShiftMeasurements(measurement):
        if me not in measurements:
          measurements.append(me)
  #
  return measurements


def rawAxisCode(expMeasurement):
  """Get raw expMeasurement axisCode (without number suffixes) from NmrExpPrototype.ExpMeasurement"""
  tagMapping = {
  'shift':'shift',
  'jcoupling':'J',
  'mqshift':'MQ',
  'rdc':'RDC',
  'shiftanisotropy':'ANISO',
  'troesy':'TROESY',
  'dipolarcoupling':'DIPOLAR',
  't1':'delay',
  't2':'delay',
  't1rho':'delay',
  't1zz':'delay'
  }


  em = expMeasurement
  emType = em.measurementType.lower()

  tag = tagMapping.get(emType, emType)
  if tag == 'delay':
    result = tag
  elif tag == 'shift':
    result = ''.join(sorted(atomSiteAxisCode(x) for x in em.atomSites))
  else:
    result = tag + ''.join(sorted(isotope2Nucleus(x.isotopeCode).lower() for x in em.atomSites))

  #
  return result


def isotope2Nucleus(isotopeCode):
  """remove integer prefix from integer+string string"""
  ii = 0
  for ii,char in enumerate(isotopeCode):
    if char not in '0123456789':
      break
  return isotopeCode[ii:]


def atomSiteAxisCode(atomSite):
  """Get axisCode (without number suffixes) from NmrExPrototype.AtomSite"""

  name = atomSite.name
  result = nucleus = isotope2Nucleus(atomSite.isotopeCode)

  if name == 'CA':
    result = 'CA'

  elif name == 'CO':
    result = 'CO'

  elif nucleus in 'HF':
    # H or F, check if bound to C or N
    ll = []
    for et in atomSite.findAllExpTransfers(transferType='onebond'):
      for site in et.atomSites:
        if site is not atomSite:
          if site.isotopeCode == '13C':
            ss = 'c'
          elif site.isotopeCode == '15N':
            ss = 'n'
          else:
            break
          if site.maxNumber == 0:
              ll.append('-'+ss)
          elif site.minNumber > 0:
              ll.append(ss)

          break

    # In rare cases we get both - this is nonsense, so remove them
    for tags in ('n', '-n'),('c','-c'):
      if tags[0] in ll and tags[1] in ll:
        for tag in tags:
          while tag in ll:
            ll.remove(tag)

    # Now remove the '-x' tags - they were there to catch the above problem
    for tag in ('-n', '-c'):
      while tag in ll:
        ll.remove(tag)

    result += ''.join(sorted(set(ll)))

  elif nucleus in 'CN':

    ll = []
    for et in atomSite.findAllExpTransfers(transferType='onebond'):
      for site in et.atomSites:
        if site is not atomSite:
          if site.isotopeCode == '1H':
            ss = 'h'
          elif site.isotopeCode == '19F':
            ss = 'f'
          else:
            break
          if site.maxNumber == 0:
              ll.append('-'+ss)
          elif site.minNumber > 0:
              ll.append(ss)
          break

    # In rare cases we get both - this is nonsense, so remove them
    for tags in ('h', '-h'),('f','-f'):
      if tags[0] in ll and tags[1] in ll:
        for tag in tags:
          while tag in ll:
            ll.remove(tag)

    # Now remove the '-x' tags - they were there to catch the above problem
    for tag in ('-h', '-f'):
      while tag in ll:
        ll.remove(tag)

    result += ''.join(sorted(set(ll)))
  #
  return result


def testExpPrototypes(resetCodes=False):
  """Test functions and make diagnostic output"""
  from ccpn.util.Io import newProject
  project = newProject("ExpPrototypeTest", overwriteExisting=True)

  codeMap = refExpDimRefCodeMap(project)

  axisCodeSet = set()
  useNames = {}
  synonyms= []
  for nmrExpPrototype in project.sortedNmrExpPrototypes():
  # for nmrExpPrototype in project.findAllNmrExpPrototypes(serial=292):
    # print("nmrExpPrototype: %s %s " % (nmrExpPrototype, nmrExpPrototype._ID))
    for refExperiment in nmrExpPrototype.sortedRefExperiments():
      # print("refExperiment: %s %s " % (refExperiment, refExperiment._ID))

      # check axis codes
      codes = []
      for red in refExperiment.sortedRefExpDims():
        # print("red: %s %s" % (red, red._ID))
        for redr in red.sortedRefExpDimRefs():
          # print("redr: %s %s " % ( redr, redr._ID))
          code = codeMap[redr]
          codes.append(code)
          axisCodeSet.add(code)
      if len(codes) == len(set(codes)):
        if resetCodes:
          # Codes are unique - set them
          for red in refExperiment.sortedRefExpDims():
            for redr in red.sortedRefExpDimRefs():
              redr.axisCode = codeMap[redr]
      else:
        print ("Duplicate code in %s: %s. SKIPPING" % (refExperiment.name, codes))

      # print ("TEST %s %s" % (refExperiment.name, codes))

      # check for duplicate synonyms and collect all synonyms
      key = refExperiment.name
      usename = refExperiment.synonym or key
      ll = useNames.get(usename, [])
      ll.append(key)
      useNames[usename] = ll
      if usename != key:
        synonyms.append((usename, key))

  print ("All axisCodes: %s" % list(sorted(axisCodeSet)))

  for key, val in sorted(useNames.items()):
    if len(val) > 1:
      print ("Duplicate name: %s %s" % (key, val))

  # for tt in sorted(synonyms):
  #   print ("SYNONYM: %s %s" % tt)

  if resetCodes:
    project.saveModified()

def experimentSynonymSummary():
  """1) set of atomSiteNames appearing
  2) List of dimensionCount, synonym, name, atomNames for refExperiments sorted by name """

  from ccpn.util.Io import newProject
  project = newProject("ExpPrototypeTest", overwriteExisting=True)

  # NBNB
  # 1) Some refExperiments have no synonym - use the name instead for these

  result= []
  # atomSiteNames = set()
  allAxisCodes = set()
  # Sort refExperiments by name
  refExperiments = list(sorted([x for y in project.nmrExpPrototypes for x in y.refExperiments],
                               key=operator.attrgetter('name')))
  for refExperiment in refExperiments:
      # print("refExperiment: %s %s " % (refExperiment, refExperiment._ID))
      typ = 'NORM'
      # siteNames = []
      axisCodes = []
      synonym = refExperiment.synonym
      for red in refExperiment.sortedRefExpDims():
        ll = [x.axisCode for x in red.sortedRefExpDimRefs()]
        if len(ll) == 1:
          axisCodes.extend(ll)
          allAxisCodes.add(ll[0])
        else:
          axisCodes.append(str(ll))
          typ = 'CPLX'

      data = [typ, len(refExperiment.refExpDims), synonym or refExperiment.name,
              refExperiment.name, axisCodes]
      result.append(data)

          # ss = ','.join(tuple(x.name for x in redr.expMeasurement.atomSites))
          # siteNames.append(ss)
          # atomSiteNames.add(ss)
  #
  return allAxisCodes, result



def fetchIsotopeRefExperimentMap(project:'MemopsRoot') -> Dict:
  """fetch {tuple(sortedNucleusCodes):RefExperiment} dictionary for project
  The key is a tuple of element names ('C, Br, H, D, T, ...) or either of J, MQ, ALT, or delay

  NB, each list value is sorted ad-hoc to bring the most common experiments to the top.
  Do NOT sort or reorder the result"""
  result = {}
  if hasattr(project, '_isotopeRefExperimentMap'):
    result = project._isotopeRefExperimentMap

  if not result:

    tuples = []
    for expPrototype in project.sortedNmrExpPrototypes():
      expGraph = expPrototype.sortedExpGraphs()[0]
      expSteps = sorted(expGraph.expSteps, key=operator.attrgetter('stepNumber'))
      atomSiteCount = len(expPrototype.atomSites)
      for refExperiment in expPrototype.sortedRefExperiments():

        # ExpSteps in order of traversal
        expMeasurements = list(x.expMeasurement for x in expSteps)
        if refExperiment.isReversed:
          expMeasurements.reverse()
        # We now have expMeasurements in traversal order, from start to acquisition

        # Sort key for simple (e.g. shift)
        # versus compound (e.g. coupling, MQ, or reduced-dimensionality) axes
        axisCodes = refExperiment.axisCodes
        multiAxisCodeSort = 100 if None in axisCodes else max(x.count(',') for x in axisCodes)

        # Sort key for start and acquisition dimensions
        ss = expMeasurements[-1].atomSites[0].isotopeCode
        for acqNucleusCode in ss:
          if not acqNucleusCode.isdigit():
            break
        if acqNucleusCode == 'H':
          ll = list(expMeasurements[0].atomSites)
          startsOnProton = (ll[0].isotopeCode == '1H' if len(ll) == 1 else False)
          if startsOnProton:
            # Proton start and end -= sort first
            nucleusAcquisitionSort = -30
          else:
            # Proton end only - sort third
            nucleusAcquisitionSort = -10
        elif acqNucleusCode == 'C':
          # Carbon detection - sort second
          nucleusAcquisitionSort = -20
        else:
          # Other. Sort last, grouping by acquisition nucleus
          nucleusAcquisitionSort = ord(acqNucleusCode)

        refExperimentName = refExperiment.name

        # Ad hoc modifications - to get more common experiments first:
        downgrade = ('(', 'base','coupling', '[n')
        adhoc = any(x in refExperimentName for x in downgrade)
        if '{C' in refExperimentName:
          # Give higher priority to CA|Cca experiments
          atomSiteCountMod = atomSiteCount -1
          if 'co' in refExperimentName.lower():
            # Move CB/CA CO experiments yet one more level up
            atomSiteCountMod -= 0.5
        else:
          atomSiteCountMod = atomSiteCount

        # Put result on tuples list, with sorting keys in position
        key = tuple(sorted(refExperiment.nucleusCodes))
        tt = (key, multiAxisCodeSort, nucleusAcquisitionSort, adhoc, atomSiteCountMod,
              len(refExperimentName),refExperiment)
        tuples.append(tt)

    # Sort tuples by arranged sort codes
    tuples.sort()
    for tt in tuples:
      # Get actual result out and in dict

      refExperiment = tt[-1]
      key = tt[0]
      ll = result.get(key, [])
      ll.append(refExperiment)
      result[key] = ll

      # print(key, refExperiment.name, refExperiment.synonym)

    project._isotopeRefExperimentMap = result

  #
  return result


if __name__ == '__main__':
  pass
  # testExpPrototypes(resetCodes=True)
  # allAxisCodes, synonymTable = experimentSynonymSummary()
  # print("Axis Codes: %s" % list(sorted(allAxisCodes)))
  # for line in synonymTable:
  #   print(line)

  # from ccpn.util.Io import newProject
  # project = newProject("ExpPrototypeTest", overwriteExisting=True)
  # refMap = fetchIsotopeRefExperimentMap(project)

  # for tt in sorted ((len(key), key, val) for key,val in sorted(refMap.items())):
  #   # print ("@~@~", tt[0], tt[1])
  #   for refExp in tt[2]:
  #     if refExp.name == 'CO_CO[N]':
  #       expGraph = refExp.nmrExpPrototype.findFirstExpGraph()
  #       step2 = expGraph.findFirstExpStep(stepNumber=2)
  #       print(step2, step2.expMeasurement)
  #       expGraph.newExpStep(stepNumber=4, expMeasurement=step2.expMeasurement)
  #       for step in expGraph.sortedExpSteps():
  #         print('@~@~ CO_CO[N]',step, step.stepNumber, step.refExpDimRefs, step.expMeasurement)
  # project.saveModified()
