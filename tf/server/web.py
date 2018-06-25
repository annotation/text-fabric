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
  tool = f'{NAME} {VERSION}'
  toolDoi = f'<a href="{DOI_URL}">{DOI}</a>'

  return f'''
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
      <div class="pval">{prov["corpus"]} {prov["corpusDoi"]}</div>
    </div>
    <div class="pline">
      <div class="pname">Tool:</div>
      <div class="pval">{tool} {toolDoi}</div>
    </div>
  '''


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
  thisFileName = form['fileName'] or ''
  with open(f'{dataSource}-{thisFileName}.tfquery', 'w') as tfj:
    json.dump(form, tfj)


def readFormData(source):
  sourceFile = f'{dataSource}-{source}.tfquery'
  if os.path.exists(sourceFile):
    with open(sourceFile) as tfj:
      form = json.load(tfj)
    for item in '''
        searchTemplate tuples sections fileName fileNameHidden
        condensetp opened author title
    '''.strip().split():
      if form.get(item, None) is None:
        form[item] = ''
    return form
  return None


def getPrevOptions(current):
  prevs = glob(f'{dataSource}-*.tfquery')
  options = ['<option value=''>none</option>']
  for prev in prevs:
    prevRep = prev[0:-8].split('-', 1)[1]
    if prevRep == current:
      continue
    options.append(f'<option value="{prevRep}">{prevRep}</option>')
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
  if form['previous'] != '':
    previous = readFormData(form['previous'])
    if previous is not None:
      form = previous
  form['previous'] = ''
  condensedAtt = ' checked ' if form['condensed'] else ''
  withNodesAtt = ' checked ' if form['withNodes'] else ''

  openedSet = {int(n) for n in form['opened'].split(',')} if form['opened'] else set()

  options = config.options
  values = getValues(options, form)

  pages = ''

  api = TF.connect()
  header = api.header()
  css = api.css()
  provenance = getProvenance(form)

  (defaultCondenseType, condenseTypes) = api.condenseTypes()
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

  return (
      template(
          'index',
          dataSource=dataSource,
          css=css,
          header=header,
          options=shapeOptions(options, values),
          tupleMessages=tupleMessages,
          queryMessages=queryMessages,
          table=table,
          condensedAtt=condensedAtt,
          condenseOpts=condenseOpts,
          withNodesAtt=withNodesAtt,
          pages=pages,
          prevOptions=prevOptions,
          **form,
      )
      if not form['export'] else
      template(
          'export',
          dataSource=dataSource,
          css=css,
          descriptionMd=descriptionMd,
          table=table,
          condenseType=condenseType,
          colofon=header,
          provenance=provenance,
          **form,
      )
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
