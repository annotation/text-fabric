"""
.. include:: ../../docs/core/timestamp.md
"""

import sys
import time

from .helpers import unexpanduser as ux


class Timestamp(object):
    def __init__(self, level=None):
        indent = self.indent

        self.oneLevelRep = "   |   "
        self.timestamp = {}
        indent(level=level, reset=True)
        self.log = []
        self.verbose = -2  # regulates all messages
        self.silent = False  # regulates informational messages only

    def raw_msg(self, msg, tm=True, nl=True, cache=0, error=False):
        # cache is a list: append to cache, do not output anything
        # cache = -1: only to cache
        # cache =  1: to cache and to console
        # cache =  0: only to console
        if self.verbose != -2 and self.level >= self.verbose:
            return
        msg = ux(msg)
        if tm:
            msgRep = f"{self.levelRep}{self._elapsed():>7} {msg}".replace(
                "\n", "\n" + self.levelRep
            )
        else:
            msgRep = f"{self.levelRep}{msg}".replace("\n", "\n" + self.levelRep)
        if type(cache) is list:
            cache.append((error, nl, msgRep))
        else:
            if cache:
                self.log.append((error, nl, msgRep))
            if cache >= 0:
                channel = sys.stderr if error else sys.stdout
                channel.write("{}{}".format(msgRep, "\n" if nl else ""))
                channel.flush()

    def reset(self):
        self.log = []

    def cache(self, _asString=False):
        if _asString:
            lines = []
            for (error, nl, msgRep) in self.log:
                lines.append("{}{}".format(msgRep, "\n" if nl else ""))
            result = "".join(lines)
        else:
            for (error, nl, msgRep) in self.log:
                channel = sys.stderr if error else sys.stdout
                channel.write("{}{}".format(msgRep, "\n" if nl else ""))
            sys.stderr.flush()
            sys.stdout.flush()
        self.log = []
        if _asString:
            return result

    def info(self, msg, tm=True, nl=True, cache=0):
        """Sends an informational message to the standard output.

        Parameters
        ----------
        msg: string
            The string to be displayed
        tm: boolean, optional `True`
            Whether the message is to be prepended with the elapsed time.
        nl: boolean, optional `True`
            Whether a newline should be appended to the message.
        cache: integer, optional `0`
            Whether the message should be cached.

        !!! caution "Silence"
            Informational messages are not displayed in silent mode.
        """

        if not self.silent:
            self.raw_msg(msg, tm=tm, nl=nl, cache=cache)

    def warning(self, msg, tm=True, nl=True, cache=0):
        """Sends an warning message to the standard output.

        Parameters
        ----------
        msg: string
            The string to be displayed
        tm: boolean, optional `True`
            Whether the message is to be prepended with the elapsed time.
        nl: boolean, optional `True`
            Whether a newline should be appended to the message.
        cache: integer, optional `0`
            Whether the message should be cached.

        !!! caution "Silence"
            Warning messages are not displayed if silent mode is `deep`.
        """

        if self.silent != "deep":
            self.raw_msg(msg, tm=tm, nl=nl, cache=cache)

    def error(self, msg, tm=True, nl=True, cache=0):
        """Sends an warning message to the standard error.

        In a Jupyter notebook, the standard error is displayed with
        a reddish background colour.

        Parameters
        ----------
        msg: string
            The string to be displayed
        tm: boolean, optional `True`
            Whether the message is to be prepended with the elapsed time.
        nl: boolean, optional `True`
            Whether a newline should be appended to the message.
        cache: integer, optional `0`
            Whether the message should be cached.

        !!! caution "Silence"
            Warning messages are displayed irrespective of the  silent mode.
        """

        self.raw_msg(msg, tm=tm, nl=nl, cache=cache, error=True)

    def indent(self, level=None, reset=False, _verbose=None):
        """Changes the indentation and timing of forthcoming messages.

        Messages can be indented. Multiline messages will have the indent
        prepended to each of its lines.

        The reported time is with respect to a starting point, which can be reset.
        The starting points at different levels are independent of each other.

        level: integer, optional `None`
            The indentation level.
        reset: boolean, optional `False`
            If `True`, the elapsed time to will be reset to 0 at the given level.
        """

        self.level = 0 if level is None else level
        self.levelRep = self.oneLevelRep * self.level
        if reset:
            self.timestamp[self.level] = time.time()
        if _verbose is not None:
            self.verbose = _verbose

    def isSilent(self):
        """The current verbosity.

        Returns
        -------
        boolean | string
            `False` not suppressing informational messages.
            `True` suppressing informational messages.
            `'deep'` also suppressing warnings.
        """
        return self.silent

    def setSilent(self, silent):
        """Set the verbosity.

        Parameters
        ----------
        silent: boolean | string
            If `False` do not suppress informational messages.
            If `True` suppress informational messages.
            If `'deep'` also suppress warnings.

        Error messages are never suppressed.
        """

        self.silent = silent

    def silentOn(self, deep=False):
        """Suppress informational messages.

        Parameters
        ----------
        deep: boolean, optional `False`
            If `True` also suppress warnings.
        """

        self.silent = True if not deep else "deep"

    def silentOff(self):
        """Enable informational messages.
        """

        self.silent = False

    def _elapsed(self):
        interval = time.time() - self.timestamp.setdefault(self.level, time.time())
        if interval < 10:
            return f"{interval: 2.2f}s"
        interval = int(round(interval))
        if interval < 60:
            return f"{interval:>2d}s"
        if interval < 3600:
            return f"{interval // 60:>2d}m {interval % 60:>02d}s"
        return (
            f"{interval // 3600:>2d}h {(interval % 3600) // 60:>02d}m"
            f" {interval % 60:>02d}s"
        )
