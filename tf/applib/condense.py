def condense(api, tuples, condenseType, multiple=False):
  F = api.F
  E = api.E
  L = api.L
  fOtype = F.otype.v
  sortNodes = api.sortNodes
  otypeRank = api.otypeRank
  maxSlot = F.otype.maxSlot
  eoslots = E.oslots.data

  slotType = F.otype.slotType
  condenseRank = otypeRank[condenseType]

  containers = {}

  if not multiple:
    tuples = (tuples, )
  for tup in tuples:
    for n in tup:
      nType = fOtype(n)
      if nType == condenseType:
        containers.setdefault(n, set())
      elif nType == slotType:
        up = L.u(n, otype=condenseType)
        if up:
          containers.setdefault(up[0], set()).add(n)
      elif otypeRank[nType] < condenseRank:
        slots = eoslots[n - maxSlot - 1]
        first = slots[0]
        last = slots[-1]
        firstUp = L.u(first, otype=condenseType)
        lastUp = L.u(last, otype=condenseType)
        allUps = set()
        if firstUp:
          allUps.add(firstUp[0])
        if lastUp:
          allUps.add(lastUp[0])
        for up in allUps:
          containers.setdefault(up, set()).add(n)
      else:
        pass
        # containers.setdefault(n, set())
  return tuple((c, ) + tuple(containers[c]) for c in sortNodes(containers))


def condenseSet(api, tuples, condenseType, multiple=False):
  F = api.F
  E = api.E
  L = api.L
  fOtype = F.otype.v
  sortNodes = api.sortNodes
  otypeRank = api.otypeRank
  maxSlot = F.otype.maxSlot
  eoslots = E.oslots.data

  slotType = F.otype.slotType
  condenseRank = otypeRank[condenseType]

  containers = set()

  if not multiple:
    tuples = (tuples, )
  for tup in tuples:
    for n in tup:
      nType = fOtype(n)
      if nType == condenseType:
        containers.add(n)
      elif nType == slotType:
        up = L.u(n, otype=condenseType)
        if up:
          containers.add(up[0])
      elif otypeRank[nType] < condenseRank:
        slots = eoslots[n - maxSlot - 1]
        first = slots[0]
        last = slots[-1]
        firstUp = L.u(first, otype=condenseType)
        lastUp = L.u(last, otype=condenseType)
        if firstUp:
          containers.add(firstUp[0])
        if lastUp:
          containers.add(lastUp[0])
      else:
        containers.add(n)
      # we skip nodes with a higher rank than that of the container
  return sortNodes(containers)
