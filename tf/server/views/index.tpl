<html> 
    <head>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
        <title>TF {{fileName}}</title>
        <meta name="application-name" content="Text-Fabric Search Box"/>

        <link rel="stylesheet" href="/server/static/main.css"/>
        {{!css}}
    </head>
    <body>
        <form id="go" method="post">
        <div class="page">
            <div id="sidebar">
                <div status="help">
                    <a href="#">Help</a>
                </div>
                <div status="load">
                    <a href="#">Load</a>
                </div>
                <div status="options">
                    <a href="#">Options</a>
                </div>
                <div status="export">
                    <a href="#">Export</a>
                </div>
                <div status="about">
                    <a href="#">About</a>
                </div>
            </div>
            <div id="sidebarcont">
                <div status="help">
                    <div class="header">
                        {{!header}}
                    </div>
                    <details class="help">
                        <summary>Section Pad</summary>
                        <p>You can enter a reference here,
                           such as <code>Genesis 1:1</code> (Hebrew Bible) or
                           <code>P003581</code> (cuneiform)
                        </p>
                        <p>You can also get references here by clicking on a
                           reference in the result list.
                        </p>
                        <p>Click go to fetch the results</p>
                        <p>The results of the references appear in the result list,
                           with a negative sequence number.
                        </p>
                    </details>
                    <details class="help">
                        <summary>Node Pad</summary>
                        <p>Enter a node or list of nodes here,
                           such as <code>123</code> or
                           <code>123,456,789</code>
                        </p>
                        <p>Click on the sequence number in the result list,
                           to put its nodes on the pad.
                        </p>
                        <p>Click on a node (when the option *show nodes* is checked,
                           to put the node on the pad.
                        </p>
                        <p>Click go to fetch the results</p>
                        <p>The results of the nodes appear in the result list,
                           with a negative sequence number.
                        </p>
                    </details>
                    <details class="help">
                        <summary>Search Pad</summary>
                        <p>Enter a search template here.
                           See the buttons on top for the docs.
                        </p>
                        <p>Click go to fetch the results</p>
                        <p>The results of the search appear in the result list,
                           with a positive sequence number.
                        </p>
                    </details>
                    <details class="help">
                        <summary>Result list</summary>
                        <p>Click the triangle to expand a result into a pretty view</p>
                        <p>Click the sequence number to add the nodes in this result to the *node pad*</p>
                        <p>Click the reference, to add it to the *reference pad*</p>
                        <p>Use the navigation button to walk through the results.<p>
                        <p>Results that you have expanded remain in view</p>
                        <p>group results by container: see the *condense* option</p>
                    </details>
                    <details class="help">
                        <summary>Load</summary>
                        <p>Your work will be saved in a file with extension <code>.tfquery</code> in the
                           current directory.</p>
                        <p>Save your work under an other name, by typing a new name in the name field.</p>
                        <p>Load a previous job by selecting the name under which it has been saved.</p>
                    </details>
                    <details class="help">
                        <summary>Export</summary>
                        <p>Export your results. Provide name, title, and description (markdown is supported),
                           and click *export*.</p>
                        <p>The exported page opens in a new window or tab, formatted for saving as PDF.</p>
                        <p>Use your browser to export this page to PDF.</p>
                        <p>The PDF will contain a complete description of your work, with persistent links
                           to the corpora and the tools, with additional metadata, and with the information
                           you specify.</p>
                        <p><b>Tip</b> Archive this PDF in a repository, and you can cite your work properly.</p>
                    </details>
                    <details class="help">
                        <summary>Options</summary>
                        <p><b>Link column</b> The column number whose contents will be hyperlinked to the online version
                           of the corpus.</p>
                        <p><b>Condense results</b> Show the results grouping all nodes in result tuples into
                           containers. The containers are *pretty*-displayed, with the result nodes in it highlighted.
                           Choose the container type as you whish.</p>
                        <p><b>Show nodes</b> Show the node number for every object in the results.
                           The node number is your access to all information about that object.</p>
                    </details>
                </div>
                <div status="load">
                    <div>
                        Name of this query:
                    </div>
                    <div>
                        <input
                            class="name" type="text" name="fileName" value="{{fileName}}"
                            placeholder="save as"
                        />
                    </div>
                    <div>Other queries in this directory (click to load):</div>
                    <select class="r" name="previous" value="{{previous}}">
                        {{!prevOptions}}
                    </select>
                </div>
                <div status="options">
                    <div>
                        <input
                            class="r int" type="text" id="lnk" name="linked" value="{{linked}}"
                            placeholder="1"
                        /> link column
                    </div>
                    <div>
                        <details id="condd" {{'open' if condensedAtt else ''}}>
                            <summary>
                                <input
                                    class="r" type="checkbox" id="cond" name="condensed" {{condensedAtt}}
                                /> condense results
                            </summary>
                            {{!condenseOpts}}
                        </details>
                    </div>
                    <div>
                        <input
                            class="r" type="checkbox" id="withn" name="withNodes" {{withNodesAtt}}
                        /> show nodes
                    </div>
                    {{!options}}
                </div>
                <div status="export">
                    <div>
                        <div>Author</div>
                        <div>
                            <input
                                class="name" type="text" name="author" value="{{author}}"
                                placeholder="My Name"
                            />
                        </div>
                        <div>Title</div>
                        <div>
                            <input
                                class="name" type="text" name="title" value="{{title}}"
                                placeholder="Title"
                            />
                        </div>
                        <div>Description</div>
                        <div class="description">
                            <textarea
                                class="description" name="description"
                                placeholder="Description"
                            >{{description}}</textarea>
                        </div>
                        <p class="buttons">
                            <button
                                class="xl" type="submit" formtarget="_new" name="export" value="1"
                            > export
                            </button>
                        </p>
                    </div>
                </div>
                <div status="about">
                    <div>
                        <p><a target="_blank" href="https://github.com/Dans-labs/text-fabric">Text-Fabric</a> is made by
                           <a target="_blank" href="https://dans.knaw.nl/en/about/organisation-and-policy/staff/roorda">Dirk Roorda</a>,
                           <a target="_blank" href="https://dans.knaw.nl/en">DANS (Data Archiving and Networked Services</a>
                        </p>
                    </div>
                    <div><img class="mainlogo" src="/server/static/dans.png"/></div>
                </div>
            </div>
            <div class="leftcol">
                <textarea
                    id="sections" class="sections" name="sections"
                    placeholder="section pad"
                >{{sections}}</textarea>
                <textarea
                    id="tuples" class="tuples" name="tuples"
                    placeholder="node pad"
                >{{tuples}}</textarea>
                <div class="messages">
                    {{!tupleMessages}}
                </div>
                <textarea
                    class="template" name="searchTemplate"
                    placeholder="search pad"
                >{{searchTemplate}}</textarea>
                <div class="messages">
                    {{!queryMessages}}
                </div>
                <p class="buttons"><button class="xl" type="submit">Go</button></p>
            </div>
            <div class="midcol">
                <div class="navigation">
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
