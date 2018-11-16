import sys
import pickle
import rpyc
from rpyc.utils.server import ThreadedServer

from ..core.helpers import console
from ..applib.appmake import (
    findAppConfig,
    findAppClass,
)
from ..applib.apphelpers import (
    runSearch, runSearchCondensed, compose, composeP, getContext, getResultsX
)
from .common import (getParam, getModules, getCheck, getLocalClones)

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


def makeTfKernel(dataSource, moduleRefs, lgc, check, port):
  config = findAppConfig(dataSource)
  if config is None:
    return None
  appClass = findAppClass(dataSource)
  if appClass is None:
    return None

  console(f'Setting up TF kernel for {dataSource} {moduleRefs}')
  app = appClass(
      dataSource,
      asApp=True,
      mod=moduleRefs,
      version=config.VERSION,
      lgc=lgc,
      check=check,
  )

  if not app.api:
    console(f'{TF_ERROR}')
    return False
  app.api.reset()
  cache = {}
  console(f'{TF_DONE}\nListening at port {port}')

  class TfKernel(rpyc.Service):

    def on_connect(self, conn):
      self.app = app
      pass

    def on_disconnect(self, conn):
      self.app = None
      pass

    def exposed_provenance(self):
      app = self.app
      return app.provenance

    def exposed_header(self):
      app = self.app
      return app.header()

    def exposed_css(self, appDir=None):
      app = self.app
      return app.loadCss()

    def exposed_condenseTypes(self):
      app = self.app
      api = app.api
      return (
          app.condenseType,
          app.exampleSection,
          app.exampleSectionText,
          api.C.levels.data,
          app.api.T.defaultFormat,
          tuple(fmt for fmt in app.api.T.formats if fmt.startswith('text-')),
      )

    def exposed_passage(
        self,
        sec0,
        sec1,
        textFormat,
        sec2=None,
        opened=set(),
        withNodes=False,
        **options,
    ):
      app = self.app
      api = app.api
      F = api.F
      L = api.L
      T = api.T
      sectionFeatureTypes = T.sectionFeatureTypes
      sec0Type = T.sectionTypes[0]
      sec1Type = T.sectionTypes[1]
      sec2Type = T.sectionTypes[2]
      passage = ''
      if sec0 and sec1:
        if sectionFeatureTypes[0] == 'int':
          sec0 = int(sec0)
        if sectionFeatureTypes[1] == 'int':
          sec1 = int(sec1)
        node = T.nodeFromSection((sec0, sec1))
        items = L.d(node, otype=sec2Type) if node else []
        passage = composeP(
            app,
            items,
            textFormat,
            opened,
            sec2,
            withNodes=withNodes,
            **options,
        )
      sec0s = tuple(T.sectionFromNode(s)[0] for s in F.otype.s(sec0Type))
      sec1s = ()
      if sec0:
        sec0Node = T.nodeFromSection((sec0, ))
        sec1s = tuple(T.sectionFromNode(s)[1] for s in L.d(sec0Node, otype=sec1Type))
      passages = (sec0s, sec1s)
      return (passage, passages)

    def exposed_search(
        self,
        query,
        tuples,
        sections,
        condensed,
        condenseType,
        textFormat,
        batch,
        position=1,
        opened=set(),
        withNodes=False,
        linked=1,
        **options,
    ):
      app = self.app
      api = app.api

      total = 0

      sectionResults = []
      sectionMessages = []
      if sections:
        sectionLines = sections.split('\n')
        for (i, sectionLine) in enumerate(sectionLines):
          sectionLine = sectionLine.strip()
          (message, node) = app.nodeFromDefaultSection(sectionLine)
          if message:
            sectionMessages.append(message)
          else:
            sectionResults.append((-i - 1, (node, )))
        total += len(sectionResults)
      sectionResults = tuple(sectionResults)
      sectionMessages = '\n'.join(sectionMessages)

      tupleResults = ()
      tupleMessages = ''
      if tuples:
        tupleLines = tuples.split('\n')
        try:
          tupleResults = tuple((-i - 1 - total, tuple(int(n)
                                                      for n in t.strip().split(',')))
                               for (i, t) in enumerate(tupleLines)
                               if t.strip())
        except Exception as e:
          tupleMessages = f'{e}'
        total += len(tupleResults)

      queryResults = ()
      queryMessages = ''
      if query:
        (queryResults, queryMessages, features) = (
            runSearchCondensed(api, query, cache, condenseType)
            if condensed and condenseType else runSearch(api, query, cache)
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

      # yapf: disable
      allResults = (
          ((None, 'sections'),)
          + sectionResults
          + ((None, 'nodes'),)
          + tupleResults
          + ((None, 'results'),)
          + beforeResults
          + tuple((i + start, r) for (i, r) in enumerate(selectedResults))
          + afterResults
      )
      table = compose(
          app,
          allResults, features, start, position, opened,
          condensed,
          condenseType,
          textFormat,
          withNodes=withNodes,
          linked=linked,
          **options,
      )
      return (table, sectionMessages, tupleMessages, queryMessages, start, total)

    def exposed_csvs(self, query, tuples, sections, condensed, condenseType, textFormat):
      app = self.app
      api = self.app.api

      sectionResults = []
      if sections:
        sectionLines = sections.split('\n')
        for sectionLine in sectionLines:
          sectionLine = sectionLine.strip()
          (message, node) = app.nodeFromDefaultSection(sectionLine)
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
        except Exception:
          pass

      queryResults = ()
      features = ()
      if query:
        (queryResults, queryMessages, features) = (
            runSearch(api, query, cache)
        )
        (queryResultsC, queryMessagesC, featuresC) = (
            runSearchCondensed(api, query, cache, condenseType)
            if condensed and condenseType else
            (None, None, None)
        )

        if queryMessages:
          queryResults = ()
        if queryMessagesC:
          queryResultsC = ()

      csvs = (
          ('sections', sectionResults),
          ('nodes', tupleResults),
          ('results', queryResults),
      )
      if condensed and condenseType:
        csvs += (
            ('resultsCondensed', queryResultsC),
        )
      context = getContext(
          api,
          (
              allNodes(sectionResults)
              | allNodes(tupleResults)
              | allNodes(queryResultsC if condensed and condenseType else queryResults)
          )
      )
      resultsX = getResultsX(
          api,
          queryResults,
          features,
          app.noDescendTypes,
          fmt=textFormat,
      )
      return (pickle.dumps(csvs), pickle.dumps(context), pickle.dumps(resultsX))

  return ThreadedServer(TfKernel, port=port, protocol_config={
      # 'allow_pickle': True,
      # 'allow_public_attrs': True,
      'sync_request_timeout': TIMEOUT,
  })


def makeTfConnection(host, port):
  class TfConnection(object):
    def connect(self):
      connection = rpyc.connect(host, port)
      self.connection = connection
      return connection.root

  return TfConnection()


def main(cargs=sys.argv):
  dataSource = getParam(cargs=cargs, interactive=True)
  modules = getModules(cargs=cargs)
  lgc = getLocalClones(cargs=cargs)
  check = getCheck(cargs=cargs)

  if dataSource is not None:
    moduleRefs = modules[6:] if modules else ''
    config = findAppConfig(dataSource)
    if config is not None:
      kernel = makeTfKernel(dataSource, moduleRefs, lgc, check, config.port)
      if kernel:
        kernel.start()


if __name__ == "__main__":
  main()
