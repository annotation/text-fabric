import os
import datetime
import time

import markdown

import bottle
from bottle import (post, get, route, template, request, static_file, run)

from tf.fabric import NAME, VERSION, DOI, DOI_URL
from tf.server.data import makeTfConnection
from tf.server.common import (
    getParam, getDebug, getConfig, getAppDir, getValues,
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


def getProvenance():
  utc_offset_sec = time.altzone if time.localtime().tm_isdst else time.timezone
  utc_offset = datetime.timedelta(seconds=-utc_offset_sec)
  now = datetime.datetime.now().replace(
      microsecond=0, tzinfo=datetime.timezone(offset=utc_offset)
  ).isoformat()

  prov = config.PROVENANCE
  tool = f'{NAME} {VERSION}'
  toolDoi = f'<a href="{DOI_URL}">{DOI}</a>'

  return f'''
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
  searchTemplate = request.forms.searchTemplate.replace('\r', '')
  tuples = request.forms.tuples.replace('\r', '')
  fileName = request.forms.fileName.strip()
  description = request.forms.description.replace('\r', '')
  withNodes = request.forms.withNodes
  condensed = request.forms.condensed
  export = request.forms.export
  expandAll = request.forms.expandAll
  linked = getInt(request.forms.linked, default=1)
  condensedAtt = ' checked ' if condensed else ''
  withNodesAtt = ' checked ' if withNodes else ''

  options = config.options
  values = getValues(options, request.forms)

  openedStr = request.forms.opened
  position = getInt(request.forms.position, default=1)
  batch = getInt(request.forms.batch, default=BATCH)
  pages = ''

  opened = {int(n) for n in openedStr.split(',')} if openedStr else set()

  api = TF.connect()
  header = api.header()
  css = api.css()
  provenance = getProvenance()

  (defaultCondenseType, condenseTypes) = api.condenseTypes()
  condenseType = request.forms.condensetp or defaultCondenseType
  condenseOpts = shapeCondense(condenseTypes, condenseType)

  resultKind = condenseType if condensed else RESULT
  resultPl = 's' if batch != 1 else ''
  resultItems = f'{batch} {resultKind}{resultPl}'

  if searchTemplate or tuples:
    (table, tupleMessages, queryMessages, start, total) = api.search(
        searchTemplate,
        tuples,
        condensed,
        condenseType,
        batch,
        position=position,
        opened=opened,
        withNodes=withNodes,
        linked=linked,
        **values,
    )
    if table is not None:
      pages = pageLinks(total, position)

    if tupleMessages:
      tupleMessages = shapeMessages(tupleMessages)
    if queryMessages:
      queryMessages = shapeMessages(queryMessages)
  else:
    table = f'no {resultKind}s'
    searchTemplate = ''
    tupleMessages = ''
    queryMessages = ''

  if not fileName:
    fileName = f'{dataSource}-{resultItems} around {position}'

  descriptionMd = markdown.markdown(
      description,
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
          searchTemplate=searchTemplate,
          tuples=tuples,
          description=description,
          condensedAtt=condensedAtt,
          condenseOpts=condenseOpts,
          withNodesAtt=withNodesAtt,
          expandAll=expandAll,
          linked=linked,
          batch=batch,
          position=position,
          opened=openedStr,
          pages=pages,
          test=condensed and condenseType,
          fileName=fileName,
      )
      if not export else
      template(
          'export',
          dataSource=dataSource,
          css=css,
          searchTemplate=searchTemplate,
          description=descriptionMd,
          tuples=tuples,
          table=table,
          condensed=condensed,
          condenseType=condenseType,
          batch=batch,
          position=position,
          colofon=header,
          provenance=provenance,
          fileName=fileName,
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
