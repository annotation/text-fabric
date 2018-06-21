import os

import bottle
from bottle import (post, get, route, template, request, static_file, run)

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

  (defaultCondenseType, condenseTypes) = api.condenseTypes()
  condenseType = request.forms.condensetp or defaultCondenseType
  condenseOpts = shapeCondense(condenseTypes, condenseType)

  resultKind = condenseType if condensed else RESULT
  resultPl = 's' if batch != 1 else ''
  resultItems = f'{batch} {resultKind}{resultPl}'

  if searchTemplate:
    (table, messages, start, total) = api.search(
        searchTemplate,
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

    if messages:
      messages = shapeMessages(messages)
  else:
    table = f'no {resultKind}s'
    searchTemplate = ''
    messages = ''

  fileName = f'{dataSource}-{resultItems} around {position}'

  return (
      template(
          'index',
          dataSource=dataSource,
          css=css,
          header=header,
          options=shapeOptions(options, values),
          messages=messages,
          table=table,
          searchTemplate=searchTemplate,
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
          table=table,
          condensed=condensed,
          condenseType=condenseType,
          batch=batch,
          position=position,
          colofon=header,
          fileName=fileName,
      )
  )


if __name__ == "__main__":
  dataSource = getParam()
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
