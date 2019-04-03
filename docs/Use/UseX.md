# Advanced Guide

Here are hints to help you to get the most out of Text-Fabric apps.

**For the full reference, start with [Use](Use.md).**

## Incantation 

Start an app like this: 

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

There is a command

```sh
text-fabric-zip
```

to make a distribution of your own features.

For a guide through all the steps of data sharing, see [Data](../Api/Data.md)
and for examples see the
[share]({{tutnb}}/bhsa/share.ipynb)
tutorial.

## Using new data

The `text-fabric` command has several optional command line arguments: 

`--mod=...` and `-c`

By means of these arguments you can load extra features, either from your own
system, or from GitHub.

```sh
text-fabric bhsa --mod=etcbc/valence/tf
```

or if you want to check for new versions online:

```sh
text-fabric bhsa --mod=etcbc/valence/tf
```

See the [incantation](../Api/App.md#incantation).

## Using old data and apps

It is even possible to go back to earlier versions of the data and apps,
which might be needed if you want to reproduce results obtained with
those versions.

For app and data, you can add specifiers to point to a specific
release or commit.

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
