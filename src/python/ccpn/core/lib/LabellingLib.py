"""Labelling scheme handling. Functions to get labelling fraction

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================

__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                 " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

import typing

from ccpn.core.Atom import Atom
from ccpn.core.Sample import Sample
from ccpn.core.SampleComponent import SampleComponent


def getLabellingScheme(schemeName:str) ->  typing.Optional[typing.Dict]:
  """Get labelling scheme dictionary from scheme name (or None if none is found

  TODO NBNB probably needs more parameters and a different location"""
  raise NotImplementedError("getLabellingScheme not yet implemented")

def sampleComponentLabelledFraction(sampleComponent:SampleComponent,
                                    atom2IsotopeCode:typing.Dict[Atom,str]
                                    ) -> float:
  """Get labelled fraction from SampleComponent.
  All atoms must be from a chain compatible with SampleComponent.

  NB for x/y and % wildcard atoms, labelling is averaged over the
  component atoms. If only some of these are specifically labelled or
  in a labelling scheme, the rest will be assumed to have the
  default labelling of the sampleComponent. This may sometimes give
  misleading results, but it is the best available default behaviour"""

  result = 1.0
  isotopeCode2Fraction = sampleComponent.isotopeCode2Fraction
  processData = {}
  substance = sampleComponent.substance
  chains = sampleComponent.chains

  for atom, isotopeCode in atom2IsotopeCode.items():

    residue = atom.residue
    chain = residue.chain
    if chain not in chains:
      raise ValueError("%s does not match any of the chains for %s" % (atom, sampleComponent))

    # fraction serves as a sentinel, to check if there was specific labelling
    fraction = None

    if substance:
      # Go from Atom to a list of component atoms, to catch wildcard atoms
      atoms = [atom]
      ll = []
      for aa in atoms:
        ll2 = aa.componentAtoms
        if ll2:
          atoms.extend(ll2)
        else:
          ll.append(aa)
      atoms = ll

      # Sum specific labelling over wildcard component atoms
      summa = 0.0
      count = 0
      for aa in atoms:
        dd = substance.getSpecificAtomLabelling(aa)
        if dd:
          # There is a specific labelling for this atom
          fract = dd.get(isotopeCode)
          if fract is None:
            raise ValueError("isotopeCode %s not recognised in specificAtomLabelling for %s"
                             % (isotopeCode, atom))
          else:
            count += 1
            summa += fract

      if count:
        # At least some atoms were specifically labelled. Use them
        fraction = summa / len(atoms)
        if count < len(atoms):
          # Not all atoms were specifically labelled,
          # Could happen e.g. when checking HG% for a Valine with only one methyl group
          # specifically labelled, or for unsuitable labelling patterns
          # Assume default labeling for the rest.
          # This may give misleading results, but it is the best we can reasonably do.
          fract = isotopeCode2Fraction.get(isotopeCode)
          if fract is None:
            raise ValueError("isotopeCode %s not recognised for %s"
                             % (isotopeCode, atom))
          else:
            fraction += fract * (1 - count/len(atoms))

    if fraction is None:
      # Most common case - put in dta structure to process below
      dd2 = processData.get(residue, {})
      dd2[atom.name] = isotopeCode
      processData[residue] = dd2
    else:
      # include fraction in result
      result *= fraction

  # Process atoms that were not specifically labelled
  labelling = sampleComponent.labelling
  if labelling:
    labellingScheme = getLabellingScheme(labelling)
  else:
    labellingScheme = None
  for residue, atomName2IsotopeCode in processData.items():
    fraction = residueLabelledFraction(atomName2IsotopeCode=atomName2IsotopeCode,
                                       residueType=residue.residueType,
                                       labellingScheme=labellingScheme,
                                       isotopeCode2Fraction=isotopeCode2Fraction)
    # include fraction in result
    result *= fraction
  #
  return result


def residueLabelledFraction(atomName2IsotopeCode:typing.Dict[str,str], residueType:str=None,
                            labellingScheme:typing.Dict=None,
                            isotopeCode2Fraction:typing.Dict[str,float]=None,
                            ) -> float:
  """Get fraction matching isotopeCodes for atoms in a single residue from labeling scheme and/or
  uniform labeling. Position-specific labeling is NOT considered. If residueType or labellingScheme
  is absent, or if an atom name is not found in the labelling scheme, the isotopeCode2Fraction
  dictionary is used for that atom(s). If any atom has no labelling information anywhere, the
  function returns None.

  :params atomName2IsotopeCode  {atomName:isotopeCode} dictionary defining the labelling pattern
  to evaluate, e.g. {'CA':'13C', 'CB':'12C', 'CG':'13C'}.
  The atom name may may end in '%', referring to equivalent atoms e.g. Leu HB%, CD%, HD1% or HD%,
  in which case the labelling is averaged over the components.
  Non-stereo assigned atoms, e.g. Leu HBx or HDy% will also be averaged, treating
  HBx as HB% and HDy% as HD%. This will be misleading if the components have very different
  labelling levels, but it is the lesser evil.

  :params residueType  Type of residue that atoms belong to.
  If absent only uniform labelling is considered.

  :params labellingScheme  Labelling scheme dictionary (see example below).
  If absent only uniform labelling is considered.

  :params isotopeCode2Fraction  gives default uniform isotope
    percentages, as for SampleComponent.uniformIsotopeFractions (q.v.).
    Example value: {'12C':0.289, '13C':0.711, '1H':0.99985, '2H':0.00015}

  |  *Example of labeling scheme dictionary*
  |
  | 'MyScheme': {
  |   '_name':'MyScheme',
  |   'GLY':[
  |     { '_weight':0.2,
  |        'CA':{'13C':0.5, '12C':0.5}
  |         'C':{'13C':0.99,'12C':0.01}
  |     },
  |     {
  |          '_weight':0.5,
  |         'CA':{'13C':0.0, '12C':1.0}
  |         'C':{'13C':0.0,'12C':1.0}
  |     },
  |     {
  |        '_weight':0.3,
  |        'C':{'13C':0.95, '12C':0.05},
  |        'HA2':{'1H':0.7, '2H':0.3},
  |        'HA3':{'1H':0.7, '2H':0.3} }
  |   ],
  |   'ALA': [
  |   ...
  |   ],
  |   ...
  | },
  |
  | The first isotopomer is 50% 13C CA and 99% 13C carbonyl, and defaults to the uniform labelling
  | fraction for 1H and 15N.
  |
  | The second isotopomer is 100% C12 for both CA and carbonyl, and defaults to the uniform
  | labelling fraction for 1H and 15N
  |
  | The third isotopomer is 95% 13C for carbonyl, 30% deuterium labelled (i.e. 70% 1H) for the
  | aliphatic protons, and defaults to the uniform labelling fraction for nitrogen, CA, and NH
  | protons.


  """

  # NB This does NOT support wildcards ending in '*' (used e.g. for DNA "H2'*")
  # But the fragility of adding '*' is not worth the limited usefulness
  wildCardEndings = ('x%', 'y%', '%', 'x', 'y',)

  if residueType and labellingScheme:
    isotopomers = labellingScheme.get(residueType)
  else:
    isotopomers = None

  if isotopomers:
    result = 0.0
    weights = 0.0
    for isotopomer in isotopomers:

      contribution = 1.0

      for name, isotopeCode in atomName2IsotopeCode.items():
        dd = isotopomer.get(name)
        if dd:
          # Isotopomer has data for atom `name`
          fraction = dd.get(isotopeCode)

        else:
          # No data for atom `name`.
          fraction = None
          for ending in wildCardEndings:
            # Check if it is a wildcard atom

            if name.endswith(ending):
              # Wildcard. average over contained atoms
              length = len(ending)
              prefix = name[:-length]
              summa = 0.0
              count = 0
              for ss, dd in isotopomer.items():
                if ss.startswith(prefix) and ss[-length:].isdigit():
                  # Atom matches wildcard expression
                  fract = dd.get(isotopeCode)
                  if fract is None:
                    raise ValueError(
                      "Residue %s, atom %s (from %s) recognised, but no data for isotope %s"
                      % (residueType, ss, name, isotopeCode)
                    )
                  else:
                    count += 1
                    summa += fract
              if count:
                fraction = summa/count

              break

        if fraction is None:
          # Not a wildcard or no matches found - get fraction from isotope
          fraction = isotopeCode2Fraction.get(isotopeCode)

        if fraction is None:
          raise ValueError("Residue %s, atom %s recognised, but no data for isotope %s"
                           % (residueType, name, isotopeCode))

        else:
          contribution *= fraction

      weight = isotopomer['_weight']
      weights += weight
      result += contribution*weight
    #
    result /= weights

  else:
    # No isotopomers - get labelling from uniform fractions only
    result = 1.0
    for isotopeCode in atomName2IsotopeCode.values():
      fraction = isotopeCode2Fraction.get(isotopeCode)
      if fraction is None:
          raise ValueError("No data for isotope %s" % isotopeCode)
      else:
        result *= fraction
  #
  return result

def atomLabelledFraction(sample:Sample, atom2IsotopeCode:typing.Dict[Atom,str]) -> float:
  """
  Get fraction of cases in sample where the atoms have the
  indicated isotopeCodes.
  Equivalent groups of atoms e.g. Leu HB%, CD%, HD1% or HD%, will be averaged over their constituent
  atoms. Non-stereo assigned atoms, e.g. Leu HBx or HDy% will also be averaged, treating
  HBx as HB% and HDy% as HD%. This will be misleading if the components have very different
  labelling levels, but it remains the lesser evil.

  :params sample  Sample to use for determining labeling

  :params atom2IsotopeCode  {atom:isotopeCode} dictionary for atoms to look at.
 """

  # Reorganise input for processing
  processData = {}
  for atom, isotopeCode in atom2IsotopeCode:
    chain = atom.residue.chain
    dd = processData.get(chain,{})
    dd[atom] = isotopeCode
    processData[chain] = dd

  result = 1.0

  # Get labelledFractions, one chain at a time
  sampleComponents = sample.sampleComponents
  for chain, dd in processData.items():
    chainComponents = [x for x in sampleComponents if chain in x.chains]

    if chainComponents:
      sampleComponent0 = chainComponents[0]
      fraction = sampleComponentLabelledFraction(sampleComponent0, dd)

      if len(chainComponents) > 1:
        # Multiple components - we need to weigh them by concentration and redetermine fraction
        concentration0 = sampleComponent0.concentration
        unit0 = sampleComponent0.concentrationUnit
        if not concentration0:
          raise ValueError("Concentration not set for %s - cannot average over sampleComponents (1)"
                           % sampleComponent)

        weight = concentration0
        summa = fraction * concentration0
        for sampleComponent in chainComponents[1:]:
          concentration = sampleComponent.concentration
          if not concentration:
            raise ValueError(
              "Concentration not set for %s - cannot average over sampleComponents (2)"
              % sampleComponent
            )
          unit = sampleComponent.concentrationUnit
          if unit != unit0:
            raise ValueError("%s unit %s does not match previous component %s - %s"
                             % (sampleComponent, unit, sampleComponent0, unit0))
          fract = sampleComponentLabelledFraction(sampleComponent, dd)
          weight += concentration
          summa += fract * concentration
        #
        fraction = summa/weight
      #
      result *= fraction

    else:
      raise ValueError("Chain %s matches no SampleComponent in sample %s" % (chain, sample))
  #
  return result


# ###############################################################################
# #
# #  Old, V2-version-derived  functions:
# #
# ###############################################################################
#
# def atomLabellingFractions(project:Project, atom:(Atom, NmrAtom, str), labelling:str) -> dict:
#   """get {isotopeCode:labellingFraction} in given sample for atom/nmrAtom or ID string"""
#
#   atomId = atom if isinstance(atom, str) else atom.id
#
#   useAtom = project.getAtom(atomId)
#   if useAtom is None:
#     fields = Pid(atomId).fields
#     if len(fields) == 4:
#       atomName = fields[3]
#       residueType = fields[2]
#       return Labeling.chemAtomLabelFractions(project, labelling, residueType, atomName)
#
#     else:
#       # No valid parameters found, return empty dict
#       return {}
#
#   else:
#     return Labeling.molAtomLabelFractions(labelling, useAtom._wrappedData.residue.molResidue,
#                                           useAtom.name)
#
#
#
# def atomPairLabellingFractions(project:Project, atomPair:typing.Sequence, labelling:str) -> dict:
#   """get {(isotopeCode1,isotopeCode2):labellingFraction with given labelling for atom pair
#   each atom in atomPair may be an Atom, an NmrAtom, or an atom ID string """
#   atomIds = tuple(x if isinstance(x, str) else x.id for x in atomPair)
#
#   useAtoms = tuple(project.getAtom(x) for x in atomIds)
#   if None in useAtoms:
#     residueTypes = set()
#     atomNames = []
#     for atomId in atomIds:
#       fields = Pid(atomId).fields
#       if len(fields) == 4:
#         atomNames.append(fields[3])
#         residueTypes.add(fields[2])
#       else:
#         break
#     else:
#       if len(residueTypes) == 1:
#         return Labeling.chemAtomPairLabelFractions(project, labelling, residueTypes.pop(), atomNames)
#
#   else:
#     residues = tuple(x._wrappedData.residue.molResidue for x in useAtoms)
#     atomNames = tuple(x.name for x in useAtoms)
#     return Labeling.molAtomLabelPairFractions(labelling, residues, atomNames)
#
#   # no valid return - return empty
#   return {}
#
#
# def sampleLabellingFractions(sample:Sample, atom:(Atom, NmrAtom, str)) -> dict:
#   """get {isotopeCode:labellingFraction} with given labelling for atom/nmrAtom or ID string"""
#
#   atomId = atom if isinstance(atom, str) else atom.id
#   fields = Pid(atomId).fields
#   if len(fields) == 4:
#     chainCode, dummy, residueType, atomName = fields
#     labelling = Labeling.sampleChainLabeling(sample, chainCode)
#     if labelling == DEFAULT_LABELLING:
#       # No labelling found - return empty
#       return {}
#     else:
#       return atomLabellingFractions(sample._project, atomId, labelling)
#   else:
#     # Not a valid atom ID - return empty
#     return {}
#
#
# def samplePairLabellingFractions(sample:Sample, atomPair:typing.Sequence) -> dict:
#   """get {(isotopeCode1,isotopeCode2):labellingFraction in given sample for atom pair
#   each atom in atomPair may be an Atom, an NmrAtom, or an atom ID string """
#   atomIds = tuple(x if isinstance(x, str) else x.id for x in atomPair)
#
#   labellings = set()
#   residueTypes = set()
#   atomNames = []
#   for atomId in atomIds:
#     fields = Pid(atomId).fields
#     if len(fields) == 4:
#       atomNames.append(fields[3])
#       residueTypes.add(fields[2])
#       labellings.add(Labeling.sampleChainLabeling(sample, fields[0]))
#     else:
#       break
#
#   else:
#     if len(labellings) == 1:
#       labelling = labellings.pop()
#       useAtoms = tuple(sample._project.getAtom(x) for x in atomIds)
#       if None in useAtoms:
#         if len(residueTypes) == 1:
#           return Labeling.chemAtomPairLabelFractions(sample._project, labelling, residueTypes.pop(),
#                                                      atomNames)
#
#       else:
#         residues = tuple(x._wrappedData.residue.molResidue for x in useAtoms)
#         return Labeling.molAtomLabelPairFractions(labelling, residues, atomNames)
#
#   # No valid return found, return empty dict
#   return {}
