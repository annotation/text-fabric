import sys
from importlib import import_module

try:
  dataSource = sys.argv[1]
except Exception:
  print('Pass a data source as first argument')
  sys.exit(1)

try:
  config = import_module(f'.{dataSource}', package='config')
except Exception as e:
  print(e)
  print(f'Data source "{dataSource}" not found')
  sys.exit(1)

try:
  controller = import_module(f'.{dataSource}', package='controllers')
except Exception as e:
  print(e)
  print(f'Controller "{dataSource}" not found')
  sys.exit(1)


from bottle import (post, get, route, template, request, static_file, run)

from tf.service import makeTfConnection

TF = makeTfConnection(config.host, config.port)


@route('/static/<filepath:path>')
def serveStatic(filepath):
  return static_file(filepath)


@post('/<anything:re:.*>')
@get('/<anything:re:.*>')
def serveSearch(anything):
  searchTemplate = request.forms.searchTemplate.replace('\r', '')

  if searchTemplate:
    api = TF.connect()
    (results, context, messages) = api.search(searchTemplate, True)

    table = controller.compose(results, context)
  else:
    table = 'no results'
    searchTemplate = ''
    messages = ''

  return template(
      'index',
      dataSource=dataSource,
      messages=messages.replace('\n', '<br/>'),
      table=table,
      searchTemplate=searchTemplate,
  )


run(
    debug=True,
    reloader=True,
    host=config.host,
    port=config.webport,
)

