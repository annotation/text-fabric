"""Machinery for request reading.

All form data comes as key value pairs where the values are strings.
We need more streamlined values, in several data types and organizations.
Also we need defaults for missing and / or empty values.
"""

from urllib.parse import unquote

from flask import request

from ...core.files import readJson
from ...core.generic import AttrDict


class Form:
    def __init__(
        self,
        features,
        defaults,
        keysStr=[],
        keysBool=[],
        keysTri=[],
        keysInt=[],
        keysTup=[],
        keysSetInt=[],
        keysJson=[],
    ):
        """Remember the specification of data types and organization for form values.

        Parameters
        ----------
        features: list
            The entity features in the tool; derives ultimately from
            `tf.ner.settings.Settings`, which reads the
            `ner/config.yaml` file.
        defaults: dict
            Provides default values for form keys with a missing or empty value.
            If the default should be a `None`, `False` or empty string value,
            nothing has to be specified. Only if the default is a specific
            meaningful value, it needs to be specified.
        keysStr,keysBool,keysTri,keysInt,keysTup,keysSetInt,keysJson: list
            See `tf.browser.ner.request.Request`.
        """
        self.features = features
        self.defaults = defaults
        self.keysStr = keysStr
        self.keysBool = keysBool
        self.keysTri = keysTri
        self.keysInt = keysInt
        self.keysTup = keysTup
        self.keysSetInt = keysSetInt
        self.keysJson = keysJson

    def fgets(self, k):
        """Makes form value under key `k` or its default into an string."""
        defaults = self.defaults
        return request.form.get(k, defaults.get(k, ""))

    def fget2(self, k):
        """Makes form value under key `k` or its default into an boolean."""
        defaults = self.defaults
        return request.form.get(k, defaults.get(k, "x")) == "v"

    def fget3(self, k):
        """Makes form value under key `k` or its default into a 3-way boolean."""
        formValue = self.fgets(k)
        return True if formValue == "v" else False if formValue == "x" else None

    def fgeti(self, k):
        """Makes form value under key `k` or its default into an integer."""
        formValue = self.fgets(k)
        return int(formValue) if formValue and formValue.isdecimal() else None

    def fgettu(self, k):
        """Makes form value under key `k` or its default into a tuple.

        The values in the tuples are strings.
        The values are retrieved by splitting the original string value on `⊙` .
        """
        formValue = self.fgets(k)
        return tuple(formValue.split("⊙")) if formValue else None

    def fgetsi(self, k):
        """Makes form value under key `k` or its default into a set.

        The values in the set are integers.
        The values are retrieved by splitting the original string value on `,` .
        Parts that do not form valid integers are skipped.
        """
        formValue = self.fgets(k)
        return (
            {int(i) for s in formValue.split(",") if (i := s.strip()).isdecimal()}
            if formValue
            else set()
        )

    def fgetj(self, k):
        """Makes form value under key `k` or its default into a data structure.

        The data structure is retrieved by interpreting the original string as
        quoted JSON.
        """
        formValue = self.fgets(k)

        return AttrDict() if formValue == "" else readJson(text=unquote(formValue))

    def fill(self):
        """Fill a dictionary with interpreted form values.

        The input data is the request data from Flask, the output data
        are the logical values derived from them by the methods in this class.

        Returns
        -------
        dict
            The filled in form.
        """
        keysStr = self.keysStr
        keysBool = self.keysBool
        keysTri = self.keysTri
        keysInt = self.keysInt
        keysTup = self.keysTup
        keysSetInt = self.keysSetInt
        keysJson = self.keysJson

        form = AttrDict()

        for k in keysStr:
            form[k] = self.fgets(k)

        for k in keysBool:
            form[k] = self.fget2(k)

        for k in keysTri:
            form[k] = self.fget3(k)

        for k in keysInt:
            form[k] = self.fgeti(k)

        for k in keysTup:
            form[k] = self.fgettu(k)

        for k in keysSetInt:
            form[k] = self.fgetsi(k)

        for k in keysJson:
            form[k] = self.fgetj(k)

        return form
