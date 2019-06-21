from ..core.helpers import console, wrapMessages
from .searchexe import SearchExe
from ..parameters import YARN_RATIO, TRY_LIMIT_FROM, TRY_LIMIT_TO

# Search and SearchExe
#
# HIGH LEVEL description of the roles of Search and SerchExe
#
# SearchExe is the class that runs queries.
# SearchFactory is a class that creates SearchExe instances.
#
# The user is given the factory class as search api S.
#
# The (public) methods of the factory class has methods for searching.
# These methods work on a dedicated instance of SearchExe
# within the factory class.
# The factory class will create this instance when needed.
#
# A reference to the factory class Search is stored in the SearchExe objects.
# This gives the SearchExe objects the possibility to create other
# SearchExe objects to perform auxiliary queries.
# This is needed to run the queries implied by
# quantifiers in the search template.
#
# The search processes done by distinct SearchExe objects do not interfere.
#
# Summarizing: the factory class Search looks to the user like the execution
# class # SearchExe.
# But under the hood, different queries are always performed on different
# instances of SearchExe.

# LOW LEVEL description of the roles of Search and SerchExe
#
# In order to search, you have to create an instance of the SearchExe class.
# This instance contains all parameters and settings relevant to the search.
#
# The factory Search may contain one instance of a SearchExe.
#
# The factory class Search has methods study() and search(),
# which create a SearchExe instance and store it inside the Search.
# After that they call methods with the same name on that SearchExe object.
#
# The factory class Search has methods fetch(), count(), showPlan().
# These call mehtods with the same name on the SearchExe instance stored in
# the factory class Search, if it has been created earlier
# by search() or study().
# If not, an error message is displayed.
#
# All the work involved in searching is performed by the SearchExe object.
# The data of a SearchExe object are tied to a particular search:
# searchTemplate, sets, shallow, silent.
# This also holds for all data that is created during executions of a query:
# qnodes, qedges, results, etc.


class Search(object):

  def __init__(self, api, silent):
    self.api = api
    self.silent = silent
    self.exe = None
    self.perfDefaults = dict(
        yarnRatio=YARN_RATIO,
        tryLimitFrom=TRY_LIMIT_FROM,
        tryLimitTo=TRY_LIMIT_TO,
    )
    self.perfParams = {}
    self.perfParams.update(self.perfDefaults)
    SearchExe.setPerfParams(self.perfParams)

  def tweakPerformance(self, silent=False, **kwargs):
    api = self.api
    error = api.error
    info = api.info
    isSilent = api.isSilent
    setSilent = api.setSilent
    defaults = self.perfDefaults

    wasSilent = isSilent()
    setSilent(silent)
    for (k, v) in kwargs.items():
      if k not in defaults:
        error(f'No such performance parameter: "{k}"', tm=False)
        continue
      if v is None:
        v = defaults[k]
      elif type(v) is not int and k != 'yarnRatio':
        error(f'Performance parameter "{k}" must be set to an integer, not to "{v}"', tm=False)
        continue
      self.perfParams[k] = v
    info('Performance parameters, current values:', tm=False)
    for (k, v) in sorted(self.perfParams.items()):
      info(f'\t{k:<20} = {v:>7}', tm=False)
    SearchExe.setPerfParams(self.perfParams)
    setSilent(wasSilent)

  def search(
      self,
      searchTemplate,
      limit=None,
      sets=None,
      shallow=False,
      silent=True,
      here=True,
      msgCache=False,
  ):
    exe = SearchExe(
        self.api,
        searchTemplate,
        outerTemplate=searchTemplate,
        quKind=None,
        offset=0,
        sets=sets,
        shallow=shallow,
        silent=silent,
        msgCache=msgCache,
        setInfo={},
    )
    if here:
      self.exe = exe
    queryResults = exe.search(limit=limit)
    if type(msgCache) is list:
      messages = wrapMessages(msgCache)
      return (queryResults, messages) if here else (queryResults, messages, exe)
    return queryResults

  def study(
      self,
      searchTemplate,
      strategy=None,
      sets=None,
      shallow=False,
      here=True,
  ):
    exe = SearchExe(
        self.api,
        searchTemplate,
        outerTemplate=searchTemplate,
        quKind=None,
        offset=0,
        sets=sets,
        shallow=shallow,
        silent=False,
        showQuantifiers=True,
        setInfo={},
    )
    if here:
      self.exe = exe
    return exe.study(strategy=strategy)

  def fetch(self, limit=None, msgCache=False):
    exe = self.exe
    if exe is None:
      error = self.api.error
      error('Cannot fetch if there is no previous "study()"')
    else:
      queryResults = exe.fetch(limit=limit)
      if type(msgCache) is list:
        messages = self.api.cache(_asString=True)
        return (queryResults, messages)
      return queryResults

  def count(self, progress=None, limit=None):
    exe = self.exe
    if exe is None:
      error = self.api.error
      error('Cannot count if there is no previous "study()"')
    else:
      exe.count(progress=progress, limit=limit)

  def showPlan(self, details=False):
    exe = self.exe
    if exe is None:
      error = self.api.error
      error('Cannot show plan if there is no previous "study()"')
    else:
      exe.showPlan(details=details)

  def relationsLegend(self):
    exe = self.exe
    if exe is None:
      exe = SearchExe(self.api, '')
    console(exe.relationLegend)

  def glean(self, r):
    T = self.api.T
    F = self.api.F
    E = self.api.E
    fOtype = F.otype.v
    slotType = F.otype.slotType
    maxSlot = F.otype.maxSlot
    eoslots = E.oslots.data

    lR = len(r)
    if lR == 0:
      return ''
    fields = []
    for (i, n) in enumerate(r):
      otype = fOtype(n)
      words = [n] if otype == slotType else eoslots[n - maxSlot - 1]
      if otype == T.sectionTypes[2]:
        field = '{} {}:{}'.format(*T.sectionFromNode(n))
      elif otype == slotType:
        field = T.text(words)
      elif otype in T.sectionTypes[0:2]:
        field = ''
      else:
        field = '{}[{}{}]'.format(
            otype,
            T.text(words[0:5]),
            '...' if len(words) > 5 else '',
        )
      fields.append(field)
    return ' '.join(fields)
