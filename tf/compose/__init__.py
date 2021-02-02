"""
# Combining data

This package contains functions to operate on TF datasets as a whole

There are the following basic operations:

* Modify, see `tf.compose.modify`,
  (add/merge/delete types and features to/from a single data source)
* Combine, see `tf.compose.combine`, (combine several data sources into one)
* Node maps, see `tf.compose.nodemaps`, (make node mappings between versions of TF data)

See also the
[compose chapter](https://nbviewer.jupyter.org/github/annotation/tutorials/blob/master/banks/compose.ipynb)
in the Banks tutorial.
"""


from .modify import modify
from .combine import combine
from .nodemaps import Versions
