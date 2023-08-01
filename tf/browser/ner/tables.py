"""Module to compose tables of result data.
"""


def composeE(app, entities, sortKey, sortDir):
    """Compose a table of entities with selection and sort controls.

    Parameters
    ----------
    app: object
        The TF app of the corpus in question.
    entities: dict
        The entities as already present in the dataset, usually the result of the
        NLP pipeline.
    sortKey: string
        Indicates how to sort the table:

        *   `freqsort`: by the frequency of the entities
        *   `kindsort`: by the kind of the entities
        *   `etxtsort`: by the text of the entities

    sortDir: string
        Indicates the direction of the sort:

        *   `u`: up, i.e. ascending
        *   `d`: down, i.e. descending

    Returns
    -------
    html string
        The finished HTML of the table, ready to put into the Flask template.
    """

    html = []

    entries = entities.items()
    if sortKey == "freqsort":
        if sortDir == "u":
            entries = sorted(entries, key=lambda x: (len(x[1]), x[0][1], x[0][0]))
        else:
            entries = sorted(entries, key=lambda x: (-len(x[1]), x[0][1], x[0][0]))
    elif sortKey == "kindsort":
        entries = sorted(entries, key=lambda x: (x[0][0], x[0][1], -len(x[1])))
        if sortDir == "d":
            entries = reversed(entries)
    elif sortKey == "etxtsort":
        entries = sorted(entries, key=lambda x: (x[0][1], x[0][0], -len(x[1])))
        if sortDir == "d":
            entries = reversed(entries)

    for ((kind, txt), es) in entries:
        x = len(es)
        item = (
            f"""<span><code class="w">{x:>5}</code> x <b>{kind}</b> {txt}</span><br>"""
        )
        html.append(item)

    return "\n".join(html)
