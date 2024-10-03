from ..html import H


SORTDIR_DESC = "d"
"""Value that indicates the descending sort direction."""

SORTDIR_ASC = "a"
"""Value that indicates the ascending sort direction."""

SORTDIR_DEFAULT = SORTDIR_ASC
"""Default sort direction."""

SORTKEY_DEFAULT = "freqsort"
"""Default sort key."""

SORT_DEFAULT = (SORTKEY_DEFAULT, SORTDIR_DESC)
"""Default sort key plus sort direction combination."""

SC_ALL = "a"
"""Value that indicates *all* buckets."""

SC_FILT = "f"  # not actually used!
"""Value that indicates *filtered* buckets."""

LIMIT_BROWSER = 100
"""Limit of amount of buckets to load on one page when in the TF browser.

This is not a hard limit. We only use it if the page contains the whole corpus or
a filtered subset of it.

But as soon we have selected a token string or an entity, we show all buckets
that contain it, no matter how many there are.

!!! note "Performance"
    We use the
    [CSS device *content-visibility*](https://developer.mozilla.org/en-US/docs/Web/CSS/content-visibility)
    to restrict rendering to the material that is visible in the viewport. However,
    this is not supported in Safari, so the performance may suffer in Safari if we load
    the whole corpus on a single page.

    In practice, even in browsers that support this device are not happy with a big
    chunk of HTML on the page, since they do have to build a large DOM, including
    event listeners.

    That's why we restrict the page to a limited amount of buckets.

    But when a selection has been made, it is more important to show the whole,
    untruncated result set, than to incur a performance penalty.
    Moreover, it is hardly the case that a selected entity of occurrence occurs in a
    very large number of buckets.
"""

LIMIT_NB = 20
"""Limit of amount of buckets to load on one page when in a Jupyter notebook.

See also `LIMIT_BROWSER` .
"""


def valRep(features, fVals):
    """HTML representation of an entity as a sequence of `feat=val` strings."""
    return ", ".join(f"<i>{feat}</i>={val}" for (feat, val) in zip(features, fVals))


def repIdent(features, vals, active=""):
    """Represents an identifier in HTML.

    Parameters
    ----------
    vals: iterable
        The material is given as a list of feature values.
    active: string, optional ""
        A CSS class name to add to the HTML representation.
        Can be used to mark the entity as active.
    """
    return H.join(
        (H.span(val, cls=f"{feat} {active}") for (feat, val) in zip(features, vals)),
        sep=" ",
    )


def repSummary(keywordFeatures, vals, active=""):
    """Represents an keyword value in HTML.

    Parameters
    ----------
    vals: iterable
        The material is given as a list of values of keyword features.
    active: string, optional ""
        A CSS class name to add to the HTML representation.
        Can be used to mark the entity as active.
    """
    return H.join(
        (
            H.span(val, cls=f"{feat} {active}")
            for (feat, val) in zip(keywordFeatures, vals)
        ),
        sep=" ",
    )
