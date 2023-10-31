"""
# Volume operations

This package contains functions to support works and their volumes in TF.

There are the following basic operations:

*   Collect, see `tf.volumes.collect`, (collect several volumes into one work)
*   Extract, see `tf.volumes.extract`, (extract volumes from a work)

"""


from .collect import collect
from .extract import extract, getVolumes
