<html> 
    <head>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
        <title>Text-Fabric {{dataSource}}</title>
        <meta name="application-name" content="Text-Fabric Search Box"/>

        <link rel="stylesheet" href="/server/static/main.css"/>
        {{!css}}
    </head>
    <body>
        <form id="go" method="post">
            <label>Query</label>
            <textarea name="searchTemplate">{{searchTemplate}}</textarea>
            Goto result <input type="text" id="pos" name="position" value="{{position}}"/> with
            <input type="text" name="batch" value="{{batch}}"/> results per page
            <button type="submit">Go</button>
        </form>
        <div>
            <label>Messages</label>
            <div class="messages">
                {{!messages}}
            </div>
        </div>
        <div>
            <label>Results</label>
            <div class="resultlist">
                {{!table}}
            </div>
        </div>
        <div>
            <label>Navigation</label>
            <div class="navigation">
                {{!pages}}
            </div>
        </div>
        <div>
            <label>Detail</label>
            <div class="resultitem"/>
        </div>
        <script src="/server/static/jquery.js"></script>
        <script src="/server/static/tf.js"/></script>
    </body>
</html>
