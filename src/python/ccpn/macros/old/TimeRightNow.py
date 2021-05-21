"""
Print the right-now time in the correct format.
Ready to copy and paste on the header template __date__ field

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$Author: Luca Mureddu $"
__dateModified__ = "$Date: 2021-05-21 12:18:18 +0100 (Fri, May 21, 2021) $"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2021-05-21 12:18:18 +0100 (Fri, May 21, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================


if __name__ == '__main__':
    import time
    # Print the right-now time in the correct format. Ready to copy and paste on the __date__ field.
    t = time.strftime('%Y-%m-%d %H:%M:%S %z (%a, %B %d, %Y)')
    print('\n==========  date and time for header ========== \n')
    print(f'__date__ = "$Date: {t} $"')
    print('\n===============================================')
