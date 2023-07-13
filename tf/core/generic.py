class AttrDict(dict):
    """Turn a dict into an object with attributes.

    If non-existing attributes are accessed for reading, `None` is returned.

    See:
    https://stackoverflow.com/questions/4984647/accessing-dict-keys-like-an-attribute

    And:
    https://stackoverflow.com/questions/16237659/python-how-to-implement-getattr
    (especially the remark that

    > `__getattr__` is only used for missing attribute lookup

    )

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
    """Turns an AttrDict into a dict, recursively.

    Parameters
    ----------
    info: any
        The input dictionary. We assume that it is a data structure built by
        tuple, list, set, frozenset, dict and atomic types such as int, str, bool.
        We assume there are no user defined objects in it,
        and no generators and functions.

    Returns
    -------
    dict
        An dict containing the same info as the input dict, but where
        each value of type AttrDict is turned into a dict.
    """
    return (
        dict({k: deepdict(v) for (k, v) in info.items()})
        if type(info) in {dict, AttrDict}
        else tuple(deepdict(item) for item in info)
        if type(info) is tuple
        else frozenset(deepdict(item) for item in info)
        if type(info) is frozenset
        else [deepdict(item) for item in info]
        if type(info) is list
        else {deepdict(item) for item in info}
        if type(info) is set
        else info
    )


def deepAttrDict(info):
    """Turn a dict into an AttrDict, recursively.

    Parameters
    ----------
    info: any
        The input dictionary. We assume that it is a data structure built by
        tuple, list, set, frozenset, dict and atomic types such as int, str, bool.
        We assume there are no user defined objects in it,
        and no generators and functions.

    Returns
    -------
    AttrDict
        An AttrDict containing the same info as the input dict, but where
        each value of type dict is turned into an AttrDict.
    """
    return (
        AttrDict({k: deepAttrDict(v) for (k, v) in info.items()})
        if type(info) in {dict, AttrDict}
        else tuple(deepAttrDict(item) for item in info)
        if type(info) is tuple
        else frozenset(deepAttrDict(item) for item in info)
        if type(info) is frozenset
        else [deepAttrDict(item) for item in info]
        if type(info) is list
        else {deepAttrDict(item) for item in info}
        if type(info) is set
        else info
    )
