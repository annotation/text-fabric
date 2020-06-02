"""
.. include:: ../../docs/writing/transcription.md
"""
import re


class Transcription(object):
    """Conversion between unicode and various transcriptions.

    Usage notes:

    Invoke the transcription functionality as follows:

        from tf.writing.transcription import Transcription

    Some of the attributes and methods below are *class* attributes,
    others are instance attributes.

    A class attribute `aaa` can be retrieved by saying

        Transcription.aaa

    To retrieve an instance attribute, you need an instance first, like

        tr = Transcription()

    and then you can say `tr.aaa`.
    """

    decomp = {
        "\u05E9\u05C1": "\uFB2A",
        "\u05E9\u05C2": "\uFB2B",
    }
    hebrew_mapping = {
        "_": " ",  # space inside word
        "92": "\u0591",  # etnahta = atnach
        "01": "\u0592",  # segolta
        "65": "\u0593",  # shalshelet
        "80": "\u0594",  # zaqef_qatan
        "85": "\u0595",  # zaqef_gadol
        "73": "\u0596",  # tipeha = tifcha
        "81": "\u0597",  # revia = rebia
        "82": "\u0598",  # zarqa = tsinorit = zinorit = sinnorit
        "03": "\u0599",  # pashta
        "10": "\u059A",  # yetiv = yetib
        "91": "\u059B",  # tevir = tebir
        "61": "\u059C",  # geresh
        "11": "\u059D",  # geresh muqdam = mugrash
        "62": "\u059E",  # gershayim = garshayim
        "84": "\u059F",  # qarney para = pazer_gadol
        "14": "\u05A0",  # telisha_gedola
        "44": "\u05A0",  # telisha_gedola = telisha_gedola_med
        "83": "\u05A1",  # pazer
        "74": "\u05A3",  # munah = munach
        "70": "\u05A4",  # mahapakh = mehuppach
        "71": "\u05A5",  # merkha = merecha
        "72": "\u05A6",  # merkha kefula = merecha_kepula
        "94": "\u05A7",  # darga
        "63": "\u05A8",  # qadma = azla
        "33": "\u05A8",  # pashta_med < qadma
        "04": "\u05A9",  # telisha_qetana
        "24": "\u05A9",  # telisha_qetana = telisha_qetana_med
        "93": "\u05AA",  # yera ben yomo = yerach
        "60": "\u05AB",  # ole = ole_weyored
        "64": "\u05AC",  # iluy = illuy
        "13": "\u05AD",  # dehi = dechi
        "02": "\u05AE",  # zinor = sinnor
        "*": "\u05AF",  # masora circle
        ":": "\u05B0",  # sheva = shewa
        ":E": "\u05B1",  # hataf segol = chataph_segol
        ":A": "\u05B2",  # hataf patah = chataph_patach
        ":@": "\u05B3",  # hataf qamats = chataph_qamats
        "I": "\u05B4",  # hiriq = chiriq
        ";": "\u05B5",  # tsere
        "E": "\u05B6",  # segol
        "A": "\u05B7",  # patach
        "@": "\u05B8",  # qamats
        "O": "\u05B9",  # holam = cholam
        "U": "\u05BB",  # qubuts = qubbuts
        ".": "\u05BC",  # dagesh
        "25": "\u05BD",  # silluq yamin
        "45": "\u05BD",  # meteg
        "35": "\u05BD",  # meteg (tikon)
        "75": "\u05BD",  # siluq = silluq
        "95": "\u05BD",  # meteg = meteg_yamin
        "&": "\u05BE",  # maqaf
        ",": "\u05BF",  # rafe = raphe
        "05": "\u05C0",  # paseq
        ".c": "\u05C1",  # shin dot
        ".f": "\u05C2",  # sin dot
        "00": "\u05C3",  # sof_pasuq
        "52": "\u05C4",  # upper dot = puncta_above
        "53": "\u05C5",  # lower dot = puncta_below
        "ñ": "\u05C6\u0307",  # nun hafukha
        "Ñ": "\u05C6\u0307",  # nun hafukha
        ">": "\u05D0",  # alef
        "B": "\u05D1",  # bet
        "G": "\u05D2",  # gimel
        "D": "\u05D3",  # dalet
        "H": "\u05D4",  # he
        "W": "\u05D5",  # vav
        "Z": "\u05D6",  # zayin
        "X": "\u05D7",  # het
        "V": "\u05D8",  # tet
        "J": "\u05D9",  # yod
        "k": "\u05DA",  # kaf final
        "K": "\u05DB",  # kaf
        "L": "\u05DC",  # lamed
        "m": "\u05DD",  # mem final
        "M": "\u05DE",  # mem
        "n": "\u05DF",  # nun final
        "N": "\u05E0",  # nun
        "S": "\u05E1",  # samekh
        "<": "\u05E2",  # ayin
        "p": "\u05E3",  # pe final
        "P": "\u05E4",  # pe
        "y": "\u05E5",  # tsadi final
        "Y": "\u05E6",  # tsadi
        "Q": "\u05E7",  # qof
        "R": "\u05E8",  # resh
        "#": "\u05E9",  # sin unpointed
        "T": "\u05EA",  # tav
        "C": "\uFB2A",  # shin pointed
        "F": "\uFB2B",  # sin pointed
        "55": "<UNMAPPED 55=large letter>",  # large_letter
        "56": "<UNMAPPED 56=small letter>",  # small_letter
        "57": "<UNMAPPED 57=suspended letter>",  # suspended_letter
        "-": "",  # suppress space afterward
        "'": "\u05f3",  # punctuation geresh
        '"': "\u05f4",  # punctuation gershayim
    }
    """
    Maps all ETCBC transliteration character combinations for Hebrew to Unicode.

    Example: print the sof-pasuq:

        print(Transcription.hebrew_mapping['00'])

    Output:

        ׃
    """

    hebrew_cons = ">BGDHWZXVJKLMNS<PYQRFCT"
    trans_final_pat = re.compile(
        r"(["
        + hebrew_cons
        + r"][^_&]*)([KMNPY])([^"
        + hebrew_cons
        + r"_&]*(:?[_&]|\Z))"
    )
    trans_hebrew_pat = re.compile(r"(:[AE@]|.[cf]|:|[0-9][0-9]|.)")
    swap_accent_pat = re.compile(
        r"(\A|[_&])([0-9][0-9])([" + hebrew_cons + r"])([:;,.EAIOU@]*)"
    )
    remove_accent_pat = re.compile(r"((?:[0-9][0-9])|[,*])")
    remove_point_pat = re.compile(
        r"((?:[0-9][0-9])|(?:\.[cf])|(?::[@AE])|[,.:;@AEIOU*])"
    )
    remove_psn_pat = re.compile(r"00[ _SPNÑñ]*")
    remove_psq_pat = re.compile(r"(?:[ _]+05[ _]*)|(?:05[ _]+)")
    shin_pat = re.compile(r"[CF]")
    ph_simple_pat = re.compile(r"([ˈˌᵊᵃᵒᵉāo*])")
    noorigspace = re.compile(
        r"""
          (?: [&-]\Z)           # space, maqef or nospace
        | (?:
               0[05]            # sof pasuq or paseq
               (?:_[SNP])*      # nun hafukha, setumah, petuhah at end of verse
               \Z
          )
        | (?:_[SPN])+           #  nun hafukha, setumah, petuhah between words
    """,
        re.X,
    )

    syriac_mapping_simple = {
        ">": "\u0710",  # alaph
        "B": "\u0712",  # beth
        "G": "\u0713",  # gamal
        "D": "\u0715",  # dalat
        "H": "\u0717",  # he
        "W": "\u0718",  # waw
        "Z": "\u0719",  # zain
        "X": "\u071A",  # heth
        "V": "\u071B",  # teth
        "J": "\u071D",  # yudh
        "K": "\u071F",  # kaph
        "L": "\u0720",  # lamadh
        "M": "\u0721",  # mim
        "N": "\u0722",  # nun
        "S": "\u0723",  # semkath
        "<": "\u0725",  # e
        "P": "\u0726",  # pe
        "Y": "\u0728",  # sadhe
        "Q": "\u0729",  # qaph
        "R": "\u072A",  # rish
        "C": "\u072B",  # shin
        "T": "\u072C",  # taw
        "s": "\u0724",  # semkath final
        "p": "\u0727",  # pe reversed
    }

    syriac_mapping_pil = {
        # LETTERS
        "'": "\u0710",  # alaph
        "b": "\u0712",  # beth
        "g": "\u0713",  # gamal
        "d": "\u0715",  # dalat
        "h": "\u0717",  # he
        "w": "\u0718",  # waw
        "z": "\u0719",  # zain
        "H": "\u071A",  # heth
        "T": "\u071B",  # teth
        "y": "\u071D",  # yod
        "k": "\u071F",  # kaf
        "l": "\u0720",  # lamad
        "m": "\u0721",  # mim
        "n": "\u0722",  # nun
        "s": "\u0723",  # semkath
        "`": "\u0725",  # 'e
        "p": "\u0726",  # pe
        "S": "\u0728",  # tsade
        "q": "\u0729",  # qof
        "r": "\u072A",  # resh
        "$": "\u072B",  # shin
        "t": "\u072C",  # taw
        # WORD-BOUND DIACRITICS
        '"': "\u0308",  # seyame
        "#": "\u0323",  # diacritical dot below
        "^": "\u0307",  # diacritical dot above
        "~": "\u0307",  # abbreviation mark
        # NON-VOCALIC LETTER-BOUND DIACRITICS
        "#,": "\u0742",  # rukkakha
        '#"': "\u0342",  # unclear (COMBINING DIAERESIS BELOW)
        "#!": "\u0744",  # unclear (SYRIAC TWO VERTICAL DOTS BELOW)
        "#_": "\u0331",  # linea occultans infera
        "^,": "\u0741",  # qushshaya
        "^!": "\u0743",  # unclear (SYRIAC TWO VERTICAL DOTS ABOVE)
        "^_": "\u0304",  # linea occultans supera
        # VOCALIC LETTER-BOUND DIACRITICS
        ":": "",  # shewa
        "A": "\u0733",  # qamets
        "A1": "\u0734",  # zeqapa
        "A2": "\u0735",  # zeqofo
        "E": "\u0739",  # tsere, revasa karya
        "O": "\u073F",  # holem, rewaha
        "a": "\u0730",  # patah
        "a1": "\u0731",  # petaha
        "a2": "\u0732",  # petoho
        "e": "\u0736",  # segol
        "e1": "\u0737",  # revasa arrika
        "e2": "\u0738",  # revoso
        "i": "\u073A",  # hireq
        "i1": "\u073B",  # hevoso
        "y#": "\u071D\u073C",  # hevasa
        "u": "\u073D",  # qubbuts
        "u1": "\u073E",  # esoso
        "w#": "\u0718\u073C",  # esasa allisa
        "w^": "\u0718\u073F",  # esasa rewiha
        # INTERPUNCTION
        "#.": "\u0702",  # menachta, meshalyana (ES), metdamrana, samka
        "#:": "\u0704",  # metkashpana (ES)
        "#\\": "\u0709",  # tahtaya, metkashpana (WS), meshalyana (WS)
        "=.": "\u002E",  # pasuqa
        "=/": "\u0707",  # elaya
        "=:": "\u003A",  # shewaya (WS), zauga (ES)
        "=\\": "\u0706",  # unclear (SYRIAC COLON SKEWED LEFT)
        "^.": "\u0701",  # paquda, metkashpana (ES), meshalyana (ES), etsyana, meshalana?
        '^"': "\u0705",  # rahta
        "^:": "\u0703",  # taksa (WS), zauga elaya (ES)
        "^\\": "\u0708",  # unclear (SYRIAC SUPRALINEAR COLON SKEWED LEFT)
        # PERICOPE MARKERS
        "*": "\u0700",  # rosette
        ".": "\u00B7",  # common dot in caesuras
        "@": "\u2722",  # vignette
        "_": "\u2014",  # dash in caesuras
        "o": "\u2022",  # large dot in caesuras
    }

    syriac_mapping = {  # this is WIT
        # LETTERS
        ">": "\u0710",  # alaph
        "B": "\u0712",  # beth
        "G": "\u0713",  # gamal
        "D": "\u0715",  # dalat
        "H": "\u0717",  # he
        "W": "\u0718",  # waw
        "Z": "\u0719",  # zain
        "X": "\u071A",  # heth
        "V": "\u071B",  # teth
        "J": "\u071D",  # yod
        "K": "\u071F",  # kaf
        "L": "\u0720",  # lamad
        "M": "\u0721",  # mim
        "N": "\u0722",  # nun
        "S": "\u0723",  # semkath
        "<": "\u0725",  # 'e
        "P": "\u0726",  # pe
        "Y": "\u0728",  # tsade
        "Q": "\u0729",  # qof
        "R": "\u072A",  # resh
        "C": "\u072B",  # shin
        "T": "\u072C",  # taw
        # WORD-BOUND DIACRITICS
        '"': "\u0308",  # seyame
        "#": "\u0323",  # diacritical dot below
        "^": "\u0307",  # diacritical dot above
        # NON-VOCALIC LETTER-BOUND DIACRITICS
        "^!": "\u0743",  # unclear (SYRIAC TWO VERTICAL DOTS ABOVE)
        # VOCALIC LETTER-BOUND DIACRITICS
        ":": "",  # shewa
        "A": "\u0733",  # qamets
        "A1": "\u0734",  # zeqapa
        "A2": "\u0735",  # zeqofo
        "O": "\u073F",  # holem, rewaha
        "@": "\u0730",  # patah
        "@1": "\u0731",  # petaha
        "@2": "\u0732",  # petoho
        "E": "\u0736",  # segol
        "E1": "\u0737",  # revasa arrika
        "E2": "\u0738",  # revoso
        "I": "\u073A",  # hireq
        "I1": "\u073B",  # hevoso
        "U": "\u073D",  # qubbuts
        "U1": "\u073E",  # esoso
        # INTERPUNCTION
        "#\\": "\u0709",  # tahtaya, metkashpana (WS), meshalyana (WS)
        "=.": "\u002E",  # pasuqa
        "=#": "\u0707",  # elaya
        "=:": "\u003A",  # shewaya (WS), zauga (ES)
        "=^": "\u0706",  # unclear (SYRIAC COLON SKEWED LEFT)
        "=/": "\u0707",  # elaya
        "=\\": "\u0706",  # unclear (SYRIAC COLON SKEWED LEFT)
        "^:": "\u0703",  # taksa (WS), zauga elaya (ES)
        "^\\": "\u0708",  # unclear (SYRIAC SUPRALINEAR COLON SKEWED LEFT)
        # PERICOPE MARKERS
        "*": "\u0700",  # rosette
        ".": "\u00B7",  # common dot in caesuras
        "_": "\u2014",  # dash in caesuras
        "o": "\u2022",  # large dot in caesuras
    }
    """
    Maps all ETCBC transliteration character combinations for Syriac to Unicode.

    Example: print the semkath-final:

        print(Transcription.syriac_mapping['s'])

    Output:

        ܤ
    """

    trans_syriac_pat = re.compile(r"([AE@IU][12]?|=[.#:\^/\\]|[\^#][!:\\]|.)")

    arabic_mapping = {
        " ": "\u0020",  # SPACE
        "'": "\u0621",  # ARABIC LETTER HAMZA
        ">": "\u0623",  # ARABIC LETTER ALEF WITH HAMZA ABOVE
        "&": "\u0624",  # ARABIC LETTER WAW WITH HAMZA ABOVE
        "<": "\u0625",  # ARABIC LETTER ALEF WITH HAMZA BELOW
        "}": "\u0626",  # ARABIC LETTER YEH WITH HAMZA ABOVE
        "A": "\u0627",  # ARABIC LETTER ALEF
        "b": "\u0628",  # ARABIC LETTER BEH
        "p": "\u0629",  # ARABIC LETTER TEH MARBUTA
        "t": "\u062a",  # ARABIC LETTER TEH
        "v": "\u062b",  # ARABIC LETTER THEH
        "j": "\u062c",  # ARABIC LETTER JEEM
        "H": "\u062d",  # ARABIC LETTER HAH
        "x": "\u062e",  # ARABIC LETTER KHAH
        "d": "\u062f",  # ARABIC LETTER DAL
        "*": "\u0630",  # ARABIC LETTER THAL
        "r": "\u0631",  # ARABIC LETTER REH
        "z": "\u0632",  # ARABIC LETTER ZAIN
        "s": "\u0633",  # ARABIC LETTER SEEN
        "$": "\u0634",  # ARABIC LETTER SHEEN
        "S": "\u0635",  # ARABIC LETTER SAD
        "D": "\u0636",  # ARABIC LETTER DAD
        "T": "\u0637",  # ARABIC LETTER TAH
        "Z": "\u0638",  # ARABIC LETTER ZAH
        "E": "\u0639",  # ARABIC LETTER AIN
        "g": "\u063a",  # ARABIC LETTER GHAIN
        "_": "\u0640",  # ARABIC TATWEEL
        "f": "\u0641",  # ARABIC LETTER FEH
        "q": "\u0642",  # ARABIC LETTER QAF
        "k": "\u0643",  # ARABIC LETTER KAF
        "l": "\u0644",  # ARABIC LETTER LAM
        "m": "\u0645",  # ARABIC LETTER MEEM
        "n": "\u0646",  # ARABIC LETTER NOON
        "h": "\u0647",  # ARABIC LETTER HEH
        "w": "\u0648",  # ARABIC LETTER WAW
        "Y": "\u0649",  # ARABIC LETTER ALEF MAKSURA
        "y": "\u064a",  # ARABIC LETTER YEH
        "F": "\u064b",  # ARABIC FATHATAN
        "N": "\u064c",  # ARABIC DAMMATAN
        "K": "\u064d",  # ARABIC KASRATAN
        "a": "\u064e",  # ARABIC FATHA
        "u": "\u064f",  # ARABIC DAMMA
        "i": "\u0650",  # ARABIC KASRA
        "~": "\u0651",  # ARABIC SHADDA
        "o": "\u0652",  # ARABIC SUKUN
        "^": "\u0653",  # ARABIC MADDAH ABOVE
        "#": "\u0654",  # ARABIC HAMZA ABOVE
        "`": "\u0670",  # ARABIC LETTER SUPERSCRIPT ALEF
        "{": "\u0671",  # ARABIC LETTER ALEF WASLA
        ":": "\u06dc",  # ARABIC SMALL HIGH SEEN
        "@": "\u06df",  # ARABIC SMALL HIGH ROUNDED ZERO
        '"': "\u06e0",  # ARABIC SMALL HIGH UPRIGHT RECTANGULAR ZERO
        "[": "\u06e2",  # ARABIC SMALL HIGH MEEM ISOLATED FORM
        ";": "\u06e3",  # ARABIC SMALL LOW SEEN
        ",": "\u06e5",  # ARABIC SMALL WAW
        ".": "\u06e6",  # ARABIC SMALL YEH
        "!": "\u06e8",  # ARABIC SMALL HIGH NOON
        "-": "\u06ea",  # ARABIC EMPTY CENTRE LOW STOP
        "+": "\u06eb",  # ARABIC EMPTY CENTRE HIGH STOP
        "%": "\u06ec",  # ARABIC ROUNDED HIGH STOP WITH FILLED CENTRE
        "]": "\u06ed",  # ARABIC SMALL LOW MEEM
    }
    """
    Maps an Arabic transliteration character to Unicode.

    Example: print the beh

        print(Transcription.syriac_mapping['b'])

    Output:

        ب

    Maps an Arabic letter in unicode to its transliteration

    Example: print the beh transliteration

        print(Transcription.syriac_mapping['ب'])

    Output:

        b
    """

    arabic_mappingi = dict((v, k) for (k, v) in arabic_mapping.items())

    def __init__(self):
        self.hebrew_consonants = {
            Transcription.hebrew_mapping[x] for x in Transcription.hebrew_cons
        }
        self.hebrew_consonants.add("\u05E9")
        self.hebrew_mappingi = dict(
            (v, k) for (k, v) in Transcription.hebrew_mapping.items() if k != ""
        )
        self.syriac_mappingi = dict(
            (v, k) for (k, v) in Transcription.syriac_mapping.items() if k != ""
        )
        # special treatment needed for nun hafukha,
        # since it is consists of two characters
        self.hebrew_mappingi["\u05C6"] = "ñ"
        self.hebrew_mappingi["\u0307"] = ""
        self.syriac_punctuation_trans = (
            "#\\",
            "=.",
            "=#",
            "=:",
            "=^",
            "=/",
            "=\\",
            "^:",
            "^\\",
        )
        self.syriac_punctuation_syc = tuple(
            Transcription.syriac_mapping[c] for c in self.syriac_punctuation_trans
        )

    def sycSplitPunc(self):
        pass

    def _comp(s):
        for (d, c) in Transcription.decomp.items():
            s = s.replace(d, c)
        return s

    def _decomp(s):
        for (d, c) in Transcription.decomp.items():
            s = s.replace(c, d)
        return s

    def suffix_and_finales(word):
        """
        Given an ETCBC transliteration, split it into the word material
        and the interword material that follows it (space, punctuation).
        Replace the last consonant of the word material by its final form, if applicable.

        Output a tuple with the modified word material and the interword material.

        Example:

            print(Transcription.suffix_and_finales('71T_H@>@95REY00'))

        Output:

            ('71T_H@>@95REy', '00\n')

        Note that the `Y` has been replaced by `y`.
        """

        # first split the word proper from the suffix,
        # and add a space if there is no other suffix
        add_space = ""
        suffix = ""
        new_word = word
        if not word:
            return (new_word, suffix + add_space)
        lastch = new_word[-1]
        if lastch == "-" or lastch == "&":
            new_word = new_word[0:-1]
            suffix = lastch
        else:
            if len(new_word) >= 2:
                lastch = new_word[-1]
                llastch = new_word[-2]
                if llastch == "_" and (lastch == "P" or lastch == "S"):
                    new_word = new_word[0:-2]
                    suffix = " " + lastch + suffix + " "
            if len(new_word) >= 2:
                lastch = new_word[-1]
                llastch = new_word[-2]
                if llastch == "_" and (lastch == "N"):
                    new_word = new_word[0:-2]
                    suffix = " ñ" + suffix + " "
            if len(new_word) >= 2:
                lastch = new_word[-1]
                llastch = new_word[-2]
                if llastch == "0" and (lastch == "0" or lastch == "5"):
                    new_word = new_word[0:-2]
                    suffix = (" " if lastch == "5" else "") + llastch + lastch + suffix
                    add_space = "\n" if lastch == "0" else " "
        if suffix == "":
            add_space = " "
        elif suffix == "-":
            add_space = ""
            suffix = ""
        # second: replace consonants by their final forms when needed
        new_word = Transcription.trans_final_pat.sub(Transcription._map_final, new_word)
        return (new_word, suffix + add_space)

    def _map_final(m):
        return m.group(1) + m.group(2).lower() + m.group(3)

    def _map_hebrew(m):
        return Transcription.hebrew_mapping.get(m.group(1), m.group(1))

    def _map_syriac(m):
        return Transcription.syriac_mapping.get(m.group(1), m.group(1))

    def _swap_accent(m):
        return m.group(1) + m.group(3) + m.group(4) + m.group(2)

    def _remove_accent(m):
        return "00" if m.group(1) == "00" else "05" if m.group(1) == "05" else ""

    def _remove_point(m):
        return "00" if m.group(1) == "00" else "05" if m.group(1) == "05" else ""

    def _ph_simple(m):
        return "å" if m.group(1) in "āo" else ""

    # unicode normalization is harmful
    # if there is a combination of dagesh, vowel and accent.

    def suppress_space(word):
        """
        Given an ETCBC transliteration of a word,
        match the end of the word for interpunction and spacing characters
        (sof pasuq, paseq, nun hafukha, setumah, petuhah, space, no-space)

        Example:

            print(Transcription.suppress_space('B.:&'))
            print(Transcription.suppress_space('B.@R@74>'))
            print(Transcription.suppress_space('71T_H@>@95REY00'))

        Output:

            <re.Match object; span=(3, 4), match='&'>
            None
            <re.Match object; span=(13, 15), match='00'>
        """

        return Transcription.noorigspace.search(word)

    def to_etcbc_v(word):
        """
        Given an ETCBC transliteration of a fully pointed word,
        strip all the non-vowel pointing (i.e. the accents).

        Example:

            print(Transcription.to_etcbc_v('HAC.@MA73JIm'))

        Output:

            HAC.@MAJIm
        """

        return Transcription.remove_accent_pat.sub(Transcription._remove_accent, word)

    def to_etcbc_c(word):
        """
        Given an ETCBC transliteration of a fully pointed word,
        strip everything except the consonants.
        Punctuation will also be stripped.

        Example:

            print(Transcription.to_etcbc_c('HAC.@MA73JIm'))

        Output:

            H#MJM

        Note that the pointed shin (`C`) is replaced by an unpointed one (`#`).
        """

        word = Transcription.remove_point_pat.sub(Transcription._remove_point, word)
        word = Transcription.remove_psn_pat.sub(
            "00", word
        )  # remove nun hafukha, setumah, petuhah at the end of a verse
        word = Transcription.remove_psq_pat.sub(
            " ", word
        )  # replace paseq with attached spaces by single space
        word = word.upper()  # no final forms of consonants
        return Transcription.shin_pat.sub("#", word)

    def to_hebrew(word):
        """
        Given a transliteration of a fully pointed word,
        produce the word in Unicode Hebrew.
        Care will be taken that vowel pointing will be added to consonants
        before accent pointing.

        Example:

            print(Transcription.to_hebrew('HAC.@MA73JIm'))

        Output:

            הַשָּׁמַ֖יִם
        """

        word = Transcription.swap_accent_pat.sub(Transcription._swap_accent, word)
        return Transcription.trans_hebrew_pat.sub(Transcription._map_hebrew, word)

    def to_hebrew_v(word):
        """
        Given a transliteration of a fully pointed word,
        produce the word in Unicode Hebrew, but without the accents.

        Example:

            print(Transcription.to_hebrew_v('HAC.@MA73JIm'))

        Output:

            הַשָּׁמַיִם
        """

        return Transcription.trans_hebrew_pat.sub(
            Transcription._map_hebrew, Transcription.to_etcbc_v(word)
        )

    def to_hebrew_c(word):
        """
        Given a transliteration of a fully pointed word,
        produce the word in Unicode Hebrew, but without the pointing.

        Example:

            print(Transcription.to_hebrew_c('HAC.@MA73JIm'))

        Output:

            השמימ

        Note that final consonant forms are not being used.
        """

        return Transcription.trans_hebrew_pat.sub(
            Transcription._map_hebrew, Transcription.to_etcbc_c(word)
        )

    def to_hebrew_x(word):
        """
        Given a transliteration of a fully pointed word,
        produce the word in Unicode Hebrew, but without the pointing.
        Vowel pointing and accent pointing will be applied in the order given
        by the input word.

        Example:

            print(Transcription.to_hebrew_x('HAC.@MA73JIm'))

        Output:

            הַשָּׁמַ֖יִם
        """

        return Transcription.trans_hebrew_pat.sub(Transcription._map_hebrew, word)

    def ph_simplify(pword):
        """
        Given a phonological transliteration of a fully pointed word,
        produce a more coarse phonological transliteration.

        Example:

            print(Transcription.ph_simplify('ʔᵉlōhˈîm'))
            print(Transcription.ph_simplify('māqˈôm'))
            print(Transcription.ph_simplify('kol'))

        Output:

            ʔlōhîm
            måqôm
            kål

        Note that the simplified version transliterates the qamets gadol and qatan
        to the same
        character.
        """

        return Transcription.ph_simple_pat.sub(Transcription._ph_simple, pword)

    def from_hebrew(self, word):
        """
        Given a fully pointed word in Unicode Hebrew,
        produce the word in ETCBC transliteration.

        Example:

            print(tr.from_hebrew('הָאָֽרֶץ׃'))

        Output:

            H@>@95REy00
        """

        return "".join(
            self.hebrew_mappingi.get(x, x) for x in Transcription._comp(word)
        )

    def to_syriac(self, word):
        """
        Given a word in ETCBC transliteration,
        produce the word in Unicode Syriac.

        Example:

            print(tr.to_syriac('MKSJN'))

        Output:

            ܡܟܣܝܢ
        """

        return Transcription.trans_syriac_pat.sub(Transcription._map_syriac, word)

    def from_syriac(self, word):
        """
        Given a word in Unicode Syriac,
        produce the word in ETCBC transliteration.

        Example:

            print(tr.from_syriac('ܡܟܣܝܢ'))

        Output:

            MKSJN
        """

        return "".join(self.syriac_mappingi.get(x, x) for x in word)

    def can_to_syriac(self, word):
        return all(
            candidate in Transcription.syriac_mapping
            for candidate in Transcription.trans_syriac_pat.findall(word)
            if candidate != " "
        )

    def can_from_syriac(self, word):
        return all(c in self.syriac_mappingi for c in word if c != " ")

    def to_arabic(word):
        """
        Given a word in transliteration,
        produce the word in Unicode Arabic.

        Example:

            print(tr.to_arabic('bisomi'))

        Output:

            بِسْمِ
        """

        return "".join(Transcription.arabic_mapping.get(x, x) for x in word)

    def from_arabic(word):
        """
        Given a word in Unicode Arabic,
        produce the word in transliteration.

        Example:

            print(tr.from_arabic('بِسْمِ'))

        Output:

            bisomi
        """

        return "".join(Transcription.arabic_mappingi.get(x, x) for x in word)
