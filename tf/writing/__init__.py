"""
# Writing systems support

Transliteration tables for various writing systems.

One can pass a language code to TF.

When TF displays text (e.g. in `tf.advanced.display`)
the language code may trigger the writing direction and the choice of font.

Here are the ones that have an effect:

`iso` | `language`
--- | ---
`akk` | `akkadian`
`hbo` | `hebrew`
`syc` | `syriac`
`uga` | `ugaritic`
`ara` | `arabic`
`grc` | `greek`
`cld` | `neo aramaic`

Default:
:   string `''`

"""
