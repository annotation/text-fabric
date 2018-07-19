import sys
import pickle
from multiprocessing.managers import BaseManager

from tf.apphelpers import (
    runSearch, runSearchCondensed,
    compose, getContext
)
from .common import getParam, getConfig

TIMEOUT = 120

TF_DONE = 'TF setup done.'
TF_ERROR = 'Could not set up TF'


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


def allNodes(table):
  allN = set()
  for tup in table:
    allN |= set(tup)
  return allN


class TfKernel(BaseManager):
  pass


def makeTfKernel(dataSource, locations, modules, port):
  config = getConfig(dataSource)
  if config is None:
    return None

  locRep = locations if type(locations) is str else '\n\t\t'.join(locations)
  modRep = modules if type(modules) is str else '\n\t\t'.join(modules)
  print(f'Setting up TF kernel for:\n\tlocations:\n\t\t{locRep}\n\tmodules:\n\t\t{modRep}')
  extraApi = config.extraApi(locations, modules)
  if not extraApi:
    print(f'{TF_ERROR}')
    sys.stdout.flush()
    return False
  extraApi.api.reset()
  cache = {}
  print(f'{TF_DONE}\nListening at port {port}')
  sys.stdout.flush()

  class ExtraApi(object):

    def header(self):
      return extraApi.header()

    def css(self, appDir=None):
      return extraApi.loadCSS()

    def condenseTypes(self):
      api = extraApi.api
      return (extraApi.condenseType, extraApi.exampleSection, api.C.levels.data)

    def search(
        self, query, tuples, sections, condensed, condenseType, batch,
        position=1, opened=set(),
        withNodes=False,
        linked=1,
        **options,
    ):
      api = self.extraApi.api

      total = 0

      sectionResults = []
      sectionMessages = []
      if sections:
        sectionLines = sections.split('\n')
        for (i, sectionLine) in enumerate(sectionLines):
          sectionLine = sectionLine.strip()
          (message, node) = extraApi.nodeFromDefaultSection(sectionLine)
          if message:
            sectionMessages.append(message)
          else:
            sectionResults.append((-i - 1, (node,)))
        total += len(sectionResults)
      sectionResults = tuple(sectionResults)
      sectionMessages = '\n'.join(sectionMessages)

      tupleResults = ()
      tupleMessages = ''
      if tuples:
        tupleLines = tuples.split('\n')
        try:
          tupleResults = tuple(
              (
                  -i - 1 - total,
                  tuple(
                      int(n) for n in t.strip().split(',')
                  )
              )
              for (i, t) in enumerate(tupleLines)
              if t.strip()
          )
        except Exception as e:
          tupleMessages = f'{e}'
        total += len(tupleResults)

      queryResults = ()
      queryMessages = ''
      if query:
        (queryResults, queryMessages) = (
            runSearchCondensed(api, query, cache, condenseType)
            if condensed and condenseType else
            runSearch(api, query, cache)
        )

        if queryMessages:
          queryResults = ()
        total += len(queryResults)

      (start, end) = batchAround(total, position, batch)

      selectedResults = queryResults[start - 1:end]
      opened = set(opened)

      before = {n for n in opened if n > 0 and n < start}
      after = {n for n in opened if n > end and n <= len(queryResults)}
      beforeResults = tuple((n, queryResults[n - 1]) for n in sorted(before))
      afterResults = tuple((n, queryResults[n - 1]) for n in sorted(after))

      allResults = (
          ((None, 'sections'),) +
          sectionResults +
          ((None, 'nodes'),) +
          tupleResults +
          ((None, 'results'),) +
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
      return (table, sectionMessages, tupleMessages, queryMessages, start, total)

    def csvs(self, query, tuples, sections, condensed, condenseType):
      api = self.extraApi.api

      sectionResults = []
      if sections:
        sectionLines = sections.split('\n')
        for sectionLine in sectionLines:
          sectionLine = sectionLine.strip()
          (message, node) = extraApi.nodeFromDefaultSection(sectionLine)
          if not message:
            sectionResults.append((node,))
      sectionResults = tuple(sectionResults)

      tupleResults = ()
      if tuples:
        tupleLines = tuples.split('\n')
        try:
          tupleResults = tuple(
              tuple(
                  int(n) for n in t.strip().split(',')
              )
              for t in tupleLines
              if t.strip()
          )
        except Exception as e:
          pass

      queryResults = ()
      if query:
        (queryResults, queryMessages) = (
            runSearchCondensed(api, query, cache, condenseType)
            if condensed and condenseType else
            runSearch(api, query, cache)
        )

        if queryMessages:
          queryResults = ()

      csvs = (
          ('sections', sectionResults),
          ('nodes', tupleResults),
          ('results', queryResults),
      )
      context = getContext(
          api,
          allNodes(sectionResults) | allNodes(tupleResults) | allNodes(queryResults)
      )
      return (pickle.dumps(csvs), pickle.dumps(context))

  TfKernel.register('EA', ExtraApi)

  manager = TfKernel(address=('', port), authkey=b'x')
  # ea = manager.ExtraApi()
  kernel = manager.get_server()
  return kernel


def makeTfConnection(host, port):
  class TfConnection(object):
    def connect(self):
      with TfKernel(address=(host, port), authkey=b'x') as manager:
        manager.connect()
        print(manager.__dict__)
        extraApi = manager.EA()
      return extraApi

  return TfConnection()


def main(cargs=sys.argv):
  dataSource = getParam(cargs=cargs, interactive=True)
  if dataSource is not None:
    config = getConfig(dataSource)
    if config is not None:
      kernel = makeTfKernel(dataSource, config.locations, config.modules, config.port)
      if kernel:
        kernel.serve_forever()


if __name__ == "__main__":
  main()
