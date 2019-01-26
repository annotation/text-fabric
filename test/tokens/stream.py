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
# ('R', node)                  : resume the specified non slot node
# ('T', node)                  : terminate specified node
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
        yield('T', curLine)
        yield ('N')
        yield ('F', dict(gap=1))
        word = word[1:]
      elif word.endswith(']'):
        yield('R', curLine)
        yield ('N')
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
  print('oslots')
  for (n, slots) in sorted(oslots.items()):
    print(f'{n} => {sorted(slots)}')

  print('\nfeatures\n')

  for (f, fData) in sorted(nodeFeatures.items()):
    print(f)
    for (n, value) in fData.items():
      print(f'\t{n} => {value}')


#######################################################################
#                                                                     #
# CALL THE CONVERSION  AND SHOW OUTPUT                                #
#                                                                     #
#######################################################################


(oslots, nodeFeatures) = weave('word', simpleTokens())

show(oslots, nodeFeatures)


#######################################################################
#                                                                     #
# THE OUTPUT                                                          #
#                                                                     #
#######################################################################

if False:
  '''
oslots
('line', 1) => [1, 2, 3]
('line', 2) => [4, 5, 6]
('line', 3) => [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
('line', 4) => [21, 22, 23, 24, 25, 26, 27]
('line', 5) => [28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38]
('line', 6) => [39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51]
('line', 7) => [52, 53, 54, 55]
('section', 1) => [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55]
('sentence', 1) => [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]
('sentence', 2) => [28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55]

features

letters
	('word', 1) => Everything
	('word', 2) => about
	('word', 3) => us
	('word', 4) => everything
	('word', 5) => around
	('word', 6) => us
	('word', 7) => everything
	('word', 8) => we
	('word', 9) => know
	('word', 10) => and
	('word', 11) => can
	('word', 12) => know
	('word', 13) => of
	('word', 14) => is
	('word', 15) => composed
	('word', 16) => ultimately
	('word', 17) => of
	('word', 18) => patterns
	('word', 19) => of
	('word', 20) => nothing
	('word', 21) => that’s
	('word', 22) => the
	('word', 23) => bottom
	('word', 24) => line
	('word', 25) => the
	('word', 26) => final
	('word', 27) => truth
	('word', 28) => So
	('word', 29) => where
	('word', 30) => we
	('word', 31) => find
	('word', 32) => we
	('word', 33) => have
	('word', 34) => any
	('word', 35) => control
	('word', 36) => over
	('word', 37) => those
	('word', 38) => patterns
	('word', 39) => why
	('word', 40) => not
	('word', 41) => make
	('word', 42) => the
	('word', 43) => most
	('word', 44) => elegant
	('word', 45) => ones
	('word', 46) => the
	('word', 47) => most
	('word', 48) => enjoyable
	('word', 49) => and
	('word', 50) => good
	('word', 51) => ones
	('word', 52) => in
	('word', 53) => our
	('word', 54) => own
	('word', 55) => terms
number
	('sentence', 1) => 1
	('line', 1) => 1
	('line', 2) => 2
	('line', 3) => 3
	('line', 4) => 4
	('sentence', 2) => 2
	('line', 5) => 1
	('line', 6) => 2
	('line', 7) => 3
punc
	('word', 3) => ,
	('word', 6) => ,
	('word', 20) => ;
	('word', 24) => ,
	('word', 27) => .
	('word', 38) => ,
	('word', 45) => ,
	('word', 51) => ,
	('word', 55) => ?
terminator
	('line', 1) => ,
	('line', 2) => ,
	('line', 3) => ;
	('line', 4) => .
	('line', 5) => ,
	('line', 6) => ,
	('line', 7) => ?
title
	('section', 1) => Consider Phlebas
'''

