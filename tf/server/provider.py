"""Retrieves data from a TF kernel and provides it to an application.
"""

import sys
import pickle

from ..applib.app import findApp, findAppConfig
from ..server.kernel import makeTfConnection

from .serve import TIMEOUT


class TfProvider:
    def __init__(self, appName, checkoutApp=""):
        (commit, release, local, appBase, appDir) = findApp(appName, checkoutApp)
        if not appBase:
            return
        appPath = f"{appBase}/{appDir}"
        config = findAppConfig(appName, appPath)
        if config is None:
            return None

        self.TF = makeTfConnection(config.HOST, config.PORT["kernel"], TIMEOUT)
        self.appName = appName

    def passage(
        self, sec0, sec1=None, sec2=None, baseTypes=None, features=None, query=None
    ):
        TF = self.TF
        kernelApi = TF.connect()
        if type(kernelApi) is str:
            sys.stderr.write(
                f"""{kernelApi}\n"""
                f"""Make sure a kernel for TF app "{self.appName}" is running\n"""
            )
            return None

        passages = kernelApi.passage(
            features, query, sec0, sec1=sec1, sec2=sec2, baseTypes=baseTypes, asDict=True,
        )
        return pickle.loads(passages)
