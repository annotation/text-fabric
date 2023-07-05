"""
Produce exports of the whole dataset in different formats.

This module supposes that you have installed Pandas and pyarrow:

```
pip install pandas pyarrow
```

Currently only Pandas is supported here,

although there is also an export to MQL elsewere:

`tf.convert.mql`
"""

import types

from ..convert.mql import exportMQL
from ..convert.pandas import exportPandas


def interchangeApi(app):
    """Produce the interchange functions API.

    Parameters
    ----------
    app: obj
        The high-level API object
    """

    app.exportMQL = types.MethodType(exportMQL, app)
    app.exportPandas = types.MethodType(exportPandas, app)
