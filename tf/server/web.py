import os

from importlib import import_module

import bottle
from bottle import (post, get, route, template, request, static_file, run)

from tf.server.service import makeTfConnection
from tf.miniapi import MiniApi

from tf.server.data import getParam, getDebug

from tf.server.controllers.common import pageLinks, shapeMessages


myDir = os.path.dirname(os.path.abspath(__file__))
bottle.TEMPLATE_PATH = [f'{myDir}/views']


def getStuff(dataSource):
  global controller
  global TF
  try:
    config = import_module(f'.{dataSource}', package='tf.server.config')
  except Exception as e:
    print(e)
    print(f'Data source "{dataSource}" not found')
    return None

  try:
    controller = import_module(f'.{dataSource}', package='tf.server.controllers')
  except Exception as e:
    print(e)
    print(f'Controller "{dataSource}" not found')
    return None

  TF = makeTfConnection(config.host, config.port)
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


@post('/<anything:re:.*>')
@get('/<anything:re:.*>')
def serveSearch(anything):
  searchTemplate = request.forms.searchTemplate.replace('\r', '')
  position = getInt(request.forms.position, default=1)
  batch = getInt(request.forms.batch, default=controller.BATCH)
  pages = ''

  header = controller.header()

  if searchTemplate:
    api = TF.connect()
    (results, context, messages, start, end, total) = api.search(
        searchTemplate,
        batch=batch,
        position=position,
        context=True,
        nodeTypes={controller.CONTAINER_TYPE},
    )
    if results is not None:
      pages = pageLinks(total, position)
    miniApi = MiniApi(**context)

    if messages:
      messages = shapeMessages(messages)

    table = controller.compose(results, start, position, miniApi)
  else:
    table = 'no results'
    searchTemplate = ''
    messages = ''

  return template(
      'index',
      dataSource=dataSource,
      css=controller.C_CSS,
      header=header,
      messages=messages,
      table=table,
      searchTemplate=searchTemplate,
      batch=batch,
      position=position,
      pages=pages,
  )


def runweb(dataSource, debug=False):
  config = getStuff(dataSource)
  if config is not None:
    run(
        debug=debug,
        reloader=debug,
        host=config.host,
        port=config.webport,
    )


if __name__ == "__main__":
  dataSource = getParam()
  debug = getDebug()
  if dataSource is not None:
    runweb(dataSource, debug=debug)
