"""
A list of publicly available namespacing for user's macros only.

Examples of import usage:

    from ccpn import api
    api.Peak ...

    from ccpn.api import Peak
    Peak ....

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$Author: Luca Mureddu $"
__dateModified__ = "$Date: 2021-06-23 17:58:44 +0000 (Wed, June 23, 2021) $"
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-07-22 13:40:13 +0100 (Thu, July 22, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2021-06-23 18:02:28 +0100 (Wed, June 23, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================


#######################################
############  Core objects ############
#######################################

from ccpn.core.Project import Project
from ccpn.core.Spectrum import Spectrum
from ccpn.core.SpectrumReference import SpectrumReference
from ccpn.core.SpectrumGroup import SpectrumGroup
from ccpn.core.PeakList import PeakList
from ccpn.core.Peak import Peak
from ccpn.core.IntegralList import IntegralList
from ccpn.core.Integral import Integral
from ccpn.core.PseudoDimension import PseudoDimension
from ccpn.core.SpectrumHit import SpectrumHit
from ccpn.core.Sample import Sample
from ccpn.core.SampleComponent import SampleComponent
from ccpn.core.Substance import Substance
from ccpn.core.Chain import Chain
from ccpn.core.Residue import Residue
from ccpn.core.Atom import Atom
from ccpn.core.Complex import Complex
from ccpn.core.NmrChain import NmrChain
from ccpn.core.NmrAtom import NmrAtom
from ccpn.core.ChemicalShiftList import ChemicalShiftList
from ccpn.core.ChemicalShift import ChemicalShift
from ccpn.core.DataSet import DataSet
from ccpn.core.RestraintList import RestraintList
from ccpn.core.Restraint import Restraint
from ccpn.core.RestraintContribution import RestraintContribution
from ccpn.core.CalculationStep import CalculationStep
from ccpn.core.Data import Data
from ccpn.core.StructureEnsemble import StructureEnsemble
from ccpn.core.Model import Model
from ccpn.core.Note import Note
from ccpn.core.PeakCluster import PeakCluster
from ccpn.core.MultipletList import MultipletList
from ccpn.core.Multiplet import Multiplet


############################################
############   UI Core objects       #######
############################################

from ccpn.ui._implementation.Window import Window
from ccpn.ui._implementation.SpectrumDisplay import SpectrumDisplay
from ccpn.ui._implementation.Strip import Strip
from ccpn.ui._implementation.Axis import Axis
from ccpn.ui._implementation.Mark import Mark
from ccpn.ui._implementation.SpectrumView import SpectrumView
from ccpn.ui._implementation.MultipletListView import MultipletListView
from ccpn.ui._implementation.PeakListView import PeakListView
from ccpn.ui._implementation.IntegralListView import IntegralListView

#######################################
############  LIB objects       #######
#######################################


#######################################
############  Core functions    #######
#######################################


#######################################
############  UI functions      #######
#######################################


#######################################
############  LIB functions      ######
#######################################
