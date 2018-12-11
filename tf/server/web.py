import os
from io import BytesIO
import json
from zipfile import ZipFile
import datetime
import time
import pickle

import markdown

from flask import (
    Flask,
    request,
    redirect,
    send_file,
    make_response,
    render_template,
    jsonify,
)
from werkzeug.serving import run_simple

# import bottle
# from bottle import (
#     post, get, route, template,
#     request, response,
#     static_file, run, redirect,
# )

from tf.core.helpers import console, shapeMessages
from tf.parameters import NAME, VERSION, DOI_TEXT, DOI_URL, COMPOSE_URL, ZIP_OPTIONS
from tf.applib.helpers import RESULT, findAppConfig, getLocalDir, configure
from tf.server.kernel import makeTfConnection
from tf.server.common import (
    getParam,
    getModules,
    getDebug,
    getDocker,
    getLocalClones,
    getAppDir,
    getValues,
    setValues,
    pageLinks,
    passageLinks,
    shapeOptions,
    shapeCondense,
    shapeFormats,
)

TIMEOUT = 180

COMPOSE = 'Compose results example'

BATCH = 20
DEFAULT_NAME = 'default'

myDir = os.path.dirname(os.path.abspath(__file__))
appDir = None
localDir = None
# bottle.TEMPLATE_PATH = [f'{myDir}/views']

dataSource = None
config = None

wildQueries = set()


def getStuff(lgc):
  global TF
  global appDir
  global localDir

  config = findAppConfig(dataSource)
  if config is None:
    return None

  TF = makeTfConnection(config.HOST, config.PORT['kernel'], TIMEOUT)
  appDir = getAppDir(myDir, dataSource)
  cfg = configure(config, lgc, None)
  version = cfg['version']
  cfg['localDir'] = getLocalDir(cfg, lgc, version)
  localDir = cfg['localDir']
  return config


def getProvenance(form, provenance, setNames):
  utc_offset_sec = time.altzone if time.localtime().tm_isdst else time.timezone
  utc_offset = datetime.timedelta(seconds=-utc_offset_sec)
  now = datetime.datetime.now().replace(microsecond=0,
                                        tzinfo=datetime.timezone(offset=utc_offset)).isoformat()
  job = form['jobName']
  author = form['author']

  dataHtml = ''
  dataMd = ''
  sep = ''

  for d in provenance:
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

  composeHtml = f'<a href="{COMPOSE_URL}">{COMPOSE}</a>'
  composeMd = f'[{COMPOSE}]({COMPOSE_URL})'

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
    <div class="pline">
      <div class="pname">See also:</div>
      <div class="pval">{composeHtml}</div>
    </div>
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
See also | {composeMd}
'''

  return (html, md)


def writeAbout(header, provenance, form):
  pass
  '''
  jobName = form['jobName']
  with open(f'about.md', 'w', encoding='utf8') as ph:
    ph.write(
  '''
  f'''
{header}

{provenance}

# {form["title"]}

## {form["author"]}

{form["description"]}

## Information requests:

### Sections

```
{form["sections"]}
```

### Nodes

```
{form["tuples"]}
```

### Search

```
{form["query"]}
```
'''
  '''
    )
  '''


def getInt(x, default=1):
  if len(x) > 15:
    return default
  if not x.isdecimal():
    return default
  return int(x)


def getFormData():
  form = {}
  jobName = request.form.get('jobName', '').strip()
  emptyRequest = False
  if jobName:
    form['jobName'] = jobName
    form['loadJob'] = ''
  else:
    emptyRequest = True
    form['jobName'] = DEFAULT_NAME
    form['loadJob'] = '1'
  form['query'] = request.form.get('query', '').replace('\r', '')
  form['messages'] = request.form.get('messages', '') or ''
  form['features'] = request.form.get('features', '') or ''
  form['tuples'] = request.form.get('tuples', '').replace('\r', '')
  form['sections'] = request.form.get('sections', '').replace('\r', '')
  form['appName'] = request.form.get('appName', '')
  form['jobName'] = request.form.get('jobName', '').strip() or DEFAULT_NAME
  form['side'] = request.form.get('side', '')
  form['help'] = request.form.get('help', '')
  form['author'] = request.form.get('author', '').strip()
  form['title'] = request.form.get('title', '').strip()
  form['description'] = request.form.get('description', '').replace('\r', '')
  form['withNodes'] = request.form.get('withNodes', '')
  form['condensed'] = request.form.get('condensed', '')
  form['condenseTp'] = request.form.get('condenseTp', '')
  form['textformat'] = request.form.get('textformat', '')
  form['sectionsExpandAll'] = request.form.get('sectionsExpandAll', '')
  form['tuplesExpandAll'] = request.form.get('tuplesExpandAll', '')
  form['queryExpandAll'] = request.form.get('queryExpandAll', '')
  form['linked'] = getInt(request.form.get('linked', ''), default=1)
  form['passageOpened'] = request.form.get('passageOpened', '')
  form['sectionsOpened'] = request.form.get('sectionsOpened', '')
  form['tuplesOpened'] = request.form.get('tuplesOpened', '')
  form['queryOpened'] = request.form.get('queryOpened', '')
  form['mode'] = request.form.get('mode', '') or 'passage'
  form['position'] = getInt(request.form.get('position', ''), default=1)
  form['batch'] = getInt(request.form.get('batch', ''), default=BATCH)
  form['sec0'] = request.form.get('sec0', '')
  form['sec1'] = request.form.get('sec1', '')
  form['sec2'] = request.form.get('sec2', '')
  setValues(config.OPTIONS, request.form, form, emptyRequest)
  return form


def factory():
  app = Flask(__name__)

  @app.route('/server/static/<path:filepath>')
  def serveStatic(filepath):
    return send_file(f'{myDir}/static/{filepath}')

  @app.route('/data/static/<path:filepath>')
  def serveData(filepath):
    return send_file(f'{appDir}/static/{filepath}')

  @app.route('/local/<path:filepath>')
  def serveLocal(filepath):
    return send_file(f'{localDir}/{filepath}')

  @app.route('/sections', methods=['GET', 'POST'])
  def serveSectionsBare():
    return serveTable('sections', None)

  @app.route('/sections/<int:getx>', methods=['GET', 'POST'])
  def serveSections(getx):
    return serveTable('sections', getx)

  @app.route('/tuples', methods=['GET', 'POST'])
  def serveTuplesBare():
    return serveTable('tuples', None)

  @app.route('/tuples/<int:getx>', methods=['GET', 'POST'])
  def serveTuples(getx):
    return serveTable('tuples', getx)

  @app.route('/query', methods=['GET', 'POST'])
  def serveQueryBare():
    return serveQuery(None)

  @app.route('/query/<int:getx>', methods=['GET', 'POST'])
  def serveQueryX(getx):
    return serveQuery(getx)

  @app.route('/passage', methods=['GET', 'POST'])
  def servePassageBare():
    return servePassage(None)

  @app.route('/passage/<getx>', methods=['GET', 'POST'])
  def servePassageX(getx):
    return servePassage(getx)

  @app.route('/export', methods=['GET', 'POST'])
  def serveExportX():
    return serveExport()

  @app.route('/download', methods=['GET', 'POST'])
  def serveDownloadX():
    return serveDownload()

  @app.route('/', methods=['GET', 'POST'])
  @app.route('/<path:anything>', methods=['GET', 'POST'])
  def serveAllX(anything=None):
    return serveAll(anything)

  return app


def serveTable(kind, getx=None, asDict=False):
  form = getFormData()
  textFormat = form['textformat'] or None
  task = form[kind].strip()
  openedKey = f'{kind}Opened'
  openedSet = {int(n) for n in form[openedKey].split(',')} if form[openedKey] else set()

  optionSpecs = config.OPTIONS
  options = getValues(optionSpecs, form)

  method = dict if asDict else jsonify

  kernelApi = TF.connect()

  messages = ''
  table = None
  if task:
    (
        table,
        messages,
    ) = kernelApi.table(
        kind,
        task,
        form['features'],
        opened=openedSet,
        fmt=textFormat,
        withNodes=form['withNodes'],
        getx=int(getx) if getx else None,
        **options,
    )

    if messages:
      messages = shapeMessages(messages)

  return method(
      table=table,
      messages=messages,
  )


def serveQuery(getx, asDict=False):
  kind = 'query'
  form = getFormData()
  task = form[kind]
  condenseType = form['condenseTp'] or None
  resultKind = condenseType if form['condensed'] else RESULT
  textFormat = form['textformat'] or None
  openedKey = f'{kind}Opened'
  openedSet = {int(n) for n in form[openedKey].split(',')} if form[openedKey] else set()

  optionSpecs = config.OPTIONS
  options = getValues(optionSpecs, form)

  pages = ''
  features = ''

  kernelApi = TF.connect()
  method = dict if asDict else jsonify

  if task:
    messages = ''
    table = None
    if task in wildQueries:
      messages = (
          f'Aborted because query is known to take longer than {TIMEOUT} second'
          + ('' if TIMEOUT == 1 else 's')
      )
    else:
      try:
        (
            table,
            messages,
            features,
            start,
            total,
        ) = kernelApi.search(
            task,
            form['batch'],
            position=form['position'],
            opened=openedSet,
            condensed=form['condensed'],
            condenseType=condenseType,
            fmt=textFormat,
            withNodes=form['withNodes'],
            linked=form['linked'],
            getx=int(getx) if getx else None,
            **options,
        )
      except TimeoutError:
        messages = (
            f'Aborted because query takes longer than {TIMEOUT} second'
            + ('' if TIMEOUT == 1 else 's')
        )
        console(f'{task}\n{messages}', error=True)
        wildQueries.add(task)

    if table is not None:
      pages = pageLinks(total, form['position'])
    # messages have already been shaped by search
    # if messages:
    #  messages = shapeMessages(messages)
  else:
    table = f'no {resultKind}s'
    messages = ''

  return method(
      pages=pages,
      table=table,
      messages=messages,
      features=features,
  )


def servePassage(getx):
  form = getFormData()
  textFormat = form['textformat'] or None

  optionSpecs = config.OPTIONS
  options = getValues(optionSpecs, form)

  passages = ''

  kernelApi = TF.connect()

  openedKey = 'passageOpened'
  openedSet = {int(n) for n in form[openedKey].split(',')} if form[openedKey] else set()

  sec0 = form['sec0']
  sec1 = form['sec1']
  sec2 = form['sec2']
  (
      table,
      passages,
  ) = kernelApi.passage(
      sec0,
      sec1,
      form['features'],
      form['query'],
      sec2=sec2,
      opened=openedSet,
      fmt=textFormat,
      withNodes=form['withNodes'],
      getx=getx,
      **options,
  )
  passages = passageLinks(passages, sec0, sec1)
  return jsonify(
      table=table,
      passages=passages,
  )


def serveExport():
  sectionsData = serveTable('sections', None, asDict=True)
  tuplesData = serveTable('tuples', None, asDict=True)
  queryData = serveQuery(None, asDict=True)

  form = getFormData()

  kernelApi = TF.connect()
  (header, appLogo, tfLogo) = kernelApi.header()
  css = kernelApi.css()
  provenance = kernelApi.provenance()
  setNames = kernelApi.setNames()
  setNamesRep = ', '.join(setNames)
  setNameHtml = f'''
<p class="setnames">Sets:
<span class="setnames">{setNamesRep}</span>
</p>''' if setNames else ''
  (provenanceHtml, provenanceMd) = getProvenance(form, provenance, setNames)

  descriptionMd = markdown.markdown(
      form['description'], extensions=[
          'markdown.extensions.tables',
          'markdown.extensions.fenced_code',
      ]
  )

  sectionsMessages = sectionsData['messages']
  sectionsTable = sectionsData['table']
  tuplesMessages = tuplesData['messages']
  tuplesTable = tuplesData['table']
  queryMessages = queryData['messages']
  queryTable = queryData['table']

  return render_template(
      'export.html',
      dataSource=dataSource,
      css=css,
      descriptionMd=descriptionMd,
      sectionsTable=(
          sectionsMessages if sectionsMessages or sectionsTable is None else sectionsTable
      ),
      tuplesTable=(
          tuplesMessages if tuplesMessages or tuplesTable is None else tuplesTable
      ),
      queryTable=(
          queryMessages if queryMessages or queryTable is None else queryTable
      ),
      colofon=f'{appLogo}{header}{tfLogo}',
      provenance=provenanceHtml,
      setNames=setNameHtml,
      **form,
  )


def serveDownload():
  form = getFormData()
  kernelApi = TF.connect()

  task = form['query']
  condenseType = form['condenseTp'] or None
  textFormat = form['textformat'] or None
  csvs = None
  resultsX = None
  messages = ''
  if task in wildQueries:
    messages = (
        f'Aborted because query is known to take longer than {TIMEOUT} second'
        + ('' if TIMEOUT == 1 else 's')
    )
  else:
    try:
      (queryMessages, csvs, resultsX) = kernelApi.csvs(
          task,
          form['tuples'],
          form['sections'],
          condensed=form['condensed'],
          condenseType=condenseType,
          fmt=textFormat,
      )
    except TimeoutError:
      messages = (
          f'Aborted because query takes longer than {TIMEOUT} second'
          + ('' if TIMEOUT == 1 else 's')
      )
      console(f'{task}\n{messages}', error=True)
      wildQueries.add(task)
      return jsonify(messages=messages)

  if queryMessages:
    redirect('/')
    return jsonify(messages=queryMessages)

  csvs = pickle.loads(csvs)
  resultsX = pickle.loads(resultsX)
  (fileName, zipBuffer) = zipData(csvs, resultsX, form)

  headers = {
      'Expires': '0',
      'Cache-Control': 'no-cache, no-store, must-revalidate',
      'Content-Type': 'application/octet-stream',
      'Content-Disposition': f'attachment; filename="{fileName}"',
      'Content-Encoding': 'identity',
  }
  return make_response(zipBuffer, headers)


def serveAll(anything):
  form = getFormData()
  condensedAtt = ' checked ' if form['condensed'] else ''
  withNodesAtt = ' checked ' if form['withNodes'] else ''

  optionSpecs = config.OPTIONS
  options = getValues(optionSpecs, form)

  pages = ''
  passages = ''

  kernelApi = TF.connect()

  (header, appLogo, tfLogo) = kernelApi.header()
  css = kernelApi.css()
  provenance = kernelApi.provenance()
  setNames = kernelApi.setNames()
  setNamesRep = ', '.join(setNames)
  setNameHtml = f'''
<p class="setnames">Sets:
<span class="setnames">{setNamesRep}</span>
</p>''' if setNames else ''
  (provenanceHtml, provenanceMd) = getProvenance(form, provenance, setNames)

  (
      defaultCondenseType,
      exampleSection,
      exampleSectionText,
      condenseTypes,
      defaultTextFormat,
      textFormats,
  ) = kernelApi.condenseTypes()
  condenseType = form['condenseTp'] or defaultCondenseType
  condenseOpts = shapeCondense(condenseTypes, condenseType)
  textFormat = form['textformat'] or defaultTextFormat
  textFormatOpts = shapeFormats(textFormats, textFormat)

  return render_template(
      'index.html',
      dataSource=dataSource,
      css=css,
      header=f'{appLogo}{header}{tfLogo}',
      setNames=setNameHtml,
      options=shapeOptions(optionSpecs, options),
      condensedAtt=condensedAtt,
      condenseOpts=condenseOpts,
      defaultCondenseType=defaultCondenseType,
      textFormatOpts=textFormatOpts,
      defaultTextFormat=defaultTextFormat,
      exampleSection=exampleSection,
      exampleSectionText=exampleSectionText,
      withNodesAtt=withNodesAtt,
      pages=pages,
      passages=passages,
      **form,
  )


def zipData(csvs, resultsX, form):
  appName = form['appName']
  jobName = form['jobName']

  zipBuffer = BytesIO()
  with ZipFile(
      zipBuffer,
      "w",
      **ZIP_OPTIONS,
  ) as zipFile:

    zipFile.writestr('job.json', json.dumps(form).encode('utf8'))
    if csvs is not None:
      for (csv, data) in csvs:
        contents = ''.join(
            ('\t'.join(str(t) for t in tup) + '\n')
            for tup in data
        )
        zipFile.writestr(f'{csv}.tsv', contents.encode('utf8'))
      for (name, data) in (
          ('resultsx', resultsX),
      ):
        if data is not None:
            contents = '\ufeff' + ''.join(
                ('\t'.join('' if t is None else str(t) for t in tup) + '\n')
                for tup in data
            )
            zipFile.writestr(f'resultsx.tsv', contents.encode('utf_16_le'))
  return (f'{appName}-{jobName}.zip', zipBuffer.getvalue())


if __name__ == "__main__":
  dataSource = getParam(interactive=True)
  modules = getModules()

  if dataSource is not None:
    modules = tuple(modules[6:].split(',')) if modules else ()
    lgc = getLocalClones()
    debug = getDebug()
    config = getStuff(lgc)
    onDocker = getDocker()
    console(f'onDocker={onDocker}')
    if config is not None:
      webapp = factory()
      run_simple(
          '0.0.0.0' if onDocker else config.HOST,
          config.PORT['web'],
          webapp,
          use_reloader=debug,
          use_debugger=debug,
      )
