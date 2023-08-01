"""TF backend processing.

This module is for functions that extract data from the corpus
and put it in various dedicated data structures.
"""

from .tables import composeE


def entities(app, sortKey, sortDir):
    """Retrieves the entities and puts them in a table.

    app: object
        The TF app of the corpus in question.
    sortKey: string
        Indicator of how the table is sorted.
    sortDir:
        Indicator of the direction of the sorting.

    Returns
    -------
    HTML string
    """

    api = app.api
    F = api.F
    T = api.T

    entities = {}

    for e in F.otype.s("ent"):
        txt = T.text(e)
        kind = F.kind.v(e)
        entities.setdefault((kind, txt), []).append(e)

    return composeE(app, entities, sortKey, sortDir)


def entityKinds(app):
    """Retrieves a frequency list of entities and presents it.

    app: object
        The TF app of the corpus in question.

    Returns
    -------
    HTML string
    """

    api = app.api
    F = api.F

    return sorted(F.kind.freqList(nodeTypes={"ent"}))
