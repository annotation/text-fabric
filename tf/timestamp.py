import sys
import collections
import time


class Timestamp(object):
    def __init__(self, level=None):
        self.oneLevelRep = '   |   '
        self.level = level if level != None else 0
        self.levelRep = self.oneLevelRep * self.level
        self.timestamp = time.time()

    def raw_msg(self, msg, tm=True, error=False):
        if tm:
            msgRep = '{}{:>7} {}'.format(self.levelRep, self._elapsed(), msg)
        else:
            msgRep = '{}{:>7} {}'.format(self.levelRep, self.oneLevelRep, msg)
        channel = sys.stderr if error else sys.stdout
        channel.write(msgRep)
        channel.flush()

    def info(self, msg, tm=True): self.raw_msg(msg, tm=tm)
    def error(self, msg, tm=True): self.raw_msg(msg, tm=tm, error=True)

    def reset(self, level=None):
        self.timestamp = time.time()

    def _elapsed(self):
        interval = time.time() - self.timestamp
        if interval < 10: return "{: 2.2f}s".format(interval)
        interval = int(round(interval))
        if interval < 60: return "{:>2d}s".format(interval)
        if interval < 3600: return "{:>2d}m {:>02d}s".format(interval // 60, interval % 60)
        return "{:>2d}h {:>02d}m {:>02d}s".format(interval // 3600, (interval % 3600) // 60, interval % 60)

