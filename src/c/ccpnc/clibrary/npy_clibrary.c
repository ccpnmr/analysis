/*
======================COPYRIGHT/LICENSE START==========================

npy_clibrary2d.c: Part of the CcpNmr Analysis program

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

#include "Python.h"

#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION  // so that warnings avoided
#include "arrayobject.h"
#include "npy_defns.h"

/*
  Module: Clibrary2d

  Function:

    Input:

    Output:

*/

static PyObject *ErrorObject; /* locally-raised exception */

static PyObject *newList() {
    PyObject *list;
    list = PyList_New(0);
    if (!list) {
        RETURN_OBJ_ERROR("allocating list memory");
    }
    return list;
}

static void *appendFloatList(PyObject *list, double value) {
    if (PyList_Append(list, PyFloat_FromDouble((double)value)) != 0) {
        RETURN_OBJ_ERROR("appending item to list");
    }
    return NULL;
}

static void *appendFloatLong(PyObject *list, long value) {
    if (PyList_Append(list, PyLong_FromLong(value)) != 0) {
        RETURN_OBJ_ERROR("appending item to list");
    }
    return NULL;
}

struct Node {
    // Struct to contain nmrResidue information

    // data
    PyObject *object;
    double relativeOffset;
    long index;
    CcpnBool seqCodeCompare;
    long seqCode;
    char *seqInsertCode;
    CcpnBool isConnected;
    CcpnBool seqIsReference;

    // pointers
    struct Node *prev;
    struct Node *next;
};

struct Node *newNode(PyObject *nmrResidue) {
    // create a new element
    struct Node *temp = (struct Node *)malloc(sizeof(struct Node));

    // set up the data
    temp->relativeOffset = -0.1;
    temp->index = -1;
    temp->object = nmrResidue;
    temp->seqIsReference = CCPN_FALSE;

    //    strcpy(&(temp->seqInsertCode), "");
    //    STRING_MALLOC_NEW(temp->seqInsertCode, "");

    // initialise the pointers
    temp->prev = NULL;
    temp->next = NULL;
    return temp;
}

static CcpnBool compareRes(struct Node *leftNode, struct Node *rightNode) {
    int strCompare;

    // compare whether 2 residues in connected stretch are similar
    // need to clean this up

    // compare index
    if (leftNode->index == rightNode->index) {
        // compare seqInsertCode
        strCompare = strcmp(leftNode->seqInsertCode, rightNode->seqInsertCode);

        if (strCompare == 0) {
            //            printf("string identical\n");

            // compare relativeOffset
            if (leftNode->relativeOffset < rightNode->relativeOffset)
                return CCPN_TRUE;
            else
                return CCPN_FALSE;
        } else if (strCompare < 0) {
            return CCPN_TRUE;
            //            printf("string less\n");
        } else {
            return CCPN_FALSE;
            //            printf("string greater\n");
        }

    } else if (leftNode->index < rightNode->index)
        return CCPN_TRUE;
    else
        return CCPN_FALSE;
}

struct Node *insertConnected(struct Node *node, struct Node *item) {
    // If the tree is empty, return previously defined new node
    if (!node) return item;

    // Otherwise, recurse down the tree
    if (compareRes(item, node) == CCPN_TRUE)
        node->prev = insertConnected(node->prev, item);
    else
        node->next = insertConnected(node->next, item);

    return node;
}

struct Node *insertConnectedNode(struct Node **headRef, PyObject *offsetItem, long index, CcpnBool isConnected,
                                 CcpnBool isMainResonance) {
    struct Node *temp = newNode(offsetItem);
    struct Node *ptr = (*headRef);
    double relOffset;
    PyObject *offsetTest;
    PyObject *seqInsertCode;
    PyObject *seqCode;
    PyObject *serial;
    PyObject *seqString;
    PyObject *apiDict = PyObject_GetAttrString(offsetItem, "__dict__");

    temp->isConnected = isConnected;
    if (isConnected == CCPN_TRUE) {
        temp->index = index;
        STRING_MALLOC_NEW(temp->seqInsertCode, "");
    } else {
        seqCode = PyDict_GetItemString(apiDict, "seqCode");
        serial = PyDict_GetItemString(apiDict, "serial");

        if (isMainResonance)
            if (seqCode == Py_None)
                temp->index = PyLong_AsLong(serial) + 1000000000;
            else
                temp->index = PyLong_AsLong(seqCode);
        else
            temp->index = index;

        seqInsertCode = PyDict_GetItemString(apiDict, "seqInsertCode");

        if (seqInsertCode == Py_None) {
            STRING_MALLOC_NEW(temp->seqInsertCode, "");
        } else {
            // read the string from the PyObject, and put into seqInsertCode
            seqString = PyUnicode_AsASCIIString(seqInsertCode);
            if (seqString) {
                temp->seqInsertCode = PyBytes_AS_STRING(seqString);
                temp->seqIsReference = CCPN_TRUE;
            }
        }
    }

    offsetTest = PyDict_GetItemString(apiDict, "relativeOffset");
    if (offsetTest != Py_None) {
        relOffset = PyFloat_AsDouble(PyObject_GetAttrString(offsetItem, "relativeOffset"));
        temp->relativeOffset = relOffset;
    }

    (*headRef) = insertConnected(ptr, temp);

    // cleanup reference counts
    return temp;  // CCPN_TRUE;

    //    seqInsertCode = PyObject_GetAttrString(offsetItem, "seqInsertCode");
    //    seqInsertCode = PyDict_GetItemString(apiDict, "seqCode");

    //    if (PyObject_RichCompareBool(seqInsertCode, Py_None, Py_NE) == 1)
    //    {
    //        continue;
    //        ss = PyBytes_Size(seqInsertCode);

    //        seqString = PyObject_Bytes(seqInsertCode);
    //        if (seqString)
    //        if (PyObject_IsInstance(seqInsertCode, &PyObject_Type))
    //            printf("    array\n");

    //    seqString = PyObject_Str(seqInsertCode);
    //    int seqLen = PyObject_Size(seqString);
    //
    //    int ss = PyLong_AsLong(seqInsertCode);
    //
    //    printf("size %i\n", ss);

    //        PyByteArrayObject *strNone = PyByteArray_FromObject(seqInsertCode);
    //        if (!strNone)
    //            RETURN_OBJ_ERROR("error defining string");

    //        seqLen = PyObject_Size(strNone);

    //        char thisString[seqLen];

    //        const char *thisString2 = PyByteArray_AsString(seqString);
    //        strncpy(thisString, *thisString2, seqLen);

    //        printf("%i \n", PyBytes_Size(strNone));
    //    }

    //    temp->seqInsertCode = PyBytes_AsString(seqInsertCode);
    //    printf(temp->seqInsertCode);

    //    (*headRef) = insertConnected(ptr, temp);
    //
    //    return temp;            // CCPN_TRUE;
}

static void getIndexInList(struct Node *node, PyObject *item, long *index, long *found) {
    if (node) {
        getIndexInList(node->prev, item, index, found);
        (*index)++;
        if (node->object == item) *found = *index;

        getIndexInList(node->next, item, index, found);
    }
}

static void deallocateNodeList(struct Node *node) {
    if (node) {
        deallocateNodeList(node->prev);
        deallocateNodeList(node->next);

        // deallocate node contents and children
        if ((node->seqIsReference == CCPN_FALSE) && (node->seqInsertCode)) free(node->seqInsertCode);
        if (node->prev) free(node->prev);
        if (node->next) free(node->next);
    }
}

static CcpnBool _flaggedForDelete(PyObject *projectDict, PyObject *apiRes) {
    PyObject *isDeleted;
    PyObject *_flagged;
    PyObject *res = PyDict_GetItem(projectDict, apiRes);

    // if -1 residue before selection and 0 residue after selection then works
    // okay

    if (res) {
        isDeleted = (PyObject *)PyObject_GetAttrString(apiRes, "isDeleted");
        if (PyObject_HasAttrString(res, "_flaggedForDelete")) {
            _flagged = (PyObject *)PyObject_GetAttrString(res, "_flaggedForDelete");
            if (isDeleted != Py_False) printf("_flaggedForDelete\n");
        } else
            printf("no flag\n");

        //        if (!isDeleted)
        //            RETURN_OBJ_ERROR("error getting isDeleted");
        //        if (!_flagged)
        //            RETURN_OBJ_ERROR("error getting _flaggedForDelete");
    }

    return CCPN_FALSE;
}

static PyObject *getNmrResidueIndex(PyObject *self, PyObject *args) {
    PyObject *apiNmrChain;
    PyTupleObject *apiNmrResiduesTuple;
    PyObject *nmrResidue;
    PyObject *returnValue;
    char error_msg[1000];
    long index = -1, numOffsets = 0, found = -1, rgSize;
    long ii, jj;
    PyObject *listRes, *mainRes;
    PyObject *apiNmrResidue;
    PyListObject *offsetList;
    PyObject *offsetRes;
    PyObject *resonanceGroupsList;
    PyObject *apiNmrProjectDict;
    PyObject *resonanceGroupDict;
    PyObject *apiNmrProject;
    CcpnBool isConnected;
    PyObject *project;
    PyDictObject *projectDict;

    //    data2Obj = project._data2Obj
    //    data2Obj[wrappedData] = self
    //    self._flaggedForDelete

    // check thart the argument is an nmrResidue
    if (!PyArg_ParseTuple(args, "O", &nmrResidue)) RETURN_OBJ_ERROR("need arguments: nmrResidue");

    // get the apiResonanceGroup
    apiNmrResidue = PyObject_GetAttrString(nmrResidue, "_wrappedData");
    if (!apiNmrResidue) RETURN_OBJ_ERROR("error getting _wrappedData");

    // get the apiNmrChain containing the resonanceGroup
    apiNmrChain = (PyObject *)PyObject_GetAttrString(apiNmrResidue, "nmrChain");
    if (!apiNmrChain) RETURN_OBJ_ERROR("error getting apiNmrChain");

    // get isConnected and serial for the apiNmrChain
    PyObject *apiNmrChainDict = PyObject_GetAttrString(apiNmrChain, "__dict__");
    PyObject *isConnectedObj = PyDict_GetItemString(apiNmrChainDict, "isConnected");
    PyObject *apiNmrChainSerialObj = PyDict_GetItemString(apiNmrChainDict, "serial");

    // get all the resonanceGroups in the local apiNmrChain
    apiNmrResiduesTuple = (PyTupleObject *)PyObject_GetAttrString(apiNmrChain, "mainResonanceGroups");

    // error checking
    if (!apiNmrResiduesTuple) RETURN_OBJ_ERROR("error getting apiNmrResiduesTuple");
    if (!isConnectedObj) RETURN_OBJ_ERROR("error getting isConnected");
    if (!apiNmrChainSerialObj) RETURN_OBJ_ERROR("error getting serial");

    if (isConnectedObj == Py_True)
        isConnected = CCPN_TRUE;
    else
        isConnected = CCPN_FALSE;

    // put the resonanceGroups into a list
    long numRes = PyTuple_GET_SIZE(apiNmrResiduesTuple);
    // PyObject *mainResGroups[numRes];
    PyObject **mainResGroups;
    MALLOC_NEW(mainResGroups, PyObject *, numRes);
    for (ii = 0; ii < numRes; ii++) {
        mainResGroups[ii] = (PyObject *)PyTuple_GET_ITEM(apiNmrResiduesTuple, ii);
    }

    // get the list of all resonanceGroups in the apiNmrProject
    apiNmrProject = PyObject_GetAttrString(apiNmrResidue, "nmrProject");
    apiNmrProjectDict = PyObject_GetAttrString(apiNmrProject, "__dict__");
    resonanceGroupDict = PyDict_GetItemString(apiNmrProjectDict, "resonanceGroups");
    resonanceGroupsList = PyDict_Values(resonanceGroupDict);

    // error checking
    if (!apiNmrProject) RETURN_OBJ_ERROR("error getting apiNmrProject");
    if (!apiNmrProjectDict) RETURN_OBJ_ERROR("error getting apiNmrProjectDict");
    if (!resonanceGroupDict) RETURN_OBJ_ERROR("error getting resonanceGroupDict");
    if (!resonanceGroupsList) RETURN_OBJ_ERROR("error getting resonanceGroupsList");

    // get the V3project
    project = PyObject_GetAttrString(nmrResidue, "project");
    projectDict = (PyDictObject *)PyObject_GetAttrString(project, "_data2Obj");

    // error checking
    if (!project) RETURN_OBJ_ERROR("error getting project");
    if (!projectDict) RETURN_OBJ_ERROR("error getting projectDict");

    // search all resonanceGroups in the project,
    // to find all attached offsetResonanceGroups
    rgSize = PyList_GET_SIZE(resonanceGroupsList);
    //    PyObject *offsetResonanceGroups[rgSize];            //  just make it
    //    full size, but only need some of it PyObject
    //    *offSetMainResonances[rgSize];
    PyObject **offsetResonanceGroups;  //  just make it full size, but only need
                                       //  some of it
    PyObject **offSetMainResonances;
    MALLOC_NEW(offsetResonanceGroups, PyObject *, rgSize);
    MALLOC_NEW(offSetMainResonances, PyObject *, rgSize);

    for (ii = 0; ii < rgSize; ii++) {
        listRes = PyList_GET_ITEM(resonanceGroupsList, ii);
        mainRes = PyObject_GetAttrString(listRes, "mainResonanceGroup");  //  not pointing to the right place?

        for (jj = 0; jj < numRes; jj++)
            if ((mainRes == mainResGroups[jj]) && (mainRes != listRes)) {
                // simple way of keeping res and mainRes together;
                offsetResonanceGroups[numOffsets] = listRes;
                offSetMainResonances[numOffsets] = mainRes;
                numOffsets++;
            }
    }

    struct Node *resonanceList = NULL;
    struct Node *thisNode = NULL;
    struct Node *offsetNode = NULL;

    // insert all resonanceGroups into a linked list for ordering
    for (ii = 0; ii < numRes; ii++) {
        mainRes = PyTuple_GET_ITEM(apiNmrResiduesTuple, ii);
        thisNode = insertConnectedNode(&resonanceList, mainRes, ii, isConnected, CCPN_TRUE);

        // if an offsetResonance, then uses the index of the mainResonance
        for (jj = 0; jj < numOffsets; jj++)
            if (offSetMainResonances[jj] == mainRes)
                offsetNode =
                    insertConnectedNode(&resonanceList, offsetResonanceGroups[jj], thisNode->index, isConnected, CCPN_FALSE);

        //        // this is the SLOW line - and has been replaced by the quicker
        //        accessing through apiNmrChain.__dict__['resonanceGroups']
        //        offsetList = (PyListObject *) PyObject_GetAttrString(listRes,
        //        "offsetResonanceGroups");
        //
        //        numOffsets = PyList_GET_SIZE(offsetList);
        //        for (long jj=0; jj < numOffsets; jj++)
        //        {
        //            offsetRes = (PyObject *) PyList_GET_ITEM(offsetList, jj);
        //            insertConnectedNode(&resonanceList, offsetRes, ii);
        //        }
    }

    // get the index of the current nmrResidue in the list
    getIndexInList(resonanceList, apiNmrResidue, &index, &found);

    // clean up allocated memory
    deallocateNodeList(resonanceList);
    if (resonanceList) free(resonanceList);

    FREE(offsetResonanceGroups, PyObject *);
    FREE(offSetMainResonances, PyObject *);
    FREE(mainResGroups, PyObject *);

    // return index
    returnValue = PyLong_FromLong(found);
    return returnValue;
}

static PyObject *testReturnList(PyObject *self, PyObject *args) {
    PyArrayObject *data_obj, *levels_obj, *indices, *vertices, *colours;
    PyObject *returnObject;

    // create a new list
    returnObject = newList();

    // append an item to the list
    appendFloatList(returnObject, 126.45);
    appendFloatList(returnObject, 54.27);
    appendFloatList(returnObject, -2.6);

    return returnObject;
}

static char testReturnList_doc[] = "Return a list from a python c routine.";
static char getNmrResidueIndex_doc[] = "Return the index of an nmrResidue in a chain";

static struct PyMethodDef Clibrary_type_methods[] = {
    {"testReturnList", (PyCFunction)testReturnList, METH_VARARGS, testReturnList_doc},
    {"getNmrResidueIndex", (PyCFunction)getNmrResidueIndex, METH_VARARGS, getNmrResidueIndex_doc},
    {NULL, NULL, 0, NULL}};

struct module_state {
    PyObject *error;
};

static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT, "Clibrary", NULL, sizeof(struct module_state), Clibrary_type_methods, NULL, NULL, NULL, NULL};

PyMODINIT_FUNC PyInit_Clibrary(void) {
    PyObject *module;

#ifdef WIN32
    Clibrary.ob_type = &PyType_Type;
#endif
    /* create the module and add the functions */
    module = PyModule_Create(&moduledef);

    import_array(); /* needed for numpy, otherwise it crashes */

    /* create exception object and add to module */
    ErrorObject = PyErr_NewException("ClibraryPy.error", NULL, NULL);
    Py_INCREF(ErrorObject);

    PyModule_AddObject(module, "error", ErrorObject);

    if (module == NULL) return NULL;

    struct module_state *st = (struct module_state *)PyModule_GetState(module);

    st->error = PyErr_NewException("ClibraryPy.error", NULL, NULL);
    if (st->error == NULL) {
        Py_DECREF(module);
        return NULL;
    }

    /* check for errors */
    if (PyErr_Occurred()) Py_FatalError("can't initialize module ClibraryPy");

    return module;
}
