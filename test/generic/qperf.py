import sys
import os
import collections
import time
from itertools import product
from datetime import date, datetime
from tf.app import use
from tf.parameters import YARN_RATIO, TRY_LIMIT_FROM, TRY_LIMIT_TO
from tf.core.timestamp import Timestamp

TASKS = (
    'measure',
    'compare',
)
TASKS_SET = set(TASKS)

YARN = 'yarnRatio'
TRYF = 'tryLimitFrom'
TRYT = 'tryLimitTo'

YARN_RATIO_RANGE = '1.0,1.1,1.2,1.25,1.3,1.4,1.5,1.6'

PERF_PARAMS = (
    (YARN, YARN_RATIO, float),
    (TRYF, TRY_LIMIT_FROM, int),
    (TRYT, TRY_LIMIT_TO, int),
)
PERF_DEFAULTS = {x[0]: (x[1],) for x in PERF_PARAMS}
PERF_TYPES = {x[0]: x[2] for x in PERF_PARAMS}


LIMIT = 'limit'
LIMITQ = 'limit'
NAME = 'name'
NAMEQ = 'name'

SUITE_PARAMS = (
    (LIMITQ, None, int),
    (NAMEQ, None, str),
)
SUITE_DEFAULTS = {x[0]: x[1] for x in SUITE_PARAMS}
SUITE_TYPES = {x[0]: x[2] for x in SUITE_PARAMS}

META_PARAMS = (
    (LIMIT, None, int),
)
META_DEFAULTS = {x[0]: x[1] for x in META_PARAMS}
META_TYPES = {x[0]: x[2] for x in META_PARAMS}

perfParamRep = '\n'.join(f'{x[0]}={x[2]}' for x in PERF_PARAMS)

HELP = f'''
USAGE python3 qperf.py task arguments

=========================
task = measure

USAGE python3 qperf.py measure apps parameters
-------------------------

Runs query performance tests for selected apps and parameters.

Each normal argument is the name of a TF app, possibly with a minus.
If no apps are given, all apps will be run.

If any app is given, only indicated apps are run.

If an app is preceded with a -, it will not be run.

Performance parameters:
~~~~~~~~~~~~~~~~~~~~~~~~~

{perfParamRep}

For each parameter, you may specify a comma separated list of values.

If you give - for the yarn ratio, a standard range of values will be used:
    {YARN_RATIO_RANGE}

Suite parameters
~~~~~~~~~~~~~~~~~~~~~~~~~

limit=integer: only run so many queries per app
name=string: comma separated list of query names to be done, the rest are skipped

=========================
task = compare

USAGE python3 qperf.py compare name refletter dateStr perfparamStr
-------------------------

Collects all measurements specified by the refletter (reference measurement),
and other measurments on all the dates specified by dateStr
with all the perfparams specified in perfParamStr.

The dateStr and perfparamStr are comma-separated lists of dates and perfparamstrings.

You may set dateStr and/or perfParamStr to - .

If dateStr is - all reports of today will be selected.

If perfParamStr is - , all choices of perfParams for the chosen date are selected.

The name of the file with comparison results is composed of the
args name, refletter and the first date in dateStr.

=========================
--help gives help.
'''

GH_BASE = os.path.expanduser('~/github')
TEST_BASE = f'{GH_BASE}/annotation/text-fabric/test/generic/qperf'
QUERY_DIR = f'{TEST_BASE}/queries'
REF_DIR = f'{TEST_BASE}/reference'
REPORT_DIR = f'{TEST_BASE}/reports'
COMPARE_DIR = f'{TEST_BASE}/compare'

RESULTS = 'results'
RESULTSC = 'resultsOK'
STUDY = 'study'
STUDYF = 'studyFrac'
STUDYD = 'studyDiff'
FETCH = 'fetch'
FETCHF = 'fetchFrac'
FETCHD = 'fetchDiff'

FIELDS = f'''
  app
  query
  {LIMIT}
  {RESULTS}
  {STUDY}
  {FETCH}
'''.strip().split()

REF_FIELDS = f'''
  {RESULTS}
  {STUDY}
  {FETCH}
'''.strip().split()

COMPARE_FIELDS = f'''
  {RESULTSC}
  {STUDY}
  {STUDYF}
  {STUDYD}
  {FETCH}
  {FETCHF}
  {FETCHD}
'''.strip().split()

apps = {}
customSets = {}
good = True

timeStamp = None

TM = Timestamp()
indent = TM.indent
info = TM.info
error = TM.error


def ir(n):
  return int(round(n))


def readApps():
  apps = set()
  with os.scandir(QUERY_DIR) as d:
    for entry in d:
      if entry.is_dir():
        apps.add(entry.name)
  return apps


def readQueries(app):
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
  return queries


def readRefs():
  refs = {}
  with os.scandir(REF_DIR) as d:
    for entry in d:
      if not entry.is_file():
        continue

      name = entry.name
      if not name.endswith('.tsv'):
        continue

      nameBare = name[0:-4]
      parts = nameBare.split('-', maxsplit=1)
      if len(parts) != 2:
        continue

      (letter, rest) = parts
      if len(letter) != 1 or not letter.isupper():
        continue

      parts = rest.split('-', maxsplit=3)
      if len(parts) != 4:
        continue

      datum = '-'.join(parts[0:3])
      perf = parts[3]
      refs[letter] = dict(name=name, letter=letter, date=datum, perf=perf)
  return refs


def readReports():
  reports = {}
  with os.scandir(REPORT_DIR) as d:
    for entry in d:
      if not entry.is_file():
        continue

      name = entry.name
      if not name.endswith('.tsv'):
        continue

      nameBare = name[0:-4]
      parts = nameBare.split('-', maxsplit=3)
      if len(parts) != 4:
        continue

      datum = '-'.join(parts[0:3])
      rest = parts[3]
      parts = rest.split('@', maxsplit=1)
      perf = parts[0]
      reports.setdefault(datum, {})[perf] = dict(name=name, date=datum, perf=perf)
  return reports


def readFields(fields):
    fieldDict = dict(zip(FIELDS[2:], fields[2:]))
    for f in (STUDY, FETCH):
      val = fieldDict[f].strip()
      fieldDict[f] = float(val) if len(val) else None
    for f in (RESULTS,):
      val = fieldDict[f]
      fieldDict[f] = int(val) if len(val) else None
    return fieldDict


def readItem(item):
  isRef = 'letter' in item
  dirName = REF_DIR if isRef else REPORT_DIR
  fileName = item[NAME]
  filePath = f'{dirName}/{fileName}'
  with open(filePath) as fh:
    lines = [line.rstrip('\n').split('\t') for line in fh][1:]
  info = {tuple(fields[0:2]): dict(zip(FIELDS[2:], fields[2:])) for fields in lines}
  info = {tuple(fields[0:2]): readFields(fields) for fields in lines}
  return info


def checkArgs(cargs):
  if '--help' in cargs:
    print(HELP)
    return None

  if len(cargs) and cargs[0] == '-v':
    cargs = cargs[1:]

  if len(cargs) == 0 or cargs[0] not in TASKS_SET:
    task = TASKS[0]
  else:
    task = cargs[0]
    cargs = cargs[1:]

  if task == TASKS[0]:
    appsYes = set()
    appsNo = set()
    perfParams = {}
    perfParams.update(PERF_DEFAULTS)
    suiteParams = {}
    suiteParams.update(SUITE_DEFAULTS)

    good = True

    for arg in cargs:
      parts = arg.split('=', maxsplit=1)
      if len(parts) == 2:
        (key, value) = parts
        if key in SUITE_DEFAULTS:
          typ = SUITE_TYPES[key]
          if key == NAMEQ:
            vals = []
            for val in value.split(','):
              try:
                vals.append(typ(val))
              except ValueError:
                good = False
                error(f'{val} has wrong type for suite param {key}: {typ}')
            suiteParams[key] = vals
          else:
            try:
              suiteParams[key] = typ(value)
            except ValueError:
              good = False
              error(f'{value} has wrong type for suite param {key}: {typ}')
        elif key in PERF_DEFAULTS:
          typ = PERF_TYPES[key]
          vals = []
          if key == YARN and value == '-':
            value = YARN_RATIO_RANGE
          for val in value.split(','):
            try:
              vals.append(typ(val))
            except ValueError:
              good = False
              error(f'{val} has wrong type for perf param {key}: {typ}')
          perfParams[key] = vals
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
      return (task, None)

    if not good:
      return (task, False)

    queries = {}
    for app in apps:
      queries[app] = readQueries(app)

    names = suiteParams[NAMEQ]
    if names:
      appsRep = ', '.join(apps)
      notFound = []
      for name in names:
        found = False
        for app in apps:
          if name in queries[app]:
            found = True
            break
        if not found:
          notFound.append(name)
      if notFound:
        notFoundRep = ', '.join(notFound)
        error(f'queries {notFoundRep} do not occur in any of {appsRep}')
        return (task, False)

    queryLists = {}

    for app in apps:
      myQueries = queries[app]
      names = suiteParams.get(NAMEQ, None)
      if names is not None:
        nameSet = set(names)
        myQueries = {q[0]: q[1] for q in myQueries.items() if q[0] in nameSet}
      queryList = sorted(myQueries.items())
      limit = suiteParams.get(LIMITQ, None)
      if limit is not None and not names:
        queryList = queryList[0:limit]
      queryLists[app] = queryList

    return (task, apps, queryLists, perfParams, suiteParams)

  refs = readRefs()
  reports = readReports()
  runDate = date.today().isoformat()

  if task == TASKS[1]:
    if len(cargs) < 4:
      info('Not all of name, refletter, dates and perfparams supplied', tm=False)
      return (task, None)

    (name, refLetter, datumStr, perfStr) = cargs[0:4]
    if datumStr == '-':
      datumStr = runDate
    if perfStr == '-':
      perfStr = None

    if len(refLetter) != 1 or not refLetter.isupper() or refLetter not in refs:
      error('No such reference report letter "{refLetter}"', tm=False)
      return (task, False)

    chosenRef = refs[refLetter]

    good = True
    datums = set(datumStr.split(','))
    perfs = None if perfStr is None else set(perfStr.split(','))

    chosenReports = []
    for (datum, dates) in sorted(reports.items()):
      for (perf, item) in sorted(dates.items()):
        if datum in datums and (perfs is None or perf in perfs):
          chosenReports.append(item)
    if not chosenReports:
      info('nothing meets the criteria; nothing to compare', tm=False)
      return ('task', None)
    nReports = len(chosenReports)
    info(f'{nReports} reports to compare', tm=False)
    return (task, name, refLetter, sorted(datums)[0], chosenRef, chosenReports)


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
  def __init__(self, apps, queryLists, perfParams, suiteParams):
    self.apps = apps
    self.queryLists = queryLists
    self.perfParams = perfParams
    self.suiteParams = suiteParams
    self.customSets = {}
    self.good = True
    self.nQueries = collections.Counter()
    self.runDate = date.today().isoformat()
    self.runTime = datetime.now().isoformat()
    indent(reset=True)
    self.rh = None

    limit = suiteParams[LIMITQ]
    names = suiteParams[NAMEQ]
    suiteRep = (
        f'queries: {", ".join(names)}\n'
        if names is not None else
        f'only: {limit} queries per corpus\n'
        if limit else
        ''
    )

    info(f'''This is QPERF measuring queries:
Run started: {self.runTime}
{suiteRep}''', tm=False)

  def finalize(self):
    suiteParams = self.suiteParams
    nQueries = self.nQueries
    indent(level=0)
    info(f'{sum(nQueries.values())} measurements of {len(nQueries)} queries')

    limit = suiteParams[LIMITQ]
    names = suiteParams[NAMEQ]

    limit = '' if limit is None or names else f'@{limit}'
    name = '' if names is None else f'@{names[0]}'

    for (perfKey, lines) in self.results.items():
      reportFile = f'{self.runDate}-{perfKey}{name}{limit}.tsv'
      reportPath = f'{REPORT_DIR}/{reportFile}'
      rh = open(reportPath, 'w')
      rh.write('\t'.join(FIELDS))
      rh.write('\n')
      for fields in lines:
        line = '\t'.join(str(f) for f in fields)
        rh.write(f'{line}\n')
      rh.close()
      info(f'report {reportFile}', tm=False)
    info(f'Reports in directory {REPORT_DIR}', tm=False)

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
    perfKey = self.perfKey

    indent(level=3, reset=True)
    info(f'{"." * 8}{qName:<30} {perfKey}', tm=False, nl=False)

    stamp()
    resultGen = S.search(qText, sets=customSets)
    studyTime = elapsed()

    limit = qMeta.get(LIMIT, None)
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
    fields = (
        app,
        qName,
        limit or '',
        nResults,
        f'{studyTime * 1000}',
        f'{fetchTime * 1000}',
    )
    self.results.setdefault(perfKey, []).append(fields)
    self.nQueries[qName] += 1
    sys.stdout.write('\r')
    sys.stdout.write('  ' * 20 + '\r')
    sys.stdout.flush()
    info(f'{qName:<30} {perfKey}')

  def runQueries(self):
    perfParams = self.perfParams
    A = self.A
    api = A.api
    S = api.S

    app = self.app
    queryList = self.queryLists[app]
    perfParamCombis = tuple(product(*(perfParams[x[0]] for x in PERF_PARAMS)))

    for (qName, (qMeta, qText)) in queryList:
      self.qName = qName
      self.qText = qText
      self.qMeta = qMeta
      for perfParamCombi in perfParamCombis:
        perfSetting = {
            k: v
            for (k, v) in zip(
                (x[0] for x in PERF_PARAMS),
                perfParamCombi,
            )
        }
        S.tweakPerformance(silent=True, **perfSetting)
        self.perfKey = '-'.join(str(x) for x in perfParamCombi)
        self.runQuery()

  def executeApp(self):
    app = self.app
    indent(level=1, reset=True)
    info(f'BEGIN testing {app} with {len(self.queryLists[app])} queries')
    indent(level=2, reset=True)
    info(f'loading {app}')
    self.A = use(f'{app}:clone', checkout='clone', silent=True)
    info(f'making sets for {app}')
    self.makeSets()
    info(f'running queries for {app}')
    self.runQueries()
    indent(level=2)
    info(f'all queries run')
    indent(level=1)
    info(f'END testing {app}')

  def execute(self):
    self.results = {}
    for app in sorted(self.apps):
      self.app = app
      self.executeApp()
    self.finalize()


class Comparer(object):
  def __init__(self, name, ref, reports):
    self.name = name
    self.ref = ref
    self.reports = reports

  def readData(self):
    ref = self.ref
    reports = self.reports
    refInfo = readItem(ref)
    letter = ref['letter']
    reportInfos = [readItem(report) for report in reports]
    allKeys = set(refInfo)
    for rInfo in reportInfos:
      allKeys |= set(rInfo)
    allKeys = sorted(allKeys)
    self.refInfo = refInfo
    self.letter = letter
    self.reportInfos = reportInfos
    self.allKeys = allKeys
    info(f'comparing measurements of {len(allKeys)} queries', tm=False)

  def compare(self):
    refInfo = self.refInfo
    letter = self.letter
    reportInfos = self.reportInfos
    allKeys = self.allKeys
    compareFields = list(FIELDS[0:3])
    compareFields.extend(f'{field}{letter}' for field in REF_FIELDS)

    for i in range(len(reportInfos)):
      compareFields.extend(f'{field}{i + 1}' for field in COMPARE_FIELDS)
    compareLines = [compareFields]

    for key in allKeys:
      fields = [key[0], key[1]]

      ref = refInfo.get(key, {})
      limitN = ref.get(LIMIT, '')
      resultsN = ref.get(RESULTS, None)
      studyN = ref.get(STUDY, None)
      fetchN = ref.get(FETCH, None)

      fields.append('?' if limitN is None else limitN)
      fields.append('?' if resultsN is None else resultsN)
      fields.append('?' if studyN is None else ir(studyN))
      fields.append('?' if fetchN is None else ir(fetchN))

      for reportInfo in reportInfos:
        rep = reportInfo.get(key, {})
        resultsI = rep.get(RESULTS, None)
        studyI = rep.get(STUDY, None)
        fetchI = rep.get(FETCH, None)

        resultsC = None
        studyF = None
        studyD = None
        fetchF = None
        fetchD = None

        if resultsN is not None and resultsI is not None:
          resultsC = 'OK' if resultsI == resultsN else resultsI
        if studyN is not None and studyI is not None:
          studyF = int(round(1000 * studyI / studyN)) if studyN else None
          studyD = int(round(studyI - studyN))
        if fetchN is not None and fetchI is not None:
          fetchF = int(round(1000 * fetchI / fetchN)) if fetchN else None
          fetchD = int(round(fetchI - fetchN))

        fields.append('?' if resultsC is None else resultsC)

        fields.append('?' if studyI is None else ir(studyI))
        fields.extend([
            '?' if f is None else f'{f}' for f in (studyF, studyD)
        ])
        fields.append('?' if fetchI is None else ir(fetchI))
        fields.extend([
            '?' if f is None else f'{f}' for f in (fetchF, fetchD)
        ])

      compareLines.append(fields)

    self.lines = compareLines

  def export(self):
    name = self.name
    lines = self.lines

    fileName = f'{name}.tsv'
    filePath = f'{COMPARE_DIR}/{fileName}'
    with open(filePath, 'w') as fh:
      for fields in lines:
        lineStr = '\t'.join(str(x) for x in fields)
        fh.write(f'{lineStr}\n')
    info(f'Comparison written to {fileName}', tm=False)
    info(f'\tin {COMPARE_DIR}', tm=False)

  def produce(self):
    self.readData()
    self.compare()
    self.export()


def main(cargs=sys.argv[1:]):
  result = checkArgs(cargs)
  if result is None:
    return
  (task, *result) = result
  if result[0] is None:
    return
  if result[0] is False:
    error(f'{task} aborted', tm=False)
    return

  if task == TASKS[0]:
    (apps, queryLists, perfParams, suiteParams) = result
    T = Tester(apps, queryLists, perfParams, suiteParams)
    T.execute()

  if task == TASKS[1]:
    (name, letter, datum, ref, reports) = result
    C = Comparer(f'{name}-{letter}-{datum}', ref, reports)
    C.produce()


if __name__ == "__main__":
  main()
