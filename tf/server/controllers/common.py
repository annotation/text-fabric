import re

msgLinePat = '^( *[0-9]+) (.*)$'
msgLineRe = re.compile(msgLinePat)


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
      commonLine = (1, nResults)
    else:
      commonLine = (1, position, nResults)
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

    lines.append(commonLine)

  html = '\n'.join(
      '<div class="pline">' +
      ' '.join(
          f'<a href="#" class="pnav {" focus" if position == p else ""}">{p}</a>'
          for p in line
      )
      +
      '</div>'
      for line in reversed(lines)
  )
  return html


def shapeMessages(messages):
  messages = messages.split('\n')
  html = []
  for msg in messages:
    match = msgLineRe.match(msg)
    if match:
      continue
    html.append(f'''
      <div class="eline">
        {msg}
      </div>
    ''')
  return ''.join(html)
