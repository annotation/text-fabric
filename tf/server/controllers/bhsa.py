def compose(results, context):
  return 'Isaiah'


def shbLink(api, n, text=None, asString=False):
  L = api.L
  T = api.T
  F = api.F
  version = self.version
  nType = F.otype.v(n)
  if nType == 'lex':
    lex = F.lex.v(n)
    lan = F.language.v(n)
    lexId = '{}{}'.format(
        '1' if lan == 'Hebrew' else '2',
        lex.replace('>', 'A').replace('<', 'O').replace('[', 'v').replace('/',
                                                                          'n').replace('=', 'i'),
    )
    href = SHEBANQ_LEX.format(
        version=version,
        lid=lexId,
    )
    title = 'show this lexeme in SHEBANQ'
    if text is None:
      text = F.voc_lex_utf8.v(n)
    result = _outLink(text, href, title=title)
    if asString:
      return result
    display(HTML(result))
    return

  (bookE, chapter, verse) = T.sectionFromNode(n)
  bookNode = n if nType == 'book' else L.u(n, otype='book')[0]
  book = F.book.v(bookNode)
  passageText = (
      bookE if nType == 'book' else '{} {}'.format(bookE, chapter)
      if nType == 'chapter' else '{} {}:{}{}'.format(bookE, chapter, verse, F.label.v(n))
      if nType == 'half_verse' else '{} {}:{}'.format(bookE, chapter, verse)
  )
  href = SHEBANQ.format(
      version=version,
      book=book,
      chapter=chapter,
      verse=verse,
  )
  if text is None:
    text = passageText
    title = 'show this passage in SHEBANQ'
  else:
    title = passageText
  result = _outLink(text, href, title=title)
  if asString:
    return result
  display(HTML(result))

def plain(
    api,
    n,
    linked=True,
    withNodes=False,
    asString=False,
):
  L = api.L
  T = api.T
  F = api.F

  nType = F.otype.v(n)
  markdown = ''
  nodeRep = f' *{n}* ' if withNodes else ''

  if nType == 'word':
    rep = T.text([n])
    if linked:
      rep = self.shbLink(n, text=rep, asString=True)
  elif nType in SECTION:
    fmt = ('{}' if nType == 'book' else '{} {}' if nType == 'chapter' else '{} {}:{}')
    rep = fmt.format(*T.sectionFromNode(n))
    if nType == 'half_verse':
      rep += F.label.v(n)
    if linked:
      rep = self.shbLink(n, text=rep, asString=True)
  elif nType == 'lex':
    rep = F.voc_lex_utf8.v(n)
    if linked:
      rep = self.shbLink(n, text=rep, asString=True)
  else:
    rep = T.text(L.d(n, otype='word'))
    if linked:
      rep = self.shbLink(n, text=rep, asString=True)

  markdown = f'{rep}{nodeRep}'

  if asString:
    return markdown
  _dm((markdown))

def plainTuple(
    api,
    ns,
    seqNumber,
    linked=1,
    withNodes=False,
    asString=False,
):
  markdown = [str(seqNumber)]
  for (i, n) in enumerate(ns):
    markdown.append(plain(
        api,
        n,
        linked=i == linked - 1,
        withNodes=withNodes,
        asString=True,
    ))
  if asString:
    return ' | '.join(markdown)
  _dm(' , '.join(markdown))


def table(
    api,
    results,
    start=None,
    end=None,
    linked=1,
    withNodes=False,
    asString=False,
):
  F = api.F

  collected = []
  if start is None:
    start = 1
  i = -1
  rest = 0
  if not hasattr(results, '__len__'):
    if end is None or end - start + 1 > LIMIT_SHOW:
      end = start - 1 + LIMIT_SHOW
    for result in results:
      i += 1
      if i < start - 1:
        continue
      if i >= end:
        break
      collected.append((i + 1, result))
  else:
    typeResults = type(results)
    if typeResults is set or typeResults is frozenset:
      results = sorted(results)
    if end is None or end > len(results):
      end = len(results)
    rest = 0
    if end - (start - 1) > LIMIT_TABLE:
      rest = end - (start - 1) - LIMIT_TABLE
      end = start - 1 + LIMIT_TABLE
    for i in range(start - 1, end):
      collected.append((i + 1, results[i]))

  if len(collected) == 0:
    return
  (firstSeq, firstResult) = collected[0]
  nColumns = len(firstResult)
  markdown = ['n | ' + (' | '.join(F.otype.v(n) for n in firstResult))]
  markdown.append(' | '.join('---' for n in range(nColumns + 1)))
  for (seqNumber, ns) in collected:
    markdown.append(
        plainTuple(
            api,
            ns,
            seqNumber,
            linked=linked,
            withNodes=withNodes,
            asString=True,
        )
    )
  markdown = '\n'.join(markdown)
  if asString:
    return markdown
  _dm(markdown)
  if rest:
    _dm(
        f'**{rest} more results skipped** because we show a maximum of'
        f' {LIMIT_TABLE} results at a time'
    )
