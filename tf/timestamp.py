import sys
import collections
import time

class Timestamp(object):
    def __init__(self):
        self.timestamp = time.time()

    def raw_msg(self, msg, error=False):
        timed_msg = '{:>7} {}'.format(self._elapsed(), msg)
        channel = sys.stderr if error else sys.stdout
        channel.write(timed_msg)
        channel.flush()

    def info(self, msg): self.raw_msg(msg)
    def error(self, msg): self.raw_msg(msg, error=True)

    def reset(self): self.timestamp = time.time()

    def _elapsed(self):
        interval = time.time() - self.timestamp
        if interval < 10: return "{: 2.2f}s".format(interval)
        interval = int(round(interval))
        if interval < 60: return "{:>2d}s".format(interval)
        if interval < 3600: return "{:>2d}m {:>02d}s".format(interval // 60, interval % 60)
        return "{:>2d}h {:>02d}m {:>02d}s".format(interval // 3600, (interval % 3600) // 60, interval % 60)

