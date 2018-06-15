from tf.extra.cunei import (
    ATF_TYPES,
    URL_FORMAT,
    CSS,
    Atf,
)

C_CSS = CSS

BATCH = 10


def _outLink(text, href, title=None):
  titleAtt = '' if title is None else f' title="{title}"'
  return f'<a target="_blank" href="{href}"{titleAtt}>{text}</a>'


class Cunei(Atf):
  def __init__(self, api):
    super().__init__(api=api)
    self.api = api

  def tabletLink(self, t, text=None):
    api = self.api
    L = api.L
    F = api.F
    if type(t) is str:
      pNum = t
    else:
      if F.otype.v(t) == 'tablet':
        n = t
      else:
        ns = L.u(t, otype='tablet')
        n = ns[0] if len(ns) else None
      pNum = None if n is None else F.catalogId.v(n)

    title = 'to CDLI main page for this tablet'
    linkText = pNum if text is None else text
    if pNum is None:
      return linkText

    url = URL_FORMAT['tablet']['main'].format(pNum)

    return _outLink(linkText, url, title=title)

  def plain(
      self,
      n,
      linked=True,
      withNodes=False,
      lineNumbers=False,
  ):
    api = self.api
    F = api.F

    nType = F.otype.v(n)
    html = ''
    nodeRep = f' <span class="nd">{n}</span> ' if withNodes else ''

    if nType in ATF_TYPES:
      isSign = nType == 'sign'
      isQuad = nType == 'quad'
      rep = (
          self.atfFromSign(n) if isSign else self.atfFromQuad(n)
          if isQuad else self.atfFromCluster(n)
      )
      if linked:
        rep = self.tabletLink(n, text=rep)
      html = f'{rep}{nodeRep}'
    elif nType == 'comment':
      rep = F.type.v(n)
      if linked:
        rep = self.tabletLink(n, text=rep)
      html = f'{rep}{nodeRep}: {F.text.v(n)}'
    elif nType == 'line' or nType == 'case':
      rep = f'{nType} {F.number.v(n)}'
      if linked:
        rep = self.tabletLink(n, text=rep)
      theLine = ''
      if lineNumbers:
        if F.terminal.v(n):
          theLine = f' @{F.srcLnNum.v(n)} '
      html = f'{rep}{nodeRep}{theLine}'
    elif nType == 'column':
      rep = f'{nType} {F.number.v(n)}'
      if linked:
        rep = self.tabletLink(n, text=rep)
      theLine = ''
      if lineNumbers:
        theLine = f' @{F.srcLnNum.v(n)} '
      html = f'{rep}{nodeRep}{theLine}'
    elif nType == 'face':
      rep = f'{nType} {F.type.v(n)}'
      if linked:
        rep = self.tabletLink(n, text=rep)
      theLine = ''
      if lineNumbers:
        theLine = f' @{F.srcLnNum.v(n)} '
      html = f'{rep}{nodeRep}{theLine}'
    elif nType == 'tablet':
      rep = f'{nType} {F.catalogId.v(n)}'
      if linked:
        rep = self.tabletLink(n, text=rep)
      theLine = ''
      if lineNumbers:
        theLine = f' @{F.srcLnNum.v(n)} '
      html = f'{rep}{nodeRep}{theLine}'

    return html

  def plainTuple(
      self,
      ns,
      seqNumber,
      position,
      linked=1,
      withNodes=False,
      lineNumbers=False,
      alone=False,
  ):
    api = self.api
    F = api.F
    current = ' class="focus"' if seqNumber == position else ''
    html = ''
    if alone:
      html = f'''
<table>
  <tr{current}>
    <th>n</th><th>{"</th><th>".join(F.otype.v(n) for n in ns)}</th>
  </tr>
'''
    html += (
        f'''
  <tr{current}>
    <td>{seqNumber}</td>
'''
        +
        ''.join(
            f'''<td>{self.plain(
                        n,
                        linked=i == linked - 1,
                        withNodes=withNodes,
                        lineNumbers=lineNumbers,
                      ).replace("|", "&#124;")
                    }
                </td>
            '''
            for (i, n) in enumerate(ns)
        )
        +
        '</tr>'
    )
    if alone:
      html += '</table>'
    return html

  def table(
      self,
      results,
      start=1,
      position=1,
      linked=1,
      withNodes=False,
      lineNumbers=False,
  ):
    if len(results) == 0:
      return 'no results'

    api = self.api
    F = api.F

    print('generate table')
    firstResult = results[0]
    html = (
        f'''
<table>
  <tr>
    <th>n</th><th>{"</th><th>".join(F.otype.v(n) for n in firstResult)}</th>
  </tr>
'''
        +
        '\n'.join(
            self.plainTuple(
                ns,
                i + start,
                position,
                linked=linked,
                withNodes=withNodes,
                lineNumbers=lineNumbers,
            )
            for (i, ns) in enumerate(results)
        )
        +
        '<table>'
    )
    print('table generated')
    return html


def compose(results, start, position, api):
  CN = Cunei(api)
  return CN.table(results, start=start, position=position, linked=1, withNodes=False)
  # return f'{len(api.nodes)} nodes in {len(results)} results'
