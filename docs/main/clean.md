# Clean

From version 7.7.7 onwards, Text-Fabric uses a parameter `tf.parameters.PACK_VERSION`
to mark the stored pre-computed data.
Whenever there are incompatible changes in the packed data format, this
version number will be increased and Text-Fabric will not attempt to load
the older pre-computed data.

The older data will not be removed, however.
Use the function `clean` to get rid of pre-computed data
that you no longer need.
