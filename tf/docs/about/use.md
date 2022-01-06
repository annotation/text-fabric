# Usage

Below `xxx` should be replaced by the name of an official
TF-app, `tf.about.corpora`,
or a path to an app on your system, or a path to TF dataset on your system.

You can work with the TF-browser or with the TF-API.
In both cases, the data will be automatically downloaded.

## TF-browser

The basic command to start the TF-browser (`tf.about.browser`) is:

``` sh
text-fabric org/repo
```

(More details in `tf.server.start`).

Then your browser will open and there you'll find links to further help.

![tfbrowser](../images/tfbrowser.png)

**On Windows:**
You can click the Start Menu, and type the command in the search box, and then Enter.

**On Linux or Macos:**
You can open a terminal, and type the command there.

## In your own programs

``` python
from tf.app import use

A = use("org/repo")
```

This `A` is your handle to the 
advanced API functions (`tf.advanced`).

## Search templates

Text-Fabric has a templates-based search engine (`tf.about.searchusage`)
which follows closely the features of the annotations to the corpus.

(Uruk)

```
tablet catalogId=P448702
  line
    case terminal=1 number=2a
        sign type=ideograph
        :> sign type=numeral
```

(Bhsa)

```
clause
/where/
  phrase function=Pred
/have/
  /without/
    word sp#verb
  /-/
/-/
  phrase function=Subj
```

(Quran)

```
query = '''\n",
aya\n",
  word pos=verb
  <: word pos=noun posx=proper root=Alh
```

## Text-Fabric API

Beyond searching, you can program your own analytical methods.
You can "talk" to your corpus through the high-level API (`tf.advanced`)
dedicated to your corpus which can download its data and display its material.

You can use it together with the core API (`tf.core`) to

* search your corpus programmatically by means of the same templates,
* prepare derived data for analysis in R, and
* create new data and distribute it to others.
