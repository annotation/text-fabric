import sys
import os
import time
from datetime import date, datetime
from tf.app import use
from tf.parameters import YARN_RATIO, TRY_LIMIT_FROM, TRY_LIMIT_TO
from tf.core.timestamp import Timestamp

PERF_PARAMS = (
    ('yarnRatio', YARN_RATIO, float),
    ('tryLimitFrom', TRY_LIMIT_FROM, int),
    ('tryLimitTo', TRY_LIMIT_TO, int),
)
PERF_DEFAULTS = {x[0]: x[1] for x in PERF_PARAMS}
PERF_TYPES = {x[0]: x[2] for x in PERF_PARAMS}

SUITE_PARAMS = (
    ('limit', None, int),
    ('name', None, str),
)
SUITE_DEFAULTS = {x[0]: x[1] for x in SUITE_PARAMS}
SUITE_TYPES = {x[0]: x[2] for x in SUITE_PARAMS}

META_PARAMS = (
    ('limit', None, int),
)
META_DEFAULTS = {x[0]: x[1] for x in META_PARAMS}
META_TYPES = {x[0]: x[2] for x in META_PARAMS}

perfParamRep = '\n'.join(f'{x[0]}={x[2]}' for x in PERF_PARAMS)

HELP = f'''
USAGE python3 qperf.py apps parameters

Runs query performance tests for selected apps and parameters.

Each normal argument is the name of a TF app, possibly with a minus.
If no apps are given, all apps will be run.

If any app is given, only indicated apps are run.

If an app is preceded with a -, it will not be run.

Performance parameters:

{perfParamRep}

Suite parameters

limit=integer: only run so many queries per app
name=strin: only if a query has this name, it will be run

--help gives help.
'''

GH_BASE = '~/github'
GH_BASEX = os.path.expanduser(GH_BASE)
TEST_BASE = f'{GH_BASE}/annotation/text-fabric/test/generic/qperf'
TEST_BASEX = f'{GH_BASEX}/annotation/text-fabric/test/generic/qperf'
QUERY_DIR = f'{TEST_BASEX}/queries'
REPORT_DIR = f'{TEST_BASE}/reports'
REPORT_DIRX = f'{TEST_BASEX}/reports'

META_FIELDS = set('''
    limit
'''.strip().split())

FIELDS = '''
  app
  query
  results
  limited
  study time
  fetch time
'''.strip().split()

apps = {}
customSets = {}
good = True

timeStamp = None

TM = Timestamp()
indent = TM.indent
info = TM.info
error = TM.error


def readApps():
  apps = set()
  with os.scandir(QUERY_DIR) as d:
    for entry in d:
      if entry.is_dir():
        apps.add(entry.name)
  return apps


def checkArgs(cargs):
  if '--help' in cargs:
    print(HELP)
    return None

  if len(cargs) and cargs[0] == '-v':
    cargs = cargs[1:]

  appsYes = set()
  appsNo = set()
  perfParams = {}
  perfParams.update(PERF_DEFAULTS)
  suiteParams = {}

  good = True

  for arg in cargs:
    parts = arg.split('=', maxsplit=1)
    if len(parts) == 2:
      (key, value) = parts
      if key in SUITE_DEFAULTS:
        typ = SUITE_TYPES[key]
        try:
          suiteParams[key] = typ(value)
        except ValueError:
          good = False
          error(f'{value} has wrong type for suite param {key}: {typ}')
      elif key in PERF_DEFAULTS:
        typ = PERF_TYPES[key]
        try:
          perfParams[key] = typ(value)
        except ValueError:
          good = False
          error(f'{value} has wrong type for perf param {key}: {typ}')
      else:
        error(f'unknown parameter {key}={value}', tm=False)
        good = False
    else:
      if arg.startswith('-'):
        appsNo.add(arg[1:])
      else:
        appsYes.add(arg)

  appsPresent = readApps()
  appsRep = ' '.join(sorted(appsPresent))
  info(f'Found tests for {len(appsPresent)} apps:\n\t{appsRep}', tm=False)

  apps = set()

  for app in appsYes:
    if app not in appsPresent:
      error(f'No such app "{app}"', tm=False)
      good = False
  for app in appsNo:
    if app not in appsPresent:
      error(f'No such app -"{app}"', tm=False)
      good = False
  for app in appsPresent:
    if app in appsNo:
      continue
    if appsYes:
      if app not in appsYes:
        continue
    apps.add(app)

  if not apps:
    info('No apps selected', tm=False)
    return None

  if not good:
    return False

  return (apps, perfParams, suiteParams)


def stamp():
  global timeStamp
  timeStamp = time.time()


def elapsed():
  return time.time() - timeStamp


def makeSetsBhsa(app, A):
  COMMON_RANK = 100
  RARE_RANK = 500
  FREQ = 70
  AMOUNT = 20

  api = A.api
  N = api.N
  F = api.F
  L = api.L

  ochapter = set()
  allChapters = F.otype.s('chapter')

  for chapter in allChapters:
    if len([
        word for word in L.d(chapter, otype='word') if F.freq_lex.v(word) < FREQ
    ]) < AMOUNT:
      ochapter.add(chapter)

  frequent = set()
  infrequent = set()

  for n in N():
      nTp = F.otype.v(n)
      if nTp == 'lex':
         continue
      if nTp == 'word':
          ranks = [F.rank_lex.v(n)]
      else:
          ranks = [F.rank_lex.v(w) for w in L.d(n, otype='word')]
      maxRank = max(ranks)
      if maxRank < COMMON_RANK:
          frequent.add(n)
      if maxRank > RARE_RANK:
          infrequent.add(n)

  query = '''
p:phrase
  wPreGap:word
  wLast:word
  :=

wGap:word
wPreGap <: wGap
wGap < wLast

p || wGap
  '''
  gapQueryResults = A.search(query, shallow=True)

  return dict(
      ochapter=ochapter,
      frequent=frequent,
      infrequent=infrequent,
      common=frequent,
      rare=infrequent,
      gapphrase=gapQueryResults,
      conphrase=set(F.otype.s('phrase')) - gapQueryResults,
  )


def makeSetsUruk(app, A):
  query = '''
tablet
/where/
  case
/have/
  /without/
    sign type=numeral
  /-/
/-/
/with/
  case
/-/
'''
  cntablet = A.search(query, shallow=True)
  return dict(cntablet=cntablet)


class Tester(object):
  def __init__(self, apps, perfParams, suiteParams):
    self.apps = apps
    self.perfParams = perfParams
    self.suiteParams = suiteParams
    self.customSets = {}
    self.good = True
    self.nQueries = 0
    self.runDate = date.today().isoformat()
    self.runTime = datetime.now().isoformat()
    indent(reset=True)
    self.rh = None
    self.perfKey = '-'.join(str(self.perfParams[x[0]]) for x in PERF_PARAMS)
    self.perfStr = '\n\t'.join(
        f'{x[0]:<15} = {self.perfParams[x[0]]:>7}'
        for x in PERF_PARAMS
    )

    info(f'''This is QPERF measuring queries:
Run started: {self.runTime}
Parameters:\n\t{self.perfStr}
''', tm=False)
    reportFile = f'{self.runDate}-{self.perfKey}.tsv'
    reportPath = f'{REPORT_DIRX}/{reportFile}'
    self.rh = open(reportPath, 'w')
    self.rh.write('\t'.join(FIELDS))
    self.rh.write('\n')
    info(f'Report in {reportFile}\n\tin directory {REPORT_DIR}', tm=False)

  def finalize(self):
    if self.rh:
      self.rh.close()
    indent(level=0)
    info(f'{self.nQueries} tested')

  def readQueries(self):
    app = self.app
    queryDir = f'{QUERY_DIR}/{app}'
    queries = {}
    with os.scandir(queryDir) as d:
      for entry in d:
        if not (entry.is_file() and entry.name.endswith('.txt')):
          continue
        qName = entry.name[0:-4]
        with open(f'{queryDir}/{entry.name}') as qf:
          metaData = {}
          qText = ''
          for line in qf:
            if line.startswith('@'):
              (key, value) = line[1:].strip().split('=', maxsplit=1)
              if key not in META_DEFAULTS:
                error(
                    'Query {qName}: warning: unrecognized meta data key "{key}"',
                    tm=False,
                )
              typ = META_TYPES[key]
              try:
                metaData[key] = typ(value)
              except ValueError:
                error(f'{value} has wrong type for meta param @{key}: {typ}')
            else:
              qText += line

        queries[qName] = (metaData, qText)
    self.queries = queries

  def makeSets(self):
    app = self.app
    A = self.A
    self.customSets = (
        makeSetsBhsa(app, A)
        if app == 'bhsa' else
        makeSetsUruk(app, A)
        if app == 'uruk' else
        {}
    )

  def runQuery(self):
    app = self.app
    A = self.A
    api = A.api
    S = api.S
    qName = self.qName
    qMeta = self.qMeta
    qText = self.qText
    customSets = self.customSets

    indent(level=3, reset=True)
    info(qName, tm=False, nl=False)

    stamp()
    resultGen = S.search(qText, sets=customSets)
    studyTime = elapsed()

    limit = qMeta.get('limit', None)
    stamp()
    if limit is None:
      results = list(resultGen)
    else:
      results = []
      for r in resultGen:
        results.append(r)
        if len(results) == limit:
          break
    fetchTime = elapsed()

    nResults = len(results)
    line = '\t'.join(
        str(x)
        for x in (
            app,
            qName,
            nResults,
            limit or '',
            f'{studyTime:5.2f}',
            f'{fetchTime:5.2f}',
        )
    )
    self.rh.write(f'{line}\n')
    self.nQueries += 1
    sys.stdout.write('\r')
    sys.stdout.write('  ' * 30 + '\r')
    sys.stdout.flush()
    info(qName)

  def runQueries(self):
    queries = self.queries
    name = self.suiteParams.get('name', None)
    if name is not None:
      queries = {q[0]: q[1] for q in queries.items() if q[0] == name}
    queryList = sorted(queries.items())
    limit = self.suiteParams.get('limit', None)
    if limit is not None:
      queryList = queryList[0:limit]
    for (qName, (qMeta, qText)) in queryList:
      self.qName = qName
      self.qText = qText
      self.qMeta = qMeta
      self.runQuery()

  def executeApp(self):
    app = self.app
    indent(level=1, reset=True)
    self.readQueries()
    info(f'BEGIN testing {app} with {len(self.queries)} queries')
    indent(level=2, reset=True)
    info(f'loading {app}')
    self.A = use(f'{app}:clone', checkout='clone', silent=True)
    info(f'making sets for {app}')
    self.makeSets()
    info(f'running queries for {app}')
    self.runQueries()
    indent(level=2)
    info(f'queries run')
    indent(level=1)
    info(f'END testing {app}')

  def execute(self):
    for app in sorted(self.apps):
      self.app = app
      self.executeApp()
    self.finalize()


def main(cargs=sys.argv[1:]):
  result = checkArgs(cargs)
  if result is None:
    return
  if result is False:
    error('aborted', tm=False)
    return

  (apps, perfParams, suiteParams) = result
  T = Tester(apps, perfParams, suiteParams)
  T.execute()


if __name__ == "__main__":
  main()
