"""
# Timed messages

Error and informational messages can be issued,
with a time indication.
"""

import sys
import time

from .files import unexpanduser as ux


VERBOSE = "verbose"
"""Increased verbosity.
"""

AUTO = "auto"
"""Convenient level of silence.
"""

TERSE = "terse"
"""More silence.
"""

DEEP = "deep"
"""No output, except error messages.
"""

SILENT_D = AUTO
"""Default value for the silent parameter.

The value is `"terse"`
"""


def silentConvert(arg):
    if arg is None:
        return SILENT_D
    if arg is False:
        return VERBOSE
    if arg is True:
        return DEEP
    if type(arg) is str and arg in {VERBOSE, AUTO, TERSE, DEEP}:
        return arg
    return not not arg


class Timestamp:
    def __init__(self, silent=SILENT_D, level=None):
        """Create a controller for timed messages.

        You can specify the degree of verbosity and also
        an indentation level.
        The verbosity affects the display of the `info`,
        `warning`, and `error` methods that are defined
        in this class, but can also affects messages emitted
        by other parts of the application, such as:

        *   the display of the number of results in searches
        *   the header that is displayed after the incantation
            of TF.

        Parameters
        ----------
        silent: string, optional tf.core.timestamp.SILENT_D
            The verbosity. Here are the values and their effects:

            `"verbose"` or `False`:
            Show all `info`, `warning`, `error` messages.
            In incantation headers, show the full metadata
            of all features.

            `"auto"`:
            Like `"verbose"`, but in incantation headers,
            show the feature descriptions only,
            not the full metadata.

            `"terse"` or `None`: **(default)**
            Like `"auto"`, but do not show `log` messages.

            `"deep"` or `True`:
            Like `"terse"` but do not show `log` and `warning`
            messages.
            Do not show fetched datasets between the incantation
            and the header, and do not show the header either.
            Do not show the number of results after searches.
        """
        silent = silentConvert(silent)
        indent = self.indent

        self.oneLevelRep = "   |   "
        self.timestamp = {}
        self.level = 0
        indent(level=level, reset=True)
        self.log = []
        self.verbose = -2  # regulates all messages
        self.silent = silent  # regulates informational and warning messages only

    def raw_msg(self, msg, tm=True, nl=True, cache=0, error=False):
        # cache is a list: append to cache, do not output anything
        # cache = -1: only to cache
        # cache =  1: to cache and to console
        # cache =  0: only to console
        if self.verbose != -2 and self.level >= self.verbose:
            return
        if type(msg) is not str:
            msg = repr(msg)
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

    def debug(self, msg, tm=True, nl=True, cache=0, force=False):
        """Sends a debug message to the standard output.

        Debug messages are normally silenced, in that case
        nothing happens.

        Parameters
        ----------
        msg: string
            The string to be displayed
        tm: boolean, optional True
            Whether the message is to be prepended with the elapsed time.
        nl: boolean, optional True
            Whether a newline should be appended to the message.
        cache: integer, optional 0
            Whether the message should be cached.
        force: boolean, optional False
            If True, any silent condition is overridden.

        !!! caution "Silence"
            Informational messages are not displayed in silent mode.
        """

        if force or self.silent in {VERBOSE}:
            self.raw_msg(msg, tm=tm, nl=nl, cache=cache)

    def info(self, msg, tm=True, nl=True, cache=0, force=False):
        """Sends an informational message to the standard output.

        Info messages may have been silenced, in that case
        nothing happens.

        Parameters
        ----------
        msg: string
            The string to be displayed
        tm: boolean, optional True
            Whether the message is to be prepended with the elapsed time.
        nl: boolean, optional True
            Whether a newline should be appended to the message.
        cache: integer, optional 0
            Whether the message should be cached.
        force: boolean, optional False
            If True, any silent condition is overridden.

        !!! caution "Silence"
            Informational messages are not displayed in silent mode.
        """

        if force or self.silent in {VERBOSE, AUTO}:
            self.raw_msg(msg, tm=tm, nl=nl, cache=cache)

    def warning(self, msg, tm=True, nl=True, cache=0, force=False):
        """Sends an warning message to the standard output.

        Warning messages may have been silenced, in that case
        nothing happens.

        Parameters
        ----------
        msg: string
            The string to be displayed
        tm: boolean, optional True
            Whether the message is to be prepended with the elapsed time.
        nl: boolean, optional True
            Whether a newline should be appended to the message.
        cache: integer, optional 0
            Whether the message should be cached.
        force: boolean, optional False
            If True, any silent condition is overridden.

        !!! caution "Silence"
            Warning messages are not displayed if silent mode is `deep`.
        """

        if force or self.silent in {VERBOSE, AUTO, TERSE}:
            self.raw_msg(msg, tm=tm, nl=nl, cache=cache)

    def error(self, msg, tm=True, nl=True, cache=0, force=True):
        """Sends an warning message to the standard error.

        In a Jupyter notebook, the standard error is displayed with
        a reddish background color.

        Parameters
        ----------
        msg: string
            The string to be displayed
        tm: boolean, optional True
            Whether the message is to be prepended with the elapsed time.
        nl: boolean, optional True
            Whether a newline should be appended to the message.
        cache: integer, optional 0
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

        Parameters
        ----------
        level: integer|boolean, optional None
            The indentation level.
            If an integer, it sets the indentation level.
            If a boolean, it decreases or increases the indentation level,
            but not below zero. `True` increases the indent with one level,
            `False` decreases the indent.
        reset: boolean, optional False
            If `True`, the elapsed time to will be reset to 0 at the given level.
        """

        self.level = (
            0
            if level is None
            else level
            if type(level) is int
            else self.level + 1
            if level
            else self.level - 1
        )
        if self.level < 0:
            self.level = 0
        self.levelRep = self.oneLevelRep * self.level
        if reset:
            self.timestamp[self.level] = time.time()
        if _verbose is not None:
            self.verbose = _verbose

    def isSilent(self):
        """The current verbosity.

        Returns
        -------
        string
            See `VERBOSE`, `AUTO`, `TERSE`, `DEEP`.
        """
        return self.silent

    def setSilent(self, silent):
        """Set the verbosity.

        Parameters
        ----------
        silent: string, optional tf.core.timestamp.SILENT_D
            See `tf.core.timestamp.Timestamp`
        """

        silent = silentConvert(silent)
        self.silent = silent

    def silentOn(self, deep=False):
        """Suppress informational messages.

        Parameters
        ----------
        deep: boolean, optional False
            If `True` also suppress warnings.
        """

        wasSilent = self.silent
        self.wasSilent = wasSilent if wasSilent in {VERBOSE, AUTO, TERSE} else AUTO
        self.silent = DEEP if deep else TERSE

    def silentOff(self):
        """Enable informational messages."""

        wasSilent = getattr(self, "wasSilent", AUTO)
        self.silent = wasSilent

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
