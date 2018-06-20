import sys
import rpyc
from rpyc.utils.server import ThreadedServer

from tf.apphelpers import runSearch, runSearchCondensed, compose
from .common import getConfig

TIMEOUT = 120

TF_DONE = 'TF setup done.'


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
  config = getConfig(dataSource)
  if config is None:
    return None

  print(f'Setting up Text-Fabric service for {locations} / {modules}')
  extraApi = config.extraApi(locations, modules)
  extraApi.api.reset()
  cache = {}
  print(f'{TF_DONE}\nListening at port {port}')
  sys.stdout.flush()

  class TfService(rpyc.Service):
    def on_connect(self, conn):
      self.extraApi = extraApi
      pass

    def on_disconnect(self, conn):
      self.extraApi = None
      pass

    def exposed_header(self):
      extraApi = self.extraApi
      return extraApi.header()

    def exposed_css(self, appDir=None):
      extraApi = self.extraApi
      return extraApi.loadCSS()

    def exposed_condenseTypes(self):
      extraApi = self.extraApi
      api = extraApi.api
      return (extraApi.condenseType, api.C.levels.data)

    def exposed_search(
        self, query, condensed, condenseType, batch,
        position=1, opened=set(),
        withNodes=False,
        linked=1,
        **options,
    ):
      extraApi = self.extraApi
      api = self.extraApi.api

      (queryResults, messages) = (
          runSearchCondensed(api, query, cache, condenseType)
          if condensed and condenseType else
          runSearch(api, query, cache)
      )

      if messages:
        queryResults = ()
      total = len(queryResults)

      (start, end) = batchAround(total, position, batch)

      selectedResults = queryResults[start - 1:end]

      before = {n for n in opened if n > 0 and n < start}
      after = {n for n in opened if n > end and n <= len(queryResults)}
      beforeResults = tuple((n, queryResults[n - 1]) for n in sorted(before))
      afterResults = tuple((n, queryResults[n - 1]) for n in sorted(after))

      allResults = (
          beforeResults +
          tuple((i + start, r) for (i, r) in enumerate(selectedResults)) +
          afterResults
      )
      table = compose(
          extraApi,
          allResults, start, position, opened,
          condensed,
          condenseType,
          withNodes=withNodes,
          linked=linked,
          **options,
      )
      return (table, messages, start, total)

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
