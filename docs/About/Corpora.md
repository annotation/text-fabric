# Corpora

Corpora are usually stored in an online repository, such as GitHub or a research data archive
such as [DANS](https://dans.knaw.nl/en/front-page?set_language=en).

Some corpora are supported by Text-Fabric *apps*.

These apps provide a browser interface for the corpus, and they enhance the API for working
with them programmatically.

A TF app can also download and update the corpus *data*.

### Current TF apps

[athenaeus](https://github.com/annotation/app-athenaeus)
:   *Greek*
    Works of Athenaeus, 80 - 170,
    **[Deipnosophistae](https://en.wikipedia.org/wiki/Deipnosophistae)**,
    Ernst Boogert

[banks](https://github.com/annotation/app-banks)
:   *modern english*
    Iain M. Banks, 1984 - 1987,
    99 words from the SF novel
    **[Consider Phlebas](https://read.amazon.com/kp/kshare?asin=B002TXZRQI&id=NpPGzf_HT5aADabyiDDSIQ&reshareId=RZ91SGMZJPWK9S1Y4EZX&reshareChannel=system)**,
    Dirk Roorda

[bhsa](https://github.com/annotation/app-bhsa)
:   *Hebrew*
    Hebrew Bible, 1000 BC - 900 AD,
    **[Biblia Hebraica Stuttgartensia (Amstelodamensis)](https://etcbc.github.io/bhsa/)**,
    ETCBC + Dirk Roorda

[dss](https://github.com/annotation/app-dss)
:   *Hebrew*
    Dead Sea Scrolls, 300 BC - 100 AD,
    **[Transcriptions with morphology based on Martin Abegg's data files](https://github.com/ETCBC/dss/blob/master/docs/about.md)**,
    Martijn Naaijer, Jarod Jacobs, Dirk Roorda

[nena](https://github.com/annotation/app-nena)
:   *Aramaic*
    North Eastern Neo-Aramaic Corpus, 2000,
    **[Nena Cambridge](https://nena.ames.cam.ac.uk)**,
    Cody Kingham

[oldassyrian](https://github.com/annotation/app-oldassyrian)
:   *Akkadian / cuneiform*
    Old Assyrian documents, 2000 - 1600 BC,
    **[Documents from Ashur](https://github.com/Nino-cunei/oldassyrian/blob/master/docs/about.md)**
    Cale Johnson, Alba de Ridder, Martijn Kokken, Dirk Roorda

[oldbabylonian](https://github.com/annotation/app-oldbabylonian)
:   *Akkadian / cuneiform*
    Old Babylonian letters, 1900 - 1600 BC,
    **[Altbabylonische Briefe in Umschrift und Übersetzung](https://github.com/Nino-cunei/oldbabylonian/blob/master/docs/about.md)**,
    Cale Johnson, Dirk Roorda

[peshitta](https://github.com/annotation/app-peshitta)
:   *Syriac*
    Syriac Old Testament, 1000 BC - 900 AD,
    **[Vetus Testamentum Syriace](https://github.com/ETCBC/peshitta/blob/master/docs/about.md)**,
    Hannes Vlaardingerbroek, Dirk Roorda

[quran](https://github.com/annotation/app-quran)
:   *Arabic*
    Quran, 600 - 900,
    **[Quranic Arabic Corpus](https://github.com/q-ran/quran/blob/master/docs/about.md)**,
    Cornelis van Lit, Dirk Roorda

[syrnt](https://github.com/annotation/app-syrnt)
:   *Syriac*
    Syriac New Testament, 0 - 1000,
    **[Novum Testamentum Syriace](https://github.com/ETCBC/syrnt/blob/master/docs/about.md)**,
    Hannes Vlaardingerbroek, Dirk Roorda

[tisch](https://github.com/annotation/app-tisch)
:   *Greek*
    New Testament, 50 - 450,
    **[Greek New Testament in Tischendorf 8th Edition](https://github.com/codykingham/tischendorf_tf)**,
    Cody Kingham, Dirk Roorda

[uruk](https://github.com/annotation/app-uruk)
:   *proto-cuneiform*
    Uruk, 4000 - 3100 BC,
    **[Archaic tablets from Uruk](https://github.com/Nino-cunei/uruk/blob/master/docs/about.md)**,
    Cale Johnson, Dirk Roorda


All these apps can be found in 
[annotation](https://github.com/annotation) on GitHub.
Each repo named `app-`*appName* hosts the app named *appName*.

### Current TF corpora without an app

[patristics](https://github.com/annotation/app-patristics)
:   *Greek*
    Works by Church Father, 200 - 600, **see [PThU](https://github.com/pthu/patristics)**, Ernst Boogert


### Intentions

oldroyal
:   *Akkadian-Sumerian cuneiform*
    Bilingual royal inscriptions, 2000 - 1600,
    **more info to come**, Martijn Kokken, Dirk Roorda


## Get corpora

### Automatically

Text-Fabric downloads apps from [annotation](https://github.com/annotation) automatically
when you use them.

See `tf.about.use`.

Data ends up in a logical place under your `~/text-fabric-data/`.

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

    use('xxxx:clone', checkout="clone")

    text-fabric xxxx:clone --checkout=clone

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
Read more about the data life cycle in `tf.about.datasharing`.
