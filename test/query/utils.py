import io
import cProfile
import pstats
from pstats import SortKey


def prof_x(code, g, l):
  cProfile.runctx(code, g, l, sort=SortKey.CUMULATIVE)


def prof(func, g, l, *args, **kwargs):
  globals().update(g)
  locals().update(l)
  pr = cProfile.Profile()
  pr.enable()
  results = func(*args, **kwargs)
  pr.disable()
  s = io.StringIO()
  sortby = SortKey.CUMULATIVE
  ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
  ps.print_stats()
  print(s.getvalue())
  return results
