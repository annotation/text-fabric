from tf.fabric import Fabric

TF = Fabric('tf', '')

maxSlot = 10
halfSlot = int(round(maxSlot / 2))

otype = {i: 'sign' for i in range(1, maxSlot + 1)}
oslots = {}

name = {i: chr(i + ord('a') - 1) for i in range(1, maxSlot + 1)}
number = {i: i for i in range(1, int(round(maxSlot / 2)))}
nameS = {
    1: 'special',
    2: 'ss-special-ss',
    3: 'ss-peculiar-ss',
}
nameP = {
    maxSlot + 1: 'special',
    maxSlot + 2: 'pp-special-pp',
    maxSlot + 3: 'pp-peculiar-pp',
}

p = 0


# GENERATE NODES OF TYPE PART

# create a part with that name and linked to those slots

def addPart(nm, signs):
  mySlots = set(s for s in signs if 1 <= s <= maxSlot)
  if not mySlots:
    return

  global p
  p += 1
  node = maxSlot + p
  otype[node] = 'part'
  oslots[node] = mySlots
  name[node] = nm
  if p < maxSlot:
    number[node] = p


# create singlet parts, doublets, triplets, etc
# nm is a prefix for the name of the parts
# kind: 1 for singlets, 2 for doublets, etc.

def addLet(nm, kind):
  for i in range(0, maxSlot):
    base = kind * i
    addPart(f'{nm}{i + 1}', range(base + 1, base + kind + 1))


# ADD ALL PARTS

addLet('s', 1)
addLet('ss', 1)
addLet('d', 2)
addLet('t', 3)
addLet('q', 4)
addLet('u', 5)

addPart('lower_a', list(range(1, halfSlot + 1)) + [halfSlot + 1, halfSlot + 3])
addPart('lower_b', list(range(1, halfSlot + 1)) + [halfSlot + 2, halfSlot + 4])
addPart('lower_c', list(range(1, halfSlot + 1)) + [halfSlot + 3, halfSlot + 5])
addPart('upper_a', [halfSlot - 3, halfSlot - 1] + list(range(halfSlot + 1, maxSlot + 1)))
addPart('upper_b', [halfSlot - 4, halfSlot - 2] + list(range(halfSlot + 1, maxSlot + 1)))
addPart('upper_c', [halfSlot - 5, halfSlot - 3] + list(range(halfSlot + 1, maxSlot + 1)))
addPart('lower', range(1, halfSlot + 1))
addPart('upper', range(halfSlot + 1, maxSlot + 1))
addPart('odd', range(1, maxSlot + 1, 2))
addPart('even', range(2, maxSlot + 1, 2))
addPart('big', [3, 5, 6, 7, 9])
addPart('small1', [3, 5, 6])
addPart('small2', [5, 6])
addPart('small3', [5, 6, 7])
addPart('small4', [5, 6, 7, 9])
addPart('small5', [5, 6, 7, 8])
addPart('small6', [4, 6, 7, 9])
addPart('small7', [5, 6, 7, 10])
addPart('small8', [2, 6, 7, 9])
addPart('john', [4, 6, 7, 9])
addPart('mary', [4, 6, 7, 9])
addPart('fred', [4, 9])
addPart('jim', [1, maxSlot])
addPart('jim1', [2, maxSlot - 1])
addPart('jim2', [3, maxSlot - 2])
addPart('jim3', [4, maxSlot - 3])
addPart('tim', [5, 6])
addPart('tom', [7, 8])
addPart('tom1n', [8, 9])
addPart('tom1p', [6, 7])
addPart('tom2n', [9, 10])
addPart('tom2p', [5, 6])
addPart('timb', [1, 2])
addPart('tomb', [3, 4])
addPart('tomb1n', [4, 5])
addPart('tomb1p', [2, 3])
addPart('tomb2n', [5, 6])
addPart('tomb2p', [1, 2])
addPart('time', [9, 10])
addPart('tome', [7, 8])
addPart('tome1n', [8, 9])
addPart('tome1p', [6, 7])
addPart('tome2n', [9, 10])
addPart('tome2p', [5, 6])
addPart('all', range(1, maxSlot + 1))

# COLLECT THE FEATURES

nodeFeatures = {
    'otype': otype,
    'number': number,
    'name': name,
    'namesign': nameS,
    'namepart': nameP,
}
edgeFeatures = {
    'oslots': oslots,
}

metaData = {
    '': {
        'name': 'testset',
    },
    'otype': {
        'valueType': 'str',
    },
    'oslots': {
        'valueType': 'str',
    },
    'number': {
        'valueType': 'int',
    },
    'name': {
        'valueType': 'str',
    },
    'namesign': {
        'valueType': 'str',
    },
    'namepart': {
        'valueType': 'str',
    },
}

# SAVE THE CORPUS AS TF

TF.save(nodeFeatures=nodeFeatures, edgeFeatures=edgeFeatures, metaData=metaData)
