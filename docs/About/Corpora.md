# Corpora

Corpora are usually stored in an online repository, such as GitHub or a research data archive
such as [DANS](https://dans.knaw.nl/en/front-page?set_language=en).

Some corpora are supported by Text-Fabric *apps*.

These apps provide a browser interface for the corpus, and they enhance the API for working
with them programmatically.

A TF app can also download and update the corpus *data*.

### Current TF apps

acronym | language/writing system | name | period | description | converted by
--- | --- | --- | --- | --- | ---
[athenaeus](https://github.com/annotation/app-athenaeus) | Greek | Works of Athenaeus | 80 - 170 | Deipnosophistae | Ernst Boogert
[banks](https://github.com/annotation/app-banks) | modern english | Iain M. Banks | 1984 - 1987 | 99 words from the SF novel [Consider Phlebas](https://read.amazon.com/kp/kshare?asin=B002TXZRQI&id=NpPGzf_HT5aADabyiDDSIQ&reshareId=RZ91SGMZJPWK9S1Y4EZX&reshareChannel=system) | Dirk Roorda
[bhsa](https://github.com/annotation/app-bhsa) | Hebrew | Hebrew Bible | 1000 BC - 900 AD | [Biblia Hebraica Stuttgartensia (Amstelodamensis)](https://etcbc.github.io/bhsa/) | Dirk Roorda + ETCBC
[dss](https://github.com/annotation/app-dss) | Hebrew | Dead Sea Scrolls | 300 BC - 100 AD | [Transcriptions with morphology based on Martin Abegg's data files](https://github.com/ETCBC/dss/blob/master/docs/about.md) | Dirk Roorda, Jarod Jacobs
[nena](https://github.com/annotation/app-nena) | Aramaic | North Eastern Neo-Aramaic Corpus | 2000 | [Nena Cambridge](https://nena.ames.cam.ac.uk) | Cody Kingham
[oldbabylonian](https://github.com/annotation/app-oldbabylonian) | Akkadian / cuneiform | Old Babylonian letters | 1900 - 1600 BC | [Altbabylonische Briefe in Umschrift und Übersetzung](https://github.com/Nino-cunei/oldbabylonian/blob/master/docs/about.md) | Dirk Roorda, Cale Johnson
[peshitta](https://github.com/annotation/app-peshitta) | Syriac | Syriac Old Testament | 1000 BC - 900 AD | [Vetus Testamentum Syriace](https://github.com/ETCBC/peshitta/blob/master/docs/about.md) | Dirk Roorda, Hannes Vlaardingerbroek
[quran](https://github.com/annotation/app-quran) | Arabic | Quran | 600 - 900 | [Quranic Arabic Corpus](https://github.com/q-ran/quran/blob/master/docs/about.md) | Dirk Roorda, Cornelis van Lit
[syrnt](https://github.com/annotation/app-syrnt) | Syriac | Syriac New Testament | 0 - 1000 | [Novum Testamentum Syriace](https://github.com/ETCBC/syrnt/blob/master/docs/about.md) | Dirk Roorda, Hannes Vlaardingerbroek
[tisch](https://github.com/annotation/app-tisch) | Greek | New Testament | 50 - 450 | Greek New Testament in Tischendorf 8th Edition | Cody Kingham
[uruk](https://github.com/annotation/app-uruk) | proto-cuneiform | Uruk | 4000 - 3100 BC | [Archaic tablets from Uruk](https://github.com/Nino-cunei/uruk/blob/master/docs/about.md) | Dirk Roorda, Cale Johnson

All these apps can be found in 
[annotation](https://github.com/annotation) on GitHub.
Each repo named `app-`*appName* hosts the app named *appName*.

### Current TF corpora without an app

acronym | language/writing system | name | period | description | converted by
--- | --- | --- | --- | --- | ---
[patristics](https://github.com/annotation/app-patristics) | Greek | Works by Church Fathers| 200 - 600 | see [PThU](https://github.com/pthu/patristics) | Ernst Boogert

### Intentions

acronym | language/writing system | name | period | description | converted by
--- | --- | --- | --- | --- | ---
[oldassyrian](https://github.com/annotation/app-oldassyrian) | Akkadian / cuneiform | Old Assyrian documents | 2000 - 1900 | see [About](https://github.com/Nino-cunei/oldassyrian/blob/master/docs/about.md) | Dirk Roorda, Cale Johnson, Alba de Ridder, Martijn Kokken
oldroyal | Akkadian-Sumerian cuneiform | Bilingual royal inscriptions | 2000 - 1600 | more info to come | Martijn Kokken, Dirk Roorda


## Get apps

### Automatically

Text-Fabric downloads apps from [annotation](https://github.com/annotation) automatically
when you use them.

If you do:

```python
use('xxxx')
```

(Python) or 

```sh
text-fabric xxxx
```

(Text-Fabric browser)

then Text-Fabric will fetch the `xxxx` app for you, if it exists.

Once you have the app, Text-Fabric will use your offline copy.
It will not check for newer versions by default.

But if you pass `-c` resp `check=True`, Text-Fabric will check online
for newer versions of the app and if there are,
it will download the newest version and run it.

```python
use('xxxx', check=True)
```

```sh
text-fabric xxxx -c
```

Apps end up in `text-fabric-data/__apps__` relative your home directory.

If you have trouble with an app `xxxx`, just remove the entire directory
`text-fabric-data/__apps__/xxxx` and run either of the commands above. 

## Get data

### Automatically
Text-Fabric apps download the corpus data for you automatically.

When you use the browser, it happens when you start it up.

And from within a Python program,
you get the data when you do the
[incantation](../Api/App.md#incantation).

In a program (e.g. a Jupyter notebook):

```python
use('xxxx')
```

In the Text-Fabric browser:

```sh
text-fabric xxxx
```

This will also automatically upgrade your data if there are new releases.
If you want to avoid upgrades, add the `:local` specifier.

```python
use('xxxx', checkout='local')
```

```sh
text-fabric xxxx --checkout=local
```

There are more options, see the
[incantation](../Api/App.md#incantation).

Data ends up in `text-fabric-data/`*orgName*/*repoName* relative your home directory,
where *orgName* is the organization or person on GitHub that has
the repo *repoName* that contains the data.

The TF data is fairly compact.

!!! caution "Size of data"
    There might be sizable additional data for some corpora,
    images for example.
    In that case, take care to have a good internet connection
    when you use a TF app for the first time.

### Manually

Corpus data of app-supported corpora reside in a GitHub repo.
You can manually clone such a data repository and point Text-Fabric to that data.

First, take care that your clone ends up in `github/`*orgName*
(relative your home directory)
where *orgName* is the organization or person on GitHub under which you have
found the repo.

Then, when you invoke the app, pass the specifier `:clone`.
This instructs Text-Fabric to look in your local GitHub clone, rather
than online or in `text-fabric-data`, where downloaded data is stored.

```python tab="notebook or program"
use('xxxx:clone')
```

```sh tab="TF browser"
text-fabric xxxx --checkout=clone
```

In this way, you can work with data that is under your control.

!!! caution "Size of data"
    Cloning a data repository is more costly then letting Text-Fabric download the data.
    A data repository may contain several versions and representations of the data,
    including the their change histories. There might also be other
    material in the repo, such as source data, tutorials, programs.

    For example, the `etcbc/bhsa` repo is several GB, but the TF data for a specific
    version is only 25MB.

### Extra data

Researchers are continually adding new insights in the form of new feature
data. TF apps make it easy to use that data alongside the main data source.
Read more about the data life cycle in [Data](../Api/Data.md)

## More corpora

The
[text-fabric-data](https://github.com/annotation/text-fabric-data)
repo has some corpora that have been converted to TF,
but for which no supporting  TF-apps have been written.
