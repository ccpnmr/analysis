"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:41 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
import sys
import string


# PATH1 = '/Users/wb104/miniconda3/envs/ccpnmr_dist'
# PATH2 = '/Users/wb104/release/ccpnmr3.0.b4/miniconda'

# Search through the /bin and /lib subdirectories of /miniconda
# and point the paths to the correct place
#
# ./convertPaths root pathfrom pathto
#
#     root        the root directory of miniconda
#     pathfrom    the paths in each file created from the installation
#     pathto      the required paths

def istext(filename):
    try:
        print(filename)
        with open(filename) as fp:
            s = fp.read(512)
        print(map(chr, range(32, 127)), list("\n\r\t\b"))
        return

        text_characters = "".join(map(chr, range(32, 127)) + list("\n\r\t\b"))
        _null_trans = string.maketrans("", "")
        if not s:
            # Empty files are considered text
            return True
        if "\0" in s:
            # Files with null bytes are likely binary
            return False
        # Get the non-text characters (maps a character to itself then
        # use the 'remove' option to get rid of the text characters.)
        t = s.translate(_null_trans, text_characters)
        # If more than 30% non-text characters, then
        # this is considered a binary file
        if float(len(t)) / float(len(s)) > 0.30:
            return False
        return True
    except:
        return False


def main(ROOT, PATH1, PATH2):
    for directory in ('bin', 'lib'):

        # os.chdir('miniconda/%s' % directory)
        os.chdir(ROOT + '/%s' % directory)

        filenames = os.listdir('.')
        filenames = [filename for filename in filenames if
                     os.path.isfile(filename) and not os.path.islink(filename)]

        for filename in filenames:
            # if istext(filename):

            try:
                # print('%s is text' % filename)
                with open(filename, 'r') as fp:
                    data = fp.read()
                if PATH1 in data:
                    print('changing path in %s' % filename)
                    data = data.replace(PATH1, PATH2)
                    with open(filename, 'w') as fp:
                        fp.write(data)

                        # else:
                        # print('%s is binary' % filename)
            except:
                # print ('  error reading:. %s' % filename)
                pass

        os.chdir('../..')


if __name__ == '__main__':
    inRoot = sys.argv[1]
    inPath1 = sys.argv[2]
    inPath2 = sys.argv[3]

    main(inRoot, inPath1, inPath2)
