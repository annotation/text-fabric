# v7 Guide

Here are hints to help you to get the most out version 7 of Text-Fabric.

## Add and distribute and use new data

See the
[share](https://nbviewer.jupyter.org/github/etcbc/bhsa/blob/master/tutorial/share.ipynb)
tutorial.

For a guide through all the steps of data sharing, see [Add](Add.md).
There it is also explained how you can invoke the new command

```sh
text-fabric-zip
```

to make a distribution of your own features.

## Start TF browser

The `text-fabric` command as two new optional command line arguments: 

`--mod=...` and `-c`.

```sh
text-fabric appname --mod=module1,module2
```

Start a TF browser for appname (such as `bhsa`).

Loads extra data from module1 and module2, to be found in a github repo specfied by the 
module strings.

You can specify as many modules as you want.

The module sgtring must have the form

```
{org}/{repo}/{path}
```

where:

* `{org}` is the organization or person on GitHub,
* `{repo}` is the repository on GitHub,
* `{path}` is the path within the repository to the tf directory.

See also the [Add](Add.md) manual.

You can optionally pass the flag `-c`.
In that case Text-Fabric will check whether a new release of the data is available.
If so, it will download and install it.
This will happen for the main data and all modules specified on the command line.

TF will always download the data to your `~/text-fabric-data` directory.

## Incantation 

The old incantation `B = Bhsa()` and `CN = Cunei()` do no longer work.

The new way is as follows:

```python
from tf.app import use
A = use('bhsa', hoist=globals())
```

```python
from tf.app import use
A = use('uruk', hoist=globals())
```

Note that we no longer use `cunei` as name of the corpus, but the more precise `uruk`.

You see that the app name (`bhsa`, `uruk`) is only used once, as first argument for the
`use()` function.

Think of the `use database` in MySQL and MongoDb.

The remaining arguments of `use()` are the same as you passed before to `Bhsa()` and `Cunei()`.
But there are a few more: `mod` and `check`.

They have the same effect as `--mod=` and `-c` when calling the browser:

* `mod` is a comma-separated list of modules in the form `{org}/{repo}/{path}`;
* `check=False` is an optional boolean argument.

Without further arguments, this will set up an TF api with most features loaded.

If you want to add other search locations for tf features manually, you can pass
optional `locations` and `modules` parameters, which will be passed to the underlying
[Fabric()](Api/General.md#loading) call.

If you want even more control, you can first set up your own TF api in the classical way,
by first calling

```python
TF = Fabric(locations=..., modules=...)
api = TF.load(features)
```

and then

```python
A = use('bhsa', api=api)
```

## See the new data

The features of the data modules you have imported are available in the same way as all other features.

You can use them in queries.

### In the TF browser

In the browser, pretty displays will show them automatically, because starting in this version,
all features that used in query are displayed in the expanded view.

If you want to see a feature that is not used in the query, you can add it as a trivial search criterion.

For example, if you want to see the `sense` feature when looking for phrases, add it like this

```
clause
  phrase sense*
```

The `*` means: always true, so it will not influence the query result set, only its display.

The extra data modules are also shown in the provenance listings when you export data from the browser.

### In a Jupyter notebook

After the incantation, you see an overview of all features per module where they come from, and
linked to their documentation or repository.

You can use the new features exactly as you are used to, with `F` and `E` (for edge features).

They will not automatically show up in `pretty` displays, because `pretty` does not know that it is
displaying query results, it can display arbitrary nodes.

So you have to tell which features you want to add to the display.
That can be done by [prettySetup](Api/Apps.md#pretty-display):

```python
A.prettySetup(features='sense')
```

and from then on the value of `sense` will be shown
on every item that has a real value for the feature `sense`.

You can cancel it by calling

```python
A.prettySetup()
```






