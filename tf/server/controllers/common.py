def _coarsify(n, spread):
  nAbs = int(round(abs(n) / spread)) * spread
  return nAbs if n >= 0 else -nAbs


def pageLinks(nResults, position, spread=10):
  if spread <= 1:
    spread = 1
  elif nResults == 0:
    lines = []
  elif nResults == 1:
    lines = [(1,)]
  elif nResults == 2:
    lines = [(1, 2)]
  else:
    if position == 1 or position == nResults:
      lastLine = (1, nResults)
    else:
      lastLine = (1, position, nResults)

    lines = []
    factor = 1
    while factor <= nResults:
      curSpread = factor * spread
      first = _coarsify(position - curSpread, curSpread)
      last = _coarsify(position + curSpread, curSpread)

      left = tuple(n for n in range(first, last, factor) if n > 0 and n < position)
      right = tuple(n for n in range(first, last, factor) if n > position and n <= nResults)

      both = tuple(n for n in left + (position,) + right if n > 0 and n <= nResults)

      if len(both) > 1:
        lines.append(both)

      factor *= spread

    lines.append(lastLine)

  html = '\n'.join(
      '<p class="pline">' +
      ' '.join(
          f'<a href="#" class="pnav {" focus" if position == p else ""}">{p}</a>'
          for p in line
      )
      +
      '</p>'
      for line in lines
  )
  return html
