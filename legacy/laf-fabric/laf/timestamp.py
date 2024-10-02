import sys
import collections
import time

class Timestamp(object):
    '''Timed progress messages.

    There are specialized methods for distinct verbosity levels: ``Emsg``, ``Wmsg`` etc.
    With ``set_verbose`` you can set the verbosity of the application.
    Only messages with that verbosity level of lower will reach the output.
    You can suppress the time indication and the newline at the end.

    ``raw_msg`` has complete flexibility. This method is exposed as ``msg`` in the API.
    '''
    verbose_level = collections.OrderedDict((
        ('SILENT', -10),
        ('ERROR', -3),
        ('WARNING', -2),
        ('INFO', -1),
        ('NORMAL', 0),
        ('DETAIL', 1),
        ('DEBUG', 10),
    ))

    def __init__(self, log_file=None, verbose=None):
        self.timestamp = time.time()
        self.log = None
        self.logs = []
        self.verbose = self.verbose_level[verbose or 'NORMAL']
        if log_file: self.connect_log(log_file)

    def Emsg(self, msg, newline=True, withtime=True): self.raw_msg('ERROR: '+msg, newline, withtime, verbose='ERROR')
    def Wmsg(self, msg, newline=True, withtime=True): self.raw_msg('WARNING: '+msg, newline, withtime, verbose='WARNING')
    def Nmsg(self, msg, newline=True, withtime=True): self.raw_msg(msg, newline, withtime, verbose='NORMAL')
    def Imsg(self, msg, newline=True, withtime=True): self.raw_msg('INFO: '+msg, newline, withtime, verbose='INFO')
    def Dmsg(self, msg, newline=True, withtime=True): self.raw_msg('DETAIL: '+msg, newline, withtime, verbose='DETAIL')
    def Xmsg(self, msg, newline=True, withtime=True): self.raw_msg('XXX: '+msg, newline, withtime, verbose='DEBUG')
    def Smsg(self, msg, verbose, newline=True, withtime=True): self.raw_msg('{}: {}'.format(verbose, msg), newline, withtime, verbose=verbose)

    def raw_msg(self, msg, newline=True, withtime=True, verbose=None, error=True):
        verbose = verbose or 'NORMAL'
        if self.verbose_level[verbose] > self.verbose: return 
        timed_msg = "{:>7} ".format(self._elapsed()) if withtime else ''
        timed_msg += msg
        if newline: timed_msg += "\n"
        channel = sys.stderr if error else sys.stdout
        channel.write(timed_msg)
        channel.flush()
        if self.log: self.log.write(timed_msg)

    def set_verbose(self, verbose): self.verbose = self.verbose_level[verbose or 'NORMAL']
    def reset(self): self.timestamp = time.time()
    def connect_log(self, log_file):
        self.logs.append(log_file)
        self.log = log_file
    def disconnect_log(self):
        try:
            self.log.close()
            del self.logs[-1]
            if self.logs: self.log = self.logs[-1]
        except: pass
        self.log = None
        self.logs = []

    def _elapsed(self):
        interval = time.time() - self.timestamp
        if interval < 10: return "{: 2.2f}s".format(interval)
        interval = int(round(interval))
        if interval < 60: return "{:>2d}s".format(interval)
        if interval < 3600: return "{:>2d}m {:>02d}s".format(interval // 60, interval % 60)
        return "{:>2d}h {:>02d}m {:>02d}s".format(interval // 3600, (interval % 3600) // 60, interval % 60)

