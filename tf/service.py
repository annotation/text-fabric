import rpyc
from rpyc.utils.server import ThreadedServer

BATCH = 100


def makeTfServer(locations, modules, port):
  from tf.fabric import Fabric
  from tf.context import gatherContext
  print(f'Setting up Text-Fabric service for {locations} / {modules}')
  TF = Fabric(locations=locations, modules=modules, silent=True)
  api = TF.load('', silent=True)
  allFeatures = TF.explore(silent=True, show=True)
  loadableFeatures = allFeatures['nodes'] + allFeatures['edges']
  TF.load(loadableFeatures, add=True, silent=True)
  api.reset()
  cache = {}
  print(f'TF setup done.\nListening at port {port}')

  class TfService(rpyc.Service):
    def on_connect(self, conn):
      self.api = api
      pass

    def on_disconnect(self, conn):
      self.api = None
      pass

    def exposed_search(self, query, position=None, batch=BATCH, context=None):
      print('start search')
      api = self.api
      if query in cache:
        (queryResults, messages) = cache[query]
        print('results from cache')
      else:
        S = api.S
        (queryResults, messages) = S.search(query, msgCache=True)
        print('results from search')
        queryResults = sorted(queryResults)
        print('results sorted')
        cache[query] = (queryResults, messages)
        print('results cached')

      theContext = {}
      if messages:
        queryResults = ()
      if position is not None:
        if position >= len(queryResults):
          queryResults = ()
          messages = f'position {position} is past last result at {len(queryResults) - 1}'
        else:
          queryResults = queryResults[position:position + batch]
      if queryResults:
        print('start gather context')
        theContext = gatherContext(api, context, queryResults)
        print('context gathered')
      return (queryResults, theContext, messages)

  return ThreadedServer(TfService, port=port, protocol_config={'allow_public_attrs': True})


def makeTfConnection(host, port):
  class TfConnection(object):
    def connect(self):
      connection = rpyc.connect(host, port)
      self.connection = connection
      return connection.root

  return TfConnection()
