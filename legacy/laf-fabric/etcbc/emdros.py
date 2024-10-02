import collections
from .lib import Transcription

# in version 4b we patch the following
#   we correct final consonants in various features
#   we add trailer_utf8

def patch(version, chunk, infile, outfile, dbnamei, dbnameo):
    def patch_copy():
        ifh = open(infile)
        ofh = open(outfile, 'w')
        print("Copying {} to {}".format(dbnamei, dbnameo))
        nl = 0
        nlc = 0
        for line in ifh:
            nl += 1
            nlc += 1
            if nlc == chunk:
                nlc = 0
                print('{:>9} lines'.format(nl))
            if nl < 10: line = line.replace(dbnamei, dbnameo)
            ofh.write(line)
        ifh.close()
        ofh.close()
        print('{:>9} lines'.format(nl))

    def patch_4b():
        ifh = open(infile)
        ofh = open(outfile, 'w')
        print("Patching (4b version) {} to {}".format(dbnamei, dbnameo))
        word_type = -1
        word_objects = 0
        in_word = 0
        features = collections.OrderedDict()
        nw = 0
        nl = 0
        nlc = 0
        for line in ifh:
            nl += 1
            nlc += 1
            if nlc == chunk:
                nlc = 0
                print('{:>9} lines, {:>7} words'.format(nl, nw))
            if nl < 10: line = line.replace(dbnamei, dbnameo)
            if word_type == 0:
                ofh.write('  trailer_utf8 : string DEFAULT "";\n')
                word_type = 1
            elif word_type == -1:
                if line.startswith('[word'): word_type = 0

            if word_objects == 0:
                if line.startswith('WITH OBJECT TYPE[word]'): word_objects = 1
            elif word_objects == 1:
                if line.startswith('WITH OBJECT TYPE[') and line[17] != 'w': word_objects = 0

            if word_objects == 1:
                if line.startswith('WITH ID_D'):
                    in_word = 1
                    features.clear()
                elif line.startswith(']'):
                    nw += 1
                    in_word = 0
                    for feat in features:
                        valraw = features[feat]
                        val = valraw.strip()[1:-2]
                        ofh.write('{}:={}'.format(feat, valraw))
                        if feat == 'g_word' or feat == 'g_cons' or feat == 'g_lex' or feat == 'lex':
                            (wval, trailer) = Transcription.suffix_and_finales(val)
                            if feat == 'g_word':
                                ofh.write('{}_utf8:="{}";\n'.format('trailer', Transcription.to_hebrew(trailer)))
                        else:
                            wval = val
                        ofh.write('{}_utf8:="{}";\n'.format(feat, Transcription.to_hebrew(wval)))

            skip = False
            if in_word and ':=' in line:
                (feat, val) = line.split(':=')
                if feat.endswith('_utf8'):
                    skip = True
                elif feat.startswith('g_') or feat.startswith('lex'):
                    features[feat] = val
                    skip = True

            if not skip:
                ofh.write(line)

        ifh.close()
        ofh.close()
        print('{:>9} lines, {:>7} words'.format(nl, nw))

    (patch_4b if version == '4b' else patch_copy)()


