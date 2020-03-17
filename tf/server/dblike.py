import pickle
from ..core.helpers import console
from ..applib.app import findApp, findAppConfig
from ..server.kernel import makeTfConnection
from .wrap import passageLinks

from .command import argParam

TIMEOUT = 180
BATCH = 100


def setup(dataSource, checkoutApp):
    (commit, release, local, appBase, appDir) = findApp(dataSource, checkoutApp)
    if not appBase:
        return
    appPath = f"{appBase}/{appDir}"
    config = findAppConfig(dataSource, appPath)
    if config is None:
        return None

    TF = makeTfConnection(config.HOST, config.PORT["kernel"], TIMEOUT)
    return TF


def servePassage(kernelApi, passage):
    passages = ""

    (sec0, sec1, sec2) = passage.split(',')

    (table, sec0Type, passages, browseNavLevel,) = kernelApi.passage(
        (),
        '',
        sec0,
        sec1=sec1,
        sec2=sec2,
    )
    passages = pickle.loads(passages)
    return passageLinks(passages, sec0Type, sec0, sec1, browseNavLevel)


def serveQuery(kernelApi, query):

    messages = ""
    table = None
    try:
        (table, messages, features, start, total,) = kernelApi.search(
            query,
            BATCH,
        )
    except TimeoutError:
        messages = (
            f"Aborted because query takes longer than {TIMEOUT} second"
            + ("" if TIMEOUT == 1 else "s")
        )
        console(f"{query}\n{messages}", error=True)

    return (table, total)


def main():
    (dataSource, checkoutApp) = argParam(interactive=True)
    if dataSource is None:
        return

    TF = setup(dataSource, checkoutApp)
    if TF is None:
        return

    commands = {
        "P": "passage",
        "Q": "query",
    }
    commandText = "\n".join(f"[{k:>2}] {v}" for (k, v) in commands.items())
    try:
        while True:
            kernelApi = TF.connect()
            line = input(f"{commandText}\nenter command: ")
            command = ''
            kind = None
            if line.startswith('Q'):
                while True:
                    line = input(f"Query line: ")
                    if line.strip():
                        command += f"{line}\n"
                    else:
                        break
                kind = "query"
            elif line.startswith('P'):
                command = input(f"Passage: ")
                kind = "passage"
            else:
                if line.strip():
                    console("try again")
                else:
                    break

            result = None

            if kind == "passage":
                result = servePassage(kernelApi, command)
                print(result)
            elif kind == "query":
                (result, total) = serveQuery(kernelApi, command)
                print(result)
                print(f"{total} results")

    except KeyboardInterrupt:
        console("\nquitting")
        return


if __name__ == "__main__":
    main()
