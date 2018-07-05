# Web site

## About

??? abstract "Local web interface"
    TF contains a local web interface
    in which you can enter a search template and view the results.

    This is realized by a web app based on 
    [bottle](http://bottlepy.org).

    This web app connects to the [TF data service](/Server/Service)
    and merges the retrieved data into a set of 
    [templates](https://github.com/Dans-labs/text-fabric/tree/master/tf/server/views).

    See the code in
    [tf.server.web](https://github.com/Dans-labs/text-fabric/tree/master/tf/server/web.py).

??? abstract "Start up"
    Data server, webserver and browser page are started
    up by means of 

## Routes

??? abstract "Routes"
    There are 4 kinds of routes in the web app:

    url pattern | effect
    --- | ---
    `/server/static/...` | serves a static file from the server-wide [static folder](https://github.com/Dans-labs/text-fabric/tree/master/tf/server/static)
    `/data/static/...` | serves a static file from the app specific static folder
    `/local/static/...` | serves a static file from a local directory specified by the app
    anything else | submits the form with user data and return the processed request

## Templates

??? abstract "Templates"
    There are two templates in
    [views](https://github.com/Dans-labs/text-fabric/tree/master/tf/server/views)
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

??? abstract "CSS"
    We format the web pages with CSS, with extensive use
    of
    [flexbox](https://css-tricks.com/snippets/css/a-guide-to-flexbox).

    There are three sources of CSS formatting:

    * the CSS loaded from the app dependent extraApi, used
      for pretty displays;
    * [main.css](https://github.com/Dans-labs/text-fabric/tree/master/tf/server/static/main.css): the formatting of the 
      *index* web page with which the user interacts;
    * inside the
      [export](https://github.com/Dans-labs/text-fabric/tree/master/tf/server/views/export.tpl)
      template, for formatting the exported page.

## Javascript

??? abstract "Javascript"
    We use a
    [modest amount of Javascript](https://github.com/Dans-labs/text-fabric/tree/master/tf/server/static/tf.js)
    on top of 
    [JQuery](https://api.jquery.com).

    For collapsing and expanding elements we use the
    [details](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/details)
    element. This is a convenient, Javascript-free way to manage
    collapsing. Unfortunately it is not supported by the Microsoft
    browsers, not even Edge.

    ??? caution "On Windows?"
        Windows users should install Chrome of Firefox.

    Safari is fine.
