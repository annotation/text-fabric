"""
# Dataset operations

This package contains functions to operate on TF datasets as a whole

There are the following basic operations:

*   Modify, see `tf.dataset.modify`,
    (add/merge/delete types and features to / from a single data source)
*   Node maps, see `tf.dataset.nodemaps`,
    (make node mappings between versions of TF data)

See also the
[dataset chapter](https://nbviewer.jupyter.org/github/annotation/banks/blob/master/tutorial/compose.ipynb)
in the Banks tutorial.
"""


from .modify import modify  # NOQA F401
from .nodemaps import Versions  # NOQA F401
