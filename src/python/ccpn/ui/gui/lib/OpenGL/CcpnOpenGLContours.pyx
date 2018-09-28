"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = ""
__credits__ = ""
__licence__ = ("")
__reference__ = ("")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as pynp

cdef unsigned int val(int ll, int numVert, int index):
    return ((((ll + 1) // 2) % numVert) + index)

def _addContoursToGLList(contourData, glList=None, colour=None):
    """ contourData is list of [NumPy array with ndim = 1 and size = twice number of points]
    """
    cdef int index, ll, cc
    cdef int thisNumVertices

    cdef unsigned int[:] indicesVIEW = glList.indices
    cdef float[:] verticesVIEW = glList.vertices
    cdef float[:] colorsVIEW = glList.colors

    cdef int indexLen = 0
    cdef int vertexLen = 0
    cdef int colorLen = 0

    cdef unsigned int[:] newIndicesVIEW
    cdef float[:] newColorsVIEW

    for contour in contourData:
        glList.vertices = pynp.append(glList.vertices, contour)

    # for contour in contourData:
    #     index = glList.numVertices
    #     thisNumVertices = len(contour) // 2
    #
    #     newIndicesVIEW = pynp.empty(2*thisNumVertices, dtype=pynp.uint32)
    #     newColorsVIEW = pynp.empty(4*thisNumVertices, dtype=pynp.float32)
    #
    #     for ll in range(2 * thisNumVertices):
    #         newIndicesVIEW[ll] = val(ll, thisNumVertices, index)
    #
    #     for ll in range(0, 4*thisNumVertices, 4):
    #         for cc in range(4):
    #             newColorsVIEW[ll+cc] = colour[cc]
    #
    #     indicesVIEW = pynp.append(indicesVIEW, newIndicesVIEW)
    #     colorsVIEW = pynp.append(colorsVIEW, newColorsVIEW)

    # for contour in contourData:
    #     index = glList.numVertices
    #     thisNumVertices = len(contour) // 2
    #     verticesVIEW = np.append(verticesVIEW, contour)
    #
    #     for ll in range(2 * thisNumVertices):
    #         newIndicesVIEW.append((((ll + 1) // 2) % thisNumVertices) + index)
    #         newColorsVIEW.append(colour)
    #
    #     indicesVIEW = np.append(indicesVIEW, newIndicesVIEW)
    #     colorsVIEW = np.append(colorsVIEW, newColorsVIEW)

        # newIndices = list([(((ll + 1) // 2) % thisNumVertices) + index for ll in range(2 * thisNumVertices)])

        # glList.indices = np.append(glList.indices, newIndices)
        # glList.colors = np.append(glList.colors, colour * thisNumVertices)

        glList.numVertices = len(verticesVIEW) // 2
        print('>>>glList.numVertices')

    glList.colors = pynp.array(colorsVIEW, dtype=pynp.float32)
    glList.indices = pynp.array(indicesVIEW, dtype=pynp.uint32)
