"""
This file contains the NmrPipe DF definitions as copied from the C-code
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:33:14 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2020-11-20 10:28:48 +0000 (Fri, November 20, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================


# from ccpn.util.traits.CcpNmrTraits import List, Int


C_NmrPipeHeaderDefs = """
/***
 * fdatap.h: defines the NMRPipe data header array FDATA, and
 *           outlines some data format details.
 ***/

#include "dimloc.h"
#include "namelist2.h"

/***
 * The NMRPipe parameter array FDATA currently consists of 512 4-byte
 * floating-point values which describe the spectral data.  While all numerical
 * values in this array are floating point, many represent parameters
 * (such as size in points) which are integers.  Some parts of the
 * header contain packed ascii text.
 *
 * There are currently three variations of spectral data in the NMRPipe
 * format:
 *
 *   1. Single-File (1D and 2D): the data are stored in a single
 *      binary file consiting of the header followed by the
 *      spectral intensities, stored in sequential order as
 *      4-byte floats.
 *
 *   2. Multi-File (3D and 4D): the data are stored as a series
 *      of 2D file planes, each with its own complete header
 *      followed by the spectral intensities in sequential order.
 *
 *   3. Data Stream (1D-4D): the data are in the form of a pipeline
 *      stream, with a single header at the beginning followed by
 *      all of the spectral intensities in sequential order.
 *
 * The header values can be manipulated directly, but this is not
 * recommended.  Instead, the functions getParm() and setParm() can
 * be used to extract or set header values according to parameter
 * codes and the dimension of interest (if any).  See the source
 * code distribution for examples of these functions.
 *
 * The NMRPipe format was created to be compatible with an older format
 * which pre-dates phase-sensitive NMR and multidimensional NMR.
 * So, for historical reasons, there are some potentially confusing
 * aspects regarding definition of dimension sizes, data types,
 * and interleaving of real and imaginary data.
 *
 * In the NMRPipe nomenclature, the dimensions are called the X-Axis,
 * Y-Axis, Z-Axis, and A-Axis.  Some rules of thumb about the data format
 * follow:
 *
 *  1. Complex data in the X-Axis is stored as separated 1D vectors
 *     of real and imaginary points (see below).
 *
 *  2. Complex data in the Y-Axis, Z-Axis, and A-Axis is stored as
 *     interleaved real and imaginary points.
 *
 *  3. The X-Axis size is recorded as complex points.
 *
 *  4. The Z-Axis and A-Axis sizes are recorded as total points real+imag.
 *
 *  5. If both the X-Axis and Y-Axis are complex, the Y-Axis size
 *     is reported as total points real+imag.
 *
 *  6. If the X-Axis is not complex but the Y-Axis is complex,
 *     the Y-axis size is reported as complex points.
 *
 *  7. TPPI data, and Bruker QSEQ mode data are treated as real data.
 ***/

/***
 * 1D Real Format:
 *  (512-point FDATA)
 *  (N real points...)
 *
 * 1D Complex Format:
 *  (512-point FDATA)
 *  (N real points...)
 *  (N imag points...)
 *
 * 2D Hypercomplex Format;
 * (direct dimension = t2, indirect dimension = t1):
 *
 *  (512-point FDATA)
 *  (N t2=real points... for t1=1 Real)
 *  (N t2=imag points... for t1=1 Real)
 *  (N t2=real points... for t1=1 Imag)
 *  (N t2=imag points... for t1=1 Imag)
 *  (N t2=real points... for t1=2 Real)
 *  (N t2=imag points... for t1=2 Real)
 *  (N t2=real points... for t1=2 Imag)
 *  (N t2=imag points... for t1=2 Imag)
 *  ... etc ...
 *  (N t2=real points... for t1=M Real)
 *  (N t2=imag points... for t1=M Real)
 *  (N t2=real points... for t1=M Imag)
 *  (N t2=imag points... for t1=M Imag)
 *
 * 3D Hypercomplex format: consists of a series of 2D hypercomplex
 * planes above, which are alternating real and imaginary in the third
 * dimension.
 *
 * 4D Hypercomplex format: consists of a series of 3D hypercomplex
 * spectra above, which are alternating real and imaginary in the
 * fourth dimension.
 ***/

/***
 * Some useful constant definitions:
 ***/

#define FDATASIZE          512   /* Length of header in 4-byte float values. */

// pipe magic numbers
#magic FDIEEECONS   0xeeeeeeee  /* Indicates IEEE floating point format.    */
#magic FDVAXCONS    0x11111111  /* Indicates DEC VAX floating point format. */
#magic FDORDERCONS       2.345  /* Constant used to determine byte-order.   */
#magic FDFMTCONS    0xeeeeeeee  /* Floating point format on this computer.  */

/***
 * General Parameter locations:
 ***/

#define FDMAGIC        0 /* Should be zero in valid NMRPipe data.            */
#define FDFLTFORMAT    1 /* Constant defining floating point format.         */
#define FDFLTORDER     2 /* Constant defining byte order.                    */

#define FDSIZE        99 /* Number of points in current dim R|I.             */
#define FDREALSIZE    97 /* Number of valid time-domain pts (obsolete).      */
#define FDSPECNUM    219 /* Number of complex 1D slices in file.             */
#define FDQUADFLAG   106 /* See Data Type codes below.                       */
#define FD2DPHASE    256 /* See 2D Plane Type codes below.                   */


/***
 * Parameters defining number of dimensions and their order in the data;
 * a newly-converted FID has dimension order (2 1 3 4). These dimension
 * codes are a hold-over from the oldest 2D NMR definitions, where the
 * directly-acquired dimension was always t2, and the indirect dimension
 * was t1.
 ***/

#define FDTRANSPOSED 221 /* 1=Transposed, 0=Not Transposed.                  */
#define FDDIMCOUNT     9 /* Number of dimensions in complete data.           */
#define FDDIMORDER    24 /* Array describing dimension order.                */

#define FDDIMORDER1   24 /* Dimension stored in X-Axis.                      */
#define FDDIMORDER2   25 /* Dimension stored in Y-Axis.                      */
#define FDDIMORDER3   26 /* Dimension stored in Z-Axis.                      */
#define FDDIMORDER4   27 /* Dimension stored in A-Axis.                      */

#define FDNUSDIM      45 /* Unexpanded NUS dimensions.                       */

/***
 * The following parameters describe the data when it is
 * in a multidimensional data stream format (FDPIPEFLAG != 0):
 ***/

#define FDPIPEFLAG    57 /* Dimension code of data stream.    Non-standard.  */
#define FDPIPECOUNT   75 /* Number of functions in pipeline.  Non-standard.  */
#define FDSLICECOUNT 443 /* Number of 1D slices in stream.    Non-standard.  */
#define FDFILECOUNT  442 /* Number of files in complete data.                */

/***
 * The following definitions are used for data streams which are
 * subsets of the complete data, as for parallel processing:
 ***/

#define FDFIRSTPLANE  77 /* First Z-Plane in subset.            Non-standard. */
#define FDLASTPLANE   78 /* Last Z-Plane in subset.             Non-standard. */
#define FDPARTITION   65 /* Slice count for client-server mode. Non-standard. */

#define FDPLANELOC    14 /* Location of this plane; currently unused.         */

/***
 * The following define max and min data values, previously used
 * for contour level setting:
 ***/

#define FDMAX        247 /* Max value in real part of data.                  */
#define FDMIN        248 /* Min value in real part of data.                  */
#define FDSCALEFLAG  250 /* 1 if FDMAX and FDMIN are valid.                  */
#define FDDISPMAX    251 /* Max value, used for display generation.          */
#define FDDISPMIN    252 /* Min value, used for display generation.          */

/***
 * Locations reserved for User customization:
 ***/

#define FDUSER1       70
#define FDUSER2       71
#define FDUSER3       72
#define FDUSER4       73
#define FDUSER5       74
#define FDUSER6       76

/***
 * Defines location of "footer" information appended to spectral
 * data; currently unused for NMRPipe format:
 ***/

#define FDLASTBLOCK  359
#define FDCONTBLOCK  360
#define FDBASEBLOCK  361
#define FDPEAKBLOCK  362
#define FDBMAPBLOCK  363
#define FDHISTBLOCK  364
#define FD1DBLOCK    365

/***
 * Defines data and time data was converted:
 ***/

#define FDMONTH      294
#define FDDAY        295
#define FDYEAR       296
#define FDHOURS      283
#define FDMINS       284
#define FDSECS       285

/***
 * Miscellaneous Parameters:
 ***/

#define FDMCFLAG      135 /* Magnitude Calculation performed.               */
#define FDNOISE       153 /* Used to contain an RMS noise estimate.         */
#define FDRANK        180 /* Estimate of matrix rank; Non-standard.         */
#define FDTEMPERATURE 157 /* Temperature, degrees C.                        */
#define FD2DVIRGIN    399 /* 0=Data never accessed, header never adjusted.  */
#define FDTAU         199 /* A Tau value (for spectral series).             */

#define FDSRCNAME    286  /* char srcFile[16]  286-289 */
#define FDUSERNAME   290  /* char uName[16]    290-293 */
#define FDOPERNAME   464  /* char oName[32]    464-471 */
#define FDTITLE      297  /* char title[60]    297-311 */
#define FDCOMMENT    312  /* char comment[160] 312-351 */

/***
 * For meanings of these dimension-specific parameters,
 * see the corresponding ND parameters below.
 ***/

#define FDF2LABEL     16
#define FDF2APOD      95
#define FDF2SW       100
#define FDF2OBS      119
#define FDF2ORIG     101
#define FDF2UNITS    152
#define FDF2QUADFLAG  56 /* Non-standard. */
#define FDF2FTFLAG   220
#define FDF2AQSIGN    64 /* Non-standard. */
#define FDF2LB       111
#define FDF2CAR       66 /* Non-standard. */
#define FDF2CENTER    79 /* Non-standard. */
#define FDF2OFFPPM   480 /* Non-standard. */
#define FDF2P0       109
#define FDF2P1       110
#define FDF2APODCODE 413
#define FDF2APODQ1   415
#define FDF2APODQ2   416
#define FDF2APODQ3   417
#define FDF2C1       418
#define FDF2ZF       108
#define FDF2X1       257 /* Non-standard. */
#define FDF2XN       258 /* Non-standard. */
#define FDF2FTSIZE    96 /* Non-standard. */
#define FDF2TDSIZE   386 /* Non-standard. */

#define FDF1LABEL     18
#define FDF1APOD     428
#define FDF1SW       229 
#define FDF1OBS      218 
#define FDF1ORIG     249 
#define FDF1UNITS    234 
#define FDF1FTFLAG   222 
#define FDF1AQSIGN   475 /* Non-standard. */
#define FDF1LB       243
#define FDF1QUADFLAG  55 /* Non-standard. */
#define FDF1CAR       67 /* Non-standard. */
#define FDF1CENTER    80 /* Non-standard. */
#define FDF1OFFPPM   481 /* Non-standard. */
#define FDF1P0       245
#define FDF1P1       246
#define FDF1APODCODE 414
#define FDF1APODQ1   420
#define FDF1APODQ2   421 
#define FDF1APODQ3   422
#define FDF1C1       423
#define FDF1ZF       437
#define FDF1X1       259 /* Non-standard. */
#define FDF1XN       260 /* Non-standard. */
#define FDF1FTSIZE    98 /* Non-standard. */
#define FDF1TDSIZE   387 /* Non-standard. */

#define FDF3LABEL     20
#define FDF3APOD      50 /* Non-standard. */
#define FDF3OBS       10
#define FDF3SW        11
#define FDF3ORIG      12
#define FDF3FTFLAG    13
#define FDF3AQSIGN   476 /* Non-standard. */
#define FDF3SIZE      15
#define FDF3QUADFLAG  51 /* Non-standard. */
#define FDF3UNITS     58 /* Non-standard. */
#define FDF3P0        60 /* Non-standard. */
#define FDF3P1        61 /* Non-standard. */
#define FDF3CAR       68 /* Non-standard. */
#define FDF3CENTER    81 /* Non-standard. */
#define FDF3OFFPPM   482 /* Non-standard. */
#define FDF3APODCODE 400 /* Non-standard. */
#define FDF3APODQ1   401 /* Non-standard. */
#define FDF3APODQ2   402 /* Non-standard. */
#define FDF3APODQ3   403 /* Non-standard. */
#define FDF3C1       404 /* Non-standard. */
#define FDF3ZF       438 /* Non-standard. */
#define FDF3X1       261 /* Non-standard. */
#define FDF3XN       262 /* Non-standard. */
#define FDF3FTSIZE   200 /* Non-standard. */
#define FDF3TDSIZE   388 /* Non-standard. */

#define FDF4LABEL     22
#define FDF4APOD      53 /* Non-standard. */
#define FDF4OBS       28
#define FDF4SW        29
#define FDF4ORIG      30
#define FDF4FTFLAG    31
#define FDF4AQSIGN   477 /* Non-standard. */
#define FDF4SIZE      32
#define FDF4QUADFLAG  54 /* Non-standard. */
#define FDF4UNITS     59 /* Non-standard. */
#define FDF4P0        62 /* Non-standard. */
#define FDF4P1        63 /* Non-standard. */
#define FDF4CAR       69 /* Non-standard. */
#define FDF4CENTER    82 /* Non-standard. */
#define FDF4OFFPPM   483 /* Non-standard. */
#define FDF4APODCODE 405 /* Non-standard. */
#define FDF4APODQ1   406 /* Non-standard. */
#define FDF4APODQ2   407 /* Non-standard. */
#define FDF4APODQ3   408 /* Non-standard. */
#define FDF4C1       409 /* Non-standard. */
#define FDF4ZF       439 /* Non-standard. */
#define FDF4X1       263 /* Non-standard. */
#define FDF4XN       264 /* Non-standard. */
#define FDF4FTSIZE   201 /* Non-standard. */
#define FDF4TDSIZE   389 /* Non-standard. */

/***
 * Header locations in use for packed text; adjust function
 * isHdrStr() and isHdrStr0 if new text locations are added:
 ***/

/* 286 287 288 289                                                     */
/* 290 291 292 293                                                     */
/* 464 465 466 467  468 469 470 471                                    */
/* 297 298 299 300  301 302 303 304  305 306 307 308  309 310 311      */
/* 312 313 314 315  316 317 318 319  320 321 322 323  324 325 326 327  */
/* 328 329 330 331  332 333 334 335  336 337 338 339  340 341 342 343  */
/* 344 345 346 347  348 349 350 351                                    */

#define SIZE_NDLABEL    8
#define SIZE_F2LABEL    8
#define SIZE_F1LABEL    8
#define SIZE_F3LABEL    8
#define SIZE_F4LABEL    8

#define SIZE_SRCNAME   16
#define SIZE_USERNAME  16
#define SIZE_OPERNAME  32
#define SIZE_COMMENT  160
#define SIZE_TITLE     60

/***
 * The following are definitions for generalized ND parameters:
 ***/

#general NDPARM        1000

#general NDSIZE        (1+NDPARM)  /* Number of points in dimension.          */
#general NDAPOD        (2+NDPARM)  /* Current valid time-domain size.         */
#general NDSW          (3+NDPARM)  /* Sweep Width Hz.                         */
#general NDORIG        (4+NDPARM)  /* Axis Origin (Last Point), Hz.           */
#general NDOBS         (5+NDPARM)  /* Obs Freq MHz.                           */
#general NDFTFLAG      (6+NDPARM)  /* 1=Freq Domain 0=Time Domain.            */
#general NDQUADFLAG    (7+NDPARM)  /* Data Type Code (See Below).             */
#general NDUNITS       (8+NDPARM)  /* Axis Units Code (See Below).            */
#general NDLABEL       (9+NDPARM)  /* 8-char Axis Label.                      */
#general NDLABEL1      (9+NDPARM)  /* Subset of 8-char Axis Label.            */
#general NDLABEL2     (10+NDPARM)  /* Subset of 8-char Axis Label.            */
#general NDP0         (11+NDPARM)  /* Zero Order Phase, Degrees.              */
#general NDP1         (12+NDPARM)  /* First Order Phase, Degrees.             */
#general NDCAR        (13+NDPARM)  /* Carrier Position, PPM.                  */
#general NDCENTER     (14+NDPARM)  /* Point Location of Zero Freq.            */
#general NDAQSIGN     (15+NDPARM)  /* Sign adjustment needed for FT.          */
#general NDAPODCODE   (16+NDPARM)  /* Window function used.                   */
#general NDAPODQ1     (17+NDPARM)  /* Window parameter 1.                     */
#general NDAPODQ2     (18+NDPARM)  /* Window parameter 2.                     */
#general NDAPODQ3     (19+NDPARM)  /* Window parameter 3.                     */
#general NDC1         (20+NDPARM)  /* Add 1.0 to get First Point Scale.       */
#general NDZF         (21+NDPARM)  /* Negative of Zero Fill Size.             */
#general NDX1         (22+NDPARM)  /* Extract region origin, if any, pts.     */
#general NDXN         (23+NDPARM)  /* Extract region endpoint, if any, pts.   */
#general NDOFFPPM     (24+NDPARM)  /* Additional PPM offset (for alignment).  */
#general NDFTSIZE     (25+NDPARM)  /* Size of data when FT performed.         */
#general NDTDSIZE     (26+NDPARM)  /* Original valid time-domain size.        */
#general MAX_NDPARM   (27)

/***
 * Axis Units, for NDUNITS:
 ***/

#define FD_SEC       1
#define FD_HZ        2
#define FD_PPM       3
#define FD_PTS       4

/***
 * 2D Plane Type, for FD2DPHASE:
 ***/

#define FD_MAGNITUDE 0
#define FD_TPPI      1
#define FD_STATES    2
#define FD_IMAGE     3
#define FD_ARRAY     4

/***
 * Data Type (FDQUADFLAG and NDQUADFLAG)
 ***/

#define FD_QUAD       0
#define FD_COMPLEX    0
#define FD_SINGLATURE 1
#define FD_REAL       1
#define FD_PSEUDOQUAD 2
#define FD_SE         3
#define FD_GRAD       4

/***
 * Sign adjustment needed for FT (NDAQSIGN):
 ***/

#define ALT_NONE            0 /* No sign alternation required.                */
#define ALT_SEQUENTIAL      1 /* Sequential data needing sign alternation.    */
#define ALT_STATES          2 /* Complex data needing sign alternation.       */
#define ALT_NONE_NEG       16 /* As above, with negation of imaginaries.      */
#define ALT_SEQUENTIAL_NEG 17 /* As above, with negation of imaginaries.      */
#define ALT_STATES_NEG     18 /* As above, with negation of imaginaries.      */

#define FOLD_INVERT        -1 /* Folding requires sign inversion.             */
#define FOLD_BAD            0 /* Folding can't be performed (extracted data). */
#define FOLD_ORDINARY       1 /* Ordinary folding, no sign inversion.         */

"""

# Convert FD defs into a dict
_tmp = []
for line in C_NmrPipeHeaderDefs.splitlines():
    fields = line.split()
    if len(fields)  >= 3 and fields[0] == '#define':
        _tmp.append( (fields[1], int(fields[2])) )

nmrPipeFDdict = dict(_tmp)