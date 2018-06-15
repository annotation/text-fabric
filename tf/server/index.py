import os

from importlib import import_module

from bottle import (post, get, route, template, request, static_file, run)

from tf.service import makeTfConnection
from tf.miniapi import MiniApi

from tf.server.serveTf import getParam

from tf.server.controllers.common import pageLinks


tpl = '''
<html>
    <head>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
        <title>Text-Fabric {{dataSource}}</title>
        <meta name="application-name" content="Text-Fabric Search Box"/>

        <link rel="stylesheet" href="/server/static/main.css"/>
        {{!css}}
    </head>
    <body>
        <form id="go" method="post">
            <label>Query</label>
            <textarea name="searchTemplate">{{searchTemplate}}</textarea>
            Goto result <input type="text" id="pos" name="position" value="{{position}}"/> with
            <input type="text" name="batch" value="{{batch}}"/> results per page
            <button type="submit">Go</button>
        </form>
        <div>
            <label>Messages</label>
            <div class="messages">
                {{!messages}}
            </div>
        </div>
        <div>
            <label>Results</label>
            <div class="resultlist">
                {{!table}}
            </div>
        </div>
        <div>
            <label>Navigation</label>
            <div class="navigation">
                {{!pages}}
            </div>
        </div>
        <div>
            <label>Detail</label>
            <div class="resultitem"/>
        </div>
        <script src="/server/static/jquery.js"></script>
        <script src="/server/static/tf.js"/></script>
    </body>
</html>
'''

myDir = os.path.dirname(os.path.abspath(__file__))


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

  if searchTemplate:
    api = TF.connect()
    (results, context, messages, start, end, total) = api.search(
        searchTemplate,
        batch=batch,
        position=position,
        context=True,
    )
    if results is not None:
      pages = pageLinks(total, position)
    print('make miniapi')
    miniApi = MiniApi(**context)
    print('miniapi ready')

    table = controller.compose(results, start, position, miniApi)
  else:
    table = 'no results'
    searchTemplate = ''
    messages = ''

  return template(
      tpl,
      dataSource=dataSource,
      css=controller.C_CSS,
      messages=messages.replace('\n', '<br/>'),
      table=table,
      searchTemplate=searchTemplate,
      batch=batch,
      position=position,
      pages=pages,
  )


def runweb(dataSource):
  config = getStuff(dataSource)
  if config is not None:
    run(
        debug=True,
        reloader=False,
        host=config.host,
        port=config.webport,
    )


if __name__ == "__main__":
  dataSource = getParam()
  if dataSource is not None:
    runweb(dataSource)
