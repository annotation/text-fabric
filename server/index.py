from bottle import (
    post, get, route, template,
    request,
    static_file,
    run
)

from tf.service import makeTfConnection

from controllers import compose

HOST = 'localhost'
PORT = 18981

TF = makeTfConnection(HOST, PORT)


def getq(name):
    return request.query.get(name, '')


@route('/static/<filepath:path>')
def serveStatic(filepath):
    return static_file(filepath)


@post('/<anything:re:.*>')
@get('/<anything:re:.*>')
def serveSearch(anything):
    searchTemplate = getq('searchTemplate')

    if searchTemplate:
        api = TF.connect()
        (results, context) = api.search(searchTemplate, True)

        results = tuple(results)
        context = {feature: context[feature] for feature in context}

        table = compose(results, context)
    else:
        table = 'no results'
        searchTemplate = ''

    return template(
        'index',
        table=table,
        searchTemplate=searchTemplate,
    )


run(
    debug=True,
    reloader=True,
    host='localhost',
    port=8001,
)
