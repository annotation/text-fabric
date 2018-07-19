import sys
import os
import re
from glob import glob
from importlib import import_module

appPat = '^(.*)-app$'
appRe = re.compile(appPat)

msgLinePat = '^( *[0-9]+) (.*)$'
msgLineRe = re.compile(msgLinePat)


def getDebug(cargs=sys.argv):
  for arg in cargs[1:]:
    if arg == '-d':
      return True
  return False


def getNoweb(cargs=sys.argv):
  for arg in cargs[1:]:
    if arg == '-noweb':
      return True
  return False


def getDocker(cargs=sys.argv):
  for arg in cargs[1:]:
    if arg == '-docker':
      return True
  return False


def getParam(cargs=sys.argv, interactive=False):
  myDir = os.path.dirname(os.path.abspath(__file__))
  dataSourcesParent = getAppDir(myDir, '')
  dataSourcesPre = glob(f'{dataSourcesParent}/*/config.py')
  dataSources = set()
  for p in dataSourcesPre:
    parent = os.path.dirname(p)
    d = os.path.split(parent)[1]
    match = appRe.match(d)
    if match:
      app = match.group(1)
      dataSources.add(app)
  dPrompt = '/'.join(dataSources)

  dataSource = None
  for arg in cargs[1:]:
    if arg.startswith('-'):
      continue
    dataSource = arg
    break

  if interactive:
    if dataSource is None:
      dataSource = input(f'specify data source [{dPrompt}] > ')
    if dataSource not in dataSources:
      print('Unknown data source')
      dataSource = None
    if dataSource is None:
      print(f'Pass a data source [{dPrompt}] as first argument')
    return dataSource

  if dataSource is None:
    return None
  if dataSource not in dataSources:
    print('Unknown data source')
    return False
  return dataSource


def getConfig(dataSource):
  try:
    config = import_module('.config', package=f'tf.extra.{dataSource}-app')
  except Exception as e:
    print('getConfig:', e)
    print(f'getConfig: Data source "{dataSource}" not found')
    return None
  return config


def getAppDir(myDir, dataSource):
  parentDir = os.path.dirname(myDir)
  tail = '' if dataSource == '' else f'{dataSource}-app'
  return f'{parentDir}/extra/{tail}'


def getValues(options, form):
  values = {}
  for (option, typ, acro, desc) in options:
    value = form.get(option, None)
    if typ == 'checkbox':
      value = True if value else False
    values[option] = value
  return values


def setValues(options, source, form):
  for (option, typ, acro, desc) in options:
    value = source.get(option, None)
    form[option] = value


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
    className = 'tline' if match else 'eline'
    html.append(f'''
      <div class="{className}">{msg.rstrip()}</div>
    ''')
  return ''.join(html)


def shapeOptions(options, values):
  html = []
  for (option, typ, acro, desc) in options:
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


def shapeCondense(condenseTypes, value):
  html = []
  lastType = len(condenseTypes) - 1
  for (i, (otype, av, b, e)) in enumerate(condenseTypes):
    checked = ' checked ' if value == otype else ''
    radio = (
        '<span class="cradio">&nbsp;</span>'
        if i == lastType else
        f'''<input class="r cradio" type="radio" id="ctp{i}"
              name="condensetp" value="{otype}" {checked}
            "/>'''
    )
    html.append(f'''
    <div class="cline">
      {radio}
      <span class="ctype">{otype}</span>
      <span class="cinfo">{e - b + 1: 8.6g} x av length {av: 4.2g}</span>
    </div>
  ''')
  return '\n'.join(html)


def _coarsify(n, spread):
  nAbs = int(round(abs(n) / spread)) * spread
  return nAbs if n >= 0 else -nAbs
