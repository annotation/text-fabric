"""
Produce exports of the whole dataset in different formats.

Currently only Pandas is supported here,

although there is also an export to MQL elsewere:

`tf.convert.mql`
"""

import types

from ..convert.pandas import makeTable


def exportApi(app):
    """Produce the export functions API.

    Parameters
    ----------
    app: obj
        The high-level API object
    """

    app.exportPandas = types.MethodType(makeTable, app)
