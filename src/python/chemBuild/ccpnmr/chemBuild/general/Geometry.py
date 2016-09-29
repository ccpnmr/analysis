def vectorsSubtract(v1, v2):
  """ Subtract vectors v1 and v2.
  """

  n = len(v1)
  if n != len(v2):
    raise Exception('length of v1 != length of v2')

  v = n * [0]
  for i in range(n):
    v[i] = v1[i] - v2[i]

  return v

def dotProduct(v1, v2):
  """ The inner product between v1 and v2.
  """

  n = len(v1)
  if (n != len(v2)):
    raise Exception('v1 and v2 must be same length')

  d = 0
  for i in range(n):
    d = d + v1[i] * v2[i]

  return d

def crossProduct(v1, v2):
  """ Returns the cross product of v1 and v2.
  Both must be 3-dimensional vectors.
  """

  if (len(v1) != 3 or len(v2) != 3):
    raise Exception('v1 and v2 must be of length 3')

  return [ v1[1]*v2[2]-v1[2]*v2[1], v1[2]*v2[0]-v1[0]*v2[2], v1[0]*v2[1]-v1[1]*v2[0] ]
