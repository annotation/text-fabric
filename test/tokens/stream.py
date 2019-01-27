import collections
import re

# The input text

text = '''
# Consider Phlebas

Everything about us,
everything around us,
everything we know [and can know of] is composed ultimately of patterns of nothing;
that’s the bottom line, the final truth.

So where we find we have any control over those patterns,
why not make the most elegant ones, the most enjoyable and good ones,
in our own terms?
'''

# The TF will have a node type for section
#
# Here we have one section, with title Consider Phlebas
#
# The sentences are the parts separated by blank lines: we have 2 sentences.
# We will give each sentence a number within its section.
#
# The sentences are divided into lines.
# We will give each line a number within its sentence.
# Words within [ ] will not be part of the line, the line has a gap.
# The gapped words will have a feature gqp=1
#
# Lines will be split into words, the slot nodes.
# We split the word from its punctuation, and add that in a punc feature

# The next function is the converter, that the user has to write

#######################################################################
#                                                                     #
# CUSTOM CONVERTER FROM TEXT TO TF                                    #
#                                                                     #
#######################################################################

# You have to yield tokens:
#
# node = yield ('N',)          : make new slot node
# node = ('N', nodeType)       : make a new non slot node
# ('T',)                       : terminate current node
# ('T', node)                  : terminate specified node
# ('R', node)                  : resume the specified non slot node
# ('R', node)                  : link current context nodes to the specified slot node
# ('F', featureDict)           : add features to current node
# ('F', node, featureDict)     : add features to specified node
# ('E', nodeFrom, edgeFrom, featureDict) : add features to specified edge fron nodeFrom to nodeTo
#
# after node = yield ('N', nodeType) all slot nodes that are yielded
# will be linked to node, until a ('T', node) is yielded.
# If needed, you can resume ('R', node) this node again, after which new slot nodes
# continue to be linked to this node.


def simpleTokens():
  lineCounter = 0
  sentenceCounter = 0
  curSentence = None
  curSection = None

  wordRe = re.compile(r'^(.*?)([^A-Za-z0-9]*)$')

  for line in text.strip().split('\n'):
    line = line.rstrip()
    if not line:
      yield ('T', curSentence)
      sentenceCounter += 1
      lineCounter = 0
      curSentence = yield ('N', 'sentence')
      yield ('F', dict(number=sentenceCounter))
      continue

    if line.startswith('# '):
      yield ('T', curSection)
      title = line[2:]
      curSection = yield ('N', 'section')
      sentenceCounter = 0
      lineCounter = 0
      yield ('F', dict(title=title))
      continue

    curLine = yield ('N', 'line')
    lineCounter += 1
    yield ('F', dict(terminator=line[-1], number=lineCounter))
    gap = False
    for word in line.split():
      if word.startswith('['):
        gap = True
        yield ('T', curLine)
        yield ('N')
        yield ('F', dict(gap=1))
        word = word[1:]
      elif word.endswith(']'):
        yield ('N')
        yield ('R', curLine)
        yield ('F', dict(gap=1))
        gap = False
        word = word[0:-1]
      else:
        yield ('N')
        if gap:
          yield ('F', dict(gap=1))

      (letters, punc) = wordRe.findall(word)[0]
      yield ('F', dict(letters=letters))
      if punc:
        yield ('F', dict(punc=punc))
    yield ('T', curLine)


#######################################################################
#                                                                     #
# TF FUNCTION TO MAKE THE CUSTOM COVERTER WORK                        #
#                                                                     #
#######################################################################

def weave(slotType, tokens):
  curSeq = collections.Counter()
  curEmbedders = set()
  curNode = None
  oslots = collections.defaultdict(set)
  nodeFeatures = {}

  i = 0
  (tType, *tInfo) = tokens.send(None)

  try:
    while True:
      i += 1

      if tType == 'N':
        nType = tInfo[0] if tInfo else slotType
        curSeq[nType] += 1
        seq = curSeq[nType]
        if tInfo:
          curEmbedders.add((nType, seq))
        else:
          for eNode in curEmbedders:
            oslots[eNode].add(seq)
        curNode = (nType, seq)

      elif tType == 'F':
        features = tInfo[-1]
        node = tInfo[0] if len(tInfo) > 1 else curNode
        for (k, v) in features.items():
          nodeFeatures.setdefault(k, {})[node] = v

      elif tType == 'T':
        node = tInfo[0] if len(tInfo) > 0 else curNode
        if node is not None:
          curEmbedders.discard(node)

      elif tType == 'R':
        node = tInfo[0]
        if node[0] != slotType:
          curEmbedders.add(node)

      if tType == 'N':
        (tType, *tInfo) = tokens.send((nType, seq))
      else:
        (tType, *tInfo) = next(tokens)

  except StopIteration:
    pass

  return (oslots, nodeFeatures)


#######################################################################
#                                                                     #
# INSPECTION OF PROTO RESULTS                                         #
#                                                                     #
#######################################################################


def show(oslots, nodeFeatures):
  with open('prototf.txt', 'w') as fh:
    fh.write('oslots\n')
    for (n, slots) in sorted(oslots.items()):
      fh.write(f'{n} => {sorted(slots)}\n')

    fh.write('\nfeatures\n\n')

    for (f, fData) in sorted(nodeFeatures.items()):
      fh.write(f'{f}\n')
      for (n, value) in fData.items():
        fh.write(f'\t{n} => {value}\n')


#######################################################################
#                                                                     #
# CALL THE CONVERSION  AND SHOW OUTPUT                                #
#                                                                     #
#######################################################################


(oslots, nodeFeatures) = weave('word', simpleTokens())

show(oslots, nodeFeatures)
