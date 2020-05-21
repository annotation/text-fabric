# Web interface

## About

TF contains a web interface
in which you can enter a search template and view the results.

This is realized by a web app based on 
[Flask](http://flask.pocoo.org/docs/1.0/).

This web app connects to the `tf.server.kernel` and merges the retrieved data into a set of 
[templates](https://github.com/annotation/text-fabric/tree/master/tf/server/views).

## Start up

TF kernel, web server and browser page are started
up by means of a script called `text-fabric`, which will be installed in an executable
directory by the `pip` installer.

## Routes

There are 4 kinds of routes in the web app:

url pattern | effect
--- | ---
`/server/static/...` | serves a static file from the server-wide [static folder](https://github.com/annotation/text-fabric/tree/master/tf/server/static)
`/data/static/...` | serves a static file from the app specific static folder
`/local/static/...` | serves a static file from a local directory specified by the app
anything else | submits the form with user data and return the processed request

## Templates

There are two templates in
[views](https://github.com/annotation/text-fabric/tree/master/tf/server/views)
:

* *index*: the normal template for returning responses
  to user requests;
* *export*: the template used for exporting results; it
  has printer/PDF-friendly formatting: good page breaks.
  Pretty displays always occur on a page by their own.
  It has very few user interaction controls.
  When saved as PDF from the browser, it is a neat record
  of work done, with DOI links to the corpus and to Text-Fabric.

## CSS

We format the web pages with CSS, with extensive use of
[flexbox](https://css-tricks.com/snippets/css/a-guide-to-flexbox).

There are several sources of CSS formatting:

* the CSS loaded from the app dependent extraApi, used
  for pretty displays;
* [index.css](https://github.com/annotation/text-fabric/blob/master/tf/server/static/index.css): the formatting of the 
  *index* web page with which the user interacts;
* [export.css](https://github.com/annotation/text-fabric/blob/master/tf/server/views/export.css)
  the formatting of the export page;
* [base.css](https://github.com/annotation/text-fabric/blob/master/tf/server/views/base.css)
  shared formatting between the index and export pages.
    
## Javascript

We use a
[modest amount of Javascript](https://github.com/annotation/text-fabric/blob/master/tf/server/static/tf.js)
on top of 
[JQuery](https://api.jquery.com).

For collapsing and expanding elements we use the
[details](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/details)
element. This is a convenient, Javascript-free way to manage
collapsing. Unfortunately it is not supported by the Microsoft
browsers, not even Edge.

!!! caution "On Windows?"
    Windows users should install Chrome of Firefox.
