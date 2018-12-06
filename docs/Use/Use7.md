# v7 Guide

Here are hints to help you to get the most out version 7 of Text-Fabric.

**For the full reference, start with [Use](Use.md).**

## Incantation 

The old incantations `B = Bhsa()` and `CN = Cunei()` do no longer work.

The new way is as follows:

```python
from tf.app import use
A = use('bhsa', hoist=globals())
```

```python
from tf.app import use
A = use('uruk', hoist=globals())
```

Read more in the [App API](../Api/App.md#incantation)

## Zipping your new data

There is a new command

```sh
text-fabric-zip
```

to make a distribution of your own features.

For a guide through all the steps of data sharing, see [Data](../Api/Data.md)
and for examples see the
[share]({{etcbcnb}}/bhsa/blob/master/tutorial/share.ipynb)
tutorial.

## Using new data

The `text-fabric` command has several new optional command line arguments: 

`--mod=...` and `-c`

By means of these arguments you can load extra features, either from your own
system, or from GitHub.

```sh
text-fabric --mod=bhsa etcbc/valence/tf
```

or if you want to check for new versions online:

```sh
text-fabric --mod=bhsa etcbc/valence/tf
```

See the [incantation](../Api/App.md#incantation).

Read more about your data life-cycle in the [Data](../Api/Data.md) guide.

## Custom sets

You can create custom sets of nodes, give them a name, and use those names
in search templates. 
The TF browser can import those sets, so that you can use such queries in the browser too.

```sh
text-fabric appname --sets=filePath
```

Read more in [Browser](Browser.md#custom-sets).

## Display

The way you control the display parameters for the functions `pretty()` and `plain()`
and friends has changed. See [Display](../Api/App.md#display).
