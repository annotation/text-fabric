class AttrDict(dict):
    """Turn a dict into an object with attributes.

    If non-existing attributes are accessed for reading, `None` is returned.

    See these links on stackoverflow:

    *   [1](https://stackoverflow.com/questions/4984647/accessing-dict-keys-like-an-attribute)
    *   [2](https://stackoverflow.com/questions/16237659/python-how-to-implement-getattr)
        especially the remark that

        > `__getattr__` is only used for missing attribute lookup

    We also need to define the `__missing__` method in case we access the underlying
    dict by means of keys, like `xxx["yyy"]` rather then by attribute like `xxx.yyy`.
    """

    def __init__(self, *args, **kwargs):
        """Create the data structure from incoming data."""
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

    def __missing__(self, key, *args, **kwargs):
        """Provide a default when retrieving a non-existent member.

        This method is used when using the `.key` notation for accessing members.
        """
        return None

    def __getattr__(self, key, *args, **kwargs):
        """Provide a default when retrieving a non-existent member.

        This method is used when using the `[key]` notation for accessing members.
        """
        return None

    def deepdict(self):
        return deepdict(self)


def deepdict(info):
    """Turns an `AttrDict` into a `dict`, recursively.

    Parameters
    ----------
    info: any
        The input dictionary. We assume that it is a data structure built by
        `tuple`, `list`, `set`, `frozenset`, `dict` and atomic types such as
        `int`, `str`, `bool`.
        We assume there are no user defined objects in it, and no generators
        and functions.

    Returns
    -------
    dict
        A dictionary containing the same info as the input dictionary, but where
        each value of type `AttrDict` is turned into a `dict`.
    """
    tp = type(info)

    return (
        dict({k: deepdict(v) for (k, v) in info.items()})
        if tp in {dict, AttrDict}
        else tuple(deepdict(item) for item in info)
        if tp is tuple
        else frozenset(deepdict(item) for item in info)
        if tp is frozenset
        else [deepdict(item) for item in info]
        if tp is list
        else {deepdict(item) for item in info}
        if tp is set
        else info
    )


def deepAttrDict(info, preferTuples=False):
    """Turn a `dict` into an `AttrDict`, recursively.

    Parameters
    ----------
    info: any
        The input dictionary. We assume that it is a data structure built by
        `tuple`, `list`, `set`, `frozenset`, `dict` and atomic types such as
        `int`, `str`, `bool`.
        We assume there are no user defined objects in it, and no generators
        and functions.
    preferTuples: boolean, optional False
        Lists are converted to tuples.

    Returns
    -------
    AttrDict
        An `AttrDict` containing the same info as the input dictionary, but where
        each value of type `dict` is turned into an `AttrDict`.
    """
    tp = type(info)

    return (
        AttrDict(
            {k: deepAttrDict(v, preferTuples=preferTuples) for (k, v) in info.items()}
        )
        if tp in {dict, AttrDict}
        else tuple(deepAttrDict(item, preferTuples=preferTuples) for item in info)
        if tp is tuple or (tp is list and preferTuples)
        else frozenset(deepAttrDict(item, preferTuples=preferTuples) for item in info)
        if tp is frozenset
        else [deepAttrDict(item, preferTuples=preferTuples) for item in info]
        if tp is list
        else {deepAttrDict(item, preferTuples=preferTuples) for item in info}
        if tp is set
        else info
    )


def isIterable(value):
    """Whether a value is a non-string iterable.

    !!! note
        Strings are iterables.
        But for this purpose we regard strings as non-iterable scalars.
    """

    return type(value) is not str and hasattr(value, "__iter__")
