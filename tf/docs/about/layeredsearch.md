# Layered Search

This is a way of full-text searching your corpus by means of
[regular expressions](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Regular_Expressions/Cheatsheet),
but with a twist to make use of the annotations made to items in the corpus at various levels.

## Corpus in layers

Your corpus is divided into levels, e.g. book/chapter/verse/sentence/word/line/letter.

At each level the items of corpus can be represented in certain ways:

* books are represented by book titles;
* chapters and verses are represented by their numbers;
* words and letters are represented by the strings of which they are composed.

Per level, there may be more than one way to represent the items.
For example, for the word level, you may have representations in the original script in unicode,
but also various transliterations in ascii.

All these representations are *layers* that you can search.
Here you can see how that looks like for the
[NENA corpus](https://github.com/CambridgeSemiticsLab/nena_tf)
which contains various text representations, among which several are dedicated to phonetic
properties.

![layers](../images/ls/layers.png)

Layers do not have to correspond with the text of the corpus.
For example, you can make a layer where you put the part-of-speech of the
words after each other. You could then search for things like

```
(verb noun noun)+
```

We'll stick to NENA to provide us with examples of how to use layered search.

## Combined search

In order to search, you specify search patterns for as many of
the available layers as you want.

When the search is performed, all these layers will produce results,
and the results per layer will be compared, and only results that
hold in all layers, filter through.

So, if you have specified 

level | layer | pattern
--- | --- | ---
**word** | **fuzzy** | `m[a-z]*t[a-z]*l`

you get all words with an `m`, `t`, and `l` in it, in that order.
There are 1338 such words in 1238 sentences.

![results1](../images/ls/results1.png)

By clicking on the checkbox next to the **full** layer,
you will see the full-ascii transliteration of these results as well.

![results2](../images/ls/results2.png)

You can specify an additional search in the **full** layer, for example
all words with a backquote \` in it. (A combining vowel diacritic).

We then get the words that meet both criteria, still a good 492:

![results3](../images/ls/results3.png)

level | layer | pattern
--- | --- | ---
**word** | **full** | \`
**word** | **fuzzy** | `m[a-z]*t[a-z]*l`

You can also constrain with other levels.
Suppose we want only occurrences of the previous results in texts
written at the place *Dure*.

level | layer | pattern
--- | --- | ---
**text** | **place** | `Dure`
**word** | **full** | \`
**word** | **fuzzy** | `m[a-z]*t[a-z]*l`

![results4](../images/ls/results4.png)

Now the additional constraint on the word pairs is that they occur
in a book with title Genesis.

You can go even further, we want them in the first 9 lines of the texts:

level | layer | pattern
--- | --- | ---
**text** | **place** | `Dure`
**line** | **number** | `Dure`
**word** | **full** | \`
**word** | **fuzzy** | `m[a-z]*t[a-z]*l`

Still 20 results.

![results5](../images/ls/results5.png)

## Additional controls

The interface gives you additional ways to control how the results of your
search are being displayed.

**Container type**: In the column `by` you see radio buttons.
Here you select the level that is used to chunk the search results in individual
bits.
Suppose you select `sentence` as your container type. 
Then all result items of type `sentence` are picked as the basis of a result.
For each result, ancestors and descendants are added to the result.
The ancestors are the items of higher levels that contain the `sentence` item.
The descendants are all items at all levels that are contained in the `sentence` item.

Note that all ancestor items are part of the search results.
But not all descendant items are part of the search results.
The ones that are results will be highlighted.
The ones that are not will be displayed a bit dimmed, and they serve as
context.

By varying the container type, you can provide more or less context
to your search results.

We can select **word**, to get a much more compact overview:

![results6](../images/ls/results6.png)

**Show layers**: In the column `show` you see a number of checkboxes.
Only the checked layers will show up in the search results.

Note that you can switch on layers in which you did not search,
and you can switch off layers in which you did search.

For example, lets look at the **lite** and **manner** layers
only (within the word layers):

![results7](../images/ls/results7.png)

### Execute

When you click the big **go search** button,
the search is executed and results get displayed.

Right below the button you'll see the number of items
found, specified per level.

### Results table

There might be (very) many results.
Displaying them all might quickly overwhelm your browser.
The interface only shows a screenful and then some,
but you have various devices to move through them fluidly.

By means of the slider you can wade through the results, and set the focus
position, i.e. the position in the table around which you want to see
some results.

The row that is in focus is clearly marked by a clear blue border,
and the row that had focus just before has a dim blue border.

You can also type that position into a box.
And you can shift the focus by one or a half screen in both directions.
Or go to the first or last result.

There are keyboard short cuts for all of these controls (except the slider).
If you hover over them, you see what the shortcut is.

![results8](../images/ls/results8.png)

## Jobs

Your search task is called a *job* and it has a name.
You see it on the interface, and you can add new jobs,
duplicate and rename existing ones, delete some, and switch
between all jobs that your browser has remembered.

![jobs](../images/ls/jobs.png)

Your browser will indeed remember your jobs (not through cookies!
but for your eyes only).

But if you want to have other eyes look at your searches,
you can also save jobs to file on disk, from where you can archive them,
or share them by any means you find convenient: mail, message, twitter , etc.

A job file is a small `.json` file that only contains the search patterns
and display settings of the job.

You can also export the search results to Excel.
When you do that, *all* results will get exported, not only the ones that show
on the interface.

![export](../images/ls/export.png)

The organization of the exported results is as follows:
for each result item a row is made.

The first column is an identifier for that item: a number, aka as *node*.
The second column is the type of that item: `text`, `word`, etc.,
aka as *node type*.

And then follow columns for the individual layers, and the corresponding
cells are filled with the values of the nodes in those layers, with
the parts that match the search between `«` and `»`.
Only layers that have their `show` checkboxes marked will make it to
the Excel file.

# The app

We have implemented layered search as an offline Single Webpage Application.

The app consists of:

* a HTML file (`index.html`)
* a CSS file (`layered.css`)
* a JS controlling program (`layered.js` with auxiliary `jquery.js`)
* a JS corpus data file (`corpus.js`) 

If you have these files on your computer, you can just open `index.html` in your
browser, and the interface is ready to use, and you do not need a server connection.

If you have found `index.html` somewhere on the web, and the page is loaded,
you can work with it offline. You can also save this webpage in your browser
(take care to save it in full, as webarchive) and work with it later, without
internet connection. You might have to put all four files together in one directory,
depending on the way the browser has saved the webpage for you.

As a consequence, the app works without any kind of installation.
It also does not collect data about you, or sets cookies.
When the browser remembers your previous jobs,
it does not use cookies for it but
[localStorage](https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage),
which other sites cannot read.

# Making this app

The construction of this app relies very much of the organization of the corpus
as a Text-Fabric dataset.

The layered search functionality is not (yet) baked into Text-Fabric.
We have created the first layered search interface for the 
[NENA](https://github.com/CambridgeSemiticsLab/nena_tf) (in the directory *nena2search*)
corpus, by means of a Jupyter Notebook
[makeCorpus](https://nbviewer.jupyter.org/github/CambridgeSemiticsLab/nena_tf/blob/master/nena2search/makedata.ipynb).

We intend to make such interfaces for other Text-Fabric corpora, using more
streamlined ways.

# Credits

The idea for this app came out of a discussion of
[Cody Kingham](https://www.linkedin.com/in/cody-kingham-1135018a)
and me about how we could
make a simple but usable search interface for people that need to get hand on with
the corpus in the first place.

Given that we have the corpus data at our finger tips through Text-Fabric,
but that TF-Query (`tf.about.searchusage`) is over the top, and requires installing Python
and almost programming, the approach is to assemble data and power a simple Javascript
program with it.

This implementation of the idea was funded by
[Prof. Geoffrey Kahn](https://www.ames.cam.ac.uk/people/professor-geoffrey-khan),
and eventually written by
[Dirk Roorda](https://pure.knaw.nl/portal/en/persons/dirk-roorda).





