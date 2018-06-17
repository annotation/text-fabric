from importlib import import_module

import rpyc
from rpyc.utils.server import ThreadedServer

TIMEOUT = 120


def batchAround(nResults, position, batch):
  halfBatch = int((batch + 1) / 2)
  left = min(max(position - halfBatch, 1), nResults)
  right = max(min(position + halfBatch, nResults), 1)
  discrepancy = batch - (right - left + 1)
  if discrepancy != 0:
    right += discrepancy
  if right > nResults:
    right = nResults
  return (left, right)


def makeTfServer(dataSource, locations, modules, port):
  from tf.context import gatherContext
  try:
    config = import_module(f'.{dataSource}', package='tf.server.config')
  except Exception as e:
    print(e)
    print(f'API "{dataSource}" not found')
    return None
  print(f'Setting up Text-Fabric service for {locations} / {modules}')
  maxiApi = config.maxiApi(locations, modules)
  maxiApi.api.reset()
  cache = {}
  print(f'TF setup done.\nListening at port {port}')

  class TfService(rpyc.Service):
    def on_connect(self, conn):
      self.maxiApi = maxiApi
      pass

    def on_disconnect(self, conn):
      self.maxiApi = None
      pass

    def exposed_pretty(
        self, tupleDict,
    ):
      maxiApi = self.maxiApi
      return {
          seq: maxiApi.prettyTuple(tupleDict[seq], seq)
          for seq in tupleDict
      }

    def exposed_search(
        self, query, batch,
        position=1, opened=set(),
        context=None, nodeTypes=None,
    ):

      maxiApi = self.maxiApi
      api = maxiApi.api

      if query in cache:
        (queryResults, messages) = cache[query]
      else:
        S = api.S
        (queryResults, messages) = S.search(query, msgCache=True)
        queryResults = sorted(queryResults)
        cache[query] = (queryResults, messages)

      theContext = {}
      if messages:
        queryResults = ()
      total = len(queryResults)

      (start, end) = batchAround(total, position, batch)

      selectedResults = queryResults[start - 1:end]

      intOpened = {int(n) for n in opened if n.isdecimal()}
      before = {n for n in intOpened if n > 0 and n < start}
      after = {n for n in intOpened if n > end and n <= len(queryResults)}
      beforeResults = tuple((str(n), queryResults[n - 1]) for n in sorted(before))
      afterResults = tuple((str(n), queryResults[n - 1]) for n in sorted(after))

      allResults = (
          beforeResults +
          tuple((str(i + start), r) for (i, r) in enumerate(selectedResults)) +
          afterResults
      )
      if allResults:
        theContext = gatherContext(
            api, context, nodeTypes,
            (r[1] for r in allResults)
        )
      return (allResults, theContext, messages, start, total)

  return ThreadedServer(TfService, port=port, protocol_config={
      'allow_public_attrs': True,
      'sync_request_timeout': TIMEOUT,
  })


def makeTfConnection(host, port):
  class TfConnection(object):
    def connect(self):
      connection = rpyc.connect(host, port)
      self.connection = connection
      return connection.root

  return TfConnection()
