import time
import datetime

from ..parameters import NAME, VERSION, DOI_TEXT, DOI_URL, APP_URL


# NAVIGATION IN MULTIPLE ITEMS (PAGES, PASSAGES)

def pageLinks(nResults, position, spread=10):
  if spread <= 1:
    spread = 1
  elif nResults == 0:
    lines = []
  elif nResults == 1:
    lines = [(1, )]
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

      both = tuple(n for n in left + (position, ) + right if n > 0 and n <= nResults)

      if len(both) > 1:
        lines.append(both)

      factor *= spread

    lines.append(commonLine)

  html = '\n'.join(
      '<div class="pline">' + ' '
      .join(f'<a href="#" class="pnav {" focus" if position == p else ""}">{p}</a>'
            for p in line) + '</div>'
      for line in reversed(lines)
  )
  return html


def passageLinks(passages, sec0Type, sec0, sec1, tillLevel):
  sec0s = []
  sec1s = []
  for s0 in passages[0]:
    selected = str(s0) == str(sec0)
    sec0s.append(f'<a href="#" class="s0nav {" focus" if selected else ""}">{s0}</a>')
  if sec0:
    for s1 in passages[1]:
      selected = str(s1) == str(sec1)
      sec1s.append(f'<a href="#" class="s1nav {" focus" if selected else ""}">{s1}</a>')
  return f'''
  <div class="sline">
    <span><span id="s0total"></span> <span class="s0total">{sec0Type}s</span></span>
    {''.join(sec0s)}
  </div>
  <div class="sline">
    {''.join(sec1s)}
  </div>
'''


# OPTIONS

def getValues(options, form):
  values = {}
  for (option, default, typ, acro, desc) in options:
    value = form.get(option, None)
    if typ == 'checkbox':
      value = True if value else False
    values[option] = value
  return values


def setValues(options, source, form, emptyRequest):
  for (option, default, typ, acro, desc) in options:
    # only apply the default value if the form is empty
    # if the form is not empty, the absence of a checkbox value means
    # that the checkbox is unchecked
    # https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input/checkbox
    value = source.get(option, default if emptyRequest else None)
    if typ == 'checkbox':
      value = True if value else False
    form[option] = value


def wrapOptions(options, values):
  html = []
  for (option, default, typ, acro, desc) in options:
    value = values[option]
    if typ == 'checkbox':
      value = 'checked' if value else ''
    else:
      value = f'value="{value}"'
    html.append(
        f'''
      <div>
        <input
          class="r" type="{typ}" id="{acro}" name="{option}" {value}
        /> <span class="ilab">{desc}</span>
      </div>'''
    )
  return '\n'.join(html)


def wrapCondense(condenseTypes, value):
  html = []
  lastType = len(condenseTypes) - 1
  for (i, (otype, av, b, e)) in enumerate(condenseTypes):
    checked = ' checked ' if value == otype else ''
    radio = (
        '<span class="cradio">&nbsp;</span>'
        if i == lastType else f'''<input class="r cradio" type="radio" id="ctp{i}"
              name="condenseTp" value="{otype}" {checked}
            "/>'''
    )
    html.append(
        f'''
    <div class="cline">
      {radio}
      <span class="ctype">{otype}</span>
      <span class="cinfo">{e - b + 1: 8.6g} x av length {av: 4.2g}</span>
    </div>
  '''
    )
  return '\n'.join(html)


def wrapFormats(textFormats, value):
  html = []
  for (i, fmt) in enumerate(textFormats):
    checked = ' checked ' if value == fmt else ''
    radio = (
        f'''<input class="r tradio" type="radio" id="ttp{i}"
              name="textformat" value="{fmt}" {checked}
            "/>'''
    )
    html.append(
        f'''
    <div class="tfline">
      {radio}
      <span class="ttext">{fmt}</span>
    </div>
  '''
    )
  return '\n'.join(html)


# PROVENANCE

def wrapProvenance(form, provenance, setNames):
  utc_offset_sec = time.altzone if time.localtime().tm_isdst else time.timezone
  utc_offset = datetime.timedelta(seconds=-utc_offset_sec)
  now = datetime.datetime.now().replace(microsecond=0,
                                        tzinfo=datetime.timezone(offset=utc_offset)).isoformat()
  job = form['jobName']
  author = form['author']

  (appProvenance, dataProvenance) = provenance

  appHtml = ''
  appMd = ''
  sep = ''

  for d in appProvenance:
    d = dict(d)
    name = d['name']
    commit = d['commit']
    url = f'{APP_URL}/app-{name}/tree/{commit}'
    liveHtml = f'<a href="{url}">{commit}</a>'
    liveMd = f'[{commit}]({url})'
    appHtml += f'''
    <div class="pline">
      <div class="pname">TF App:</div>
      <div class="pval">{name}</div>
    </div>
    <div class="p2line">
      <div class="pname">commit</div>
      <div class="pval">{liveHtml}</div>
    </div>
'''
    appMd += f'''{sep}TF app | {name}
commit | {liveMd}'''
    sep = '\n'

  dataHtml = ''
  dataMd = ''
  sep = ''

  for d in dataProvenance:
    d = dict(d)
    corpus = d['corpus']
    version = d['version']
    release = d['release']
    (live, liveU) = d['live']
    liveHtml = f'<a href="{liveU}">{live}</a>'
    liveMd = f'[{live}]({liveU})'
    (doiText, doiUrl) = d['doi']
    doiHtml = f'<a href="{doiUrl}">{doiText}</a>'
    doiMd = f'[{doiText}]({doiUrl})'
    dataHtml += f'''
    <div class="pline">
      <div class="pname">Data:</div>
      <div class="pval">{corpus}</div>
    </div>
    <div class="p2line">
      <div class="pname">version</div>
      <div class="pval">{version}</div>
    </div>
    <div class="p2line">
      <div class="pname">release</div>
      <div class="pval">{release}</div>
    </div>
    <div class="p2line">
      <div class="pname">download</div>
      <div class="pval">{liveHtml}</div>
    </div>
    <div class="p2line">
      <div class="pname">DOI</div>
      <div class="pval">{doiHtml}</div>
    </div>
'''
    dataMd += f'''{sep}Data source | {corpus}
version | {version}
release | {release}
download   | {liveMd}
DOI | {doiMd}'''
    sep = '\n'

  setHtml = ''
  setMd = ''

  if setNames:
    setNamesRep = ', '.join(setNames)
    setHtml += f'''
    <div class="psline">
      <div class="pname">Sets:</div>
      <div class="pval">{setNamesRep} (<b>not exported</b>)</div>
    </div>
'''
    setMd += f'''Sets | {setNamesRep} (**not exported**)'''

  tool = f'{NAME} {VERSION}'
  toolDoiHtml = f'<a href="{DOI_URL}">{DOI_TEXT}</a>'
  toolDoiMd = f'[{DOI_TEXT}]({DOI_URL})'

  html = f'''
    <div class="pline">
      <div class="pname">Job:</div><div class="pval">{job}</div>
    </div>
    <div class="pline">
      <div class="pname">Author:</div><div class="pval">{author}</div>
    </div>
    <div class="pline">
      <div class="pname">Created:</div><div class="pval">{now}</div>
    </div>
    {dataHtml}
    {setHtml}
    <div class="pline">
      <div class="pname">Tool:</div>
      <div class="pval">{tool} {toolDoiHtml}</div>
    </div>
    {appHtml}
  '''

  md = f'''
meta | data
--- | ---
Job | {job}
Author | {author}
Created | {now}
{dataMd}
{setMd}
Tool | {tool} {toolDoiMd}
{appMd}
'''

  return (html, md)


# LOWER LEVEL

def _coarsify(n, spread):
  nAbs = int(round(abs(n) / spread)) * spread
  return nAbs if n >= 0 else -nAbs
