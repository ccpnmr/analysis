
def isFastaFormat(inputFile):

  if inputFile.split('.')[-1] == 'fasta':
    return True
  else:
    print("isFastaFormat else")
    with open(inputFile, 'r') as f:
      try:
        if f.readlines()[0].startswith('>'):
          return True
      except:
        pass

  return False


def parseFastaFile(inputFile):

  sequences = []
  with open(inputFile, 'r') as f:
    chains = []
    lines = [line.strip() for line in f.readlines()][:-1]
    for line in lines:
      if line and line[0] == '>':
        chains.append(lines.index(line))
  for chain in chains :
    name = lines[chain].split()[0]
    index = chains.index(chain)
    if not index == len(chains)-1:
      endIndex = chains[index+1]
      sequences.append([name, ''.join(lines[chain+1:endIndex])])
    else:
      sequences.append([name, ''.join(lines[chain+1:])])

  return sequences
