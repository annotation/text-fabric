import os
import collections

from ..fabric import Fabric
from ..core.data import WARP
from ..core.timestamp import Timestamp
from ..core.helpers import itemize

OTYPE = WARP[0]
OSLOTS = WARP[1]
OTEXT = WARP[2]

GENERATED = set('''
    writtenBy
    dateWritten
    version
'''.strip().split())

TM = Timestamp()
indent = TM.indent
info = TM.info
error = TM.error


def add(
    location,
    targetLocation,
    nodeTypes=None,
    nodeFeatures=None,
    edgeFeatures=None,
):
  TF = Fabric(locations=location, silent=True)
  api = TF.load(list(nodeFeatures or []) + list(edgeFeatures or []), silent=True)
  if not api:
    error(f'Cannot load features of TF set in {location}', tm=False)
    return False

  F = api.F
  slotType = F.otype.slotType
  origMaxNode = F.otype.maxNode
  origTypes = set(F.otype.all)

  def writeTf():
    TF = Fabric(locations=targetLocation)
    TF.save(metaData=metaData, nodeFeatures=nodeFeatures, edgeFeatures=edgeFeatures)
    return True

  def process():
    indent(level=0, reset=True)
    info('inspect metadata ...')
    if not getMetas():
      return False
    info('determine nodetypes ...')
    if not getNtypes():
      return False
    info('compute offsets ...')
    if not getOffsets():
      return False
    info('remap features ...')
    if not remapFeatures():
      return False
    info('merge types ...')
    if not thinTypes():
      return False
    info('write TF data ...')
    if not writeTf():
      return False
    info('done')
    return True

  return process()
