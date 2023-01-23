"""
This file contains Reference ChemicalShifts related functionalities

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2023-01-23 11:36:54 +0000 (Mon, January 23, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2023-01-14 18:34:47 +0000 (Sat, January 14, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

import math
from collections import Counter, OrderedDict

from ccpn.util.traits.CcpNmrJson import CcpNmrJson, CcpnJsonDirectoryABC
from ccpn.util.traits.CcpNmrTraits import Unicode, Int, Float, Bool, List

from ccpn.framework.PathsAndUrls import ccpnResourcesPath
from ccpn.util.Path import aPath
from ccpn.util.decorators import singleton


#=========================================================================================
# namespaces

TITLE = 'title'
COMMENT = 'comment'
MOLECULETYPE = 'moleculeType'
APPLICATIONVERSION = 'applicationVersion'
FILEVERSION = 'fileVersion'
CREATIONDATE = 'creation_date_dd-mm-yy'
USER = 'user'

### residues level
RESIDUES = 'residues'
RESIDUENAME = 'residueName'
SHORTNAME = 'shortName'
CCPCODE = 'ccpcode'
ATOMS = 'atoms'

### Atoms level
ATOMNAME = 'atomName'
ELEMENT = 'element'
AVERAGESHIFT = "averageShift"
MINSHIFT = "minShift"
MAXSHIFT= "maxShift"
STDSHIFT = "stdShift"
DISTRIBUTION = 'distribution'
DISTRIBUTIONREFVALUE = 'distributionRefValue'
DISTRIBUTIONVALUEPERPOINT = 'distributionValuePerPoint'

VERSION = 1.0

class AtomReferenceShift(CcpNmrJson):
    """Class to store the Atom ReferenceChemicalShift information
    """
    classVersion = VERSION
    saveAllTraitsToJson = True

    atomName  =  Unicode(allow_none=False, default_value='??').tag(info='The atom name. NEF nomenclature. E.g.: HB%')
    residueName = Unicode(allow_none=False, default_value='??').tag(info='The parent Residue name. E.g.: Alanine')
    isotopeCode = Unicode(allow_none=False, default_value='??').tag(info='The isotope code identifier, e.g. 1H, 13C, etc')
    averageShift = Float(allow_none=False, default_value=0.0).tag(info='The atom average chemical shift in ppm. E.g.: 1.352')
    stdShift = Float(allow_none=False, default_value=0.0).tag(info='The atom standard deviation of all observed chemical shifts. E.g.: 0.277')
    minShift = Float(allow_none=True, default_value=0.0).tag(info='The atom minimal observed chemical shift in ppm. E.g.: -14.040')
    maxShift = Float(allow_none=True, default_value=0.0).tag(info='The atom minimal observed chemical shift in ppm. E.g.: -14.040')

    ## The following information is needed only to accurately plot the distribution curve on the Reference ChemicalShifts GUI module.
    distribution =  List(allow_none=True, default_value=[]).tag(info='The individually observed chemical shift Y values for plotting the distribution curve')
    distributionRefValue = Float(allow_none=True, default_value=0.0).tag(info='The reference value of the distribution list.  Mandatory if the distribution list is given')
    distributionValuePerPoint =  Float(allow_none=True, default_value=None).tag(info='The value per point needed for recreating the X axis of the distribution. Mandatory if the distribution list is given')

    # to allow them to be sorted
    def __le__(self, other):
        return self.averageShift <= other.averageShift

    def __lt__(self, other):
        return self.averageShift < other.averageShift

    def __str__(self):
        return '<AtomReference %s>' % self.atomName

    def __repr__(self):
        distribution = self.distribution
        distributionRepr = [] if not distribution else [distribution[0], '...']
        dd = dict(self.items())
        dd.update({'distribution':distributionRepr})
        return 'AtomReference(%s)' % ', '.join(['%s=%r'%(k,v) for k,v in dd.items()])

class ResidueReferenceShift(CcpNmrJson):
    """Class to store the Residue ReferenceChemicalShift information
    """
    classVersion = VERSION
    saveAllTraitsToJson = True

    residueName = Unicode(allow_none=False, default_value='??').tag(info='The residue name. E.g.: Alanine')
    shortName = Unicode(allow_none=False, default_value='??').tag(info='The residue short name. Three letter code for protein, Two letter code for DNA, etc. E.g.: ALA')
    ccpcode = Unicode(allow_none=True, default_value='??').tag(info='The unique ccp code if available. E.g.: Ala')
    atoms = List(allow_none=False, default_value=[]).tag(info='The list of AtomReference as JsonObject')
    # parent = the ReferenceShift JsonObject


class ReferenceChemicalShift(CcpNmrJson):
    """Class to store the ReferenceChemicalShift information
    """
    title = Unicode(allow_none=False, default_value='??').tag(info='A short one/two word title.  This will appear in the GUI as an entry in ReferenceChemicalShifts selection widget(s)')
    comment = Unicode(allow_none=False, default_value='??').tag(info='A brief explanation of what the file contains.  This message will appear in the GUI tooltips for the selection widget(s)')
    moleculeType = Unicode(allow_none=True, default_value='??').tag(info='The molecule type described in the file')
    residues = List(allow_none=False, default_value=[]).tag(info='The list of  ResidueReference as JsonObject')

    # parent = the ReferenceShift JsonObject


    def toJson(self, path=None):
        pass


    def fromJson(self, path):
        pass

@singleton
class ReferenceChemicalShifts(dict):
    """
    Class to contain all ReferenceChemicalShifts
    """
    attributeName = 'ReferenceChemicalShifts'
    directory = aPath(ccpnResourcesPath) / 'referenceChemicalShifts'


    #------------------------------------------------------------------------------------------------------
    # Json save and restore
    #------------------------------------------------------------------------------------------------------
    def toJson(self, path=None):
        pass

    def fromJson(self, path):
        pass
