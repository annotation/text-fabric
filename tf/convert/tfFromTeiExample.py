"""This is example code for calling the TEI to TF conversion.

Put this in the `programs` directory of your corpus, tweak it and
run it.
"""

from tf.convert.tei import TEI
from tf.core.files import baseNm


TEST_SET = set(
    '''
    18920227_HMKR_0001.xml
    18920302_HMKR_0002.xml
    18930711_PM_RANI_5003.xml
    18980415y_PRIX_0007.xml
    '''.strip().split()
)

AUTHOR = "Piet Mondriaan"
TITLE = "Letters"
INSTITUTE = "KNAW/Huygens Amsterdam"

GENERIC = dict(
    author=AUTHOR,
    title=TITLE,
    institute=INSTITUTE,
    language="nl",
    converters="Dirk Roorda (Text-Fabric)",
    sourceFormat="TEI",
    descriptionTf="Critical edition",
)

ABOUT_TEXT = '''
# CONTRIBUTORS

Researcher: Mariken Teeuwen

Editors: Peter Boot et al.
'''

TRANSCRIPTION_TEXT = '''

The TEI has been validated and polished
before generating the TF data.
'''

DOC_MATERIAL = dict(
    about=ABOUT_TEXT,
    trans=TRANSCRIPTION_TEXT,
)

CONFIG = dict(
    provenanceSpec=dict(
        corpus=f"{GENERIC['author']} - {GENERIC['title']}",
        doi="10.5281/zenodo.nnnnnn",
    )
)


HY = "\u2010"  # hyphen


def transform(text):
    return text.replace(",,", HY)


if __name__ == "__main__":
    T = TEI(
        schema="MD",
        sourceVersion="2023-01-31",
        testSet=TEST_SET,
        wordAsSlot=True,
        sectionModel=dict(model="I"),
        generic=GENERIC,
        transform=transform,
        tfVersion="0.1",
        appConfig=CONFIG,
        docMaterial=DOC_MATERIAL,
        force=True,
    )

    T.run(baseNm(__file__))
