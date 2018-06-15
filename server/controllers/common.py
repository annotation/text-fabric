def pageLinks(nResults, position, spread=10):
  if spread <= 1:
    spread = 1
  if nResults == 0:
    return []
  if nResults == 1:
    return [(1,)]
  if nResults == 2:
    return [(1, 2)]
  if position == 1 or position == nResults:
    firstLine = (1, nResults)
  else:
    firstLine = (1, position, nResults)

  lines = [firstLine]
  factor = 1
  while factor <= nResults:
    curSpread = factor * spread

    right = tuple(range(position, position + curSpread + 1, factor))
    left = tuple(reversed(range(position - factor, position - curSpread - 1, -factor)))

    both = tuple(n for n in left + right if n > 0 and n <= nResults)

    if len(both) > 1:
      lines.append(both)

    factor *= spread
  html = '\n'.join(
      '<p class="pline">' +
      ' '.join(
          f'<a href="#" class="pnav">{p}</a>'
          for p in line
      )
      +
      '</p>'
      for line in lines
  )
  return html
