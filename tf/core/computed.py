"""
.. include:: ../../docs/core/computed.md
"""


class Computeds(object):
    pass


class Computed(object):
    """Provides access to precomputed data.

    For component `ccc` it is the result of `C.ccc` or `Cs('ccc')`.
    """

    def __init__(self, api, data):
        self.api = api
        self.data = data
