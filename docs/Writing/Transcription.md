# Transcription

Text-Fabric has support for several writing systems, by means of 
transcription tables and fonts that will be invoked when displaying the main text.

It also calls functions to use these tables for converting Hebrew and Syriac
text material to transliterated representations and back.

There is also a phonetic transcription for Hebrew, designed in 
[phono.ipynb](https://nbviewer.jupyter.org/github/etcbc/phono/blob/master/programs/phono.ipynb)

## Character tables and fonts

### `hbo` Hebrew

`tf.writing.hebrew`: full list of characters covered by the ETCBC and phonetic transcriptions

Font `Ezra SIL`.

### `syc` Syriac

`tf.writing.syriac`: full list of characters covered by the ETCBC transcriptions

Font `Estrangelo Edessa`.

### `ara` Arabic

`tf.writing.arabic`: full list of characters covered by the transcription used for the Quran

Font `AmiriQuran`.

### `grc` Greek

Font `Gentium`.

### `akk` Akkadian

Font `Santakku`.

### `cld` Neo Aramaic

Font `CharisSIL-R`.
