import re
import unicodedata

class Transcription(object):
    decomp = {
        '\u05E9\u05C1': "\uFB2A",
        '\u05E9\u05C2': "\uFB2B",
    }
    hebrew_mapping = {
        '_': ' ', # space inside word
        '92': "\u0591", # etnahta = atnach
        '01': "\u0592", # segolta
        '65': "\u0593", # shalshelet
        '80': "\u0594", # zaqef_qatan
        '85': "\u0595", # zaqef_gadol
        '73': "\u0596", # tipeha = tifcha
        '81': "\u0597", # revia = rebia
        '82': "\u0598", # zarqa = tsinorit = zinorit = sinnorit
        '03': "\u0599", # pashta
        '10': "\u059A", # yetiv = yetib
        '91': "\u059B", # tevir = tebir
        '61': "\u059C", # geresh
        '11': "\u059D", # geresh muqdam = mugrash
        '62': "\u059E", # gershayim = garshayim
        '84': "\u059F", # qarney para = pazer_gadol
        '14': "\u05A0", # telisha_gedola
        '44': "\u05A0", # telisha_gedola = telisha_gedola_med
        '83': "\u05A1", # pazer
        '74': "\u05A3", # munah = munach
        '70': "\u05A4", # mahapakh = mehuppach
        '71': "\u05A5", # merkha = merecha
        '72': "\u05A6", # merkha kefula = merecha_kepula
        '94': "\u05A7", # darga
        '63': "\u05A8", # qadma = azla
        '33': "\u05A8", # pashta_med < qadma
        '04': "\u05A9", # telisha_qetana
        '24': "\u05A9", # telisha_qetana = telisha_qetana_med
        '93': "\u05AA", # yera ben yomo = yerach
        '60': "\u05AB", # ole = ole_weyored
        '64': "\u05AC", # iluy = illuy
        '13': "\u05AD", # dehi = dechi
        '02': "\u05AE", # zinor = sinnor
        '*': "\u05AF", # masora circle
        ':': "\u05B0", # sheva = shewa
        ':E': "\u05B1", # hataf segol = chataph_segol
        ':A': "\u05B2", # hataf patah = chataph_patach
        ':@': "\u05B3", # hataf qamats = chataph_qamats
        'I': "\u05B4", # hiriq = chiriq
        ';': "\u05B5", # tsere
        'E': "\u05B6", # segol
        'A': "\u05B7", # patach
        '@': "\u05B8", # qamats
        'O': "\u05B9", # holam = cholam
        'U': "\u05BB", # qubuts = qubbuts
        '.': "\u05BC", # dagesh
        '25': "\u05BD", # silluq yamin 
        '45': "\u05BD", # meteg 
        '35': "\u05BD", # meteg (tikon)
        '75': "\u05BD", # siluq = silluq
        '95': "\u05BD", # meteg = meteg_yamin
        '&': "\u05BE", # maqaf
        ',': "\u05BF", # rafe = raphe
        '05': "\u05C0", # paseq
        '.c': "\u05C1", # shin dot
        '.f': "\u05C2", # sin dot
        '00': "\u05C3", # sof_pasuq
        '52': "\u05C4", # upper dot = puncta_above
        '53': "\u05C5", # lower dot = puncta_below
        'ñ': "\u05C6\u0307", # nun hafukha
        'Ñ': "\u05C6\u0307", # nun hafukha
        '>': "\u05D0", # alef
        'B': "\u05D1", # bet
        'G': "\u05D2", # gimel
        'D': "\u05D3", # dalet
        'H': "\u05D4", # he
        'W': "\u05D5", # vav
        'Z': "\u05D6", # zayin
        'X': "\u05D7", # het
        'V': "\u05D8", # tet
        'J': "\u05D9", # yod
        'k': "\u05DA", # kaf final
        'K': "\u05DB", # kaf
        'L': "\u05DC", # lamed
        'm': "\u05DD", # mem final
        'M': "\u05DE", # mem
        'n': "\u05DF", # nun final
        'N': "\u05E0", # nun
        'S': "\u05E1", # samekh
        '<': "\u05E2", # ayin
        'p': "\u05E3", # pe final
        'P': "\u05E4", # pe
        'y': "\u05E5", # tsadi final
        'Y': "\u05E6", # tsadi
        'Q': "\u05E7", # qof
        'R': "\u05E8", # resh
        '#': "\u05E9", # sin unpointed
        'T': "\u05EA", # tav
        'C': "\uFB2A", # shin pointed
        'F': "\uFB2B", # sin pointed
        '55': "<UNMAPPED 55=large letter>", # large_letter
        '56': "<UNMAPPED 56=small letter>", # small_letter
        '57': "<UNMAPPED 57=suspended letter>", # suspended_letter
        '-': "", # suppress space afterward
    }
    hebrew_cons = '>BGDHWZXVJKLMNS<PYQRFCT'
    trans_final_pat = re.compile(r'([' + hebrew_cons + r'][^_&]*)([KMNPY])([^' + hebrew_cons + r'_&]*(:?[_&]|\Z))')
    trans_hebrew_pat = re.compile(r'(:[AE@]|.[cf]|:|[0-9][0-9]|.)')
    swap_accent_pat = re.compile(r'(\A|[_&])([0-9][0-9])([' + hebrew_cons + r'])([:;,.EAIOU@]*)')
    remove_accent_pat = re.compile(r'((?:[0-9][0-9])|[,*])')
    remove_point_pat  = re.compile(r'((?:[0-9][0-9])|(?:\.[cf])|(?::[@AE])|[,.:;@AEIOU*])')
    remove_psn_pat = re.compile(r'00[ _SPNÑñ]*')
    remove_psq_pat = re.compile(r'(?:[ _]+05[ _]*)|(?:05[ _]+)')
    shin_pat = re.compile(r'[CF]')
    ph_simple_pat = re.compile(r'([ˈˌᵊᵃᵒᵉāo*])')
    noorigspace = re.compile('''
          (?: [&-]\Z)           # space, maqef or nospace
        | (?: 
               0[05]            # sof pasuq or paseq
               (?:_[SNP])*      # nun hafukha, setumah, petuhah at end of verse
               \Z
          )
        | (?:_[SPN])+           #  nun hafukha, setumah, petuhah between words
    ''', re.X)


    syriac_mapping = {
        '>': "\u0710", # alaph
        'B': "\u0712", # beth
        'G': "\u0713", # gamal
        'D': "\u0715", # dalat
        'H': "\u0717", # he
        'W': "\u0718", # waw
        'Z': "\u0719", # zain
        'X': "\u071A", # heth
        'V': "\u071B", # teth
        'J': "\u071D", # yudh
        'K': "\u071F", # kaph
        'L': "\u0720", # lamadh
        'M': "\u0721", # mim
        'N': "\u0722", # nun
        'S': "\u0723", # semkath
        '<': "\u0725", # e
        'P': "\u0726", # pe
        'Y': "\u0728", # sadhe
        'Q': "\u0729", # qaph
        'R': "\u072A", # rish
        'C': "\u072B", # shin
        'T': "\u072C", # taw
        's': "\u0724", # semkath final
        'p': "\u0727", # pe reversed
    }

    def __init__(self):
        self.hebrew_consonants = {Transcription.hebrew_mapping[x] for x in Transcription.hebrew_cons}
        self.hebrew_consonants.add('\u05E9')
        self.hebrew_mappingi = dict((v,k) for (k,v) in Transcription.hebrew_mapping.items() if k != '')
        # special treatment needed for nun hafukha, since it is consists of two characters 
        self.hebrew_mappingi['\u05C6'] = 'ñ'
        self.hebrew_mappingi['\u0307'] = ''

    def _comp(s):
        for (d, c) in Transcription.decomp.items(): s = s.replace(d, c)
        return s
    def _decomp(s): 
        for (d, c) in Transcription.decomp.items(): s = s.replace(c, d)
        return s

    def suffix_and_finales(word):
        # first split the word proper from the suffix, and add a space if there is no other suffix
        add_space = ''
        suffix = ''
        new_word = word
        if not word:
            return (new_word, suffix + add_space)
        lastch = new_word[-1]
        if lastch == '-' or lastch == '&':
            new_word = new_word[0:-1]
            suffix = lastch
        else:
            if len(new_word) >= 2:
                lastch = new_word[-1]
                llastch = new_word[-2]
                if llastch == '_' and (lastch == 'P' or lastch == 'S'):
                    new_word = new_word[0:-2]
                    suffix = ' ' + lastch + suffix + ' '
            if len(new_word) >= 2:
                lastch = new_word[-1]
                llastch = new_word[-2]
                if llastch == '_' and (lastch == 'N'):
                    new_word = new_word[0:-2]
                    suffix = ' ñ' + suffix + ' '
            if len(new_word) >= 2:
                lastch = new_word[-1]
                llastch = new_word[-2]
                if llastch == '0' and (lastch == '0' or lastch == '5'):
                    new_word = new_word[0:-2]
                    suffix = (' ' if lastch == '5' else '') + llastch + lastch + suffix
                    add_space = '\n' if lastch == '0' else ' '
        if suffix == '': add_space = ' '
        elif suffix == '-':
            add_space = ''
            suffix = ''
        # second: replace consonants by their final forms when needed
        new_word = Transcription.trans_final_pat.sub(Transcription._map_final, new_word)
        return (new_word, suffix + add_space)

    def _map_final(m): return m.group(1) + m.group(2).lower() + m.group(3)
    def _map_hebrew(m): return Transcription.hebrew_mapping.get(m.group(1), m.group(1))
    def _swap_accent(m): return m.group(1) + m.group(3) + m.group(4) + m.group(2)
    def _remove_accent(m): return '00' if m.group(1) == '00' else '05' if m.group(1) == '05' else ''
    def _remove_point(m):  return '00' if m.group(1) == '00' else '05' if m.group(1) == '05' else ''
    def _ph_simple(m): return 'å' if m.group(1) in 'āo' else ''

# return unicodedata.normalize('NFKD', Transcription.trans_hebrew_pat.sub(Transcription._map_hebrew, nword))
# unicode normalization is harmful if there is a combination of dagesh, vowel and accent.

    def suppress_space(word):
        return Transcription.noorigspace.search(word)

    def to_etcbc_v(word):
        return Transcription.remove_accent_pat.sub(Transcription._remove_accent, word)

    def to_etcbc_c(word):
        word = Transcription.remove_point_pat.sub(Transcription._remove_point, word)
        word = Transcription.remove_psn_pat.sub('00', word) # remove nun hafukha, setumah, petuhah at the end of a verse
        word = Transcription.remove_psq_pat.sub(' ', word) # replace paseq with attached spaces by single space
        word = word.upper() # no final forms of consonants
        return Transcription.shin_pat.sub('#', word)

    def to_hebrew(word):
        word = Transcription.swap_accent_pat.sub(Transcription._swap_accent, word)
        return Transcription.trans_hebrew_pat.sub(Transcription._map_hebrew, word)

    def to_hebrew_v(word):
        return Transcription.trans_hebrew_pat.sub(Transcription._map_hebrew, Transcription.to_etcbc_v(word))

    def to_hebrew_c(word):
        return Transcription.trans_hebrew_pat.sub(Transcription._map_hebrew, Transcription.to_etcbc_c(word))

    def to_hebrew_x(word):
        return Transcription.trans_hebrew_pat.sub(Transcription._map_hebrew, word)

    def ph_simplify(pword): return Transcription.ph_simple_pat.sub(Transcription._ph_simple, pword)

    def from_hebrew(self, word): return ''.join(self.hebrew_mappingi.get(x, x) for x in Transcription._comp(word))
    def to_syriac(self, word): return Transcription._decomp(''.join(self.syriac_mapping.get(x, x) for x in Transcription._comp(word)))
    def from_syriac(self, word): return ''.join(self.syriac_mappingi.get(x, x) for x in Transcription._comp(word))


def monad_set(monadsrep):
    monads = set()
    for rng in monadsrep.split(','):
        bounds = rng.split('-')
        if len(bounds) == 2:
            for j in range(int(bounds[0]), int(bounds[1]) + 1): monads.add(j)
        else: monads.add(int(bounds[0]))
    return monads

object_rank = {
    'book': -4,
    'chapter': -3,
    'verse': -2,
    'half_verse': -1,
    'sentence': 1,
    'sentence_atom': 2,
    'clause': 3,
    'clause_atom': 4,
    'phrase': 5,
    'phrase_atom': 6,
    'subphrase': 7,
    'word': 8,
}

