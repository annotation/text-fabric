from importlib import import_module

from bottle import (post, get, route, template, request, static_file, run)

from tf.service import makeTfConnection
from tf.miniapi import MiniApi

from serveTf import getParam


def getStuff(dataSource):
  global controller
  global TF
  try:
    config = import_module(f'.{dataSource}', package='config')
  except Exception as e:
    print(e)
    print(f'Data source "{dataSource}" not found')
    return None

  try:
    controller = import_module(f'.{dataSource}', package='controllers')
  except Exception as e:
    print(e)
    print(f'Controller "{dataSource}" not found')
    return None

  TF = makeTfConnection(config.host, config.port)
  return config


@route('/static/<filepath:path>')
def serveStatic(filepath):
  return static_file(filepath)


@post('/<anything:re:.*>')
@get('/<anything:re:.*>')
def serveSearch(anything):
  searchTemplate = request.forms.searchTemplate.replace('\r', '')

  if searchTemplate:
    api = TF.connect()
    (results, context, messages) = api.search(searchTemplate, position=0, context=True)
    print('make miniapi')
    miniApi = MiniApi(**context)
    print('miniapi ready')

    table = controller.compose(results, miniApi)
  else:
    table = 'no results'
    searchTemplate = ''
    messages = ''

  return template(
      'index',
      dataSource=dataSource,
      css=controller.C_CSS,
      messages=messages.replace('\n', '<br/>'),
      table=table,
      searchTemplate=searchTemplate,
  )


def runweb(dataSource):
  config = getStuff(dataSource)
  if config is not None:
    run(
        debug=True,
        reloader=True,
        host=config.host,
        port=config.webport,
    )


if __name__ == "__main__":
  dataSource = getParam()
  if dataSource is not None:
    runweb(dataSource)
