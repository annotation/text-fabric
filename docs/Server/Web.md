# Local Web interface

## About

??? abstract "Local web interface"
    TF contains a local web interface
    in which you can enter a search template and view the results.

    This is realized by a web app based on 
    [bottle]({{bottle}}).

    This web app connects to the [TF kernel](Kernel.md)
    and merges the retrieved data into a set of 
    [templates]({{tfght}}/{{c_views}}).

    See the code in
    [local]({{tfghb}}/{{c_local}}).

## Start up

??? abstract "Start up"
    TF kernel, webserver and browser page are started
    up by means of a script called `text-fabric`, which will be installed in an executable
    directory by the `pip` installer.
    
    What the script does is the same as:
    
    ```sh
    python3 -m tf.server.start
    ```
    
??? abstract "Process management"
    During start up the following happens:
    
    ??? abstract "Kill previous processes"
        The system is searched for non-terminated incarnations of the processes
        it wants to start up.
        If they are encountered, they will be killed, so that they cannot prevent
        a successful start up.
    
    ??? abstract "TF kernel"
        A [TF kernel](Kernel.md) is started.
        This process loads the bulk of the TF data, so it can take a while.
        When it has loaded the data, it sends out a message that loading is done,
        which is picked up by the script.

    ??? abstract "TF webserver"
        A short while after receiving the "data loading done" message, the TF webserver is started.
        
        ??? hint "Debug mode"
            If you have passed `-d` to the `text-fabric` script, the **bottle** will be started
            in debug and reload mode.
            That means that if you modify `web.py` or a module it imports, the webserver will
            reload itself automatically.
            When you refresh the browser you see the changes.
            If you have changed templates, the css, or the javascript, you should do a "refresh from origin".

    ??? abstract "Load web page"
        After a short while, the default web browser will be started with a url and port at which the
        webserver will listen. You see your browser being started up and the TF page being loaded.

    ??? abstract "Waiting"
        The script now waits till the webserver is finished.
        You finish it by pressing Ctrl-C, and if you have used the `-d` flag, you have to press it twice.

    ??? abstract "Terminate the TF kernel"
        At this point, the `text-fabric` script will terminate the TF kernel.

    ??? abstract "Clean up"
        Now all processes that have started up have been killed.
        
        If something went wrong in this sequence, chances are that a process keeps running.
        It will be terminated next time you call the `text-fabric`.
        
        ??? hint "You can kill too"
            If you run
            
            ```sh
            text-fabric -k
            ``` 
            
            all tf-browser-related processes will be killed.

            ```sh
            text-fabric -k ddd
            ```

            will kill all such processes as far as they are for data source `ddd`.

## Routes

??? abstract "Routes"
    There are 4 kinds of routes in the web app:

    url pattern | effect
    --- | ---
    `/server/static/...` | serves a static file from the server-wide [static folder]({{tfght}}/{{c_static}})
    `/data/static/...` | serves a static file from the app specific static folder
    `/local/static/...` | serves a static file from a local directory specified by the app
    anything else | submits the form with user data and return the processed request

## Templates

??? abstract "Templates"
    There are two templates in
    [views]({{tfght}}/{{c_views}})
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
    [flexbox]({{cssflex}}).

    There are three sources of CSS formatting:

    * the CSS loaded from the app dependent extraApi, used
      for pretty displays;
    * [main.css]({{tfghb}}/{{c_static}}/main.css): the formatting of the 
      *index* web page with which the user interacts;
    * inside the
      [export]({{tfghb}}/{{c_views}}/export.tpl)
      template, for formatting the exported page.

## Javascript

??? abstract "Javascript"
    We use a
    [modest amount of Javascript]({{tfghb}}/{{c_static}}/tf.js)
    on top of 
    [JQuery](https://api.jquery.com).

    For collapsing and expanding elements we use the
    [details]({{moz_details}})
    element. This is a convenient, Javascript-free way to manage
    collapsing. Unfortunately it is not supported by the Microsoft
    browsers, not even Edge.

    ??? caution "On Windows?"
        Windows users should install Chrome of Firefox.

    Safari is fine.
