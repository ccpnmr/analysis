"""Module Documentation here

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

# EXPERIMENT_TYPES = {1:{'1D':'H',
#                        'STD': 'STD.H',
#                        'WATER-LOGSY':'Water-LOGSY.H',
#                        'T2 relaxation-filtered': 'STD.H'
#                       },
#
#                     2:
#                       {'HN': {
#                       '15N HSQC/HMQC': 'H[N]',
#                       '15N HMBC': 'H_[N].Jcoupling'
#                      },
#                       'CH':{
#                         '13C HSQC/HMQC': 'H[C]',
#                         '13C HMBC': 'H_[C].Jcoupling',
#                         'CBcgcdHD':'hbCBcgcdHD',
#                         'CBcgcdhdHE':'hbCBcgcdceHE',
#                         'aromatic 13C HSQC': 'H[C[caro]]',
#                         'CACA':'Hca_CA.relayed',
#                       },
#                       'HH':{'NOESY':'H_H.through-space',
#                           'TOCSY':'H_H.relayed',
#                           'COSY': 'HH'
#                     },
#                       'CC': {
#                         'CACO': 'CACO',
#                         'CBCACO': 'CBCACO',
#                         'CC (onebond)': 'CC',
#                         'CC (relayed)': 'C_C.relayed',
#                         'CC (through-space)': 'C_C.through-space',
#                         'CC (relayed-alternate)': 'C_C.relayed-alternate',
#                       },
#                       'NC': {
#
#                       },
#                     },
#                     3:
#                       {'CHN':{
#                     'HNCA': 'H[N[CA]]',
#                     'H-detected HNcoCA': 'H[N[co[CA]]]',
#                     'HNcoCA/CB': 'H[N[co[{CA|ca[C]}]]]',
#                     'HNCA/CB': 'H[N[{CA|ca[Cali]}]]',
#                     'HNCO': 'H[N[CO]]',
#                     'HNcaCO': 'HNcaCO',
#                     'H-edited 13C,15N HSQC-NOESY-HSQC': 'h[C]_H[N].through-space'},
#
#                     'HH1N':{
#                         '15N HSQC-TOCSY': 'H[N]_H.relayed',
#                         '15N TOCSY-HSQC': 'H_H[N].relayed',
#                         '15N NOESY-HSQC': 'H_H[N].through-space',
#                         '15N HSQC-NOESY': 'H[N]_H.through-space',
#                         '15N HSQC-COSY':'H[N]H',
#                         '15N COSY-HSQC': 'HH[N]',
#                         'out-and-back HNCAHA': 'H[N[ca[HA]]]',
#                         'HBHAcoNH': 'H{ca|cca}[co[N]]HA',
#                         'HNcaHA': 'HNcaHA',
#                         'HAcaNH': 'HAcaNH',
#
#
#
#                       },
#                       'CCH1':{
#                             'CCH-TOCSY': 'C_CH.relayed',
#                             'HCC-TOCSY': 'HC_C.relayed',
#                       },
#                       'CHH1': {
#                               'HCcH-TOCSY': 'HC_cH.relayed',
#                               'HcCH-TOCSY': 'Hc_CH.relayed',
#                               '13C HSQC-NOESY': 'H[C]_H.through-space',
#                               '13C NOESY-HSQC': 'H_[C]H.through-space'
#
#                       },
#                       'CC1N' : {'NCACX': '',
#                                 'NCOCX': '',
#
#                       },
#                        },
#                     4: {
#                       '13C,15N HSQC-NOESY-HSQC': 'H[C]_H[N].through-space'
#                     },
#                     }
