<html> 
    <head>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
        <title>Text-Fabric {{fileName}}</title>
        <meta name="application-name" content="Text-Fabric Search Box"/>
<style type="text/css">
body {
    padding: 2rem;
}
div.hline {
    font-size: large;
    font-style: italic;
    text-align: center;
}
pre.template {
	font-size: medium;
	font-family: monospace;
	width: calc(100% - 1rem);
	margin: 0.3rem 0.3rem;
    background-color: #ffeedd;
}
div.dtheadrow {
    font-weight: bold;
    background-color: #aaaaaa;
    margin-top: 0.5rem;
    margin-bottom: 0.5rem;
}
div.dtheadrow > span {
    padding: 0.2rem;
    border-right: 0.1rem solid #bbbbbb;
}
details.dtrow {
    border: 0.1rem solid #bbbbbb;
    padding: 0.1rem 0;
}
details.dtrow[open] {
    page-break-before: always;
    break-before: always;
    page-break-after: always;
    break-after: always;
}
details.dtrow > summary {
    background-color: #f0f0f0;
}
details.dtrow > summary > span {
    padding: 0.2rem;
    border-right: 0.1rem solid #bbbbbb;
}
div.pretty {
    width: 100%;
    padding: 0.2rem 0 0.5rem 0;
}
div.colofon {
    display: flex;
    flex-flow: row nowrap;
    justify-content: space-between;
    align-items: flex-start;
}
img.hdlogo {
    flex: 0 0 auto;
    max-width: 5rem;
    height: 4rem;
}
div.hdlinks {
    flex: 0 1 auto;
    display: flex;
    flex-flow: row wrap;
    justify-content: space-around;
    align-items: baseline;
}
div.hdlinks > a {
    flex: 1 1 4rem;
    background-color: #eeeeff;
    border-radius: 0.4rem;
    border: 0.1rem solid #cccccc;
    padding: 0.2rem 0.2rem;
    margin: 0.2rem 0.2rem;
    text-align: center;
    text-decoration: none;
}
</style>
        {{!css}}
    </head>
    <body>
        <div class="header">
            <div class="hline">{{fileName}}</div>
        </div>
        <hr/>
        <div>
            <pre class="template">{{searchTemplate}}</pre>
        </div>
        <div class="table">
            {{!table}}
        </div>
        <hr/>
        <div class="colofon">
            {{!colofon}}
        </div>
    </body>
</html>
