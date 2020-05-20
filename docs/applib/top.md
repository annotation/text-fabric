# Advanced API

A higher level API so that users can get the corpus data in a simple way
and can display materials of their corpus in an intuitive way.

There are many scenarios in which you can work with the advanced API:
in a Python script or in a notebook or in the TF-browser.
If you `tf.server.start` the TF browser, a `tf.server.kernel` process is started
that holds the TF data.
Then a `tf.server.web` server is started that communicates with the kernel,
much like how webserver communicates with a database.

The advanced API supports all these scenarios and is divided into these parts:

* Start up, see `tf.app.use` (call up a corpus)
* App, see `tf.applib.app` (the API of a corpus)
* Display, see `tf.applib.display` (displaying material)
* Linking, see `tf.applib.links` (generating useful links)
* Search, see `tf.applib.search` (control the search engine)
* Sections, see `tf.applib.sections` (headings for sections and structure)

Working behind the scenes:

* Settings, see `tf.applib.settings` (configure an app)
* Display Settings, see `tf.applib.displaysettings` (tweak the display)
* Data, see `tf.applib.data` (load data)
* Repo, see `tf.applib.repo` (negotiate with the data back-end)

Lower level:

* Condense, see `tf.applib.condense` (distribute query results over containers)
* Find, see `tf.applib.find` (finding TF apps)
* Highlight, see `tf.applib.highlight` (highlight nodes in displays)
* Tables, see `tf.applib.tables` (tabular structures)
* Text, see `tf.applib.text` (text formats)
* ZipData, see `tf.applib.zipdata` (package and zip TF datasets for sharing)

Lowest level:

* Helpers, see `tf.applib.helpers` (the usual riff-raff)
