

import os

def _chemicalShiftMappingPymolTemplate(filePath, pdbPath, aboveThresholdResidues, belowThresholdResidues,
                                      missingdResidues, colourMissing, colourAboveThreshold,
                                      colourBelowThreshold, selection):

  """
  _CCPNnmr Internal. Used in ChemicalShift mapping Module
  This creates a file with a PyMol script to mirror the chemical shift mapping module selections etc..."""

  if os.path.exists(pdbPath):
    warn = 'This script is auto-generated. Any changes here will be lost.'
    with open(filePath, 'w') as f:
      f.write('''\n"""''' + warn + '''"""''')
      f.write('''\nfrom pymol import cmd''')
      f.write('''\n''')
      f.write('''\ncmd.load("''' + pdbPath + '''") ''')
      f.write('''\ncmd.hide('lines')''')
      f.write('''\ncmd.show('cartoon')''')
      f.write('''\ncmd.color('white')''')
      if len(aboveThresholdResidues)>0:
        f.write('''\ncmd.select('aboveThreshold', 'res  ''' + aboveThresholdResidues + ''' ')''')
        f.write('''\ncmd.set_color("AboveColour", " ''' + str(colourAboveThreshold) + ''' ")''')
        f.write('''\ncmd.color('AboveColour', 'aboveThreshold')''')
      if len(belowThresholdResidues) > 0:
        f.write('''\ncmd.select('belowThreshold', 'res  ''' + belowThresholdResidues + ''' ')''')
        f.write('''\ncmd.set_color("BelowColour", " ''' + str(colourBelowThreshold) + ''' ")''')
        f.write('''\ncmd.color('BelowColour', 'belowThreshold')''')
      if len(missingdResidues) > 0:
        f.write('''\ncmd.select('missing', 'res  ''' + missingdResidues + ''' ')''')
        f.write('''\ncmd.set_color("MissingColour", " ''' + str(colourMissing) + ''' ")''')
        f.write('''\ncmd.color('MissingColour', 'missing')''')
      if len(selection)>0:
        f.write('''\ncmd.select('Selected', 'res  ''' + selection + ''' ')''')
      else:
        f.write('''\ncmd.deselect()''')

  return filePath