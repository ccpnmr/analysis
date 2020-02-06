
/*
======================COPYRIGHT/LICENSE START==========================

npy_defns.h: Part of the CcpNmr Analysis program

Copyright (C) 2011 Wayne Boucher and Tim Stevens (University of Cambridge)

=======================================================================

The CCPN license can be found in ../../../license/CCPN.license.

======================COPYRIGHT/LICENSE END============================

for further information, please contact :

- CCPN website (http://www.ccpn.ac.uk/)

- email: ccpn@bioc.cam.ac.uk

- contact the authors: wb104@bioc.cam.ac.uk, tjs23@cam.ac.uk
=======================================================================

If you are using this software for academic purposes, we suggest
quoting the following references:

===========================REFERENCE START=============================
R. Fogh, J. Ionides, E. Ulrich, W. Boucher, W. Vranken, J.P. Linge, M.
Habeck, W. Rieping, T.N. Bhat, J. Westbrook, K. Henrick, G. Gilliland,
H. Berman, J. Thornton, M. Nilges, J. Markley and E. Laue (2002). The
CCPN project: An interim report on a data model for the NMR community
(Progress report). Nature Struct. Biol. 9, 416-418.

Wim F. Vranken, Wayne Boucher, Tim J. Stevens, Rasmus
H. Fogh, Anne Pajon, Miguel Llinas, Eldon L. Ulrich, John L. Markley, John
Ionides and Ernest D. Laue (2005). The CCPN Data Model for NMR Spectroscopy:
Development of a Software Pipeline. Proteins 59, 687 - 696.

===========================REFERENCE END===============================
*/
#ifndef _incl_npy_defns
#define _incl_npy_defns

#include "Python.h"
#include "defns.h"

#define RETURN_OBJ_ERROR(message)              \
    {                                          \
        PyErr_SetString(ErrorObject, message); \
        return NULL;                           \
    }

#define RETURN_INT_ERROR(message)              \
    {                                          \
        PyErr_SetString(ErrorObject, message); \
        return -1;                             \
    }

#define CHECK_OBJ_STATUS(status)                                 \
    {                                                            \
        if ((status) == CCPN_ERROR) RETURN_OBJ_ERROR(error_msg); \
    }

#define PY_MALLOC(obj, type, typeobj)      \
    {                                      \
        obj = PyObject_NEW(type, typeobj); \
        DEBUG_CODE_HEX("py_malloc", obj);  \
    }

#define PY_FREE(obj)                    \
    {                                   \
        DEBUG_CODE_HEX("py_free", obj); \
        PyObject_DEL(obj);              \
    }

#ifdef WIN32
#define PY_MOD_INIT_FUNC PyMODINIT_FUNC
#else
#define PY_MOD_INIT_FUNC void
#endif

#endif /* _incl_npy_defns */
