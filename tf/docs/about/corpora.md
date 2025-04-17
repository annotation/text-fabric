# Corpora

TF corpora are usually stored on GitHub / GitLab and TF
knows how to download a corpus from GitHub / GitLab if you specify the `org/repo`.

Most corpora are configured by metadata in a directory *app* in the repo.

You can load a corpus into a Python data structure by

``` python
from tf.app import use
A = use("org/repo")
```

And you can get it in the TF browser by saying this on a command prompt:


``` sh
tf org/repo
```

Here is a list of corpora that can be loaded this way.
Since everybody can put a TF corpus on GitHub / GitLab, the list may not be complete!

[annotation/banks](https://github.com/annotation/banks)
:   *modern English*
    Iain M. Banks, 1954 - 2013,
    99 words from the SF novel
    **[Consider Phlebas](https://read.amazon.com/kp/kshare?asin=B002TXZRQI&id=NpPGzf_HT5aADabyiDDSIQ&reshareId=RZ91SGMZJPWK9S1Y4EZX&reshareChannel=system)**,
    Dirk Roorda

    *to see the details*

[annotation/mobydick](https://github.com/annotation/mobydick)
:   *English*
    Herman Melville, 1819 - 1891,
    Novel, 1851;
    converted from TEI in the Oxford Text Archive,
    Dirk Roorda

    *with NLP output from Spacy woven in*

[annotation/mondriaan](https://github.com/annotation/mondriaan)
:   *English*
    Piet Mondriaan, 1872 - 1944,
    Test corpus of 14 letters (proeftuin);
    converted from TEI from the Huygens Institute, together with RKD and HuC;
    many people involved

    *with NLP output from Spacy woven in*

## [Cambridge Semitics Lab](https://github.com/CambridgeSemiticsLab)

[CambridgeSemiticsLab/nena_tf](https://github.com/CambridgeSemiticsLab/nena_tf)
:   *Aramaic*
    North Eastern Neo-Aramaic Corpus, 2000,
    **[Nena Cambridge](https://nena.ames.cam.ac.uk)**,
    Cody Kingham

    *with a client-side, offline search interface in JavaScript*

## [CenterBLC Andrews University](https://github.com/CenterBLC)

[CenterBLC/LXX](https://github.com/CenterBLC/LXX)
:   *Greek*
    [Septuagint](https://en.wikipedia.org/wiki/Septuagint), 300 - 100 BCE,
    **LXX Rahlf's edition 1935 plus additional features by CenterBLC**;
    earliest extant Greek translation of Hebrew Bible books;
    Oliver Glanz, Adrian Negrea

[CenterBLC/N1904](https://github.com/CenterBLC/N1904)
:   *Greek*
    New Testament, 100 - 400,
    **GNT Nestle-Aland edition 1904 with new features by CenterBLC**,
    using data from 
    [Clear Bible - Macula Greek](https://github.com/Clear-Bible/macula-greek/tree/main/Nestle1904/lowfat);
    Tony Jurg, Saulo Oliveira de Cantanhêde, Oliver Glanz, Willem van Peursen

[CenterBLC/SBLGNT](https://github.com/CenterBLC/SBLGNT)
:   *Greek*
    New Testament, 100 - 400,
    converted from
    **James Tauber's [morphgnt / sblgnt](https://github.com/morphgnt/sblgnt) with additional features by CenterBLC**;
    Adrian Negrea, Clacir Virmes, Oliver Glanz, Krysten Thomas

## [CLARIAH](https://github.com/CLARIAH)

[CLARIAH/descartes-tf](https://github.com/CLARIAH/descartes-tf)
:   *French*, *Latin*, *Dutch* 
    Letters from and to Descartes, 1619 - 1650,
    **René Descartes - Correspondance**;
    Ch. Adam et G. Milhaud (eds. and illustrations, 1896-1911);
    Katsuzo Murakami, Meguru Sasaki, Takehumi Tokoro (ASCII digitization, 1998);
    Erik-Jan Bos (ed, 2011); 
    Dirk Roorda (converter TEI, 2011 and TF 2023)

    *with math display and illustrations*

[CLARIAH/wp6-ferdinandhuyck](https://github.com/CLARIAH/wp6-ferdinandhuyck)
:   *Dutch* 
    a novel by Jacob van Lennep, 1840,
    **Jacob van Lennep - Ferdinand Huyck**;
    From [DBNL](https://www.dbnl.org/tekst/lenn006lotg01_01/), TEI-Lite;
    Dirk Roorda (converter TEI to TF), see also
    [tff.convert.tei](https://annotation.github.io/text-fabric-factory/tff/convert/tei.html)

    *with NLP output from Spacy woven in*

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

    *with many OCR errors and an attempt to detect them*

## [Cody Kingham](https://github.com/codykingham)

[codykingham/tischendorf_tf](https://github.com/codykingham/tischendorf_tf)
:   *Greek*
    New Testament, 50 - 450,
    **Tischendorf 8th Edition**,
    Cody Kingham, Dirk Roorda

## [Digital Theologians of the University of Copenhagen](https://github.com/DT-UCPH)

[DT-UCPH/sp](https://github.com/DT-UCPH/sp)
:   *Hebrew*
    [Samaritan Pentateuch](https://en.wikipedia.org/wiki/Samaritan_Pentateuch)
    , 516 BCE - 70 AD,
    **MS Dublin Chester Beatty Library 751 + MS Garizim 1**,
    Martijn Naaijer, Christian Canu Højgaard

[DT-UCPH/cuc](https://github.com/DT-UCPH/cuc)
:   *Hebrew*
    Copenhagen Ugaritic Corpus, 1223 BCE - 1172 AD,
    **[selected clay tablets](https://en.wikipedia.org/wiki/Keilalphabetische_Texte_aus_Ugarit)**,
    Martijn Naaijer, Christian Canu Højgaard

## [Eep Talstra Center for Bible and Computer](https://github.com/ETCBC)

[ETCBC/bhsa](https://github.com/ETCBC/bhsa)
:   *Hebrew*
    Bible (Old Testament), 1000 BCE - 900 AD,
    **[Biblia Hebraica Stuttgartensia (Amstelodamensis)](https://ETCBC.github.io/bhsa/)**,
    ETCBC + Dirk Roorda

    *the canonical TF dataset, where it all started*

[ETCBC/dhammapada](https://github.com/ETCBC/dhammapada)
:   *Pāli* and *Latin*
    Ancient Buddhist verses, 300 BCE and 1855 AD,
    **Transcription with Latin translations based on Viggo Fausbøll's book**,
    Bee Scherer, Yvonne Mataar, Dirk Roorda

[ETCBC/dss](https://github.com/ETCBC/dss)
:   *Hebrew*
    Dead Sea Scrolls, 300 BCE - 100 AD,
    **Transcriptions with morphology based on Martin Abegg's data files**,
    Martijn Naaijer, Jarod Jacobs, Dirk Roorda

[ETCBC/nestle1904](https://github.com/ETCBC/nestle1904)
:   *Greek*
    New Testament, 100 - 400,
    **GNT Nestle-Aland edition 1904 from LOWFAT-XML syntax trees**,
    converted from 
    [biblicalhumanities/greek-new-testament](https://github.com/biblicalhumanities/greek-new-testament/tree/master/syntax-trees/sblgnt-lowfat)
    contributed by Jonathan Robie and Micheal Palmer;
    Oliver Glanz, Tony Jurg, Saulo de Oliveira Cantanhêde, Dirk Roorda

[ETCBC/peshitta](https://github.com/ETCBC/peshitta)
:   *Syriac*
    Peshitta (Old Testament), 1000 BCE - 900 AD,
    **Vetus Testamentum Syriace**,
    Hannes Vlaardingerbroek, Dirk Roorda

[ETCBC/syrnt](https://github.com/ETCBC/syrnt)
:   *Syriac*
    New Testament, 0 - 1000,
    **Novum Testamentum Syriace**,
    Hannes Vlaardingerbroek, Dirk Roorda

## [KNAW/HuygensING](https://github.com/HuygensING) and [gitlab.huc.knaw.nl](https://gitlab.huc.knaw.nl)

[hermans/works](https://gitlab.huc.knaw.nl/hermans/works)
:   *Dutch*
    Complete Works of W.F. Hermans.
    The conversion to TF is work in progress.
    So far these works have been done:

    *   Paranoia
    *   Sadistisch Universum
    *   Nooit meer slapen

    Bram Oostveen, Peter Kegel, Dirk Roorda

    **Not publicly accessible, the book is under copyright.**

    *with a critical apparatus*

[mondriaan/letters](https://github.com/annotation/mondriaan)
:   *Dutch*
    Letters of Piet Mondriaan , 1892-1923.
    Straight conversion from TEI to TF,
    Peter Boot et al., Dirk Roorda

    **Work in progress, test set only ("proeftuin").**

    *with NLP output from Spacy woven in*

[HuygensING/suriano](https://github.com/HuygensING/suriano)
:   *Italian*
    Correspondence of Christofforo Suriano , 1616-1623.
    Complex conversion from DOCX through simple TEI to TF,
    From the TF a stream of annotations is generated
    (WATM) that drives the publishing machinery of
    [HuC Team Text](https://di.huc.knaw.nl/text-analysis-en.html)
    leading to the website
    [edition.suriano.huygens.knaw.nl](https://edition.suriano.huygens.knaw.nl).
    Nina Lamal, Helmer Helmers, Sebastiaan van Dalen, Bram Buitendijk, Hayco de Jong,
    Hennie Brugman, Dirk Roorda

    **with additional meta data, named entities, and page scans.**

[HuygensING/translatin-manif](https://github.com/translatin-manif)
:   *Latin*
    The transnational impact of Latin drama from the early modern Netherlands,
    a qualitative and computational analysis.
    Conversion from PageXML to TF,
    Jirsi Reinders, Hayco de Jong, et al., Dirk Roorda

    **Work in progress*.*

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
    **Archaic tablets from Uruk**
    *with lots of illustrations*,
    Cale Johnson, Dirk Roorda
    
## [Protestant Theological University](https://github.com/pthu)

[Greek Literature](https://github.com/pthu/greek_literature)
:   *Greek*
    Literature, -400 - +400,
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

## [University of Utrecht: Cornelis van Lit](https://github.com/among)

[among/fusus](https://github.com/among/fusus)
:   *Arabic*
    Fusus Al Hikam,  1165- 2000,
    **editions (Lakhnawi and Afifi) of Ibn Arabi's Fusus plus commentaries in the centuries thereafter**,
    Cornelis van Lit, Dirk Roorda

## Get corpora

### Automatically

TF downloads corpus data and apps from GitHub / GitLab on demand.

See `tf.about.use`.

Data ends up in a logical place under your `~/text-fabric-data/`.

The TF data is fairly compact.

!!! caution "Size of data"
    There might be sizable additional data for some corpora,
    images for example.
    In that case, take care to have a good internet connection
    when you use a TF app for the first time.

### Manually

TF data of corpora reside in a back-end repo.
You can manually clone such a data repository and point TF to that data.

First, take care that your clone ends up in `github/orgName` or `gitlab/orgName`
(relative your home directory)
where `orgName` is the organization or person or group on GitHub / GitLab under
which you have found the repo.

Then, when you invoke the app, pass the specifier `:clone`.
This instructs TF to look in your local GitHub / GitLab clone, rather
than online or in your local `~/text-fabric-data`, where downloaded data is stored.

``` python
use('org/repo:clone', checkout="clone")
```

``` sh
tf org/repo:clone --checkout=clone
```

In this way, you can work with data that is under your control.

!!! caution "Size of data"
    Cloning a data repository is more costly then letting TF download the data.
    A data repository may contain several versions and representations of the data,
    including their change histories. There might also be other
    material in the repo, such as source data, tutorials, programs.

    For example, the `ETCBC/bhsa` repo is several gigabytes, but the TF data for a specific
    version is only 25MB.

### Extra data

Researchers are continually adding new insights in the form of new feature
data. TF apps make it easy to use that data alongside the main data source.
Read more about the data life cycle in `tf.about.datasharing`.
