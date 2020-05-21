import sys
from ..core.helpers import console
from ..server.kernel import makeTfConnection
from ..parameters import HOST
from .command import argKernel

TIMEOUT = 180


def main(cargs=sys.argv):
    args = argKernel(cargs)
    if not args:
        return

    (dataSource, portKernel) = args

    TF = makeTfConnection(HOST, portKernel, TIMEOUT)
    if TF is None:
        return

    commands = {
        "1": "searchExe",
        "2": "_msgCache",
    }
    commandText = "\n".join(f"[{k:>2}] {v}" for (k, v) in commands.items())
    try:
        while True:
            kernelApi = TF.connect()
            number = input(f"{commandText}\nenter number: ")
            command = commands[number]
            data = kernelApi.monitor()
            console(f"{command} = {data[command]}\n")
    except KeyboardInterrupt:
        console("\nquitting")
        return


if __name__ == "__main__":
    main()
