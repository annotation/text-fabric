import sys
import pickle
from functools import reduce

import rpyc
from rpyc.utils.server import ThreadedServer

from ..core.helpers import console
from ..applib.app import findApp, findAppConfig, findAppClass
from ..applib.highlight import getPassageHighlights
from ..applib.search import runSearch, runSearchCondensed
from ..applib.display import getResultsX
from ..applib.tables import compose, composeP, composeT

from .command import (
    argCheck,
    argLocalClones,
    argModules,
    argSets,
    argParam,
)

TF_DONE = 'TF setup done.'
TF_ERROR = 'Could not set up TF'


# KERNEL CREATION

def makeTfKernel(dataSource, appDir, commit, moduleRefs, setFile, lgc, check, port):
  config = findAppConfig(dataSource, appDir)
  if config is None:
    return None
  appClass = findAppClass(dataSource, appDir)
  if appClass is None:
    return None

  console(f'Setting up TF kernel for {dataSource} {moduleRefs} {setFile}')
  app = appClass(
      dataSource,
      appDir,
      commit,
      _asApp=True,
      mod=moduleRefs,
      setFile=setFile,
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

    def exposed_monitor(self):
      app = self.app
      api = app.api
      S = api.S

      searchExe = getattr(S, 'exe', None)
      if searchExe:
        searchExe = searchExe.outerTemplate

      msgCache = api.cache(_asString=True)

      data = dict(
          searchExe=searchExe,
          msgCache=msgCache,
      )
      return data

    def exposed_header(self):
      app = self.app
      return app.header()

    def exposed_provenance(self):
      app = self.app
      appProvenance = (
          (
              ('name', dataSource),
              ('commit', commit),
          ),
      )
      return (appProvenance, app.provenance)

    def exposed_setNames(self):
      app = self.app
      return (
          tuple(sorted(app.sets.keys())) if hasattr(app, 'sets') and type(app.sets) is dict else ()
      )

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
        features,
        query,
        sec2=None,
        opened=set(),
        getx=None,
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
        if getx is not None:
          if sectionFeatureTypes[2] == 'int':
            getx = int(getx)
        node = T.nodeFromSection((sec0, sec1))
        items = L.d(node, otype=sec2Type) if node else []
        highlights = getPassageHighlights(app, node, query, cache)
        passage = composeP(
            app,
            features,
            items,
            opened,
            sec2,
            getx=getx,
            highlights=highlights,
            **options,
        )
      sec0s = tuple(T.sectionFromNode(s)[0] for s in F.otype.s(sec0Type))
      sec1s = ()
      if sec0:
        sec0Node = T.nodeFromSection((sec0, ))
        sec1s = tuple(T.sectionFromNode(s)[1] for s in L.d(sec0Node, otype=sec1Type))
      return (passage, (sec0s, sec1s))

    def exposed_rawSearch(self, query):
      rawSearch = self.app.api.S.search

      (results, messages) = rawSearch(query, msgCache=True)
      if messages:
        # console(messages, error=True)
        results = ()
      else:
        results = tuple(sorted(results))
        # console(f'{len(results)} results')
      return (results, messages)

    def exposed_table(
        self,
        kind,
        task,
        features,
        opened=set(),
        getx=None,
        **options,
    ):
      app = self.app

      if kind == 'sections':
        results = []
        messages = []
        if task:
          lines = task.split('\n')
          for (i, line) in enumerate(lines):
            line = line.strip()
            node = app.nodeFromSectionStr(line)
            if type(node) is not int:
              messages.append(str(node))
            else:
              results.append((i + 1, (node, )))
        results = tuple(results)
        messages = '\n'.join(messages)
      elif kind == 'tuples':
        results = ()
        messages = ''
        if task:
          lines = task.split('\n')
          try:
            results = tuple((i + 1, tuple(int(n)
                                          for n in t.strip().split(',')))
                            for (i, t) in enumerate(lines)
                            if t.strip())
          except Exception as e:
            messages = f'{e}'

      # yapf: disable
      allResults = (
          ((None, kind),)
          + results
      )
      table = composeT(
          app,
          features,
          allResults,
          opened,
          getx=getx,
          **options,
      )
      return (table, messages)

    def exposed_search(
        self,
        query,
        batch,
        position=1,
        opened=set(),
        getx=None,
        **options,
    ):
      app = self.app
      display = app.display
      d = display.get(options)

      total = 0

      results = ()
      messages = ''
      if query:
        (results, messages, features) = (
            runSearchCondensed(app, query, cache, d.condenseType)
            if d.condensed and d.condenseType else runSearch(app, query, cache)
        )

        if messages:
          results = ()
        total += len(results)

      (start, end) = _batchAround(total, position, batch)

      selectedResults = results[start - 1:end]
      opened = set(opened)

      before = {n for n in opened if n > 0 and n < start}
      after = {n for n in opened if n > end and n <= len(results)}
      beforeResults = tuple((n, results[n - 1]) for n in sorted(before))
      afterResults = tuple((n, results[n - 1]) for n in sorted(after))

      # yapf: disable
      allResults = (
          ((None, 'results'),)
          + beforeResults
          + tuple((i + start, r) for (i, r) in enumerate(selectedResults))
          + afterResults
      )
      features = set(reduce(
          set.union,
          (x[1] for x in features),
          set(),
      ))
      featureStr = ' '.join(sorted(features))
      table = compose(
          app,
          allResults,
          featureStr,
          position,
          opened,
          start=start,
          getx=getx,
          **options,
      )
      return (table, messages, featureStr, start, total)

    def exposed_csvs(self, query, tuples, sections, **options):
      app = self.app
      display = app.display
      d = display.get(options)

      api = self.app.api

      sectionResults = []
      if sections:
        sectionLines = sections.split('\n')
        for sectionLine in sectionLines:
          sectionLine = sectionLine.strip()
          node = app.nodeFromSectionStr(sectionLine)
          if type(node) is int:
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
      queryMessages = ''
      features = ()
      if query:
        (queryResults, queryMessages, features) = (
            runSearch(app, query, cache)
        )
        (queryResultsC, queryMessagesC, featuresC) = (
            runSearchCondensed(app, query, cache, d.condenseType)
            if not queryMessages and d.condensed and d.condenseType else
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
      if d.condensed and d.condenseType:
        csvs += (
            (f'resultsBy{d.condenseType}', queryResultsC),
        )
      resultsX = getResultsX(
          api,
          queryResults,
          features,
          app.noDescendTypes,
          fmt=d.fmt,
      )
      return (queryMessages, pickle.dumps(csvs), pickle.dumps(resultsX))

  return ThreadedServer(TfKernel, port=port, protocol_config={
      # 'allow_pickle': True,
      # 'allow_public_attrs': True,
  })


# KERNEL CONNECTION

def makeTfConnection(host, port, timeout):
  class TfConnection(object):
    def connect(self):
      connection = rpyc.connect(host, port, config=dict(sync_request_timeout=timeout))
      self.connection = connection
      return connection.root

  return TfConnection()


# TOP LEVEL

def main(cargs=sys.argv):
  dataSource = argParam(cargs=cargs, interactive=True)
  modules = argModules(cargs=cargs)
  sets = argSets(cargs=cargs)
  lgc = argLocalClones(cargs=cargs)
  check = argCheck(cargs=cargs)

  if dataSource is not None:
    moduleRefs = modules[6:] if modules else ''
    setFile = sets[7:] if sets else ''
    (commit, appDir) = findApp(dataSource, lgc, check)
    if appDir is not None:
      config = findAppConfig(dataSource, appDir)
      if config is not None:
        kernel = makeTfKernel(
            dataSource,
            appDir,
            commit,
            moduleRefs,
            setFile,
            lgc,
            check,
            config.PORT['kernel'],
        )
        if kernel:
          kernel.start()


# LOWER LEVEL

def _batchAround(nResults, position, batch):
  halfBatch = int((batch + 1) / 2)
  left = min(max(position - halfBatch, 1), nResults)
  right = max(min(position + halfBatch, nResults), 1)
  discrepancy = batch - (right - left + 1)
  if discrepancy != 0:
    right += discrepancy
  if right > nResults:
    right = nResults
  return (left, right)


if __name__ == "__main__":
  main()
