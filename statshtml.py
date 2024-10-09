import sys

from tf.core.files import dirExists, dirContents, extNm, stripExt


statsDir = sys.argv[1]
indexFile = f"{statsDir}/index.html"


if not dirExists(statsDir):
    print(f"No stats directory found: {statsDir}")
    sys.exit(1)


files = dirContents(statsDir)[0]
mods = dirContents(f"{statsDir}/mod")[0]


htmlPre = """\
<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8"/>
    </head>
    <body>
        <h2>Overview</h2>
        <ul>
"""

htmlHead = """\
        </ul>
        <h2>By module</h2>
        <ul>
"""

htmlPost = """\
        </ul>
    </body>
</html>
"""

htmlInner = []


for file in sorted(files):
    if extNm(file) != "txt":
        continue

    ind = " " * 12
    name = stripExt(file)
    htmlInner.append(f"""{ind}<li><a href="{file}">{name}</a></li>""")

htmlInner.append(htmlHead)

for mod in sorted(mods):
    ind = " " * 12
    name = stripExt(mod)
    htmlInner.append(f"""{ind}<li><a href="mod/{mod}">{name}</a></li>""")

with open(indexFile, "w") as fh:
    htmlInner = "\n".join(htmlInner)
    fh.write(f"{htmlPre}{htmlInner}{htmlPost}")
