from tf.transcription import Transcription

tr = Transcription()

hebrew = 'בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים אֵ֥ת הַשָּׁמַ֖יִם וְאֵ֥ת הָאָֽרֶץ׃'

etcbc = tr.from_hebrew(hebrew)

print(etcbc)

print(Transcription.hebrew_mapping['00'])
print(Transcription.syriac_mapping['s'])
print(Transcription.suffix_and_finales('71T_H@>@95REY00'))
print(Transcription.suppress_space('B.:&'))
print(Transcription.suppress_space('B.@R@74>'))
print(Transcription.suppress_space('71T_H@>@95REY00'))
print(Transcription.to_etcbc_v('HAC.@MA73JIm'))
print(Transcription.to_etcbc_c('HAC.@MA73JIm'))
print(Transcription.to_hebrew('HAC.@MA73JIm'))
print(Transcription.to_hebrew_v('HAC.@MA73JIm'))
print(Transcription.to_hebrew_c('HAC.@MA73JIm'))
print(Transcription.to_hebrew_x('HAC.@MA73JIm'))
print(Transcription.ph_simplify('ʔᵉlōhˈîm'))
print(Transcription.ph_simplify('māqˈôm'))
print(Transcription.ph_simplify('kol'))
print(tr.from_hebrew('הָאָֽרֶץ׃'))
print(tr.from_syriac('ܡܟܣܝܢ'))
print(tr.to_syriac('MKSJN'))
