<html> 
    <head>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
        <title>Text-Fabric {{fileName}}</title>
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
                    <div>
                        <input
                            class="r int" type="text" id="lnk" name="linked" value="{{linked}}"
                        /> link column
                    </div>
                    <div>
                        <input
                            class="r" type="checkbox" id="withn" name="withNodes" {{withNodesAtt}}
                        /> show nodes
                    </div>
                    <div>
                        <div>
                            <input
                                class="r" type="checkbox" id="cond" name="condensed" {{condensedAtt}}
                            /> condense results
                            </div>
                        {{!condenseOpts}}
                    </div>
                    {{!options}}
                </div>
            </div>
            <div class="midcol">
                <div class="navigation">
                    <div>
                        <button
                            type="submit" formtarget="_new" name="export" value="1"
                        > export
                        </button>
                    </div>
                    <div>
                        <input
                            type="checkbox" id="expac"
                        /> expand all
                        <input type="hidden" name="expandAll" id="expa" value="{{expandAll}}"/>
                    </div>
                    <div>
                        <input
                            class="r int" type="text" id="pos" name="position" value="{{position}}"
                        /> current position
                    </div>
                    <div>
                        <input
                            class="r int" type="text" name="batch" value="{{batch}}"
                        /> results per page
                    </div>
                </div>
                <div class="pages">
                    {{!pages}}
                </div>
            </div>
            <div class="rightcol">
                <input type="hidden" id="op" name="opened" value="{{opened}}"/>
                {{!table}}
            </div>
        </div>
        </form>
        <script src="/server/static/jquery.js"></script>
        <script src="/server/static/tf.js"/></script>
    </body>
</html>
