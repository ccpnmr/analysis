#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2018"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               )
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y"
                 )
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: geertenv $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:36 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2018-05-14 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

class TraitJsonHandlerBase():
    """Base class for all Trait json handlers;

     Any jsonHandler class must derive from TraitJsonHandlerBase and can subclass
     two  methods:

         encode(obj, trait) which returns a json serialisable object
         decode(obj, trait, value) which uses value to generate and set the new (or modified) obj

     Example:

         class myHandler(TraitJsonHandlerBase):
               def encode(self, obj, trait):
                   "returns a json serialisable object"
                   value = getattr(obj, trait)
                   -- some action on value --
                   return value

               def decode(self, obj, trait, value):
                   "uses value to generate and set the new (or modified) obj"
                   newValue =  --- some action using value ---
                   setattr(obj, trait, newValue)
    """

    def encode(self, obj, trait):
        "returns a json serialisable object"
        return getattr(obj, trait)

    def decode(self, obj, trait, value):
        "uses value to generate and set the new (or modified) obj"
        setattr(obj, trait, value)
