# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.11.4
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# + [markdown] jp-MarkdownHeadingCollapsed=true tags=[]
# # Pretty display with editable fields
#
# ## Mockup
#
# We mock up a pretty display with editable fields: Genesis 1:1 in phonological transcription

# + [markdown] tags=[]
# # Load the BHSA
#
# We load the BHSA and display the example in question.
# -

# %load_ext autoreload
# %autoreload 2

# +
# pip3 install beautifulsoup4

from bs4 import BeautifulSoup as bs

from tf.app import use
from tf.advanced.helpers import dh
# -

A = use("bhsa", hoist=globals())

from ipywidgets import Text, Layout, Box, HBox, VBox, Label, HTML, Button

v1 = T.nodeFromSection(("Genesis", 1, 1))
A.pretty(v1, standardFeatures=True, fmt="text-phono-full")

# What we want is a display like this, but with the glosses (`in` `beginning` `create` etc) editable.
# Also all values after `pdp=` should be editable. And the information in the labels with clause and phrase as well
# (`xQtX`, `PP`, `Time`) etc. If you hover over them, you see they are values of features `typ`, `rela` and `function`.
#
# The task is to rebuild this from the
# [layout widgets of ipywidgets](https://ipywidgets.readthedocs.io/en/7.6.3/examples/Widget%20Styling.html),
# such as Box, HBox, VBox, HTML.
#
# We start with something simpler, the first phrase (`in beginning`), without the passage reference.
# We first generate the html, then display it
#

p1 = F.otype.s("phrase")[0]
html = A.pretty(p1, standardFeatures=True, fmt="text-phono-full", withPassage=False, _asString=True)
dh(html)


# We could also show the underlying HTML as a decently formatted string,
# using *beautifulsoup* and a convenience function:

# +
def pdh(html):
    print(bs(html).prettify())

# pdh(html)


# + [markdown] tags=[]
# # Displaying
#
# We have a (clumsy) shot at displaying this phrase with editable content.
# -

word1 = """<a
  class="txtu hbo"
  href="https://shebanq.ancient-data.org/hebrew/word?version=2021&amp;id=1B"
  target="_blank"
  title="Show this on SHEBANQ">
        <span class="txtp">
         bᵊ
        </span>
       </a>"""
word2 = """<a
  class="txtu hbo"
  href="https://shebanq.ancient-data.org/hebrew/word?version=2021&amp;id=1RACJTn"
  target="_blank"
  title="Show this on SHEBANQ">
        <span class="txtp">
         rēšˌîṯ
        </span>
       </a>"""
gloss1 = "in"
gloss2 = "beginning"
pdp1 = "prep"
pdp2 = "subs"

layout1 = Layout(flex="auto 1 1")
layout1a = Layout(
    flex="auto 0 0",
    overflow="hidden",
)
layout1b = Layout(
    flex="auto 1 1",
    overflow="auto",
)
layout2 = Layout(
    display="inline-flex",
    flex_flow="column nowrap",
    border="2px solid gray",
    flex="auto 0 1",
    overflow="auto",
)
layout2a = Layout(
    display="inline-flex",
    flex_flow="column nowrap",
    border="2px solid gray",
    flex="auto 0 1",
    overflow="auto",
)
layout2b = Layout(
    display="inline-flex",
    flex_flow="row wrap",
    border="1px solid gray",
    flex="auto 0 1",
    overflow="auto",
)

w1 = Box(
    [
        HTML(value=word1, layout=layout1),
        Text(value=gloss1, placeholder="gloss", layout=layout1a),
        Box([HTML(value="pdp="), Text(value=pdp1, placeholder="pdp", layout=layout1a)], layout=layout1b),
    ],
    layout=layout2,
)

# + tags=[]
display(w1)
# -

w2 = Box(
    [
        HTML(value=word2, layout=layout1),
        Text(value=gloss2, placeholder="gloss", layout=layout1a),
        Text(value=pdp2, placeholder="pdp", description="pdp=", layout=layout1a),
    ],
    layout=layout2,
)

# + tags=[]
display(w2)
# -

layout3 = Layout(align_content="flex-start")
w12 = Box([w1, w2], layout=layout3)

# + tags=[]
display(w12)

# +
typ = "PP"
function = "Time"

w = Box(
    [
        Box(
            [
                HTML(value="phrase", layout=layout1),
                Text(value=typ, placeholder="typ", layout=layout1a),
                Text(value=function, placeholder="function", layout=layout1a),
            ],
            layout=layout2b,
        ),
        w12,
    ],
    layout=layout2a,
)
# -

display(w)

# The styling and layout are far from optimal.
# But for the moment it will do.

# + [markdown] tags=[]
# # Updating
#
# Now we want to change values and save them.
#
# For the moment, we store the data in dictionaries, keyed by feature name and then by node.
#
# We regenerate the display in a different way, but before we do that, we display the phrase with node numbers.
# -

A.pretty(p1, standardFeatures=True, fmt="text-phono-full", withPassage=False, withNodes=True)

# ## Context
#
# Knowledge about the features.

# +
standardFeatures = {"typ", "function", "gloss"}

featsFromType = dict(
    phrase=["typ", "function"],
    word=["gloss", "pdp"],
)
featOrder = ("_", "typ", "function", "gloss", "pdp")
# -

# ## Arguments
#
# Initial values of the features and structure of the data to display.

features = dict(
    typ={
        651573: "PP",
    },
    function={
        651573: "Time",
    },
    gloss={
        1: "in",
        2: "beginning",
    },
    pdp={
        1: "prep",
        2: "subs",
    },
    _= {
        1: "bᵊ",
        2: "rēšˌîṯ",
    },
)
structure = [
    ("phrase", 651573),
    [("word", 1)], 
    [("word", 2)],
]

# When we create the display, we use the info in the dict `features` to provide the edit widgets with initial values.
# It also contains the texts to display with nodes, in the pseudo feature `_`.
#
# We write a function called `place` to place an editable representation of a node in an output cell.
# Its arguments are the structure and the initial values.
#
# We do not pass `standardFeatures` and `featsFromType`, we consider that part of the context that `place()` has access to.
# In it, 
# we create a dictionary `widgets` with the same structure, but the values are now handles to the corresponding widgets.
#
# Finally we have to attach event handlers to all widgets whose values may change.

layoutCommon = dict(
    align_items="flex-start",
    align_content="flex-start",
    justify_content="flex-start",
)
layoutA = Layout(
    overflow="hidden",
    flex="auto 0 0",
    **layoutCommon
)
layoutV = Layout(
    display="inline-flex",
    flex_flow="column nowrap",
    overflow="auto",
    border="1px solid gray",
    flex="auto 0 0",
    **layoutCommon
)
layoutV2 = Layout(
    display="inline-flex",
    flex_flow="column nowrap",
    overflow="auto",
    border="3px solid gray",
    flex="auto 0 0",
    **layoutCommon
)
layoutV3 = Layout(
    display="flex",
    flex_flow="column nowrap",
    align_items="flex-start",
    overflow="auto",
    border="2px solid #eeeeee",
    flex="auto 0 0",
)
layoutH = Layout(
    display="inline-flex",
    flex_flow="row wrap",
    overflow="auto",
    border="3px solid gray",
    flex="auto 0 0",
    **layoutCommon
)
layoutST = Layout(
    # width="100%",
    # overflow="auto",
    flex="auto 1 1",
)
layoutSV = Layout(
    # width="100%",
    # overflow="auto",
    flex="auto 1 1",
    border="1px solid black",
)


def place(structure, features):
    widgets = {}
    for (feat, values) in features.items():
        for (node, value) in values.items():
            if feat == "_":
                w = HTML(value=value, layout=layoutA)
            else:
                params = dict(value=value, placeholder="feat", layout=layoutA)
                if feat not in standardFeatures:
                    params["description"] = f"{feat}="
                w = Text(**params)
            widgets.setdefault(feat, {})[node] = w

    def build(fragments):
        result = []

        for fragment in fragments:
            (nType, node) = fragment[0]
            children = fragment[1:]

            ws = [HTML(value=nType, layout=layoutA)]
            feats = featsFromType[nType]
            for feat in featOrder:
                if feat != "_" and feat not in feats:
                    continue
                wf = widgets.get(feat, {}).get(node, None)
                if wf is not None:
                    ws.append(wf)

            nodeResult = Box(ws, layout=layoutV) if len(ws) > 1 else ws[0]
            childrenResult = build(children)

            if childrenResult:
                thisResult = Box([nodeResult, childrenResult], layout=layoutV2)
            else:
                thisResult = nodeResult
            result.append(thisResult)

        if len(result) == 0:
            return None
        if len(result) == 1:
            return result[0]
        return Box(result, layout=layoutH)

    def observe(widgets):
        updates = {}

        status = Label(value="Up to date", layout=layoutST)
        save = Button(description="Save", layout=layoutSV, disabled=True)

        def handleSave(b):
            if updates:
                for (feat, upds) in updates.items():
                    for (node, value) in upds.items():
                        features.setdefault(feat, {})[node] = value
                updates.clear()
            status.value = "Up to date"
            save.disabled = True

        save.on_click(handleSave)

        def makeHandler(feat, node):
            def handleChange(change):
                updates.setdefault(feat, {})[node] = change.new
                status.value = (
                    f"""node {node} feature {feat} changed from '{change.old}' to '{change.new}'. """
                )
                save.disabled = False

            return handleChange

        for (feat, ws) in widgets.items():
            for (node, w) in ws.items():
                if type(w) is not Text:
                    continue
                w.continuous_update = False
                w.observe(makeHandler(feat, node), names="value")
        
        return (status, save)

    w = Box([build([structure]), *observe(widgets)], layout=layoutV3)
    display(w)


place(structure, features)

# Before we start doing anything, we inspect the current values of the first phrase feature (`typ`):

features["typ"]

# Make a change to the PP value.
# The button that says Up-to-date will change and show the change, and you can click to save the change back to the
# `features` dictionary.
#
# Before that click, the button looks like this
#
# ![button](images/button.png)

# After saving a change, inspect the current value of the first phrase feature (`typ`)

features["typ"]


# + [markdown] jp-MarkdownHeadingCollapsed=true tags=[]
# # Editable displays are possible
#
# Remarkable: your change has been saved!
#
# What does this really mean?
#
# Well, the widget gives you a user interface with which you can interact.
# This happens solely in the browser, through Javascript.
#
# However, through observing, we can make the Python kernel aware of the changes, and store them in a Python
# dictionary.
#
# In the end, we have changed Python data through Javascript.
#
# Put otherwise: we have changed Python data without running code cells, only by interacting with output cells.
#
# Users can now create/update annotations to a text inside a Jupyter notebook.

# + [markdown] tags=[]
# # Further steps
#
# We can now write functions in Text-Fabric that let users edit feature data and save it back to other features
# or the same feature.
#
# Probably it is better to accomodate features in a local `edit` directory alongside the original features,
# so that the original features stay untouched.
#
# When loading features, we can ask Text-Fabric to use the features in `edit` to override existing features.
#
# When such edited features gain quality, the author can share them in his/her own github repo as a new
# data module.
#
# Imagine you can do a query and view its results while being able to change odd feature values and save it to a 
# solid file on disk. Or comment on the query results one by one, storing the comments in a new, personal feature.
#
# See [datasharing](https://annotation.github.io/text-fabric/tf/about/datasharing.html).
#
# -

# # Low level experiments
#
# What follows are some intermediate bits and pieces where I try certain things out.

# +
def vbox(contents): 
    return f"""
<div style="
    display: flex;
    flex-flow: column nowrap;
    align-items: flex-start;
    align-content: flex-start;
    justify-content: flex-start;
    border: 3px solid blue;
    margin: 1em;
    padding: 1em;
    "
>{contents}</div>
"""

def hbox(contents): 
    return f"""
<div style="
    display: inline-flex;
    flex-flow: row wrap;
    align-items: flex-start;
    align-content: flex-start;
    justify-content: flex-start;
    border: 3px solid red;
    margin: 1em;
    padding: 1em;
    "
>{contents}</div>
"""


def abox(contents):
    return f"""
<div style="
    flex: auto 0 0;
    align-items: flex-start;
    align-content: flex-start;
    justify-content: flex-start;
    border: 2px solid gray;
    margin: 0.5em;
    padding: 0.5em;
    "
>{contents}</div>
"""

blocks = ["A", "B", "C"]
html = hbox(vbox("".join(abox(b) for b in blocks)))
dh(html)
