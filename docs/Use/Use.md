# Usage

Below `xxx` should be replaced by the name of an official
[TF-app](https://annotation.github.io/text-fabric/About/Corpora/).

You can work with the TF-browser or with the TF-API.
In both cases, the data will be automatically downloaded.

## TF-browser

The basic command to start the TF-browser [TF-browser](Browser.md) is:

``` sh
text-fabric xxx
```

Then your browser will open and there you'll find links to further help.

![tfbrowser](../images/tfbrowser.png)

**On Windows:**
You can click the Start Menu, and type the command in the search box, and then Enter.

**On Linux or Macos:**
You can open a terminal, and type the command there.

## In your own programs

``` python
from tf.app import use

A = use("xxx")
```

This `A` is your handle to the 
[advanced API functions](../Api/App.md).

## Search templates

Text-Fabric has a [templates](Search.md)-based search engine
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
You can "talk" to your corpus through a high-level
[API](../Api/App.md)
dedicated to your corpus which can download its data and display its material.

You can use it together with the core [TF API](../Api/Fabric.md) to

* search your corpus programmatically by means of the same templates,
* prepare derived data for analysis in R, and
* create new data and distribute it to others.

## Data sharing
The [data sharing guide](UseX.md)
tells more about data usage and data sharing.
