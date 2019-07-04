# Transcription

While Text-Fabric is a generic package to deal with text and annotations
in a model of nodes, edges, and features, there is need for some additions.

## Transcription

??? abstract "About"
    [transcription.py]({{tfghb}}/{{c_transcription}}) contains transliteration tables for Hebrew, Syriac and Arabic.

    It also calls functions to use these tables for converting Hebrew and Syriac text material to transliterated
    representations and back.

    There is also a phonetic transcription for Hebrew, designed in 
    [phono.ipynb]({{etcbcnb}}/phono/blob/master/programs/phono.ipynb)

???+ abstract "Character tables"
    [Hebrew](../Writing/Hebrew.md): full list of characters covered by the ETCBC and phonetic transcriptions

    [Syriac](../Writing/Syriac.md): full list of characters covered by the ETCBC transcriptions

    [Arabic](../Writing/Arabic.md): full list of characters covered by the transcription used for the Quran

??? abstract "Usage"
    Invoke the transcription functionality as follows:

    ```python
    from tf.writing.transcription import Transcription
    ```

    Some of the attributes and methods below are *class* attributes, others are instance attributes.
    A class attribute `aaa` can be retrieved by saying `Transcription.aaa`.

    To retrieve an instance attribute, you need an instance first, like

    ```python
    tr = Transcription()
    ```

    and then you can say `tr.aaa`.

    For each attribute we'll give a usage example.

??? abstract "Transcription.hebrew mapping"
    Maps all ETCBC transliteration character combinations for Hebrew to Unicode.

    Example: print the sof-pasuq:

    ```python
    print(Transcription.hebrew_mapping['00'])
    ```

    Output:

    ```
    ׃
    ```

??? abstract "Transcription.syriac mapping"
    Maps all ETCBC transliteration character combinations for Syriac to Unicode.

    Example: print the semkath-final:

    ```python
    print(Transcription.syriac_mapping['s'])
    ```

    Output:

    ```
    ܤ
    ```

??? abstract "Transcription.arabic mapping"
    Maps an Arabic transliteration character to Unicode.

    Example: print the beh 

    ```python
    print(Transcription.syriac_mapping['b'])
    ```

    Output:

    ```
    ب
    ```

??? abstract "Transcription.arabic mappingi"
    Maps an Arabic letter in unicode to its transliteration

    Example: print the beh transliteration 

    ```python
    print(Transcription.syriac_mapping['ب'])
    ```

    Output:

    ```
    b
    ```

??? abstract "Transcription.suffix_and_finales(word)"
    Given an ETCBC transliteration, split it into the word material and the interword material
    that follows it (space, punctuation).
    Replace the last consonant of the word material by its final form, if applicable.

    Output a tuple with the modified word material and the interword material.

    Example: 

    ```python
    print(Transcription.suffix_and_finales('71T_H@>@95REY00'))
    ```

    Output:

    ```
    ('71T_H@>@95REy', '00\n')
    ```

    Note that the `Y` has been replaced by `y`.

??? abstract "Transcription.suppress_space(word)"
    Given an ETCBC transliteration of a word,
    match the end of the word for interpunction and spacing characters
    (sof pasuq, paseq, nun hafukha, setumah, petuhah, space, no-space)

    Example:

    ```python
    print(Transcription.suppress_space('B.:&'))
    print(Transcription.suppress_space('B.@R@74>'))
    print(Transcription.suppress_space('71T_H@>@95REY00'))
    ```

    Output:

    ```
    <re.Match object; span=(3, 4), match='&'>
    None
    <re.Match object; span=(13, 15), match='00'>
    ```

??? abstract "Transcription.to_etcbc_v(word)"
    Given an ETCBC transliteration of a fully pointed word,
    strip all the non-vowel pointing (i.e. the accents).

    Example: 

    ```python
    print(Transcription.to_etcbc_v('HAC.@MA73JIm'))
    ```

    Output:

    ```
    HAC.@MAJIm
    ```

??? abstract "Transcription.to_etcbc_c(word)"
    Given an ETCBC transliteration of a fully pointed word,
    strip everything except the consonants.
    Punctuation will also be stripped.

    Example: 

    ```python
    print(Transcription.to_etcbc_c('HAC.@MA73JIm'))
    ```

    Output:

    ```
    H#MJM
    ```

    Note that the pointed shin (`C`) is replaced by an unpointed one (`#`).

??? abstract "Transcription.to_hebrew(word)"
    Given a transliteration of a fully pointed word,
    produce the word in Unicode Hebrew.
    Care will be taken that vowel pointing will be added to consonants before accent pointing.

    Example: 

    ```python
    print(Transcription.to_hebrew('HAC.@MA73JIm'))
    ```

    Output:

    ```
    הַשָּׁמַ֖יִם
    ```

??? abstract "Transcription.to_hebrew_x(word)"
    Given a transliteration of a fully pointed word,
    produce the word in Unicode Hebrew.
    Vowel pointing and accent pointing will be applied in the order given by the input word.
    produce the word in Unicode Hebrew, but without the pointing.

    Example: 

    ```python
    print(Transcription.to_hebrew_x('HAC.@MA73JIm'))
    ```

    Output:

    ```
    הַשָּׁמַ֖יִם
    ```

??? abstract "Transcription.to_hebrew_v(word)"
    Given a transliteration of a fully pointed word,
    produce the word in Unicode Hebrew, but without the accents.

    Example: 

    ```python
    print(Transcription.to_hebrew_v('HAC.@MA73JIm'))
    ```

    Output:

    ```
    הַשָּׁמַיִם
    ```

??? abstract "Transcription.to_hebrew_c(word)"
    Given a transliteration of a fully pointed word,
    produce the word in Unicode Hebrew, but without the pointing.

    Example: 

    ```python
    print(Transcription.to_hebrew_c('HAC.@MA73JIm'))
    ```

    Output:

    ```
    השמימ
    ```

    Note that final consonant forms are not being used.

??? abstract "Transcription.ph_simplify(pword)"
    Given a phonological transliteration of a fully pointed word,
    produce a more coarse phonological transliteration.

    Example: 

    ```python
    print(Transcription.ph_simplify('ʔᵉlōhˈîm'))
    print(Transcription.ph_simplify('māqˈôm'))
    print(Transcription.ph_simplify('kol'))
    ```

    Output:

    ```
    ʔlōhîm
    måqôm
    kål
    ```

    Note that the simplified version transliterates the qamets gadol and qatan to the same
    character.

??? abstract "tr.from_hebrew(word)"
    Given a fully pointed word in Unicode Hebrew,
    produce the word in ETCBC transliteration.

    Example: 

    ```python
    print(tr.from_hebrew('הָאָֽרֶץ׃'))
    ```

    Output:

    ```
    H@>@95REy00
    ```

??? abstract "tr.from_syriac(word)"
    Given a word in Unicode Syriac,
    produce the word in ETCBC transliteration.

    Example: 

    ```python
    print(tr.from_syriac('ܡܟܣܝܢ'))
    ```

    Output:

    ```
    MKSJN
    ```

??? abstract "tr.to_syriac(word)"
    Given a word in ETCBC transliteration,
    produce the word in Unicode Syriac.

    Example: 

    ```python
    print(tr.to_syriac('MKSJN'))
    ```

    Output:

    ```
    ܡܟܣܝܢ
    ```

??? abstract "tr.from_arabic(word)"
    Given a word in Unicode Arabic,
    produce the word in transliteration.

    Example: 

    ```python
    print(tr.from_arabic('بِسْمِ'))
    ```

    Output:

    ```
    bisomi
    ```

??? abstract "tr.to_arabic(word)"
    Given a word in transliteration,
    produce the word in Unicode Arabic.

    Example: 

    ```python
    print(tr.to_arabic('bisomi'))
    ```

    Output:

    ```
    بِسْمِ
    ```

