# Adding data modules

Text-Fabric supports the flow of creating research data,
packaging it, distributing it, and importing in apps.

## Assumptions

The data sharing workflow is built around the following assumptions:

??? note "main corpus app"
    You work with a main corpus for which a text-fabric app is available.
    See [Corpora](../About/Corpora.md)

??? note "versioned tf data"
    The data you share consists of a set of TF features, tied to a specific
    *version* of the main corpus, preferably the most recent version.
    The new features must sit in a directory named after the version
    of the main corpus they correspond to.

??? note "local github"
    The data you share must reside in a directory on your hard drive.
    The convention is, that you have a directory `github` under your
    home directory. And inside `github`, you have directories for
    organizations or people first, and then repositories, exactly as 
    the online GitHub is organized. 

    Your own data should be in such a repo as well, e.g.

    `ch-jensen/Semantic-mapping-of-participants/actor/tf`

    or

    `etcbc/lingo/heads/tf`

??? note "synchronized with GitHub"
    You must have your local repo contents synchronized with that on GitHub

??? note "online GitHub"
    Before you share your data, you must make a *release* on GitHub.
    Then you must attach your features as a zip file to that release.
    Text-Fabric has a command to produce a zip file with exactly the
    right structure and name.

??? note "get data"
    In order to get data, the only thing Text-Fabric needs to know,
    is a string with the organisation or person, the repository,
    and the path within the repository.

    Based on the string `{org}/{repo}/{path}` it will find the online
    repository, check the latest release, find the zip file,
    download and expand it to your local
    `~/text-fabric/data/{org}/{repo}/{path}`
    
??? note "everywhere"
    The extra data is accessible whether you work in a Jupyter notebook,
    or in the Text-Fabric browser.
    The extra features are clearly listed after the incantation in a notebook,
    and they show up in the pretty displays in the TF browser.
    And when you export data from the TF browser, all data modules are reported
    in the provenance section.

## Step by step

### Data in place

We use the existing [etcbc/valence/tf]({{etcbcgh}}/valence) data as an example.

We assume you have this data locally, in 

```
~/github/etcbc/valence/tf
```

under which there are versions such as `c`, `2017`, which contain the actual `.tf` files.

### Package into zip files

To create zip files for the data, execute the following command in your terminal:

```sh
text-fabric-zip etcbc/valence/tf
```

You'll see

```
zipping etcbc/valence             2016 with  10 features
zipping etcbc/valence             2017 with  10 features
zipping etcbc/valence                4 with  10 features
zipping etcbc/valence               4b with  10 features
zipping etcbc/valence                c with  10 features
```

and as a result you have this in your Downloads folder

```
~/Downloads/etcbc-release/valence/
    tf-4.zip
    tf-4b.zip
    tf-2016.zip
    tf-2017.zip
    tf-c.zip
```
        
### Make a release

Locally, commit your changes and push them to GitHub

```sh
git add --all .
git commit -m "releasing data"
git push origin master
```

**You can only do this for repositories for which you have write access,
so do not try to perform this on `etcbc/valence` but use a repo of your own.**

Go to the online version on GitHub, and click *releases*

![releases](../images/add-releases.png)

Then click *Draft a new release*

![releases](../images/add-draft.png)

Fill in the details, especially the version (something like `1.6`),
although nothing in the workflow depends on the exact form of the version number;
you will see the release version in the provenance, though.

Do not forget to select your freshly made zip files
(you can select and upload them in one go).

Last, but not least, click the button *Publish release*.

![releases](../images/add-attach.png)

Now your data is available to others.

### Use data

The valence data has been made available by the ETCBC, so the following steps
you can perform literally.

#### In the TF browser

Start the TF browser as follows:

```sh
text-fabric bhsa --mod=etcbc/valence/tf
```

You will see that the valence data is being used.
If you do not have `~/github/etcbc/valence/tf`
nor `~/text-fabric-data/etcbc/valence/tf`
data will be downloaded and expanded to the
latter location.

??? note "output when loading new data"
    ```
    Setting up TF kernel for bhsa etcbc/valence/tf
    Using etcbc/bhsa - c r1.5 in ~/text-fabric-data/etcbc/bhsa/tf/c
    Using etcbc/phono - c r1.2 in ~/text-fabric-data/etcbc/phono/tf/c
    Using etcbc/parallels - c r1.2 in ~/text-fabric-data/etcbc/parallels/tf/c
      downloading etcbc/valence - c r1.1
      from https://github.com/etcbc/valence/releases/download/1.1/tf-c.zip ...
      unzipping ...
      saving etcbc/valence - c r1.1
      saved etcbc/valence - c r1.1
    Using etcbc/valence - c r1.1 (=latest) in ~/text-fabric-data/etcbc/valence/tf/c
       |     0.29s T cfunction            from /Users/dirk/text-fabric-data/etcbc/valence/tf/c
       |     0.23s T f_correction         from /Users/dirk/text-fabric-data/etcbc/valence/tf/c
       |     0.46s T grammatical          from /Users/dirk/text-fabric-data/etcbc/valence/tf/c
       |     0.31s T lexical              from /Users/dirk/text-fabric-data/etcbc/valence/tf/c
       |     0.23s T original             from /Users/dirk/text-fabric-data/etcbc/valence/tf/c
       |     0.46s T predication          from /Users/dirk/text-fabric-data/etcbc/valence/tf/c
       |     0.23s T s_manual             from /Users/dirk/text-fabric-data/etcbc/valence/tf/c
       |     0.31s T semantic             from /Users/dirk/text-fabric-data/etcbc/valence/tf/c
       |     0.14s T sense                from /Users/dirk/text-fabric-data/etcbc/valence/tf/c
       |     0.47s T valence              from /Users/dirk/text-fabric-data/etcbc/valence/tf/c
    TF setup done.
    ```

If you run it a second time, all data is in place.

??? note "output when all data is in place"
    ```
    Setting up TF kernel for bhsa etcbc/valence/tf
    Using etcbc/bhsa - c r1.5 in ~/text-fabric-data/etcbc/bhsa/tf/c
    Using etcbc/phono - c r1.2 in ~/text-fabric-data/etcbc/phono/tf/c
    Using etcbc/parallels - c r1.2 in ~/text-fabric-data/etcbc/parallels/tf/c
    Using etcbc/valence - c r1.1 in ~/text-fabric-data/etcbc/valence/tf/c
    TF setup done.
    ```

If you have reasons to think that there is a new release of any of the data
involved, you can pass the `-c` switch:

```sh
text-fabric bhsa --mod=etcbc/valence/tf -c
```

??? note "output when all checking for data updates"
    ```
    Loading data for bhsa. Please wait ...
    Setting up TF kernel for bhsa etcbc/valence/tf
    No new data release available online.
    Using bhsa - c r1.5 (=latest) in ~/text-fabric-data/etcbc/bhsa/tf/c.
    No new data release available online.
    Using phono - c r1.2 (=latest) in ~/text-fabric-data/etcbc/phono/tf/c.
    No new data release available online.
    Using parallels - c r1.2 (=latest) in ~/text-fabric-data/etcbc/parallels/tf/c.
    No new data release available online.
    Using valence - c r1.1 (=latest) in ~/text-fabric-data/etcbc/valence/tf/c.
    TF setup done.
    ```

And if there is a new release for the valence data, it will be downloaded.

??? note "output when updating a data module"
    ```
    Setting up TF kernel for bhsa etcbc/valence/tf
    No new data release available online.
    Using bhsa - c r1.5 (=latest) in ~/text-fabric-data/etcbc/bhsa/tf/c.
    No new data release available online.
    Using phono - c r1.2 (=latest) in ~/text-fabric-data/etcbc/phono/tf/c.
    No new data release available online.
    Using parallels - c r1.2 (=latest) in ~/text-fabric-data/etcbc/parallels/tf/c.
      downloading etcbc/valence - c r1.1
      from https://github.com/etcbc/valence/releases/download/1.1/tf-c.zip ...
      unzipping ...
      saving etcbc/valence - c r1.1
      saved etcbc/valence - c r1.1
    Using etcbc/valence - c r1.1 (=latest) in ~/text-fabric-data/etcbc/valence/tf/c
       |     0.30s T cfunction            from /Users/dirk/text-fabric-data/etcbc/valence/tf/c
       |     0.23s T f_correction         from /Users/dirk/text-fabric-data/etcbc/valence/tf/c
       |     0.47s T grammatical          from /Users/dirk/text-fabric-data/etcbc/valence/tf/c
       |     0.32s T lexical              from /Users/dirk/text-fabric-data/etcbc/valence/tf/c
       |     0.23s T original             from /Users/dirk/text-fabric-data/etcbc/valence/tf/c
       |     0.47s T predication          from /Users/dirk/text-fabric-data/etcbc/valence/tf/c
       |     0.23s T s_manual             from /Users/dirk/text-fabric-data/etcbc/valence/tf/c
       |     0.32s T semantic             from /Users/dirk/text-fabric-data/etcbc/valence/tf/c
       |     0.14s T sense                from /Users/dirk/text-fabric-data/etcbc/valence/tf/c
       |     0.49s T valence              from /Users/dirk/text-fabric-data/etcbc/valence/tf/c
    TF setup done.
    ```

You can now use the new features in the TF browser.

Fill out this query:

```
book book=Genesis
  chapter chapter=1
    clause
      phrase sense*
```

and expand the first result in Genesis 1:1.

The display looks like this:

![sense](../images/add-sense.png)

And if you export the data, the extra module is listed in the provenance.

![sense](../images/add-prov.png)

??? hint "Feature display"
    Pretty displays will show them automatically, because
    all features used in a query are displayed in the expanded view.

    If you want to see a feature that is not used in the query
    you can add it as a trivial search criterion.

    For example, if you want to see the `sense` feature when looking for phrases,
    add it like this

    ```
    clause
      phrase sense*
    ```

    The `*` means: always true, so it will not influence the query result set,
    only its display;

    In fact, the feature sense is only present on nodes of type `word`.
    But mentioning a feature anywhere in the query
    will trigger the display wherever it occurs with a non-trivial values.

    The extra data modules are also shown in the provenance listings
    when you export data from the browser.

#### In a Jupyter notebook

After the incantation, you see an overview of all features per module where they come from,
linked to their documentation or repository.

You can use the new features exactly as you are used to, with `F` and `E` (for edge features).

They will also automatically show up in `pretty` displays,
provided you have run a query using them before.

Alternatively, you can
tell which features you want to add to the display.
That can be done by [`displaySetup()` and `displayReset()`](App.md#display),
using the parameter `extraFeatures`.

### Develop your own data

When you develop your own data features, you'll probably make many changes before
you take the trouble of publishing them in the manner described above.
Here we describe the easiest workflow to work with your developing data with a view to share
it much less often than you modify it.

??? abstract "Produce in your local GitHub folder"
    You probably have a program or notebook that synthesizes a bunch of new features.
    It is a good idea to have that program in a version control system, and publish
    it on GitHub, in a repository of your choice.

    Set up that program in such a way, that your features end up in the same repository,
    in a folder of your choosing, but directly under a folder that corresponds with
    the version of the main data source against which you are building your data.

    ??? example "BHSA and versions"
        Suppose you are building a the dairy features `butter`, `cheese` and `eggs`,
        in the `dairy/tf` sub folder of your repo. Suppose you build them for versions
        `2017` and `2018` of your corpus. Then deliver those features in

        ```
        dairy/tf/2017/butter.tf
        dairy/tf/2017/cheese.tf
        dairy/tf/2017/eggs.tf
        dairy/tf/2018/butter.tf
        dairy/tf/2018/cheese.tf
        dairy/tf/2018/eggs.tf
        ```

    Currently, your features only live on your computer, in your local github folder.
    You may or may not commit your local changes to the online GitHub.
    But you do not want to create a new release and attach your zipped feature data to it yet.

??? abstract "Test your features"
    When you want to load your local features, you can pass to your `use(appName, ...)` call
    the `mod` parameter:
    
    ```python
    mod=f'{org}/{repo}/{path}'
    ```

    But TF then tries to download it from GitHub, or look it up from your `~/text-fabric-data`.
    Both will fail, especially when you let TF manage your `~/text-fabric-data` directory.

    You have to pass an extra parameter: 

    ```python
    mod=f'{org}/{repo}/{path}', lgc=True
    ```

    The `lgc` flag means: try **l**ocal **g**ithub **c**lones first.
    With this set, TF first looks in the right place inside your `~/github` directory.
    If it find your features there, it will not go online,
    and not look into `~/text-fabric-data`.

??? abstract "Publish your features"
    When the time comes to share your new feature data, everything is already in place
    to do that.

    Zip your data with the `text-fabric-zip` command as explained above.
    It will look into your local github directory, pickup the features from there,
    zip them, and put the zip files in your Downloads folder. Then you can pick
    that zip file up and attach it manually to a new release of your repository
    on the online GitHub.

    From then on, other users (and you too) can use that data by passing just the switch

    ```python
    mod=f'{org}/{repo}/{path}'
    ```

    without the `lgc` parameter.
    If you do that, you get a copy of your features in your `~/text-fabric-data`
    directory.

??? abstract "Continue developing your features"
    Probably you'll make changes to your features after having published them.
    Then you have the cutting edge version of your features in your local github
    directory, and the published version in your text-fabric-data directory.

    By selectively choosing `lgc=True` or `lgc=False` you can decide whether to load
    the cutting edge versions or the published versions.

##### More modules

Now that we get the hang of it, we would like to use the `heads` feature
that Cody Kingham prepared in
[etcbc/lingo/heads]({{etcbcgh}}/lingo/tree/master/heads)
as well as the `actor` feature that Christian Høygaard-Jensen prepared in
[ch-jensen/Semantic-mapping-of-participants]({{jensengh}})
We'll include it next to the valence data, by calling the TF browser like this:

```sh
text-fabric bhsa --mod=etcbc/valence/tf,etcbc/lingo/heads/tf,ch-jensen/Semantic-mapping-of-participants/actor/tf
```

Unsurprisingly: the `heads` and `actor` features and friends are downloaded and made ready for import.

You can test it by means of this query

```
book book=Leviticus
  phrase sense*
    phrase_atom actor=KHN
  -heads> word
```

Note that `heads` is an edge feature.

![sense](../images/add-heads.png)

#### In a Jupyter notebook

```python
from tf.app import use
A = use(
    'bhsa',
    mod=(
        'etcbc/valence/tf,'
        'etcbc/lingo/heads/tf,'
        'ch-jensen/Semantic-mapping-of-participants/actor/tf'
    ),
    hoist=globals(),
)
```

![sense](../images/add-incantation.png)

Now you can run the same query as before:

```python
results = A.search('''
book book=Leviticus
  phrase sense*
    phrase_atom actor=KHN
  -heads> word
''')
```

And let's see results in pretty display.
We have to manually declare that we want to see the `sense` and `actor` feature.

```
A.displaySetup(extraFeatures='sense actor')
A.show(results, start=8, end=8, condensed=True, condenseType='verse')
```

See the
[share]({{an}}/app-bhsa/blob/master/tutorial/share.ipynb)
tutorial.

##### Exercise

See whether you can find the quote in the Easter egg that is in `etcbc/lingo/easter/tf` !

