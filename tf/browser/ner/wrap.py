"""Wraps various pieces into HTML.
"""

from textwrap import dedent


def wrapEntityHeaders(sortKey, sortDir):
    """HTML for the header of the entity table.

    Dependent on the state of sorting.

    Parameters
    ----------
    sortKey: string
        Indicator of how the table is sorted.
    sortDir:
        Indicator of the direction of the sorting.

    Returns
    -------
    HTML string

    """
    html = []
    html.append("<span>")

    for (label, key) in (
        ("Frequency", "freqsort"),
        ("Kind", "kindsort"),
        ("Text", "etxtsort"),
    ):
        theDir = sortDir if key == sortKey else "u"
        theArrow = "↑" if theDir == "u" else "↓"
        html.append(
            dedent(
                f"""
                <span>{label}<button type="submit" name="{key}" value="{theDir}"
                >{theArrow}</button><span>
                """
            )
        )

    html.append("</span><br>\n")
    return "".join(html)


def wrapEntityKinds(kinds):
    """HTML for the kinds of entities.

    Parameters
    ----------
    kinds: tuple of tuples
        Frequency list of entity kinds

    Returns
    -------
    HTML string
    """
    html = []

    for (kind, freq) in kinds:
        html.append(
            dedent(
                f"""
                <span><code class="w">{freq:>5}</code> x
                <button type="submit" value="v">{kind}</button>
                </span><br>
                """
            )
        )

    html.append("</span><br>\n")
    return "".join(html)
