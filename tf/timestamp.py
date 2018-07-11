import sys
import time


class Timestamp(object):
  def __init__(self, level=None):
    self.oneLevelRep = '   |   '
    self.timestamp = {}
    self.indent(level=level, reset=True)
    self.log = []
    self.verbose = -2

  def raw_msg(self, msg, tm=True, nl=True, cache=0, error=False):
    # cache = -1: only to cache
    # cache =  1: to cache and to console
    # cache =  0: only to console
    if self.verbose != -2 and self.level >= self.verbose:
      return
    if tm:
      msgRep = '{}{:>7} {}'.format(self.levelRep, self._elapsed(),
                                   msg).replace('\n', '\n' + self.levelRep)
    else:
      msgRep = '{}{}'.format(self.levelRep, msg).replace('\n', '\n' + self.levelRep)
    if cache:
      self.log.append((error, nl, msgRep))
    if cache >= 0:
      channel = sys.stderr if error else sys.stdout
      channel.write('{}{}'.format(msgRep, '\n' if nl else ''))
      channel.flush()

  def reset(self):
    self.log = []

  def cache(self, asString=False):
    if asString:
      lines = []
      for (error, nl, msgRep) in self.log:
        lines.append('{}{}'.format(msgRep, '\n' if nl else ''))
      result = ''.join(lines)
    else:
      for (error, nl, msgRep) in self.log:
        channel = sys.stderr if error else sys.stdout
        channel.write('{}{}'.format(msgRep, '\n' if nl else ''))
      sys.stderr.flush()
      sys.stdout.flush()
    self.log = []
    if asString:
      return result

  def info(self, msg, tm=True, nl=True, cache=0):
    self.raw_msg(msg, tm=tm, nl=nl, cache=cache)

  def error(self, msg, tm=True, nl=True, cache=0):
    self.raw_msg(msg, tm=tm, nl=nl, cache=cache, error=True)

  def indent(self, level=None, reset=False, verbose=None):
    self.level = level if level is not None else 0
    self.levelRep = self.oneLevelRep * self.level
    if reset:
      self.timestamp[self.level] = time.time()
    if verbose is not None:
      self.verbose = verbose

  def _elapsed(self):
    interval = time.time() - self.timestamp.setdefault(self.level, time.time())
    if interval < 10:
      return "{: 2.2f}s".format(interval)
    interval = int(round(interval))
    if interval < 60:
      return "{:>2d}s".format(interval)
    if interval < 3600:
      return "{:>2d}m {:>02d}s".format(interval // 60, interval % 60)
    return "{:>2d}h {:>02d}m {:>02d}s".format(
        interval // 3600, (interval % 3600) // 60, interval % 60
    )
