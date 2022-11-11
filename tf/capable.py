from textwrap import dedent
from importlib import import_module

from .core.helpers import console


class Capable:
    def __init__(self, *extras):
        self.backendProviders = set()
        self.canBrowse = False
        self.modules = {}
        self.tryImport(*extras)

    def tryImport(self, *extras):
        backendProviders = self.backendProviders
        modules = self.modules

        for kind in extras:
            if kind == "github":
                try:
                    import github

                    modules["github"] = github
                    backendProviders.add(kind)
                except Exception:
                    pass

            if kind == "gitlab":
                try:
                    import gitlab

                    modules["gitlab"] = gitlab
                    backendProviders.add(kind)
                except Exception:
                    pass

            elif kind == "browser":
                try:
                    import psutil
                    import rpyc
                    import flask

                    modules["psutil"] = psutil
                    modules["rpyc"] = rpyc
                    modules["flask"] = flask
                    self.canBrowse = True
                except Exception:
                    pass

        if backendProviders:
            try:
                import requests

                modules["requests"] = requests
            except Exception:
                backendProviders = set()

    def load(self, module):
        modules = self.modules
        loaded = modules.get(module, None)

        if loaded:
            return loaded

        try:
            loaded = import_module(module)
        except Exception:
            pass

        return loaded

    def loadFrom(self, module, *members):
        loaded = self.load(module)

        result = (
            tuple(getattr(loaded, member, None) for member in members)
            if loaded
            else tuple(None for x in members)
        )
        return result[0] if len(result) == 1 else result

    def can(self, extra):
        if extra in {"github", "gitlab"}:
            backendProviders = self.backendProviders

            if extra in backendProviders:
                return True

            console(
                dedent(
                    f"""
                    Backend provider {extra} not supported.
                    Cannot reach online data on {extra}
                    Try installing text-fabric one of the following:
                    pip install text-fabric[{extra}]
                    pip install text-fabric[all]
            """
                )
            )
            return False

        if extra == "browser":
            if self.canBrowse:
                return True

            console(
                dedent(
                    """
                    Text-Fabric browser not supported.
                    Try installing text-fabric one of the following:
                    pip install text-fabric[browser]
                    pip install text-fabric[all]
            """
                )
            )
            return False
