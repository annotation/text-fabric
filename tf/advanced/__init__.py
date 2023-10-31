"""
# Advanced API

A higher level API so that users can get the corpus data in a simple way
and can display materials of their corpus in an intuitive way.

There are many scenarios in which you can work with the advanced API:
in a Python script or in a notebook or in the TF browser.
If you `tf.browser.start` the TF browser, a `tf.browser.web` server is started.

The advanced API supports all these scenarios and is divided into these parts:

*   `Use`, see `tf.app.use` (call up a corpus)
*   `App`, see `tf.advanced.app` (the API of a corpus)
*   `Display`, see `tf.advanced.display` (displaying material)
*   `Linking`, see `tf.advanced.links` (generating useful links)
*   `Search`, see `tf.advanced.search` (control the search engine)
*   `Sections`, see `tf.advanced.sections` (headings for sections and structure)

Working behind the scenes:

*   `Settings`, see `tf.advanced.settings` (configure an app)
*   `Options` for display, see `tf.advanced.options` (tweak the display)
*   `Data`, see `tf.advanced.data` (load data)
*   `Repo`, see `tf.advanced.repo` (negotiate with the data back-end)

Lower level:

*   `Condense`, see `tf.advanced.condense` (distribute query results over containers)
*   `Find`, see `tf.advanced.find` (finding TF apps)
*   `Highlight`, see `tf.advanced.highlight` (highlight nodes in displays)
*   `Tables`, see `tf.advanced.tables` (tabular structures)
*   `Text`, see `tf.advanced.text` (text formats)
*   `ZipData`, see `tf.advanced.zipdata` (package and zip TF datasets for sharing)

Lowest level:

*   `Helpers`, see `tf.advanced.helpers` (the usual riffraff)
"""
