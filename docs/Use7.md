# v7 Guide

Here are hints to help you to get the most out version 7 of Text-Fabric.

## Working with new data

There is a new command

```sh
text-fabric-zip
```

to make a distribution of your own features.

For a guide through all the steps of data sharing, see [Add](Add.md)
and for examples see the
[share]({{etcbcnb}}/bhsa/blob/master/tutorial/share.ipynb)
tutorial.


## TF browser command

The `text-fabric` command as two new optional command line arguments: 

`--mod=...` and `-c`.

```sh
text-fabric appname --mod=module1,module2
```

* Start a TF browser for appname (such as `bhsa`).
* Loads extra data from `module1` and `module2`,
  to be found in a github repo specfied by the 
  module strings.
* You can specify as many modules as you want.

The module strings must have the form

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

??? hint "do not modify yourself"
    You can better leave your `~/text-fabric-data` under control
    of Text-Fabric, and not manually add data there.
    It does not much harm to delete data from here, because TF will download
    missing data automatically when needed.

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

Note that we no longer use `cunei` as name of the corpus, but the more precise `uruk`.

You see that app names (`bhsa`, `uruk`) are used once in the incantation, as first argument for the
`use()` function.

Think of the `use {database}` statements in MySQL and MongoDb.

Without further arguments, this will set up an TF API with most features loaded.

The remaining arguments of `use()` are the same as you passed before to `Bhsa()` and `Cunei()`.
But there are a few more optional ones: `mod` and `check`.

They have the same effect as `--mod=` and `-c` when calling the browser:

* `mod` is a comma-separated list of modules in the form `{org}/{repo}/{path}`;
* `check=False` is a boolean argument.

If you want to add other search locations for tf features manually, you can pass
optional `locations` and `modules` parameters, which will be passed to the underlying
[Fabric()](Api/General.md#loading) call.

If you want even more control, you can first set up your own TF API in the classical way,
by calling

```python
TF = Fabric(locations=..., modules=...)
api = TF.load(features)
```

and then wrapping the app API around it:

```python
A = use('bhsa', api=api)
```

## See the new data

The features of the data modules you have imported are available in the same way as all other features.

You can use them in queries.

### In the TF browser

In the browser, pretty displays will show them automatically, because
all features used in a query are displayed in the expanded view.

If you want to see a feature that is not used in the query, you can add it as a trivial search criterion.

For example, if you want to see the `sense` feature when looking for phrases, add it like this

```
clause
  phrase sense*
```

* The `*` means: always true, so it will not influence the query result set, only its display;
* In fact, the feature sense is only present on nodes of type `word`. But mentioning a feature anywhere in the query
  will trigger the display wherever it occurs with a non-trivial values.
* The extra data modules are also shown in the provenance listings when you export data from the browser.

### In a Jupyter notebook

After the incantation, you see an overview of all features per module where they come from, and
linked to their documentation or repository.

You can use the new features exactly as you are used to, with `F` and `E` (for edge features).

They will not automatically show up in `pretty` displays, because `pretty` does not know that it is
displaying query results, and hence does not know which features were used in the latest query.

So you have to tell which features you want to add to the display.
That can be done by [prettySetup](Api/Apps.md#pretty-display):

```python
A.prettySetup(features='sense')
```

and from then on the value of `sense` will be shown
on every item that has a real value for the feature `sense`.

You can cancel the extra features by

```python
A.prettySetup()
```






