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

Layers do not have to correspond with the text of the corpus.
For example, you can make a layer where you put the part-of-speech of the
words after each other. You could then search for things like

```
(verb noun noun)+
```

## Combined search

In order to search, you specify search patterns for as many of
the available layers as you want.

When the search is performed, all these layers will produce results,
and the results per layer will be compared, and only results that
hold in all layers, filter through.

So, if you have specified 

level | layer | pattern
--- | --- | ---
**word** | *part-of-speech* | `verb noun`

then the results are sequences of two words, of which the first is a verb and the
second is a noun.

If you have specified

level | layer | pattern
--- | --- | ---
**word** | *part-of-speech* | `verb noun`
**word** | *ascii* | `\b\w*G\w*\b\w*H\w*`

the previous results are constrained by the fact that
the candidate word pairs must be such that the first one contains the
letter `G` and the second one the letter `H`.

You can also constrain with other levels:

level | layer | pattern
--- | --- | ---
**word** | *part-of-speech* | `verb noun`
**word** | *ascii* | `\b\w*G\w*\b\w*H\w*`
**book** | *title* | `Genesis`

Now the additional constraint on the word pairs is that they occur
in a book with title Genesis.

You can go even further:

level | layer | pattern
--- | --- | ---
**word** | *part-of-speech* | `verb noun`
**word** | *ascii* | `\b\w*G\w*\b\w*H\w*`
**sentence** | *number* | `\b[123]\b`
**book** | *title* | `Genesis`

Not only must the word pairs occur in Genesis, they also must occur in one
of the first 3 sentences of a chapter, assuming that the sentences have been
numbered by chapter.

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
The onse that are not will be displayed a bit dimmed, and they serve as
context.

By varying the container type, you can provide more or less context
to your search results.

**Show layers**: In the column `show` you see a number of checkboxes.
Only the checked layers will show up in the search results.

Note that you can switch on layers in which you did not search,
and you can switch off layers in which you did search.

For example, if you searched this

show | level | layer | pattern
--- | --- | --- | ---
`[ ]` | **word** | *text* | ` `
`[v]` | **word** | *consonant-vowel* | `CVCC`

then your results will look like

```
CVCC ... CVCC ... CVCC
```

But if you selected the other level for show:

show | level | layer | pattern
--- | --- | --- | ---
`[v]` | **word** | *text* | ` `
`[ ]` | **word** | *consonant-vowel* | `CVCC`

your results will look like

```
hark ... word ... calm
```

and if you select both they will look like

```
CVCC ... CVCC ... CVCC
hark ... word ... calm
```

### Execute

When you click the big **Go** button,
the search is executed and results get displayed.

Right below the button you'll see the number of items
found, specified per level.

### Results table

There might be (very) many results.
Displaying them all might quickly overwhelm your browser.
The interface only shows in the order of 40 results at a time.

By means of the slider you can wade through the results, and set the focus
position, i.e. the position in the table around which you want to see those
40 results.

You can also type that position into a box, and you can shift it
by a full or half-window forward or backward.

## Jobs

Your search task is called a *job* and it has a name.
You see it on the interface, and you can change it.

Your browser will remember your jobs, but you can also save jobs to file
on disk, from where you can archive them, or share them by any means you find
convenient: mail, message, twitter , etc.

A job file is a small `.json` file that only contains the search patterns
and display settings of the job.

You can also export the results to Excel.
When you do that, *all* results will get exported, not only the ones that show
on the interface.

The organization of the exported results is as follows: for each item
that is in some level in some result, a row is made.

The first column is an identifier for that item: a number.
The second column is the type of the level of that item: `text`, `word`, etc.

And then follow columns for the individual layers, and the corresponding
cells are filled with the values of the items in those layers, with
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





