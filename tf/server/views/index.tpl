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
                <div class="messages">
                    {{!messages}}
                </div>
                <p class="go"><button class="go" type="submit">Go</button></p>
                <div class="setting">
                    <div><input class="int" type="text" id="lnk" name="linked" value="{{linked}}"/> link column</div>
                    <div><input type="checkbox" id="withn" name="withNodes" {{withNodesAtt}}/> show nodes</div>
                    <div>
                        <div><input type="checkbox" id="cond" name="condensed" {{condensedAtt}}/> condense results</div>
                        {{!condenseOpts}}
                    </div>
                    {{!options}}
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
            <input type="hidden" id="op" name="opened" value="{{opened}}"/>
            <div class="rightcol">
                {{!table}}
            </div>
        </div>
        <div>
            <div>Test</div>
            <div>{{test}}</div>
        </div>
        </form>
        <script src="/server/static/jquery.js"></script>
        <script src="/server/static/tf.js"/></script>
    </body>
</html>
