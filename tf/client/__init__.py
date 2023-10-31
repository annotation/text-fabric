"""
# Layered Search

A search interface for TF datasets.
The interface is purely client side, written in JavaScript.
It depends on corpus data generated from the underlying TF data
of a corpus.

This repo contains the machinery to generate such an interface,
based on essentially two parameters:

*   a bunch of configuration details;
*   a piece of code that generates the search data.

See also:

*   `tf.about.clientmanual`
*   `tf.client.make.build`

## Author

**Author**:
[Dirk Roorda](https://pure.knaw.nl/portal/en/persons/dirk-roorda)

## Acknowledgments

Layered search has been developed first in a project for the
[NENA corpus developed at Cambridge](https://github.com/CambridgeSemiticsLab/nena_tf).

Thanks to Cody Kingham for developing the foundational ideas and to Geoffrey Khan
for funding the project.
Thanks to DANS for giving me the space to turn these ideas into a product and
developing them further.
"""
