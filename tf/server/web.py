import os
import datetime
import time
from glob import glob

import json
import markdown

import bottle
from bottle import (post, get, route, template, request, static_file, run)

from tf.fabric import NAME, VERSION, DOI, DOI_URL
from tf.server.service import makeTfConnection
from tf.server.common import (
    getParam, getDebug, getConfig, getAppDir, getValues, setValues,
    pageLinks,
    shapeMessages, shapeOptions, shapeCondense,
)
from tf.apphelpers import RESULT


BATCH = 20

myDir = os.path.dirname(os.path.abspath(__file__))
appDir = None
bottle.TEMPLATE_PATH = [f'{myDir}/views']

dataSource = None
config = None


def getStuff():
  global TF
  global appDir

  config = getConfig(dataSource)
  if config is None:
    return None

  TF = makeTfConnection(config.host, config.port)
  appDir = getAppDir(myDir, dataSource)
  return config


def getProvenance(form):
  utc_offset_sec = time.altzone if time.localtime().tm_isdst else time.timezone
  utc_offset = datetime.timedelta(seconds=-utc_offset_sec)
  now = datetime.datetime.now().replace(
      microsecond=0, tzinfo=datetime.timezone(offset=utc_offset)
  ).isoformat()
  job = form['fileName']
  author = form['author']

  prov = config.PROVENANCE

  corpus = prov['corpus']
  (corpusDoi, corpusUrl) = prov['corpusDoi']
  corpusDoiHtml = f'<a href="{corpusUrl}">{corpusDoi}</a>'
  corpusDoiMd = f'[{corpusDoi}]({corpusUrl})'

  tool = f'{NAME} {VERSION}'
  toolDoiHtml = f'<a href="{DOI_URL}">{DOI}</a>'
  toolDoiMd = f'[{DOI}]({DOI_URL})'

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
    <div class="pline">
      <div class="pname">Corpus:</div>
      <div class="pval">{corpus} {corpusDoiHtml}</div>
    </div>
    <div class="pline">
      <div class="pname">Tool:</div>
      <div class="pval">{tool} {toolDoiHtml}</div>
    </div>
  '''

  md = f'''
meta | data
--- | ---
Job | {job}
Author | {author}
Created | {now}
Corpus | {corpus} {corpusDoiMd}
Tool | {tool} {toolDoiMd}
'''

  return (html, md)


def writeAbout(header, provenance, form):
  fileName = form['fileName']
  dirName = f'{dataSource}-{fileName}'
  if not os.path.exists(dirName):
    os.makedirs(dirName, exist_ok=True)
  with open(f'{dirName}/about.md', 'w') as ph:
    ph.write(f'''
{header}

{provenance}

# {form["title"]}

## {form["author"]}

{form["description"]}

''')


def writeCsvs(csvs, context, form):
  fileName = form['fileName']
  dirName = f'{dataSource}-{fileName}'
  if not os.path.exists(dirName):
    os.makedirs(dirName, exist_ok=True)
  for (csv, data) in csvs:
    with open(f'{dirName}/{csv}.tsv', 'w') as th:
      for tup in data:
        th.write('\t'.join(str(t) for t in tup) + '\n')
  with open(f'{dirName}/CONTEXT.tsv', 'w') as th:
      for tup in context:
        th.write('\t'.join('' if t is None else str(t) for t in tup) + '\n')


def getInt(x, default=1):
  if len(x) > 15:
    return default
  if not x.isdecimal():
    return default
  return int(x)


def getFormData():
  form = {}
  form['searchTemplate'] = request.forms.searchTemplate.replace('\r', '')
  form['tuples'] = request.forms.tuples.replace('\r', '')
  form['sections'] = request.forms.sections.replace('\r', '')
  form['fileName'] = request.forms.fileName.strip()
  form['previous'] = request.forms.previous
  form['previousdo'] = request.forms.previousdo
  form['side'] = request.forms.side
  form['fileNameHidden'] = request.forms.fileNameHidden.strip()
  form['author'] = request.forms.author.strip()
  form['title'] = request.forms.title.strip()
  form['description'] = request.forms.description.replace('\r', '')
  form['withNodes'] = request.forms.withNodes
  form['condensed'] = request.forms.condensed
  form['condensetp'] = request.forms.condensetp
  form['export'] = request.forms.export
  form['expandAll'] = request.forms.expandAll
  form['linked'] = getInt(request.forms.linked, default=1)
  form['opened'] = request.forms.opened
  form['position'] = getInt(request.forms.position, default=1)
  form['batch'] = getInt(request.forms.batch, default=BATCH)
  setValues(config.options, request.forms, form)
  return form


def writeFormData(form):
  excludedFields = {'export'}
  thisFileName = form['fileName'] or ''
  with open(f'{dataSource}-{thisFileName}.tfquery', 'w') as tfj:
    json.dump({f: form[f] for f in form if f not in excludedFields}, tfj)


def readFormData(source):
  sourceFile = f'{dataSource}-{source}.tfquery'
  if os.path.exists(sourceFile):
    with open(sourceFile) as tfj:
      form = json.load(tfj)
    for item in '''
        searchTemplate tuples sections fileName fileNameHidden
        condensetp opened author title export
        previous previousdo side author title description
    '''.strip().split():
      if form.get(item, None) is None:
        form[item] = ''
    return form
  return None


def getPrevOptions(current):
  prevs = glob(f'{dataSource}-*.tfquery')
  options = []
  for prev in prevs:
    prevVal = prev[0:-8].split('-', 1)[1]
    if prevVal == '':
      prevVal = 'DefaulT'
    selected = ' selected ' if prevVal == current else ''
    options.append(f'<option value="{prevVal}"{selected}>{prevVal}</option>')
  return '\n'.join(options)


@route('/server/static/<filepath:path>')
def serveStatic(filepath):
  return static_file(filepath, root=f'{myDir}/static')


@route('/data/static/<filepath:path>')
def serveData(filepath):
  return static_file(filepath, root=f'{appDir}/static')


@route('/local/<filepath:path>')
def serveLocal(filepath):
  return static_file(filepath, root=f'{config.localDir}')


@post('/<anything:re:.*>')
@get('/<anything:re:.*>')
def serveSearch(anything):
  form = getFormData()
  previousDo = form['previousdo']
  if previousDo != '' or form['fileName'] == '':
    prev = previousDo if previousDo else 'DefaulT'
    previous = readFormData(prev)
    if previous is not None:
      form = previous
    form['fileName'] = prev
  form['previousdo'] = ''
  condensedAtt = ' checked ' if form['condensed'] else ''
  withNodesAtt = ' checked ' if form['withNodes'] else ''

  openedSet = {int(n) for n in form['opened'].split(',')} if form['opened'] else set()

  options = config.options
  values = getValues(options, form)

  pages = ''

  api = TF.connect()
  (header, appLogo, tfLogo) = api.header()
  css = api.css()
  (provenanceHtml, provenanceMd) = getProvenance(form)

  (defaultCondenseType, exampleSection, condenseTypes) = api.condenseTypes()
  condenseType = form['condensetp'] or defaultCondenseType
  condenseOpts = shapeCondense(condenseTypes, condenseType)

  resultKind = condenseType if form['condensed'] else RESULT

  if form['searchTemplate'] or form['tuples'] or form['sections']:
    (
        table,
        sectionMessages, tupleMessages, queryMessages,
        start, total,
    ) = api.search(
        form['searchTemplate'],
        form['tuples'],
        form['sections'],
        form['condensed'],
        condenseType,
        form['batch'],
        position=form['position'],
        opened=openedSet,
        withNodes=form['withNodes'],
        linked=form['linked'],
        **values,
    )
    if table is not None:
      pages = pageLinks(total, form['position'])

    if sectionMessages:
      sectionMessages = shapeMessages(sectionMessages)
    if tupleMessages:
      tupleMessages = shapeMessages(tupleMessages)
    if queryMessages:
      queryMessages = shapeMessages(queryMessages)
  else:
    table = f'no {resultKind}s'
    sectionMessages = ''
    tupleMessages = ''
    queryMessages = ''

  writeFormData(form)

  prevOptions = getPrevOptions(form['fileName'])

  descriptionMd = markdown.markdown(
      form['description'],
      extensions=[
          'markdown.extensions.tables',
          'markdown.extensions.fenced_code',
      ]
  )

  if form['export']:
    form['export'] = ''
    writeAbout(
        header,
        provenanceMd,
        form,
    )
    (csvs, context) = api.csvs(
        form['searchTemplate'],
        form['tuples'],
        form['sections'],
        form['condensed'],
        condenseType,
    )
    writeCsvs(csvs, context, form)

    return template(
        'export',
        dataSource=dataSource,
        css=css,
        descriptionMd=descriptionMd,
        table=table,
        condenseType=condenseType,
        colofon=f'{appLogo}{header}{tfLogo}',
        provenance=provenanceHtml,
        **form,
    )
  return template(
      'index',
      dataSource=dataSource,
      css=css,
      header=f'{appLogo}{header}{tfLogo}',
      options=shapeOptions(options, values),
      sectionMessages=sectionMessages,
      tupleMessages=tupleMessages,
      queryMessages=queryMessages,
      table=table,
      condensedAtt=condensedAtt,
      condenseOpts=condenseOpts,
      defaultCondenseType=defaultCondenseType,
      exampleSection=exampleSection,
      withNodesAtt=withNodesAtt,
      pages=pages,
      prevOptions=prevOptions,
      **form,
  )


if __name__ == "__main__":
  dataSource = getParam(interactive=True)
  if dataSource is not None:
    debug = getDebug()
    config = getStuff()
    if config is not None:
      run(
          debug=debug,
          reloader=debug,
          host=config.host,
          port=config.webport,
      )
