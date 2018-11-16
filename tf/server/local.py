import os
from shutil import rmtree
import datetime
import time
import pickle
from glob import glob

import json
import markdown

import bottle
from bottle import (post, get, route, template, request, static_file, run)

from ..core.helpers import console
from ..parameters import NAME, VERSION, DOI, DOI_URL, COMPOSE_URL
from ..applib.apphelpers import RESULT
from ..applib.appmake import (
    findAppConfig,
)
from .kernel import makeTfConnection
from .common import (
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
    shapeMessages,
    shapeOptions,
    shapeCondense,
    shapeFormats,
)

COMPOSE = 'Compose results example'

BATCH = 20
DEFAULT_NAME = 'DefaulT'
EXTENSION = '.tfjob'

myDir = os.path.dirname(os.path.abspath(__file__))
appDir = None
localDir = None
bottle.TEMPLATE_PATH = [f'{myDir}/views']

dataSource = None
config = None


def getStuff(lgc):
  global TF
  global appDir
  global localDir

  config = findAppConfig(dataSource)
  if config is None:
    return None

  TF = makeTfConnection(config.host, config.port)
  appDir = getAppDir(myDir, dataSource)
  cfg = config.configure(lgc, version=config.VERSION)
  localDir = cfg['localDir']
  return config


def getProvenance(form, provenance):
  utc_offset_sec = time.altzone if time.localtime().tm_isdst else time.timezone
  utc_offset = datetime.timedelta(seconds=-utc_offset_sec)
  now = datetime.datetime.now().replace(microsecond=0,
                                        tzinfo=datetime.timezone(offset=utc_offset)).isoformat()
  job = form['jobName']
  author = form['author']

  dataHtml = ''
  dataMd = ''

  for d in provenance:
    corpus = d['corpus']
    version = d['version']
    release = d['release']
    (live, liveUrl) = d['live']
    liveHtml = f'<a href="{liveUrl}">{live}</a>'
    liveMd = f'[{live}]({liveUrl})'
    (doi, doiUrl) = d['doi']
    doiHtml = f'<a href="{doiUrl}">{doi}</a>'
    doiMd = f'[{doi}]({doiUrl})'
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
    dataMd += f'''Data source | {corpus}
version | {version}
release | {release}
download   | {liveMd}
DOI | {doiMd}'''

  tool = f'{NAME} {VERSION}'
  toolDoiHtml = f'<a href="{DOI_URL}">{DOI}</a>'
  toolDoiMd = f'[{DOI}]({DOI_URL})'

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
Tool | {tool} {toolDoiMd}
See also | {composeMd}
'''

  return (html, md)


def writeAbout(header, provenance, form):
  jobName = form['jobName']
  dirName = f'{dataSource}-{jobName}'
  if os.path.exists(dirName):
    rmtree(dirName)
  os.makedirs(dirName, exist_ok=True)
  with open(f'{dirName}/about.md', 'w', encoding='utf8') as ph:
    ph.write(
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
{form["searchTemplate"]}
```
'''
    )


def writeCsvs(csvs, context, resultsX, form):
  jobName = form['jobName']
  dirName = f'{dataSource}-{jobName}'
  if not os.path.exists(dirName):
    os.makedirs(dirName, exist_ok=True)
  for (csv, data) in csvs:
    with open(f'{dirName}/{csv}.tsv', 'w', encoding='utf8') as th:
      for tup in data:
        th.write('\t'.join(str(t) for t in tup) + '\n')
  for (name, data) in (
      ('CONTEXT', context),
      ('RESULTSX', resultsX),
  ):
    with open(f'{dirName}/{name}.tsv', 'w', encoding='utf_16_le') as th:
      th.write('﻿')  # utf8 bom mark, useful for opening file in Excel
      for tup in data:
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
  form['jobDir'] = request.forms.jobDir.strip()
  form['jobName'] = request.forms.jobName.strip()
  form['jobNameHidden'] = request.forms.jobNameHidden.strip()
  form['chdir'] = request.forms.chdir
  form['rename'] = request.forms.rename
  form['duplicate'] = request.forms.duplicate
  form['otherJob'] = request.forms.otherJob
  form['otherJobDo'] = request.forms.otherJobDo
  form['side'] = request.forms.side
  form['help'] = request.forms.help
  form['author'] = request.forms.author.strip()
  form['title'] = request.forms.title.strip()
  form['description'] = request.forms.description.replace('\r', '')
  form['withNodes'] = request.forms.withNodes
  form['condensed'] = request.forms.condensed
  form['condensetp'] = request.forms.condensetp
  form['textformat'] = request.forms.textformat
  form['export'] = request.forms.export
  form['expandAll'] = request.forms.expandAll
  form['linked'] = getInt(request.forms.linked, default=1)
  form['opened'] = request.forms.opened
  form['mode'] = request.forms.mode
  form['position'] = getInt(request.forms.position, default=1)
  form['batch'] = getInt(request.forms.batch, default=BATCH)
  form['sec0'] = request.forms.sec0
  form['sec1'] = request.forms.sec1
  form['sec2'] = request.forms.sec2
  setValues(config.options, request.forms, form)
  return form


def writeFormData(form):
  excludedFields = {
      'export',
      'chdir',
      'rename',
      'duplicate',
      'jobName',
      'jobNameHidden',
      'jobDir',
      'otherJobDo',
      'otherJob',
  }
  thisJobName = form['jobName'] or ''
  with open(f'{dataSource}-{thisJobName}{EXTENSION}', 'w', encoding='utf8') as tfj:
    json.dump({f: form[f] for f in form if f not in excludedFields}, tfj)


def readFormData(source):
  sourceFile = f'{dataSource}-{source}{EXTENSION}'
  if os.path.exists(sourceFile):
    with open(sourceFile, encoding='utf8') as tfj:
      form = json.load(tfj)
    for item in '''
        searchTemplate tuples sections
        jobNameHidden
        chdir rename duplicate
        condensetp textformat opened author title export
        otherJob otherJobDo side help author title description
        mode sec0 sec1 sec2
    '''.strip().split():
      if form.get(item, None) is None:
        form[item] = ''
      form['jobName'] = source
      form['jobDir'] = os.getcwd()
    return form
  return None


def getOtherOptions(current):
  others = glob(f'{dataSource}-*{EXTENSION}')
  trimLength = len(EXTENSION)
  options = []
  for other in others:
    otherVal = other[0:-trimLength].split('-', 1)[1]
    if otherVal == '':
      otherVal = DEFAULT_NAME
    selected = ' selected ' if otherVal == current else ''
    options.append(f'<option value="{otherVal}"{selected}>{otherVal}</option>')
  return '\n'.join(options)


@route('/server/static/<filepath:path>')
def serveStatic(filepath):
  return static_file(filepath, root=f'{myDir}/static')


@route('/data/static/<filepath:path>')
def serveData(filepath):
  return static_file(filepath, root=f'{appDir}/static')


@route('/local/<filepath:path>')
def serveLocal(filepath):
  return static_file(filepath, root=f'{localDir}')


@post('/<anything:re:.*>')
@get('/<anything:re:.*>')
def serveSearch(anything):
  form = getFormData()
  curJobDir = os.getcwd()
  newDir = form['jobDir']
  dirMsg = ''
  if newDir != curJobDir:
    if form['chdir']:
      good = True
      if not os.path.exists(newDir):
        try:
          os.makedirs(newDir, exist_ok=True)
          os.chdir(newDir)
        except Exception:
          good = False
      if good:
        os.chdir(newDir)
        form['jobName'] = ''
      else:
        dirMsg = f'Cannot create directory "{newDir}"'
      form['chdir'] = ''
    else:
      form['jobDir'] = curJobDir
  if form['jobName'] != form['jobNameHidden']:
    src = f'{dataSource}-{form["jobNameHidden"] or DEFAULT_NAME}{EXTENSION}'
    form['jobNameHidden'] = form['jobName']
    if form['rename']:
      if os.path.exists(src):
        os.unlink(src)
    form['rename'] = ''
    form['duplicate'] = ''
  otherJobDo = form['otherJobDo']
  if otherJobDo != '' or form['jobName'] == '':
    other = otherJobDo if otherJobDo else DEFAULT_NAME
    otherJob = readFormData(other)
    if otherJob is not None:
      form = otherJob
    form['jobName'] = other
  form['otherJobDo'] = ''
  condensedAtt = ' checked ' if form['condensed'] else ''
  withNodesAtt = ' checked ' if form['withNodes'] else ''

  options = config.options
  values = getValues(options, form)

  pages = ''
  passages = ''

  kernelApi = TF.connect()
  (header, appLogo, tfLogo) = kernelApi.header()
  css = kernelApi.css()
  provenance = kernelApi.provenance()
  (provenanceHtml, provenanceMd) = getProvenance(form, provenance)

  (
      defaultCondenseType,
      exampleSection,
      exampleSectionText,
      condenseTypes,
      defaultTextFormat,
      textFormats,
  ) = kernelApi.condenseTypes()
  condenseType = form['condensetp'] or defaultCondenseType
  condenseOpts = shapeCondense(condenseTypes, condenseType)
  textFormat = form['textformat'] or defaultTextFormat
  textFormatOpts = shapeFormats(textFormats, textFormat)
  mode = form['mode']

  resultKind = condenseType if form['condensed'] else RESULT

  sectionMessages = ''
  tupleMessages = ''
  queryMessages = ''

  if mode == 'results':
    openedSet = {int(n) for n in form['opened'].split(',')} if form['opened'] else set()
    if form['searchTemplate'] or form['tuples'] or form['sections']:
      (
          table,
          sectionMessages,
          tupleMessages,
          queryMessages,
          start,
          total,
      ) = kernelApi.search(
          form['searchTemplate'],
          form['tuples'],
          form['sections'],
          form['condensed'],
          condenseType,
          textFormat,
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
  else:
    openedSet = set(form['opened'].split(',')) if form['opened'] else set()
    sec0 = form['sec0']
    sec1 = form['sec1']
    sec2 = form['sec2']
    (
        table,
        passages,
    ) = kernelApi.passage(
        sec0,
        sec1,
        textFormat,
        sec2=sec2,
        opened=openedSet,
        withNodes=form['withNodes'],
        **values,
    )
    passages = passageLinks(passages, sec0, sec1)

  writeFormData(form)

  otherJobs = getOtherOptions(form['jobName'])

  descriptionMd = markdown.markdown(
      form['description'], extensions=[
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
    (csvs, context, resultsX) = kernelApi.csvs(
        form['searchTemplate'],
        form['tuples'],
        form['sections'],
        form['condensed'],
        condenseType,
        textFormat,
    )
    csvs = pickle.loads(csvs)
    context = pickle.loads(context)
    resultsX = pickle.loads(resultsX)
    writeCsvs(csvs, context, resultsX, form)

    return template(
        'export',
        dataSource=dataSource,
        css=css,
        descriptionMd=descriptionMd,
        table=table,
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
      textFormatOpts=textFormatOpts,
      defaultTextFormat=defaultTextFormat,
      exampleSection=exampleSection,
      exampleSectionText=exampleSectionText,
      withNodesAtt=withNodesAtt,
      pages=pages,
      passages=passages,
      otherJobs=otherJobs,
      dirMsg=dirMsg,
      EXTENSION=EXTENSION,
      **form,
  )


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
      run(
          debug=debug,
          reloader=debug,
          host='0.0.0.0' if onDocker else config.host,
          port=config.webport,
      )
