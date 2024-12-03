import sys
from textwrap import dedent

from .helpers import console


# (good, tasks, params, flags, defaults) = readArgs("tf-addnlp", HELP, TASKS, PARAMS, FLAGS)


def readArgs(
    command, descr, possibleTasks, possibleParams, possibleFlags, notInAll=set()
):
    """Interpret tasks, parameters and flags specified.

    Parameters
    ----------
    command:
        The name of the command, as entered on the command-line
    descr: string
        A description of the task
    possibleTasks: dict
        Keyed by the names of tasks, the values are a short description of the task.
    possibleParams: dict
        Keyed by the names of the parameters, the values are tuples with a short
        description of the parameter plus a default value for it.
    possibleFlags: dict
        Keyed by the name of the flags, the values are tuples with a short
        description of the flag, plus a default value for it, plus the number
        of values it can take.
        There are these possibilities:

        *   `2`: values are False or True, represented by `-` and `+`;
        *   `3`: values are `-1`, `0` or `1`, represented by `-`, `+` and `++`.

    notInAll: set, optional set()
        A set of tasks which are excluded from execution if `all` is passed as a task
        argument. Such tasks will only by executed if they are explicitly passed
        as an argument to the command.

    Returns
    -------
    tuple
        The tuple returned consists of

        *   a boolean whether there is an error in the arguments
        *   a dict keyed by the tasks, values are True or False
        *   a dict of the parameters, values are strings
        *   a dict of the flags, values are -1, 0 or 1
    """

    taskArgs = set()
    helpTasks = []

    for (task, helpStr) in possibleTasks.items():
        helpTasks.append(f"\t{task}:\n\t\t{helpStr}\n")
        taskArgs.add(task)

    notInAllRep = f" except {', '.join(notInAll)}" if len(notInAll) else ""
    helpTasks.append(f"all:\n\t\tall tasks{notInAllRep}")
    taskArgs.add("all")

    paramArgsDef = {}
    helpParams = []

    for (param, (helpStr, default)) in possibleParams.items():
        helpParams.append(f"\t{param}={default}:\n\t\t{helpStr}\n")
        paramArgsDef[param] = default

    flagArgsDef = {}
    flagArgs = {}
    helpFlags = []

    for (flag, (helpStr, default, nValues)) in possibleFlags.items():
        helpFlags.append(f"\t{flag}={default}:\n\t\t{helpStr}\n")
        valueCoding = (
            (("-", False, "no"), ("+", True, "yes"))
            if nValues == 2
            else (("-", -1, "no"), ("+", 0, "a bit"), ("++", 1, "more"))
            if nValues == 3
            else None
        )

        if valueCoding is not None:
            for (sigil, value, rep) in valueCoding:
                helpFlags.append(f"\t\t{sigil}{flag}: {rep} {flag}")
                flagArgsDef[flag] = default
                flagArgs[f"{sigil}{flag}"] = value

    helpText = (
        f"{command} [tasks/params/flags] [--help]\n\n{descr}\n\n"
        + dedent(
            """
        --help: show this text and exit

        tasks:
        «tasks»

        parameters:
        «params»

        flags:
        «flags»
        """
        )
        .replace("«tasks»", "".join(helpTasks))
        .replace("«params»", "".join(helpParams))
        .replace("«flags»", "".join(helpFlags))
    )

    possibleArgs = set(taskArgs) | set(flagArgs)

    args = set(sys.argv[1:])

    if not len(args) or "--help" in args or "-h" in args:
        console(helpText)
        if not len(args):
            console("No task specified")
        return (True, {}, {}, {})

    illegalArgs = {
        arg
        for arg in args
        if not (arg in possibleArgs or arg.split("=", 1)[0] in paramArgsDef)
    }

    if len(illegalArgs):
        console(helpText)
        for arg in illegalArgs:
            console(f"Illegal argument `{arg}`")
        return (False, {}, {}, {})

    tasks = {}
    flags = {}
    params = {}

    for arg in args:
        if arg in taskArgs:
            tasks[arg] = True
        elif arg in flagArgs:
            flags[arg.lstrip("+-")] = flagArgs[arg]
        else:
            parts = arg.split("=", 1)
            (p, val) = parts
            params[p] = val or paramArgsDef[p]

    for (f, default) in flagArgsDef.items():
        if f not in flags:
            flags[f] = default

    for (p, default) in paramArgsDef.items():
        if p not in params:
            params[p] = default

    if "all" in tasks:
        if tasks["all"]:
            tasks = {
                arg: True
                for arg in possibleTasks
                if arg != "all" and arg not in notInAll
            }
        else:
            del tasks["all"]

    return (True, tasks, params, flags)
