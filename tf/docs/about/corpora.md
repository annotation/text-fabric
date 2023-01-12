# Corpora

Text-Fabric corpora are usually stored on GitHub/GitLab and Text-Fabric
knows how to download a corpus from GitHub/GitLab if you specify the *org/repo*.

Most corpora are configured by metadata in a directory *app* in the repo.

You can load a corpus into a Python datastructure by

``` python
from tf.app import use
A = use("org/repo")
```

And you can get it in the Text-Fabric browser by saying this on a command prompt:


``` sh
text-fabric org/repo
```

Here is a list of corpora that can be loaded this way.
Since everybody can put a Text-Fabric corpus on GitHub/GitLab, the list may not be complete!

[annotation/banks](https://github.com/annotation/banks)
:   *modern english*
    Iain M. Banks, 1984 - 1987,
    99 words from the SF novel
    **[Consider Phlebas](https://read.amazon.com/kp/kshare?asin=B002TXZRQI&id=NpPGzf_HT5aADabyiDDSIQ&reshareId=RZ91SGMZJPWK9S1Y4EZX&reshareChannel=system)**,
    Dirk Roorda

## [Cambridge Semitics Lab](https://github.com/CambridgeSemiticsLab)

[CambridgeSemiticsLab/nena_tf](https://github.com/CambridgeSemiticsLab/nena_tf)
:   *Aramaic*
    North Eastern Neo-Aramaic Corpus, 2000,
    **[Nena Cambridge](https://nena.ames.cam.ac.uk)**,
    Cody Kingham

## [CenterBLC Andrews University](https://github.com/CenterBLC)

[CenterBLC/LXX](https://github.com/CenterBLC/LXX)
:   *Greek*
    [Septuagint](https://en.wikipedia.org/wiki/Septuagint), 300 - 100 BCE,
    **LXX Rahlf's edition 1935 plus additional features by CenterBLC**;
    earliest extant Greek translation of Hebrew Bible books;
    Oliver Glanz, Adrian Negrea

[CenterBLC/NA](https://github.com/CenterBLC/NA)
:   *Greek*
    New Testament, 100 - 400,
    **GNT Nestle-Aland edition 1904 with new features by CentrBLC**,
    converted from 
    [biblicalhumanities/Nestle1904](https://github.com/biblicalhumanities/Nestle1904)
    contributed by Ulrik Sandborg Petersen, Jonathan Robie;
    Oliver Glanz

[CenterBLC/SBLGNT](https://github.com/CenterBLC/SBLGNT)
:   *Greek*
    New Testament, 100 - 400,
    converted from
    **James Tauber's [morphgnt/sblgnt](https://github.com/morphgnt/sblgnt) with additional features by CenterBLC**;
    Adrian Negrea, Clacir Virmes, Oliver Glanz, Krysten Thomas

## [CLARIAH](https://github.com/CLARIAH)

[CLARIAH/descartes](https://github.com/CLARIAH/wp6-missieven)
:   *French*, *Latin*, *Dutch* 
    Letters from and to Descartes, 1619 - 1650,
    **René Descartes - Correspondance**;
    Ch. Adam et G. Milhaud (eds. and illustrations, 1896-1911);
    Katsuzo Murakami, Meguru Sasaki, Takehumi Tokoro (ascii digitization, 1998);
    Erik-Jan Bos (ed, 2011); 
    Dirk Roorda (converter TEI, 2011 and TF 2023)

[CLARIAH/wp6-missieven](https://github.com/CLARIAH/wp6-missieven)
:   *Dutch* 
    General Missives, 1600 - 1800,
    **General Missives, Dutch East-Indian Company**,
    Jesse van der Does, Sophie Arnoult, Dirk Roorda

[CLARIAH/wp6-daghregisters](https://github.com/CLARIAH/wp6-daghregisters)
:   *Dutch* 
    Dagh Registers Batavia, 1640 - 1641,
    **Daily events at Batavia, Indonesia, historical source for
    the operation of the Dutch East-Indian Company**,
    Lodewijk Petram, Dirk Roorda.
    *work in progress, currently only volume 4*

## [Cody Kingham](https://github.com/codykingham)

[codykingham/tischendorf_tf](https://github.com/codykingham/tischendorf_tf)
:   *Greek*
    New Testament, 50 - 450,
    **Tischendorf 8th Edition**,
    Cody Kingham, Dirk Roorda

## [Eep Talstra Centre for Bible and Computer](https://github.com/etcbc)

[etcbc/bhsa](https://github.com/etcbc/bhsa)
:   *Hebrew*
    Bible (Old Testament), 1000 BCE - 900 AD,
    **[Biblia Hebraica Stuttgartensia (Amstelodamensis)](https://etcbc.github.io/bhsa/)**,
    ETCBC + Dirk Roorda

[etcbc/dhammapada](https://github.com/etcbc/dhammapada)
:   *Pāli* and *Latin*
    Ancient Buddhist verses, 300 BCE and 1855 AD,
    **Transcription with Latin translations based on Viggo Fausbøll's book**,
    Bee Scherer, Yvonne Mataar, Dirk Roorda

[etcbc/dss](https://github.com/etcbc/dss)
:   *Hebrew*
    Dead Sea Scrolls, 300 BCE - 100 AD,
    **Transcriptions with morphology based on Martin Abegg's data files**,
    Martijn Naaijer, Jarod Jacobs, Dirk Roorda

[etcbc/peshitta](https://github.com/etcbc/peshitta)
:   *Syriac*
    Peshitta (Old Testament), 1000 BCE - 900 AD,
    **Vetus Testamentum Syriace**,
    Hannes Vlaardingerbroek, Dirk Roorda

[etcbc/syrnt](https://github.com/etcbc/syrnt)
:   *Syriac*
    New Testament, 0 - 1000,
    **Novum Testamentum Syriace**,
    Hannes Vlaardingerbroek, Dirk Roorda

## [NINO Cuneiform](https://github.com/Nino-cunei)

[Nino-cunei/ninmed](https://github.com/Nino-cunei/ninmed)
:   *Akkadian / cuneiform*
    Medical Encyclopedia from Nineveh, ca. 800 BCE,
    **Medical documents with lemma annotations**,
    Cale Johnson, Dirk Roorda

[Nino-cunei/oldassyrian](https://github.com/Nino-cunei/oldassyrian)
:   *Akkadian / cuneiform*
    Old Assyrian documents, 2000 - 1600 BCE,
    **Documents from Ashur**
    Cale Johnson, Alba de Ridder, Martijn Kokken, Dirk Roorda

[Nino-cunei/oldbabylonian](https://github.com/Nino-cunei/oldbabylonian)
:   *Akkadian / cuneiform*
    Old Babylonian letters, 1900 - 1600 BCE,
    **Altbabylonische Briefe in Umschrift und Übersetzung**,
    Cale Johnson, Dirk Roorda

[Nino-cunei/uruk](https://github.com/Nino-cunei/uruk)
:   *proto-cuneiform*
    Uruk, 4000 - 3100 BCE,
    **Archaic tablets from Uruk**,
    Cale Johnson, Dirk Roorda

## [Protestant Theological University](https://github.com/pthu)

[Greek Literature](https://nbviewer.jupyter.org/github/pthu/greek_literature/blob/master/tutorial/start.ipynb)
:   *Greek*
    [Literature, -400 - +400](https://github.com/pthu/greek_literature),
    [Perseus Digital Library](https://github.com/PerseusDL/canonical-greekLit) and 
    [Open Greek and Latin Project](https://github.com/OpenGreekAndLatin/First1KGreek)
    The result of a massive conversion effort by Ernst Boogert.

[pthu/athenaeus](https://github.com/pthu/athenaeus)
:   *Greek*
    Works of Athenaeus, 80 - 170,
    **[Deipnosophistae](https://en.wikipedia.org/wiki/Deipnosophistae)**,
    Ernst Boogert

## [Quran](https://github.com/q-ran)

[q-ran/quran](https://github.com/q-ran/quran)
:   *Arabic*
    Quran, 600 - 900,
    **Quranic Arabic Corpus**,
    Cornelis van Lit, Dirk Roorda

## [KNAW/Huygens](https://gitlab.huc.knaw.nl/tt)

[hermans/works](https://gitlab.huc.knaw.nl/hermans/works)
:   *Dutch*
    Complete Works of W.F. Hermans.
    The conversion to Text-Fabric is work in progress.
    So far these works have been done:

    * Paranoia
    * Sadistisch Universum
    * Nooit meer slapen

    Bram Oostveen, Peter Kegel, Dirk Roorda

    **Not publicly accessible, the book is under copyright.**

## [University of Utrecht: Cornelis van Lit](https://github.com/among)

[among/fusus](https://github.com/among/fusus)
:   *Arabic*
    Fusus Al Hikam,  1165- 2000,
    **editions (Lakhnawi and Afifi) of Ibn Arabi's Fusus plus commentaries in the centuries thereafter**,
    Cornelis van Lit, Dirk Roorda

### Intentions

oldroyal
:   *Akkadian-Sumerian cuneiform*
    Bilingual royal inscriptions, 2000 - 1600,
    **more info to come**, Martijn Kokken, Dirk Roorda


## Get corpora

### Automatically

Text-Fabric downloads corpus data and apps from GitHub/GitLab on demand.

See `tf.about.use`.

Data ends up in a logical place under your `~/text-fabric-data/`.

The TF data is fairly compact.

!!! caution "Size of data"
    There might be sizable additional data for some corpora,
    images for example.
    In that case, take care to have a good internet connection
    when you use a TF app for the first time.

### Manually

TF data of corpora reside in a backend repo.
You can manually clone such a data repository and point Text-Fabric to that data.

First, take care that your clone ends up in `github/`*orgName* or `gitlab/`*orgName*
(relative your home directory)
where *orgName* is the organization or person or group on GitHub/GitLab under which you have
found the repo.

Then, when you invoke the app, pass the specifier `:clone`.
This instructs Text-Fabric to look in your local GitHub/GitLab clone, rather
than online or in your local `text-fabric-data`, where downloaded data is stored.

    use('org/repo:clone', checkout="clone")

    text-fabric org/repo:clone --checkout=clone

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
