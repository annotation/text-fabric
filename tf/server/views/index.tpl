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
        <div class="page">
            <div class="leftcol">
                <div class="header">
                    {{!header}}
                </div>
                <textarea class="template" name="searchTemplate">{{searchTemplate}}</textarea>
                <p class="go"><button class="go" type="submit">Go</button></p>
                <div class="messages">
                    {{!messages}}
                </div>
            </div>
            <div class="midcol">
                <div class="navigation">
                    <div><input class="int" type="text" id="pos" name="position" value="{{position}}"/> current position</div>
                    <div><input class="int" type="text" name="batch" value="{{batch}}"/> results per page</div>
                </div>
                <div class="pages">
                    {{!pages}}
                </div>
            </div>
            <div class="rightcol">
                {{!table}}
            </div>
        </div>
        </form>
        <script src="/server/static/jquery.js"></script>
        <script src="/server/static/tf.js"/></script>
    </body>
</html>
